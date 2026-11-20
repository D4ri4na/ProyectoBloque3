"""Núcleo no supervisado con protocolo documentado y contraste posterior de popularidad."""
from pathlib import Path
import hashlib
import importlib.metadata
import itertools
import json
import platform
import time
import warnings
import html
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler, PowerTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.decomposition import PCA
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score, adjusted_rand_score
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'resultados'
PROTOCOL = json.loads((ROOT/'protocolo_mejora.json').read_text('utf-8'))
FEATURES = PROTOCOL['features']
SEED = PROTOCOL['seed']

def dump(name, value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=lambda v:v.item() if hasattr(v,'item') else str(v)),encoding='utf-8')

def table(frame):
    frame=frame.copy()
    for c in frame:
        frame[c]=frame[c].map(lambda x:f'{x:.5f}' if isinstance(x,(float,np.floating)) and np.isfinite(x) else ('—' if pd.isna(x) else str(x)))
    return '\n'.join(['| '+' | '.join(map(str,frame.columns))+' |','| '+' | '.join(['---']*len(frame.columns))+' |']+['| '+' | '.join(str(x).replace('|','/') for x in row)+' |' for row in frame.itertuples(index=False,name=None)])

def figure(name):
    plt.tight_layout(); plt.savefig(OUT/'figuras'/f'{name}.png',dpi=140,bbox_inches='tight'); plt.close()

def artists(value):
    return {v.strip().casefold() for v in str(value).split(';') if v.strip() and v.strip().casefold()!='nan'}

def artist_groups(frame):
    parent=list(range(len(frame))); owner={}
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,value in enumerate(frame.artists):
        for a in sorted(artists(value)):
            if a in owner:
                # Representante canónico: no depender del orden aleatorio de sets.
                left,right=find(i),find(owner[a])
                parent[max(left,right)]=min(left,right)
            else: owner[a]=i
    return np.array([find(i) for i in range(len(frame))])

def artist_union(frame):
    return set().union(*(artists(v) for v in frame.artists))

def clean_data(frame):
    frame=frame.dropna(subset=['track_id']).drop_duplicates('track_id',keep='first').copy()
    for col in FEATURES+['popularity']:
        frame[col]=pd.to_numeric(frame[col],errors='coerce').replace([np.inf,-np.inf],np.nan)
    for col in [c for c in FEATURES if c not in ['loudness','tempo','duration_ms']]:
        frame.loc[~frame[col].between(0,1),col]=np.nan
    for col in ['tempo','duration_ms']:
        frame.loc[frame[col]<=0,col]=np.nan
    frame.loc[~frame.popularity.between(0,100),'popularity']=np.nan
    return frame.loc[frame[FEATURES].notna().any(axis=1)].reset_index(drop=True)

def signatures(frame):
    return pd.util.hash_pandas_object(frame[FEATURES].astype('float64').round(7),index=False).to_numpy()

def splits():
    raw=pd.read_csv(ROOT/'data/raw/spotify_tracks.csv')
    clean=clean_data(raw)
    prior_train=clean_data(pd.read_csv(ROOT/'data/referencia_anterior/train.csv'))
    prior_test=clean_data(pd.read_csv(ROOT/'data/referencia_anterior/test.csv'))
    previous=pd.concat([prior_train,prior_test],ignore_index=True)
    groups=artist_groups(prior_train)
    a,b=next(GroupShuffleSplit(n_splits=1,test_size=PROTOCOL['validation_group_fraction'],random_state=SEED).split(prior_train,groups=groups))
    fit=prior_train.iloc[a].reset_index(drop=True); validation=prior_train.iloc[b].reset_index(drop=True)
    previous_artists=artist_union(previous)
    mask=~clean.track_id.isin(previous.track_id)
    mask &= clean.artists.map(lambda v:bool(artists(v)) and not bool(artists(v)&previous_artists))
    mask &= ~np.isin(signatures(clean),signatures(previous))
    eligible=clean.loc[mask]
    if len(eligible)<2000: raise ValueError('No existen 2000 canciones reservables con los filtros predefinidos')
    holdout=eligible.sample(n=2000,random_state=PROTOCOL['holdout_seed']).reset_index(drop=True)
    assert not artist_union(fit)&artist_union(validation)
    assert not artist_union(previous)&artist_union(holdout)
    assert not set(previous.track_id)&set(holdout.track_id)
    assert not set(signatures(previous))&set(signatures(holdout))
    audit=dict(raw_rows=len(raw),unique_rows=len(clean),development=len(prior_train),inner_fit=len(fit),validation=len(validation),holdout=len(holdout),eligible_holdout=len(eligible),previous_test_reused_for_selection=False,shared_artists_fit_validation=0,shared_artists_previous_holdout=0,shared_exact_audio_previous_holdout=0,raw_missing=raw[FEATURES].isna().sum().to_dict(),training_missing=prior_train[FEATURES].isna().sum().to_dict(),dataset_sha256=hashlib.sha256((ROOT/'data/raw/spotify_tracks.csv').read_bytes()).hexdigest())
    for name,frame in [('entrenamiento',prior_train),('validacion_interna',validation),('ajuste_interno',fit),('prueba_reservada',holdout)]:frame.to_csv(OUT/f'{name}.csv',index=False)
    dump('auditoria.json',audit)
    return prior_train,fit,validation,holdout,audit

def pipeline(preprocessing):
    if preprocessing=='standard':return make_pipeline(SimpleImputer(strategy='median'),StandardScaler())
    return make_pipeline(SimpleImputer(strategy='median'),PowerTransformer(method='yeo-johnson',standardize=True))

def estimator(family,k,covariance='NA',seed=SEED):
    if family=='KMeans':return KMeans(n_clusters=int(k),n_init=20,random_state=seed)
    return GaussianMixture(n_components=int(k),covariance_type=covariance,n_init=3,max_iter=500,reg_covar=1e-5,random_state=seed)

def fit_model(est,X):
    t=time.perf_counter()
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter('always',ConvergenceWarning);est.fit(X)
    return time.perf_counter()-t,bool(getattr(est,'converged_',True)),len(records)

