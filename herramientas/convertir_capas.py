"""Conversor opcional a GeoJSON/CSV. No forma parte de la instalación básica.
Requiere geopandas para vectores; pandas/openpyxl para Excel. Nunca cambia el origen.
Después de convertir, normalice los campos del diccionario antes de cargar en la app.
"""
import argparse
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('origen',type=Path);parser.add_argument('destino',type=Path)
parser.add_argument('--capa');parser.add_argument('--hoja',default=0)
args=parser.parse_args()
if args.origen.resolve()==args.destino.resolve() or args.destino.exists():raise SystemExit('Use un destino nuevo; no se sobrescriben archivos.')
if args.origen.suffix.lower() in ('.xlsx','.xls'):
    try:import pandas as pd
    except ImportError:raise SystemExit('Instale pandas y el lector de Excel en un entorno separado para usar este conversor opcional.')
    sheet=int(args.hoja) if str(args.hoja).isdigit() else args.hoja
    data=pd.read_excel(args.origen,sheet_name=sheet,dtype=str)
    if args.destino.suffix.lower()!='.csv':raise SystemExit('Para Excel el destino debe ser .csv.')
    data.to_csv(args.destino,index=False,encoding='utf-8-sig')
else:
    try:import geopandas as gpd
    except ImportError:raise SystemExit('Instale geopandas en un entorno separado para convertir formatos vectoriales.')
    if args.destino.suffix.lower() not in ('.json','.geojson'):raise SystemExit('El destino vectorial debe ser .geojson.')
    data=gpd.read_file(args.origen,**({'layer':args.capa} if args.capa else {}))
    if data.crs is None:raise SystemExit('La fuente no declara su sistema de coordenadas. Identifíquelo antes de convertir.')
    if data.geometry.isna().any() or data.geometry.is_empty.any() or (~data.geometry.is_valid).any():raise SystemExit('La fuente contiene geometrías vacías o inválidas. Corríjalas antes de convertir.')
    data.to_crs(4326).to_file(args.destino,driver='GeoJSON',encoding='utf-8')
print('Conversión terminada. Revise los campos y valores con manuales/datos.html antes de cargar.')
