"""Adaptador local del lector de microplanificación v5. Fuentes originales intactas."""
from pathlib import Path
from datetime import datetime,timezone
import json,gzip,hashlib,re,threading,uuid,os

ROOT=Path(__file__).resolve().parent
DEFAULT=Path(r'D:\00000-PAHO-OMS\0-Priorizacion\COL')
CATALOGS={};JOBS={}
LABELS={'salud':'Servicios de salud','vias':'Vías','escuelas':'Educación','localidades':'Localidades','rios':'Ríos','edificios':'Edificios','sitios':'Sitios de interés','aeropuertos':'Aeropuertos','accesibilidad':'Accesibilidad','limites':'Límites','otros':'Otras capas','tabla':'Puntos de tablas','raster':'Raster'}

def norm(v):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFKD',str(v)) if not unicodedata.combining(c)).lower()

def category(e):
    p=norm(e.get('archive_source') or e['path']);n=norm(Path(e['path']).name)
    if e['kind']=='raster':return 'raster'
    if e['kind']=='table':return 'tabla'
    for key,hints in [('accesibilidad',['_access.gpkg','accesibilidad']),('salud',['health','salud']),('escuelas',['education','educacion','escuelas']),('localidades',['populated_places','localidades']),('vias',['roads','vias','red_vial']),('rios',['waterways','rios']),('edificios',['buildings','edificios']),('aeropuertos',['airports','aeropuerto']),('limites',['basicas','adm0','adm1','adm2']),('sitios',['points_of_interest','cultural_places','sitiosdeinteres'])]:
        if any(x in p for x in hints):return key
    return 'otros'

def inspect(path):
    from microplan.sources import inventory
    from microplan.discovery import name_field
    root=Path(path).expanduser().resolve()
    if not root.is_dir():raise ValueError('La carpeta no existe. Seleccione la misma carpeta local de microplanificación.')
    if (root/'COL').is_dir():root=root/'COL'
    entries,notes=inventory(root)
    # metadata.json are auxiliary manifests, not vector layers.
    notes=[n for n in notes if not n.startswith('metadata.json:')]
    defaults={'health_facilities_points.shp','health_facilities_polygons.shp','education_facilities_points.shp','education_facilities_polygons.shp','roads_lines.shp','waterways_lines.shp','populated_places_points.shp','points_of_interest_points.shp','cultural_places_points.shp'}
    for e in entries:
        e['id']=hashlib.sha256(((e.get('archive_source') or e['path'])+'|'+str(e.get('layer'))).encode()).hexdigest()[:16]
        e['category']=category(e);e['category_label']=LABELS[e['category']]
        e['name_field']=name_field(e) if e.get('fields') else None
        e['selected']=Path(e['path']).name.lower() in defaults or e['category']=='accesibilidad' and str(e.get('layer')).lower()=='adm0'
        e['bytes']=Path(e['path']).stat().st_size
        e['modified']=datetime.fromtimestamp(Path(e['path']).stat().st_mtime,timezone.utc).isoformat()
    if not any(e['selected'] and e['category']=='salud' for e in entries):
        from microplan.discovery import suggest
        ix=suggest(entries,'salud')
        if ix is not None:entries[ix]['selected']=True
    token=uuid.uuid4().hex
    result={'id':token,'root':str(root),'entries':entries,'notes':notes,'scanned':datetime.now(timezone.utc).isoformat(),'engine':'microplanificación v5 · lector reutilizado'}
    CATALOGS[token]=result
    return result

def folders(path=None):
    p=Path(path or (DEFAULT if DEFAULT.exists() else ROOT)).expanduser().resolve()
    if not p.is_dir():raise ValueError('La carpeta no existe.')
    try:children=[{'name':c.name,'path':str(c)} for c in sorted(p.iterdir(),key=lambda x:x.name.casefold()) if c.is_dir() and not c.name.startswith('.') and not c.is_symlink()]
    except OSError as exc:raise ValueError('No fue posible leer esta carpeta.') from exc
    drives=[str(Path(f'{x}:/')) for x in 'CDEFGHIJKLMNOPQRSTUVWXYZ' if Path(f'{x}:/').is_dir()] if os.name=='nt' else ['/']
    return {'path':str(p),'parent':str(p.parent),'children':children,'drives':drives}

