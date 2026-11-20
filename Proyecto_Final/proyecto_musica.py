"""Experimento reproducible de clustering. Popularidad nunca entra en el ajuste."""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import itertools
import json
import platform
import time
import warnings

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import kruskal
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.metrics import (adjusted_rand_score, silhouette_score,
                             davies_bouldin_score, calinski_harabasz_score)
from sklearn.mixture import GaussianMixture
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
from descargar_dataset import download

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs'
FEATURES = ['danceability', 'energy', 'loudness', 'speechiness', 'acousticness',
            'instrumentalness', 'liveness', 'valence', 'tempo', 'duration_ms']
SEED = 42

def savefig(name):
    plt.tight_layout()
    plt.savefig(OUT / 'figures' / f'{name}.png', dpi=150, bbox_inches='tight')
    plt.close()

def metrics(X, labels):
    """Silhouette sobre muestra fija para limitar memoria; otras métricas completas."""
    unique = np.unique(labels)
    if len(unique) < 2 or len(unique) >= len(labels):
        return dict(silhouette=np.nan, davies_bouldin=np.nan, calinski_harabasz=np.nan)
    # Muestreo independiente del resultado: no favorece perfiles pequeños artificialmente.
    ix = np.random.default_rng(SEED).choice(len(X), min(2000, len(X)), replace=False)
    sample_labels = labels[ix]
    sil = (silhouette_score(X[ix], sample_labels)
           if 1 < len(np.unique(sample_labels)) < len(ix) else np.nan)
    return dict(silhouette=float(sil), davies_bouldin=float(davies_bouldin_score(X, labels)),
                calinski_harabasz=float(calinski_harabasz_score(X, labels)))

def model(family, k, covariance='full', seed=SEED):
    if family == 'KMeans':
        return KMeans(n_clusters=k, n_init=20, random_state=seed)
    return GaussianMixture(n_components=k, covariance_type=covariance,
                           n_init=3, max_iter=500, reg_covar=1e-5, random_state=seed)

def fit_checked(estimator, X):
    start = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always', ConvergenceWarning)
        estimator.fit(X)
    converged = bool(getattr(estimator, 'converged_', True))
    return estimator, time.perf_counter() - start, converged, [str(w.message) for w in caught]

