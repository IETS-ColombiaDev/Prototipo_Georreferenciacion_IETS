import math
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from .sources import read_vector
from .layers import base_role

def choose_area(data, index):
    area = data.iloc[[int(index)]].copy()
    if area.empty or not area.geom_type.isin(['Polygon', 'MultiPolygon']).all():
        raise ValueError('Seleccione un límite poligonal válido, no un punto o una línea.')
    if area.geometry.iloc[0].area == 0:
        raise ValueError('El área seleccionada no tiene superficie.')
    return area

def analyze(area, selections):
    crs = area.estimate_utm_crs()
    if crs is None:
        raise ValueError('No se puede determinar una proyección métrica para esta área.')
    projected = area.to_crs(crs)
    result = {'area_km2': float(projected.area.sum() / 1e6), 'crs_metric': str(crs),
              'layers': {}, 'metrics': {}, 'warnings': [], 'sources': {}}
    expected = {'escuelas': {'Point','MultiPoint','Polygon','MultiPolygon'},
                'salud': {'Point','MultiPoint','Polygon','MultiPolygon'},
                'vias': {'LineString','MultiLineString'},
                'rios': {'LineString','MultiLineString','Polygon','MultiPolygon'},
                'edificios': {'Polygon','MultiPolygon'},
                'localidades': {'Point','MultiPoint','Polygon','MultiPolygon'},
                'sitios': {'Point','MultiPoint','Polygon','MultiPolygon'},
                'manzanas': {'Polygon','MultiPolygon'},'aeropuertos':{'Point','MultiPoint','Polygon','MultiPolygon'},
                'geocodificados':{'Point'},'accesibilidad':{'Point','MultiPoint','Polygon','MultiPolygon','LineString','MultiLineString'}}
    expected['sitios'].update({'LineString','MultiLineString'})
    for role, config in selections.items():
        if not config:
            continue
        entry = config['entry']
        try:
            data, notes = read_vector(entry, area)
            result['warnings'].extend(notes)
            rejected=data.attrs.pop('rejected_coordinates',None)
            if rejected is not None:result.setdefault('coordinate_rejections',{})[role]=rejected
            for field,value in config.get('filters',{}).items():
                if field not in data:raise ValueError('Campo de filtro no encontrado: '+field)
                data=data.loc[data[field].astype(str)==str(value)].copy()
            if not data.geom_type.isin(expected[base_role(role)]).all():
                raise ValueError('Tipo geométrico incompatible con el uso seleccionado.')
            # One source per role prevents counting overlapping national/local versions twice.
            before = len(data)
            signatures=data.apply(lambda row: row.geometry.wkb_hex+'|'+json.dumps(
                {k:v for k,v in row.items() if k!='geometry' and not k.startswith('_')},sort_keys=True,default=str),axis=1)
            data = data.loc[~signatures.duplicated()].copy()
            if len(data) != before:
                result['warnings'].append(f'{role}: {before-len(data)} registros idénticos eliminados; establecimientos distintos en el mismo punto se conservan.')
            name = config.get('name')
            if name and name in data.columns:
                data['_nombre'] = data[name].fillna('').astype(str)
            else:
                data['_nombre'] = ''
            missing = data['_nombre'].str.strip().eq('')
            data.loc[missing, '_nombre'] = [f'Sin nombre · registro {i+1}' for i in data.index[missing]]
            if missing.any():
                result['warnings'].append(f'{role}: {int(missing.sum())} registros sin nombre en la fuente.')
            data['_archivo_fuente']=data.get('_archivo_fuente',entry['path'])
            if base_role(role)=='salud':
                fields={str(c).lower() for c in data.columns}
                if {'edad','numero_dos','residencia'}.issubset(fields):
                    raise ValueError('Registros de dosis/residencia: no son ubicaciones verificadas de establecimientos de salud.')
                data['_servicio_clinico']=data['amenity'].fillna('').str.lower().isin(['hospital','clinic','doctors','health_post','health_centre']) if 'amenity' in data else True
            result['layers'][role] = data
            result['sources'][role] = {**entry, 'name_field':name,
                'coverage_confirmed':bool(config.get('complete',False)),
                'display_label':config.get('label'), 'filters':config.get('filters',{})}
            if base_role(role)=='accesibilidad':
                data['_alcance_atributos']='Atributos originales del territorio de la fuente; no recalculados para el recorte ni sumables entre rangos.'
                result['warnings'].append(f'{role}: accesibilidad de la fuente; no sumar rangos acumulados ni trasladar su población al recorte.')
            result['metrics'][role + '_registros'] = len(data)
            if role in ['edificios','manzanas']:
                points=gpd.GeoSeries(gpd.points_from_xy(data['_punto_conteo_lon'],data['_punto_conteo_lat']),index=data.index,crs=4326)
                data['_contado_en_area']=points.intersects(area.to_crs(4326).geometry.union_all())
                result['metrics'][role+'_contados']=int(data['_contado_en_area'].sum())
            if role == 'vias':
                result['metrics']['vias_km'] = float(data.to_crs(crs).geometry.union_all().length / 1000)
            if not config.get('complete'):
                result['warnings'].append(f'{role}: cobertura no confirmada; los conteos son registros disponibles, no totales oficiales.')
        except Exception as e:
            result['warnings'].append(f'{role}: datos no disponibles. {e}')
    # Merge selected institutional sources for matrices and routing, keeping row provenance.
    for category in ['salud','escuelas']:
        roles=[r for r in result['layers'] if base_role(r)==category]
        if len(roles)<2:continue
        pieces=[result['layers'][r].to_crs(4326) for r in roles]
        combined=gpd.GeoDataFrame(pd.concat(pieces,ignore_index=True),geometry='geometry',crs=4326)
        # Same source record selected twice is removed; separate sources remain auditable.
        combined=combined.drop_duplicates(subset=['_archivo_fuente','_fid_fuente']) if '_fid_fuente' in combined else combined
        originals=[result['sources'][r] for r in roles]
        for r in roles:
            result['layers'].pop(r);result['sources'].pop(r);result['metrics'].pop(r+'_registros',None)
        result['layers'][category]=combined
        result['sources'][category]={'path':' | '.join(x['path'] for x in originals),'layer':'combined',
            'components':originals,'coverage_confirmed':False,'display_label':None}
        result['metrics'][category+'_registros']=len(combined)
    from .semantics import normalize_geo
    result=normalize_geo(result)
    for role in ['escuelas', 'salud', 'vias', 'localidades']:
        if role not in result['layers']:
            result['warnings'].append(f'Falta capa utilizable de {role}. No se sustituye por cero.')
    schools, health = result['layers'].get('escuelas'), result['layers'].get('salud')
    if schools is not None and health is not None and len(schools) and len(health):
        a, b = schools.to_crs(crs).copy(), health.to_crs(crs).copy()
        a.geometry = a.geometry.representative_point()
        b.geometry = b.geometry.representative_point()
        nearest = gpd.sjoin_nearest(a[['_nombre','geometry']], b[['_nombre','geometry']],
                                  how='left', distance_col='distancia_m')
        nearest = nearest.loc[~nearest.index.duplicated()].copy()
        result['distances'] = nearest.drop(columns=['geometry','index_right']).rename(
            columns={'_nombre_left':'escuela','_nombre_right':'salud_mas_cercana_en_area'})
        result['warnings'].append('Distancias euclidianas entre puntos representativos y centros dentro del área: '
            'no son rutas, tiempos de viaje ni asignaciones sanitarias; no se copian a las columnas de recorrido.')
    return result

