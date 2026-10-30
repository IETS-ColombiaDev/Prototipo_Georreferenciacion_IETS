"""Country-neutral suggestions: geometry and specific filenames before folders."""
from pathlib import Path
from .catalogue import norm

PATTERNS={
 'escuelas':['education_facilities_points','education_facilities','escuelas','schools'],
 'salud':['vacunacion_pan_pai.shp','ptos_vacuna_eess','healthsites.shp','health_facilities_points','centros_salud','establecimientos_salud','puntosvac2'],
 'vias':['roads_lines','streets.shp','roads.gpkg','vias_pst','red_vial','carreteras','caminos'],
 'rios':['waterways','rios_mayores','rios','rivers'],
 'edificios':['edificiosfull','open_buildings','buildings'],
 'localidades':['cp_p.shp','populated_places','localidades'],
 'sitios':['points_of_interest','sitiosinteres'],
 'aeropuertos':['airports','aeropuertos'],
 'manzanas':['manzanas_catastrales']}

def suggest(entries,role):
 allowed=['line'] if role=='vias' else ['polygon'] if role in ['edificios','manzanas'] else ['point','polygon','line'] if role=='rios' else ['point','polygon']
 candidates=[]
 for i,e in enumerate(entries):
  if e.get('kind')!='vector' or not any(g in e.get('geometry','').lower() for g in allowed):continue
  path=norm(e['path']);name=norm(Path(e['path']).name)
  if any(word in name for word in ['buffer','voronoi','dissolv','_bf_']):continue
  for rank,hint in enumerate(PATTERNS[role]):
   if hint in path:
    exact=0 if Path(name).stem==Path(hint).stem else 1 if name.startswith(hint) else 2 if hint in name else 3
    candidates.append((rank,exact,-e.get('features',0),i));break
 return min(candidates)[3] if candidates else None

def name_field(entry):
 priorities=['nombre','name','nomcp','nombccpp','adm_natn','nom_inst','nombre_cen','nam','id5']
 fields=entry['fields'];lookup={norm(f):f for f in fields}
 return next((lookup[n] for n in priorities if n in lookup),None)

def auto_selections(entries):
 result={}
 for role in PATTERNS:
  idx=suggest(entries,role)
  if idx is not None:result[role]={'entry':entries[idx],'name':name_field(entries[idx]),'complete':False}
 return result


def companions(entries, selection):
    """Only the explicit point/polygon pair in the same directory; no duplicate versions."""
    if not selection:return []
    path=Path(selection['entry']['path'])
    other=path.name.replace('_points.', '_polygons.') if '_points.' in path.name else path.name.replace('_polygons.', '_points.')
    return [e for e in entries if other!=path.name and Path(e['path']).parent==path.parent and Path(e['path']).name==other]


def accessibility_defaults(entries,level):
    """Prefer national accessibility geometry; read_vector clips it to the selected area."""
    from collections import defaultdict
    grouped=defaultdict(list)
    for e in entries:
        if e.get('kind')=='vector' and ('_access' in Path(e['path']).name.lower() or 'accesibilidad' in e['path'].lower()):
            grouped[Path(e['path']).name.lower()].append(e)
    wanted=['adm0','adm1','adm2']
    result=[]
    for candidates in grouped.values():
        def rank(e):
            layer=str(e.get('layer','')).lower()
            return (wanted.index(layer) if layer in wanted else 9,'accesibilidad' not in str(Path(e['path']).parent).lower(),e['path'])
        result.append(min(candidates,key=rank))
    return result


def interest_defaults(entries):
    """Include complementary interest and cultural layers without financial/road datasets."""
    hints=['points_of_interest','cultural_places','parks','parques','plazas','recreation','community']
    return [e for e in entries if e.get('kind')=='vector' and any(h in Path(e['path']).name.lower() for h in hints)]
