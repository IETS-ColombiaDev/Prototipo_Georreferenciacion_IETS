import unittest,tempfile,sys,json,threading,urllib.request,urllib.error
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from servidor import Store,create_server,ARRAYS

def fixture():return {'schema':1,**{k:[] for k in ARRAYS}}
class StorageTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.store=Store(Path(self.tmp.name)/'test.sqlite')
    def tearDown(self):self.tmp.cleanup()
    def test_atomic_save_read(self):self.assertEqual(self.store.put(fixture(),0),1);self.assertEqual(self.store.get(),(1,fixture()))
    def test_conflict_preserves_previous(self):
        self.store.put(fixture(),0)
        with self.assertRaises(RuntimeError):self.store.put(fixture(),0)
        self.assertEqual(self.store.get()[0],1)
    def test_bad_schema_preserves_previous(self):
        self.store.put(fixture(),0)
        with self.assertRaises(ValueError):self.store.put({'schema':0},1)
        self.assertEqual(self.store.get()[0],1)
    def test_history_retains_twenty(self):
        for i in range(25):self.store.put(fixture(),i)
        with self.store.connect() as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM history').fetchone()[0],20)

class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.server=create_server(0,Path(cls.tmp.name)/'api.sqlite',seed_path=None);cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.base='http://127.0.0.1:'+str(cls.server.server_port)
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.tmp.cleanup()
    def request(self,path='/',method='GET',headers=None,body=None):
        req=urllib.request.Request(self.base+path,method=method,headers=headers or {},data=json.dumps(body).encode() if body else None)
        try:
            with urllib.request.urlopen(req) as r:return r.status,r.read(),r.headers
        except urllib.error.HTTPError as r:return r.code,r.read(),r.headers
    def test_index_and_content_policy(self):
        code,body,headers=self.request();self.assertEqual(code,200);self.assertIn(b'Observatorio',body);self.assertIn("connect-src 'self'",headers['Content-Security-Policy'])
    def test_database_not_served(self):self.assertEqual(self.request('/datos/observatorio.sqlite')[0],404)
    def test_path_escape_not_served(self):self.assertEqual(self.request('/%2e%2e/servidor.py')[0],404)
    def test_external_origin_rejected(self):self.assertEqual(self.request(headers={'Origin':'https://example.org'})[0],403)
    def test_spoofed_host_rejected(self):self.assertEqual(self.request(headers={'Host':'other.example'})[0],403)
    def test_save_requires_token(self):self.assertEqual(self.request('/api/state','PUT',body=fixture())[0],403)
    def test_session_and_revision_save(self):
        code,body,_=self.request('/api/session');self.assertEqual(code,200);session=json.loads(body)
        headers={'Content-Type':'application/json','X-IETS-Token':session['token'],'If-Match':str(session['revision'])}
        self.assertEqual(self.request('/api/state','PUT',headers,fixture())[0],200)
        self.assertEqual(self.request('/api/state','PUT',headers,fixture())[0],409)

if __name__=='__main__':unittest.main(verbosity=2)
