(function(root,factory){const api=factory();if(typeof module==='object')module.exports=api;else root.IETS_REPO=api;})(typeof window!=='undefined'?window:globalThis,function(){
  function convert(base,result){
    const state=JSON.parse(JSON.stringify(base));
    // A new geographic workspace replaces only repository-derived layers and points.
    // User actions, evidence and manually imported records remain intact.
    const characterized=new Map(state.facilities.filter(r=>r.repository&&r.verified_at).map(r=>[r.id,r]));
    for(const k of ['facilities','origins','roads','accessibility','sources'])state[k]=state[k].filter(r=>!(r.properties||r).repository);
    const dept=result.filters.department||'',muni=result.filters.municipality||'',area=result.filters.area||'';
    state.repositoryLayers=result.layers;state.repository={root:result.root,generated:result.generated,filters:result.filters,boundary:result.boundary,notes:result.notes,catalog:result.catalog};
    state.sources.push(...result.sources);state.preferReal=true;
    for(const layer of result.layers){
      for(const feature of layer.collection.features){
        const p=feature.properties,id=p._iets_id,g=feature.geometry;
        const common={id,name:p._nombre||id,department:dept,municipality:muni,area,source_id:layer.source_id,demo:false,repository:true,repositoryLayer:layer.id,conditions:[],services:[],profiles:[],source_properties:p};
        if(layer.category==='salud'||layer.category==='localidades'||layer.category==='tabla'){
          const point=g.type==='Point'?g.coordinates:[p._punto_conteo_lon,p._punto_conteo_lat];
          if(!point||!Number.isFinite(point[0])||!Number.isFinite(point[1]))continue;
          const record={...common,lon:point[0],lat:point[1],notes:'Registro geográfico del repositorio. Estado operativo y relación con ECNT pendientes de caracterización.',geometry_method:g.type==='Point'?'Punto de fuente':'Punto representativo de geometría; no es domicilio ni acceso verificado'};
          if(layer.category==='salud'){record.status='Sin verificar';record.source_type=String(p.healthcare||p.amenity||'Sin clasificación');const prior=characterized.get(id);if(prior)for(const key of ['status','conditions','services','profiles','verification_source','verified_at'])record[key]=prior[key];state.facilities.push(record);}
          else state.origins.push({...record,gap:null,barrier:null,disruption:null,indicator_note:'Localidad o punto geográfico. No representa una necesidad clínica constatada.'});
        }
        if(layer.category==='vias'&&['LineString','MultiLineString'].includes(g.type)){const attrs={...common};delete attrs.source_properties;state.roads.push({type:'Feature',geometry:g,properties:{...attrs,bridge:p.bridge,tunnel:p.tunnel,layer:p.layer}});}
        // Source accessibility remains native in repositoryLayers. No equivalence with an ECNT service is invented.
      }
    }
    return state;
  }
  return {convert};
});
