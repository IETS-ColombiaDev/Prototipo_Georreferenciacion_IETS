from pathlib import Path
import re
import uuid
import zipfile
import hashlib,json
import xml.etree.ElementTree as ET
import geopandas as gpd
import pyogrio

VECTOR = {'.shp', '.gpkg', '.geojson', '.json', '.fgb', '.kml'}

def hot_export_crs(path,info):
    """Documented inference, only for unchanged HOT exports with embedded README.
    Never guess a CRS merely because coordinates resemble longitude/latitude.
    """
    archive=path.with_suffix('.zip')
    if not path.name.startswith('hotosm_') or not archive.exists():return None
    with zipfile.ZipFile(archive) as z:
        names={Path(n).name.lower():n for n in z.namelist()}
        readme=names.get('readme.txt')
        if not readme or 'github.com/hotosm/raw-data-api' not in z.read(readme).decode('utf8',errors='replace'):return None
        for ext in ['.shp','.shx','.dbf']:
            component=path.with_suffix(ext);member=names.get(component.name.lower())
            if not member or not component.exists():return None
            with component.open('rb') as f,z.open(member) as other:
                if hashlib.file_digest(f,'sha256').digest()!=hashlib.file_digest(other,'sha256').digest():return None
        prj=names.get(path.with_suffix('.prj').name.lower())
        if prj:
            from pyproj import CRS
            return CRS.from_wkt(z.read(prj).decode()).to_string(),[str(archive)+'!'+prj]
        bounds=info.get('total_bounds')
        if bounds is None or not (-180<=bounds[0]<=bounds[2]<=180 and -90<=bounds[1]<=bounds[3]<=90):return None
        return 'EPSG:4326',[str(archive)+'!'+readme,'CRS inferido de exportación HOT Raw Data API intacta; geometría WGS84. https://github.com/hotosm/raw-data-api/blob/develop/src/query_builder/builder.py']

def archived_vectors(root):
    """Read small ZIP-only shapefiles into a private cache; never edit originals."""
    cache=Path(__file__).resolve().parents[1]/'cache/archivos'
    result=[]
    for archive in root.rglob('*.zip'):
        try:
            with zipfile.ZipFile(archive) as z:
                shapes=[n for n in z.namelist() if n.lower().endswith('.shp')]
                for member in shapes:
                    stem=Path(member).stem
                    if (archive.parent/(stem+'.shp')).exists():continue
                    components=[n for n in z.namelist() if Path(n).stem==stem and Path(n).suffix.lower() in ['.shp','.shx','.dbf','.prj','.cpg']]
                    if sum(z.getinfo(n).file_size for n in components)>500_000_000:continue
                    if not {'.shp','.shx','.dbf','.prj'}<= {Path(n).suffix.lower() for n in components}:continue
                    key=hashlib.sha256((str(archive)+str(archive.stat().st_mtime_ns)).encode()).hexdigest()[:20]
                    dest=cache/key;dest.mkdir(parents=True,exist_ok=True)
                    for n in components:
                        target=dest/Path(n).name
                        if not target.exists():
                            with z.open(n) as src,target.open('wb') as out:
                                import shutil
                                shutil.copyfileobj(src,out)
                    result.append((dest/Path(member).name,str(archive)))
        except (OSError,zipfile.BadZipFile):continue
    return result

def qgis_crs_metadata(root):
    """Read CRS declarations only; never execute project code or fetch remote sources."""
    declarations={}
    for project in sorted(root.glob('*.qgz')):
        try:
            with zipfile.ZipFile(project) as z:
                for member in z.infolist():
                    if not member.filename.endswith('.qgs') or member.file_size>25_000_000: continue
                    tree=ET.fromstring(z.read(member))
                    for layer in tree.findall('.//projectlayers/maplayer'):
                        source=layer.findtext('datasource','').split('|')[0]
                        auth=layer.findtext('srs/spatialrefsys/authid','')
                        if not source or not auth or source.startswith(('/vsi','http')): continue
                        path=(project.parent/source).resolve()
                        if root not in path.parents: continue
                        declarations.setdefault(str(path),[]).append((auth,str(project)))
        except (OSError,zipfile.BadZipFile,ET.ParseError):
            continue
    return declarations

