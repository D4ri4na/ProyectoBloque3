"""Ampliación controlada: mayor granularidad y contextos de género posteriores al ajuste."""
from pathlib import Path
import json
import hashlib
import re
import html
import itertools
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits
import mejorar_proyecto as core
import analizar_popularidad as pop

CTX_ROOT=Path(__file__).resolve().parent
CTX_OUT=CTX_ROOT/'resultados/ampliacion'
CTX_P=json.loads((CTX_ROOT/'protocolo_contextos.json').read_text('utf-8'))

def ctx_save(name,value):
    (CTX_OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)),'utf-8')

def ctx_figure(name):
    plt.tight_layout();plt.savefig(CTX_OUT/'figuras'/f'{name}.png',dpi=140,bbox_inches='tight');plt.close()

def ctx_tags(raw,frames):
    tags=raw.groupby('track_id',sort=True).track_genre.agg(lambda values:set(str(v).strip().casefold() for v in values if pd.notna(v))).to_dict()
    result=[]
    for frame in frames:
        result.append({name:np.array([bool(tags.get(t,set())&set(genres)) for t in frame.track_id]) for name,genres in CTX_P['contexts'].items()})
    return result

def ctx_search(fit,val,preprocessing):
    prep=core.pipeline(preprocessing).fit(fit[core.FEATURES]);A=prep.transform(fit[core.FEATURES]);B=prep.transform(val[core.FEATURES])
    ref=core.pipeline('standard').fit(fit[core.FEATURES]);V=ref.transform(val[core.FEATURES])
    pca=PCA(n_components=.9,svd_solver='full').fit(A)
    rows=[];choices=[]
    for family in ['KMeans','GMM']:
        for space,X,T in [('original',A,B),('pca',pca.transform(A),pca.transform(B))]:
            block=[]
            for k in CTX_P['k_grid']:
                for cov in (['NA'] if family=='KMeans' else CTX_P['covariances']):
                    est=core.estimator(family,k,cov);seconds,ok,nwarn=core.fit_model(est,X);lt=est.predict(X);lv=est.predict(T)
                    min_train=float(np.bincount(lt,minlength=k).min()/len(lt));min_val=float(np.bincount(lv,minlength=k).min()/len(lv))
                    sil=core.silhouette(V,lv)
                    row=dict(model=family,space=space,k=k,covariance=cov,converged=ok,warnings=nwarn,min_train_fraction=min_train,min_val_fraction=min_val,val_sil_common=sil,train_sil_native=core.silhouette(X,lt),bic=float(est.bic(X)) if family=='GMM' else np.nan,inertia=float(est.inertia_) if family=='KMeans' else np.nan,fit_seconds=seconds)
                    row['eligible']=bool(ok and np.isfinite(sil) and min_train>=CTX_P['min_cluster_fraction'] and min_val>=CTX_P['min_cluster_fraction']);rows.append(row);block.append(row)
            d=pd.DataFrame(block);eligible=d.loc[d.eligible]
            if eligible.empty:raise RuntimeError('Ningún modelo fino elegible: '+family+'/'+space)
            near=eligible.loc[eligible.val_sil_common>=eligible.val_sil_common.max()-CTX_P['silhouette_tolerance']]
            best=near.sort_values(['k','bic'],na_position='last').iloc[0];choices.append(best.to_dict())
            fig,axs=plt.subplots(1,2,figsize=(10,3.7))
            for cov,g in d.groupby('covariance'):
                axs[0].plot(g.k,g.val_sil_common,'o-',label=cov);axs[1].plot(g.k,g.bic if family=='GMM' else g.inertia,'o-',label=cov)
            axs[0].set(xlabel='K',ylabel='Silhouette validación común',title=family+'/'+space);axs[1].set(xlabel='K',ylabel='BIC' if family=='GMM' else 'Inercia');axs[0].legend();axs[1].legend();ctx_figure('busqueda_'+family+'_'+space)
            print(f'Fino {family}/{space}: K={int(best.k)}; validación={best.val_sil_common:.4f}',flush=True)
    pd.DataFrame(rows).to_csv(CTX_OUT/'busqueda.csv',index=False);pd.DataFrame(choices).to_csv(CTX_OUT/'seleccion.csv',index=False)
    return choices

