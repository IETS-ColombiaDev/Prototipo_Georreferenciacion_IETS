from pathlib import Path
from functools import lru_cache
import gzip,json,unicodedata
import geopandas as gpd
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
def norm(v):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(v)) if not unicodedata.combining(c)).strip().casefold()

def resolve_search(frame,text,selected=None):
    """Never silently replace a requested locality with its parent."""
    text=norm(text)
    if not text:return selected
    exact=frame[frame.ADM_NATN.map(norm).eq(text) | frame.GIS_CODE.map(norm).eq(text)]
    matches=exact if len(exact) else frame[frame.ADM_NATN.map(norm).str.contains(text,regex=False)]
    if selected is not None and selected in matches.GIS_CODE.tolist():return selected
    if len(matches)==1:return str(matches.iloc[0].GIS_CODE)
    raise ValueError('locality_not_found' if matches.empty else 'locality_ambiguous')

def country_options(root=ROOT):
    frame=pd.read_parquet(Path(root)/'data/poblacion/geography.parquet',columns=['country','ADM0_ISON'])
    return dict(sorted(frame.drop_duplicates('country')[['country','ADM0_ISON']].values.tolist(),key=lambda p:p[1]))

@lru_cache(maxsize=12)
def load_geo(root,level,iso):
    root=Path(root)
    folders={'adm0':['adm0'],'adm1':['adm1'],'adm2':['adm2_v03','adm2'],'unit':['report','spatial']}[level]
    for folder in folders:
        for ext in ['.geojson.gz','.geojson']:
            path=root/'geo'/folder/'country'/(iso+ext)
            if not path.exists():continue
            data=json.loads(gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes())
            frame=gpd.GeoDataFrame.from_features(data['features'],crs=4326)
            frame=frame.loc[frame.geometry.notna() & ~frame.geometry.is_empty].copy()
            invalid=~frame.geometry.is_valid
            frame['_geometry_repair']='none'
            if invalid.any():
                # National boundaries may contain dense overlapping rings. Structure
                # repairs the supplied shells/holes without a costly global line network.
                method='structure' if level=='adm0' else 'linework'
                frame.loc[invalid,'geometry']=frame.loc[invalid].geometry.make_valid(method=method)
                frame.loc[invalid,'_geometry_repair']='Shapely make_valid: '+method
            frame['_source']=str(path)
            return frame
    return gpd.GeoDataFrame({'GIS_CODE':[],'ADM_NATN':[]},geometry=[],crs=4326)

def children(frame,parent_code,parent_name=None,level='adm1'):
    if frame.empty or not parent_code:return frame
    code=str(parent_code).split('_',1)[-1]
    field='ADM1_NATC' if level=='adm1' else 'ADM2_NATC'
    if field in frame:
        selected=frame[frame[field].astype(str).eq(code)]
        if len(selected):return selected
    # Source country-qualified code paths are reliable for matching its nested units.
    selected=frame[frame.GIS_CODE.astype(str).str.startswith(str(parent_code))]
    if len(selected):return selected
    # Named parents only within an already country/ADM1-filtered frame, never global fuzzy matching.
    field='ADM1_NATN' if level=='adm1' else 'ADM2_NATN'
    if parent_name and field in frame:
        return frame[frame[field].map(norm).eq(norm(parent_name))]
    return frame.iloc[0:0]

def area_selection(root,iso,adm1=None,adm2=None,unit=None):
    level='unit' if unit else 'adm2' if adm2 else 'adm1' if adm1 else 'adm0'
    code=unit or adm2 or adm1 or iso
    frame=load_geo(str(root),level,iso)
    chosen=frame[frame.GIS_CODE.astype(str).eq(code)].copy()
    if len(chosen)!=1:raise ValueError(f'Boundary not unique: {code}')
    units=load_geo(str(root),'unit',iso)
    for parent,parent_level in [(adm1,'adm1'),(adm2,'adm2')]:
        if parent:
            parents=load_geo(str(root),parent_level,iso)
            matches=parents[parents.GIS_CODE.eq(parent)]
            if len(matches)!=1:raise ValueError(f'Parent boundary not unique: {parent}')
            units=children(units,parent,str(matches.iloc[0].ADM_NATN),level=parent_level)
    if unit:units=units[units.GIS_CODE.eq(unit)]
    if units.empty:units=chosen.copy()
    return chosen,units,level