def silhouette(X,labels,limit=1200):
    ix=np.random.default_rng(SEED).choice(len(X),min(limit,len(X)),replace=False)
    labs=labels[ix]
    return float(silhouette_score(X[ix],labs)) if 1<len(np.unique(labs))<len(ix) else np.nan

def metrics(X,labels):
    if len(np.unique(labels))<2:return dict(silhouette=np.nan,davies_bouldin=np.nan,calinski_harabasz=np.nan)
    return dict(silhouette=silhouette(X,labels,2000),davies_bouldin=float(davies_bouldin_score(X,labels)),calinski_harabasz=float(calinski_harabasz_score(X,labels)))

def choose(frame):
    ok=frame.loc[frame.eligible].copy()
    if ok.empty:raise RuntimeError('Ninguna configuración cumple separación, convergencia y tamaño mínimo')
    near=ok.loc[ok.val_sil_common>=ok.val_sil_common.max()-PROTOCOL['silhouette_tolerance']]
    return near.sort_values(['k','bic'],na_position='last').iloc[0]

def search(fit,validation):
    reference=pipeline('standard').fit(fit[FEATURES])
    common_train=reference.transform(fit[FEATURES]);common_val=reference.transform(validation[FEATURES])
    rows=[];selected=[]
    for prep in PROTOCOL['preprocessing']:
        transform=pipeline(prep).fit(fit[FEATURES]);X=transform.transform(fit[FEATURES]);V=transform.transform(validation[FEATURES])
        pca=PCA(n_components=PROTOCOL['pca_variance'],svd_solver='full').fit(X)
        for space,A,B in [('original',X,V),('pca',pca.transform(X),pca.transform(V))]:
            for family in ['KMeans','GMM']:
                current=[]
                for k in PROTOCOL['k_grid']:
                    for cov in (['NA'] if family=='KMeans' else PROTOCOL['gmm_covariances']):
                        est=estimator(family,k,cov);seconds,converged,nwarnings=fit_model(est,A)
                        lt=est.predict(A);lv=est.predict(B)
                        sizes_t=np.bincount(lt,minlength=k)/len(lt);sizes_v=np.bincount(lv,minlength=k)/len(lv)
                        score=silhouette(common_val,lv)
                        row=dict(preprocessing=prep,model=family,space=space,k=k,covariance=cov,converged=converged,warnings=nwarnings,fit_seconds=seconds,train_sil_native=silhouette(A,lt),val_sil_native=silhouette(B,lv),val_sil_common=score,min_train_fraction=float(sizes_t.min()),min_val_fraction=float(sizes_v.min()),bic=float(est.bic(A)) if family=='GMM' else np.nan,aic=float(est.aic(A)) if family=='GMM' else np.nan,inertia=float(est.inertia_) if family=='KMeans' else np.nan,validation_loglik=float(est.score(B)) if family=='GMM' else np.nan)
                        row['eligible']=bool(converged and np.isfinite(score) and sizes_t.min()>=PROTOCOL['min_cluster_fraction'] and sizes_v.min()>=PROTOCOL['min_cluster_fraction'])
                        current.append(row);rows.append(row)
                frame=pd.DataFrame(current);best=choose(frame);selected.append(best.to_dict())
                frame.to_csv(OUT/f'busqueda_{prep}_{family}_{space}.csv',index=False)
                fig,axs=plt.subplots(1,2,figsize=(11,3.8))
                for cov,g in frame.groupby('covariance'):
                    axs[0].plot(g.k,g.val_sil_common,'o-',label=cov);axs[1].plot(g.k,g.bic if family=='GMM' else g.inertia,'o-',label=cov)
                axs[0].set(xlabel='Número de grupos',ylabel='Silhouette validación, geometría común',title=f'{family}: separación');axs[1].set(xlabel='Número de grupos',ylabel='BIC (menor mejor)' if family=='GMM' else 'Inercia',title='Densidad / codo');axs[0].legend();axs[1].legend();figure(f'busqueda_{prep}_{family}_{space}')
                print(f'{prep}/{family}/{space}: K={best.k}, cov={best.covariance}, val común={best.val_sil_common:.4f}',flush=True)
    all_rows=pd.DataFrame(rows);selected=pd.DataFrame(selected)
    all_rows.to_csv(OUT/'busqueda_completa.csv',index=False);selected.to_csv(OUT/'seleccion_por_preparacion.csv',index=False)
    summary=selected.groupby('preprocessing').val_sil_common.mean()
    prep='yeo_johnson' if summary['yeo_johnson']>summary['standard']+PROTOCOL['preprocessing_min_gain'] else 'standard'
    frozen=dict(protocol_sha256=hashlib.sha256((ROOT/'protocolo_mejora.json').read_bytes()).hexdigest(),preprocessing=prep,mean_validation_silhouette=summary.to_dict(),selected=selected.loc[selected.preprocessing==prep].replace({np.nan:None}).to_dict('records'),selection_uses_popularity=False,selection_uses_holdout=False)
    dump('seleccion_congelada.json',frozen)
    return frozen,all_rows,selected

