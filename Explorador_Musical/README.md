# SONORA — Explorador musical

Versión independiente del proyecto de Bloque 3. El experimento de popularidad
se conserva como análisis secundario. La nueva pregunta es cómo cambian perfiles
y sugerencias entre K-Means/GMM y representaciones original/PCA.

## Abrir la demostración

Haz doble clic en **Explorador_Musical.html**. El archivo contiene el catálogo,
los modelos ya aplicados y las coordenadas: funciona sin servidor y sin internet.
Los enlaces para escuchar en Spotify sí requieren conexión.

1. Busca una canción o artista entre las 10.000 canciones disponibles.
2. Selecciona un resultado o pulsa Enter para elegir la primera coincidencia.
3. Cambia modelo, espacio o filtros y compara las sugerencias.
4. Usa “Explorar desde aquí” para continuar desde otra canción.

La popularidad NO entrena ni ordena el sistema. “Menor popularidad” es un filtro
opcional aplicado después del entrenamiento. Las sugerencias no son personalizadas.
No se garantiza que una canción cercana geométricamente guste al usuario.

## Leer el informe

- `outputs/informe_explorador.html`: nueva pregunta, funcionamiento y evaluación de vecinos.
- `outputs/informe.html`: análisis completo de clustering y doce respuestas de la rúbrica;
  la popularidad se mantiene como pregunta secundaria.
- `Proyecto_Explorador_Musical.ipynb`: cuaderno con el experimento y construcción de la demo.
- `outputs/resumen_recuperacion.csv`: comparación adicional de sugerencias.
- `outputs/integridad_explorador.json`: reproducción de los cuatro modelos y comprobaciones.

## Reproducir desde cero

Requiere Python 3.10 o superior y las dependencias indicadas:

```powershell
python -m pip install -r requirements.txt
python descargar_dataset.py
python proyecto_musica.py
python construir_explorador.py
```

También puedes ejecutar todas las celdas del cuaderno desde esta carpeta.
Para regenerarlo: `python preparar_cuaderno.py`.
Para verificar sus celdas sin servidor Jupyter: `python verificar_cuaderno.py`.
Las versiones exactas de la ejecución se registran en `requirements-lock.txt`.

## Qué se evalúa

Datos originales: 114.000 registros, 89.741 IDs únicos. Muestra reproducible de
10.000 canciones: 8.000 entrenamiento, 2.000 prueba. Diez variables numéricas.
Escalador, imputador y PCA se ajustan solo con entrenamiento. Se comparan los
dos algoritmos antes y después de PCA, métricas internas, ARI, tiempos y estabilidad.

Adicionalmente se evalúan 200 consultas de prueba con candidatos de entrenamiento.
Recall@10 compara con vecinos originales sin restricción de grupo y Jaccard
mide coincidencia de sugerencias original/PCA. Son métricas geométricas,
no validación de satisfacción de oyentes. El valor de popularidad es histórico.

Se aplica exclusión de artistas compartidos en la búsqueda, no en la división
train/test. Se reconocen artistas compartidos entre conjuntos y versiones de
una canción con identificadores diferentes como limitaciones.

## Fuente y autoría

Pandya, M. (s. f.). *Spotify Tracks Dataset*. Hugging Face.
https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset

La ficha declara BSD; revisar términos originales antes de redistribuir. No se
incluye audio ni se necesita una API de Spotify. Se utilizó ChatGPT/Codex para
implementación y documentación; declarar la asistencia al entregar el trabajo.
Completar los datos de autores y revisar personalmente la interpretación.


## Ampliación: laboratorio profesional
La demo incluye comparación de referencias, ficha de posicionamiento sonoro
exportable a JSON y simulación de diez características. Selecciona una canción
arriba y baja a Laboratorio profesional.

El simulador utiliza los centros K-Means y densidades GMM entrenados y el mismo
escalador/PCA ajustados solo con train. No modifica audio ni predice éxito.
Los contextos de marketing son hipótesis editoriales manuales, con umbrales
visibles; no se infieren audiencia, presupuesto o retorno de inversión.
Cambiar canción, modelo o espacio restablece la simulación.

Código: profesional.js, integrado por construir_explorador.py.
Validación: node verificar_interfaz.cjs. Guía: GUIA_LABORATORIO.md.
