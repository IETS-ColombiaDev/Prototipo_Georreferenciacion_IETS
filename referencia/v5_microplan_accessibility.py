"""Reproducible proximity and road-network estimates, with explicit limits."""
import heapq,math
import pandas as pd
import geopandas as gpd
from shapely import union_all,get_parts
from shapely.geometry import Point,LineString,MultiLineString
from shapely.ops import substring
from shapely.strtree import STRtree

def network_distances(geo,max_snap=500,collect=False):
    schools=geo['layers'].get('escuelas');health=geo['layers'].get('salud');roads=geo['layers'].get('vias')
    if schools is None or health is None or schools.empty or health.empty:return pd.DataFrame()
    if '_servicio_clinico' in health:
        health=health[health['_servicio_clinico'].fillna(False)].copy()
        if health.empty:return pd.DataFrame()
    elif 'amenity' in health:
        # Pharmacies/dentists are not interchangeable with a clinical facility.
        health=health[health.amenity.fillna('').str.lower().isin(['hospital','clinic','doctors','health_post','health_centre'])].copy()
        if health.empty:return pd.DataFrame()
    crs=geo['crs_metric'];a=schools.to_crs(crs);b=health.to_crs(crs)
    features=[]
    def finish():
        result=pd.DataFrame(rows)
        result.attrs['map_features']=features
        return result
    def feature(kind,geometry,row,destination):
        if collect and geometry.length>0:
            features.append({'geometry':geometry,'tipo':kind,'_nombre':str(row['escuela'])+' → '+str(destination),
                'origen':row['escuela'],'destino':destination,'distancia_km':geometry.length/1000,
                'fuente_origen':row['fuente_escuelas'],'fuente_destino':row['fuente_salud'],
                'fuente_vias':row['fuente_vias'],'metodo':{'recta':'Línea recta; no es una ruta transitable',
                'red':'Red no dirigida del recorte; sin tiempos ni verificación de transitabilidad',
                'conexion':'Separación entre punto y vía; no es un camino verificado'}[kind]})
    ap=a.geometry.representative_point();bp=b.geometry.representative_point()
    tree=STRtree(bp.tolist());rows=[]
    for idx,p in enumerate(ap):
        j=int(tree.nearest(p))
        rows.append({'escuela':a.iloc[idx]['_nombre'],'id_escuela':str(a.iloc[idx].get('_fid_fuente',idx)),
            'salud_mas_cercana_recta':b.iloc[j]['_nombre'],'distancia_recta_km':p.distance(bp.iloc[j])/1000,
            'salud_destino_red':None,'distancia_red_km':None,'acceso_fuera_red_m':None,
            'estado_red':'Sin red de vías disponible','metodo':'Puntos representativos; distancias métricas. Sin tiempo de viaje ni asignación sanitaria.',
            'fuente_escuelas':a.iloc[idx].get('_archivo_fuente',geo['sources'].get('escuelas',{}).get('path')),'fuente_salud':b.iloc[j].get('_archivo_fuente',geo['sources'].get('salud',{}).get('path')),
            'fuente_vias':geo['sources'].get('vias',{}).get('path')})
        feature('recta',LineString([p,bp.iloc[j]]),rows[-1],b.iloc[j]['_nombre'])
    if roads is None or roads.empty:return finish()
    projected=roads.to_crs(crs)
    # Avoid false connections at bridges/tunnels by requiring ordinary at-grade roads.
    mask=pd.Series(True,index=projected.index)
    for field in ['bridge','tunnel']:
        if field in projected:mask &= projected[field].fillna('').astype(str).str.lower().isin(['','no','0','0.0','false','f','n','none'])
    if 'layer' in projected:mask &= projected['layer'].fillna('0').astype(str).isin(['','0','0.0'])
    network=union_all(projected.loc[mask].geometry.values)
    segments=[s for s in get_parts(network) if s.geom_type=='LineString' and s.length>0]
    if not segments:return finish()
    stree=STRtree(segments);cuts={i:[] for i in range(len(segments))};snaps={}
    for kind,points in [('school',ap),('health',bp)]:
        for idx,p in enumerate(points):
            edge=int(stree.nearest(p));line=segments[edge];d=line.project(p);on=line.interpolate(d);gap=p.distance(on)
            if gap<=max_snap:cuts[edge].append(d);snaps[(kind,idx)]=(edge,d,gap)
    edges={};graph={};key=lambda p:(round(p.x,3),round(p.y,3))
    for edge,line in enumerate(segments):
        positions=sorted(set([0.0,line.length]+cuts[edge]))
        for left,right in zip(positions,positions[1:]):
            x,y=key(line.interpolate(left)),key(line.interpolate(right));weight=right-left
            graph.setdefault(x,[]).append((y,weight));graph.setdefault(y,[]).append((x,weight))
            if collect:
                piece=substring(line,left,right)
                if (x,y) not in edges or piece.length<edges[(x,y)].length:
                    edges[(x,y)]=piece;edges[(y,x)]=piece
    queue=[];best={};target={};following={}
    for (kind,idx),(edge,d,gap) in snaps.items():
        if kind!='health':continue
        node=key(segments[edge].interpolate(d))
        if gap<best.get(node,math.inf):best[node]=gap;target[node]=idx;following[node]=None;heapq.heappush(queue,(gap,node,idx))
    while queue:
        dist,node,idx=heapq.heappop(queue)
        if dist!=best.get(node):continue
        for nxt,weight in graph.get(node,[]):
            value=dist+weight
            if value<best.get(nxt,math.inf):best[nxt]=value;target[nxt]=idx;following[nxt]=node;heapq.heappush(queue,(value,nxt,idx))
    for idx,row in enumerate(rows):
        snap=snaps.get(('school',idx))
        row['estado_red']='Sin conexión verificable en las vías del recorte'
        if snap:
            edge,d,gap=snap;node=key(segments[edge].interpolate(d))
            if node in best:
                j=target[node];healthgap=snaps[('health',j)][2]
                row.update(salud_destino_red=b.iloc[j]['_nombre'],distancia_red_km=(best[node]-healthgap)/1000,
                    acceso_fuera_red_m=gap+healthgap,estado_red='Estimación geométrica sobre red disponible; revisar acceso',
                    metodo=f'Red no dirigida de vías a nivel; sin puentes/túneles. Conexión a red <= {max_snap} m. Accesos fuera de red separados; sin velocidades ni rutas fluviales.')
                if collect:
                    row['fuente_salud']=b.iloc[j].get('_archivo_fuente',geo['sources'].get('salud',{}).get('path'))
                    pieces=[];cursor=node
                    while following.get(cursor) is not None:
                        nxt=following[cursor];pieces.append(edges[(cursor,nxt)]);cursor=nxt
                    if pieces:feature('red',MultiLineString(pieces),row,b.iloc[j]['_nombre'])
                    feature('conexion',LineString([ap.iloc[idx],segments[edge].interpolate(d)]),row,b.iloc[j]['_nombre'])
                    he,hd,_=snaps[('health',j)]
                    feature('conexion',LineString([segments[he].interpolate(hd),bp.iloc[j]]),row,b.iloc[j]['_nombre'])
    return finish()

