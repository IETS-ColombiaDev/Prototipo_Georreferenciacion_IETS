/* Produce la instantánea inicial a partir de recortes reales, sin modificar fuentes. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..'),C=require('../app/js/core.js'),R=require('../app/js/repository-core.js');
const ctx={window:{IETS:C}};vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(root,'app/js/demo.js'),'utf8'),ctx);
const inputs=process.argv.slice(2);if(!inputs.length)throw Error('Indique los JSON de recortes producidos por repositorio.py.');
const results=inputs.map(p=>JSON.parse(fs.readFileSync(p,'utf8'))),result=results[0];
for(const more of results.slice(1)){result.layers.push(...more.layers);result.sources.push(...more.sources);result.notes.push(...more.notes);}
const state=R.convert(ctx.window.IETS_DEMO,result);C.validateState(state);
const json=JSON.stringify(state);fs.writeFileSync(path.join(root,'datos/ejemplo_cali.json'),json);
fs.writeFileSync(path.join(root,'app/js/initial.js'),'window.IETS_INITIAL='+json.replace(/</g,'\\u003c')+';');
console.log(JSON.stringify({bytes:Buffer.byteLength(json),layers:result.layers.length,features:result.layers.reduce((a,x)=>a+x.featureCount,0),facilities:state.facilities.filter(x=>x.repository).length,origins:state.origins.filter(x=>x.repository).length}));