def inventory(root):
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError('La carpeta no existe o no es accesible en este equipo.')
    entries, warnings = [], []
    declared=qgis_crs_metadata(root)
    archived=archived_vectors(root);archive_sources={str(p):source for p,source in archived}
    for path in sorted(list(root.rglob('*'))+[p for p,_ in archived]):
        if not path.is_file() or path.is_symlink():
            continue
        if path.suffix.lower() in VECTOR:
            if path.suffix.lower() == '.shp':
                siblings = {p.suffix.lower() for p in path.parent.glob(path.stem + '.*')}
                if not {'.dbf', '.shx'} <= siblings:
                    warnings.append(f'{path.name}: shapefile incompleto; requiere SHP, SHX y DBF.')
                    continue
            try:
                for layer, geom in pyogrio.list_layers(path):
                    if geom is None:
                        continue
                    info = pyogrio.read_info(path, layer=layer)
                    if str(geom).lower() in ['unknown','geometry']:
                        sample=pyogrio.read_dataframe(path,layer=layer,max_features=100)
                        geom='/'.join(sorted(sample.geom_type.dropna().unique()))
                    fallback=None; evidence=[]
                    if not info['crs']:
                        candidates=declared.get(str(path.resolve()),[])
                        distinct={x[0] for x in candidates}
                        if len(distinct)==1:
                            fallback=next(iter(distinct)); evidence=[x[1] for x in candidates]
                            warnings.append(f'{path.name}: CRS {fallback} recuperado de metadatos QGIS; fuente intacta.')
                        elif (hot:=hot_export_crs(path,info)) is not None:
                            fallback,evidence=hot
                            warnings.append(f'{path.name}: {fallback} por evidencia de exportación HOT; consultar método CRS en fuentes.')
                        else:
                            warnings.append(f'{path.name}: CRS ausente o declaraciones QGIS contradictorias; capa excluida.')
                            continue
                    entries.append(dict(path=str(path), layer=str(layer), kind='vector',
                        label=f'{archive_sources.get(str(path),str(path.relative_to(root)) if path.is_relative_to(root) else path.name)} · {layer}', geometry=str(geom),
                        archive_source=archive_sources.get(str(path)),
                        crs=info['crs'] or fallback, crs_override=fallback, crs_evidence=evidence,
                        fields=list(info['fields']), features=int(info['features'])))
            except Exception as e:
                warnings.append(f'{path.name}: no se pudo leer ({e}).')
        elif path.suffix.lower() in {'.csv','.ods','.xlsx','.xlsm'} and 'geocodific' in str(path.parent).lower():
            try:
                from .coordinates import table_entries
                entries.extend(table_entries(path))
            except Exception as exc: warnings.append(f'{path.name}: tabla no disponible. {exc}')
        elif path.suffix.lower() in {'.tif', '.tiff'}:
            entries.append(dict(path=str(path), layer=None, kind='raster', label=str(path.relative_to(root))))
    return entries, warnings

