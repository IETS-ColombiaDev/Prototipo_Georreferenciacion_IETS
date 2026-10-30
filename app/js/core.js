/* Georreferenciación para la acción · motor independiente de la interfaz. */
(function(root,factory){const api=factory();if(typeof module==='object')module.exports=api;else root.IETS=api;})(typeof window!=='undefined'?window:globalThis,function(){
  'use strict';
  const VERSION='1.0.0', CONDITIONS=['Diabetes','Hipertensión','Cáncer','Todas las ECNT'];
  const SERVICES=['Seguimiento ambulatorio','Medicamentos','Oncología','Laboratorio','Rehabilitación'];
  const PROFILES=['Coordinación territorial','Medicina','Enfermería','Farmacia','Gestión de servicios'];
  const STATUS=['Operativa','Capacidad limitada','No operativa','Sin verificar'];
  const ACTION_STATUS=['Pendiente','En curso','Bloqueada','Cerrada'];
  const norm=v=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const clone=v=>JSON.parse(JSON.stringify(v));
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const id=prefix=>prefix+'-'+(globalThis.crypto?.randomUUID?.()||Date.now()+'-'+Math.random().toString(36).slice(2));
  const today=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/Bogota',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  const dateValid=x=>/^\d{4}-\d{2}-\d{2}$/.test(x||'')&&!isNaN(Date.parse(x))&&new Date(x).toISOString().slice(0,10)===x;
  const lists=v=>Array.isArray(v)?v:String(v??'').split('|').map(s=>s.trim()).filter(Boolean);
  const has=(items,value)=>!value||lists(items).includes(value)||lists(items).includes('Todas las ECNT');
  function matches(r,f){return (!f.department||r.department===f.department)&&(!f.municipality||r.municipality===f.municipality)&&(!f.area||r.area===f.area)&&has(r.conditions,f.condition)&&has(r.services,f.service)&&(!f.profile||lists(r.profiles).includes(f.profile));}
  function inRing(point,ring){
    let inside=false; const [x,y]=point;
    for(let i=0,j=ring.length-1;i<ring.length;j=i++){
      const [xi,yi]=ring[i],[xj,yj]=ring[j];
      const cross=(x-xi)*(yj-yi)-(y-yi)*(xj-xi);
      if(Math.abs(cross)<1e-10&&x>=Math.min(xi,xj)&&x<=Math.max(xi,xj)&&y>=Math.min(yi,yj)&&y<=Math.max(yi,yj))return true;
      if(((yi>y)!==(yj>y))&&x<(xj-xi)*(y-yi)/(yj-yi)+xi)inside=!inside;
    }return inside;
  }
  function inGeometry(p,g){if(!g)return false;const poly=r=>inRing(p,r[0])&&!r.slice(1).some(h=>inRing(p,h));return g.type==='Polygon'?poly(g.coordinates):g.type==='MultiPolygon'?g.coordinates.some(poly):false;}
  function haversine(a,b){const rad=Math.PI/180;const dlat=(b[1]-a[1])*rad,dlon=(b[0]-a[0])*rad;const h=Math.sin(dlat/2)**2+Math.cos(a[1]*rad)*Math.cos(b[1]*rad)*Math.sin(dlon/2)**2;return 6371.0088*2*Math.asin(Math.min(1,Math.sqrt(h)));}
  const coord=r=>[Number(r.lon),Number(r.lat)];
  function csvParse(text){
    text=text.replace(/^\uFEFF/,'');const first=text.split(/\r?\n/)[0];const delimiter=(first.match(/;/g)||[]).length>(first.match(/,/g)||[]).length?';':',';
    let rows=[],row=[],cell='',quote=false;
    for(let i=0;i<text.length;i++){
      const ch=text[i];if(ch==='"'){if(quote&&text[i+1]==='"'){cell+='"';i++;}else if(quote||cell==='')quote=!quote;else throw Error('Comillas mal ubicadas en CSV.');}
      else if(ch===delimiter&&!quote){row.push(cell);cell='';}
      else if((ch==='\n'||ch==='\r')&&!quote){if(ch==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(x=>x.trim()))rows.push(row);row=[];cell='';}else cell+=ch;
    }
    if(quote)throw Error('Hay un campo CSV con comillas sin cerrar.');
    row.push(cell);if(row.some(x=>x.trim()))rows.push(row);
    if(rows.length<2)throw Error('El CSV debe tener encabezados y al menos una fila.');
    const headers=rows.shift().map(x=>x.trim());if(new Set(headers).size!==headers.length)throw Error('Hay encabezados duplicados.');
    return rows.map((r,i)=>{if(r.length!==headers.length)throw Error('Fila '+(i+2)+': número de columnas diferente al encabezado.');return Object.fromEntries(headers.map((h,j)=>[h,r[j].trim()]));});
  }
  function csv(rows,columns){const cols=columns||[...new Set(rows.flatMap(r=>Object.keys(r)))];const value=v=>{let s=Array.isArray(v)?v.join('|'):typeof v==='object'&&v!==null?JSON.stringify(v):String(v??'');if(/^[=+@\-\t\r]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';};return '\uFEFF'+[cols.map(value).join(','),...rows.map(r=>cols.map(c=>value(r[c])).join(','))].join('\r\n');}
  function pointFeatures(rows){return {type:'FeatureCollection',features:rows.map(r=>({type:'Feature',geometry:{type:'Point',coordinates:coord(r)},properties:clone(r)}))};}
  function ranking(origins,weights){
    const keys=['gap','barrier','disruption'];const sum=keys.reduce((a,k)=>a+Number(weights[k]),0);
    if(!Number.isFinite(sum)||sum<=0||keys.some(k=>!Number.isFinite(+weights[k])||+weights[k]<0))throw Error('Asigne al menos un peso positivo; los pesos no pueden ser negativos.');
    return origins.map(r=>({...r,score:keys.every(k=>r[k]!==null&&r[k]!==''&&r[k]!==undefined&&Number.isFinite(+r[k])&&+r[k]>=0&&+r[k]<=100)?keys.reduce((a,k)=>a+Number(r[k])*weights[k],0)/sum:null})).sort((a,b)=>(b.score??-1)-(a.score??-1)||a.id.localeCompare(b.id));
  }
  function nearest(origin,facilities){return facilities.filter(f=>f.status==='Operativa'||f.status==='Capacidad limitada').map(f=>({...f,distance:haversine(coord(origin),coord(f))})).sort((a,b)=>a.distance-b.distance);}
  function networkRoute(origin,destinations,roads,maxSnapM=500){
    // Port conceptual del antecedente v5: Dijkstra, red no dirigida, conexiones separadas.
    // Aquí se conectan solamente vértices compartidos; no se infieren cruces ni transitabilidad.
    const graph=new Map(),positions=new Map();const key=p=>p.map(n=>Number(n).toFixed(6)).join(',');
    function edge(a,b){const ka=key(a),kb=key(b);if(ka===kb)return;positions.set(ka,a);positions.set(kb,b);if(!graph.has(ka))graph.set(ka,[]);if(!graph.has(kb))graph.set(kb,[]);const d=haversine(a,b);graph.get(ka).push([kb,d]);graph.get(kb).push([ka,d]);}
    for(const f of roads){const p=f.properties||{};if((p.bridge&&!['no','0','false'].includes(norm(p.bridge)))||(p.tunnel&&!['no','0','false'].includes(norm(p.tunnel)))||(p.layer&&Number(p.layer)!==0))continue;const lines=f.geometry.type==='MultiLineString'?f.geometry.coordinates:f.geometry.type==='LineString'?[f.geometry.coordinates]:[];for(const line of lines)for(let i=1;i<line.length;i++)edge(line[i-1],line[i]);}
    if(!graph.size)return {status:'Sin red compatible'};
    const snap=p=>{let found=null;for(const [k,pos] of positions){const d=haversine(p,pos);if(d*1000<=maxSnapM&&(!found||d<found.gap))found={key:k,gap:d};}return found;};
    const start=snap(coord(origin));if(!start)return {status:'Origen a más de '+maxSnapM+' m de los vértices de la red'};
    const goals=destinations.filter(f=>['Operativa','Capacidad limitada'].includes(f.status)).map(f=>({facility:f,snap:snap(coord(f))})).filter(x=>x.snap);
    if(!goals.length)return {status:'Sin destinos funcionales conectados'};
    // Min-heap to retain reasonable performance for supplied local networks.
    const heap=[];const push=x=>{heap.push(x);let i=heap.length-1;while(i){const p=(i-1)>>1;if(heap[p][0]<=x[0])break;heap[i]=heap[p];i=p;}heap[i]=x;};
    const pop=()=>{const out=heap[0],last=heap.pop();if(heap.length){let i=0;while(i*2+1<heap.length){let c=i*2+1;if(c+1<heap.length&&heap[c+1][0]<heap[c][0])c++;if(heap[c][0]>=last[0])break;heap[i]=heap[c];i=c;}heap[i]=last;}return out;};
    const best=new Map([[start.key,0]]),previous=new Map();push([0,start.key]);
    while(heap.length){const [dist,k]=pop();if(dist!==best.get(k))continue;for(const [n,w] of graph.get(k)||[]){const val=dist+w;if(val<(best.get(n)??Infinity)){best.set(n,val);previous.set(n,k);push([val,n]);}}}
    const connected=goals.filter(x=>best.has(x.snap.key)).sort((a,b)=>(best.get(a.snap.key)+a.snap.gap)-(best.get(b.snap.key)+b.snap.gap));
    if(!connected.length)return {status:'Red desconectada entre origen y destinos'};
    const chosen=connected[0];let k=chosen.snap.key,path=[positions.get(k)];while(previous.has(k)){k=previous.get(k);path.push(positions.get(k));}path.reverse();
    return {status:'Estimación sobre red disponible',facility:chosen.facility,networkKm:best.get(chosen.snap.key),connectionM:(start.gap+chosen.snap.gap)*1000,path,connectors:[[coord(origin),path[0]],[path[path.length-1],coord(chosen.facility)]],method:'Dijkstra en red no dirigida con vértices compartidos. Sin tiempos de viaje ni transitabilidad verificada.',maxSnapM};
  }
  function accessibilityAt(origin,features,service){
    const groups=new Map();for(const f of features){const p=f.properties;if(service&&p.service!==service)continue;const k=[p.source_id,p.service,p.unit].join('|');if(!groups.has(k))groups.set(k,[]);groups.get(k).push(f);}
    const out=[];for(const features of groups.values()){
      const sorted=features.slice().sort((a,b)=>Number(a.properties.threshold)-Number(b.properties.threshold));
      const f=sorted.find(f=>inGeometry(coord(origin),f.geometry));if(!f)continue;const p=f.properties;
      const lower=Math.max(0,...sorted.filter(x=>+x.properties.threshold<+p.threshold).map(x=>+x.properties.threshold));
      out.push({source_id:p.source_id,service:p.service,unit:p.unit,lower,upper:+p.threshold,method:'Menor umbral que contiene el punto; rango de la fuente, no tiempo exacto. No identifica un destino.'});
    }return out;
  }
  function validateImport(type,input,meta,territories,existing){
    const errors=[],warnings=[];const allowed=['facilities','origins','areas','roads','accessibility'];
    if(!allowed.includes(type))return {errors:['Tipo de capa no admitido.'],warnings,records:[]};
    for(const k of ['name','source','cutoff','version','owner','license'])if(!String(meta[k]??'').trim())errors.push('Complete el metadato '+k+'.');
    if(!dateValid(meta.cutoff))errors.push('La fecha de corte debe ser válida (AAAA-MM-DD).');
    const isPoints=['facilities','origins'].includes(type);
    let rows;
    if(Array.isArray(input)&&isPoints)rows=input;
    else if(input?.type==='FeatureCollection'&&Array.isArray(input.features))rows=input.features;
    else return {errors:[...errors,'Use CSV de puntos o GeoJSON FeatureCollection.'],warnings,records:[]};
    if(!rows.length)errors.push('El archivo no contiene registros.');
    if(rows.length>15000)errors.push('El prototipo admite hasta 15.000 registros por carga.');
    const ids=new Set(),records=[],municipalities=new Map(territories.municipalities.features.map(f=>[f.properties.id,f]));
    const areas=new Set((existing.areas||[]).map(f=>f.properties.id));
    const allowedGeometry=isPoints?['Point']:type==='roads'?['LineString','MultiLineString']:['Polygon','MultiPolygon'];
    function geometryValid(g){
      if(!g||!allowedGeometry.includes(g.type))return false;
      let count=0,ok=true;function walk(x){if(!Array.isArray(x)||!x.length){ok=false;return;}if(typeof x[0]==='number'){if(x.length<2||!x.every(Number.isFinite)||x[0]<-82.5||x[0]>-66||x[1]<-5||x[1]>14)ok=false;count++;}else x.forEach(walk);}walk(g.coordinates);
      if(g.type==='LineString'&&g.coordinates.length<2)ok=false;
      if(g.type==='MultiLineString'&&g.coordinates.some(l=>l.length<2))ok=false;
      const polys=g.type==='Polygon'?[g.coordinates]:g.type==='MultiPolygon'?g.coordinates:[];
      for(const poly of polys)for(const r of poly)if(r.length<4||JSON.stringify(r[0])!==JSON.stringify(r[r.length-1]))ok=false;
      return ok&&count>0;
    }
    rows.slice(0,15001).forEach((raw,i)=>{
      const before=errors.length;const p=clone(raw.type==='Feature'?raw.properties||{}:raw);const row='Registro '+(i+1)+': ';
      if(!p.id||!String(p.id).trim())errors.push(row+'falta id.');else if(ids.has(String(p.id)))errors.push(row+'id duplicado '+p.id+'.');ids.add(String(p.id));
      if(!p.name)errors.push(row+'falta name.');
      p.id=String(p.id||'');p.department=String(p.department||'').padStart(2,'0');p.municipality=String(p.municipality||'').padStart(5,'0');
      const muni=municipalities.get(p.municipality);if(!muni||muni.properties.department!==p.department)errors.push(row+'departamento y municipio incompatibles con el catálogo.');
      let geometry=raw.type==='Feature'?clone(raw.geometry):null;
      if(isPoints){
        if(!geometry){const validNum=x=>x!==''&&x!==null&&x!==undefined&&Number.isFinite(Number(x));if(!validNum(p.lon)||!validNum(p.lat))errors.push(row+'longitud y latitud obligatorias y numéricas.');geometry={type:'Point',coordinates:[Number(p.lon),Number(p.lat)]};}
        if(geometry?.type==='Point'){p.lon=geometry.coordinates[0];p.lat=geometry.coordinates[1];if(muni&&!inGeometry([p.lon,p.lat],muni.geometry))errors.push(row+'punto fuera del límite municipal de referencia; revisar coordenadas o catálogo.');}
        for(const [field,catalog] of [['conditions',CONDITIONS],['services',SERVICES],['profiles',PROFILES]]){p[field]=lists(p[field]);if(!p[field].length||p[field].some(v=>!catalog.includes(v)))errors.push(row+field+' requiere valores del diccionario separados por |.');}
        if(p.area&&!areas.has(p.area)&&!(existing.demoAreaIds||[]).includes(p.area))errors.push(row+'área no registrada; cargue su límite primero o deje area vacío.');
        if(p.area&&areas.has(p.area)){const area=existing.areas.find(f=>f.properties.id===p.area);if(area.properties.municipality!==p.municipality||!inGeometry(coord(p),area.geometry))errors.push(row+'punto incompatible con el área indicada.');}
        if(type==='facilities'&&!STATUS.includes(p.status))errors.push(row+'status no admitido.');
        if(type==='origins')for(const k of ['gap','barrier','disruption']){p[k]=(p[k]===''||p[k]===null||p[k]===undefined)?null:Number(p[k]);if(p[k]!==null&&(!Number.isFinite(p[k])||p[k]<0||p[k]>100))errors.push(row+k+' debe ser porcentaje entre 0 y 100, o vacío.');}
      }
      if(!geometryValid(geometry))errors.push(row+'geometría incompatible, coordenadas fuera de Colombia, anillo abierto o valores no válidos. Use EPSG:4326 (longitud, latitud).');
      if(type==='accessibility'){p.threshold=Number(p.threshold);if(!SERVICES.includes(p.service)||!['min','h','km','m','s'].includes(p.unit)||!Number.isFinite(p.threshold)||p.threshold<=0)errors.push(row+'accesibilidad exige service, threshold positivo y unit (min, h, s, km o m).');}
      if((existing[type]||[]).some(r=>(r.properties||r).id===p.id))errors.push(row+'id ya existente; use un identificador nuevo.');
      p.source_id=meta.id;p.demo=false;
      if(errors.length===before)records.push(isPoints?p:{type:'Feature',geometry,properties:p});
    });
    if(!isPoints)warnings.push('Se verifican estructura y coordenadas. La validez topológica completa, la correspondencia territorial de polígonos/vías y la actualidad requieren revisión de la fuente.');
    if(type==='roads')warnings.push('La red debe estar segmentada con vértices compartidos. No se crean intersecciones automáticamente.');
    return {errors,warnings,records};
  }
  function validateAction(a){const errors=[];for(const k of ['title','problem','alternatives','criterion','responsible','deadline','department','municipality','condition','service','profile'])if(!String(a[k]||'').trim())errors.push('Complete '+k+'.');if(!dateValid(a.deadline))errors.push('Plazo inválido.');if(!ACTION_STATUS.includes(a.status))errors.push('Estado inválido.');if(a.status==='Cerrada'&&!String(a.verification||'').trim())errors.push('El cierre exige verificación.');return errors;}
  function validateState(s){
    if(!s||s.schema!==1)throw Error('Respaldo incompatible: se requiere schema 1.');
    for(const k of ['facilities','origins','areas','roads','accessibility','sources','evidence','actions'])if(!Array.isArray(s[k]))throw Error('Respaldo incompleto: '+k+'.');
    const stringList=v=>Array.isArray(v)&&v.every(x=>typeof x==='string');
    for(const k of ['facilities','origins','evidence','actions','sources']){const ids=new Set();for(const r of s[k]){if(!r||typeof r.id!=='string'||!r.id||ids.has(r.id))throw Error('Identificador ausente o duplicado en '+k+'.');ids.add(r.id);}}
    for(const k of ['facilities','origins'])for(const r of s[k])if(!r.name||!Number.isFinite(r.lat)||!Number.isFinite(r.lon)||r.lat<-5||r.lat>14||r.lon<-82.5||r.lon>-66||!stringList(r.conditions)||!stringList(r.services)||!stringList(r.profiles))throw Error('Registro inválido en '+k+'.');
    for(const r of s.facilities)if(!STATUS.includes(r.status))throw Error('Estado de sede inválido en respaldo.');
    for(const r of s.evidence)if(!r.title||!stringList(r.conditions)||!stringList(r.services)||!stringList(r.profiles))throw Error('Ficha de evidencia inválida en respaldo.');
    for(const a of s.actions)if(validateAction(a).length||!Array.isArray(a.history)||!stringList(a.conditions)||!stringList(a.services)||!stringList(a.profiles))throw Error('Acción incompleta en respaldo.');
    for(const k of ['areas','roads','accessibility'])for(const f of s[k]){
      const allowed=k==='roads'?['LineString','MultiLineString']:['Polygon','MultiPolygon'];
      if(f.type!=='Feature'||!f.geometry||!f.properties?.id||!allowed.includes(f.geometry.type)||!Array.isArray(f.geometry.coordinates))throw Error('Geometría inválida en '+k+'.');
      const walk=a=>Array.isArray(a)&&a.length>0&&(typeof a[0]==='number'?a.length>=2&&a.every(Number.isFinite):a.every(walk));
      if(!walk(f.geometry.coordinates))throw Error('Coordenadas inválidas en '+k+'.');
    }
    return clone(s);
  }
  return {VERSION,CONDITIONS,SERVICES,PROFILES,STATUS,ACTION_STATUS,norm,clone,esc,id,today,dateValid,lists,has,matches,inGeometry,haversine,coord,csvParse,csv,pointFeatures,ranking,nearest,networkRoute,accessibilityAt,validateImport,validateAction,validateState};
});
