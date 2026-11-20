# Segmentación de un catálogo musical por perfiles sonoros

## Comparación de K-Means y GMM antes y después de PCA

## Resumen

Se analizaron 10,000 canciones únicas (8,000 entrenamiento y 2,000 prueba) usando diez características sonoras. PCA retuvo 7 componentes y 90.81% de varianza. La configuración recomendada por Silhouette de entrenamiento en el espacio común es **KMeans/pca**, con 2 grupos y Silhouette 0.2497. La recomendación prioriza compactación y debe contrastarse con estabilidad e interpretación. No se entrenó un predictor de éxitos. En prueba, las medianas de popularidad de la configuración recomendada van de 28.0 (grupo 1) a 35.0 (grupo 0), con epsilon cuadrado 0.0071. Los intervalos intercuartílicos de esos grupos son [13.0, 47.0] y [21.0, 49.0]. Las medianas diferentes no permiten identificar individualmente una canción popular; debe considerarse el solapamiento de distribuciones.

## 1. Problema y justificación

¿Cómo cambian los perfiles sonoros de un catálogo musical al aplicar K-Means y GMM antes y después de PCA? La necesidad es organizar un catálogo por características acústicas para facilitar su exploración y seleccionar referencias de producción. La popularidad es un análisis descriptivo secundario. No existen etiquetas verdaderas de perfil sonoro; el género es información contextual y no objetivo de entrenamiento. No se interpretan asociaciones como causas ni se afirma predecir popularidad futura.

## 2. Fuente y preparación

### Diccionario de las diez variables

| Variable | Interpretación | Unidad |
|---|---|---|
| danceability | Bailabilidad | 0–1 |
| energy | Intensidad percibida | 0–1 |
| loudness | Nivel sonoro | dB |
| speechiness | Presencia de habla | 0–1 |
| acousticness | Carácter acústico | 0–1 |
| instrumentalness | Carácter instrumental | 0–1 |
| liveness | Indicios de interpretación en directo | 0–1 |
| valence | Positividad sonora estimada | 0–1 |
| tempo | Velocidad del pulso | BPM |
| duration_ms | Duración | milisegundos |

### Calidad y descriptiva de entrenamiento

| variable | tipo | faltantes_fuente | invalidos_a_faltantes |
|---|---|---|---|
| danceability | float64 | 0 | 0 |
| energy | float64 | 0 | 0 |
| loudness | float64 | 0 | 0 |
| speechiness | float64 | 0 | 0 |
| acousticness | float64 | 0 | 0 |
| instrumentalness | float64 | 0 | 0 |
| liveness | float64 | 0 | 0 |
| valence | float64 | 0 | 0 |
| tempo | float64 | 0 | 157 |
| duration_ms | int64 | 0 | 1 |

| variable | count | mean | std | min | 25% | 50% | 75% | max |
|---|---|---|---|---|---|---|---|---|
| danceability | 8000 | 0.5644 | 0.1766 | 0 | 0.454 | 0.5785 | 0.694 | 0.98 |
| energy | 8000 | 0.6344 | 0.2551 | 2.01e-05 | 0.457 | 0.675 | 0.852 | 1 |
| loudness | 8000 | -8.5 | 5.113 | -40.61 | -10.41 | -7.176 | -5.126 | 0.681 |
| speechiness | 8000 | 0.08823 | 0.115 | 0 | 0.0359 | 0.0488 | 0.0855 | 0.959 |
| acousticness | 8000 | 0.3262 | 0.3357 | 0 | 0.01767 | 0.189 | 0.6172 | 0.996 |
| instrumentalness | 8000 | 0.1706 | 0.3218 | 0 | 0 | 6.265e-05 | 0.08968 | 1 |
| liveness | 8000 | 0.2147 | 0.1928 | 0.00986 | 0.0981 | 0.131 | 0.272 | 0.991 |
| valence | 8000 | 0.4744 | 0.2613 | 0 | 0.261 | 0.465 | 0.687 | 0.991 |
| tempo | 7979 | 122.1 | 29.61 | 35.79 | 99.35 | 122.1 | 140.1 | 220 |
| duration_ms | 8000 | 2.279e+05 | 1.004e+05 | 1.339e+04 | 1.721e+05 | 2.126e+05 | 2.63e+05 | 2.647e+06 |

Las asociaciones lineales más fuertes son energy/loudness: r=+0.753; energy/acousticness: r=-0.727; loudness/acousticness: r=-0.572; danceability/valence: r=+0.498. La redundancia parcial justifica explorar PCA, pero correlación no implica que se pueda descartar una variable sin evaluar la estructura.

Instrumentalness y speechiness presentan asimetría y acumulación en valores bajos; los extremos IQR pueden representar canciones instrumentales o habladas legítimas. Duración y nivel sonoro tienen unidades distintas de las variables acotadas; StandardScaler iguala la escala, pero no elimina asimetrías ni vuelve gaussianos los datos.

Fuente: Maharshi Pandya, Spotify Tracks Dataset, repositorio público de Hugging Face. La ficha declara BSD; revisar el alcance de esa declaración y los términos originales antes de redistribuir. Se descargan características tabulares, no audio. La fecha exacta de medición de popularidad no se conoce.

Filas fuente: 114,000; utilizables únicas: 89,741; filas con identificador repetido: 40,900. Eliminados por duplicación de ID: 24,259 registros (los valores exactos de cada paso se conservan en auditoria.json). Se conserva la primera aparición en orden de archivo, sin escoger por popularidad. Ver auditoria.json para tipos, faltantes y conflictos entre duplicados.

