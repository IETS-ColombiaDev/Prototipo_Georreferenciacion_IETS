(function(){
const C=window.IETS,cutoff='2026-10-30',profiles=C.PROFILES.slice(),conditions=C.CONDITIONS.slice(0,3);
const base={department:'76',municipality:'76001',source_id:'DEMO-2026',demo:true,profiles};
const areaNames={'demo-cali-1':'Comuna 1 · ensayo','demo-cali-13':'Comuna 13 · ensayo','demo-cali-15':'Comuna 15 · ensayo','demo-cali-18':'Comuna 18 · ensayo','demo-cali-20':'Comuna 20 · ensayo','demo-cali-montebello':'Montebello · ensayo'};
const origins=[
 ['O-01','Necesidad de seguimiento · sector occidental','demo-cali-1',-76.551,3.456,48,62,35],
 ['O-02','Necesidad de continuidad · sector oriental','demo-cali-13',-76.501,3.427,72,76,68],
 ['O-03','Necesidad de medicamentos · sector suroriental','demo-cali-15',-76.505,3.400,65,58,73],
 ['O-04','Necesidad de atención · sector sur','demo-cali-18',-76.547,3.382,40,52,30],
 ['O-05','Necesidad de coordinación · ladera','demo-cali-20',-76.561,3.415,78,85,65],
 ['O-06','Necesidad de acceso · entorno rural','demo-cali-montebello',-76.570,3.477,55,88,48]
].map(([id,name,area,lon,lat,gap,barrier,disruption])=>({...base,id,name,area,lon,lat,gap,barrier,disruption,conditions,services:C.SERVICES.slice(),indicator_note:'Porcentajes ficticios de un ejercicio. No son prevalencias ni estimaciones poblacionales.'}));
const facilities=[
 ['S-01','Sede demostrativa Norte',-76.531,3.470,'Operativa','Seguimiento ambulatorio|Laboratorio','Diabetes|Hipertensión','demo-cali-1'],
 ['S-02','Sede demostrativa Oriente',-76.499,3.435,'Capacidad limitada','Seguimiento ambulatorio','Diabetes|Hipertensión','demo-cali-13'],
 ['S-03','Dispensación demostrativa Oriente',-76.497,3.423,'No operativa','Medicamentos','Diabetes|Hipertensión|Cáncer','demo-cali-13'],
 ['S-04','Sede demostrativa Sur',-76.531,3.394,'Operativa','Seguimiento ambulatorio|Rehabilitación','Diabetes|Hipertensión','demo-cali-18'],
 ['S-05','Unidad demostrativa Oncología',-76.538,3.423,'Capacidad limitada','Oncología|Laboratorio','Cáncer','demo-cali-20'],
 ['S-06','Dispensación demostrativa Centro',-76.528,3.445,'Operativa','Medicamentos','Diabetes|Hipertensión|Cáncer','demo-cali-1'],
 ['S-07','Laboratorio demostrativo Sur',-76.515,3.396,'Sin verificar','Laboratorio','Diabetes|Hipertensión|Cáncer','demo-cali-15'],
 ['S-08','Sede demostrativa Ladera',-76.557,3.423,'No operativa','Seguimiento ambulatorio|Rehabilitación','Diabetes|Hipertensión','demo-cali-20'],
 ['S-09','Sede demostrativa Rural',-76.565,3.470,'Capacidad limitada','Seguimiento ambulatorio','Diabetes|Hipertensión','demo-cali-montebello'],
 ['S-10','Dispensación demostrativa Sur',-76.539,3.385,'Operativa','Medicamentos','Diabetes|Hipertensión|Cáncer','demo-cali-18'],
 ['S-11','Unidad demostrativa de Recuperación',-76.520,3.414,'Operativa','Rehabilitación|Seguimiento ambulatorio','Diabetes|Hipertensión|Cáncer','demo-cali-15'],
 ['S-12','Laboratorio demostrativo Occidente',-76.547,3.443,'Operativa','Laboratorio','Diabetes|Hipertensión|Cáncer','demo-cali-1']
].map(([id,name,lon,lat,status,services,cs,area])=>({...base,id,name,lon,lat,status,services:services.split('|'),conditions:cs.split('|'),area,notes:'Sede ficticia. La ubicación, la oferta y el estado se usan únicamente para ensayar el flujo.'}));
const roads=[...origins,...facilities].map((r,i)=>({type:'Feature',properties:{...base,id:'V-'+i,name:'Conexión de ensayo '+(i+1),bridge:'no',tunnel:'no',layer:0},geometry:{type:'LineString',coordinates:[[r.lon,r.lat],[-76.53,3.43]]}}));
const ring=(lon,lat,r)=>Array.from({length:65},(_,i)=>{const a=i/64*2*Math.PI;return [lon+Math.cos(a)*r,lat+Math.sin(a)*r];});
const accessibility=[15,30,60].map((n,i)=>({type:'Feature',properties:{...base,id:'A-'+n,name:'Umbral sintético '+n+' min',threshold:n,unit:'min',service:'Seguimiento ambulatorio'},geometry:{type:'Polygon',coordinates:[ring(-76.53,3.43,[.022,.045,.075][i])]}}));
const evidence=[
 {id:'E-01',title:'Continuidad de seguimiento en diabetes e hipertensión',conditions:['Diabetes','Hipertensión'],services:['Seguimiento ambulatorio','Medicamentos'],question:'¿Qué alternativas organizativas permiten mantener el seguimiento y el acceso al servicio en el territorio?',population:'Personas con diabetes o hipertensión, según el alcance que defina el equipo.',alternative:'Por definir con el equipo científico.',outcomes:'Continuidad, barreras de acceso y factibilidad institucional.',applicability:'Identificar el contexto territorial y verificar las condiciones de implementación.'},
 {id:'E-02',title:'Continuidad de servicios oncológicos',conditions:['Cáncer'],services:['Oncología','Medicamentos','Laboratorio'],question:'¿Qué opciones de coordinación institucional permiten mantener la atención oncológica ante una afectación?',population:'Población y servicio por delimitar en la pregunta de decisión.',alternative:'Alternativas organizativas por documentar.',outcomes:'Continuidad del servicio y factibilidad de las alternativas.',applicability:'Verificar el servicio requerido y la capacidad funcional de cada alternativa.'},
 {id:'E-03',title:'Recuperación territorial de servicios para ECNT',conditions:['Todas las ECNT'],services:C.SERVICES.slice(),question:'¿Qué criterios documentados apoyan la priorización de la recuperación de servicios?',population:'Territorios y servicios afectados definidos para el ejercicio.',alternative:'Escenarios de organización de servicios por comparar.',outcomes:'Trazabilidad de decisiones y cierre de acciones.',applicability:'Contrastar los supuestos con responsables territoriales.'}
].map(e=>({...e,profiles,status:'Borrador',reference:'',reviewer:'',certainty:'No evaluada',design:'Pendiente de revisión metodológica',version:'0.1',reviewed:'',next_review:'',summary:'Plantilla para registrar evidencia. No contiene una recomendación clínica ni una síntesis científica aprobada.',demo:true}));
window.IETS_DEMO={schema:1,version:C.VERSION,created:cutoff,facilities,origins,roads,accessibility,areas:[],demoAreas:Object.entries(areaNames).map(([id,name])=>({id,name,department:'76',municipality:'76001',demo:true})),evidence,actions:[],sources:[
 {id:'MP5-COL',name:'Límites administrativos de Colombia',source:'Microplanificacion_v5.zip · geo/adm1 y geo/adm2_v03/COL.geojson.gz',cutoff:null,version:'v5 · adaptación cartográfica 1.0',owner:'Responsable original por confirmar',license:'Condiciones de redistribución por verificar antes de publicación externa',coverage:'33 unidades departamentales y 1.122 unidades del catálogo aportado. No certifica el catálogo DIVIPOLA vigente.',demo:false,note:'Límites simplificados para visualización. Los originales y sus hashes se conservan en referencia. Sin límites oficiales de comunas.'},
 {id:'DEMO-2026',name:'Escenario de ensayo en Cali',source:'Datos sintéticos creados para el prototipo IETS',cutoff,version:'1.0',owner:'Equipo del prototipo',license:'Uso demostrativo local',coverage:'6 necesidades, 12 sedes ficticias, red radial y umbrales de ensayo',demo:true,note:'No contiene personas, establecimientos reales, carga observada ni tiempos de viaje medidos.'}
]};
})();