def final_experiment(train,holdout,frozen):
    prep=frozen['preprocessing'];before=time.perf_counter()
    transform=pipeline(prep).fit(train[FEATURES]);X=transform.transform(train[FEATURES]);T=transform.transform(holdout[FEATURES])
    reference=pipeline('standard').fit(train[FEATURES]);common_train=reference.transform(train[FEATURES]);common_test=reference.transform(holdout[FEATURES])
    pca=PCA(n_components=PROTOCOL['pca_variance'],svd_solver='full').fit(X);Z=pca.transform(X);W=pca.transform(T)
    preprocess_seconds=time.perf_counter()-before
    spectrum=PCA(svd_solver='full').fit(X)
    variance=pd.DataFrame(dict(component=np.arange(1,11),ratio=spectrum.explained_variance_ratio_,cumulative=np.cumsum(spectrum.explained_variance_ratio_)));variance.to_csv(OUT/'varianza_pca.csv',index=False)
    loads=pd.DataFrame(pca.components_.T,index=FEATURES,columns=[f'PC{i+1}' for i in range(pca.n_components_)]);loads.to_csv(OUT/'cargas_pca.csv')
    plt.figure(figsize=(7,4));plt.plot(variance.component,variance.cumulative,'o-');plt.axhline(.9,color='red',ls='--',label='90 %');plt.axvline(pca.n_components_,color='gray',ls=':');plt.xlabel('Componentes');plt.ylabel('Varianza acumulada');plt.title('Elección de PCA solo con entrenamiento');plt.legend();figure('varianza_pca')
    models={};labels={};rows=[];stability=[];profiles=[];pops=[];unscaled=[];timings=[]
    for cfg in frozen['selected']:
        family,space=cfg['model'],cfg['space'];key=family+'_'+space
        A,B=(X,T) if space=='original' else (Z,W)
        est=estimator(family,cfg['k'],cfg['covariance']);seconds,converged,_=fit_model(est,A)
        if not converged:raise RuntimeError(f'No converge {key} al reajustar')
        lt=est.predict(A);tick=time.perf_counter();lv=est.predict(B);predict_seconds=time.perf_counter()-tick
        models[key]=est;labels[key]=(lt,lv)
        for split,matrix,common,lab in [('train',A,common_train,lt),('test',B,common_test,lv)]:
            ari=adjusted_rand_score(labels[family+'_original'][0 if split=='train' else 1],lab) if space=='pca' else np.nan
            for geometry,evaluation in [('native',matrix),('reference_original',common)]:
                rows.append(dict(model=family,space=space,preprocessing=prep,split=split,evaluation_space=geometry,hyperparameters=json.dumps(dict(k=cfg['k'],covariance=cfg['covariance'])),groups=len(np.unique(lab)),noise_pct=0.,fit_seconds=seconds,predict_seconds=predict_seconds,ari_vs_original=ari,**metrics(evaluation,lab)))
        # Las repeticiones no seleccionan ni vuelven a ajustar hiperparámetros.
        for kind in ['seed','subsample']:
            repeated=[]
            for seed in [42,7,21,123]:
                idx=np.random.default_rng(seed).choice(len(A),int(.8*len(A)),replace=False) if kind=='subsample' else np.arange(len(A))
                e=estimator(family,cfg['k'],cfg['covariance'],seed);_,ok,_=fit_model(e,A[idx])
                if not ok:raise RuntimeError(f'No converge repetición {key}/{kind}/{seed}')
                repeated.append(e.predict(B))
            for i,j in itertools.combinations(range(4),2):stability.append(dict(model=family,space=space,kind=kind,run_a=i,run_b=j,ari=float(adjusted_rand_score(repeated[i],repeated[j]))))
        assigned=pd.concat([train.assign(split='train',cluster=lt),holdout.assign(split='test',cluster=lv)],ignore_index=True)
        assigned.to_csv(OUT/f'asignaciones_{key}.csv',index=False)
        med=train.assign(cluster=lt).groupby('cluster')[FEATURES].median();med.to_csv(OUT/f'perfiles_{key}.csv')
        sizes=pd.Series(lt).value_counts()
        for c,r in med.iterrows():profiles.append(dict(model=family,space=space,cluster=int(c),n=int(sizes[c]),**r.to_dict()))
        for split,g in assigned.groupby('split'):
            for c,h in g.groupby('cluster'):pops.append(dict(model=family,space=space,split=split,cluster=int(c),n=len(h),median=float(h.popularity.median()),q25=float(h.popularity.quantile(.25)),q75=float(h.popularity.quantile(.75))))
        plt.figure(figsize=(9,4));plt.imshow(((med-train[FEATURES].mean())/train[FEATURES].std()).to_numpy(),aspect='auto',cmap='RdBu_r',vmin=-2,vmax=2);plt.xticks(range(10),FEATURES,rotation=75);plt.yticks(range(len(med)),med.index);plt.colorbar(label='Mediana respecto a media global (DE)');plt.title('Perfiles: '+key);figure('perfiles_'+key)
        plt.figure(figsize=(7,4));sc=plt.scatter(Z[:,0],Z[:,1],c=lt,cmap='tab20',s=4,alpha=.45);plt.colorbar(sc,label='Grupo');plt.xlabel('PC1');plt.ylabel('PC2');plt.title(key+': proyección, no prueba de separación');figure('mapa_'+key)
        # Benchmark corto repetido, sin búsqueda ni preprocesamiento.
        for repeat in range(3):
            e=estimator(family,cfg['k'],cfg['covariance']);elapsed,ok,_=fit_model(e,A)
            tick=time.perf_counter();e.predict(B);prediction=time.perf_counter()-tick
            timings.append(dict(model=family,space=space,repeat=repeat,fit_seconds=elapsed,predict_seconds=prediction,converged=ok))
    # Control sin escalar en los dos modelos originales, evaluado en geometría común.
    U=SimpleImputer(strategy='median').fit_transform(train[FEATURES])
    for family in ['KMeans','GMM']:
        cfg=next(c for c in frozen['selected'] if c['model']==family and c['space']=='original')
        e=estimator(family,cfg['k'],cfg['covariance']);_,ok,_=fit_model(e,U)
        if not ok:raise RuntimeError('No converge control sin escalar: '+family)
        labs=e.predict(U);unscaled.append(dict(model=family,ari_scaled_unscaled=float(adjusted_rand_score(labels[family+'_original'][0],labs)),silhouette_scaled_common=silhouette(common_train,labels[family+'_original'][0],2000),silhouette_unscaled_labels_common=silhouette(common_train,labs,2000)))
    for filename,value in [('comparativa',rows),('estabilidad',stability),('perfiles',profiles),('popularidad',pops),('control_escalado',unscaled),('tiempos_repetidos',timings)]:pd.DataFrame(value).to_csv(OUT/f'{filename}.csv',index=False)
    stats=pd.DataFrame(dict(skew_raw=train[FEATURES].skew(),skew_selected=pd.DataFrame(X,columns=FEATURES).skew(),iqr_outlier_fraction=((train[FEATURES]<train[FEATURES].quantile(.25)-1.5*(train[FEATURES].quantile(.75)-train[FEATURES].quantile(.25)))|(train[FEATURES]>train[FEATURES].quantile(.75)+1.5*(train[FEATURES].quantile(.75)-train[FEATURES].quantile(.25)))).mean()));stats.to_csv(OUT/'asimetria_atipicos.csv')
    train[FEATURES].describe().T.to_csv(OUT/'descriptiva.csv')
    train[FEATURES].hist(figsize=(12,8),bins=35);plt.suptitle('Distribuciones de entrenamiento en unidades originales');figure('distribuciones')
    corr=train[FEATURES].corr();corr.to_csv(OUT/'correlaciones.csv');plt.figure(figsize=(9,7));plt.imshow(corr,vmin=-1,vmax=1,cmap='RdBu_r');plt.xticks(range(10),FEATURES,rotation=90);plt.yticks(range(10),FEATURES);plt.colorbar(label='Pearson r');plt.title('Correlaciones acústicas');figure('correlaciones')
    summary=dict(preprocessing=prep,pca_components=int(pca.n_components_),pca_variance=float(pca.explained_variance_ratio_.sum()),pc1_pc2_variance=float(pca.explained_variance_ratio_[:2].sum()),preprocess_seconds=preprocess_seconds)
    dump('transformacion.json',summary)
    return pd.DataFrame(rows),pd.DataFrame(stability),pd.DataFrame(profiles),pd.DataFrame(pops),loads,labels,common_train,common_test,summary

