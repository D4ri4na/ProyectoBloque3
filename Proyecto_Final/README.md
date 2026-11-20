# Perfiles sonoros y alta popularidad musical

## Pregunta principal
¿Existen perfiles sonoros que concentren canciones de alta popularidad y qué características los distinguen?

El proyecto busca asociaciones entre perfiles acústicos y popularidad. El clustering
es el método para responder esa pregunta, no un reemplazo del objetivo. No se
pretende demostrar causalidad ni garantizar éxito comercial.

## Qué abrir
1. `resultados/informe.html`: informe actualizado, ampliación y 12 respuestas.
2. `Proyecto_Mejorado.ipynb`: código completo y salidas reales de todas las etapas.
3. `resultados/ampliacion/resultado_contextos.json`: conclusión de la ampliación.
4. `resultados/ampliacion/concentracion.csv`: tasas, lift, cobertura e incertidumbre.
5. `resultados/ampliacion/contextos.csv`: contextos y corrección múltiple.

## Ampliación actual
La referencia de dos grupos se conserva y se compara con perfiles más detallados
(K=3,4,5,6,8,10), manteniendo K-Means/GMM antes y después de PCA. Los parámetros
se eligen por separación de validación y tamaños mínimos, nunca por popularidad.
Se reserva otra muestra uniforme de hasta 6.000 canciones, excluyendo los IDs,
nombres de artistas y vectores acústicos exactos de las 14.000 utilizadas antes.

Género se utiliza únicamente después del clustering. Se recuperan todas las
etiquetas por ID y se analizan familias editoriales fijadas antes de los cálculos.
Las familias se solapan y no son confirmaciones independientes. Los contextos
con muestra insuficiente no se convierten en conclusiones negativas.

Interpretar concentración junto con cobertura y captura: un perfil más selectivo
puede concentrar más canciones populares, pero abarcar menos de los éxitos totales.
No confundir lift con probabilidad de éxito, precisión o causalidad.

## Diseño de referencia conservado
1. K-Means y GMM, antes y después de PCA, se ajustan únicamente con diez
   características sonoras. Popularidad no elige preparación, K, covarianza o modelo.
2. Con los modelos congelados, se identifica el perfil con mayor proporción de
   canciones >=70 en entrenamiento. Esta selección posterior sí mira popularidad,
   pero solo en entrenamiento, y no cambia las asignaciones aprendidas.
3. La configuración principal es la ya elegida por Silhouette de validación.
4. Otras 2.000 canciones, sin IDs, artistas ni vectores acústicos exactos compartidos
   con los datos ya utilizados, evalúan la concentración del candidato.
5. Se reportan tasas, lift, diferencia frente al resto, intervalos bootstrap por
   componentes de artistas y sensibilidad con umbrales 60/80.
6. Se describen rasgos del candidato mediante medianas originales, sin atribuir
   efectos causales ni importancia predictiva.

Alta popularidad significa >=70 en el archivo histórico. No equivale a ingresos,
ventas o éxito universal. La evaluación adicional anterior ya observada se presenta
como retrospectiva; la nueva evaluación del objetivo no selecciona modelos.

## Reproducir
Con Python 3.12, desde esta carpeta:

```powershell
python -m pip install -r requirements.txt
python mejorar_proyecto.py
```

El script ejecuta clustering/PCA, el objetivo de referencia y la ampliación por contextos. Puede tardar varios minutos. Alternativa:
abrir `Proyecto_Mejorado.ipynb` en Jupyter y ejecutar todas las celdas en orden.
Para recalcular solo la ampliación con las etapas de referencia ya disponibles:

```powershell
python analizar_contextos.py
```

No necesita conexión si están instaladas las dependencias y se conserva el CSV.
Los enlaces a canciones requieren internet; no se incluye audio descargado.
El dataset no contiene año, idioma ni estructura temporal del audio; no se inventan.

## Organización
- `mejorar_proyecto.py`: ajuste sin popularidad, comparación de modelos y PCA.
- `analizar_popularidad.py`: contraste de popularidad de la etapa de referencia.
- `analizar_contextos.py`: ampliación, evaluación adicional y publicación final.
- `protocolo_contextos.json`: reglas de granularidad, contextos, tamaños y multiplicidad.
- `Proyecto_Mejorado.ipynb`: ambos módulos visibles y ejecutados.
- `protocolo_popularidad.json`: objetivo, umbrales y contraste principal.
- `protocolo_mejora.json`: protocolo metodológico previo del núcleo de clustering;
  se preserva para no alterar retroactivamente la selección ya congelada.
- `requirements.txt`: entorno de ejecución.
- `data/raw/`: CSV original y procedencia.
- `data/referencia_anterior/`: registros ya utilizados, necesarios para exclusiones
  y para la comparación metodológica histórica.
- `resultados/`: referencia, evidencia y un informe final en HTML y Markdown.
- `resultados/ampliacion/`: resultados y muestra reservada de la ampliación.

## Qué significan las diez variables
| Variable | Interpretación | Unidad |
| --- | --- | --- |
| danceability | Bailabilidad estimada | 0–1 |
| energy | Intensidad percibida | 0–1 |
| loudness | Nivel sonoro | dB |
| speechiness | Presencia de habla | 0–1 |
| acousticness | Carácter acústico | 0–1 |
| instrumentalness | Carácter instrumental | 0–1 |
| liveness | Indicios de interpretación en directo | 0–1 |
| valence | Positividad sonora estimada | 0–1 |
| tempo | Velocidad del pulso | BPM |
| duration_ms | Duración | Milisegundos |

## Interpretación y límites
No basta con que un perfil tenga más canciones populares en entrenamiento:
debe conservar concentración en la nueva evaluación y mostrar incertidumbre.
Si el contraste no se confirma, ese es el resultado; no se cambia el umbral o
el modelo para obtener una asociación más llamativa. Las cuatro configuraciones
comparten observaciones y no representan confirmaciones independientes.

La fuente es histórica y de conveniencia. Artista, promoción, idioma o exposición
pueden explicar diferencias; no se analizan estructura, melodía o letra. La revisión
fue motivada por resultados previos y no se presenta como prerregistro externo.

Fuente: Pandya, Spotify Tracks Dataset, Hugging Face; licencia declarada: bsd.
https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset
Se utilizó ChatGPT/Codex para implementación y documentación. Completar autores,
revisar los resultados y declarar la asistencia. No se garantiza una nota de 100.
