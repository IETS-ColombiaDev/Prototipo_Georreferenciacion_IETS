import unittest,tempfile,sys,hashlib,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import geopandas as gpd
from shapely.geometry import Point,box,mapping,shape
import repositorio as r

class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.folder=Path(self.tmp.name);self.area=gpd.GeoDataFrame(geometry=[box(-76.6,3.4,-76.4,3.6)],crs=4326)
        self.path=self.folder/'health_facilities_points.shp'
        gpd.GeoDataFrame({'name':['Interior','Exterior'],'capacity':[11,22]},geometry=[Point(-76.5,3.5),Point(-74,4)],crs=4326).to_file(self.path)
    def tearDown(self):self.tmp.cleanup()
    def hashes(self):return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.folder.iterdir() if p.is_file()}
    def test_native_inventory_clip_and_source_unchanged(self):
        before=self.hashes();c=r.inspect(str(self.folder));self.assertEqual(len(c['entries']),1);e=c['entries'][0];self.assertEqual(e['category'],'salud')
        result=r.load_layers(c,[{'id':e['id']}],{'department':'76','municipality':'76001','area_geometry':mapping(self.area.geometry.iloc[0])})
        self.assertEqual(result['layers'][0]['featureCount'],1);p=result['layers'][0]['collection']['features'][0]['properties'];self.assertEqual(p['capacity'],11);self.assertEqual(p['_nombre'],'Interior');self.assertEqual(before,self.hashes());self.assertIsNone(result['sources'][0]['cutoff'])
    def test_large_polygon_reader_clips_and_preserves_native_units(self):
        p=self.folder/'COL_hospitals_access.gpkg';gpd.GeoDataFrame({'category':['hospitals'],'range_type':['TIME'],'range':[600],'population':[1000]},geometry=[box(-77,3,-76,4)],crs=4326).to_file(p,layer='adm0')
        before=self.hashes();entry={'path':str(p),'layer':'adm0','crs':'EPSG:4326'};frame,_=r.read_accessibility(entry,self.area)
        self.assertEqual(frame.iloc[0]['range'],600);self.assertEqual(frame.iloc[0]['population'],1000);self.assertTrue(frame.geometry.iloc[0].equals(self.area.geometry.iloc[0]));self.assertEqual(before,self.hashes())
    def test_invalid_selection_rejected(self):
        c=r.inspect(str(self.folder))
        with self.assertRaises(ValueError):r.load_layers(c,[{'id':'missing'}],{})
        eid=c['entries'][0]['id']
        with self.assertRaises(ValueError):r.load_layers(c,[{'id':eid},{'id':eid}],{})
    def test_missing_folder_is_explained(self):
        with self.assertRaisesRegex(ValueError,'carpeta no existe'):r.inspect(str(self.folder/'ausente'))
    def test_packaged_geometries_remain_inside_cali(self):
        s=json.loads((r.ROOT/'datos/ejemplo_cali.json').read_text('utf8'));area=gpd.GeoDataFrame.from_features(s['repository']['boundary']['features'],crs=4326).geometry.union_all().buffer(1e-10)
        for layer in s['repositoryLayers']:
            frame=gpd.GeoDataFrame.from_features(layer['collection']['features'],crs=4326)
            self.assertTrue(frame.geometry.covered_by(area).all(),layer['name'])

if __name__=='__main__':unittest.main(verbosity=2)