Se convierten valores imposibles en faltantes; tempo cero se trata como estimación ausente. No se eliminan automáticamente atípicos legítimos. Se imputa por mediana y se aplica StandardScaler ajustando ambos solo con entrenamiento. División 80/20 y semilla 42. Los diez campos son danceability, energy, loudness, speechiness, acousticness, instrumentalness, liveness, valence, tempo, duration_ms. Popularidad, género, identificadores, nombres y artistas quedan fuera del ajuste. Duración conserva milisegundos y loudness decibelios en los perfiles originales.

![Distribuciones](figures/01_distribuciones.png)

![Correlación](figures/02_correlaciones.png)

Los atípicos por regla IQR se documentan en atipicos_train.csv.

| variable | fracción atípicos IQR |
|---|---|
| danceability | 0.007625 |
| energy | 0 |
| loudness | 0.05187 |
| speechiness | 0.122 |
| acousticness | 0 |
| instrumentalness | 0.2184 |
| liveness | 0.07925 |
| valence | 0 |
| tempo | 0.00525 |
| duration_ms | 0.046 |

El escalado no neutraliza su influencia: K-Means es sensible a distancias extremas y GMM a estimaciones de medias y covarianzas.

## 3. Diseño experimental

Se esperan gradientes acústicos y solapamiento: K-Means aporta una partición por centroides compactos y GMM admite covarianzas completas y pertenencia probabilística. Ninguno demuestra categorías musicales naturales.

![Selección de hiperparámetros KMeans/original](figures/04_busqueda_KMeans_original.png)

![Selección de hiperparámetros KMeans/pca](figures/04_busqueda_KMeans_pca.png)

![Selección de hiperparámetros GMM/original](figures/04_busqueda_GMM_original.png)

![Selección de hiperparámetros GMM/pca](figures/04_busqueda_GMM_pca.png)

Se exploran K=2…16. K-Means usa n_init=20 y se selecciona por mayor Silhouette en entrenamiento; el codo se utiliza como diagnóstico. GMM compara covarianzas full/diag, n_init=3, máximo 500 iteraciones y regularización 1e-5; se elige el menor BIC entre ajustes convergidos. Se reajustan hiperparámetros tras PCA. Si criterios discrepan se mantienen estas reglas predefinidas, sin consultar popularidad. Silhouette usa hasta 2.000 filas elegidas con semilla fija; Davies-Bouldin y Calinski-Harabasz usan el conjunto completo.

Silhouette mayor indica mejor cohesión/separación; Davies-Bouldin menor indica menor similitud entre grupos; Calinski-Harabasz mayor refleja separación entre grupos respecto a dispersión interna. Son criterios geométricos, no pruebas de categorías musicales verdaderas.

## 4. PCA

PC1 contrapone nivel sonoro y energía positivos a carácter acústico negativo: resume intensidad/producción frente a textura acústica. PC2 combina valencia y bailabilidad positivas con duración negativa: describe un contraste de positividad y ritmo frente a formatos más largos. Estas lecturas se apoyan en las cargas de la tabla; no equivalen a emociones reales del oyente.

La proyección 2D pierde parte de la información: los modelos PCA reciben todos los componentes retenidos, no solo PC1 y PC2.

![Varianza](figures/03_varianza_pca.png)

| variable | PC1 | PC2 |
|---|---|---|
| danceability | 0.2731 | 0.435 |
| energy | 0.4977 | -0.2916 |
| loudness | 0.5121 | -0.09364 |
| speechiness | 0.1056 | 0.1414 |
| acousticness | -0.4276 | 0.3594 |
| instrumentalness | -0.29 | -0.3315 |
| liveness | 0.05869 | -0.08664 |
| valence | 0.319 | 0.4618 |
| tempo | 0.1747 | -0.2438 |
| duration_ms | -0.0409 | -0.4216 |

Las cargas son coeficientes de la combinación lineal sobre variables estandarizadas. Su signo puede invertirse sin cambiar el significado de PCA. No equivalen a causalidad.

## 5. Tabla comparativa obligatoria

Las filas PCA evaluadas en original usan las etiquetas de PCA y las distancias del espacio original escalado. Son las filas apropiadas para comparar configuraciones en una geometría común. Ruido es 0 % por construcción: estos modelos asignan todas las canciones; no realizan detección de ruido.

| model | space | evaluation_space | split | hyperparameters | groups | noise_pct | fit_seconds | predict_test_seconds | ari_vs_original | silhouette | davies_bouldin | calinski_harabasz |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KMeans | original | original | train | {"k": 2, "covariance": "NA"} | 2 | 0 | 0.1542 | 0.0005511 | nan | 0.2493 | 1.683 | 1948 |
| KMeans | original | original | test | {"k": 2, "covariance": "NA"} | 2 | 0 | 0.1542 | 0.0005511 | nan | 0.246 | 1.679 | 493.5 |
| KMeans | pca | pca | train | {"k": 2, "covariance": "NA"} | 2 | 0 | 0.1459 | 0.0006024 | 0.9825 | 0.2703 | 1.56 | 2195 |
| KMeans | pca | original | train | {"k": 2, "covariance": "NA"} | 2 | 0 | 0.1459 | 0.0006024 | 0.9825 | 0.2497 | 1.678 | 1947 |
| KMeans | pca | pca | test | {"k": 2, "covariance": "NA"} | 2 | 0 | 0.1459 | 0.0006024 | 0.983 | 0.268 | 1.554 | 558.3 |
| KMeans | pca | original | test | {"k": 2, "covariance": "NA"} | 2 | 0 | 0.1459 | 0.0006024 | 0.983 | 0.2477 | 1.673 | 493.7 |
| GMM | original | original | train | {"k": 16, "covariance": "full"} | 16 | 0 | 5.77 | 0.005555 | nan | -0.02737 | 3.337 | 344.6 |
| GMM | original | original | test | {"k": 16, "covariance": "full"} | 16 | 0 | 5.77 | 0.005555 | nan | -0.02455 | 3.774 | 87.97 |
| GMM | pca | pca | train | {"k": 15, "covariance": "full"} | 15 | 0 | 2.016 | 0.001987 | 0.3325 | 0.02143 | 2.322 | 572.1 |
| GMM | pca | original | train | {"k": 15, "covariance": "full"} | 15 | 0 | 2.016 | 0.001987 | 0.3325 | 0.01615 | 2.518 | 488.4 |
| GMM | pca | pca | test | {"k": 15, "covariance": "full"} | 15 | 0 | 2.016 | 0.001987 | 0.32 | 0.02 | 2.306 | 145.5 |
| GMM | pca | original | test | {"k": 15, "covariance": "full"} | 15 | 0 | 2.016 | 0.001987 | 0.32 | 0.01584 | 2.504 | 123.8 |