def boundary_for(filters,catalog):
    import geopandas as gpd
    muni=str(filters.get('municipality') or '');dept=str(filters.get('department') or '')
    if muni and not re.fullmatch(r'\d{5}',muni):raise ValueError('Código municipal inválido.')
    if dept and not re.fullmatch(r'\d{2}',dept):raise ValueError('Código departamental inválido.')
    area=filters.get('area_geometry')
    if area:
        frame=gpd.GeoDataFrame.from_features([{'type':'Feature','geometry':area,'properties':{}}],crs=4326)
        if not frame.geometry.is_valid.all() or not frame.geom_type.isin(['Polygon','MultiPolygon']).all():raise ValueError('Área de análisis inválida.')
        return frame
    # Prefer the same national catalogue already present in the user's repository.
    names=['COL_ADM2_FN_2026.shp','COL_N2.shp'] if muni else ['COL_ADM1_FN.shp'] if dept else ['COL_ADM0_FN.shp','COL_N0.shp']
    for name in names:
        entry=next((e for e in catalog['entries'] if Path(e['path']).name.lower()==name.lower()),None)
        if not entry:continue
        code=muni or dept
        candidates=['ADM2_NATC','ADM2_NAT_C','MPIO_CCNCT','GIS_CODE','ID'] if muni else ['ADM1_NATC','ADM1_NAT_C','DPTO_CCDGO','GIS_CODE','ID']
        field=next((f for f in candidates if f in entry['fields']),None)
        if code and not field:continue
        value='COL_'+code if field=='GIS_CODE' else code
        frame=gpd.read_file(entry['path'],layer=entry['layer'],**({'where':f'"{field}" = \'{value}\''} if code else {}))
        if len(frame)==1:
            if frame.crs is None:frame=frame.set_crs(entry['crs'])
            frame=frame.to_crs(4326);frame.geometry=frame.geometry.make_valid();return frame
    folder='adm2_v03' if muni else 'adm1'
    data=json.loads(gzip.decompress((ROOT/'referencia'/f'COL_{folder}.geojson.gz').read_bytes()))
    if muni or dept:
        code=muni or dept;key='ADM2_NATC' if muni else 'ADM1_NATC';data['features']=[f for f in data['features'] if f['properties'].get(key)==code]
    frame=gpd.GeoDataFrame.from_features(data['features'],crs=4326)
    if frame.empty:raise ValueError('No se encontró el territorio.')
    frame.geometry=frame.geometry.make_valid();return frame

def read_accessibility(entry,area):
    """Clip very large national polygons one feature at a time, without changing the source."""
    import geopandas as gpd
    import pyogrio,shapely,pandas as pd
    source=Path(entry['path']);boundary=area.to_crs(4326).geometry.union_all()
    signature=[str(source),source.stat().st_size,source.stat().st_mtime_ns,entry['layer'],boundary.wkb_hex]
    key=hashlib.sha256(json.dumps(signature).encode()).hexdigest()
    cache=ROOT/'cache'/'accesibilidad';cache.mkdir(parents=True,exist_ok=True)
    target=cache/(key+'.parquet')
    if target.exists():return gpd.read_parquet(target),[]
    pieces=[];bbox=tuple(area.to_crs(entry['crs']).total_bounds)
    with pyogrio.open_arrow(source,layer=entry['layer'],bbox=bbox,batch_size=1,return_fids=True,use_pyarrow=True) as stream:
        metadata,reader=stream
        for batch in reader:
            tab=batch.to_pandas();geometry=shapely.from_wkb(tab.pop(metadata.get('geometry_name') or 'wkb_geometry').to_numpy())
            tab['_fid_fuente']=tab.pop(metadata.get('fid_column') or 'fid').astype(str)
            frame=gpd.GeoDataFrame(tab,geometry=geometry,crs=entry['crs']).to_crs(4326)
            frame=frame.loc[frame.geometry.notna() & ~frame.geometry.is_empty].copy()
            frame.geometry=frame.geometry.make_valid()
            frame['_geometria_fuente_sha256']=[hashlib.sha256(g.wkb).hexdigest() for g in frame.geometry]
            frame.geometry=frame.geometry.intersection(boundary)
            frame=frame.loc[~frame.geometry.is_empty].copy()
            if not frame.empty:pieces.append(frame)
    result=gpd.GeoDataFrame(pd.concat(pieces,ignore_index=True),crs=4326) if pieces else gpd.GeoDataFrame(geometry=[],crs=4326)
    result['_archivo_fuente']=str(source);result['_capa_fuente']=entry['layer']
    temporary=target.with_suffix('.'+uuid.uuid4().hex+'.tmp');result.to_parquet(temporary,index=False);temporary.replace(target)
    return result,[]

