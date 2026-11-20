from pathlib import Path
import json
import zipfile

ROOT=Path(__file__).resolve().parent
dest=ROOT.parent/'entregables/Explorador_Musical.zip'
dest.parent.mkdir(exist_ok=True)
files=[p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts
       and '.ipynb_checkpoints' not in p.parts and p.name!='interfaz_verificacion.js']
with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for p in files: archive.write(p,'Explorador_Musical/'+p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(dest) as archive: assert archive.testzip() is None
print(json.dumps(dict(file=str(dest),files=len(files),bytes=dest.stat().st_size),indent=2),flush=True)
