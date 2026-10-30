"""Paquetes territoriales en disco: evita comprimir recortes grandes en el navegador."""
from pathlib import Path
from datetime import datetime,timezone
import json,zipfile,uuid,threading,csv,io,copy
ROOT=Path(__file__).resolve().parent
JOBS={}
def encoded(value):return json.dumps(value,ensure_ascii=False,separators=(',',':'))
def geographic(row,f):return all(not f.get(k) or row.get(k)==f[k] for k in ('department','municipality','area'))
def clinical(row,f):
    return all(not f.get(a) or f[a] in row.get(b,[]) or (a!='profile' and 'Todas las ECNT' in row.get(b,[])) for a,b in [('condition','conditions'),('service','services'),('profile','profiles')])
def select_state(state,options):
    f=options.get('filters',{});demo=options.get('showDemo',False);out=dict(state)
    def visible(r):return (demo or not r.get('demo')) and geographic(r,f) and clinical(r,f)
    for key in ('facilities','origins'):out[key]=[r for r in state[key] if visible(r)]
    out['actions']=[r for r in state['actions'] if visible(r)] if options.get('includeActions') else []
    out['evidence']=[r for r in state['evidence'] if clinical(r,f)]
    for key in ('roads','areas','accessibility'):out[key]=[r for r in state[key] if (demo or not r['properties'].get('demo')) and all(not f.get(k) or r['properties'].get(k)==f[k] for k in ('department','municipality'))]
    out['repositoryLayers']=[l for l in state.get('repositoryLayers',[]) if geographic(l,f)]
    out['demoAreas']=[a for a in state.get('demoAreas',[]) if demo and geographic(a,f)]
    ids={r.get('source_id') for key in ('facilities','origins') for r in out[key]}
    ids.update(r['properties'].get('source_id') for key in ('roads','areas','accessibility') for r in out[key])
    ids.update(l['source_id'] for l in out['repositoryLayers']);ids.add('MP5-COL')
    out['sources']=[r for r in state['sources'] if r['id'] in ids]
    return out
def csv_data(rows):
    columns=['id','name','department','municipality','area','lon','lat','status','conditions','services','profiles','source_id']
    stream=io.StringIO();writer=csv.writer(stream);writer.writerow(columns)
    for r in rows:
        row=[]
        for key in columns:
            value=r.get(key,'');numeric=isinstance(value,(int,float));value='|'.join(value) if isinstance(value,list) else str(value)
            if not numeric and value.startswith(('=','+','-','@','\t','\r')):value="'"+value
            row.append(value)
        writer.writerow(row)
    return '\ufeff'+stream.getvalue()
def build(state,options,destination):
    s=select_state(state,options);f=options.get('filters',{});package={'id':'PKG-'+uuid.uuid4().hex,'filters':f,'showDemo':bool(options.get('showDemo')),'generated':datetime.now(timezone.utc).isoformat(),'state':s}
    app=ROOT/'app';read=lambda p:(app/p).read_text('utf8');script=lambda x:'<script>'+x.replace('</script','<\\/script')+'</script>'
    import base64
    logo='data:image/png;base64,'+base64.b64encode((app/'assets/logo.png').read_bytes()).decode()
    # Only one copy of the state is embedded in the standalone page.
    html='<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Consulta territorial · IETS</title><style>'+read('vendor/leaflet.css')+'\n'+read('assets/app.css')+'</style><body><div id="app"></div><div id="toast" role="status"></div><dialog id="dialog"></dialog>'
    for file in ('vendor/leaflet.js','vendor/fflate.js','js/core.js','js/repository-core.js','js/territories.js'):html+=script(read(file))
    html+=script('window.IETS_PACKAGE='+encoded(package).replace('<','\\u003c')+';window.IETS_DEMO=window.IETS_PACKAGE.state;window.IETS_EMBED_LOGO='+encoded(logo)+';')+script(read('js/app.js'))+'</body></html>'
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'x',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        z.writestr('Consulta_territorial.html',html)
        z.writestr('Estado_territorial.json',encoded(s));z.writestr('Fuentes.json',encoded(s['sources']))
        z.writestr('Informe_territorial.html',str(options.get('report') or '<h1>Consulta territorial IETS</h1><p>Consulte el geoportal y Fuentes.json.</p>'))
        for key,title in [('facilities','Sedes'),('origins','Puntos_territoriales')]:z.writestr(title+'.csv',csv_data(s[key]))
        z.writestr('Puntos.geojson',encoded({'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[r['lon'],r['lat']]},'properties':r} for key in ('facilities','origins') for r in s[key]]}))
        for l in s['repositoryLayers']:z.writestr('Capas/'+l['id']+'.geojson',encoded(l['collection']))
        for p in (ROOT/'manuales').glob('*.html'):z.writestr('manuales/'+p.name,p.read_text('utf8').replace('../app/index.html','../Consulta_territorial.html'))
        for p in (app/'vendor').glob('*LICENSE*'):z.write(p,'Licencias/'+p.name)
        z.writestr('LEEME.txt','Extraiga el ZIP completo y abra Consulta_territorial.html en un navegador moderno. La consulta no necesita internet. Para editar bases grandes y cargar nuevas carpetas use el prototipo con INICIAR.bat. Esta copia no se sincroniza. Los datos geográficos no confirman funcionamiento ni servicios clínicos. La población nativa de accesibilidad no fue recalculada para el recorte. Consulte los manuales y fuentes.')
    return {'path':str(destination),'bytes':destination.stat().st_size,'layers':len(s['repositoryLayers']),'facilities':len(s['facilities'])}
def start(store,seed_path,options):
    key=uuid.uuid4().hex;job={'id':key,'status':'working','message':'Preparando el ZIP en disco…'};JOBS[key]=job
    def run():
        try:
            _,s=store.get()
            if s is None:s=json.loads(seed_path.read_text('utf8'))
            scope=str(options.get('filters',{}).get('municipality') or options.get('filters',{}).get('department') or 'Colombia')
            scope=''.join(c for c in scope if c.isalnum())[:30]
            result=build(s,options,ROOT/'salidas'/('IETS_'+scope+'_'+key[:8]+'.zip'))
            job.update(status='complete',message='Paquete listo',result=result,url='/api/export/download/'+key)
        except Exception as exc:job.update(status='failed',message=str(exc))
    threading.Thread(target=run,daemon=True).start();return {'id':key}
