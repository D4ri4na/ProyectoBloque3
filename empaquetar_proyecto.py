"""Empaqueta solo el proyecto y sus resultados, sin archivos ajenos ni cachés."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parent
out = ROOT / 'entregables'
out.mkdir(exist_ok=True)
dest = out / 'Proyecto_Musica_Bloque3.zip'
names = ['README.md', 'requirements.txt', 'requirements-lock.txt', 'descargar_dataset.py',
         'proyecto_musica.py', 'crear_cuaderno.py', 'ejecutar_cuaderno.py',
         'empaquetar_proyecto.py', 'Proyecto_Musica.ipynb', 'Informe_Tecnico_Bloque3.pdf',
         'Diapositivas_Proyecto_Bloque3.pdf', 'Presentacion_Proyecto_Bloque3.pptx']
files = [ROOT / name for name in names]
files += sorted((ROOT / 'outputs').rglob('*'))
files += sorted((ROOT / 'data/raw').glob('*'))
files = [p for p in files if p.is_file() and p.suffix != '.part']
with zipfile.ZipFile(dest, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in files:
        archive.write(path, 'Proyecto_Musica_Bloque3/' + path.relative_to(ROOT).as_posix())
with zipfile.ZipFile(dest) as archive:
    assert archive.testzip() is None
    assert any(n.endswith('data/raw/spotify_tracks.csv') for n in archive.namelist())
    assert any(n.endswith('outputs/validacion.json') for n in archive.namelist())
print(json.dumps(dict(path=str(dest), files=len(files), bytes=dest.stat().st_size,
                     sha256=hashlib.sha256(dest.read_bytes()).hexdigest()), indent=2), flush=True)
