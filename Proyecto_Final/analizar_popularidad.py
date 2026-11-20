"""Contraste posterior al clustering: popularidad, perfiles y rasgos descriptivos."""
from pathlib import Path
import hashlib
import json
import re
import html
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits
import mejorar_proyecto as core

POP_ROOT = Path(__file__).resolve().parent
POP_OUT = POP_ROOT/'resultados'

def pop_artists_bootstrap(frame, labels, leader, threshold, repetitions, seed):
    valid=frame.popularity.notna().to_numpy()
    f=frame.loc[valid].reset_index(drop=True);labs=np.asarray(labels)[valid]
    _,groups=np.unique(core.artist_groups(f),return_inverse=True)
    n_groups=int(groups.max()+1)
    in_profile=(labs==leader);high=(f.popularity.to_numpy()>=threshold)
    # Cada componente de artistas se remuestrea como una unidad completa.
    counts=np.zeros((n_groups,4),dtype=float)
    np.add.at(counts[:,0],groups,in_profile.astype(float))
    np.add.at(counts[:,1],groups,(in_profile&high).astype(float))
    np.add.at(counts[:,2],groups,(~in_profile).astype(float))
    np.add.at(counts[:,3],groups,((~in_profile)&high).astype(float))
    total=counts.sum(axis=0)
    if total[0]==0 or total[2]==0:return dict(diff_low=np.nan,diff_high=np.nan,lift_low=np.nan,lift_high=np.nan,artist_components=n_groups)
    rng=np.random.default_rng(seed);diff=[];lift=[]
    for start in range(0,repetitions,200):
        ix=rng.integers(0,n_groups,size=(min(200,repetitions-start),n_groups))
        draw=counts[ix].sum(axis=1)
        good=(draw[:,0]>0)&(draw[:,2]>0)
        draw=draw[good]
        r1=draw[:,1]/draw[:,0];r0=draw[:,3]/draw[:,2]
        base=(draw[:,1]+draw[:,3])/(draw[:,0]+draw[:,2])
        diff.extend(r1-r0);positive=base>0;lift.extend(r1[positive]/base[positive])
    if not diff:return dict(diff_low=np.nan,diff_high=np.nan,lift_low=np.nan,lift_high=np.nan,artist_components=n_groups)
    a,b=np.quantile(diff,[.025,.975]);c,d=np.quantile(lift,[.025,.975]) if lift else (np.nan,np.nan)
    return dict(diff_low=float(a),diff_high=float(b),lift_low=float(c),lift_high=float(d),artist_components=n_groups)

def pop_profile_summary(frame, labels, name, split, threshold):
    rows=[];valid=frame.popularity.notna();global_rate=float((frame.loc[valid,'popularity']>=threshold).mean())
    for cluster in sorted(np.unique(labels)):
        f=frame.loc[(np.asarray(labels)==cluster)&valid.to_numpy()];n=len(f);high=int((f.popularity>=threshold).sum());rate=high/n if n else np.nan
        rows.append(dict(configuration=name,split=split,cluster=int(cluster),threshold=threshold,n=n,high_count=high,high_rate=rate,global_rate=global_rate,lift=rate/global_rate if global_rate else np.nan,median=float(f.popularity.median()),q25=float(f.popularity.quantile(.25)),q75=float(f.popularity.quantile(.75))))
    return pd.DataFrame(rows)

def pop_reproduce(train,previous_test,frozen):
    prep=core.pipeline(frozen['preprocessing']).fit(train[core.FEATURES]);X=prep.transform(train[core.FEATURES])
    pca=PCA(n_components=.9,svd_solver='full').fit(X)
    reference=core.pipeline('standard').fit(train[core.FEATURES])
    models={};check=[]
    for cfg in frozen['selected']:
        key=cfg['model']+'_'+cfg['space'];A=X if cfg['space']=='original' else pca.transform(X)
        est=core.estimator(cfg['model'],cfg['k'],cfg['covariance']);_,ok,_=core.fit_model(est,A)
        if not ok:raise RuntimeError('No converge reproducción '+key)
        known=pd.read_csv(POP_OUT/f'asignaciones_{key}.csv').set_index('track_id')
        predicted=est.predict(A);ari=adjusted_rand_score(known.loc[train.track_id,'cluster'],predicted)
        B=prep.transform(previous_test[core.FEATURES]);B=B if cfg['space']=='original' else pca.transform(B)
        ari_test=adjusted_rand_score(known.loc[previous_test.track_id,'cluster'],est.predict(B))
        if ari<.999999 or ari_test<.999999:raise RuntimeError('No reproduce particiones '+key)
        models[key]=(est,cfg['space'],predicted);check.append(dict(configuration=key,ari_train=float(ari),ari_previous_test=float(ari_test)))
    return prep,pca,reference,models,check

