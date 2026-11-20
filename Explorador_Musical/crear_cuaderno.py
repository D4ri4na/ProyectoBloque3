"""Construye un notebook con el código completo visible y secciones de lectura."""
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parent
source = (ROOT / 'proyecto_musica.py').read_text(encoding='utf-8')
source = source.split("if __name__ == '__main__':")[0]
source = source.replace("ROOT = Path(__file__).resolve().parent", "ROOT = Path.cwd()")
sections = source.split('\ndef ')
cells = [nbf.v4.new_markdown_cell('''# ¿Las canciones populares tienen un sonido particular?

**Bloque 3 · Aprendizaje no supervisado**

Comparación de K-Means y GMM antes/después de PCA. La popularidad se reserva
para describir los grupos después de seleccionar modelos con entrenamiento.

Ejecutar desde la carpeta del proyecto con **Run All**. Si falta el CSV, se
intentará descargar. No hay resultados inventados ni entrenamiento supervisado.

## Diseño

- Diez características numéricas, sin identificadores, género ni popularidad.
- Canciones únicas; muestra reproducible de 10.000; partición 80/20.
- Imputación, escalado y PCA ajustados únicamente con entrenamiento.
- K-Means: Silhouette; GMM: BIC. PCA: mínimo 90 % de varianza.
- Tres métricas, comparación en geometría común, ARI, tiempos y estabilidad.
- Descripción de popularidad en prueba, sin usarla para elegir configuraciones.

El código de todas las etapas aparece a continuación para facilitar su revisión.
'''), nbf.v4.new_code_cell(sections[0])]
descriptions = {
    'prepare':'Preparación y análisis exploratorio; ajuste sin fuga de información.',
    'tune':'Búsqueda de hiperparámetros sobre entrenamiento exclusivamente.',
    'stability':'Estabilidad: semillas y submuestras; etiquetas sobre el mismo test.',
    'profiles':'Perfiles en unidades originales y popularidad retenida fuera del ajuste.',
    'run':'Orquestación del experimento completo y exportación de resultados.',
    'write_report':'Informe con cifras calculadas y las doce preguntas de la rúbrica.',
    'validate_outputs':'Comprobaciones de integridad de los resultados.'}
for section in sections[1:]:
    name = section.split('(')[0]
    if name in descriptions:
        cells.append(nbf.v4.new_markdown_cell('### '+descriptions[name]))
    cells.append(nbf.v4.new_code_cell('def '+section))
cells += [nbf.v4.new_markdown_cell('## Ejecutar los cuatro experimentos\nLa búsqueda puede tardar varios minutos. Los resultados se guardan en `outputs/`.'),
    nbf.v4.new_code_cell('with threadpool_limits(limits=1):\n    run(sample_size=10000, kmax=12)'),
    nbf.v4.new_markdown_cell('## Comparación de modelos'),
    nbf.v4.new_code_cell("print(pd.read_csv(OUT / 'comparativa.csv').to_string(index=False))"),
    nbf.v4.new_markdown_cell('## Varianza y perfiles'),
    nbf.v4.new_code_cell("print(pd.read_csv(OUT / 'varianza_pca.csv').to_string(index=False))\nprint(pd.read_csv(OUT / 'popularidad_pruebas.csv').to_string(index=False))"),
    nbf.v4.new_markdown_cell('![Varianza PCA](outputs/figures/03_varianza_pca.png)\n\n![Popularidad K-Means PCA](outputs/figures/06_popularidad_KMeans_pca.png)\n\n![Popularidad GMM PCA](outputs/figures/06_popularidad_GMM_pca.png)'),
    nbf.v4.new_markdown_cell('## Informe y declaración de IA\nAbrir `outputs/informe.html` para leer el informe completo. Se utilizó ChatGPT/Codex para estructurar el análisis y escribir código; el estudiante debe revisar los resultados y declarar esta asistencia.'),
    nbf.v4.new_code_cell("print((OUT / 'informe.md').read_text(encoding='utf-8'))\nprint((OUT / 'versiones.json').read_text(encoding='utf-8'))")]
nb = nbf.v4.new_notebook(cells=cells, metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}, 'language_info':{'name':'python','version':'3.12'}})
nbf.validate(nb)
nbf.write(nb, ROOT / 'Proyecto_Musica.ipynb')
print('Cuaderno creado con código completo visible.')
