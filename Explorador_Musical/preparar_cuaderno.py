"""Genera el notebook independiente con base experimental y explorador."""
from pathlib import Path
import runpy
import nbformat as nbf

ROOT=Path(__file__).resolve().parent
runpy.run_path(str(ROOT/'crear_cuaderno.py'))
temporary=ROOT/'Proyecto_Musica.ipynb'
notebook=nbf.read(temporary,as_version=4)
notebook.cells[0]=nbf.v4.new_markdown_cell('''# SONORA — Explorador musical

## ¿Cómo cambian perfiles y sugerencias entre modelos y representaciones sonoras?

Este cuaderno ejecuta el experimento completo de Bloque 3: K-Means y GMM antes
y después de PCA, con diez variables y sin utilizar popularidad ni género para
entrenar. Conserva la popularidad como una pregunta descriptiva secundaria.

Después construye un explorador offline y evalúa la conservación de vecinos
sobre 200 consultas de prueba, con candidatos de entrenamiento. La evaluación
geométrica no equivale a validación de preferencias de los oyentes.

Ejecutar todas las celdas desde esta carpeta. El HTML generado contiene datos,
coordenadas y asignaciones y funciona con doble clic, sin servidor ni API.

Los nombres de perfiles son descripciones, no géneros musicales verdaderos.
Se utilizó ChatGPT/Codex como asistencia; revisar el código y declarar su uso.
''')
notebook.cells += [nbf.v4.new_markdown_cell('## Construir y evaluar el explorador\nReproduce las cuatro particiones con ARI=1, calcula vecinos y genera la interfaz offline.'),
    nbf.v4.new_code_cell("from construir_explorador import build\nwith threadpool_limits(limits=1):\n    explorer_data = build()"),
    nbf.v4.new_markdown_cell('## Evaluación adicional e informe principal'),
    nbf.v4.new_code_cell("print(pd.read_csv(OUT / 'resumen_recuperacion.csv').to_string(index=False))\nprint((OUT / 'informe_explorador.md').read_text(encoding='utf-8'))\nprint('Demo: Explorador_Musical.html')")]
nbf.validate(notebook)
nbf.write(notebook,ROOT/'Proyecto_Explorador_Musical.ipynb')
temporary.unlink()
print('Cuaderno del explorador creado.',flush=True)