def pop_new_evaluation(protocol,previous):
    raw=core.clean_data(pd.read_csv(POP_ROOT/'data/raw/spotify_tracks.csv'))
    used_artists=core.artist_union(previous)
    eligible=(~raw.track_id.isin(previous.track_id)) & raw.artists.map(lambda v:bool(core.artists(v)) and not bool(core.artists(v)&used_artists))
    eligible &= ~np.isin(core.signatures(raw),core.signatures(previous))
    pool=raw.loc[eligible]
    if len(pool)<protocol['nueva_evaluacion']:raise ValueError('No hay suficientes canciones reservables')
    test=pool.sample(n=protocol['nueva_evaluacion'],random_state=protocol['semilla_nueva_evaluacion']).reset_index(drop=True)
    assert not core.artist_union(previous)&core.artist_union(test)
    assert not set(previous.track_id)&set(test.track_id)
    assert not set(core.signatures(previous))&set(core.signatures(test))
    test.to_csv(POP_OUT/'prueba_objetivo_popularidad.csv',index=False)
    return test,len(pool)

def pop_characteristics(train,labels,leader,name):
    a=train.loc[np.asarray(labels)==leader,core.FEATURES];b=train.loc[np.asarray(labels)!=leader,core.FEATURES]
    med_a=a.median();med_b=b.median();sd=train[core.FEATURES].std()
    result=pd.DataFrame(dict(configuration=name,cluster=leader,variable=core.FEATURES,profile_median=med_a.to_numpy(),rest_median=med_b.to_numpy(),difference=(med_a-med_b).to_numpy(),standardized_difference=((med_a-med_b)/sd).to_numpy()))
    return result.sort_values('standardized_difference',key=abs,ascending=False)

