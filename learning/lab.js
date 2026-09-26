'use strict';
const M=LabModels,$=id=>document.getElementById(id),val=id=>Number($(id).value);
const palette=['#007f86','#c75527','#7259a3','#32794e'];
const fmt=(v,n=2)=>Number(v).toLocaleString('en-GB',{maximumFractionDigits:n});
function output(id,unit,scale=1,n=1){$(id+'-o').textContent=fmt(val(id)*scale,n)+' '+unit;}
function plot(id,x,series,xlabel,ylabel,logx=false,logy=false){
  const canvas=$(id),box=canvas.parentElement,ctx=canvas.getContext('2d'),width=canvas.clientWidth;
  if(width<20)return;
  const h=265,dpr=window.devicePixelRatio||1;canvas.width=width*dpr;canvas.height=h*dpr;ctx.scale(dpr,dpr);
  const L=70,R=18,T=12,B=53,w=width-L-R,ph=h-T-B;
  const tx=z=>logx?Math.log10(z):z,ty=z=>logy?Math.log10(z):z;
  let xmin=tx(x[0]),xmax=tx(x.at(-1));let all=series.flatMap(s=>s.y).filter(v=>Number.isFinite(v)&&(!logy||v>0)).map(ty);
  let ymin=Math.min(...all),ymax=Math.max(...all);let pad=(ymax-ymin)*.08||1;ymin-=pad;ymax+=pad;
  const sx=z=>L+(tx(z)-xmin)/(xmax-xmin)*w,sy=z=>T+ph-(ty(z)-ymin)/(ymax-ymin)*ph;
  const tick=v=>{let a=Math.abs(v);return a>=100000?fmt(v/1e6,1)+'M':a>=1000?fmt(v/1000,1)+'k':a>0&&a<.01?v.toExponential(0):fmt(v, a<1?3:1)};
  ctx.fillStyle='#192d36';ctx.strokeStyle='#d5ddd9';ctx.lineWidth=1;ctx.font='12px system-ui';
  let xticks=logx?M.lin(Math.ceil(xmin),Math.floor(xmax),Math.floor(xmax)-Math.ceil(xmin)+1).filter((_,i)=>width>550||i%2===0).map(v=>10**v):M.lin(x[0],x.at(-1),width<450?4:6);
  xticks.forEach(v=>{let xx=sx(v);ctx.beginPath();ctx.moveTo(xx,T);ctx.lineTo(xx,T+ph);ctx.stroke();ctx.textAlign='center';ctx.fillText(tick(v),xx,T+ph+21)});
  M.lin(ymin,ymax,5).forEach(v=>{let yy=T+ph-(v-ymin)/(ymax-ymin)*ph;ctx.beginPath();ctx.moveTo(L,yy);ctx.lineTo(L+w,yy);ctx.stroke();ctx.textAlign='right';ctx.fillText(tick(logy?10**v:v),L-9,yy+4)});
  ctx.textAlign='center';ctx.fillText(xlabel,L+w/2,h-7);ctx.save();ctx.translate(14,T+ph/2);ctx.rotate(-Math.PI/2);ctx.fillText(ylabel,0,0);ctx.restore();
  ctx.save();ctx.beginPath();ctx.rect(L,T,w,ph);ctx.clip();
  series.forEach((s,k)=>{ctx.strokeStyle=palette[k%4];ctx.lineWidth=1.8;ctx.setLineDash(k===2?[5,3]:[]);ctx.beginPath();s.y.forEach((y,j)=>{if(j===0)ctx.moveTo(sx(x[j]),sy(y));else ctx.lineTo(sx(x[j]),sy(y))});ctx.stroke()});ctx.restore();ctx.setLineDash([]);
  let legend=box.querySelector('.legend');if(legend)legend.innerHTML=series.map((s,j)=>`<span><i class="swatch" style="border-color:${palette[j%4]}"></i>${s.name}</span>`).join('');
  canvas.onpointermove=e=>{let rect=canvas.getBoundingClientRect(),pos=Math.max(0,Math.min(1,(e.clientX-rect.left-L)/w));let xx=logx?10**(xmin+pos*(xmax-xmin)):xmin+pos*(xmax-xmin);
    let lo=0,hi=x.length-1;while(hi-lo>1){let mid=(hi+lo)>>1;if(x[mid]<xx)lo=mid;else hi=mid;}let a=(xx-x[lo])/(x[hi]-x[lo]);
    let tip=box.querySelector('.tooltip');if(tip)tip.textContent=xlabel+': '+tick(xx)+' · '+series.map(s=>s.name+': '+fmt(s.y[lo]+a*(s.y[hi]-s.y[lo]),3)).join(' · ');
  };
}
function switching(){
  [['swv','V'],['swd','%'],['swf','kHz'],['swl','µH'],['swi','A']].forEach(x=>output(...x));output('swr','Ω',1,2);
  const a=M.halfBridge({v:val('swv'),d:val('swd')/100,f:val('swf')*1000,l:val('swl')*1e-6,r:val('swr'),i:val('swi')});let t=a.t.map(x=>x*1e6);
  plot('switch-v',t,[{name:'Switch node',y:a.q.map(x=>x*val('swv'))}],'Time (µs)','Voltage (V)');
  plot('switch-i',t,[{name:'Winding',y:a.winding},{name:'Bridge bus draw',y:a.load}],'Time (µs)','Current (A)');
  plot('switch-c',t,[{name:'Into capacitor',y:a.cap}],'Time (µs)','Current (A)');
  $('switch-result').innerHTML=`<p>Winding variation: <strong>${fmt(a.pp)} A peak-to-peak</strong>. Mean bus current: <strong>${fmt(a.avg)} A</strong>. Capacitor current: <strong>${fmt(M.rms(a.cap))} A RMS</strong>.</p><p>Back EMF set to ${fmt(a.e)} V to hold this operating point. Negative capacitor current means discharge.</p>`;
}
function capacitors(){
  [['cn','parts'],['cret','%'],['ci','A'],['cf','kHz'],['cd','%'],['cl','nH']].forEach(x=>output(...x));
  let b=M.bank(val('cn'),val('cret')/100,val('cl')*1e-9),p=M.pulse({i:val('ci'),d:val('cd')/100,f:val('cf')*1000,c:b.c,r:b.r});
  plot('cap-v',p.t.map(x=>x*1e6),[{name:'Capacitance only',y:p.vc},{name:'Including ESR',y:p.v}],'Time (µs)','Deviation (V)');
  let z=M.impedance({n:val('cn'),ret:val('cret')/100,connection:val('cl')*1e-9});
  plot('cap-z',z.f,[{name:'Source ∥ capacitor',y:z.z},{name:'Capacitor branch alone',y:z.branch}],'Frequency (Hz)','Impedance (Ω)',true,true);
  $('cap-result').innerHTML=`<p>${fmt(val('cn')*4.7,1)} µF nameplate → <strong>${fmt(b.c*1e6,1)} µF effective</strong>. Charge-related ripple: <strong>${fmt(p.capacitivePP)} V p-p</strong>; ESR step: ${fmt(p.esrStep,3)} V.</p><p>Bank current: ${fmt(p.ir)} A RMS; estimated resistive loss: ${fmt(p.loss,3)} W. Equal sharing would be about ${fmt(p.ir/val('cn'),3)} A RMS per part. ESR assumptions: 20 mΩ per capacitor plus 1 mΩ common connection; this is not a thermal rating.</p>`;
}
function supply(){
  [['tc','µF'],['tl','µH'],['tr','mΩ'],['te','mΩ'],['tv','V'],['energy','J']].forEach(x=>output(...x));
  let a=M.transient({c:val('tc')*1e-6,rc:val('te')*.001,rs:val('tr')*.001,l:val('tl')*1e-6,v:val('tv'),startup:$('event').value==='start'});
  plot('trans-v',a.t.map(x=>x*1000),[{name:'Bus',y:a.voltage}],'Time (ms)','Voltage (V)');
  plot('trans-i',a.t.map(x=>x*1000),[{name:'Cable current',y:a.source}],'Time (ms)','Current (A)');
  $('trans-result').innerHTML=`<p>Natural frequency: <strong>${fmt(a.f0)} Hz</strong>. Damping ratio ζ: <strong>${fmt(a.zeta,3)}</strong>. Peak bus voltage: ${fmt(Math.max(...a.voltage))} V. Peak cable current: ${fmt(Math.max(...a.source))} A.</p><p>ζ &lt; 1 gives an oscillatory mode; ζ ≥ 1 gives a non-oscillatory mode. Source current and voltage settle differently.</p>`;
  let c=val('tc')*1e-6,head=.5*c*(46**2-42**2),need=2*val('energy')/(46**2-42**2),final=Math.sqrt(42**2+2*val('energy')/c);
  $('energy-result').innerHTML=`<p>This capacitance stores only <strong>${fmt(head,4)} J</strong> between 42 and 46 V. Absorbing ${fmt(val('energy'),1)} J in that window alone would require <strong>${fmt(need*1e6,0)} µF</strong>.</p><p>With no other energy destination, the ideal constant-C calculation reaches ${fmt(final,1)} V. That is a mathematical indication that a clamp or failure would intervene—not an allowed operating voltage. 46 V is an illustrative ceiling, not our qualified bus limit.</p>`;
}
function placement(){
  [['pl','nH'],['pi','A'],['pt','ns'],['pg','Ω']].forEach(x=>output(...x));
  let spike=val('pl')*val('pi')/val('pt'),rt=val('pg')+3,ig=(10-4)/rt,edge=12/ig,loss=.5*36*val('pi')*2*edge*1e-9*20000;
  let a=M.impedance({connection:3e-9}),b=M.impedance({connection:val('pl')*1e-9});
  plot('placement-z',a.f,[{name:'3 nH connection',y:a.branch},{name:fmt(val('pl'))+' nH connection',y:b.branch}],'Frequency (Hz)','Impedance (Ω)',true,true);
  $('placement-result').innerHTML=`<p>L × ΔI/Δt = <strong>${fmt(spike)} V</strong> across the selected connection. This is a scale estimate, not the complete MOSFET overshoot waveform.</p><p>Separate gate-drive example: ${fmt(val('pg'),1)} Ω external + 3 Ω assumed driver/internal resistance → ${fmt(ig,2)} A plateau current. With assumed Qgd = 12 nC, gate supply 10 V and plateau 4 V: ${fmt(edge,1)} ns per edge and ~${fmt(loss,2)} W overlap loss per hard-switched MOSFET at 36 V, ${fmt(val('pi'))} A, 20 kHz. These assumed gate parameters are not characterised CSD88599 values. The independent transition-time slider above is not linked to this estimate.</p>`;
}
function sensing(){
  [['si','A'],['sr','µΩ'],['fr','Ω'],['fc','nF'],['fb','Hz'],['fd','µs']].forEach(x=>output(...x));
  let i=val('si'),v=1.65+.014*i,p=i*i*.0005,error=i*(val('sr')*1e-6)/.0005,tau=val('fr')*val('fc')*1e-9,phase=-Math.atan(2*Math.PI*val('fb')*tau)*180/Math.PI,delay=-360*val('fb')*val('fd')*1e-6;
  let a=M.filters({r:val('fr'),c:val('fc')*1e-9,delay:val('fd')*1e-6});
  plot('filter-mag',a.f,[{name:'Actual bus filter',y:a.bus},{name:'Hypothetical current LPF',y:a.hyp},{name:'Optional feedback, DNP',y:a.optional}],'Frequency (Hz)','Normalised gain (dB)',true);
  const n=a.f.findIndex(f=>f>10000);
  plot('filter-phase',a.f.slice(0,n),[{name:'Hypothetical filter',y:a.phase.slice(0,n)},{name:'Filter + delay',y:a.totalPhase.slice(0,n)}],'Frequency (Hz)','Phase (degrees)',true);
  $('sense-result').innerHTML=`<p>At ${fmt(i)} A: <strong>${fmt(v,3)} V</strong> ideal amplifier output, <strong>${fmt(p,2)} W</strong> instantaneous shunt heating. With the same power current through the shared copper, ${fmt(val('sr'))} µΩ adds <strong>${fmt(error,2)} A</strong> equivalent measurement error. Kelvin routing excludes this extra drop.</p><p>Hypothetical filter cutoff: ${fmt(a.fc)} Hz. At ${fmt(val('fb'))} Hz: filter phase ${fmt(phase,1)}° + delay phase ${fmt(delay,1)}° = <strong>${fmt(phase+delay,1)}°</strong>. This is added phase lag, not the complete loop phase margin. A 12-bit, 3.3 V ADC gives ~${fmt(3.3/4096/.014,4)} A/count ideally.</p>`;
}
let active='s0';const renderers={s1:switching,s2:capacitors,s3:supply,s4:placement,s5:sensing};
document.querySelectorAll('nav button').forEach(button=>button.addEventListener('click',()=>{
  document.querySelectorAll('nav button').forEach(b=>b.setAttribute('aria-selected',String(b===button)));
  active=button.getAttribute('aria-controls');document.querySelectorAll('main>section').forEach(s=>s.hidden=s.id!==active);
  if(renderers[active])renderers[active]();
}));
document.querySelectorAll('input,select').forEach(el=>el.addEventListener('input',()=>renderers[active]?.()));
document.querySelectorAll('nav button').forEach((button,i)=>button.addEventListener('keydown',e=>{
  if(e.key==='ArrowLeft'||e.key==='ArrowRight'){
    e.preventDefault();const buttons=[...document.querySelectorAll('nav button')];
    const next=buttons[(i+(e.key==='ArrowRight'?1:buttons.length-1))%buttons.length];next.focus();next.click();
  }
}));
window.addEventListener('resize',()=>renderers[active]?.());
const rows=Object.entries(window.ComparisonData||{});
$('comparison-table').innerHTML='<table><thead><tr><th>Architecture</th><th>Effective µF</th><th>Bus p-p, V</th><th>Cap branch RMS, A</th><th>Estimated resistive loss, W</th></tr></thead><tbody>'+rows.map(([k,v])=>`<tr><td>${k}</td><td>${fmt(v.effective_C_uF,1)}</td><td>${fmt(v.bus_pp_V)}</td><td>${v.branch_rms_A.map(x=>fmt(x,2)).join(' / ')}</td><td>${fmt(v.estimated_ESR_loss_W,2)}</td></tr>`).join('')+'</tbody></table>';