def listening_example(train,test,labels,common_train,common_test,config):
    a,b=labels[config];low=np.flatnonzero(train.popularity.to_numpy()<=30);high=np.flatnonzero(test.popularity.to_numpy()>=70);pairs=[]
    for qi in high:
        pool=low[a[low]==b[qi]]
        if not len(pool):continue
        distance=np.linalg.norm(common_train[pool]-common_test[qi],axis=1);i=int(pool[np.argmin(distance)])
        pairs.append(dict(query_index=int(qi),reference_index=i,distance=float(distance.min()),high_song=str(test.iloc[qi].track_name),high_artist=str(test.iloc[qi].artists),high_id=str(test.iloc[qi].track_id),high_popularity=int(test.iloc[qi].popularity),low_song=str(train.iloc[i].track_name),low_artist=str(train.iloc[i].artists),low_id=str(train.iloc[i].track_id),low_popularity=int(train.iloc[i].popularity),configuration=config))
    frame=pd.DataFrame(pairs).sort_values(['distance','high_id']) if pairs else pd.DataFrame()
    frame.to_csv(OUT/'ejemplos_escucha.csv',index=False)
    if len(frame):
        r=frame.iloc[0];comparison=pd.DataFrame({'variable':FEATURES,'cancion_popular':test.iloc[int(r.query_index)][FEATURES].to_numpy(),'referencia_menor_popularidad':train.iloc[int(r.reference_index)][FEATURES].to_numpy()});comparison.to_csv(OUT/'comparacion_escucha.csv',index=False)
    return frame