def pop_write_report(protocol,primary,leaders,summary,effects,features,reproduction,new_test,pool_size):
    base=(POP_OUT/'informe.md').read_text('utf-8')
    # La ejecución independiente reconstruye el método desde resultados verificados.
    # No necesita conservar otro informe con un objetivo diferente.
    if '## 2. Datos y preparación sin fuga' not in base:
        core.report(json.loads((POP_OUT/'auditoria.json').read_text('utf-8')),
            json.loads((POP_OUT/'seleccion_congelada.json').read_text('utf-8')),
            pd.read_csv(POP_OUT/'busqueda_completa.csv'),pd.read_csv(POP_OUT/'seleccion_por_preparacion.csv'),
            pd.read_csv(POP_OUT/'comparativa.csv'),pd.read_csv(POP_OUT/'estabilidad.csv'),
            pd.read_csv(POP_OUT/'perfiles.csv'),pd.read_csv(POP_OUT/'popularidad.csv'),
            pd.read_csv(POP_OUT/'cargas_pca.csv',index_col=0),
            json.loads((POP_OUT/'transformacion.json').read_text('utf-8')),
            pd.read_csv(POP_OUT/'ejemplos_escucha.csv'))
        base=(POP_OUT/'informe.md').read_text('utf-8')
    method_start=base.index('## 2. Datos y preparación sin fuga')
    method_end=base.index('## 9. Cierre con canciones reales')
    method=base[method_start:method_end]
    for number,title in [(2,'Datos y preparación sin fuga'),(3,'Protocolo y selección'),(4,'PCA e interpretación'),(5,'Tabla comparativa obligatoria y comparación justa'),(6,'Estabilidad y costo'),(7,'Interpretación y acciones por perfil')]:
        method=method.replace(f'## {number}. {title}',f'### Método: {title}')
    method=method.replace('## 8. Las doce respuestas de la rúbrica','## 8. Las doce respuestas de la rúbrica')
    method=method.replace('### Popularidad como análisis secundario','### Distribuciones de popularidad después del agrupamiento')
    method=method.replace('La decisión práctica es segmentar el catálogo','La segmentación permite contrastar perfiles y popularidad')
    method=method.replace('La popularidad es un análisis descriptivo secundario.','La popularidad se contrasta después de congelar los modelos.')
    e=effects.query("configuration==@primary and split=='nueva_evaluacion' and threshold==70").iloc[0]
    leader=leaders[primary];train_row=summary.query("configuration==@primary and split=='entrenamiento' and threshold==70 and cluster==@leader").iloc[0]
    test_row=summary.query("configuration==@primary and split=='nueva_evaluacion' and threshold==70 and cluster==@leader").iloc[0]
    if e.diff_low>0:verdict='La nueva evaluación aporta evidencia de una mayor concentración de alta popularidad en el perfil candidato, dentro de esta fuente y estos criterios.'
    elif e.diff_high<0:verdict='La asociación se invierte en la nueva evaluación: el perfil candidato no conserva la ventaja observada en entrenamiento.'
    else:verdict='No se confirma una mayor concentración en la nueva evaluación: el intervalo de la diferencia incluye cero.'
    method=method.replace('### 12. Recomendación final','### 12. Recomendación final\n\n'+f'Para la pregunta de popularidad, el contraste principal de {primary} da lift {test_row.lift:.2f} e IC95 de diferencia [{100*e.diff_low:+.2f}, {100*e.diff_high:+.2f}] pp. {verdict} No se recomienda convertir el perfil en regla comercial ni escoger otra configuración porque produzca una asociación más favorable. La recomendación geométrica que sigue se refiere a la calidad de agrupamiento, no a predicción de éxito.')
    feature_primary=features.query('configuration==@primary')
    dominant='; '.join(f'{r.variable}: mediana {r.profile_median:.3f} frente a {r.rest_median:.3f} en el resto' for r in feature_primary.head(4).itertuples())
    blocks=['# ¿Existen perfiles sonoros que concentren canciones de alta popularidad y qué características los distinguen?',
        'Proyecto de Bloque 3 · Aprendizaje no supervisado · K-Means y GMM antes y después de PCA. Completar autores y fecha de entrega.',
        '## Resumen del resultado',
        f'El contraste principal usa {primary}, seleccionado antes por calidad geométrica y sin popularidad. El perfil candidato es el grupo {leader}, elegido en entrenamiento por su proporción de canciones con popularidad ≥70: {int(train_row.high_count)}/{int(train_row.n)} ({train_row.high_rate:.2%}). En 2.000 canciones adicionales de artistas no utilizados antes, el perfil presenta {int(test_row.high_count)}/{int(test_row.n)} ({test_row.high_rate:.2%}), frente a una tasa global de {test_row.global_rate:.2%}. Su lift es {test_row.lift:.2f}. {verdict}',
        f'Diferencia frente al resto: {100*e.rate_difference:+.2f} puntos porcentuales, IC95 por artistas [{100*e.diff_low:+.2f}, {100*e.diff_high:+.2f}]. Las características que más distinguen el perfil en entrenamiento son: {dominant}. Son rasgos descriptivos del grupo, no causas del éxito.',
        '## 1. Objetivo y alcance',protocol['objetivo'],
        'Objetivo general: descubrir perfiles utilizando exclusivamente características sonoras, determinar si alguno concentra canciones de alta popularidad y describir los atributos que lo distinguen. Objetivos específicos: limpiar y preparar datos; comparar K-Means y GMM antes/después de PCA; identificar candidatos en entrenamiento; evaluar concentración en canciones adicionales; comprobar sensibilidad y comunicar límites.',
        'El clustering es el método para responder esta pregunta, no el fin comercial del proyecto. No se convierte el trabajo en un predictor supervisado ni se usa popularidad para escoger algoritmos, preparación, K o covarianza.',
        '## 2. Cómo se define y mide alta popularidad',
        'Definición operativa principal: popularity ≥70 en la escala histórica 0–100 del dataset. No equivale a ventas, ingresos o éxito universal. Los umbrales 60 y 80 son sensibilidad fijada antes de esta evaluación; no se elige el que produzca la mejor historia. Ceros se conservan como valores del archivo, sin interpretarlos como ausencia real de oyentes.',
        'Concentración = canciones ≥70 / canciones con popularidad válida del perfil. Lift = tasa del perfil / tasa global del mismo conjunto: 1 indica igual concentración; 2 significa el doble de la tasa observada, no el doble de probabilidad causal de éxito. La diferencia principal compara perfil y resto, expresada en puntos porcentuales.',
        'Protocolo: algoritmos y parámetros ya estaban congelados por separación geométrica. Para cada una de las cuatro configuraciones se elige el perfil candidato exclusivamente por la mayor tasa ≥70 de entrenamiento, con desempate por ID. El modelo principal se fija por el mayor Silhouette de validación previamente registrado. Se preserva esa elección en sensibilidad, sin seleccionar nuevos perfiles con los resultados de prueba.',
        '## 3. Comprobación en canciones no utilizadas antes',
        f'Se reservaron {len(new_test)} canciones con semilla {protocol["semilla_nueva_evaluacion"]}, de {pool_size} elegibles. Se excluyeron los 10.000 IDs históricos, las 2.000 canciones de la evaluación adicional anterior, todos sus artistas individuales y los vectores acústicos iguales a siete decimales. No se eligieron canciones por su popularidad. La fuente histórica es la misma: no se presenta como evidencia temporal o externa.',
        'La evaluación anterior de 2.000 canciones ya había sido observada y se muestra como retrospectiva. La conclusión principal utiliza la nueva evaluación. La decisión de revisar el objetivo está informada por análisis previos: este protocolo documenta criterios anteriores a este nuevo cálculo, pero no es un prerregistro externo.',
        '![Concentración de alta popularidad por perfil](figuras/concentracion_popularidad.png)',
        core.table(summary.query('threshold==70')),
        '### Contraste principal y comparación de configuraciones',core.table(effects.query("split=='nueva_evaluacion' and threshold==70")),
        'Intervalos percentiles de 2.000 remuestreos por componentes de artistas colaboradores; cada unidad se conserva completa. Son condicionales a los modelos y perfiles elegidos y no incluyen toda la incertidumbre de volver a entrenar. Las cuatro configuraciones comparten canciones y no son cuatro confirmaciones independientes; solo la configuración principal define el contraste primario. Los análisis restantes son exploratorios.',
        '![Lift y su incertidumbre en la evaluación nueva](figuras/lift_popularidad.png)',
        '## 4. Qué características distinguen los perfiles candidatos',
        'Las tablas usan medianas en unidades originales y contraste perfil−resto. La diferencia estandarizada solo ordena atributos descriptivos; no es un coeficiente causal ni una prueba de importancia predictiva. El perfil se define por todas las variables, no por una sola regla musical.',core.table(feature_primary),
        '![Características del perfil candidato principal](figuras/rasgos_popularidad.png)',
        '### Perfiles candidatos de las cuatro configuraciones',core.table(features),
        '## 5. Sensibilidad y distribución completa',core.table(effects.query("split=='nueva_evaluacion'")),
        'La sensibilidad mantiene el perfil candidato identificado con umbral 70. Revisar si el signo de la diferencia se conserva con 60 y 80 y cuán amplios son sus intervalos; no elegir un umbral después de ver los resultados. Con pocos casos ≥80 la incertidumbre puede ser grande.',
        '![Popularidad completa por perfil](figuras/distribucion_popularidad.png)',
        'Las cajas muestran mediana y dispersión: una proporción alta puede coexistir con muchas canciones de baja popularidad. La superposición impide convertir un perfil en garantía individual.',
        '## 6. Respuesta y límites',verdict,
        f'La respuesta debe citar el contraste de {primary}, perfil {leader}: tasa {test_row.high_rate:.2%}, lift {test_row.lift:.2f}, diferencia {100*e.rate_difference:+.2f} pp e intervalo [{100*e.diff_low:+.2f}, {100*e.diff_high:+.2f}]. Si no se confirma, no se afirma que no exista ningún patrón posible: solo que este candidato y este diseño no lo confirman.',
        'El análisis no distingue causas de popularidad: promoción, artista, idioma, exposición en playlists y momento del lanzamiento pueden explicar asociaciones. Los atributos agregados no describen melodía, letra o estructura verso/estribillo. No se recomienda una receta de producción ni se afirma un porcentaje de precisión de éxitos.',
        '## 7. Experimento obligatorio de clustering y PCA']
    blocks.extend(method.strip().split('\n\n'))
    blocks+=['## 9. Cierre de la presentación',
        'Primero presentar la tasa global, la del perfil candidato y sus intervalos. Después mostrar sus rasgos acústicos y escuchar ejemplos que permitan contrastarlos. El archivo cierre_escucha.html conserva una pareja ilustrativa de canciones cercanas con popularidades distintas: sirve para explicar los límites de una asociación, no para reemplazar el contraste principal. No se incluye audio ni una supuesta estructura ganadora.',
        '## 10. Reproducibilidad, declaración de IA y referencias',
        'Ejecutar Proyecto_Mejorado.ipynb completo o python mejorar_proyecto.py. El núcleo ajusta los cuatro modelos y este módulo reproduce sus particiones con ARI=1 antes de estudiar popularidad. Protocolo, selección de perfiles, IDs y conteos, remuestreos, tablas y figuras acompañan la entrega. Se utilizó ChatGPT/Codex para implementación y documentación; revisar y declarar esa asistencia. No hay evaluaciones humanas inventadas ni garantía de nota.',
        'Pandya, M. (s. f.). Spotify Tracks Dataset [Conjunto de datos]. Hugging Face. https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset',
        'Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825–2830. https://jmlr.org/papers/v12/pedregosa11a.html',
        'Scikit-learn developers. (s. f.). PowerTransformer y GroupShuffleSplit [Documentación]. https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.PowerTransformer.html ; https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html']
    document=core.render_report(blocks).replace('Segmentación musical — Informe mejorado','Perfiles sonoros y alta popularidad')
    (POP_OUT/'informe.md').write_text('\n\n'.join(blocks),'utf-8');(POP_OUT/'informe.html').write_text(document,'utf-8')
    return dict(primary_model=primary,primary_profile=leader,verdict=verdict,profile_rate=float(test_row.high_rate),baseline_rate=float(test_row.global_rate),lift=float(test_row.lift),difference_pp=float(100*e.rate_difference),difference_ci_pp=[float(100*e.diff_low),float(100*e.diff_high)])