## 6. Estabilidad

Cuatro semillas y cuatro submuestras del 80 % de entrenamiento. Cada ejecución asigna el mismo conjunto de prueba y se calcula ARI entre pares. El preprocesamiento permanece fijo: esta es estabilidad condicional al escalado/PCA, no incertidumbre de todo el pipeline.

| model | space | kind | mean | min | max |
|---|---|---|---|---|---|
| GMM | original | seed | 0.6324 | 0.5292 | 0.7149 |
| GMM | original | subsample | 0.4996 | 0.4046 | 0.584 |
| GMM | pca | seed | 0.7066 | 0.5612 | 0.9644 |
| GMM | pca | subsample | 0.5263 | 0.4691 | 0.591 |
| KMeans | original | seed | 1 | 1 | 1 |
| KMeans | original | subsample | 0.9947 | 0.9915 | 0.9979 |
| KMeans | pca | seed | 0.9979 | 0.9957 | 1 |
| KMeans | pca | subsample | 0.994 | 0.9893 | 0.9957 |

## 7. Interpretación de perfiles y aplicación al catálogo

### KMeans/original

![Proyección PC1/PC2: KMeans/original](figures/07_mapa_KMeans_original.png)

| grupo | accion | tempo_BPM | duracion_min |
|---|---|---|---|
| 0 | organizar referencias de mayor intensidad | 125 | 3.58 |
| 1 | seleccionar referencias acústicas de menor intensidad | 108.9 | 3.35 |

Estas acciones organizan la exploración del catálogo; su utilidad perceptiva requiere escucha. No se infieren audiencia ni éxito comercial.

![Perfiles](figures/05_perfiles_KMeans_original.png)

| cluster | danceability | energy | loudness | speechiness | acousticness | instrumentalness | liveness | valence | tempo | duration_ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.61 | 0.763 | -6.134 | 0.0547 | 0.0784 | 1.8e-05 | 0.141 | 0.533 | 125 | 2.148e+05 |
| 1 | 0.471 | 0.303 | -12.94 | 0.0393 | 0.817 | 0.00504 | 0.117 | 0.262 | 108.9 | 2.013e+05 |

Popularidad histórica por perfil: análisis secundario, sin intervenir en el ajuste.

| split | cluster | n | median | mean | q25 | q75 | fraction_ge_70 |
|---|---|---|---|---|---|---|---|
| test | 0 | 1498 | 35 | 34.12 | 21 | 49 | 0.03872 |
| test | 1 | 502 | 28 | 29.9 | 13 | 47 | 0.01195 |
| train | 0 | 5967 | 34 | 33.76 | 20 | 48 | 0.03704 |
| train | 1 | 2033 | 29 | 30.41 | 17 | 46 | 0.01623 |

Grupo 0: **energía alta, perfil mixto**; mediana tempo 125.0 BPM y duración 3.58 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 1: **energía baja, perfil acústico**; mediana tempo 108.9 BPM y duración 3.35 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

### KMeans/pca

![Proyección PC1/PC2: KMeans/pca](figures/07_mapa_KMeans_pca.png)

| grupo | accion | tempo_BPM | duracion_min |
|---|---|---|---|
| 0 | organizar referencias de mayor intensidad | 125 | 3.58 |
| 1 | seleccionar referencias acústicas de menor intensidad | 108.4 | 3.34 |

Estas acciones organizan la exploración del catálogo; su utilidad perceptiva requiere escucha. No se infieren audiencia ni éxito comercial.

![Perfiles](figures/05_perfiles_KMeans_pca.png)

| cluster | danceability | energy | loudness | speechiness | acousticness | instrumentalness | liveness | valence | tempo | duration_ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.61 | 0.762 | -6.142 | 0.0546 | 0.0793 | 1.795e-05 | 0.141 | 0.5325 | 125 | 2.149e+05 |
| 1 | 0.468 | 0.299 | -13.02 | 0.0393 | 0.8185 | 0.00516 | 0.117 | 0.261 | 108.4 | 2.004e+05 |

Popularidad histórica por perfil: análisis secundario, sin intervenir en el ajuste.

| split | cluster | n | median | mean | q25 | q75 | fraction_ge_70 |
|---|---|---|---|---|---|---|---|
| test | 0 | 1504 | 35 | 34.12 | 21 | 49 | 0.03856 |
| test | 1 | 496 | 28 | 29.86 | 13 | 47 | 0.0121 |
| train | 0 | 5990 | 34 | 33.79 | 20 | 48 | 0.03706 |
| train | 1 | 2010 | 29 | 30.3 | 17 | 46 | 0.01592 |

Grupo 0: **energía alta, perfil mixto**; mediana tempo 125.0 BPM y duración 3.58 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 1: **energía baja, perfil acústico**; mediana tempo 108.4 BPM y duración 3.34 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