def render_report(blocks):
    result=[]
    for b in blocks:
        if b.startswith('!['):
            alt,url=b[2:].split('](',1);result.append('<figure><img src="'+html.escape(url[:-1])+'" alt="'+html.escape(alt)+'"><figcaption>'+html.escape(alt)+'</figcaption></figure>')
        elif b.startswith('| '):
            lines=b.splitlines();row=lambda l,t:'<tr>'+''.join('<'+t+'>'+html.escape(v.strip())+'</'+t+'>' for v in l.strip('|').split('|'))+'</tr>'
            result.append('<div class="table"><table>'+row(lines[0],'th')+''.join(row(l,'td') for l in lines[2:])+'</table></div>')
        elif b.startswith('#'):
            level=len(b)-len(b.lstrip('#'));result.append(f'<h{level}>'+html.escape(b[level:].strip())+f'</h{level}>')
        else:
            escaped=html.escape(b)
            escaped=re.sub(r'(https://[^\s<>]+)',r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>',escaped)
            result.append('<p>'+escaped+'</p>')
    return '<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Segmentación musical — Informe mejorado</title><style>body{max-width:1120px;margin:40px auto;padding:24px;font:16px/1.65 system-ui;color:#183044}h1,h2,h3{color:#124e68}img{max-width:100%}figure{margin:24px 0}figcaption{font-size:12px}.table{overflow:auto}table{border-collapse:collapse;font-size:12px}th,td{padding:8px;border:1px solid #c8d7df}th{background:#eaf2f6}p{white-space:pre-line}@media print{figure,table{break-inside:avoid}}</style><main>'+''.join(result)+'</main></html>'

def report(audit,frozen,searches,selected,comparison,stable,profiles,pops,loads,summary,examples):
    common=comparison.query("evaluation_space=='reference_original'")
    selection=pd.DataFrame(frozen['selected']);winner=selection.sort_values('val_sil_common',ascending=False).iloc[0];key=winner.model+'_'+winner.space
    benchmark=pd.read_csv(OUT/'tiempos_repetidos.csv').groupby(['model','space'])[['fit_seconds','predict_seconds']].agg(['median','min','max']).reset_index();benchmark.columns=['_'.join(c).rstrip('_') if isinstance(c,tuple) else c for c in benchmark.columns]
    stab=stable.groupby(['model','space','kind']).ari.agg(['mean','min','max']).reset_index()
    correlations=pd.read_csv(OUT/'correlaciones.csv',index_col=0);pairs=sorted([(a,b,float(correlations.loc[a,b])) for i,a in enumerate(FEATURES) for b in FEATURES[i+1:]],key=lambda x:abs(x[2]),reverse=True)[:3]
    blocks=['# Segmentación musical: perfiles fiables, sin prometer éxitos',
        'Comparación de K-Means y GMM antes y después de PCA · ISW-222 / Bloque 3. Autor(es) y fecha de entrega: completar antes de presentar.',
        '## Resumen',f'Se reutilizan {audit["development"]} canciones de desarrollo. La selección usa {audit["inner_fit"]} para ajuste y {audit["validation"]} para validación, separados por componentes de artistas colaboradores. La prueba adicional tiene {audit["holdout"]} canciones fuera de la muestra anterior y sin artistas compartidos. Preparación elegida: {summary["preprocessing"]}. PCA conserva {summary["pca_components"]} componentes ({summary["pca_variance"]:.2%}). Recomendación fijada con validación: {key}. Popularidad nunca interviene en ajustes ni selección.',
        '## 1. Problema y aporte propio',
        '¿Cómo organizar un catálogo por perfiles sonoros interpretables y estables, y cuánto cambian al aplicar PCA? Los grupos permiten filtrar referencias acústicas para exploración musical y producción. No hay etiquetas verdaderas de perfil; género, nombre, artista y popularidad se excluyen del vector de entrenamiento. Se investiga descriptivamente si perfiles parecidos pueden alcanzar popularidades distintas.',
        'El aporte es comparar preparación, familias y reducción bajo el mismo criterio, controlar artistas compartidos y reservar una prueba adicional. Una mejora de métricas no demuestra calidad artística ni una fórmula de éxito.',
        '## 2. Datos y preparación sin fuga',
        'Fuente: Pandya, Spotify Tracks Dataset, Hugging Face. Licencia declarada en su ficha: bsd; no se atribuye una variante BSD no especificada. Se utilizan datos tabulares y no se distribuye audio. La popularidad es la registrada en el archivo, no reproducciones actuales.',
        table(pd.DataFrame([dict(variable=f,unidad='ms' if f=='duration_ms' else 'BPM' if f=='tempo' else 'dB' if f=='loudness' else '0–1',faltantes_fuente=audit['raw_missing'][f],faltantes_train=audit['training_missing'][f]) for f in FEATURES])),
        table(pd.DataFrame([dict(etapa=k,n=audit[k]) for k in ['raw_rows','unique_rows','development','inner_fit','validation','eligible_holdout','holdout']])),
        'Se conserva la primera aparición por ID sin seleccionar por popularidad. Variables fuera de rango, valores no finitos y tempo/duración no positivos pasan a faltantes. Medianas y transformaciones se ajustan solo con el subconjunto de ajuste, y se reajustan en desarrollo completo una vez congeladas las elecciones.',
        'Los grupos de artistas unen colaboraciones transitivamente; dividir solo por cadena completa de artista dejaría fugas. En la prueba adicional se excluyen IDs previos, artistas individuales de toda la muestra anterior y vectores acústicos iguales tras redondeo a siete decimales. Esto no identifica todas las versiones semánticamente duplicadas ni constituye una muestra temporal o un dataset externo.',
        table(pd.read_csv(OUT/'descriptiva.csv').rename(columns={'Unnamed: 0':'variable'})),
        '![Distribuciones en unidades originales](figuras/distribuciones.png)',
        table(pd.read_csv(OUT/'asimetria_atipicos.csv').rename(columns={'Unnamed: 0':'variable'})),
        'Los extremos IQR se describen, no se eliminan automáticamente: instrumentalidad o habla elevadas pueden ser legítimas. Yeo-Johnson transforma las distribuciones marginales y después estandariza; no garantiza gaussianidad conjunta ni mejores agrupamientos. StandardScaler iguala escalas, pero no elimina asimetría.',
        '![Correlaciones de entrenamiento](figuras/correlaciones.png)',
        '; '.join(f'{a}/{b}: r={r:+.3f}' for a,b,r in pairs)+'. Las correlaciones anticipan redundancia parcial, no autorizan a descartar información sin comparar.',
        '## 3. Protocolo y selección',
        'El protocolo se escribió antes de ejecutar la nueva búsqueda y se conserva con huella SHA-256. Esta revisión es exploratoria y está informada por la versión anterior; no se presenta como prerregistro externo. No se usa la prueba adicional para seleccionar. El test anterior ya observado tampoco selecciona.',
        table(pd.DataFrame([dict(preparacion=k,silhouette_validacion_media=v) for k,v in frozen['mean_validation_silhouette'].items()])),
        'Regla común: maximizar Silhouette en validación, calculado siempre en las diez variables estandarizadas por el escalador de referencia. Se exige al menos 2 % por grupo en ajuste y validación. Dentro de 0,005 del máximo se prefiere menor K; a igualdad de K, menor BIC para GMM. Para cambiar de preparación se exige ganancia media superior a 0,005 en las cuatro configuraciones. Es una regla explícita de parsimonia, no una prueba de significación.',
        'BIC y AIC se calculan como diagnósticos de densidad, pero no se priorizan sobre la utilidad de segmentación. Este cambio de objetivo respecto a la versión anterior se declara; no prueba que la densidad GMM ahora esté mejor ajustada. BIC no se compara entre espacios o transformaciones diferentes. La geometría común favorece por definición conservar la representación estandarizada original.',
        table(selected[['preprocessing','model','space','k','covariance','val_sil_common','bic','min_train_fraction','min_val_fraction']])]
    for prep in PROTOCOL['preprocessing']:
        for family in ['KMeans','GMM']:
            for space in ['original','pca']:blocks.append(f'![Selección {prep}/{family}/{space}](figuras/busqueda_{prep}_{family}_{space}.png)')
    blocks+=['## 4. PCA e interpretación',f'Umbral fijado en 90 %: se retienen {summary["pca_components"]} componentes y {summary["pca_variance"]:.2%}. PC1+PC2 muestran solo {summary["pc1_pc2_variance"]:.2%}; no son todo el espacio del modelo.',
        '![Varianza acumulada de PCA](figuras/varianza_pca.png)',table(loads.iloc[:,:2].reset_index(names='variable'))]
    for pc in ['PC1','PC2']:
        dom=loads[pc].abs().nlargest(4).index
        blocks.append(pc+': '+', '.join(f'{v} ({loads.loc[v,pc]:+.3f})' for v in dom)+'. El componente contrasta los atributos positivos y negativos indicados. Si se selecciona Yeo-Johnson, las cargas corresponden a características transformadas, no a relaciones lineales con las unidades físicas originales. El signo global es arbitrario.')
    blocks+=['PC1 contrapone intensidad y nivel sonoro (energy y loudness) frente a carácter acústico (acousticness). En términos musicales, resume un eje de sonido más intenso/producido frente a textura más acústica; no clasifica automáticamente géneros ni calidad.',
        'PC2 contrapone valencia y bailabilidad frente a instrumentalidad y duración. Describe un eje de positividad sonora y ritmo bailable frente a formatos más largos o instrumentales. Son interpretaciones descriptivas de las cargas observadas, no emociones del oyente ni una receta de éxito.',
        '## 5. Tabla comparativa obligatoria y comparación justa',
        'Original significa diez características preparadas, sin PCA. Native usa la geometría de cada ajuste; reference_original siempre utiliza las diez características con StandardScaler de referencia. Solo estas últimas filas permiten comparar separaciones en la misma geometría. Se incluyen entrenamiento y prueba, hiperparámetros, grupos, tres métricas, tiempos y ARI. Ruido=0 porque ambos asignan todas las canciones; no equivale a detectar ausencia de anomalías.',table(comparison),
        'Silhouette: mayor mejor, cohesión frente a separación. Davies-Bouldin: menor mejor, similitud entre grupos. Calinski-Harabasz: mayor mejor, dispersión entre grupos respecto a dispersión interna. Favorecen agrupamientos compactos y no son medidas de gusto o éxito. Silhouette usa hasta 2.000 observaciones con semilla fija; las otras métricas usan el conjunto completo.',
        '## 6. Estabilidad y costo',table(stab),
        'Cuatro semillas y cuatro submuestras de 80 % por configuración; ARI entre pares sobre las mismas canciones de prueba. Transformación y PCA permanecen fijos: mide estabilidad condicional de los modelos. No se selecciona con esta prueba. La incertidumbre de toda la preparación requiere remuestrear el pipeline completo.',table(benchmark),
        f'Preparación final compartida (incluye representación de referencia y PCA): {summary["preprocess_seconds"]:.4f} s. Los tiempos repetidos de modelos excluyen búsqueda y preparación, usan un hilo numérico y no son una garantía de rendimiento en otro equipo.',
        '## 7. Interpretación y acciones por perfil']
    for cfg in frozen['selected']:
        family,space=cfg['model'],cfg['space'];name=family+'_'+space
        group=profiles.query('model==@family and space==@space')
        blocks += ['### '+name,table(group.drop(columns=['model','space'])),f'![Perfiles originales {name}](figuras/perfiles_{name}.png)',f'![Mapa PC1/PC2 {name}](figuras/mapa_{name}.png)']
        for r in group.itertuples():
            energy='intenso' if r.energy>=.65 else 'suave' if r.energy<.35 else 'intermedio';texture='acústico' if r.acousticness>=.6 else 'instrumental' if r.instrumentalness>=.5 else 'mixto'
            blocks.append(f'Grupo {r.cluster}: {energy}, {texture}, {r.tempo:.1f} BPM, {r.duration_ms/60000:.2f} min; {r.n} canciones. Acción: filtrar referencias con esta combinación y contrastarlas por escucha. No prescribe una mezcla, género verdadero o público objetivo.')
    blocks+=['### Popularidad como análisis secundario',table(pops),
        'Las medianas y cuartiles describen el archivo. Las diferencias no garantizan éxito individual ni prueban causalidad. La validación por artistas cambia la población: no se comparan sin más estas cifras con las del test anterior.',
        '## 8. Las doce respuestas de la rúbrica',
        '### 1. Escalado',table(pd.read_csv(OUT/'control_escalado.csv')),
        'Duración en milisegundos domina distancias sin escalar frente a variables 0–1. El control conserva hiperparámetros y evalúa sus etiquetas en la misma geometría común. El ARI cuantifica el cambio de partición y evita concluir por un Silhouette medido con otra escala.',
        '### 2. Elección de hiperparámetros',table(selection[['model','space','k','covariance','val_sil_common','bic']]),
        'La búsqueda y sus curvas abarcan K=2–10,12,16,20,24 y covarianzas full/diag para GMM. Se prioriza separación de validación con tamaños mínimos y parsimonia; BIC explica ajuste de densidad, distinto del objetivo de segmentación. La tabla completa conserva todos los intentos, no solo ganadores.',
        '### 3. Sesgo de las métricas',table(common.query("split=='test'")[[ 'model','space','silhouette','davies_bouldin','calinski_harabasz']]),
        'El objetivo euclidiano y el criterio favorecen a K-Means y a gaussianas compactas. Las nubes superpuestas en los mapas advierten que los perfiles pueden ser discretizaciones de un continuo. La proyección PC1/PC2 no prueba separación en todas las dimensiones; contrastar con estas métricas y no solo colores.',
        '### 4. Ruido y atípicos',table(pd.read_csv(OUT/'asimetria_atipicos.csv').rename(columns={'Unnamed: 0':'variable'})),
        'No se utilizó DBSCAN. K-Means y GMM asignan todos los puntos: ruido 0 % es una propiedad del método. Los atípicos pueden desplazar centroides y covarianzas. No se eliminan perfiles musicales válidos por IQR; se compara una transformación marginal predefinida y se describen sus límites.',
        '### 5. Componentes principales',f'{summary["pca_components"]} componentes, varianza {summary["pca_variance"]:.2%}; dos primeras dimensiones {summary["pc1_pc2_variance"]:.2%}.',table(loads.iloc[:,:2].reset_index(names='variable')),
        'Las mayores cargas absolutas de la sección 4 definen los contrastes acústicos; se interpretan con sus signos. La varianza retenida no es porcentaje de información musical ni de éxito explicado.',
        '### 6. Efecto de la reducción']
    for family in ['KMeans','GMM']:
        a=common.query("model==@family and split=='test' and space=='original'").iloc[0];b=common.query("model==@family and split=='test' and space=='pca'").iloc[0]
        blocks.append(f'{family}, prueba en geometría común: Silhouette {a.silhouette:.4f} → {b.silhouette:.4f}; Davies-Bouldin {a.davies_bouldin:.4f} → {b.davies_bouldin:.4f}; Calinski-Harabasz {a.calinski_harabasz:.2f} → {b.calinski_harabasz:.2f}. PCA puede quitar redundancia o descartar diferencias útiles; las cifras no identifican por sí solas cuál causa actuó. Diez variables no justifican invocar automáticamente maldición de dimensionalidad.')
    blocks+=['### 7. Comparación justa',table(comparison.query("split=='train'")[[ 'model','space','evaluation_space','silhouette','davies_bouldin','calinski_harabasz']]),
        'Comparar Native original con Native PCA mezcla geometrías. La conclusión de separación utiliza reference_original. Cuando las conclusiones difieren, se prioriza esta geometría declarada y se reconoce el sesgo a favor de preservarla.',
        '### 8. Cambio de asignaciones',table(common.query("space=='pca'")[[ 'model','split','ari_vs_original']]),
        'ARI=1 implica particiones equivalentes aun con etiquetas permutadas; cercano a cero es acuerdo compatible con azar. Puede ser negativo. Se compara el mismo conjunto en cada fila y no popularidad o género.',
        '### 9. Estabilidad',table(stab)]
    for space in ['original','pca']:
        s=stable.query('space==@space').groupby('model').ari.mean().sort_values(ascending=False)
        blocks.append(f'En {space}, mayor ARI medio condicional: {s.index[0]}={s.iloc[0]:.4f}; '+', '.join(f'{k}={v:.4f}' for k,v in s.iloc[1:].items())+'. K-Means puede variar por centroides iniciales; GMM añade sensibilidad de covarianzas y máximos locales. Un ARI alto no prueba que los grupos sean verdaderos.')
    blocks+=['### 10. Costo computacional',table(benchmark),
        'Con 100 veces más observaciones no se extrapolan segundos ciegamente. K-Means escala aproximadamente O(n·K·d·iteraciones); GMM full añade operaciones de covarianza O(n·K·d²) y factorización O(K·d³) por iteración. Reducir d puede ayudar a GMM, pero depende también de convergencia. Silhouette completo tiene costo cuadrático en n; mantener muestreo. Incluir ajuste/transformación PCA antes de afirmar ahorro total.',
        '### 11. Visualización no lineal',f'No se ejecutó UMAP ni t-SNE: son opcionales. PCA muestra {summary["pc1_pc2_variance"]:.2%} en dos ejes y no todo el espacio. Islas en una visualización no lineal hipotética no demostrarían grupos naturales. t-SNE altera distancias globales y densidades, depende de parámetros y no es entrada de este clustering.',
        '### 12. Recomendación final',f'Se recomienda provisionalmente {key}, elegido en validación con Silhouette común={winner.val_sil_common:.4f}; no se cambia por los resultados de prueba ni popularidad. Revisar conjuntamente las tres métricas, estabilidad, tamaños y perfiles, y reconocer que diferencias pequeñas no demuestran superioridad estadística.',
        'Limitaciones: muestra histórica de conveniencia; exclusión por artistas modifica la población y no equivale a evaluación temporal; versiones no detectadas; características agregadas omiten melodía, letra y secciones; sin evaluación de oyentes. Con más tiempo: validación temporal/externa, remuestreo de toda la preparación, protocolo humano y medidas longitudinales de exposición/promoción.',
        '## 9. Cierre con canciones reales']
    if len(examples):
        r=examples.iloc[0];blocks += [f'Hay {len(examples)} consultas de popularidad ≥70 con al menos una referencia ≤30 dentro del mismo perfil. La pareja siguiente minimiza su distancia en las diez variables estandarizadas; es un ejemplo deliberadamente seleccionado para ilustrar similitud con popularidades distintas, no prueba representativa de todas las canciones.',table(examples.head(3).drop(columns=['query_index','reference_index'])),table(pd.read_csv(OUT/'comparacion_escucha.csv')),
            'Abrir las canciones legalmente en Spotify y comprobar mediante escucha si la similitud percibida coincide con las características. No se seleccionó un tramo del audio ni se analizó estructura verso/estribillo; el dataset no contiene audio. Si al escuchar no parecen similares, explicar qué no capturan las variables y no ocultar ese resultado.',f'Canción A: https://open.spotify.com/track/{r.high_id}\nCanción B: https://open.spotify.com/track/{r.low_id}']
    else:blocks.append('No hay pareja que cumpla los umbrales predefinidos; no se relajaron tras ver los resultados.')
    blocks+=['### Evaluación humana propuesta, no realizada',
        'Consultas fijadas antes de escuchar, sugerencias original/PCA con etiquetas ocultas, orden alternado y fragmentos de igual duración elegidos de forma consistente. Voluntarios con consentimiento e identificadores anónimos puntúan similitud y utilidad de 1 a 5. Reportar participantes, consultas, distribuciones y comentarios negativos; una muestra pequeña no generaliza a todos los oyentes. No hay puntuaciones humanas inventadas.',
        '## 10. Qué mejoró y qué no puede afirmarse',
        'Se añadió selección separada por artistas, comparación acotada de preparación, tamaños mínimos, búsqueda hasta 24 grupos, regla común orientada a segmentación, prueba adicional sin artistas previos y benchmarks repetidos. No se cambió la métrica para demostrar éxito: se declaró el cambio respecto al objetivo BIC anterior y se mantienen sus diagnósticos.',
        'Una nueva Silhouette no es directamente comparable con la anterior cuando cambia la población, el ajuste o la geometría. La comparación controlada entre StandardScaler y Yeo-Johnson es la tabla de validación con los mismos datos y referencia. El test reservado es una comprobación posterior, no otra oportunidad de ajuste. Si no mejora, debe reportarse.',
        '## 11. Reproducibilidad y asistencia de IA',
        'Ejecutar Proyecto_Mejorado.ipynb completo o python mejorar_proyecto.py desde esta carpeta. Semillas, criterios, búsqueda completa, IDs de las particiones, huellas y versiones acompañan la entrega. No hace falta descargar audio, abrir una API o tener internet para repetir con el CSV incluido. Se utilizó ChatGPT/Codex para código, documentación y análisis; los estudiantes deben revisar y declarar la asistencia. La preparación no garantiza una calificación.',
        '## Referencias',
        'Pandya, M. (s. f.). Spotify Tracks Dataset [Conjunto de datos]. Hugging Face. https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset',
        'Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825–2830. https://jmlr.org/papers/v12/pedregosa11a.html',
        'Scikit-learn developers. (s. f.). PowerTransformer y GroupShuffleSplit [Documentación]. https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.PowerTransformer.html ; https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html']
    # Comparación controlada sobre las mismas canciones y geometría de referencia.
    old=pd.read_csv(ROOT/'data/referencia_anterior/comparativa.csv').query("split=='train' and evaluation_space=='original'")
    revised=common.query("split=='train'")
    history=old[['model','space','groups','silhouette']].merge(revised[['model','space','groups','silhouette']],on=['model','space'],suffixes=('_anterior','_revision'))
    history['delta_silhouette']=history.silhouette_revision-history.silhouette_anterior
    history.to_csv(OUT/'comparacion_controlada_anterior.csv',index=False)
    position=blocks.index('## 10. Qué mejoró y qué no puede afirmarse')+1
    gain=frozen['mean_validation_silhouette']['yeo_johnson']-frozen['mean_validation_silhouette']['standard']
    blocks[position:position]=[table(history),
        'Esta comparación usa las mismas 8.000 canciones, las mismas diez variables y StandardScaler de referencia. La revisión modifica preparación y selección: no permite atribuir toda la diferencia solo a Yeo-Johnson. Se observa mejora geométrica en GMM y empeoramiento en K-Means; no es una mejora universal, ni demuestra mejor ajuste de densidad o utilidad para oyentes.',
        f'La ventaja media de Yeo-Johnson en validación fue {gain:+.5f}, frente al umbral predefinido de 0,005. Es pequeña y está cerca del umbral; no se evaluó significación estadística ni robustez a múltiples particiones de validación. No debe presentarse como una superioridad contundente.']
    if len(examples):
        r=examples.iloc[0]
        comparison_html=table(pd.read_csv(OUT/'comparacion_escucha.csv'))
        cards=''.join('<article><p>'+label+'</p><h2>'+html.escape(str(r[prefix+'_song']))+'</h2><p>'+html.escape(str(r[prefix+'_artist']))+'</p><strong>Popularidad histórica '+str(int(r[prefix+'_popularity']))+'/100</strong><p><a href="https://open.spotify.com/track/'+html.escape(str(r[prefix+'_id']))+'" target="_blank" rel="noopener noreferrer">Abrir en Spotify</a></p></article>' for label,prefix in [('Canción A','high'),('Canción B','low')])
        document='<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cierre musical</title><style>body{max-width:1000px;margin:40px auto;padding:24px;background:#0c1524;color:#edf4ff;font:18px/1.6 system-ui}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:24px}article{background:#17263b;border:1px solid #38516c;border-radius:16px;padding:24px}a{color:#9ff0c8}strong{font-size:24px}.note{color:#b7c8db;font-size:15px}</style><h1>Sonidos cercanos. Popularidades distintas.</h1><section>'+cards+'</section><p>Distancia en las diez características estandarizadas: '+f'{r.distance:.3f}'+'</p><p class="note">Ejemplo elegido por la menor distancia entre '+str(len(examples))+' consultas elegibles: popularidad ≥70 frente a ≤30, mismo perfil. Es una ilustración deliberada, no una prueba representativa ni una garantía de similitud perceptiva.</p><p>Escucha fragmentos de igual duración y contrasta lo que percibes con los datos. Si suenan diferentes, identifica qué no capturan estas características.</p><p class="note">No se incluye audio ni se analizan versos, estribillos o melodía. Los enlaces requieren conexión.</p><p><a href="informe.html">Volver al informe completo</a></p></html>'
        (OUT/'cierre_escucha.html').write_text(document,'utf-8')
    (OUT/'informe.md').write_text('\n\n'.join(blocks),'utf-8');(OUT/'informe.html').write_text(render_report(blocks),'utf-8')
    return key

def run():
    OUT.mkdir(exist_ok=True);(OUT/'figuras').mkdir(exist_ok=True)
    (OUT/'protocolo_ejecutado.json').write_text((ROOT/'protocolo_mejora.json').read_text('utf-8'),'utf-8')
    start=time.perf_counter()
    train,fit,val,test,audit=splits();print('Particiones verificadas: '+str({k:audit[k] for k in ['development','inner_fit','validation','holdout','eligible_holdout']}),flush=True)
    frozen,searches,selected=search(fit,val)
    print('Selección congelada: '+frozen['preprocessing'],flush=True)
    comparison,stable,profiles,pops,loads,labels,common_train,common_test,summary=final_experiment(train,test,frozen)
    config=pd.DataFrame(frozen['selected']).sort_values('val_sil_common',ascending=False).iloc[0];key=config.model+'_'+config.space
    examples=listening_example(train,test,labels,common_train,common_test,key)
    report(audit,frozen,searches,selected,comparison,stable,profiles,pops,loads,summary,examples)
    versions={p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','scikit-learn','matplotlib','nbformat','threadpoolctl']};versions['python']=platform.python_version();dump('versiones.json',versions)
    assert len(comparison)==16 and len(stable)==48
    assert np.isfinite(comparison[['silhouette','davies_bouldin','calinski_harabasz']]).all().all()
    assert len(train)>=500 and len(FEATURES)>=8 and summary['pca_variance']>=.9
    text=(OUT/'informe.md').read_text('utf-8');assert re.findall(r'^### (\d+)\. ',text,re.M)==[str(i) for i in range(1,13)]
    assert not frozen['selection_uses_holdout'] and not frozen['selection_uses_popularity']
    dump('validacion.json',dict(status='passed',comparison_rows=len(comparison),stability_pairs=len(stable),questions=12,shared_artists_fit_validation=0,shared_artists_previous_holdout=0,holdout_ids_not_previously_used=True,protocol_sha256=frozen['protocol_sha256'],elapsed_seconds=time.perf_counter()-start))
    print(comparison.query("split=='test' and evaluation_space=='reference_original'")[[ 'model','space','groups','silhouette','davies_bouldin','calinski_harabasz']].to_string(index=False),flush=True)
    print('FINALIZADO: resultados/informe.html',flush=True)
    # La pregunta principal se responde después de congelar los modelos.
    from analizar_popularidad import ejecutar_objetivo
    ejecutar_objetivo()
    from analizar_contextos import ejecutar_ampliacion
    ejecutar_ampliacion()

if __name__=='__main__':
    with threadpool_limits(limits=1):run()
