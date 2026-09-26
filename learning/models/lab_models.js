/* SI units except where stated. Pure functions shared by the offline lab and checks. */
(function(root){
  const pi=Math.PI;
  const add=(a,b)=>[a[0]+b[0],a[1]+b[1]], inv=a=>{let d=a[0]*a[0]+a[1]*a[1];return[a[0]/d,-a[1]/d]},abs=a=>Math.hypot(...a);
  const capZ=(f,c,r,l)=>[r,2*pi*f*l-1/(2*pi*f*c)];
  const parallel=zs=>inv(zs.map(inv).reduce(add,[0,0]));
  const lin=(a,b,n)=>Array.from({length:n},(_,i)=>a+(b-a)*i/(n-1));
  const log=(a,b,n)=>lin(Math.log10(a),Math.log10(b),n).map(x=>10**x);
  const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
  const rms=a=>Math.sqrt(mean(a.map(x=>x*x)));
  function halfBridge({v=36,d=.5,f=20000,l=100e-6,r=.1,i=20}={}){
    let T=1/f,tau=l/r,e=d*v-r*i,a=Math.exp(-d*T/tau),b=Math.exp(-(1-d)*T/tau),on=(v-e)/r,off=-e/r;
    let start=(off*(1-b)+on*(1-a)*b)/(1-a*b),peak=on+(start-on)*a;
    let t=Array.from({length:1800},(_,j)=>j*T/600),q=t.map(x=>(x%T)<d*T?1:0);
    let winding=t.map((x,j)=>q[j]?on+(start-on)*Math.exp(-(x%T)/tau):off+(peak-off)*Math.exp(-((x%T)-d*T)/tau));
    let load=winding.map((x,j)=>x*q[j]);let avg=mean(load);
    return {t,q,winding,load,cap:load.map(x=>avg-x),e,avg,pp:peak-start};
  }
  function pulse({i=20,d=.5,f=20000,c=100e-6,r=.002}={}){
    let t=lin(0,2/f,1201),ic=t.map(x=>(x*f%1)<d?-(1-d)*i:d*i),T=1/f;
    let vc=t.map(x=>{let u=x%T;return u<d*T?-(1-d)*i*u/c:-(1-d)*i*d*T/c+d*i*(u-d*T)/c});
    let offset=mean(vc);let v=vc.map((x,j)=>x-offset+r*ic[j]);
    return {t,ic,vc:vc.map(x=>x-offset),v,capacitivePP:i*d*(1-d)/(f*c),esrStep:i*r,ir:rms(ic),loss:i*i*d*(1-d)*r};
  }
  function bank(n=40,ret=.5,connection=3e-9){return{c:n*4.7e-6*ret,r:.02/n+.001,l:1e-9/n+connection}}
  function impedance({n=40,ret=.5,connection=3e-9,rs=.05,ls=1e-6}={}){
    let f=log(1,1e8,650),b=bank(n,ret,connection);
    let branch=f.map(x=>capZ(x,b.c,b.r,b.l));let z=f.map((x,j)=>parallel([[rs,2*pi*x*ls],branch[j]]));
    return {f,z: z.map(abs),phase:z.map(x=>Math.atan2(x[1],x[0])*180/pi),branch:branch.map(abs),b};
  }
  function transient({c=94e-6,rc=.0015,rs=.05,l=1e-6,v=36,i=20,startup=false}={}){
    // Exact 2x2 matrix exponential: initial state minus final equilibrium.
    let il=startup?0:i,eqi=il,eqv=v-rs*il,x0=-eqi,y0=(startup?0:v)-eqv;
    let aa=-(rs+rc)/l,bb=-1/l,cc=1/c,h=aa/2,disc=h*h+bb*cc;
    let t=lin(0,.002,1501),voltage=[],source=[];
    t.forEach(tt=>{
      let co,si;
      if(Math.abs(disc)<1e-8){co=1;si=tt;}
      else if(disc<0){let w=Math.sqrt(-disc);co=Math.cos(w*tt);si=Math.sin(w*tt)/w;}
      else {let w=Math.sqrt(disc);/* combine exponentials to avoid cosh overflow */
        let ep=Math.exp((h+w)*tt),em=Math.exp((h-w)*tt);
        let ex=.5*(ep+em),es=.5*(ep-em)/w;
        let ix=eqi+ex*x0+es*((aa-h)*x0+bb*y0),vy=eqv+ex*y0+es*(cc*x0-h*y0);
        source.push(ix);voltage.push(vy+rc*(ix-il));return;}
      let ex=Math.exp(h*tt),ix=eqi+ex*(co*x0+si*((aa-h)*x0+bb*y0)),vy=eqv+ex*(co*y0+si*(cc*x0-h*y0));
      source.push(ix);voltage.push(vy+rc*(ix-il));
    });
    return {t,voltage,source,f0:1/(2*pi*Math.sqrt(l*c)),zeta:(rs+rc)*Math.sqrt(c/l)/2};
  }
  function filters({r=1000,c=10e-9,delay=25e-6}={}){
    let f=log(10,1e6,650),tau=r*c,btau=(540000*27000/567000+1000)*10e-9;
    let gain=t=>f.map(x=>-10*Math.log10(1+(2*pi*x*t)**2)),phase=t=>f.map(x=>-Math.atan(2*pi*x*t)*180/pi);
    let bus=gain(btau),hyp=gain(tau),optional=f.map(x=>{
      let w=2*pi*x*28000*47e-12,den=1+w*w;
      return 20*Math.log10(Math.hypot((1+28/den)/29,(-28*w/den)/29));
    });
    return {f,bus,hyp,optional,phase:phase(tau),totalPhase:f.map((x,j)=>phase(tau)[j]-360*x*delay),fc:1/(2*pi*tau),btau};
  }
  const api={add,inv,abs,capZ,parallel,lin,log,mean,rms,halfBridge,pulse,bank,impedance,transient,filters};
  if(typeof module!=='undefined')module.exports=api;else root.LabModels=api;
})(typeof window!=='undefined'?window:globalThis);