### GMM/original

![Proyección PC1/PC2: GMM/original](figures/07_mapa_GMM_original.png)

| grupo | accion | tempo_BPM | duracion_min |
|---|---|---|---|
| 0 | organizar referencias de mayor intensidad | 122 | 3.45 |
| 1 | explorar un perfil intermedio y contrastarlo mediante escucha | 118 | 3.51 |
| 2 | explorar referencias instrumentales | 125 | 5.63 |
| 3 | explorar referencias instrumentales | 130 | 4.25 |
| 4 | organizar referencias de mayor intensidad | 108.4 | 3.44 |
| 5 | explorar referencias instrumentales | 119.7 | 3.34 |
| 6 | explorar un perfil intermedio y contrastarlo mediante escucha | 120 | 3.72 |
| 7 | organizar referencias de mayor intensidad | 127.3 | 3.44 |
| 8 | explorar un perfil intermedio y contrastarlo mediante escucha | 116.3 | 3.68 |
| 9 | seleccionar referencias acústicas de menor intensidad | 113 | 3.86 |
| 10 | explorar un perfil intermedio y contrastarlo mediante escucha | 122.6 | 3.38 |
| 11 | explorar un perfil intermedio y contrastarlo mediante escucha | 112.9 | 3.09 |
| 12 | organizar referencias de mayor intensidad | 131 | 3.55 |
| 13 | seleccionar referencias acústicas de menor intensidad | 106.7 | 3.27 |
| 14 | organizar referencias de mayor intensidad | 128 | 4.38 |
| 15 | organizar referencias de mayor intensidad | 128 | 3.34 |

Estas acciones organizan la exploración del catálogo; su utilidad perceptiva requiere escucha. No se infieren audiencia ni éxito comercial.

![Perfiles](figures/05_perfiles_GMM_original.png)

| cluster | danceability | energy | loudness | speechiness | acousticness | instrumentalness | liveness | valence | tempo | duration_ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.65 | 0.728 | -5.726 | 0.0444 | 0.0896 | 1.29e-06 | 0.101 | 0.5375 | 122 | 2.068e+05 |
| 1 | 0.4685 | 0.532 | -12.07 | 0.07185 | 0.4115 | 0.498 | 0.355 | 0.248 | 118 | 2.107e+05 |
| 2 | 0.738 | 0.7675 | -8.527 | 0.0489 | 0.004905 | 0.8265 | 0.0922 | 0.3785 | 125 | 3.376e+05 |
| 3 | 0.4555 | 0.9255 | -5.821 | 0.0691 | 0.0003325 | 0.667 | 0.2115 | 0.2555 | 130 | 2.553e+05 |
| 4 | 0.5955 | 0.7175 | -7.078 | 0.355 | 0.439 | 0 | 0.4755 | 0.603 | 108.4 | 2.066e+05 |
| 5 | 0.589 | 0.521 | -10.28 | 0.04665 | 0.434 | 0.579 | 0.145 | 0.3995 | 119.7 | 2.002e+05 |
| 6 | 0.596 | 0.5115 | -8.913 | 0.0367 | 0.4445 | 0.03155 | 0.105 | 0.468 | 120 | 2.235e+05 |
| 7 | 0.487 | 0.94 | -4.766 | 0.115 | 0.00095 | 0.0334 | 0.154 | 0.334 | 127.3 | 2.062e+05 |
| 8 | 0.5395 | 0.639 | -8.179 | 0.06355 | 0.534 | 0 | 0.5235 | 0.559 | 116.3 | 2.209e+05 |
| 9 | 0.519 | 0.384 | -9.39 | 0.03155 | 0.654 | 2.99e-06 | 0.107 | 0.301 | 113 | 2.313e+05 |
| 10 | 0.6 | 0.572 | -7.574 | 0.0389 | 0.501 | 0 | 0.192 | 0.651 | 122.6 | 2.03e+05 |
| 11 | 0.722 | 0.643 | -6.861 | 0.21 | 0.238 | 0 | 0.112 | 0.574 | 112.9 | 1.852e+05 |
| 12 | 0.492 | 0.92 | -4.448 | 0.0579 | 0.00118 | 2.22e-05 | 0.154 | 0.489 | 131 | 2.132e+05 |
| 13 | 0.3925 | 0.155 | -18.98 | 0.0413 | 0.937 | 0.906 | 0.108 | 0.136 | 106.7 | 1.961e+05 |
| 14 | 0.5965 | 0.7815 | -7.156 | 0.0466 | 0.0192 | 0.007305 | 0.185 | 0.589 | 128 | 2.626e+05 |
| 15 | 0.603 | 0.843 | -4.793 | 0.091 | 0.0313 | 0 | 0.299 | 0.556 | 128 | 2.005e+05 |

Popularidad histórica por perfil: análisis secundario, sin intervenir en el ajuste.