def classify_places(geo,iso):
    data=geo['layers'].get('localidades')
    if data is None:return pd.DataFrame()
    rows=[]
    for _,r in data.iterrows():
        value=None;source=None
        # Use explicit source classification when present, never classify a whole
        # district from the fact that its capital is urban.
        for field in ['urbano_rural','area_urbana_rural','AMBITO','ambito','AREA']:
            raw=str(r.get(field,'')).strip().casefold()
            if raw in ['urbano','urbana','rural']:value='Urbano' if raw.startswith('urban') else 'Rural';source=field;break
        if value is None and iso=='PER' and str(r.get('CAPITAL','')).replace('.0','') in ['1','2','3']:
            value='Urbano (capital, criterio censal)';source='CAPITAL: diccionario CP_P; INEI, definición censal de capital de distrito'
        rows.append({'lugar':r['_nombre'],'codigo':r.get('CPINEI',r.get('GIS_CODE')),'ubigeo':r.get('UBIGEO'),
            'clasificacion':value or 'Sin clasificación verificable','evidencia':source or 'No se infiere ruralidad por ausencia de una etiqueta urbana',
            'alcance':'Centro poblado puntual; no clasifica todo el distrito','fuente':geo['sources']['localidades']['path'],
            'referencia': 'https://sdmr.inei.gob.pe/cms/multimedia/home/menuSect-2-23' if iso=='PER' else ''})
    return pd.DataFrame(rows)