def ctx_leader(frame,labels,minimum):
    rows=[]
    for label in sorted(np.unique(labels)):
        f=frame.loc[np.asarray(labels)==label];valid=f.popularity.dropna()
        if len(valid)>=minimum and len(frame)-len(f)>=minimum:rows.append((float((valid>=70).mean()),int(label)))
    if not rows:return None
    return sorted(rows,key=lambda x:(-x[0],x[1]))[0][1]

def ctx_effect(frame,labels,leader,alpha=.05,min_side=1):
    valid=frame.popularity.notna().to_numpy();f=frame.loc[valid].reset_index(drop=True);labs=np.asarray(labels)[valid]
    inside=labs==leader;high=f.popularity.to_numpy()>=70;n=int(inside.sum());rest=int((~inside).sum());hits=int((inside&high).sum());total_high=int(high.sum())
    rate=hits/n if n else np.nan;other=float(high[~inside].mean()) if rest else np.nan;base=float(high.mean()) if len(f) else np.nan
    result=dict(n=len(f),n_profile=n,high_count=hits,total_high=total_high,profile_rate=rate,rest_rate=other,global_rate=base,lift=rate/base if base else np.nan,coverage=n/len(f) if len(f) else np.nan,capture=hits/total_high if total_high else np.nan,difference=rate-other,diff_low=np.nan,diff_high=np.nan,lift_low=np.nan,lift_high=np.nan,alpha=alpha,status='ok')
    if min(n,rest)<min_side:result['status']='muestra insuficiente';return result
    if not total_high:result['status']='sin casos de alta popularidad';return result
    _,groups=np.unique(core.artist_groups(f),return_inverse=True);ng=int(groups.max()+1);counts=np.zeros((ng,4))
    for col,values in enumerate([inside,inside&high,~inside,(~inside)&high]):np.add.at(counts[:,col],groups,values.astype(float))
    rng=np.random.default_rng(CTX_P['bootstrap_seed']);differences=[];lifts=[]
    for start in range(0,CTX_P['bootstrap'],100):
        draw=counts[rng.integers(0,ng,size=(min(100,CTX_P['bootstrap']-start),ng))].sum(axis=1)
        draw=draw[(draw[:,0]>0)&(draw[:,2]>0)]
        r1=draw[:,1]/draw[:,0];r0=draw[:,3]/draw[:,2];global_r=(draw[:,1]+draw[:,3])/(draw[:,0]+draw[:,2])
        differences.extend(r1-r0);ok=global_r>0;lifts.extend(r1[ok]/global_r[ok])
    result['diff_low'],result['diff_high']=map(float,np.quantile(differences,[alpha/2,1-alpha/2]))
    result['lift_low'],result['lift_high']=map(float,np.quantile(lifts,[alpha/2,1-alpha/2]))
    return result

def ctx_new_test(raw):
    previous=core.clean_data(pd.concat([pd.read_csv(CTX_ROOT/'data/referencia_anterior/train.csv'),pd.read_csv(CTX_ROOT/'data/referencia_anterior/test.csv'),pd.read_csv(CTX_ROOT/'resultados/prueba_reservada.csv'),pd.read_csv(CTX_ROOT/'resultados/prueba_objetivo_popularidad.csv')],ignore_index=True))
    clean=core.clean_data(raw);used=core.artist_union(previous)
    mask=(~clean.track_id.isin(previous.track_id))&clean.artists.map(lambda s:bool(core.artists(s)) and not bool(core.artists(s)&used))
    mask &= ~np.isin(core.signatures(clean),core.signatures(previous));pool=clean.loc[mask]
    if len(pool)<CTX_P['new_evaluation_minimum']:raise ValueError('Pocas canciones adicionales disponibles con las exclusiones fijadas')
    test=pool.sample(n=min(len(pool),CTX_P['new_evaluation_size']),random_state=CTX_P['new_evaluation_seed']).reset_index(drop=True)
    assert not core.artist_union(previous)&core.artist_union(test)
    assert not set(previous.track_id)&set(test.track_id)
    assert not set(core.signatures(previous))&set(core.signatures(test))
    test.to_csv(CTX_OUT/'prueba_nueva.csv',index=False)
    return test,len(pool)