def raster_summary(path, area, semantics='descriptivo'):
    import rasterio
    from rasterio.mask import mask
    from rasterio.features import geometry_mask
    from rasterio.features import geometry_window
    from shapely.geometry import box
    with rasterio.open(path) as src:
        if not src.crs:
            raise ValueError('El ráster no tiene CRS.')
        if src.count != 1:
            raise ValueError('Seleccione un ráster de una sola banda.')
        shapes = [g.__geo_interface__ for g in area.to_crs(src.crs).geometry]
        window=geometry_window(src,shapes)
        if window.width*window.height>25_000_000:
            raise ValueError('El recorte supera 25 millones de píxeles. Seleccione un área menor o un ráster de menor resolución.')
        polygon=area.to_crs(src.crs).geometry.union_all()
        area_coverage=polygon.intersection(box(*src.bounds)).area/polygon.area
        image, transform = mask(src, shapes, crop=True, filled=False, all_touched=False)
        inside = geometry_mask(shapes, image.shape[1:], transform, invert=True)
        raw = image[0]
        valid = inside & ~np.ma.getmaskarray(raw) & np.isfinite(raw.data)
        count = int(valid.sum())
        denominator = int(inside.sum())
        if count == 0:
            raise ValueError('No hay píxeles válidos dentro del área.')
        values = raw.data[valid].astype(float) * src.scales[0] + src.offsets[0]
        result = {'source': str(path), 'semantics': semantics, 'valid_pixels':count,
                  'coverage_of_crop':float(count/max(denominator,1)), 'area_coverage':float(area_coverage),
                  'min':float(values.min()), 'max':float(values.max()), 'mean':float(values.mean()),
                  'method':'Centros de píxel dentro del polígono; sin reparto fraccional de celdas de borde.'}
        if semantics == 'personas_por_pixel':
            if (values < 0).any():
                raise ValueError('Población negativa: verifique NoData y unidades.')
            result['population_estimate'] = float(values.sum())
        return result