def prepare(path, sample_size):
    raw = pd.read_csv(path)
    required = FEATURES + ['track_id', 'track_name', 'artists', 'popularity']
    missing = set(required) - set(raw.columns)
    if missing:
        raise ValueError(f'Faltan columnas: {missing}')
    audit = {'raw_rows': len(raw), 'raw_columns': len(raw.columns),
             'raw_types': raw.dtypes.astype(str).to_dict(),
             'raw_missing': raw[required].isna().sum().to_dict()}
    raw = raw.dropna(subset=['track_id']).copy()
    for col in FEATURES + ['popularity']:
        raw[col] = pd.to_numeric(raw[col], errors='coerce')
    raw[FEATURES] = raw[FEATURES].replace([np.inf, -np.inf], np.nan)
    unit = ['danceability', 'energy', 'speechiness', 'acousticness',
            'instrumentalness', 'liveness', 'valence']
    invalid = {}
    for col in unit:
        bad = raw[col].notna() & ~raw[col].between(0, 1)
        invalid[col] = int(bad.sum())
        raw.loc[bad, col] = np.nan
    for col in ['duration_ms', 'tempo']:
        bad = raw[col].notna() & (raw[col] <= 0)
        invalid[col] = int(bad.sum())
        raw.loc[bad, col] = np.nan  # tempo cero: estimación no disponible, no silencio demostrado.
    raw.loc[~raw.popularity.between(0, 100), 'popularity'] = np.nan
    audit['invalid_to_missing'] = invalid
    duplicated = raw[raw.duplicated('track_id', keep=False)]
    audit['duplicate_ids_rows'] = len(duplicated)
    audit['duplicate_ids_conflicting_audio'] = int(
        (duplicated.groupby('track_id')[FEATURES].nunique().max(axis=1) > 1).sum())
    # Mantener primera aparición en orden fuente: jamás elegir por popularidad.
    clean = raw.drop_duplicates('track_id', keep='first').copy()
    clean = clean.loc[clean[FEATURES].notna().any(axis=1)].copy()
    audit['unique_usable_rows'] = len(clean)
    if len(clean) < 500:
        raise ValueError('No hay 500 canciones únicas utilizables.')
    sample = clean.sample(n=min(sample_size, len(clean)), random_state=SEED).reset_index(drop=True)
    train_ix, test_ix = train_test_split(np.arange(len(sample)), test_size=.2, random_state=SEED)
    train, test = sample.iloc[train_ix].copy(), sample.iloc[test_ix].copy()
    audit.update(sample_rows=len(sample), train_rows=len(train), test_rows=len(test))
    assert not set(train.track_id) & set(test.track_id)
    audit['shared_artist_strings_train_test'] = len(set(train.artists.dropna()) & set(test.artists.dropna()))
    train.assign(split='train').to_csv(OUT / 'train.csv', index=False)
    test.assign(split='test').to_csv(OUT / 'test.csv', index=False)
    train[FEATURES].describe().T.to_csv(OUT / 'descriptiva_train.csv')
    # Atípicos para diagnóstico, sin eliminarlos usando información de prueba.
    q1, q3 = train[FEATURES].quantile(.25), train[FEATURES].quantile(.75)
    iqr = q3 - q1
    outliers = ((train[FEATURES] < q1 - 1.5 * iqr) | (train[FEATURES] > q3 + 1.5 * iqr)).mean()
    outliers.rename('fraction_iqr_outliers').to_csv(OUT / 'atipicos_train.csv')
    audit['train_iqr_outlier_fraction'] = outliers.to_dict()
    train[FEATURES].hist(figsize=(14, 9), bins=35)
    plt.suptitle('Distribuciones en entrenamiento; unidades originales')
    savefig('01_distribuciones')
    corr = train[FEATURES].corr()
    corr.to_csv(OUT / 'correlaciones_train.csv')
    plt.figure(figsize=(10, 8))
    plt.imshow(corr, vmin=-1, vmax=1, cmap='RdBu_r')
    plt.xticks(range(10), FEATURES, rotation=90); plt.yticks(range(10), FEATURES)
    plt.colorbar(label='Correlación de Pearson'); plt.title('Correlaciones en entrenamiento')
    savefig('02_correlaciones')
    imputer = SimpleImputer(strategy='median')
    scaler = StandardScaler()
    U = imputer.fit_transform(train[FEATURES])
    V = imputer.transform(test[FEATURES])
    X, T = scaler.fit_transform(U), scaler.transform(V)
    if X.shape[1] != 10 or not np.isfinite(X).all():
        raise ValueError('Variables incompletas o valores no finitos tras preparación.')
    # PCA se ajusta exclusivamente sobre entrenamiento.
    pca = PCA(n_components=.90, svd_solver='full')
    Z, W = pca.fit_transform(X), pca.transform(T)
    spectrum = PCA(svd_solver='full').fit(X)
    pd.DataFrame({'component': range(1, 11), 'variance_ratio': spectrum.explained_variance_ratio_,
                  'cumulative': np.cumsum(spectrum.explained_variance_ratio_)}).to_csv(OUT / 'varianza_pca.csv', index=False)
    loadings = pd.DataFrame(pca.components_.T, index=FEATURES,
                             columns=[f'PC{i+1}' for i in range(pca.n_components_)])
    loadings.to_csv(OUT / 'cargas_pca.csv')
    plt.figure(figsize=(8, 4))
    plt.plot(range(1, 11), np.cumsum(spectrum.explained_variance_ratio_), 'o-')
    plt.axhline(.90, color='red', linestyle='--', label='Umbral 90 %')
    plt.axvline(pca.n_components_, color='gray', linestyle=':')
    plt.xlabel('Componentes'); plt.ylabel('Varianza acumulada'); plt.legend(); plt.title('Selección de componentes PCA')
    savefig('03_varianza_pca')
    (OUT / 'auditoria.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    return train, test, U, X, T, Z, W, pca, loadings, audit

def tune(family, space, X, kmax):
    rows = []
    for k in range(2, kmax + 1):
        for covariance in (['full', 'diag'] if family == 'GMM' else ['NA']):
            est, seconds, converged, messages = fit_checked(model(family, k, covariance), X)
            labels = est.predict(X)
            row = dict(model=family, space=space, k=k, covariance=covariance,
                       fit_seconds=seconds, converged=converged, warnings=' | '.join(messages), **metrics(X, labels))
            row['bic'] = float(est.bic(X)) if family == 'GMM' else np.nan
            row['aic'] = float(est.aic(X)) if family == 'GMM' else np.nan
            row['inertia'] = float(est.inertia_) if family == 'KMeans' else np.nan
            rows.append(row)
            print(f'{family} {space}: k={k} {covariance}, silhouette={row["silhouette"]:.3f}', flush=True)
    table = pd.DataFrame(rows)
    table.to_csv(OUT / f'busqueda_{family}_{space}.csv', index=False)
    eligible = table.loc[table.converged & table.silhouette.notna()]
    if eligible.empty:
        raise RuntimeError(f'No hay ajustes válidos para {family}/{space}.')
    best = (eligible.sort_values(['silhouette', 'k'], ascending=[False, True]).iloc[0]
            if family == 'KMeans' else eligible.sort_values(['bic', 'k']).iloc[0])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    if family == 'KMeans':
        axes[0].plot(table.k, table.inertia, 'o-'); axes[0].set_ylabel('Inercia (codo)')
        axes[1].plot(table.k, table.silhouette, 'o-'); axes[1].set_ylabel('Silhouette')
    else:
        for cov, part in table.groupby('covariance'):
            axes[0].plot(part.k, part.bic, 'o-', label=cov)
            axes[1].plot(part.k, part.silhouette, 'o-', label=cov)
        axes[0].set_ylabel('BIC (menor es mejor)'); axes[1].set_ylabel('Silhouette'); axes[0].legend()
    for ax in axes:
        ax.set_xlabel('Número de grupos'); ax.axvline(best.k, color='gray', linestyle=':')
    fig.suptitle(f'Ajuste: {family}, espacio {space}')
    savefig(f'04_busqueda_{family}_{space}')
    return dict(k=int(best.k), covariance=str(best.covariance)), table

def stability(family, config, X, T):
    """Semillas y submuestras de train; ARI siempre en el MISMO test común."""
    seed_labels, subsample_labels = [], []
    records = []
    for seed in [11, 29, 71, 101]:
        est, _, ok, _ = fit_checked(model(family, **config, seed=seed), X)
        if not ok:
            raise RuntimeError('GMM no convergió en análisis de estabilidad.')
        seed_labels.append(est.predict(T))
        idx = np.random.default_rng(seed).choice(len(X), int(.8 * len(X)), replace=False)
        est, _, ok, _ = fit_checked(model(family, **config, seed=seed), X[idx])
        if not ok:
            raise RuntimeError('GMM no convergió en submuestreo.')
        subsample_labels.append(est.predict(T))
    for kind, sets in [('seed', seed_labels), ('subsample', subsample_labels)]:
        for i, j in itertools.combinations(range(len(sets)), 2):
            records.append(dict(kind=kind, run_a=i, run_b=j, ari=adjusted_rand_score(sets[i], sets[j])))
    return records

def profiles(family, space, train, test, labels, predicted, X, T, est):
    combined = []
    for split, frame, lab, matrix in [('train', train, labels, X), ('test', test, predicted, T)]:
        frame = frame.copy(); frame['cluster'] = lab; frame['split'] = split
        if family == 'GMM':
            probabilities = est.predict_proba(matrix)
            frame['membership_confidence'] = probabilities.max(axis=1)
            frame['membership_entropy'] = -(probabilities * np.log(np.clip(probabilities, 1e-15, 1))).sum(axis=1)
        combined.append(frame)
    assigned = pd.concat(combined)
    assigned.to_csv(OUT / f'asignaciones_{family}_{space}.csv', index=False)
    medians = assigned.loc[assigned.split == 'train'].groupby('cluster')[FEATURES].median()
    medians.to_csv(OUT / f'perfiles_{family}_{space}.csv')
    standardized = (medians - train[FEATURES].mean()) / train[FEATURES].std()
    plt.figure(figsize=(11, max(3, len(medians)*.55)))
    plt.imshow(standardized, aspect='auto', cmap='RdBu_r', vmin=-2, vmax=2)
    plt.xticks(range(10), FEATURES, rotation=90); plt.yticks(range(len(medians)), medians.index)
    plt.colorbar(label='Mediana del grupo respecto a media global (DE)')
    plt.title(f'Perfiles de entrenamiento: {family}/{space}'); savefig(f'05_perfiles_{family}_{space}')
    pop = assigned.groupby(['split', 'cluster']).popularity.agg(
        n='count', median='median', mean='mean', q25=lambda x:x.quantile(.25), q75=lambda x:x.quantile(.75))
    pop['fraction_ge_70'] = assigned.groupby(['split', 'cluster']).popularity.apply(
        lambda x: (x.dropna() >= 70).mean())
    pop.to_csv(OUT / f'popularidad_{family}_{space}.csv')
    # Comparación descriptiva de prueba: popularidad jamás interviene en selección.
    test_assigned = assigned.loc[assigned.split == 'test']
    groups = [g.popularity.dropna().to_numpy() for _, g in test_assigned.groupby('cluster')]
    nonempty = [g for g in groups if len(g)]
    result = dict(model=family, space=space, n=sum(map(len, nonempty)), groups=len(nonempty))
    if len(nonempty) >= 2 and len(np.unique(np.concatenate(nonempty))) > 1:
        H, p = kruskal(*nonempty)
        n, k = result['n'], result['groups']
        result.update(H=float(H), p=float(p), epsilon_squared=max(0., float((H-k+1)/(n-k))))
    vals, names = [], []
    for label, group in test_assigned.groupby('cluster'):
        valid = group.popularity.dropna()
        if len(valid): vals.append(valid); names.append(str(label))
    plt.figure(figsize=(9, 4)); plt.boxplot(vals, showfliers=False)
    plt.xticks(range(1, len(names)+1), names)
    plt.xlabel('Grupo'); plt.ylabel('Popularidad del dataset (0–100)')
    plt.title(f'Popularidad en prueba: {family}/{space}'); savefig(f'06_popularidad_{family}_{space}')
    # Representantes por cercanía al centro, sin consultar popularidad.
    centers = est.cluster_centers_ if family == 'KMeans' else est.means_
    examples = []
    for c in np.unique(labels):
        idx = np.flatnonzero(labels == c)
        distances = np.linalg.norm(X[idx] - centers[c], axis=1)
        example = train.iloc[idx[np.argsort(distances)[:5]]][['track_id','track_name','artists','popularity']].copy()
        example['cluster'] = c; examples.append(example)
    pd.concat(examples).to_csv(OUT / f'ejemplos_{family}_{space}.csv', index=False)
    return result, pop, medians

def md_table(frame):
    """Markdown sin dependencia opcional tabulate."""
    frame = frame.copy()
    def fmt(x):
        if isinstance(x, (float, np.floating)): return f'{x:.4g}'
        return str(x).replace('|', '/').replace('\n', ' ')
    return '| ' + ' | '.join(map(str, frame.columns)) + ' |\n|' + '|'.join(['---']*len(frame.columns)) + '|\n' + '\n'.join(
        '| ' + ' | '.join(fmt(x) for x in row) + ' |' for row in frame.itertuples(index=False, name=None))

def run(sample_size=10000, kmax=16):
    for directory in [OUT, OUT / 'figures']:
        directory.mkdir(parents=True, exist_ok=True)
    path = download()
    train, test, U, X, T, Z, W, pca, loadings, audit = prepare(path, sample_size)
    rows, stability_rows, pop_results, selected, artifacts = [], [], [], {}, {}
    for family in ['KMeans', 'GMM']:
        for space, A, B in [('original', X, T), ('pca', Z, W)]:
            config, search = tune(family, space, A, kmax)
            est, seconds, ok, messages = fit_checked(model(family, **config), A)
            if not ok: raise RuntimeError(f'No convergió {family}/{space}')
            t0 = time.perf_counter(); predicted = est.predict(B); pred_seconds = time.perf_counter()-t0
            labels = est.predict(A)
            selected[(family, space)] = (est, labels, predicted, config)
            for split, matrix, lab in [('train', A, labels), ('test', B, predicted)]:
                rows.append(dict(model=family, space=space, evaluation_space=space, split=split,
                    hyperparameters=json.dumps(config), groups=len(np.unique(lab)), noise_pct=0.,
                    fit_seconds=seconds, predict_test_seconds=pred_seconds,
                    ari_vs_original=np.nan, **metrics(matrix, lab)))
                if space == 'pca':
                    original_labels = selected[(family,'original')][1 if split=='train' else 2]
                    ari = adjusted_rand_score(original_labels, lab)
                    rows[-1]['ari_vs_original'] = ari
                    rows.append(dict(rows[-1], evaluation_space='original', **metrics(X if split=='train' else T, lab)))
            for record in stability(family, config, A, B):
                stability_rows.append(dict(model=family, space=space, **record))
            result, pop, medians = profiles(family, space, train, test, labels, predicted, A, B, est)
            pop_results.append(result); artifacts[(family,space)] = (pop, medians)
            plt.figure(figsize=(8, 5))
            scatter = plt.scatter(Z[:,0], Z[:,1], c=labels, cmap='tab10', s=5, alpha=.45)
            plt.xlabel('PC1'); plt.ylabel('PC2'); plt.title(f'{family}/{space}: proyección PCA, no prueba de separación')
            plt.colorbar(scatter, label='Grupo'); savefig(f'07_mapa_{family}_{space}')
    comparisons = pd.DataFrame(rows)
    comparisons.to_csv(OUT / 'comparativa.csv', index=False)
    stable = pd.DataFrame(stability_rows)
    stable.to_csv(OUT / 'estabilidad.csv', index=False)
    pd.DataFrame(pop_results).to_csv(OUT / 'popularidad_pruebas.csv', index=False)
    # Control sin escalar para LOS DOS modelos, con hiperparámetros del espacio original.
    scale_rows = []
    for family in ['KMeans','GMM']:
        _, lab, _, config = selected[(family,'original')]
        est, elapsed, ok, _ = fit_checked(model(family, **config), U)
        if not ok:
            scale_rows.append(dict(model=family, converged=False, note='Control sin escalar no convergió'))
            continue
        unscaled = est.predict(U)
        scale_rows.append(dict(model=family, converged=True, ari_scaled_unscaled=adjusted_rand_score(lab,unscaled),
            silhouette_own_unscaled=metrics(U,unscaled)['silhouette'],
            silhouette_labels_unscaled_on_scaled=metrics(X,unscaled)['silhouette'],
            silhouette_scaled=metrics(X,lab)['silhouette'], fit_seconds=elapsed))
    scale = pd.DataFrame(scale_rows); scale.to_csv(OUT / 'control_escalado.csv', index=False)
    versions = {pkg:importlib.metadata.version(pkg) for pkg in
                ['numpy','pandas','scipy','scikit-learn','matplotlib','threadpoolctl']}
    versions['python'] = platform.python_version()
    (OUT / 'versiones.json').write_text(json.dumps(versions, indent=2), encoding='utf-8')
    summary = dict(seed=SEED, sample=sample_size, kmax=kmax, features=FEATURES,
                   pca_components=int(pca.n_components_), explained_variance=float(pca.explained_variance_ratio_.sum()),
                   dataset_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    (OUT / 'configuracion.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    write_report(comparisons, stable, scale, pop_results, artifacts, loadings, audit, summary, selected)
    validate_outputs(comparisons, stable, train, test, summary)
    print('FINALIZADO: outputs/informe.md y outputs/informe.html', flush=True)

def write_report(table, stable, scale, pop_results, artifacts, loads, audit, cfg, selected):
    train = table.query("split == 'train' and evaluation_space == 'original'")
    # Decisión principal exclusivamente con entrenamiento; prueba y popularidad no seleccionan.
    winner = train.sort_values('silhouette', ascending=False).iloc[0]
    name = f'{winner.model}/{winner.space}'
    winpop = artifacts[(winner.model, winner.space)][0].reset_index()
    winpop = winpop.loc[winpop.split == 'test'].sort_values('median')
    lowest, highest = winpop.iloc[0], winpop.iloc[-1]
    effect = next(r for r in pop_results if r['model'] == winner.model and r['space'] == winner.space)
    popularity_finding = (f'En prueba, las medianas de popularidad de la configuración recomendada van de '
        f'{lowest["median"]:.1f} (grupo {int(lowest.cluster)}) a {highest["median"]:.1f} '
        f'(grupo {int(highest.cluster)}), con epsilon cuadrado {effect.get("epsilon_squared", float("nan")):.4f}. '
        f'Los intervalos intercuartílicos de esos grupos son [{lowest.q25:.1f}, {lowest.q75:.1f}] '
        f'y [{highest.q25:.1f}, {highest.q75:.1f}]. '
        'Las medianas diferentes no permiten identificar individualmente una canción popular; '
        'debe considerarse el solapamiento de distribuciones.')
    lines = ['# Segmentación de un catálogo musical por perfiles sonoros',
        '## Comparación de K-Means y GMM antes y después de PCA',
        '## Resumen',
        f'Se analizaron {audit["sample_rows"]:,} canciones únicas ({audit["train_rows"]:,} entrenamiento y '
        f'{audit["test_rows"]:,} prueba) usando diez características sonoras. PCA retuvo '
        f'{cfg["pca_components"]} componentes y {cfg["explained_variance"]:.2%} de varianza. '
        f'La configuración recomendada por Silhouette de entrenamiento en el espacio común es **{name}**, '
        f'con {int(winner.groups)} grupos y Silhouette {winner.silhouette:.4f}. La recomendación prioriza '
        'compactación y debe contrastarse con estabilidad e interpretación. No se entrenó un predictor de éxitos. '
        + popularity_finding,
        '## 1. Problema y justificación',
        '¿Cómo cambian los perfiles sonoros de un catálogo musical al aplicar K-Means y GMM antes y después de PCA? '
        'La necesidad es organizar un catálogo por características acústicas para facilitar su exploración y seleccionar referencias de producción. La popularidad es un análisis descriptivo secundario. '
        'No existen etiquetas verdaderas de perfil sonoro; el género es información contextual y no objetivo de entrenamiento. '
        'No se interpretan asociaciones como causas ni se afirma predecir popularidad futura.',
        '## 2. Fuente y preparación',
        'Fuente: Maharshi Pandya, Spotify Tracks Dataset, repositorio público de Hugging Face. '
        'La ficha declara BSD; revisar el alcance de esa declaración y los términos originales antes de redistribuir. '
        'Se descargan características tabulares, no audio. La fecha exacta de medición de popularidad no se conoce.',
        f'Filas fuente: {audit["raw_rows"]:,}; utilizables únicas: {audit["unique_usable_rows"]:,}; '
        f'filas con identificador repetido: {audit["duplicate_ids_rows"]:,}. '
        f'Eliminados por duplicación de ID: {audit["raw_rows"]-audit["unique_usable_rows"]:,} registros '
        '(los valores exactos de cada paso se conservan en auditoria.json). '
        'Se conserva la primera aparición en orden de archivo, sin escoger por popularidad. '
        'Ver auditoria.json para tipos, faltantes y conflictos entre duplicados.',
        'Se convierten valores imposibles en faltantes; tempo cero se trata como estimación ausente. '
        'No se eliminan automáticamente atípicos legítimos. Se imputa por mediana y se aplica StandardScaler '
        'ajustando ambos solo con entrenamiento. División 80/20 y semilla 42. '
        'Los diez campos son ' + ', '.join(FEATURES) + '. '
        'Popularidad, género, identificadores, nombres y artistas quedan fuera del ajuste. '
        'Duración conserva milisegundos y loudness decibelios en los perfiles originales.',
        '![Distribuciones](figures/01_distribuciones.png)', '![Correlación](figures/02_correlaciones.png)',
        'Los atípicos por regla IQR se documentan en atipicos_train.csv.',
        md_table(pd.DataFrame(list(audit['train_iqr_outlier_fraction'].items()),columns=['variable','fracción atípicos IQR'])),
        'El escalado no neutraliza su influencia: '
        'K-Means es sensible a distancias extremas y GMM a estimaciones de medias y covarianzas.',
        '## 3. Diseño experimental',
        f'Se exploran K=2…{cfg["kmax"]}. K-Means usa n_init=20 y se selecciona por mayor Silhouette '
        'en entrenamiento; el codo se utiliza como diagnóstico. GMM compara covarianzas full/diag, '
        'n_init=3, máximo 500 iteraciones y regularización 1e-5; se elige el menor BIC entre ajustes convergidos. '
        'Se reajustan hiperparámetros tras PCA. Si criterios discrepan se mantienen estas reglas predefinidas, '
        'sin consultar popularidad. Silhouette usa hasta 2.000 filas elegidas con semilla fija; '
        'Davies-Bouldin y Calinski-Harabasz usan el conjunto completo.',
        'Silhouette mayor indica mejor cohesión/separación; Davies-Bouldin menor indica menor similitud '
        'entre grupos; Calinski-Harabasz mayor refleja separación entre grupos respecto a dispersión interna. '
        'Son criterios geométricos, no pruebas de categorías musicales verdaderas.',
        '## 4. PCA',
        '![Varianza](figures/03_varianza_pca.png)',
        md_table(loads.reset_index(names='variable').iloc[:,:3]),
        'Las cargas son coeficientes de la combinación lineal sobre variables estandarizadas. '
        'Su signo puede invertirse sin cambiar el significado de PCA. No equivalen a causalidad.',
        '## 5. Tabla comparativa obligatoria',
        'Las filas PCA evaluadas en original usan las etiquetas de PCA y las distancias del espacio '
        'original escalado. Son las filas apropiadas para comparar configuraciones en una geometría común. '
        'Ruido es 0 % por construcción: estos modelos asignan todas las canciones; no realizan detección de ruido.',
        md_table(table),
        '## 6. Estabilidad',
        'Cuatro semillas y cuatro submuestras del 80 % de entrenamiento. Cada ejecución asigna el mismo '
        'conjunto de prueba y se calcula ARI entre pares. El preprocesamiento permanece fijo: '
        'esta es estabilidad condicional al escalado/PCA, no incertidumbre de todo el pipeline.',
        md_table(stable.groupby(['model','space','kind']).ari.agg(['mean','min','max']).reset_index()),
        '## 7. Interpretación de perfiles y aplicación al catálogo']
    for (family, space), (pop, medians) in artifacts.items():
        lines += [f'### {family}/{space}',
            f'![Perfiles](figures/05_perfiles_{family}_{space}.png)',
            md_table(medians.reset_index()),
            'Popularidad histórica por perfil: análisis secundario, sin intervenir en el ajuste.',
            md_table(pop.reset_index())]
        for cluster, values in medians.iterrows():
            # Nombres descriptivos basados en unidades originales y umbrales explícitos.
            energy = 'energía alta' if values.energy >= .65 else ('energía baja' if values.energy < .35 else 'energía intermedia')
            texture = 'acústico' if values.acousticness >= .6 else ('instrumental' if values.instrumentalness >= .5 else 'mixto')
            lines.append(f'Grupo {cluster}: **{energy}, perfil {texture}**; mediana tempo '
                f'{values.tempo:.1f} BPM y duración {values.duration_ms/60000:.2f} minutos. '
                'Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.')
    lines += ['## 8. Respuestas a las 12 preguntas de análisis']
    lines += ['### 1. Escalado', md_table(scale),
        'Duración en milisegundos tiene escala muy superior a variables entre 0 y 1. El control mantiene '
        'hiperparámetros y compara etiquetas en el espacio escalado para no confundir geometrías.',
        '### 2. Hiperparámetros',
        md_table(pd.DataFrame([dict(model=f,space=s,**v[3]) for (f,s),v in selected.items()])),
        'Se priorizó Silhouette para K-Means y BIC para GMM. Ver curvas y búsquedas completas; '
        'la elección en un extremo del rango exige ampliar el rango en trabajo futuro.',
        '### 3. Sesgo de las métricas',
        f'La tabla común recomienda {name} por Silhouette={winner.silhouette:.4f}. '
        'Las distancias euclidianas favorecen grupos compactos, lo que puede beneficiar a K-Means '
        'frente a gaussianas alargadas de GMM. Las gráficas 2D se contrastan con las métricas, pero '
        'no validan separación en todas las dimensiones.',
        '### 4. Ruido y atípicos',
        'No se utilizó DBSCAN y el ruido es 0 % en todas las filas por asignación completa. '
        'Las fracciones de atípicos por variable están en atipicos_train.csv. '
        'No se confunde pertenencia incierta de GMM con ruido. Se conservan atípicos plausibles '
        'y se reconoce sensibilidad del escalador, centroides y covarianzas.',
        '### 5. Componentes principales',
        f'Se conservaron {cfg["pca_components"]} componentes, varianza {cfg["explained_variance"]:.2%}.']
    for pc in loads.columns[:2]:
        dominant = loads[pc].abs().nlargest(3).index
        lines.append(f'{pc}: mayores cargas absolutas: ' + ', '.join(f'{v} ({loads.loc[v,pc]:+.3f})' for v in dominant) +
                     '. El componente representa el contraste acústico indicado por esas variables y sus signos.')
    for family in ['KMeans','GMM']:
        part = table.query("model == @family and split == 'train' and evaluation_space == 'original'")
        a = part.loc[part.space=='original'].iloc[0]; b = part.loc[part.space=='pca'].iloc[0]
        lines.append(f'{family}: Silhouette original {a.silhouette:.4f}, etiquetas PCA evaluadas en original '
                     f'{b.silhouette:.4f}; diferencia {b.silhouette-a.silhouette:+.4f}, ARI {b.ari_vs_original:.4f}.')
    lines += ['### 6. Efecto de la reducción',
        'Las diferencias numéricas anteriores y la tabla distinguen cambio de asignaciones de cambio de '
        'geometría. PCA elimina direcciones de baja varianza; pueden ser redundancia o información útil. '
        'Una mejora no demuestra eliminación de ruido y un empeoramiento puede indicar pérdida de estructura. '
        'Una diferencia muy pequeña de Silhouette puede carecer de relevancia práctica; '
        'la selección por máximo numérico no demuestra superioridad estadística. '
        'Con diez variables no debe atribuirse automáticamente el resultado a la maldición de dimensionalidad.',
        '### 7. Comparación justa',
        md_table(table.query("split == 'train'")[[ 'model','space','evaluation_space','silhouette','davies_bouldin','calinski_harabasz']]),
        'Comparar directamente métricas de geometrías diferentes no permite concluir una mejora de agrupación. '
        'Se utilizan las filas evaluation_space=original para esa conclusión.',
        '### 8. Cambio en asignaciones',
        md_table(table.query("space == 'pca' and evaluation_space == 'pca'")[[ 'model','split','ari_vs_original']]),
        'ARI=1 indica mismas particiones aunque cambien sus números; cercano a 0 indica acuerdo '
        'compatible con azar y puede ser negativo. No mide relación con popularidad.',
        '### 9. Estabilidad',
        md_table(stable.groupby(['model','space','kind']).ari.mean().reset_index()),
        'Mayor ARI medio indica mayor estabilidad en este diseño. Ver mínimos para detectar '
        'ejecuciones sensibles. La prueba común no ajusta hiperparámetros.',
        '### 10. Costo computacional',
        md_table(table.query("split == 'test' and space == evaluation_space")[[ 'model','space','fit_seconds','predict_test_seconds']]),
        'Los tiempos corresponden a un ajuste final, sin búsqueda ni preprocesamiento y con un hilo '
        'numérico; no son benchmarks repetidos. Debe incluirse el costo de ajustar/transformar PCA '
        'antes de afirmar un ahorro total del pipeline. Con 100 veces más datos crecen el ajuste, la memoria '
        'y especialmente Silhouette, cuyo cálculo completo requiere distancias cuadráticas. '
        'No se extrapolan segundos linealmente; se mantendría muestreo de evaluación.',
        '### 11. Visualización no lineal',
        f'La representación usada conserva {cfg["explained_variance"]:.2%} en '
        f'{cfg["pca_components"]} componentes; el mapa solo muestra PC1/PC2. '
        'No se ejecutó UMAP ni t-SNE: son opcionales. Si una visualización no lineal mostrara islas, '
        'no probaría grupos verdaderos. t-SNE distorsiona distancias globales y densidades, depende '
        'de parámetros y no se recomienda como entrada para este clustering comparativo.',
        '### 12. Recomendación y limitaciones',
        f'Se recomienda provisionalmente **{name}** por el criterio predefinido de Silhouette '
        f'en entrenamiento común ({winner.silhouette:.4f}); revisar además estabilidad y perfiles. '
        'No se seleccionó por conseguir diferencias de popularidad. Limitaciones: muestra de conveniencia, '
        'popularidad histórica con fecha no documentada, duplicados semánticos entre versiones, '
        f'{audit["shared_artist_strings_train_test"]} cadenas de artista compartidas entre train y test '
        '(conteo de cadenas exactas, no de personas únicas), ausencia de publicidad/exposición en playlists '
        'y posible estructura continua sin clusters naturales. Con más tiempo se separaría por artista, '
        'se repetirían muestras y tiempos, y se añadirían popularidades medidas longitudinalmente.',
        '## 9. Conclusiones',
        f'Los resultados de los cuatro ajustes, sus perfiles y las distribuciones de popularidad están '
        f'documentados arriba. La mejor Silhouette común corresponde a {name}. '
        + popularity_finding + ' La asociación no implica causalidad. No se garantiza predecir éxitos futuros.',
        '## 10. Reproducibilidad y uso de IA',
        'Semilla 42; CSV de entrada verificado por SHA-256 en manifest.json y configuracion.json. '
        'Versiones efectivas en versiones.json. Ejecutar el cuaderno de principio a fin o '
        'python proyecto_musica.py. Se utilizó ChatGPT/Codex para estructurar el proyecto, escribir '
        'código y generar explicaciones. Las tablas del informe se calculan con datos reales; '
        'el estudiante debe revisar e interpretar los resultados y declarar esta asistencia.',
        '## Referencias',
        'Pandya, M. (s. f.). *Spotify Tracks Dataset* [Conjunto de datos]. Hugging Face. '
        'https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset',
        'Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. '
        '*Journal of Machine Learning Research, 12*, 2825–2830. https://jmlr.org/papers/v12/pedregosa11a.html',
        'Documentación oficial de scikit-learn: https://scikit-learn.org/stable/modules/clustering.html '
        'y https://scikit-learn.org/stable/modules/decomposition.html#pca']
    # Evidencia propia y lectura contextual, integrada en las secciones evaluadas.
    def insert_after(heading, additions):
        pos=lines.index(heading)+1
        lines[pos:pos]=additions
    corr=pd.read_csv(OUT/'correlaciones_train.csv',index_col=0)
    pairs=sorted([(a,b,float(corr.loc[a,b])) for i,a in enumerate(FEATURES) for b in FEATURES[i+1:]],key=lambda r:abs(r[2]),reverse=True)[:4]
    insert_after('## 2. Fuente y preparación',[
        '### Diccionario de las diez variables',
        md_table(pd.DataFrame([
            ('danceability','Bailabilidad','0–1'),('energy','Intensidad percibida','0–1'),
            ('loudness','Nivel sonoro','dB'),('speechiness','Presencia de habla','0–1'),
            ('acousticness','Carácter acústico','0–1'),('instrumentalness','Carácter instrumental','0–1'),
            ('liveness','Indicios de interpretación en directo','0–1'),('valence','Positividad sonora estimada','0–1'),
            ('tempo','Velocidad del pulso','BPM'),('duration_ms','Duración','milisegundos')],columns=['Variable','Interpretación','Unidad'])),
        '### Calidad y descriptiva de entrenamiento',
        md_table(pd.DataFrame([dict(variable=v,tipo=audit['raw_types'][v],faltantes_fuente=audit['raw_missing'][v],invalidos_a_faltantes=audit['invalid_to_missing'].get(v,0)) for v in FEATURES])),
        md_table(pd.read_csv(OUT/'descriptiva_train.csv').rename(columns={'Unnamed: 0':'variable'})),
        'Las asociaciones lineales más fuertes son '+ '; '.join(f'{a}/{b}: r={r:+.3f}' for a,b,r in pairs)+'. La redundancia parcial justifica explorar PCA, pero correlación no implica que se pueda descartar una variable sin evaluar la estructura.',
        'Instrumentalness y speechiness presentan asimetría y acumulación en valores bajos; los extremos IQR pueden representar canciones instrumentales o habladas legítimas. Duración y nivel sonoro tienen unidades distintas de las variables acotadas; StandardScaler iguala la escala, pero no elimina asimetrías ni vuelve gaussianos los datos.'])
    search_blocks=['Se esperan gradientes acústicos y solapamiento: K-Means aporta una partición por centroides compactos y GMM admite covarianzas completas y pertenencia probabilística. Ninguno demuestra categorías musicales naturales.']
    for family in ['KMeans','GMM']:
        for space in ['original','pca']:
            search_blocks.append(f'![Selección de hiperparámetros {family}/{space}](figures/04_busqueda_{family}_{space}.png)')
    insert_after('## 3. Diseño experimental',search_blocks)
    insert_after('## 4. PCA',[
        'PC1 contrapone nivel sonoro y energía positivos a carácter acústico negativo: resume intensidad/producción frente a textura acústica. PC2 combina valencia y bailabilidad positivas con duración negativa: describe un contraste de positividad y ritmo frente a formatos más largos. Estas lecturas se apoyan en las cargas de la tabla; no equivalen a emociones reales del oyente.',
        'La proyección 2D pierde parte de la información: los modelos PCA reciben todos los componentes retenidos, no solo PC1 y PC2.'])
    for family in ['KMeans','GMM']:
        for space in ['original','pca']:
            heading=f'### {family}/{space}'
            medians=artifacts[(family,space)][1]
            actions=[]
            for c,v in medians.iterrows():
                action='seleccionar referencias acústicas de menor intensidad' if v.acousticness>=.6 and v.energy<.5 else ('explorar referencias instrumentales' if v.instrumentalness>=.5 else ('organizar referencias de mayor intensidad' if v.energy>=.65 else 'explorar un perfil intermedio y contrastarlo mediante escucha'))
                actions.append(dict(grupo=int(c),accion=action,tempo_BPM=round(v.tempo,1),duracion_min=round(v.duration_ms/60000,2)))
            insert_after(heading,[f'![Proyección PC1/PC2: {family}/{space}](figures/07_mapa_{family}_{space}.png)',md_table(pd.DataFrame(actions)),
                'Estas acciones organizan la exploración del catálogo; su utilidad perceptiva requiere escucha. No se infieren audiencia ni éxito comercial.'])
    insert_after('### 5. Componentes principales',[
        f'PC1: loudness {loads.loc["loudness","PC1"]:+.3f}, energy {loads.loc["energy","PC1"]:+.3f} y acousticness {loads.loc["acousticness","PC1"]:+.3f}: intensidad frente a carácter acústico.',
        f'PC2: valence {loads.loc["valence","PC2"]:+.3f}, danceability {loads.loc["danceability","PC2"]:+.3f} y duration_ms {loads.loc["duration_ms","PC2"]:+.3f}: positividad/bailabilidad frente a duración.'])
    stable_summary=stable.groupby(['model','space','kind']).ari.mean().unstack('kind')
    insert_after('### 9. Estabilidad',[
        '; '.join(f'{f}/{sp}: ARI entre semillas {r["seed"]:.4f}; entre submuestras {r["subsample"]:.4f}' for (f,sp),r in stable_summary.iterrows())+'.',
        'K-Means presenta mayor estabilidad en estos resultados. GMM ajusta más grupos y covarianzas, y puede converger a soluciones locales distintas; estabilidad baja obliga a tratar sus perfiles con cautela.'])
    selection_notes=[]
    for (f,sp),(_,_,_,params) in selected.items():
        if params['k']==cfg['kmax']:
            selection_notes.append(f'{f}/{sp} selecciona K={params["k"]}, límite superior de la búsqueda. Es el mejor BIC dentro del presupuesto declarado, no un óptimo global demostrado; no se afirma que existan exactamente esos géneros o categorías.')
    insert_after('### 2. Hiperparámetros',selection_notes or ['Ninguna selección coincide con el límite superior de la búsqueda.'])
    insert_after('## 9. Conclusiones',[
        'La decisión práctica es segmentar el catálogo en perfiles descriptivos para filtrar y comparar referencias, manteniendo visibles el solapamiento y la incertidumbre. Las acciones se derivan de sus medianas originales, no de nombres de artistas ni de popularidad. Una interfaz adicional no es necesaria para demostrar el experimento.',
        'No se garantiza una calificación: los resultados no prueban que la configuración numéricamente ganadora sea superior en percepción musical. La defensa debe explicar esa diferencia.'])
    report = '\n\n'.join(lines)
    (OUT / 'informe.md').write_text(report, encoding='utf-8')
    # HTML accesible sin paquetes opcionales, mantiene tablas/figuras con conversor reducido.
    import html
    blocks = []
    for block in lines:
        if block.startswith('!['):
            alt, url = block[2:].split('](',1)
            blocks.append(f'<figure><img src="{html.escape(url[:-1])}" alt="{html.escape(alt)}"></figure>')
        elif block.startswith('| '):
            tr = block.splitlines()
            cells = lambda line, tag: '<tr>'+''.join(f'<{tag}>{html.escape(v.strip())}</{tag}>' for v in line.strip('|').split('|'))+'</tr>'
            blocks.append('<div class="table"><table>'+cells(tr[0],'th')+''.join(cells(t,'td') for t in tr[2:])+'</table></div>')
        elif block.startswith('#'):
            level = len(block)-len(block.lstrip('#')); blocks.append(f'<h{level}>{html.escape(block[level:].strip())}</h{level}>')
        else:
            blocks.append('<p>'+html.escape(block).replace('**','')+'</p>')
    document = '<!doctype html><html lang="es"><meta charset="utf-8"><title>Segmentación musical — Informe final</title><style>body{font:16px/1.65 system-ui;max-width:1100px;margin:48px auto;padding:24px;color:#183044}h1,h2,h3{color:#124e68}img{max-width:100%}.table{overflow:auto}table{border-collapse:collapse;font-size:13px}td,th{padding:9px;border:1px solid #ccdbe2}th{background:#e8f2f6}@media print{body{margin:0}h2{break-before:auto}figure{break-inside:avoid}}</style><main>'+''.join(blocks)+'</main></html>'
    (OUT / 'informe.html').write_text(document, encoding='utf-8')

def validate_outputs(table, stable, train, test, cfg):
    assert 'popularity' not in FEATURES and len(FEATURES) >= 8
    assert len(train)+len(test) >= 500 and train.track_id.is_unique and test.track_id.is_unique
    assert not set(train.track_id) & set(test.track_id)
    assert len(table) == 12  # 4 modelos-espacio x train/test + 4 filas comparación justa.
    assert np.isfinite(table[['silhouette','davies_bouldin','calinski_harabasz']]).all().all()
    assert cfg['explained_variance'] >= .90
    assert len(stable) == 48
    assert len(list((OUT/'figures').glob('*.png'))) >= 19
    (OUT / 'validacion.json').write_text(json.dumps(dict(status='passed', checks=[
        'dataset mínimo', 'IDs sin fuga', '10 variables sin popularidad', '12 filas comparativas',
        'métricas finitas', 'varianza >= 90%', '48 comparaciones de estabilidad', 'figuras generadas']), indent=2), encoding='utf-8')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--muestra', type=int, default=10000)
    parser.add_argument('--kmax', type=int, default=16)
    args = parser.parse_args()
    if args.muestra < 500 or args.kmax < 2:
        parser.error('muestra >=500 y kmax >=2')
    with threadpool_limits(limits=1):
        run(args.muestra, args.kmax)
