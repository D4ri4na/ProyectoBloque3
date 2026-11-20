"""Ejecuta el notebook del explorador usando el verificador secuencial existente."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
source=(ROOT/'ejecutar_cuaderno.py').read_text(encoding='utf-8')
source=source.replace('Proyecto_Musica.ipynb','Proyecto_Explorador_Musical.ipynb')
exec(compile(source,str(ROOT/'ejecutar_cuaderno.py'),'exec'),{'__name__':'__main__','__file__':str(ROOT/'ejecutar_cuaderno.py')})