def ejecutar_objetivo():
    protocol=json.loads((POP_ROOT/'protocolo_popularidad.json').read_text('utf-8'))
    frozen=json.loads((POP_OUT/'seleccion_congelada.json').read_text('utf-8'))
    train=core.clean_data(pd.read_csv(POP_OUT/'entrenamiento.csv'))
    previous_test=core.clean_data(pd.read_csv(POP_OUT/'prueba_reservada.csv'))
    prep,pca,reference,models,reproduction=pop_reproduce(train,previous_test,frozen)
    primary_row=pd.DataFrame(frozen['selected']).sort_values(['val_sil_common','model','space'],ascending=[False,True,True]).iloc[0]
    primary=primary_row.model+'_'+primary_row.space
    leaders={};train_stats=[]
    for key,(_,_,labels) in models.items():
        stats=pop_profile_summary(train,labels,key,'entrenamiento',70);train_stats.append(stats)
        leaders[key]=int(stats.sort_values(['high_rate','cluster'],ascending=[False,True]).iloc[0].cluster)
    # Archivo escrito antes de cargar las nuevas observaciones de evaluación.
    decision=dict(objective=protocol['objetivo'],threshold=70,primary_model=primary,leaders=leaders,models_reselected_by_popularity=False,profile_selection_uses_training_only=True,protocol_sha256=hashlib.sha256((POP_ROOT/'protocolo_popularidad.json').read_bytes()).hexdigest())
    core.dump('perfiles_candidatos_congelados.json',decision)
    old=pd.concat([pd.read_csv(POP_ROOT/'data/referencia_anterior/train.csv'),pd.read_csv(POP_ROOT/'data/referencia_anterior/test.csv'),previous_test],ignore_index=True)
    test,pool_size=pop_new_evaluation(protocol,core.clean_data(old))
    all_stats=list(train_stats);effects=[];features=[];new_labels={}
    for key,(est,space,lt) in models.items():
        leader=leaders[key];features.append(pop_characteristics(train,lt,leader,key))
        for split,frame in [('evaluacion_anterior_observada',previous_test),('nueva_evaluacion',test)]:
            A=prep.transform(frame[core.FEATURES]);A=A if space=='original' else pca.transform(A);labs=est.predict(A)
            if split=='nueva_evaluacion':new_labels[key]=labs
            frame.assign(cluster=labs).to_csv(POP_OUT/f'popularidad_asignaciones_{split}_{key}.csv',index=False)
            for threshold in [70]+protocol['sensibilidad']:
                stats=pop_profile_summary(frame,labs,key,split,threshold);all_stats.append(stats)
                row=stats.loc[stats.cluster==leader].iloc[0];rest=frame.loc[(labs!=leader)&frame.popularity.notna().to_numpy(),'popularity'];rest_rate=float((rest>=threshold).mean())
                ci=pop_artists_bootstrap(frame,labs,leader,threshold,protocol['bootstrap'],protocol['semilla_bootstrap'])
                effects.append(dict(configuration=key,split=split,cluster=leader,threshold=threshold,n_profile=int(row.n),high_count=int(row.high_count),profile_rate=float(row.high_rate),rest_rate=rest_rate,global_rate=float(row.global_rate),lift=float(row.lift),rate_difference=float(row.high_rate-rest_rate),**ci))
    summary=pd.concat(all_stats,ignore_index=True);effects=pd.DataFrame(effects);features=pd.concat(features,ignore_index=True)
    summary.to_csv(POP_OUT/'concentracion_por_perfil.csv',index=False);effects.to_csv(POP_OUT/'contrastes_popularidad.csv',index=False);features.to_csv(POP_OUT/'rasgos_perfiles_populares.csv',index=False)
    principal=summary.query("configuration==@primary and split=='nueva_evaluacion' and threshold==70")
    plt.figure(figsize=(7,4));plt.bar(principal.cluster.astype(str),100*principal.high_rate,color='#358ca1');plt.axhline(100*principal.global_rate.iloc[0],ls='--',color='black',label='Tasa global');plt.xlabel('Perfil sonoro');plt.ylabel('Canciones con popularidad ≥70 (%)');plt.title('Nueva evaluación: '+primary);plt.legend();core.figure('concentracion_popularidad')
    eff=effects.query("split=='nueva_evaluacion' and threshold==70").reset_index(drop=True)
    plt.figure(figsize=(8,4))
    for i,r in eff.iterrows():plt.plot([r.lift_low,r.lift_high],[i,i],color='#358ca1');plt.scatter(r.lift,i,color='#123e50')
    plt.axvline(1,ls='--',color='black');plt.yticks(range(len(eff)),eff.configuration);plt.xlabel('Lift respecto a tasa global (IC95 por artistas)');plt.title('Concentración del perfil candidato, fijado en entrenamiento');core.figure('lift_popularidad')
    fp=features.query('configuration==@primary').sort_values('standardized_difference');plt.figure(figsize=(8,4));plt.barh(fp.variable,fp.standardized_difference,color='#358ca1');plt.axvline(0,color='black');plt.xlabel('Diferencia de medianas perfil−resto / DE de entrenamiento');plt.title('Rasgos descriptivos del perfil candidato: '+primary);core.figure('rasgos_popularidad')
    fig,axs=plt.subplots(2,2,figsize=(10,7))
    for ax,(key,labs) in zip(axs.flat,new_labels.items()):
        groups=sorted(np.unique(labs));ax.boxplot([test.loc[labs==g,'popularity'].dropna() for g in groups],tick_labels=[str(g) for g in groups],showfliers=True,flierprops=dict(marker='.',markersize=3,alpha=.35));ax.set(title=key,xlabel='Perfil',ylabel='Popularidad histórica');ax.axhline(70,color='red',ls='--',lw=.8)
    core.figure('distribucion_popularidad')
    conclusion=pop_write_report(protocol,primary,leaders,summary,effects,features,reproduction,test,pool_size)
    text=(POP_OUT/'informe.md').read_text('utf-8');assert re.findall(r'^### (\d+)\. ',text,re.M)==[str(i) for i in range(1,13)]
    assert len(effects)==24 and len(summary.query("split=='entrenamiento'"))>=8
    core.dump('resultado_objetivo.json',dict(**conclusion,n_new_evaluation=len(test),eligible_pool=pool_size,bootstrap_repetitions=protocol['bootstrap'],reproduction=reproduction,status='passed',exploratory_previous_evaluation=True,models_reselected_by_popularity=False))
    print(json.dumps(conclusion,ensure_ascii=False,indent=2),flush=True)
    return conclusion

if __name__=='__main__':
    with threadpool_limits(limits=1):ejecutar_objetivo()
