/* Test presentation-code wiring with DOM/canvas stubs. This is NOT browser rendering QA. */
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..'),structure=JSON.parse(fs.readFileSync(path.join(root,'qa/dom_structure.json')));
let drawCalls=0,finiteCoordinates=0;
const ctx=new Proxy({}, {get(t,key){if(key in t)return t[key];return (...args)=>{drawCalls++;for(const a of args)if(typeof a==='number'){assert(Number.isFinite(a),`Non-finite ${key}`);finiteCoordinates++;}};},set(t,k,v){t[k]=v;return true;}});
class Element{
 constructor(tag,a){this.tag=tag;this.a={...a};this.id=a.id;this.value=a.value||'';this.textContent='';this.innerHTML='';this.hidden='hidden'in a;this.listeners={};this.clientWidth=520;this.parentElement={querySelector:()=>({innerHTML:'',textContent:''})};}
 addEventListener(event,fn){this.listeners[event]=fn;}
 setAttribute(k,v){this.a[k]=v;}
 getAttribute(k){return this.a[k]??null;}
 getContext(){return ctx;}
 focus(){}
 click(){this.listeners.click?.({});}
}
const elements=structure.filter(([,a])=>a.id).map(([tag,a])=>new Element(tag,a)),byId=Object.fromEntries(elements.map(x=>[x.id,x]));
byId.event.value='step';
const document={getElementById:id=>{assert(byId[id],`Missing ${id}`);return byId[id];},querySelectorAll:q=>{
 if(q==='nav button')return elements.filter(e=>e.tag==='button'&&e.a.role==='tab');
 if(q==='main>section')return elements.filter(e=>e.tag==='section');
 if(q==='input,select')return elements.filter(e=>['input','select'].includes(e.tag));
 throw Error('Unhandled selector '+q);
}};
const window={devicePixelRatio:1,addEventListener(){},ComparisonData:JSON.parse(fs.readFileSync(path.join(root,'data/comparison.json')))};
const sandbox={document,window,LabModels:require('./lab_models.js'),Math,Number,Array,String,console};vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(root,'lab.js'),'utf8'),sandbox);
let inputEvents=0,tabs=0;
// Each range belongs to the last preceding section in the actual HTML structure.
let section='s0';const owners={};for(const [tag,a]of structure){if(tag==='section')section=a.id;if(tag==='input'||tag==='select')owners[a.id]=section;}
for(let i=0;i<=6;i++){
 byId['t'+i].click();tabs++;assert(!byId['s'+i].hidden);
 for(const el of elements.filter(e=>e.tag==='input'&&owners[e.id]==='s'+i)){
   const initial=el.value;
   for(const v of [el.a.min,el.a.max,initial]){el.value=v;el.listeners.input();inputEvents++;}
 }
 if(i===3){byId.event.value='start';byId.event.listeners.input();inputEvents++;byId.event.value='step';}
}
// Exercise the narrow-layout numerical drawing path, without claiming a real layout screenshot.
for(const e of elements.filter(e=>e.tag==='canvas'))e.clientWidth=284;
for(let i=1;i<=5;i++)byId['t'+i].click();
for(const id of ['switch-result','cap-result','trans-result','energy-result','placement-result','sense-result']){
 assert(byId[id].innerHTML.length>50);assert(!/NaN|Infinity|undefined/.test(byId[id].innerHTML));
}
assert(byId['comparison-table'].innerHTML.includes('80 ceramics'));
const report={tab_handlers_exercised:tabs,input_events_exercised:inputEvents,draw_calls:drawCalls,finite_numeric_canvas_arguments:finiteCoordinates,
result_texts_finite:'passed',comparison_table_present:true,method:'DOM/canvas stubs, no browser engine; does not verify actual CSS layout or visual rendering'};
fs.writeFileSync(path.join(root,'qa/lab_wiring_checks.json'),JSON.stringify(report,null,2)+'\n');console.log(report);