| split | cluster | n | median | mean | q25 | q75 | fraction_ge_70 |
|---|---|---|---|---|---|---|---|
| test | 0 | 215 | 41 | 36.7 | 19 | 56 | 0.07907 |
| test | 1 | 68 | 25.5 | 26.71 | 13 | 37.25 | 0 |
| test | 2 | 83 | 22 | 26.39 | 9 | 45.5 | 0.01205 |
| test | 3 | 120 | 23 | 27.27 | 16.75 | 38.25 | 0.008333 |
| test | 4 | 75 | 29 | 33.49 | 21 | 48 | 0.02667 |
| test | 5 | 163 | 27 | 29.48 | 14.5 | 44 | 0.0184 |
| test | 6 | 75 | 36 | 36.37 | 22.5 | 51.5 | 0.02667 |
| test | 7 | 48 | 21.5 | 25.06 | 13.5 | 34 | 0.04167 |
| test | 8 | 126 | 37 | 33.62 | 22 | 45 | 0.01587 |
| test | 9 | 162 | 38 | 33.65 | 19 | 50 | 0.01852 |
| test | 10 | 305 | 37 | 35.73 | 23 | 49 | 0.03607 |
| test | 11 | 146 | 41 | 37.55 | 24.5 | 50 | 0.04795 |
| test | 12 | 129 | 32 | 35.6 | 23 | 53 | 0.0155 |
| test | 13 | 101 | 36 | 30.94 | 12 | 49 | 0 |
| test | 14 | 44 | 31.5 | 31.91 | 17.75 | 46.75 | 0.04545 |
| test | 15 | 140 | 32 | 32.29 | 20.75 | 47 | 0.06429 |
| train | 0 | 824 | 39 | 36.02 | 19 | 55 | 0.06189 |
| train | 1 | 302 | 26.5 | 27.23 | 15 | 40 | 0.003311 |
| train | 2 | 290 | 18 | 24.1 | 8 | 40 | 0.006897 |
| train | 3 | 490 | 22 | 26.63 | 16 | 36 | 0.008163 |
| train | 4 | 280 | 28 | 31.6 | 22 | 43 | 0.007143 |
| train | 5 | 676 | 27 | 30.26 | 17 | 45 | 0.01775 |
| train | 6 | 276 | 39 | 37.01 | 21 | 54 | 0.04348 |
| train | 7 | 197 | 26 | 31.91 | 17 | 49 | 0.02538 |
| train | 8 | 494 | 38 | 34.77 | 23 | 45 | 0.01012 |
| train | 9 | 704 | 38 | 35.07 | 22 | 51 | 0.03551 |
| train | 10 | 1186 | 35 | 33.34 | 21 | 47 | 0.03288 |
| train | 11 | 647 | 38 | 35.96 | 21 | 51 | 0.05719 |
| train | 12 | 519 | 32 | 35.09 | 22 | 52 | 0.04624 |
| train | 13 | 396 | 28 | 30.76 | 18 | 47.25 | 0.005051 |
| train | 14 | 192 | 29.5 | 31.65 | 20 | 44.25 | 0.02604 |
| train | 15 | 527 | 35 | 34.95 | 22 | 51 | 0.05313 |

Grupo 0: **energía alta, perfil mixto**; mediana tempo 122.0 BPM y duración 3.45 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 1: **energía intermedia, perfil mixto**; mediana tempo 118.0 BPM y duración 3.51 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 2: **energía alta, perfil instrumental**; mediana tempo 125.0 BPM y duración 5.63 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 3: **energía alta, perfil instrumental**; mediana tempo 130.0 BPM y duración 4.25 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 4: **energía alta, perfil mixto**; mediana tempo 108.4 BPM y duración 3.44 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 5: **energía intermedia, perfil instrumental**; mediana tempo 119.7 BPM y duración 3.34 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 6: **energía intermedia, perfil mixto**; mediana tempo 120.0 BPM y duración 3.72 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 7: **energía alta, perfil mixto**; mediana tempo 127.3 BPM y duración 3.44 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 8: **energía intermedia, perfil mixto**; mediana tempo 116.3 BPM y duración 3.68 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 9: **energía intermedia, perfil acústico**; mediana tempo 113.0 BPM y duración 3.86 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 10: **energía intermedia, perfil mixto**; mediana tempo 122.6 BPM y duración 3.38 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 11: **energía intermedia, perfil mixto**; mediana tempo 112.9 BPM y duración 3.09 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 12: **energía alta, perfil mixto**; mediana tempo 131.0 BPM y duración 3.55 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 13: **energía baja, perfil acústico**; mediana tempo 106.7 BPM y duración 3.27 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 14: **energía alta, perfil mixto**; mediana tempo 128.0 BPM y duración 4.38 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 15: **energía alta, perfil mixto**; mediana tempo 128.0 BPM y duración 3.34 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

### GMM/pca

![Proyección PC1/PC2: GMM/pca](figures/07_mapa_GMM_pca.png)

| grupo | accion | tempo_BPM | duracion_min |
|---|---|---|---|
| 0 | organizar referencias de mayor intensidad | 106 | 3.42 |
| 1 | organizar referencias de mayor intensidad | 132.1 | 3.44 |
| 2 | explorar referencias instrumentales | 130.4 | 4.12 |
| 3 | explorar un perfil intermedio y contrastarlo mediante escucha | 129.1 | 3.67 |
| 4 | organizar referencias de mayor intensidad | 136.1 | 3.49 |
| 5 | explorar un perfil intermedio y contrastarlo mediante escucha | 120.1 | 3.07 |
| 6 | organizar referencias de mayor intensidad | 126 | 4.54 |
| 7 | seleccionar referencias acústicas de menor intensidad | 109.9 | 3.16 |
| 8 | seleccionar referencias acústicas de menor intensidad | 88.5 | 3.24 |
| 9 | explorar referencias instrumentales | 118 | 4.24 |
| 10 | explorar un perfil intermedio y contrastarlo mediante escucha | 123 | 3.47 |
| 11 | organizar referencias de mayor intensidad | 102.8 | 3.44 |
| 12 | explorar referencias instrumentales | 125 | 5.82 |
| 13 | seleccionar referencias acústicas de menor intensidad | 110.6 | 3.06 |
| 14 | organizar referencias de mayor intensidad | 122.2 | 3.52 |

Estas acciones organizan la exploración del catálogo; su utilidad perceptiva requiere escucha. No se infieren audiencia ni éxito comercial.

![Perfiles](figures/05_perfiles_GMM_pca.png)

