"""Preparación reproducible desde los insumos locales autorizados. No modifica las fuentes."""
from pathlib import Path
from zipfile import ZipFile
import gzip, json, hashlib, math, shutil, sys

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(sys.argv[1])
def compact(o): return json.dumps(o, ensure_ascii=False, separators=(',', ':'))
def dp(points, eps):
    if len(points) < 4: return points
    a,b = points[0],points[-1]; dx,dy=b[0]-a[0],b[1]-a[1]; d=dx*dx+dy*dy
    top,idx=0,0
    for i,p in enumerate(points[1:-1],1):
        t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/d)) if d else 0
        dis=(p[0]-a[0]-t*dx)**2+(p[1]-a[1]-t*dy)**2
        if dis>top: top,idx=dis,i
    if top>eps*eps: return dp(points[:idx+1],eps)[:-1]+dp(points[idx:],eps)
    return [a,b]
def ring(r):
    # Split closed ring into two open chains; preserve closure and minimum vertices.
    half=len(r)//2
    s=dp(r[:half+1],0.00035)[:-1]+dp(r[half:],0.00035)
    if len(s)<4:s=r
    return [[round(x,5),round(y,5)] for x,y,*_ in s]
manifest=[]
with ZipFile(BASE/'Microplanificacion_v5.zip') as z:
    def read(name):
        full='microplanificacion_v5/'+name; b=z.read(full)
        manifest.append({'archivo_origen':full,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
        return b
    for f in ['leaflet.js','leaflet.css','LEAFLET_LICENSE.txt','fflate.js','FFLATE_LICENSE.txt']:
        (ROOT/'app/vendor'/f).write_bytes(read('vendor/'+f))
    catalog={}
    for level,folder in [('departments','adm1'),('municipalities','adm2_v03')]:
        b=read(f'geo/{folder}/country/COL.geojson.gz')
        (ROOT/'referencia'/f'COL_{folder}.geojson.gz').write_bytes(b)
        data=json.loads(gzip.decompress(b))
        for f in data['features']:
            p=f['properties'];g=f['geometry'];code=p.get('ADM2_NATC') if level=='municipalities' else p.get('ADM1_NATC')
            f['properties']={'id':code,'name':p['ADM_NATN'],'department':p['ADM1_NATC'],'source':'MP5-COL','cutoff':None}
            if g['type']=='Polygon':g['coordinates']=[ring(r) for r in g['coordinates']]
            elif g['type']=='MultiPolygon':g['coordinates']=[[ring(r) for r in poly] for poly in g['coordinates']]
        catalog[level]=data
    for file in ['README.md','requirements.txt','microplan/accessibility.py','microplan/catalogue.py','microplan/geo.py','microplan/coordinates.py']:
        (ROOT/'referencia'/('v5_'+file.replace('/','_'))).write_bytes(read(file))
    (ROOT/'referencia/FUENTES_SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8')
for p in (BASE/'assets').iterdir():
    if p.suffix in ['.png','.svg']:shutil.copyfile(p,ROOT/'app/assets'/p.name)
(ROOT/'app/js/territories.js').write_text('window.IETS_TERRITORIES='+compact(catalog)+';','utf-8')
print('Catálogo preparado:', {k:len(v['features']) for k,v in catalog.items()})
