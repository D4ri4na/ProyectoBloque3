# Perfiles sonoros y popularidad musical

Proyecto Bloque 3: dos algoritmos de clustering antes y después de PCA.

**Pregunta:** ¿los grupos formados únicamente con características sonoras
presentan diferencias de popularidad?

## Ejecución

Desde esta carpeta, con Python 3.10 o superior:

```powershell
python -m pip install -r requirements.txt
python descargar_dataset.py
python proyecto_musica.py
```

También puedes abrir `Proyecto_Musica.ipynb` en Jupyter o VS Code y ejecutar
todas las celdas con el directorio de trabajo en esta carpeta. El notebook
contiene el código completo y produce los mismos resultados que el script.
No hace falta descargar audio ni disponer de una cuenta de Spotify.

La entrega incluye las salidas reales del cuaderno. Se verificaron sus celdas
Python secuencialmente en un mismo espacio de nombres, sin depender de un
servidor Jupyter. Para repetir esa verificación: `python ejecutar_cuaderno.py`.
Las versiones exactas utilizadas están en `requirements-lock.txt`; para
reproducirlas puedes instalar ese archivo en lugar de `requirements.txt`.

Si falla la conexión, descarga `dataset.csv` desde
https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset/tree/main
y ejecuta:

```powershell
python descargar_dataset.py --archivo "C:\ruta\dataset.csv"
python proyecto_musica.py
```

Configuración predeterminada: 10.000 canciones únicas, semilla 42, 80/20,
K=2…12, PCA con 90 % de varianza. Para otra muestra:

```powershell
python proyecto_musica.py --muestra 10000 --kmax 12
```

## Archivos

- `Proyecto_Musica.ipynb`: cuaderno ejecutable con código visible y resultados.
- `proyecto_musica.py`: implementación completa.
- `descargar_dataset.py`: descarga, validación de columnas y SHA-256.
- `data/raw/spotify_tracks.csv`: datos fuente, sin modificar.
- `data/raw/manifest.json`: procedencia y huella de los datos.
- `outputs/informe.html`: informe para lectura en navegador o impresión.
- `outputs/informe.md`: informe editable con las 12 preguntas de análisis.
- `outputs/comparativa.csv`: métricas train/test y comparación en espacio común.
- `outputs/busqueda_*.csv`: hiperparámetros, métricas, BIC/AIC y convergencia.
- `outputs/estabilidad.csv`: ARI por pares, semillas y submuestras.
- `outputs/perfiles_*.csv`: medianas en unidades originales.
- `outputs/asignaciones_*.csv`: canciones y grupos; GMM incluye incertidumbre.
- `outputs/popularidad_*.csv`: distribución de popularidad y prueba exploratoria.
- `outputs/ejemplos_*.csv`: representantes seleccionados sin usar popularidad.
- `outputs/figures/`: gráficos del análisis.
- `outputs/versiones.json`: versiones realmente utilizadas.
- `outputs/validacion.json`: comprobaciones al terminar una ejecución válida.

## Decisiones importantes

Se excluye popularidad, artista, género e identificadores de clustering y PCA.
Las canciones repetidas por ID se deduplican sin escoger por popularidad.
El escalador, imputador y PCA solo aprenden del entrenamiento. Se conservan
atípicos plausibles y se documentan. K-Means se selecciona por Silhouette y
GMM por BIC, nunca por diferencias de popularidad. Se reajustan ambos tras PCA.
La comparación entre espacios se realiza también con etiquetas PCA evaluadas
en el espacio original escalado. El ARI compara particiones sobre las mismas
canciones. Silhouette utiliza una muestra fija máxima de 2.000 canciones para
limitar memoria. Los otros dos índices utilizan el conjunto completo.

Los p-valores de popularidad son exploratorios: las canciones pueden compartir
artista y no son observaciones independientes. Popularidad no equivale a
ventas, rentabilidad ni calidad. El dataset es histórico y no representa todo
Spotify. Las versiones duplicadas con IDs distintos pueden permanecer. No se
promete predecir éxitos ni demostrar causas de popularidad.

## Fuente, licencia y asistencia

Pandya, M. (s. f.). *Spotify Tracks Dataset* [Conjunto de datos]. Hugging Face.
https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset

La ficha del repositorio declara BSD. Verificar el alcance de la licencia y
los términos originales antes de redistribuir el dataset. No se distribuye audio.

Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python.
*Journal of Machine Learning Research, 12*, 2825–2830.
https://jmlr.org/papers/v12/pedregosa11a.html

Se utilizó ChatGPT/Codex para escribir y revisar código, estructurar el trabajo
y generar explicaciones. Las cifras finales provienen de la ejecución real.
Antes de entregar: completar autores, docente, fecha y revisar personalmente
el significado de perfiles y conclusiones.