| cluster | danceability | energy | loudness | speechiness | acousticness | instrumentalness | liveness | valence | tempo | duration_ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.694 | 0.761 | -5.498 | 0.0512 | 0.0636 | 5.32e-06 | 0.0989 | 0.564 | 106 | 2.05e+05 |
| 1 | 0.529 | 0.933 | -4.249 | 0.145 | 0.0151 | 7.44e-06 | 0.276 | 0.473 | 132.1 | 2.062e+05 |
| 2 | 0.4805 | 0.9195 | -5.981 | 0.06305 | 0.001115 | 0.757 | 0.214 | 0.269 | 130.4 | 2.471e+05 |
| 3 | 0.5575 | 0.483 | -8.142 | 0.0358 | 0.5025 | 2.135e-06 | 0.103 | 0.4145 | 129.1 | 2.203e+05 |
| 4 | 0.527 | 0.881 | -4.69 | 0.05 | 0.011 | 7.03e-06 | 0.212 | 0.551 | 136.1 | 2.096e+05 |
| 5 | 0.722 | 0.6305 | -7 | 0.2205 | 0.2345 | 0 | 0.119 | 0.5645 | 120.1 | 1.841e+05 |
| 6 | 0.526 | 0.6745 | -7.323 | 0.0418 | 0.15 | 9.465e-05 | 0.252 | 0.412 | 126 | 2.724e+05 |
| 7 | 0.403 | 0.1625 | -18.35 | 0.043 | 0.9145 | 0.901 | 0.108 | 0.1385 | 109.9 | 1.895e+05 |
| 8 | 0.4645 | 0.297 | -11.35 | 0.036 | 0.8385 | 6.65e-06 | 0.136 | 0.339 | 88.54 | 1.944e+05 |
| 9 | 0.4045 | 0.5155 | -13.14 | 0.09655 | 0.409 | 0.6935 | 0.3655 | 0.177 | 118 | 2.541e+05 |
| 10 | 0.656 | 0.649 | -7.571 | 0.0362 | 0.366 | 4.21e-06 | 0.192 | 0.846 | 123 | 2.08e+05 |
| 11 | 0.6205 | 0.6845 | -8.494 | 0.475 | 0.6725 | 0 | 0.607 | 0.5935 | 102.8 | 2.066e+05 |
| 12 | 0.74 | 0.757 | -8.856 | 0.0486 | 0.00726 | 0.829 | 0.0938 | 0.376 | 125 | 3.49e+05 |
| 13 | 0.563 | 0.406 | -12.75 | 0.042 | 0.672 | 0.513 | 0.137 | 0.393 | 110.6 | 1.834e+05 |
| 14 | 0.5295 | 0.689 | -7.377 | 0.0547 | 0.441 | 1.75e-06 | 0.683 | 0.519 | 122.2 | 2.11e+05 |

Popularidad histórica por perfil: análisis secundario, sin intervenir en el ajuste.

| split | cluster | n | median | mean | q25 | q75 | fraction_ge_70 |
|---|---|---|---|---|---|---|---|
| test | 0 | 183 | 42 | 38.03 | 19.5 | 56 | 0.09836 |
| test | 1 | 121 | 28 | 32.66 | 21 | 50 | 0.04132 |
| test | 2 | 125 | 22 | 26.14 | 14 | 38 | 0.016 |
| test | 3 | 314 | 39 | 36.43 | 23 | 51 | 0.03822 |
| test | 4 | 210 | 34.5 | 35.8 | 23 | 52 | 0.0381 |
| test | 5 | 162 | 40 | 35.05 | 21 | 50 | 0.03086 |
| test | 6 | 134 | 39 | 35.87 | 22 | 50 | 0.02985 |
| test | 7 | 111 | 35 | 31.34 | 15.5 | 49 | 0 |
| test | 8 | 95 | 22 | 23.64 | 0 | 39.5 | 0.02105 |
| test | 9 | 56 | 28 | 28.77 | 16.75 | 37 | 0 |
| test | 10 | 119 | 32 | 34.13 | 24 | 46 | 0.03361 |
| test | 11 | 51 | 24 | 33 | 21 | 48 | 0.03922 |
| test | 12 | 86 | 22.5 | 25.36 | 9 | 44 | 0 |
| test | 13 | 101 | 25 | 28.26 | 11 | 44 | 0.009901 |
| test | 14 | 132 | 36.5 | 33.27 | 23 | 44 | 0.007576 |
| train | 0 | 801 | 38 | 36.1 | 16 | 56 | 0.08365 |
| train | 1 | 459 | 30 | 33.1 | 20 | 48.5 | 0.03268 |
| train | 2 | 478 | 22 | 28.23 | 16 | 42 | 0.008368 |
| train | 3 | 1212 | 39 | 36.78 | 22 | 53 | 0.04043 |
| train | 4 | 861 | 34 | 34.16 | 21 | 50 | 0.03368 |
| train | 5 | 684 | 36 | 34.73 | 20 | 49 | 0.04825 |
| train | 6 | 484 | 38 | 36.91 | 24 | 52 | 0.02479 |
| train | 7 | 452 | 29 | 31.21 | 18 | 47 | 0.01106 |
| train | 8 | 386 | 25 | 27.15 | 12 | 43 | 0.005181 |
| train | 9 | 258 | 25 | 26.47 | 12 | 39 | 0.003876 |
| train | 10 | 503 | 33 | 31.68 | 19 | 44.5 | 0.03579 |
| train | 11 | 196 | 25.5 | 29.68 | 21.75 | 39 | 0 |
| train | 12 | 329 | 18 | 24.49 | 8 | 41 | 0.009119 |
| train | 13 | 423 | 24 | 27.78 | 15 | 42.5 | 0.01655 |
| train | 14 | 474 | 39 | 36.12 | 24 | 45 | 0.01899 |

