"""Construye la demo offline y evalúa recuperación geométrica en canciones de prueba."""
from pathlib import Path
import html
import json
import time
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits
import proyecto_musica as base

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs'
KEYS = [('KMeans','original'),('KMeans','pca'),('GMM','original'),('GMM','pca')]

def artist_set(value):
    return {s.strip().casefold() for s in str(value).split(';') if s.strip()}

def build():
    train=pd.read_csv(OUT/'train.csv'); test=pd.read_csv(OUT/'test.csv')
    catalog=pd.concat([train,test],ignore_index=True)
    features=base.FEATURES
    assert 'popularity' not in features
    assert catalog.track_id.is_unique and len(catalog)>=500
    imputer=SimpleImputer(strategy='median')
    scaler=StandardScaler()
    X=scaler.fit_transform(imputer.fit_transform(train[features]))
    T=scaler.transform(imputer.transform(test[features]))
    pca=PCA(n_components=.90,svd_solver='full')
    Z=pca.fit_transform(X); W=pca.transform(T)
    matrices={'original':np.vstack([X,T]),'pca':np.vstack([Z,W])}
    comparison=pd.read_csv(OUT/'comparativa.csv')
    labels={}; specs={}; integrity=[]; predictors={}
    for family,space in KEYS:
        key=family+'_'+space
        row=comparison.query('model == @family and space == @space and split == "train"').iloc[0]
        cfg=json.loads(row.hyperparameters)
        estimator=base.model(family,**cfg)
        matrix=matrices[space]
        before=time.perf_counter()
        estimator.fit(matrix[:len(train)])
        if not bool(getattr(estimator,'converged_',True)):
            raise RuntimeError('GMM no convergió al construir explorador')
        predicted=estimator.predict(matrix)
        if family == 'KMeans':
            predictors[key] = dict(centers=estimator.cluster_centers_.tolist())
        else:
            predictors[key] = dict(means=estimator.means_.tolist(), weights=estimator.weights_.tolist(),
                precision=np.linalg.inv(estimator.covariances_).tolist(),
                logdet=np.linalg.slogdet(estimator.covariances_)[1].tolist())
        reference=pd.read_csv(OUT/f'asignaciones_{family}_{space}.csv').set_index('track_id')
        old=reference.loc[catalog.track_id,'cluster'].to_numpy()
        ari=adjusted_rand_score(old,predicted)
        if ari < .999999:
            raise RuntimeError(f'No se reprodujeron las asignaciones {key}: ARI={ari}')
        labels[key]=predicted
        names={}
        for c in np.unique(predicted[:len(train)]):
            med=train.loc[predicted[:len(train)]==c,features].median()
            energy='Energía alta' if med.energy>=.65 else ('Energía baja' if med.energy<.35 else 'Energía media')
            texture='acústico' if med.acousticness>=.6 else ('instrumental' if med.instrumentalness>=.5 else 'mixto')
            names[str(c)]=energy+' · '+texture
        specs[key]=dict(family=family,space=space,parameters=cfg,names=names,train_size=len(train))
        integrity.append(dict(configuration=key,ari_reproduced=float(ari),fit_seconds=time.perf_counter()-before))

    # Consultas solo de prueba. Catálogo de candidatos exclusivamente entrenamiento.
    # Los artistas no entran en distancias; se usan solo para excluir repeticiones.
    train_artists=[artist_set(a) for a in train.artists.fillna('')]
    queries=np.random.default_rng(42).choice(len(test),min(200,len(test)),replace=False)
    retrieval=[]; overlap=[]; validation=[]
    for qi in queries:
        q=len(train)+int(qi)
        qa=artist_set(catalog.iloc[q].artists)
        eligible=np.array([not bool(a & qa) for a in train_artists])
        d0=np.linalg.norm(X-matrices['original'][q],axis=1)
        candidates=np.flatnonzero(eligible)
        reference=candidates[np.argsort(d0[candidates],kind='stable')[:10]]
        answers={}
        for family,space in KEYS:
            key=family+'_'+space
            pool=np.flatnonzero(eligible & (labels[key][:len(train)]==labels[key][q]))
            distances=np.linalg.norm(matrices[space][:len(train)]-matrices[space][q],axis=1)
            recommended=pool[np.argsort(distances[pool],kind='stable')[:10]]
            answers[key]=set(map(int,recommended))
            retrieval.append(dict(query_id=catalog.iloc[q].track_id,configuration=key,
                candidate_pool=len(pool),returned=len(recommended),
                recall_at_10=len(set(recommended)&set(reference))/len(reference),
                mean_original_distance=float(d0[recommended].mean()) if len(recommended) else np.nan))
            assert all(not (train_artists[i]&qa) for i in recommended)
            assert all(catalog.iloc[i].track_id != catalog.iloc[q].track_id for i in recommended)
        for family in ['KMeans','GMM']:
            a,b=answers[family+'_original'],answers[family+'_pca']
            overlap.append(dict(query_id=catalog.iloc[q].track_id,model=family,
                jaccard=len(a&b)/len(a|b) if a|b else np.nan))
    retrieval=pd.DataFrame(retrieval); overlap=pd.DataFrame(overlap)
    retrieval.to_csv(OUT/'evaluacion_recuperacion.csv',index=False)
    overlap.to_csv(OUT/'solapamiento_recomendaciones.csv',index=False)
    summary=retrieval.groupby('configuration').agg(queries=('query_id','count'),
        recall_at_10=('recall_at_10','mean'),mean_pool=('candidate_pool','mean'),
        mean_returned=('returned','mean'),mean_original_distance=('mean_original_distance','mean')).reset_index()
    summary.to_csv(OUT/'resumen_recuperacion.csv',index=False)
    # Exportación con precisión suficiente; JS usa exactamente las mismas coordenadas.
    songs=[]
    for row in catalog.itertuples(index=False):
        songs.append([str(row.track_id),str(row.track_name),str(row.artists),
            None if pd.isna(row.popularity) else int(row.popularity),
            '' if pd.isna(row.track_genre) else str(row.track_genre),str(row.split)])
    raw=imputer.transform(catalog[features])
    initial=int(len(train)+np.argmax(test.popularity.fillna(-1).to_numpy()))
    data=dict(transform=dict(mean=scaler.mean_.tolist(),scale=scaler.scale_.tolist(),
            pca_mean=pca.mean_.tolist(),components=pca.components_.tolist()),predictors=predictors,
        songs=songs,features=features,raw=np.round(raw,7).tolist(),
        matrices={key:np.round(val,9).tolist() for key,val in matrices.items()},
        labels={key:val.tolist() for key,val in labels.items()},specs=specs,
        train_size=len(train),initial=initial,
        pca=dict(components=int(pca.n_components_),variance=float(pca.explained_variance_ratio_.sum())),
        retrieval=summary.round(5).to_dict('records'),
        comparison=comparison.replace({np.nan:None}).to_dict('records'))
    template=(ROOT/'interfaz.template.html').read_text(encoding='utf-8')
    template=template.replace('// PROFESSIONAL_MODULE', (ROOT/'profesional.js').read_text(encoding='utf-8'))
    payload=json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    payload=payload.replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    (ROOT/'Explorador_Musical.html').write_text(template.replace('__DATA__',payload),encoding='utf-8')
    (OUT/'integridad_explorador.json').write_text(json.dumps(dict(status='passed',queries=len(queries),
        catalog=len(catalog),features=len(features),train_size=len(train),test_size=len(test),
        preprocessing_fit='train_only',models=integrity,
        checks=['IDs únicos','cuatro modelos reproducidos ARI=1','sin autorrecomendaciones',
                'sin artistas compartidos en recomendaciones evaluadas','consultas test y candidatos train',
                'popularidad excluida de características']),indent=2),encoding='utf-8')
    report(summary,overlap,data)
    print(summary.to_string(index=False),flush=True)
    print('Explorador offline e informe generados.',flush=True)
    return data

