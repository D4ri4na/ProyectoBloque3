# Explorador musical: canciones parecidas y descubrimiento de catálogo

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

PCA conserva **7 componentes y 90.81% de varianza**.

## Evaluación de sugerencias

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

| configuration | queries | recall_at_10 | mean_pool | mean_returned | mean_original_distance |
|---|---|---|---|---|---|
| GMM_original | 200 | 0.589 | 878.1 | 10 | 1.307 |
| GMM_pca | 200 | 0.46 | 804.8 | 10 | 1.401 |
| KMeans_original | 200 | 0.9425 | 4981 | 10 | 1.183 |
| KMeans_pca | 200 | 0.5385 | 5013 | 10 | 1.34 |

### Coincidencia antes y después de PCA

| model | mean | min | max |
|---|---|---|---|
| GMM | 0.2657 | 0 | 0.8182 |
| KMeans | 0.4042 | 0 | 1 |

Jaccard=1 significa las mismas sugerencias; 0 significa ninguna en común.

## Recomendación para la demostración

La interfaz inicia con **K-Means + PCA**, una configuración compacta y de fácil
interpretación. Recupera en promedio 53.8% de los vecinos de la
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
