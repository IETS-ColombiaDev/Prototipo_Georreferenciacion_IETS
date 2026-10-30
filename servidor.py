"""Servidor local IETS. HTTP y SQLite estándar; lectura geográfica con el entorno indicado en requirements.txt."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit, unquote
import argparse, json, sqlite3, secrets, mimetypes, webbrowser, threading, sys
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parent
MAX_BODY = 120 * 1024 * 1024
ARRAYS = ('facilities','origins','areas','roads','accessibility','sources','evidence','actions')

def validate_state(value):
    if not isinstance(value,dict) or value.get('schema') != 1:
        raise ValueError('Esquema incompatible: se requiere schema 1.')
    if any(not isinstance(value.get(k),list) for k in ARRAYS):
        raise ValueError('La base debe contener todas las colecciones.')
    for k in ARRAYS:
        if len(value[k])>100000 or any(not isinstance(r,dict) for r in value[k]):
            raise ValueError('Colección inválida o excesiva: '+k)
    return value

class Store:
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS current_state (id INTEGER PRIMARY KEY CHECK(id=1), revision INTEGER NOT NULL, payload TEXT NOT NULL)')
            conn.execute('CREATE TABLE IF NOT EXISTS history (revision INTEGER PRIMARY KEY, saved_at TEXT DEFAULT CURRENT_TIMESTAMP, payload TEXT NOT NULL)')
    @contextmanager
    def connect(self):
        conn=sqlite3.connect(self.path,timeout=10)
        try:
            with conn:yield conn
        finally:conn.close()
    def get(self):
        with self.connect() as conn:
            row=conn.execute('SELECT revision,payload FROM current_state WHERE id=1').fetchone()
        return (row[0],json.loads(row[1])) if row else (0,None)
    def put(self,state,expected):
        validate_state(state); payload=json.dumps(state,ensure_ascii=False,allow_nan=False,separators=(',',':'))
        with self.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            row=conn.execute('SELECT revision,payload FROM current_state WHERE id=1').fetchone()
            revision=row[0] if row else 0
            if revision != expected:raise RuntimeError('La base cambió en otra pestaña. Recargue la página antes de guardar para evitar sobrescribir cambios.')
            if row:conn.execute('INSERT OR REPLACE INTO history(revision,payload) VALUES (?,?)',row)
            revision+=1
            conn.execute('INSERT OR REPLACE INTO current_state VALUES (1,?,?)',(revision,payload))
            conn.execute('DELETE FROM history WHERE revision NOT IN (SELECT revision FROM history ORDER BY revision DESC LIMIT 20)')
        return revision

class Handler(BaseHTTPRequestHandler):
    server_version='IETSLocal/1.0'
    def log_message(self,format,*args):
        if args and (' 4' in str(args) or ' 5' in str(args)):super().log_message(format,*args)
    def trusted(self):
        host=self.headers.get('Host','')
        valid={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
        origin=self.headers.get('Origin')
        return host in valid and (not origin or origin in {'http://'+x for x in valid})
    def send_json(self,status,value):
        data=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
    def reject_write(self,message):
        # Drain small rejected requests before closing HTTP/1.0; unread bytes can cause TCP resets on Windows.
        try:length=int(self.headers.get('Content-Length','0'))
        except ValueError:length=0
        if 0<length<=1024*1024:self.rfile.read(length)
        return self.send_json(403,{'error':message})
    def do_GET(self):
        if not self.trusted():return self.send_json(403,{'error':'Solo se aceptan consultas desde el equipo local.'})
        path=unquote(urlsplit(self.path).path)
        if path=='/api/session':
            rev,state=self.server.store.get()
            if state is None and self.server.seed_path and self.server.seed_path.is_file():state=json.loads(self.server.seed_path.read_text('utf-8'))
            return self.send_json(200,{'application':'IETS-local','token':self.server.token,'revision':rev,'state':state})
        if path.startswith('/api/repository/job/'):
            from repositorio import job_state
            try:return self.send_json(200,job_state(path.rsplit('/',1)[-1]))
            except ValueError as exc:return self.send_json(404,{'error':str(exc)})
        if path.startswith('/api/export/'):
            from exportar import JOBS
            job=JOBS.get(path.rsplit('/',1)[-1])
            if not job:return self.send_json(404,{'error':'Exportación no encontrada.'})
            if path.startswith('/api/export/job/'):return self.send_json(200,job)
            if path.startswith('/api/export/download/') and job['status']=='complete':
                import shutil
                target=Path(job['result']['path']);self.send_response(200);self.send_header('Content-Type','application/zip');self.send_header('Content-Length',str(target.stat().st_size));self.send_header('Content-Disposition','attachment; filename="'+target.name+'"');self.end_headers()
                with target.open('rb') as source:shutil.copyfileobj(source,self.wfile,1024*1024)
                return
            return self.send_json(409,{'error':'La exportación todavía no está lista.'})
        if path.startswith('/api/'):return self.send_json(404,{'error':'Ruta no disponible.'})
        base=ROOT/'manuales' if path.startswith('/manuales/') else ROOT/'app'
        relative=path[len('/manuales/'):] if path.startswith('/manuales/') else path[len('/app/'):] if path.startswith('/app/') else path.lstrip('/')
        if not relative:relative='index.html'
        target=(base/relative).resolve()
        if not target.is_relative_to(base.resolve()) or not target.is_file() or target.suffix.lower() not in {'.html','.css','.js','.png','.jpg','.jpeg','.svg','.txt','.json','.geojson','.csv','.md'}:
            return self.send_json(404,{'error':'Archivo no disponible.'})
        data=target.read_bytes();content=mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
        self.send_response(200);self.send_header('Content-Type',content+('; charset=utf-8' if content.startswith('text/') or target.suffix in ('.js','.json') else ''));self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-cache');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self' data: blob:; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'");self.end_headers();self.wfile.write(data)
    def do_PUT(self):
        if not self.trusted() or not secrets.compare_digest(self.headers.get('X-IETS-Token',''),self.server.token):return self.reject_write('Solicitud local no autorizada. Recargue la aplicación.')
        if urlsplit(self.path).path!='/api/state':return self.send_json(404,{'error':'Ruta no disponible.'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<=0 or length>MAX_BODY:return self.send_json(413,{'error':'La base supera el límite de 120 MB.'})
            expected=int(self.headers.get('If-Match','-1'))
            state=json.loads(self.rfile.read(length).decode('utf-8'),parse_constant=lambda x:(_ for _ in ()).throw(ValueError('Número no finito')))
            rev=self.server.store.put(state,expected);return self.send_json(200,{'revision':rev})
        except RuntimeError as err:return self.send_json(409,{'error':str(err)})
        except (ValueError,TypeError,UnicodeError) as err:return self.send_json(400,{'error':str(err)})
        except (sqlite3.Error,OSError):return self.send_json(500,{'error':'No fue posible guardar en disco. Revise espacio y permisos; conserve un respaldo.'})
    def do_POST(self):
        if not self.trusted() or not secrets.compare_digest(self.headers.get('X-IETS-Token',''),self.server.token):return self.reject_write('Recargue la aplicación para activar el acceso local.')
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<=0 or length>10*1024*1024:return self.send_json(413,{'error':'Solicitud demasiado grande.'})
            body=json.loads(self.rfile.read(length).decode('utf-8'))
            from repositorio import start_job,folders
            path=urlsplit(self.path).path
            if path=='/api/export':
                from exportar import start
                return self.send_json(202,start(self.server.store,self.server.seed_path,body))
            if path=='/api/repository/inspect':return self.send_json(202,start_job('inspect',body))
            if path=='/api/repository/load':return self.send_json(202,start_job('load',body))
            if path=='/api/repository/folders':return self.send_json(200,folders(body.get('path')))
            return self.send_json(404,{'error':'Ruta no disponible.'})
        except (ValueError,OSError,ImportError) as exc:return self.send_json(400,{'error':str(exc)})

def create_server(port=8516,db=None,seed_path=ROOT/'datos/ejemplo_cali.json'):
    httpd=ThreadingHTTPServer(('127.0.0.1',port),Handler);httpd.token=secrets.token_urlsafe(32);httpd.store=Store(db or ROOT/'datos/observatorio.sqlite');httpd.seed_path=seed_path;return httpd

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Prototipo local del Observatorio IETS')
    parser.add_argument('--port',type=int,default=8516);parser.add_argument('--open',action='store_true');parser.add_argument('--db',type=Path)
    args=parser.parse_args()
    try:httpd=create_server(args.port,args.db)
    except OSError as err:
        print('No se pudo iniciar. El puerto puede estar ocupado. Use --port 8517 o cierre la instancia previa.\n'+str(err));sys.exit(1)
    url=f'http://127.0.0.1:{httpd.server_port}'
    print('Observatorio IETS - Georreferenciacion para la accion\n'+url+'\nSolo este equipo. Cierre con Ctrl+C.',flush=True)
    if args.open:threading.Timer(.6,lambda:webbrowser.open(url)).start()
    try:httpd.serve_forever()
    except KeyboardInterrupt:pass
    finally:httpd.server_close()