def report(summary,overlap,data):
    overlap_summary=overlap.groupby('model').jaccard.agg(['mean','min','max']).reset_index()
    km=summary.set_index('configuration').loc['KMeans_pca']
    text='''# Explorador musical: canciones parecidas y descubrimiento de catálogo

## Pregunta principal

¿Cómo cambian los perfiles y las canciones sugeridas al utilizar K-Means y GMM,
antes y después de PCA? ¿Permiten esos perfiles explorar canciones de artistas distintos?

## Objetivo

Construir un explorador de un catálogo fijo, comparando dos algoritmos de
clustering y dos representaciones sonoras. La popularidad es información
secundaria y un filtro opcional del usuario, nunca una característica de ajuste.

## Funcionamiento

1. El usuario busca una canción o artista dentro de la muestra disponible.
2. Elige K-Means o GMM y espacio original o PCA.
3. Se asigna el perfil de la canción y se buscan vecinos por distancia euclidiana.
4. Por defecto se recuperan canciones del mismo grupo, del catálogo de entrenamiento
   y sin artistas compartidos con la consulta. Se excluye siempre la propia canción.
5. Puede ampliar a todos los perfiles o filtrar canciones de menor popularidad.

Clustering organiza el catálogo; la distancia dentro del espacio elegido ordena
los vecinos. Dos algoritmos pueden dar sugerencias similares si comparten
candidatos próximos. Buscar en todos los perfiles elimina la influencia del
modelo sobre el ranking: únicamente cambia la geometría original/PCA.

## Diseño y rúbrica

Se conservan 10.000 canciones únicas, 8.000 entrenamiento y 2.000 prueba,
diez variables numéricas, semilla fija 42 y entrenamiento sin popularidad ni género.
Imputación, escalador y PCA se ajustan exclusivamente con entrenamiento.
Se comparan K-Means y GMM, con búsqueda K=2…12 y full/diag para GMM.
K-Means se selecciona por Silhouette y GMM por BIC, sin consultar popularidad.
El mínimo de BIC en el extremo del rango es una limitación de la búsqueda, no
prueba de que existan exactamente doce categorías musicales.

La tabla 2×2 ampliada, tres métricas en train/test, ARI antes/después, tiempos,
estabilidad, perfiles originales, efectos de escalado, cargas de PCA y las doce
preguntas conceptuales se conservan en **informe.html**. Ese informe es la base
experimental y su pregunta de popularidad se mantiene como análisis secundario.
Este documento establece la nueva pregunta principal y su evaluación adicional.

'''
    text+=f'PCA conserva **{data["pca"]["components"]} componentes y {data["pca"]["variance"]:.2%} de varianza**.\n\n'
    text+='''## Evaluación de sugerencias

Se utilizan 200 consultas seleccionadas aleatoriamente de prueba con semilla 42.
Los candidatos provienen exclusivamente de entrenamiento y se excluyen artistas
compartidos, separando nombres por punto y coma. El catálogo no incluye todo Spotify.

La referencia son los diez vecinos más cercanos en el espacio original escalado,
sin restricción de grupo y con la misma exclusión de artistas. Recall@10 mide
cuántos de esos vecinos recupera cada configuración. Este indicador favorece la
geometría original por definición: mide conservación geométrica, **no satisfacción
del usuario, calidad artística ni relevancia musical validada**. No se ajustan
hiperparámetros con estas consultas. El filtro de popularidad está desactivado en
esta evaluación para aislar el efecto de geometría y agrupación.

'''
    text+=base.md_table(summary)+'\n\n### Coincidencia antes y después de PCA\n\n'+base.md_table(overlap_summary)
    text+='\n\nJaccard=1 significa las mismas sugerencias; 0 significa ninguna en común.\n\n'
    text+=f'''## Recomendación para la demostración

La interfaz inicia con **K-Means + PCA**, una configuración compacta y de fácil
interpretación. Recupera en promedio {km.recall_at_10:.1%} de los vecinos de la
referencia original en estas consultas. Esta configuración se eligió por el análisis
de clustering previo; la evaluación adicional no se utiliza para reoptimizarla.
El usuario puede comparar las cuatro alternativas y observar cambios reales.
La ventaja de Silhouette común de K-Means con PCA sobre el original es mínima;
no debe presentarse como una mejora importante ni estadísticamente demostrada.

## Cómo defenderlo

“Agrupé canciones usando diez características de sonido. Comparé dos métodos
antes y después de resumir los datos con PCA. Después construí un explorador
que busca canciones cercanas y permite comparar las sugerencias. Evalué cuánto
se conservan los vecinos geométricos, pero no afirmo que el sistema conozca los
gustos de una persona. La popularidad se utiliza solo como dato descriptivo o filtro.”

## Limitaciones y siguiente paso

- Las características agregadas no captan completamente melodía, letra ni estructura.
- Los registros de popularidad son históricos y no equivalen a reproducciones actuales.
- Puede haber versiones distintas con identificadores diferentes y alias de artistas.
- La división evita canciones iguales, pero no todos los artistas compartidos entre train y test.
- El filtro de artistas se aplica a las sugerencias, no transforma la división en una partición por artista.
- No se ha realizado una evaluación humana de utilidad; sería el siguiente paso.
- Abrir Spotify requiere conexión; el explorador, sus datos y cálculos funcionan offline.

## Referencias y reproducibilidad

Fuente: Pandya, M. (s. f.). *Spotify Tracks Dataset*. Hugging Face.
https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset

El dataset bruto, su huella SHA-256 y versiones de dependencias están incluidos.
Consultar la licencia declarada y términos originales antes de redistribuir datos.
Se reutilizó el experimento base y se reprodujeron sus cuatro particiones con ARI=1.
Código: proyecto_musica.py y construir_explorador.py. Se utilizó ChatGPT/Codex
para implementación, documentación y revisión; declarar esta asistencia en la entrega.
'''
    (OUT/'informe_explorador.md').write_text(text,encoding='utf-8')
    import re
    def inline(s):
        return re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',html.escape(s))
    blocks=[]
    for block in text.split('\n\n'):
        if block.startswith('#'):
            level=len(block)-len(block.lstrip('#'))
            blocks.append(f'<h{level}>'+inline(block[level:].strip())+f'</h{level}>')
        elif block.startswith('|'):
            rows=block.splitlines()
            def row(line,tag):
                return '<tr>'+''.join(f'<{tag}>'+inline(v.strip())+f'</{tag}>' for v in line.strip('|').split('|'))+'</tr>'
            blocks.append('<div class="table"><table>'+row(rows[0],'th')+''.join(row(line,'td') for line in rows[2:])+'</table></div>')
        elif block.startswith('- '):
            blocks.append('<ul>'+''.join('<li>'+inline(part.strip())+'</li>' for part in block[2:].split('\n- '))+'</ul>')
        else:
            blocks.append('<p>'+inline(block)+'</p>')
    document='<!doctype html><html lang="es"><meta charset="utf-8"><title>Informe del explorador musical</title><style>body{max-width:1000px;margin:40px auto;padding:20px;font:16px/1.7 system-ui;color:#183044}a{color:#006b7b}h1,h2,h3{color:#124e68}.table{overflow:auto}table{border-collapse:collapse;font-size:13px}th,td{padding:10px;border:1px solid #c8d8e0}th{background:#e7f2f6}</style><p><a href="../Explorador_Musical.html">Abrir explorador</a> · <a href="informe.html">Experimento base y 12 preguntas</a></p>'+''.join(blocks)+'</html>'
    (OUT/'informe_explorador.html').write_text(document,encoding='utf-8')

if __name__=='__main__':
    with threadpool_limits(limits=1):
        build()
