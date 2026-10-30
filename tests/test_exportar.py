import sys,json,tempfile,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import exportar as ex

class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.state=json.loads((ex.ROOT/'datos/ejemplo_cali.json').read_text('utf8'))
    def test_geographic_filter_does_not_label_cali_as_other_municipality(self):
        s=ex.select_state(self.state,{'filters':{'department':'76','municipality':'76520'}})
        self.assertEqual(s['repositoryLayers'],[]);self.assertEqual(s['facilities'],[])
    def test_clinical_filter_does_not_invent_services(self):
        s=ex.select_state(self.state,{'filters':{'municipality':'76001','condition':'Diabetes'}})
        self.assertEqual(s['facilities'],[]);self.assertEqual(len(s['repositoryLayers']),12)
    def test_actions_require_explicit_inclusion(self):
        s=dict(self.state);s['actions']=[{'id':'test','municipality':'76001','demo':False}]
        self.assertEqual(ex.select_state(s,{'filters':{}})['actions'],[])
        self.assertEqual(len(ex.select_state(s,{'filters':{},'includeActions':True})['actions']),1)
    def test_full_real_package_contains_native_layers_sources_and_one_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'cali.zip';result=ex.build(self.state,{'filters':{'department':'76','municipality':'76001'},'report':'<h1>Prueba de exportación</h1>'},dest)
            self.assertEqual(result['facilities'],1091)
            with zipfile.ZipFile(dest) as z:
                self.assertIsNone(z.testzip());s=json.loads(z.read('Estado_territorial.json'));html=z.read('Consulta_territorial.html').decode()
                self.assertEqual(len([n for n in z.namelist() if n.startswith('Capas/')]),12)
                self.assertEqual(len(s['repositoryLayers']),12);self.assertEqual(s['actions'],[])
                self.assertIn('window.IETS_DEMO=window.IETS_PACKAGE.state;',html)
                for layer in s['repositoryLayers']:self.assertTrue(any(source['id']==layer['source_id'] for source in s['sources']))
                self.assertEqual(len([n for n in z.namelist() if n.startswith('manuales/')]),4)

if __name__=='__main__':unittest.main(verbosity=2)
