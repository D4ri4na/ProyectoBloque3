// Pruebas del motor JavaScript en Node, sin abrir ni controlar un navegador.
// El DOM mínimo solo recibe texto/eventos; no sustituye una revisión visual.
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const root=__dirname;
const html=fs.readFileSync(path.join(root,'Explorador_Musical.html'),'utf8');
const script=html.split('<script>')[1].split('</script>')[0];
function element(){return {value:'',checked:false,innerHTML:'',textContent:'',dataset:{},listeners:{},children:[],
 addEventListener(type,callback){this.listeners[type]=callback;},
 replaceChildren(){this.children=[];this.innerHTML='';},
 append(child){this.children.push(child);},querySelectorAll(){return [];}};}
const elements={};
const document={getElementById(id){return elements[id]??=(element());},createElement(){return element();},addEventListener(){}};
for(const [name,value] of Object.entries({model:'KMeans',space:'pca',scope:'cluster'}))document.getElementById(name).value=value;
document.getElementById('differentArtist').checked=true;
const context=vm.createContext({document,console});
vm.runInContext(script,context);
const run=code=>vm.runInContext(code,context);
assert.equal(run('DATA.songs.length'),10000);
assert.match(elements.status.textContent,/10 sugerencias/);
assert.match(elements.results.innerHTML,/open.spotify.com/);
const ids=run('Object.keys(DATA.specs)');
let checks=0;
for(const id of ids){
  for(const q of run('[DATA.initial, DATA.train_size, DATA.train_size+19, 0]')){
    run(`chosen=${q}`);
    const result=run(`retrieve(${JSON.stringify(id)})`);
    assert(result.items.length>0);
    for(const item of result.items){
      assert.notEqual(item.index,q);
      assert(item.index<run('DATA.train_size'));
      assert(!run(`sharedArtist(${item.index},chosen)`));
      assert.equal(run(`DATA.labels[${JSON.stringify(id)}][${item.index}]`),run(`DATA.labels[${JSON.stringify(id)}][chosen]`));
    }
    for(let i=1;i<result.items.length;i++)assert(result.items[i].distance>=result.items[i-1].distance);
    checks++;
  }
}
run('chosen=DATA.initial');elements.lessPopular.checked=true;
for(const item of run("retrieve('KMeans_pca')").items){
 assert(run(`DATA.songs[${item.index}][3]<DATA.songs[chosen][3]`));
}
// Caso sin resultados: popularidad cero y filtro estrictamente menor.
run('chosen=DATA.songs.findIndex(s=>s[3]===0);render()');
assert.match(elements.results.innerHTML,/No hay canciones/);
elements.lessPopular.checked=false;
elements.scope.value='all';run('chosen=DATA.initial');
assert.equal(JSON.stringify(run("retrieve('KMeans_original').items")),JSON.stringify(run("retrieve('GMM_original').items")));
assert.equal(JSON.stringify(run("retrieve('KMeans_pca').items")),JSON.stringify(run("retrieve('GMM_pca').items")));
// Búsqueda y selección por eventos: título real, sin resultados, y selección.
elements.search.value='zzzzzzzz-no-song-92834';elements.search.listeners.input();
assert.match(elements.searchInfo.textContent,/No hay coincidencias/);
elements.search.value=run('DATA.songs[DATA.initial][1]');elements.search.listeners.input();
assert(elements.matches.children.length>0);
elements.matches.children[0].listeners.click();
assert.equal(elements.search.value,'');
assert.match(elements.seed.innerHTML,/Tu canción/);
// Coincidencia Python/JS para cuatro consultas reales de la evaluación de prueba.
elements.scope.value='cluster';
const csv=fs.readFileSync(path.join(root,'outputs/evaluacion_recuperacion.csv'),'utf8').trim().split(/\r?\n/);
const fields=csv[0].split(',');
const evaluated=csv.slice(1,17).map(line=>Object.fromEntries(line.split(',').map((v,i)=>[fields[i],v])));
for(const row of evaluated){
 run(`chosen=DATA.songs.findIndex(s=>s[0]===${JSON.stringify(row.query_id)})`);
 const result=run(`retrieve(${JSON.stringify(row.configuration)})`);
 assert.equal(result.total,Number(row.candidate_pool));
 assert.equal(result.items.length,Number(row.returned));
 const recall=run(`(()=>{const q=DATA.matrices.original[chosen];const candidates=[];for(let i=0;i<DATA.train_size;i++){if(sharedArtist(i,chosen))continue;let d=0;for(let j=0;j<q.length;j++)d+=(q[j]-DATA.matrices.original[i][j])**2;candidates.push({i,d});}candidates.sort((a,b)=>a.d-b.d||a.i-b.i);let reference=new Set(candidates.slice(0,10).map(x=>x.i));return retrieve(${JSON.stringify(row.configuration)}).items.filter(x=>reference.has(x.index)).length/10;})()`);
 assert(Math.abs(recall-Number(row.recall_at_10))<1e-9);
 checks++;
}
// Validación del laboratorio: proyección y predicción sobre canciones conocidas.
let professionalChecks=0;
for(const config of ids){
 for(const idx of [0,19,7999,8000,9458,9999]){
  assert.equal(run(`predictVector(DATA.raw[${idx}],${JSON.stringify(config)}).cluster`),run(`DATA.labels[${JSON.stringify(config)}][${idx}]`));
  const error=run(`(()=>{const q=projectRaw(DATA.raw[${idx}],DATA.specs[${JSON.stringify(config)}].space),r=DATA.matrices[DATA.specs[${JSON.stringify(config)}].space][${idx}];return Math.max(...q.map((v,j)=>Math.abs(v-r[j])));})()`);
  assert(error<1e-5);professionalChecks++;
 }
}
run('chosen=DATA.initial;render()');
assert.match(elements.marketingBrief.innerHTML,/Hipótesis editoriales/);
assert.equal(run('latestBrief.training_profile_size'),run('DATA.labels[key()].slice(0,DATA.train_size).filter(x=>x===DATA.labels[key()][chosen]).length'));
run('simulated[1]=0.15;simulated[4]=0.95;renderSimulation()');
assert.match(elements.simulationOutput.innerHTML,/Combinación hipotética/);
for(const config of ids){const result=run(`simulatedNeighbors(simulated,${JSON.stringify(config)})`);for(const x of result.items){assert(x.index<8000);assert(!run(`sharedArtist(${x.index},chosen)`));assert(Number.isFinite(x.distance));}professionalChecks++;}
elements.resetSimulation.listeners.click();
assert.equal(run('JSON.stringify(simulated)'),run('JSON.stringify(DATA.raw[chosen])'));
console.log('Laboratorio: '+professionalChecks+' casos de proyección, predicción y simulación; ficha, filtros y reinicio verificados.');
const report={status:'passed',motor_cases:checks,professional_cases:professionalChecks,checks:['cuatro configuraciones','sin autorrecomendación',
 'candidatos train','exclusión de artistas','distancias ordenadas','filtro de popularidad',
 'estado sin resultados','modo global independiente del modelo','búsqueda y selección',
 'concordancia Python-JavaScript en 16 consultas/configuraciones'],
 limitation:'Pruebas del motor y eventos con DOM mínimo; no equivalen a inspección visual en navegador.'};
fs.writeFileSync(path.join(root,'outputs/validacion_interfaz.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
