"""Read user tables as WGS84 points. No remote geocoding, no source edits."""
from pathlib import Path
import re, unicodedata, zipfile, xml.etree.ElementTree as ET
import pandas as pd
import geopandas as gpd

LIMIT = 200000
NS = {'t':'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
      'x':'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
      'o':'urn:oasis:names:tc:opendocument:xmlns:office:1.0'}

def norm(value):
    return ''.join(c for c in unicodedata.normalize('NFD',str(value).lower()) if not unicodedata.combining(c)).strip()

def coordinate_fields(fields):
    found={norm(f):f for f in fields}
    return (next((found[n] for n in ['latitud','latitude','lat'] if n in found),None),
            next((found[n] for n in ['longitud','longitude','lon','long','lng'] if n in found),None))

def ods_sheets(path):
    with zipfile.ZipFile(path) as z:
        if z.getinfo('content.xml').file_size > 50_000_000: raise ValueError('ODS excede 50 MB de contenido.')
        root=ET.fromstring(z.read('content.xml'))
    result={}
    for table in root.findall('.//t:table',NS):
        rows=[];pending_empty=0
        for row in table.findall('t:table-row',NS):
            cells=[]
            for cell in row:
                repeat=int(cell.get('{'+NS['t']+'}number-columns-repeated',1))
                value=cell.get('{'+NS['o']+'}value')
                if value is None: value=' '.join(''.join(p.itertext()) for p in cell.findall('x:p',NS))
                if value and len(cells)+repeat>500: raise ValueError('ODS excede 500 columnas con datos.')
                cells.extend([value]*min(repeat,max(0,500-len(cells))))
            if not any(v not in ['',None] for v in cells):
                pending_empty+=int(row.get('{'+NS['t']+'}number-rows-repeated',1));continue
            count=int(row.get('{'+NS['t']+'}number-rows-repeated',1))
            if len(rows)+pending_empty+count > LIMIT+20: raise ValueError('Tabla excede 200.000 filas; divida por territorio.')
            rows.extend([[]]*pending_empty);pending_empty=0
            rows.extend([cells]*count)
        result[table.get('{'+NS['t']+'}name')]=rows
    return result

def read_tables(path):
    path=Path(path)
    if path.suffix.lower()=='.ods': return ods_sheets(path)
    if path.suffix.lower() in ['.xlsx','.xlsm']:
        import openpyxl
        wb=openpyxl.load_workbook(path,read_only=True,data_only=True)
        try:
            result={}
            for sheet in wb:
                if sheet.max_row>LIMIT+20 or sheet.max_column>500: raise ValueError('Hoja demasiado grande; divida por territorio.')
                result[sheet.title]=list(sheet.values)
            return result
        finally: wb.close()
    try: frame=pd.read_csv(path,sep=None,engine='python',header=None,dtype=str,nrows=LIMIT+21,encoding='utf-8-sig')
    except UnicodeDecodeError: frame=pd.read_csv(path,sep=None,engine='python',header=None,dtype=str,nrows=LIMIT+21,encoding='cp1252')
    if len(frame)>LIMIT+20: raise ValueError('CSV excede 200.000 filas.')
    return {path.stem:frame.fillna('').values.tolist()}

def as_frame(rows):
    if not rows:return pd.DataFrame(),0
    header=next((i for i,row in enumerate(rows[:20]) if all(coordinate_fields(row))),0)
    fields=[];seen={}
    for i,value in enumerate(rows[header]):
        name=str(value).strip() if value is not None and str(value).strip() else f'Columna_{i+1}'
        seen[name]=seen.get(name,0)+1
        fields.append(name if seen[name]==1 else f'{name}_{seen[name]}')
    frame=pd.DataFrame([list(row[:len(fields)])+[None]*max(0,len(fields)-len(row)) for row in rows[header+1:]],columns=fields)
    return frame,header+2

def table_entries(path):
    result=[]
    for sheet,rows in read_tables(path).items():
        frame,start=as_frame(rows)
        if frame.empty:continue
        lat,lon=coordinate_fields(frame.columns)
        result.append(dict(path=str(path),layer=sheet,kind='table',geometry='Point',
            label=f'{Path(path).name} · {sheet}',fields=list(frame.columns),features=len(frame),
            crs='EPSG:4326',latitude=lat,longitude=lon))
    return result

def read_points(entry,area):
    frame,start=as_frame(read_tables(entry['path'])[entry['layer']])
    lat,lon=entry.get('latitude'),entry.get('longitude')
    if not lat or not lon or lat==lon:raise ValueError('Seleccione campos distintos de latitud y longitud en grados WGS84.')
    def parse(v):
        if pd.isna(v):return float('nan')
        text=str(v).strip().replace('−','-')
        if re.fullmatch(r'[+-]?\d+,\d+',text):text=text.replace(',','.')
        try:return float(text)
        except ValueError:return float('nan')
    y=frame[lat].map(parse);x=frame[lon].map(parse)
    valid=y.between(-90,90)&x.between(-180,180)
    frame['_fila_fuente']=range(start,start+len(frame));frame['_fid_fuente']=frame['_fila_fuente']
    frame['_archivo_fuente']=entry['path'];frame['_hoja_fuente']=entry['layer']
    rejected=frame.loc[~valid].copy();rejected['_motivo']='Coordenada ausente, no numérica o fuera de rango WGS84'
    data=gpd.GeoDataFrame(frame.loc[valid].copy(),geometry=gpd.points_from_xy(x[valid],y[valid]),crs=4326)
    data['_punto_conteo_lon']=x[valid];data['_punto_conteo_lat']=y[valid]
    notes=[f'{entry["label"]}: {len(frame)} filas; {len(rejected)} con coordenadas inválidas. No se invierten coordenadas ni se buscan direcciones automáticamente.']
    if area is not None:
        inside=data.intersects(area.to_crs(4326).geometry.union_all())
        outside=data.loc[~inside].drop(columns='geometry').copy();outside['_motivo']='Fuera del territorio seleccionado'
        rejected=pd.concat([rejected,outside],ignore_index=True)
        notes.append(f'{entry["label"]}: {int((~inside).sum())} coordenadas fuera del territorio seleccionado.')
        data=data.loc[inside].copy()
    data.attrs['rejected_coordinates']=rejected
    return data,notes