def load_layers(catalog,selected,filters,progress=lambda value:None):
    from microplan.sources import read_vector
    import geopandas as gpd
    entries={e['id']:e for e in catalog['entries']};ids=[x['id'] for x in selected]
    if len(ids)!=len(set(ids)):raise ValueError('No seleccione la misma capa dos veces.')
    if not ids or any(x not in entries for x in ids):raise ValueError('Seleccione capas del inventario vigente.')
    area=boundary_for(filters,catalog);results=[];notes=[];sources=[];total=0
    for i,selection in enumerate(selected):
        entry=dict(entries[selection['id']]);role=selection.get('category',entry['category']);field=selection.get('name_field') or entry.get('name_field')
        if role not in LABELS or entry['kind']=='raster':raise ValueError('La consulta vectorial no admite esa categoría. El raster permanece inventariado.')
        progress(f'Leyendo y recortando {i+1}/{len(selected)}: {entry["label"]}')
        if entry['kind']=='table':
            from microplan.coordinates import coordinate_fields
            lat,lon=coordinate_fields(entry['fields']);entry['latitude']=selection.get('latitude') or lat;entry['longitude']=selection.get('longitude') or lon
        frame,warnings=read_accessibility(entry,area) if role=='accesibilidad' and Path(entry['path']).suffix.lower()=='.gpkg' else read_vector(entry,area)
        if len(frame)>150000:raise ValueError(f'{entry["label"]}: el recorte contiene {len(frame):,} registros. Use un área menor o excluya esa capa. No se truncó la fuente.')
        total+=len(frame)
        if total>250000:raise ValueError('La selección supera 250.000 elementos para el geoportal. Reduzca territorio o capas; no se publican resultados parciales.')
        notes.extend(warnings)
        source_id='REPO-'+entry['id'];features=[]
        # Keep native fields. Null attributes do not carry useful information in the portal.
        encoded=json.loads(frame.to_json(drop_id=True,na='drop'))
        for index,feature in enumerate(encoded['features']):
            props=feature['properties'];fid=str(props.get('_fid_fuente',index));name=str(props.get(field) or props.get('name') or props.get('nombre') or f'Sin nombre · {fid}')
            props['_iets_id']=entry['id']+'-'+fid;props['_nombre']=name;props['source_id']=source_id
            feature['id']=props['_iets_id'];features.append(feature)
        result={'id':entry['id'],'name':LABELS[role]+' · '+Path(entry['path']).stem,'category':role,'source_id':source_id,'department':filters.get('department',''),'municipality':filters.get('municipality',''),'area':filters.get('area',''),'visible':role not in ['accesibilidad','edificios'],'featureCount':len(features),'geometry':entry.get('geometry'),'collection':{'type':'FeatureCollection','features':features},'fields':entry.get('fields',[]),'name_field':field}
        results.append(result)
        sources.append({'id':source_id,'name':result['name'],'source':entry.get('archive_source') or entry['path'],'layer':entry.get('layer'),'cutoff':None,'version':'Archivo local · modificado '+entry['modified'],'owner':'Responsable de la fuente por confirmar','license':'Conservar las condiciones del repositorio de origen','coverage':f'Recorte del ámbito {filters.get("municipality") or filters.get("department") or "Colombia"}: {len(features)} elementos. Cobertura no confirmada.','demo':False,'repository':True,'note':'Fecha de modificación del archivo no equivale a fecha de corte de los datos. CRS de origen: '+str(entry['crs']),'fingerprint':hashlib.sha256(json.dumps(features,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()})
    clipped=json.loads(area.to_json(drop_id=True,na='drop'));result={'layers':results,'sources':sources,'notes':notes,'boundary':clipped,'filters':filters,'root':catalog['root'],'generated':datetime.now(timezone.utc).isoformat(),'catalog':{k:v for k,v in catalog.items() if k!='id'}}
    size=len(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode())
    if size>100*1024*1024:raise ValueError('El recorte supera 100 MB. Reduzca el área o las capas para conservar una consulta manejable.')
    progress(f'Listo: {len(results)} capas y {total:,} elementos recortados')
    return result

def start_job(kind,body):
    job_id=uuid.uuid4().hex;job={'id':job_id,'status':'working','message':'Preparando lectura local…'};JOBS[job_id]=job
    def run():
        try:
            if kind=='inspect':result=inspect(body.get('path',str(DEFAULT)))
            else:
                catalog=CATALOGS.get(body.get('catalog_id'))
                if not catalog:raise ValueError('Vuelva a leer el repositorio; el inventario ya no está activo en este servidor.')
                result=load_layers(catalog,body.get('selected',[]),body.get('filters',{}),lambda m:job.update(message=m))
            job.update(status='complete',result=result,message='Lectura terminada')
        except Exception as exc:job.update(status='failed',message=str(exc))
    threading.Thread(target=run,daemon=True).start();return {'id':job_id,'status':'working'}

def job_state(job_id):
    job=JOBS.get(job_id)
    if not job:raise ValueError('Trabajo no encontrado.')
    return dict(job)