Grupo 0: **energía alta, perfil mixto**; mediana tempo 106.0 BPM y duración 3.42 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 1: **energía alta, perfil mixto**; mediana tempo 132.1 BPM y duración 3.44 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 2: **energía alta, perfil instrumental**; mediana tempo 130.4 BPM y duración 4.12 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 3: **energía intermedia, perfil mixto**; mediana tempo 129.1 BPM y duración 3.67 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 4: **energía alta, perfil mixto**; mediana tempo 136.1 BPM y duración 3.49 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 5: **energía intermedia, perfil mixto**; mediana tempo 120.1 BPM y duración 3.07 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 6: **energía alta, perfil mixto**; mediana tempo 126.0 BPM y duración 4.54 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 7: **energía baja, perfil acústico**; mediana tempo 109.9 BPM y duración 3.16 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 8: **energía baja, perfil acústico**; mediana tempo 88.5 BPM y duración 3.24 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 9: **energía intermedia, perfil instrumental**; mediana tempo 118.0 BPM y duración 4.24 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 10: **energía intermedia, perfil mixto**; mediana tempo 123.0 BPM y duración 3.47 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 11: **energía alta, perfil acústico**; mediana tempo 102.8 BPM y duración 3.44 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 12: **energía alta, perfil instrumental**; mediana tempo 125.0 BPM y duración 5.82 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 13: **energía intermedia, perfil acústico**; mediana tempo 110.6 BPM y duración 3.06 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

Grupo 14: **energía alta, perfil mixto**; mediana tempo 122.2 BPM y duración 3.52 minutos. Puede utilizarse como filtro exploratorio de catálogo; no implica una recomendación personalizada validada.

## 8. Respuestas a las 12 preguntas de análisis

### 1. Escalado

| model | converged | ari_scaled_unscaled | silhouette_own_unscaled | silhouette_labels_unscaled_on_scaled | silhouette_scaled | fit_seconds |
|---|---|---|---|---|---|---|
| KMeans | True | 0.002381 | 0.6215 | 0.1319 | 0.2493 | 0.2652 |
| GMM | True | 0.3474 | -0.2549 | 0.01582 | -0.02737 | 16.21 |

Duración en milisegundos tiene escala muy superior a variables entre 0 y 1. El control mantiene hiperparámetros y compara etiquetas en el espacio escalado para no confundir geometrías.

### 2. Hiperparámetros

GMM/original selecciona K=16, límite superior de la búsqueda. Es el mejor BIC dentro del presupuesto declarado, no un óptimo global demostrado; no se afirma que existan exactamente esos géneros o categorías.

| model | space | k | covariance |
|---|---|---|---|
| KMeans | original | 2 | NA |
| KMeans | pca | 2 | NA |
| GMM | original | 16 | full |
| GMM | pca | 15 | full |

Se priorizó Silhouette para K-Means y BIC para GMM. Ver curvas y búsquedas completas; la elección en un extremo del rango exige ampliar el rango en trabajo futuro.

### 3. Sesgo de las métricas

La tabla común recomienda KMeans/pca por Silhouette=0.2497. Las distancias euclidianas favorecen grupos compactos, lo que puede beneficiar a K-Means frente a gaussianas alargadas de GMM. Las gráficas 2D se contrastan con las métricas, pero no validan separación en todas las dimensiones.

### 4. Ruido y atípicos

No se utilizó DBSCAN y el ruido es 0 % en todas las filas por asignación completa. Las fracciones de atípicos por variable están en atipicos_train.csv. No se confunde pertenencia incierta de GMM con ruido. Se conservan atípicos plausibles y se reconoce sensibilidad del escalador, centroides y covarianzas.

### 5. Componentes principales

PC1: loudness +0.512, energy +0.498 y acousticness -0.428: intensidad frente a carácter acústico.

PC2: valence +0.462, danceability +0.435 y duration_ms -0.422: positividad/bailabilidad frente a duración.

Se conservaron 7 componentes, varianza 90.81%.

PC1: mayores cargas absolutas: loudness (+0.512), energy (+0.498), acousticness (-0.428). El componente representa el contraste acústico indicado por esas variables y sus signos.

PC2: mayores cargas absolutas: valence (+0.462), danceability (+0.435), duration_ms (-0.422). El componente representa el contraste acústico indicado por esas variables y sus signos.

KMeans: Silhouette original 0.2493, etiquetas PCA evaluadas en original 0.2497; diferencia +0.0003, ARI 0.9825.

GMM: Silhouette original -0.0274, etiquetas PCA evaluadas en original 0.0162; diferencia +0.0435, ARI 0.3325.

### 6. Efecto de la reducción

Las diferencias numéricas anteriores y la tabla distinguen cambio de asignaciones de cambio de geometría. PCA elimina direcciones de baja varianza; pueden ser redundancia o información útil. Una mejora no demuestra eliminación de ruido y un empeoramiento puede indicar pérdida de estructura. Una diferencia muy pequeña de Silhouette puede carecer de relevancia práctica; la selección por máximo numérico no demuestra superioridad estadística. Con diez variables no debe atribuirse automáticamente el resultado a la maldición de dimensionalidad.

### 7. Comparación justa

| model | space | evaluation_space | silhouette | davies_bouldin | calinski_harabasz |
|---|---|---|---|---|---|
| KMeans | original | original | 0.2493 | 1.683 | 1948 |
| KMeans | pca | pca | 0.2703 | 1.56 | 2195 |
| KMeans | pca | original | 0.2497 | 1.678 | 1947 |
| GMM | original | original | -0.02737 | 3.337 | 344.6 |
| GMM | pca | pca | 0.02143 | 2.322 | 572.1 |
| GMM | pca | original | 0.01615 | 2.518 | 488.4 |

