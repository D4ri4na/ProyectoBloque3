"""Descarga verificable, sin credenciales. También admite un CSV ya descargado."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
import requests

ROOT = Path(__file__).resolve().parent
URL = 'https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset/resolve/635b034f69257814eff850a5c2b3346fe458134f/dataset.csv?download=true'
SOURCE = 'https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset'

def download(local=None):
    dest = ROOT / 'data/raw/spotify_tracks.csv'
    dest.parent.mkdir(parents=True, exist_ok=True)
    if local:
        origin = Path(local).resolve()
        if origin != dest.resolve():
            shutil.copyfile(origin, dest)
    elif not dest.exists():
        temp = dest.with_suffix('.part')
        try:
            with requests.get(URL, stream=True, timeout=(15, 90)) as response:
                response.raise_for_status()
                with temp.open('wb') as handle:
                    for chunk in response.iter_content(1024 * 1024):
                        handle.write(chunk)
            temp.replace(dest)
        except requests.RequestException as exc:
            temp.unlink(missing_ok=True)
            raise RuntimeError('No se pudo descargar el dataset. Descarga dataset.csv desde '
                               + SOURCE + '/tree/main y ejecuta python descargar_dataset.py --archivo RUTA') from exc
    header = dest.open(encoding='utf-8-sig').readline()
    if not all(name in header for name in ['track_id', 'popularity', 'danceability', 'tempo']):
        raise ValueError('El archivo no tiene las columnas esperadas; no se acepta HTML ni datos simulados.')
    manifest = dict(source=SOURCE, download_url=URL, revision='635b034f69257814eff850a5c2b3346fe458134f',
                    sha256=hashlib.sha256(dest.read_bytes()).hexdigest(), bytes=dest.stat().st_size,
                    checked_at_utc=datetime.now(timezone.utc).isoformat(),
                    license_note='La ficha del repositorio declara BSD; verificar términos antes de redistribuir. No se incluye audio.')
    (dest.parent / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Dataset disponible: {dest} ({manifest["bytes"]:,} bytes)', flush=True)
    return dest

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--archivo', help='CSV obtenido manualmente de la fuente')
    download(parser.parse_args().archivo)