def read_vector(entry, area=None):
    if entry.get('kind')=='table':
        from .coordinates import read_points
        return read_points(entry,area)
    info = pyogrio.read_info(entry['path'], layer=entry['layer'])
    effective_crs=info['crs'] or entry.get('crs_override')
    if not effective_crs:
        raise ValueError(f"{entry['label']}: falta CRS; asígnelo en el archivo fuente con un SIG.")
    bbox = None if area is None else tuple(area.to_crs(effective_crs).total_bounds)
    source=Path(entry['path']); components=sorted(source.parent.glob(source.stem+'.*')) if source.suffix.lower()=='.shp' else [source]
    signature={'version':4,'files':[(str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in components if p.is_file()],
               'layer':entry['layer'],'crs':effective_crs,'boundary':None if area is None else area.geometry.union_all().wkb_hex}
    cache=Path(__file__).resolve().parents[1]/'cache/recortes';cache.mkdir(parents=True,exist_ok=True)
    key=hashlib.sha256(json.dumps(signature,sort_keys=True).encode()).hexdigest();cached=cache/(key+'.parquet');notes_file=cache/(key+'.json')
    if cached.exists() and notes_file.exists():
        result=gpd.read_parquet(cached)
        if entry.get('archive_source'):
            result['_archivo_fuente']=entry['archive_source'];result['_miembro_archivo']=source.name
        return result,json.loads(notes_file.read_text(encoding='utf8'))
    data = gpd.read_file(entry['path'], layer=entry['layer'], bbox=bbox,fid_as_index=True,use_arrow=True,max_features=500001)
    if len(data)>500000:
        # Read in bounded batches and discard outside geometries before concatenation.
        # This handles large cities without loading the national building layer.
        import pandas as pd
        import shapely
        from shapely.geometry import box
        boundary_native=area.to_crs(effective_crs).geometry.union_all() if area is not None else box(*bbox)
        chunks=[];total=0
        with pyogrio.open_arrow(entry['path'],layer=entry['layer'],bbox=bbox,batch_size=50000,return_fids=True,use_pyarrow=True) as arrow_source:
            metadata,reader=arrow_source
            for batch in reader:
                tab=batch.to_pandas();geom_col=metadata.get('geometry_name') or 'wkb_geometry'
                geometry=shapely.from_wkb(tab.pop(geom_col).to_numpy())
                mask=shapely.intersects(shapely.make_valid(geometry),boundary_native)
                if not mask.any():continue
                tab=tab.loc[mask].copy();tab.index=tab.pop(metadata.get('fid_column','fid'))
                piece=gpd.GeoDataFrame(tab,geometry=geometry[mask],crs=effective_crs)
                total+=len(piece)
                if total>2000000:raise ValueError('El lugar supera dos millones de registros; seleccione un área menor. No se entregan conteos parciales.')
                chunks.append(piece)
        data=gpd.GeoDataFrame(pd.concat(chunks),geometry='geometry',crs=effective_crs) if chunks else data.iloc[:0]
    data['_fid_fuente']=data.index.astype(str)
    data['_archivo_fuente']=entry.get('archive_source') or str(source.resolve());data['_capa_fuente']=str(entry['layer'])
    if entry.get('archive_source'):data['_miembro_archivo']=source.name
    warnings = []
    if data.crs is None:
        data=data.set_crs(effective_crs)
        warnings.append(f'{entry["label"]}: CRS asignado solo en memoria desde '+', '.join(entry.get('crs_evidence',[])))
    bad = data.geometry.isna() | data.geometry.is_empty
    if bad.any():
        warnings.append(f'{bad.sum()} geometrías vacías excluidas de {entry["label"]}.')
        data = data.loc[~bad].copy()
    invalid = ~data.geometry.is_valid
    if invalid.any():
        data.loc[invalid, 'geometry'] = data.loc[invalid].geometry.make_valid()
        warnings.append(f'{invalid.sum()} geometrías reparadas en memoria: {entry["label"]}.')
    data = data.to_crs(4326)
    points=data.geometry.representative_point()
    data['_punto_conteo_lon']=points.x;data['_punto_conteo_lat']=points.y
    data['_geometria_fuente_sha256']=[hashlib.sha256(g.wkb).hexdigest() for g in data.geometry]
    if not data.empty:
        x1, y1, x2, y2 = data.total_bounds
        if x1 < -180 or x2 > 180 or y1 < -90 or y2 > 90:
            raise ValueError('Coordenadas fuera de rango; revise el CRS declarado.')
    if area is not None:
        boundary = area.to_crs(4326).geometry.union_all()
        data = data.loc[data.intersects(boundary)].copy()
        data.geometry = data.geometry.intersection(boundary)
        data = data.loc[~data.geometry.is_empty].copy()
    data=data.reset_index(drop=True)
    temporary=cached.with_suffix('.'+uuid.uuid4().hex+'.tmp')
    try:
        data.to_parquet(temporary,index=False);temporary.replace(cached)
        notes_file.write_text(json.dumps(warnings,ensure_ascii=False),encoding='utf8')
    except (ValueError,TypeError,OSError) as exc:
        warnings.append('No se guardó el recorte en caché; la extracción sigue disponible. '+str(exc))
    return data, warnings

def download_drive(url, cache):
    """Public/shared links; private data use Drive Desktop's local mirrored folder."""
    import truststore
    truststore.inject_into_ssl()  # System CA store; certificate verification remains enabled.
    import gdown
    match = re.fullmatch(r'https://drive\.google\.com/drive/folders/([\w-]+)(?:\?[^\s]*)?', url.strip())
    if not match:
        raise ValueError('Use un enlace https://drive.google.com/drive/folders/ID válido.')
    target = Path(cache) / (match.group(1) + '_' + uuid.uuid4().hex[:8])
    target.mkdir(parents=True, exist_ok=False)
    try:
        files = gdown.download_folder(id=match.group(1), output=str(target), quiet=True,
                                      use_cookies=False, skip_download=True)
        if not files:
            raise ValueError('La carpeta está vacía o no permite descargar sus archivos.')
        allowed=VECTOR|{'.shx','.dbf','.prj','.cpg','.sbn','.sbx','.tif','.tiff','.qgz'}
        downloaded=0
        for item in files:
            relative=Path(item.path.replace('\\','/'))
            if any(part.startswith('.') for part in relative.parts) or relative.suffix.lower() not in allowed:
                continue
            path=(target/relative).resolve()
            if target.resolve() not in path.parents:
                raise ValueError('Ruta de archivo de Drive fuera de la carpeta de destino.')
            path.parent.mkdir(parents=True,exist_ok=True)
            if not gdown.download(id=item.id,output=str(path),quiet=True,use_cookies=False):
                raise ValueError(f'Descarga incompleta: {relative}')
            downloaded+=1
        if not downloaded:
            raise ValueError('No hay archivos geográficos compatibles para descargar.')
    except Exception as e:
        raise ValueError('No se pudo descargar Drive. Revise permisos y conexión. Para carpetas privadas, '
                         'use Google Drive para escritorio, marque Disponible sin conexión y seleccione '
                         'esa carpeta en modo local. La descarga parcial no se usará. Detalle: ' + str(e)) from e
    return target