def locality_distances(geo,units):
    """Route from a uniquely named settlement point, never an arbitrary centroid."""
    from .catalogue import norm
    places=geo['layers'].get('localidades');origins=[];missing=[]
    for _,unit in units.to_crs(4326).iterrows():
        candidates=None if places is None else places[places.to_crs(4326).intersects(unit.geometry) & places['_nombre'].map(norm).eq(norm(unit.ADM_NATN))]
        if candidates is not None and len(candidates)==1 and candidates.iloc[0].geometry.geom_type=='Point':
            r=candidates.iloc[0].copy();r['codigo']=str(unit.GIS_CODE);origins.append(r)
        else:missing.append({'codigo':str(unit.GIS_CODE),'origen':unit.ADM_NATN,'distancia_red_km':None,'estado_red':'No hay un único punto de localidad con nombre coincidente; no se usa el centroide'})
    rows=[]
    if origins:
        frame=gpd.GeoDataFrame(origins,geometry='geometry',crs=places.crs).reset_index(drop=True)
        clone={**geo,'layers':{**geo['layers'],'escuelas':frame},'sources':{**geo['sources'],'escuelas':geo['sources'].get('localidades',{})}}
        routes=network_distances(clone).rename(columns={'escuela':'origen','id_escuela':'id_origen','fuente_escuelas':'fuente_localidad'})
        if not routes.empty:
            routes['codigo']=frame.codigo.tolist();rows=routes.to_dict('records')
    return pd.DataFrame(rows+missing)

def health_road_access(geo):
    """Nearest-point gap from a health facility to an explicitly major road."""
    health=geo['layers'].get('salud');roads=geo['layers'].get('vias')
    if health is None or roads is None or health.empty or roads.empty:return pd.DataFrame()
    field=next((c for c in ['fclass','highway'] if c in roads),None)
    if field is None:return pd.DataFrame()
    main=roads[roads[field].astype(str).str.lower().isin(['motorway','trunk','primary','secondary','motorway_link','trunk_link','primary_link','secondary_link'])].to_crs(geo['crs_metric'])
    if main.empty:return pd.DataFrame()
    tree=STRtree(main.geometry.tolist());rows=[]
    for _,r in health.to_crs(geo['crs_metric']).iterrows():
        point=r.geometry.representative_point();j=int(tree.nearest(point));road=main.iloc[j]
        rows.append({'salud':r['_nombre'],'via':road.get('_nombre',''),'clase':road[field],'distancia_acceso_m':point.distance(road.geometry),
            'metodo':'Distancia mínima geométrica hasta una vía principal/secundaria; no es recorrido transitable ni tiempo',
            'fuente_salud':geo['sources'].get('salud',{}).get('path'),'fuente_vias':geo['sources'].get('vias',{}).get('path')})
    return pd.DataFrame(rows)


def map_distances(geo,out,lang='es'):
    """Routes for actual settlement, school and supplied coordinate points."""
    from .layers import base_role,label
    from pathlib import Path
    parts=[]
    for role,frame in geo['layers'].items():
        if base_role(role) not in ['escuelas','localidades','geocodificados'] or frame.empty:continue
        part=frame.to_crs(4326).copy()
        part['_archivo_fuente']=part.get('_archivo_fuente',geo['sources'][role]['path'])
        part['_nombre']=label(role,geo,lang)+' · '+part['_nombre'].astype(str)
        parts.append(part)
    if not parts:return
    origins=gpd.GeoDataFrame(pd.concat(parts,ignore_index=True),geometry='geometry',crs=4326)
    clone={**geo,'layers':{**geo['layers'],'escuelas':origins}}
    result=network_distances(clone,collect=True)
    features=result.attrs.pop('map_features',[])
    if result.empty:
        result=pd.DataFrame({'escuela':origins['_nombre'],'estado_red':'Sin establecimientos clínicos utilizables en el área; no se calculan distancias.'})
    result.rename(columns={'escuela':'origen','id_escuela':'id_origen','fuente_escuelas':'fuente_origen'}).to_csv(Path(out)/'distancias_mapa.csv',index=False,encoding='utf-8-sig')
    geo['map_layers']={};geo['map_sources']={}
    for kind in ['recta','red','conexion']:
        records=[f for f in features if f['tipo']==kind]
        frame=gpd.GeoDataFrame(records,geometry='geometry',crs=geo['crs_metric']).to_crs(4326) if records else gpd.GeoDataFrame(geometry=[],crs=4326)
        role='distancias_'+kind
        geo['map_layers'][role]=frame
        geo['map_sources'][role]={'path':'Cálculo con fuentes identificadas en cada elemento',
            'display_label':{'recta':'Distancias en línea recta (no rutas)','red':'Recorridos por vías disponibles','conexion':'Accesos fuera de red (no verificados)'}[kind]}
        if not frame.empty:frame.to_file(Path(out)/(role+'.geojson'),driver='GeoJSON')