Comparar directamente métricas de geometrías diferentes no permite concluir una mejora de agrupación. Se utilizan las filas evaluation_space=original para esa conclusión.

### 8. Cambio en asignaciones

| model | split | ari_vs_original |
|---|---|---|
| KMeans | train | 0.9825 |
| KMeans | test | 0.983 |
| GMM | train | 0.3325 |
| GMM | test | 0.32 |

ARI=1 indica mismas particiones aunque cambien sus números; cercano a 0 indica acuerdo compatible con azar y puede ser negativo. No mide relación con popularidad.

### 9. Estabilidad

GMM/original: ARI entre semillas 0.6324; entre submuestras 0.4996; GMM/pca: ARI entre semillas 0.7066; entre submuestras 0.5263; KMeans/original: ARI entre semillas 1.0000; entre submuestras 0.9947; KMeans/pca: ARI entre semillas 0.9979; entre submuestras 0.9940.

K-Means presenta mayor estabilidad en estos resultados. GMM ajusta más grupos y covarianzas, y puede converger a soluciones locales distintas; estabilidad baja obliga a tratar sus perfiles con cautela.

| model | space | kind | ari |
|---|---|---|---|
| GMM | original | seed | 0.6324 |
| GMM | original | subsample | 0.4996 |
| GMM | pca | seed | 0.7066 |
| GMM | pca | subsample | 0.5263 |
| KMeans | original | seed | 1 |
| KMeans | original | subsample | 0.9947 |
| KMeans | pca | seed | 0.9979 |
| KMeans | pca | subsample | 0.994 |

Mayor ARI medio indica mayor estabilidad en este diseño. Ver mínimos para detectar ejecuciones sensibles. La prueba común no ajusta hiperparámetros.

### 10. Costo computacional

| model | space | fit_seconds | predict_test_seconds |
|---|---|---|---|
| KMeans | original | 0.1542 | 0.0005511 |
| KMeans | pca | 0.1459 | 0.0006024 |
| GMM | original | 5.77 | 0.005555 |
| GMM | pca | 2.016 | 0.001987 |

Los tiempos corresponden a un ajuste final, sin búsqueda ni preprocesamiento y con un hilo numérico; no son benchmarks repetidos. Debe incluirse el costo de ajustar/transformar PCA antes de afirmar un ahorro total del pipeline. Con 100 veces más datos crecen el ajuste, la memoria y especialmente Silhouette, cuyo cálculo completo requiere distancias cuadráticas. No se extrapolan segundos linealmente; se mantendría muestreo de evaluación.

### 11. Visualización no lineal

La representación usada conserva 90.81% en 7 componentes; el mapa solo muestra PC1/PC2. No se ejecutó UMAP ni t-SNE: son opcionales. Si una visualización no lineal mostrara islas, no probaría grupos verdaderos. t-SNE distorsiona distancias globales y densidades, depende de parámetros y no se recomienda como entrada para este clustering comparativo.

### 12. Recomendación y limitaciones

Se recomienda provisionalmente **KMeans/pca** por el criterio predefinido de Silhouette en entrenamiento común (0.2497); revisar además estabilidad y perfiles. No se seleccionó por conseguir diferencias de popularidad. Limitaciones: muestra de conveniencia, popularidad histórica con fecha no documentada, duplicados semánticos entre versiones, 671 cadenas de artista compartidas entre train y test (conteo de cadenas exactas, no de personas únicas), ausencia de publicidad/exposición en playlists y posible estructura continua sin clusters naturales. Con más tiempo se separaría por artista, se repetirían muestras y tiempos, y se añadirían popularidades medidas longitudinalmente.

## 9. Conclusiones

La decisión práctica es segmentar el catálogo en perfiles descriptivos para filtrar y comparar referencias, manteniendo visibles el solapamiento y la incertidumbre. Las acciones se derivan de sus medianas originales, no de nombres de artistas ni de popularidad. Una interfaz adicional no es necesaria para demostrar el experimento.

No se garantiza una calificación: los resultados no prueban que la configuración numéricamente ganadora sea superior en percepción musical. La defensa debe explicar esa diferencia.

Los resultados de los cuatro ajustes, sus perfiles y las distribuciones de popularidad están documentados arriba. La mejor Silhouette común corresponde a KMeans/pca. En prueba, las medianas de popularidad de la configuración recomendada van de 28.0 (grupo 1) a 35.0 (grupo 0), con epsilon cuadrado 0.0071. Los intervalos intercuartílicos de esos grupos son [13.0, 47.0] y [21.0, 49.0]. Las medianas diferentes no permiten identificar individualmente una canción popular; debe considerarse el solapamiento de distribuciones. La asociación no implica causalidad. No se garantiza predecir éxitos futuros.

## 10. Reproducibilidad y uso de IA

Semilla 42; CSV de entrada verificado por SHA-256 en manifest.json y configuracion.json. Versiones efectivas en versiones.json. Ejecutar el cuaderno de principio a fin o python proyecto_musica.py. Se utilizó ChatGPT/Codex para estructurar el proyecto, escribir código y generar explicaciones. Las tablas del informe se calculan con datos reales; el estudiante debe revisar e interpretar los resultados y declarar esta asistencia.

## Referencias

Pandya, M. (s. f.). *Spotify Tracks Dataset* [Conjunto de datos]. Hugging Face. https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset

Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825–2830. https://jmlr.org/papers/v12/pedregosa11a.html

Documentación oficial de scikit-learn: https://scikit-learn.org/stable/modules/clustering.html y https://scikit-learn.org/stable/modules/decomposition.html#pca