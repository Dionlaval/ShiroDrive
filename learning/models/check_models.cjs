// Meaningful analytical/reference checks for the model used by the offline lab.
const fs=require('fs'),path=require('path'),assert=require('assert');
const M=require('./lab_models.js'),ROOT=path.resolve(__dirname,'..');
let maxError=0,comparisons=0;
for(const fixture of JSON.parse(fs.readFileSync(path.join(ROOT,'qa/transient_reference.json'),'utf8'))){
  const out=M.transient(fixture.parameters);
  for(const s of fixture.samples)for(const key of ['voltage','source']){
    const delta=Math.abs(out[key][s.index]-s[key]);maxError=Math.max(maxError,delta);comparisons++;
    assert(delta<2e-6,`${key} diverged ${delta}`);
  }
}
for(const d of [.1,.25,.5,.9]){
  const p=M.pulse({i:20,d,f:20000,c:100e-6,r:0});
  assert(Math.abs(p.capacitivePP-20*d*(1-d)/(20000*100e-6))<1e-12);
  assert(Math.abs(p.loss)<1e-12);
}
const h=M.halfBridge();assert(Math.abs(M.mean(h.winding)-20)<.03);assert(Math.abs(h.pp-4.499414)<.005);
assert(Math.abs(M.filters().btau-267.1428571428571e-6)<1e-14);
let sweep=0;
for(const c of [20e-6,94e-6,2200e-6])for(const l of [.2e-6,5e-6])for(const rs of [.005,.3])for(const rc of [.001,.1])for(const startup of [false,true]){
  const a=M.transient({c,l,rs,rc,startup});assert(a.voltage.every(Number.isFinite));assert(a.source.every(Number.isFinite));sweep++;
}
for(const n of [10,40,100])for(const ret of [.2,.5,1])for(const connection of [1e-9,50e-9]){
  const a=M.impedance({n,ret,connection});assert(a.z.every(x=>Number.isFinite(x)&&x>0));
}
const result={transient_reference_comparisons:comparisons,max_absolute_difference:maxError,
  extreme_transient_cases_finite:sweep,analytic_pulse_halfbridge_filter_checks:'passed',
  impedance_positive_and_finite:'passed',browser_preview:'not performed; security policy blocked file URL'};
fs.writeFileSync(path.join(ROOT,'qa/javascript_checks.json'),JSON.stringify(result,null,2)+'\n');console.log(result);