def ctx_report(base,frozen,comparison,effects,contexts,traits,stability,summary,counts):
    primary=summary['primary'];fine=effects.query('strategy=="fino" and configuration==@primary').iloc[0];baseline=effects.query('strategy=="referencia"').iloc[0]
    if fine.diff_low>0:verdict='El perfil fino candidato presenta mayor concentración en esta evaluación adicional, con un intervalo de diferencia completamente positivo.'
    elif fine.diff_high<0:verdict='La ventaja del perfil fino candidato se invierte en la evaluación adicional.'
    else:verdict='No se confirma una mayor concentración global del perfil fino candidato: su intervalo incluye cero.'
    supported=contexts.loc[(contexts.status=='ok')&(contexts.diff_low>0)] if len(contexts) else pd.DataFrame()
    new_result=dict(primary=primary,verdict=verdict,profile_rate=float(fine.profile_rate),global_rate=float(fine.global_rate),lift=float(fine.lift),difference_pp=float(100*fine.difference),difference_ci_pp=[float(100*fine.diff_low),float(100*fine.diff_high)],baseline_lift=float(baseline.lift),supported_contexts=supported.context.tolist() if len(supported) else [],context_claims_multiplicity_adjusted=True,n_new_evaluation=summary['n_new_evaluation'])
    blocks=['# ¿Existen perfiles sonoros que concentren canciones de alta popularidad y qué características los distinguen?',
        'Ampliación: perfiles más detallados y contraste por contextos de género. Se conserva la referencia anterior y la comparación K-Means/GMM antes y después de PCA.',
        '## Resumen actualizado',
        f'La configuración fina principal, {primary}, se eligió por calidad geométrica de validación sin consultar popularidad. El candidato identificado en entrenamiento presenta {fine.profile_rate:.2%} de canciones con popularidad ≥70 frente a {fine.global_rate:.2%} global en {summary["n_new_evaluation"]} canciones adicionales: lift {fine.lift:.2f}; diferencia frente al resto {100*fine.difference:+.2f} pp, IC95 [{100*fine.diff_low:+.2f}, {100*fine.diff_high:+.2f}]. {verdict}',
        f'La referencia de dos grupos presenta lift {baseline.lift:.2f} en estas mismas canciones. Los perfiles cubren conjuntos distintos: revisar cobertura y captura de canciones populares antes de interpretar una mayor concentración como mejora útil.',
        f'El candidato fino abarca {fine.coverage:.1%} de las canciones y contiene {fine.capture:.1%} de las canciones ≥70. Aun así, {1-fine.profile_rate:.1%} de sus canciones no alcanza ese umbral. Lift indica concentración relativa, no precisión predictiva.',
        '## 1. Ampliación y criterios fijados',
        'Hipótesis: dos grupos amplios pueden ocultar asociaciones dentro de perfiles más específicos o de contextos musicales. Se exploran K=3,4,5,6,8,10 para los dos algoritmos y espacios. Este brazo exige mayor granularidad deliberadamente; no se afirma que mejorar la popularidad requiera más grupos ni que su Silhouette deba superar al de K=2.',
        'Se conserva la preparación previamente congelada. Selección: Silhouette de validación en geometría común, grupos mínimos de 2 %, tolerancia 0,005 y preferencia por K menor y luego BIC. Modelo principal por mayor Silhouette de validación. El conjunto de validación ya fue observado en etapas previas; esta ampliación es exploratoria y usa otra evaluación adicional para contrastar candidatos.',
        'Solo después del ajuste se escoge el perfil de mayor tasa ≥70 en entrenamiento, con al menos 200 observaciones. Los contextos emplean un mínimo de 400 canciones de entrenamiento y 80 por perfil/resto. La lista de contextos y sus reglas se fijaron antes de observar sus tasas. No se seleccionan algoritmos, K o contextos por los resultados de prueba.',
        core.table(pd.DataFrame(frozen['selected'])[['model','space','k','covariance','val_sil_common']]),
        '## 2. Otra evaluación y comparación controlada',
        f'Se reservaron {summary["n_new_evaluation"]} canciones de {summary["eligible_pool"]} elegibles, excluyendo los 14.000 registros usados antes, sus nombres de artistas y los vectores acústicos exactos a siete decimales. El muestreo es uniforme, sin enriquecer artificialmente con canciones populares. Los nombres no son identificadores universales: alias pueden escapar de la exclusión.',
        'Tasa = canciones ≥70 / canciones con popularidad válida. Lift = tasa del perfil / tasa global del mismo conjunto. Cobertura = fracción del catálogo incluida en el perfil. Captura = fracción de todas las canciones ≥70 que están en él. No son precisión predictiva ni efectos causales.',
        core.table(effects),
        '![Concentración y cobertura en la nueva evaluación](ampliacion/figuras/concentracion.png)',
        'Las cuatro configuraciones finas comparten observaciones; solo la principal fija el contraste global primario. El resto es exploratorio. Los intervalos remuestrean componentes de artistas completos y son condicionales a los modelos ajustados, no a todo el pipeline.',
        'La diferencia entre lift fino y lift de referencia se presenta descriptivamente. El contraste con intervalo corresponde al candidato frente al resto de canciones, no a una prueba formal de superioridad entre ambos algoritmos.',
        '## 3. Contextos musicales: contraste posterior al clustering',
        'El CSV no contiene año, idioma ni estructura del audio. Se utilizan familias editoriales explícitas: electrónica, rock/metal, pop, hip-hop/R&B, latina y acústica/folk/country. Se recuperan todas las etiquetas brutas por ID, en lugar de conservar solo la primera. Una canción puede pertenecer a varios contextos: sus tamaños no se suman y no son confirmaciones independientes.',
        'Género no entra al vector acústico ni determina los hiperparámetros. Dentro de cada contexto elegible se escoge el candidato solo en entrenamiento, entre los perfiles del modelo fino principal. En prueba se exigen 150 canciones del contexto y 30 por candidato/resto; los casos insuficientes se reportan, no se interpretan como ausencia de asociación.',
        core.table(counts),core.table(contexts) if len(contexts) else 'No hubo contextos con tamaños de entrenamiento suficientes.',
        f'Los contextos secundarios utilizan intervalos bootstrap Bonferroni: alfa=0,05/{max(len(frozen["contexts"]),1)} según los contextos elegibles fijados en entrenamiento. La corrección es una aproximación por remuestreo; reduce hallazgos casuales al explorar varios contextos, pero no convierte esta revisión en un estudio causal o externo.',
        '![Contrastes por contexto con corrección múltiple](ampliacion/figuras/contextos.png)',
        ('Contextos con intervalo corregido completamente positivo: '+', '.join(supported.context)+'. Son asociaciones condicionadas a este diseño, no recetas de éxito.') if len(supported) else 'Ningún contexto evaluable conserva un intervalo corregido completamente positivo.',
        '### Sensibilidad descriptiva del candidato principal',core.table(pd.read_csv(CTX_OUT/'sensibilidad.csv')),
        'Se mantiene el candidato elegido con umbral 70. Los umbrales 60/80 son comprobaciones descriptivas, no nuevas oportunidades de seleccionar un modelo o declarar confirmación sin sus propios intervalos.',
        '## 4. Rasgos de los perfiles candidatos',core.table(traits),
        'Las medianas están en unidades originales. Las diferencias perfil−resto, estandarizadas por la DE de entrenamiento, describen qué distingue al grupo. No estiman cuánto subiría la popularidad al modificar energía, tempo u otro atributo.',
        '![Rasgos del candidato principal](ampliacion/figuras/rasgos.png)',
        '## 5. Calidad y estabilidad de la segmentación ampliada',core.table(comparison),
        'Las filas reference_original usan el mismo escalador de referencia y las mismas canciones para comparar modelos y PCA. Native usa la geometría de cada modelo. Métricas de contextos o muestras distintas no se comparan directamente. Ruido=0 es asignación completa, no ausencia comprobada de anomalías.',
        'Los tiempos de la ampliación corresponden al ajuste actual y a predicción de su nueva muestra; la referencia anterior predijo 2.000 canciones en otra ejecución. No comparar esos segundos como si fueran un benchmark con el mismo tamaño de prueba y carga del equipo.',
        core.table(pd.read_csv(CTX_OUT/'todos_los_perfiles.csv')),
        '![Mapa del modelo fino principal](ampliacion/figuras/mapa_principal.png)',
        'La proyección muestra PC1 y PC2; el clustering PCA utiliza todos los componentes retenidos. La separación visual no sustituye las métricas ni demuestra categorías musicales naturales.',
        core.table(stability.groupby(['model','space','kind']).ari.agg(['mean','min','max']).reset_index()),
        f'PCA de la ampliación conserva {summary["pca_components"]} componentes y {summary["pca_variance"]:.2%} de varianza. La preparación y PCA se ajustan solo con entrenamiento.',
        '## 6. Interpretación final y límites',verdict,
        'Un perfil más pequeño puede concentrar más canciones populares pero abarcar menos éxitos totales. La comparación informa concentración, cobertura, captura y separación; no se elige una historia mirando solo el mejor número. Si no mejora, el resultado se conserva.',
        'Persisten límites: popularidad histórica de conveniencia; pocas canciones ≥70; falta de exposición, promoción, fecha e idioma; atributos agregados sin melodía o estructura; candidatos seleccionados tras observar entrenamiento; intervalos condicionales y contextos solapados. No se afirma que no exista ningún patrón posible si este diseño no lo confirma.',
        '## 7. Referencia experimental y doce respuestas de la rúbrica']
    start=base.index('## 7. Experimento obligatorio de clustering y PCA');end=base.index('## 9. Cierre de la presentación')
    method=base[start:end].replace('## 7. Experimento obligatorio de clustering y PCA','### Experimento de referencia conservado')
    method=method.replace('### 12. Recomendación final','### 12. Recomendación final\n\nLa ampliación se interpreta con las secciones 2–6 anteriores. La recomendación y cifras de referencia siguientes corresponden al experimento anterior de 2.000 canciones, no a la nueva evaluación de la ampliación. Ninguna configuración se elige mirando popularidad de prueba.')
    blocks.extend(method.strip().split('\n\n'))
    blocks+=['## 9. Reproducción y presentación',
        'Ejecutar Proyecto_Mejorado.ipynb o python mejorar_proyecto.py para todas las etapas. Para recalcular esta ampliación desde resultados previos: python analizar_contextos.py. Protocolo, selección congelada, IDs, tablas y figuras están incluidos. El cierre auditivo es ilustrativo y requiere escuchar legalmente los enlaces, sin prometer un fragmento o estructura ganadora.',
        'Se utilizó ChatGPT/Codex para implementación y documentación. Completar autores y revisar personalmente antes de defender. Fuente: Pandya, M. (s. f.). Spotify Tracks Dataset [Conjunto de datos]. Hugging Face. https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset',
        'Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825–2830. https://jmlr.org/papers/v12/pedregosa11a.html']
    position=blocks.index('## 2. Otra evaluación y comparación controlada')
    blocks[position:position]=[f'![Búsqueda fina {family}/{space}](ampliacion/figuras/busqueda_{family}_{space}.png)' for family in ['KMeans','GMM'] for space in ['original','pca']]
    text='\n\n'.join(blocks);assert re.findall(r'^### (\d+)\. ',text,re.M)==[str(i) for i in range(1,13)]
    (CTX_ROOT/'resultados/informe.md').write_text(text,'utf-8');(CTX_ROOT/'resultados/informe.html').write_text(core.render_report(blocks),'utf-8')
    ctx_save('resultado_contextos.json',new_result)
    return new_result

