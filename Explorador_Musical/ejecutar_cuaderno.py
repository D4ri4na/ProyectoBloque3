"""Ejecuta las celdas Python en orden y conserva sus salidas reales, sin servidor Jupyter."""
from pathlib import Path
import contextlib
import io
import json
import os
import time
import traceback

ROOT = Path(__file__).resolve().parent
path = ROOT / 'Proyecto_Musica.ipynb'
notebook = json.loads(path.read_text(encoding='utf-8'))
os.chdir(ROOT)
namespace = {'__name__':'__main__'}
start = time.perf_counter()
count = 0
for index, cell in enumerate(notebook['cells']):
    if cell['cell_type'] != 'code':
        continue
    count += 1
    print(f'Ejecutando celda Python {count} (posición {index+1})', flush=True)
    output, error = io.StringIO(), io.StringIO()
    cell['execution_count'] = count
    cell['outputs'] = []
    failed = False
    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            exec(compile(''.join(cell['source']), f'Proyecto_Musica.ipynb/celda_{index+1}', 'exec'), namespace)
    except Exception as exc:
        cell['outputs'].append(dict(output_type='error', ename=type(exc).__name__,
                                    evalue=str(exc), traceback=traceback.format_exc().splitlines()))
        failed = True
    for stream, buffer in [('stdout',output),('stderr',error)]:
        if buffer.getvalue():
            cell['outputs'].append(dict(output_type='stream', name=stream, text=buffer.getvalue().splitlines(keepends=True)))
            print(buffer.getvalue()[-1500:], flush=True)
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding='utf-8')
    if failed:
        raise RuntimeError(f'Falló la celda {index+1}; revisar salida del notebook.')
notebook['metadata']['execution_verification'] = {
    'method':'Sequential Python exec, shared namespace, real stdout/stderr; no magics',
    'code_cells_executed':count, 'errors':0, 'elapsed_seconds':time.perf_counter()-start}
path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'Cuaderno completo: {count} celdas Python, cero errores, {time.perf_counter()-start:.1f}s.', flush=True)
