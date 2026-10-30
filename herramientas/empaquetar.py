"""Actualiza el generador autónomo y comprueba el inventario. Python estándar."""
from pathlib import Path
import json, base64, hashlib
ROOT=Path(__file__).resolve().parents[1]
app=ROOT/'app'
mapping={'leafletCss':'vendor/leaflet.css','leafletJs':'vendor/leaflet.js','fflate':'vendor/fflate.js','core':'js/core.js','repositoryCore':'js/repository-core.js','app':'js/app.js','css':'assets/app.css','leafletLicense':'vendor/LEAFLET_LICENSE.txt','fflateLicense':'vendor/FFLATE_LICENSE.txt'}
b={k:(app/v).read_text('utf-8') for k,v in mapping.items()}
b['logo']='data:image/png;base64,'+base64.b64encode((app/'assets/logo.png').read_bytes()).decode('ascii')
b['manuals']={p.name:p.read_text('utf-8') for p in (ROOT/'manuales').glob('*.html')}
(app/'js/bundle.js').write_text('window.IETS_BUNDLE='+json.dumps(b,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+';','utf-8')
inventory={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.rglob('*') if p.is_file() and not any(x in p.parts for x in ['datos','qa','salidas','__pycache__','.venv','cache']) and p.name!='INVENTARIO_SHA256.json'}
(ROOT/'referencia/INVENTARIO_SHA256.json').write_text(json.dumps(inventory,indent=2,ensure_ascii=False),'utf-8')
print('Generador actualizado. Archivos inventariados:',len(inventory))