def ejecutar_ampliacion():
    CTX_OUT.mkdir(exist_ok=True);(CTX_OUT/'figuras').mkdir(exist_ok=True)
    base=(CTX_ROOT/'resultados/informe.md').read_text('utf-8')
    if '## 1. Ampliación y criterios fijados' in base:
        pop.ejecutar_objetivo();base=(CTX_ROOT/'resultados/informe.md').read_text('utf-8')
    frozen_base=json.loads((CTX_ROOT/'resultados/seleccion_congelada.json').read_text('utf-8'))
    train=core.clean_data(pd.read_csv(CTX_ROOT/'resultados/entrenamiento.csv'))
    fit=core.clean_data(pd.read_csv(CTX_ROOT/'resultados/ajuste_interno.csv'));val=core.clean_data(pd.read_csv(CTX_ROOT/'resultados/validacion_interna.csv'))
    assert not core.artist_union(fit)&core.artist_union(val)
    selected=ctx_search(fit,val,frozen_base['preprocessing'])
    primary_row=pd.DataFrame(selected).sort_values(['val_sil_common','model','space'],ascending=[False,True,True]).iloc[0];primary=primary_row.model+'_'+primary_row.space
    prep=core.pipeline(frozen_base['preprocessing']).fit(train[core.FEATURES]);X=prep.transform(train[core.FEATURES]);pca=PCA(n_components=.9,svd_solver='full').fit(X)
    ref=core.pipeline('standard').fit(train[core.FEATURES]);common=ref.transform(train[core.FEATURES]);models={};train_labels={};leaders={}
    for cfg in selected:
        key=cfg['model']+'_'+cfg['space'];A=X if cfg['space']=='original' else pca.transform(X);e=core.estimator(cfg['model'],cfg['k'],cfg['covariance']);seconds,ok,_=core.fit_model(e,A)
        if not ok:raise RuntimeError('No converge ajuste final fino '+key)
        models[key]=(e,dict(cfg,final_fit_seconds=seconds));train_labels[key]=e.predict(A);leaders[key]=ctx_leader(train,train_labels[key],CTX_P['candidate_min_training'])
        if leaders[key] is None:raise RuntimeError('No hay candidato global elegible')
    baseline_decision=json.loads((CTX_ROOT/'resultados/perfiles_candidatos_congelados.json').read_text('utf-8'));baseline_key=baseline_decision['primary_model'];baseline_leader=baseline_decision['leaders'][baseline_key]
    bc=next(x for x in frozen_base['selected'] if x['model']+'_'+x['space']==baseline_key);baseline=core.estimator(bc['model'],bc['k'],bc['covariance']);A=X if bc['space']=='original' else pca.transform(X);_,ok,_=core.fit_model(baseline,A)
    if not ok:raise RuntimeError('No converge referencia')
    known=pd.read_csv(CTX_ROOT/f'resultados/asignaciones_{baseline_key}.csv').set_index('track_id')
    assert np.array_equal(baseline.predict(A),known.loc[train.track_id,'cluster'].to_numpy()),'Cambió la identidad de grupos de referencia'
    raw=pd.read_csv(CTX_ROOT/'data/raw/spotify_tracks.csv');training_contexts=ctx_tags(raw,[train])[0]
    context_leaders={};counts=[]
    for name,mask in training_contexts.items():
        leader=ctx_leader(train.loc[mask].reset_index(drop=True),train_labels[primary][mask],CTX_P['context_min_profile_training']) if mask.sum()>=CTX_P['context_min_training'] else None
        counts.append(dict(context=name,training_songs=int(mask.sum()),eligible=leader is not None))
        if leader is not None:context_leaders[name]=leader
    frozen=dict(primary=primary,selected=pd.DataFrame(selected).replace({np.nan:None}).to_dict('records'),leaders=leaders,contexts=context_leaders,baseline_key=baseline_key,baseline_leader=baseline_leader,preprocessing=frozen_base['preprocessing'],protocol_sha256=hashlib.sha256((CTX_ROOT/'protocolo_contextos.json').read_bytes()).hexdigest(),selection_uses_test=False,models_use_popularity=False,models_use_genre=False)
    ctx_save('seleccion_congelada.json',frozen)
    test,pool_size=ctx_new_test(raw);T=prep.transform(test[core.FEATURES]);common_test=ref.transform(test[core.FEATURES]);test_contexts=ctx_tags(raw,[test])[0]
    rows=[];stability=[];effects=[];traits=[];test_labels={};all_profiles=[]
    for key,(e,cfg) in models.items():
        A,B=(X,T) if cfg['space']=='original' else (pca.transform(X),pca.transform(T));lt=train_labels[key];tick=time.perf_counter();lv=e.predict(B);predict_seconds=time.perf_counter()-tick;test_labels[key]=lv
        pd.concat([train.assign(split='train',cluster=lt),test.assign(split='test',cluster=lv)]).to_csv(CTX_OUT/f'asignaciones_{key}.csv',index=False)
        for split,native,reference,labels in [('train',A,common,lt),('test',B,common_test,lv)]:
            ari=adjusted_rand_score(train_labels[cfg['model']+'_original'] if split=='train' else test_labels[cfg['model']+'_original'],labels) if cfg['space']=='pca' else np.nan
            for geometry,matrix in [('native',native),('reference_original',reference)]:rows.append(dict(model=cfg['model'],space=cfg['space'],split=split,evaluation_space=geometry,k=cfg['k'],covariance=cfg['covariance'],groups=len(np.unique(labels)),noise_pct=0.,fit_seconds=cfg['final_fit_seconds'],predict_seconds=predict_seconds,ari_vs_original=ari,**core.metrics(matrix,labels)))
        for kind in ['seed','subsample']:
            repeated=[]
            for seed in [42,7,21,123]:
                ix=np.random.default_rng(seed).choice(len(A),int(.8*len(A)),replace=False) if kind=='subsample' else np.arange(len(A))
                m=core.estimator(cfg['model'],cfg['k'],cfg['covariance'],seed);_,ok,_=core.fit_model(m,A[ix])
                if not ok:raise RuntimeError('No converge estabilidad '+key)
                repeated.append(m.predict(B))
            for i,j in itertools.combinations(range(4),2):stability.append(dict(model=cfg['model'],space=cfg['space'],kind=kind,ari=float(adjusted_rand_score(repeated[i],repeated[j]))))
        effect=ctx_effect(test,lv,leaders[key]);effects.append(dict(strategy='fino',configuration=key,cluster=leaders[key],**effect))
        traits.append(pop.pop_characteristics(train,lt,leaders[key],key))
        median=train.assign(cluster=lt).groupby('cluster')[core.FEATURES].median();median.to_csv(CTX_OUT/f'perfiles_{key}.csv')
        for cluster,r in median.iterrows():
            energy='intenso' if r.energy>=.65 else 'suave' if r.energy<.35 else 'intermedio';texture='acústico' if r.acousticness>=.6 else 'instrumental' if r.instrumentalness>=.5 else 'mixto'
            all_profiles.append(dict(configuration=key,cluster=int(cluster),n=int((lt==cluster).sum()),name=energy+' / '+texture,**r.to_dict()))
    baseline_labels=baseline.predict(T if bc['space']=='original' else pca.transform(T));effects.append(dict(strategy='referencia',configuration=baseline_key,cluster=baseline_leader,**ctx_effect(test,baseline_labels,baseline_leader)))
    context_rows=[];m=max(len(context_leaders),1)
    for name,leader in context_leaders.items():
        mask=test_contexts[name];frame=test.loc[mask].reset_index(drop=True);labels=test_labels[primary][mask]
        result=ctx_effect(frame,labels,leader,alpha=.05/m,min_side=CTX_P['context_min_profile_test']) if len(frame) else dict(status='muestra insuficiente',n=0,diff_low=np.nan,diff_high=np.nan,lift=np.nan)
        if len(frame)<CTX_P['context_min_test']:result['status']='muestra insuficiente';result['diff_low']=np.nan;result['diff_high']=np.nan
        context_rows.append(dict(context=name,cluster=leader,**result))
    comparison=pd.DataFrame(rows);effects=pd.DataFrame(effects);traits=pd.concat(traits,ignore_index=True);stability=pd.DataFrame(stability);contexts=pd.DataFrame(context_rows);counts=pd.DataFrame(counts)
    for filename,frame in [('comparativa',comparison),('concentracion',effects),('contextos',contexts),('rasgos',traits),('estabilidad',stability),('cobertura_contextos',counts)]:frame.to_csv(CTX_OUT/f'{filename}.csv',index=False)
    pd.DataFrame(all_profiles).to_csv(CTX_OUT/'todos_los_perfiles.csv',index=False)
    Z=pca.transform(X);plt.figure(figsize=(7,4));sc=plt.scatter(Z[:,0],Z[:,1],c=train_labels[primary],cmap='tab20',s=5,alpha=.4);plt.colorbar(sc,label='Grupo');plt.xlabel('PC1');plt.ylabel('PC2');plt.title('Modelo fino '+primary);ctx_figure('mapa_principal')
    plot=effects.copy();plt.figure(figsize=(9,4));plt.barh(plot.strategy+' / '+plot.configuration,100*plot.profile_rate,color='#358da0');plt.axvline(100*plot.global_rate.iloc[0],ls='--',color='black',label='Tasa global');plt.xlabel('Canciones ≥70 en el perfil (%)');plt.legend();plt.title('Concentración: comparar junto con cobertura y captura');ctx_figure('concentracion')
    plt.figure(figsize=(8,4))
    if len(contexts):
        for i,r in contexts.iterrows():
            if r.status=='ok':plt.plot([100*r.diff_low,100*r.diff_high],[i,i],color='#358da0');plt.scatter(100*r.difference,i,color='#123e50')
        plt.yticks(range(len(contexts)),contexts.context)
    plt.axvline(0,ls='--',color='black');plt.xlabel('Diferencia perfil−resto (pp), IC corregido');plt.title('Contextos secundarios');ctx_figure('contextos')
    q=traits.query('configuration==@primary').sort_values('standardized_difference');plt.figure(figsize=(8,4));plt.barh(q.variable,q.standardized_difference,color='#358da0');plt.xlabel('Diferencia de medianas / DE de entrenamiento');plt.axvline(0,color='black');plt.title('Rasgos del candidato fino principal');ctx_figure('rasgos')
    sensitivity=[]
    for threshold in CTX_P['sensitivity']:
        f=test.loc[test_labels[primary]==leaders[primary],'popularity'];base_rate=float((test.popularity>=threshold).mean());rate=float((f>=threshold).mean());sensitivity.append(dict(threshold=threshold,profile_rate=rate,global_rate=base_rate,lift=rate/base_rate if base_rate else np.nan))
    pd.DataFrame(sensitivity).to_csv(CTX_OUT/'sensibilidad.csv',index=False)
    summary=dict(primary=primary,n_new_evaluation=len(test),eligible_pool=pool_size,pca_components=int(pca.n_components_),pca_variance=float(pca.explained_variance_ratio_.sum()))
    result=ctx_report(base,frozen,comparison,effects,contexts,traits,stability,summary,counts)
    assert len(comparison)==16 and len(stability)==48 and not frozen['selection_uses_test']
    ctx_save('validacion.json',dict(status='passed',new_test=len(test),grid_candidates=36,comparison_rows=16,stability_pairs=48,context_count=len(context_leaders),no_previous_ids_artists_or_audio=True,protocol_sha256=frozen['protocol_sha256']))
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    return result

if __name__=='__main__':
    with threadpool_limits(limits=1):ejecutar_ampliacion()
