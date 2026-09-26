"""Rebuild the ShiroFOC teaching figures/data. Not a hardware qualification model.
Run from any directory: python learning/models/build_models.py
Dependencies: numpy, scipy, matplotlib. All electrical quantities internally SI.
"""
from pathlib import Path
import csv, hashlib, json, math, os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/shiro-learning-mpl')
import numpy as np
from scipy import signal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
DATA, FIG = ROOT/'data', ROOT/'figures'
for p in (DATA, FIG): p.mkdir(exist_ok=True)
plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False,
                     'figure.dpi': 130, 'savefig.dpi': 170, 'axes.grid': True, 'grid.alpha': .18})
COLORS = ['#007f86', '#c75527', '#7259a3', '#32794e', '#af3863']

def savefig(name):
    plt.savefig(FIG/(name+'.png'), bbox_inches='tight')
    plt.savefig(FIG/(name+'.svg'), bbox_inches='tight')
    plt.close()

def csvout(name, headers, rows):
    with (DATA/name).open('w', newline='') as f:
        w=csv.writer(f); w.writerow(headers); w.writerows(rows)

def cap_z(f, c, r, l):
    w=2j*np.pi*np.asarray(f)
    return r+w*l+1/(w*c)

def network(f, branches, rs=.05, ls=1e-6):
    zs=rs+2j*np.pi*f*ls
    zc=[cap_z(f, **b) for b in branches]
    z=1/(1/zs+sum(1/x for x in zc))
    return z,zs,zc

def ceramic(n, retention=.5, connection_nh=3):
    # Illustrative part ESR/ESL and shared connection, not Murata part data.
    return dict(c=n*4.7e-6*retention, r=.02/n+.001, l=1e-9/n+connection_nh*1e-9)

SCENARIOS = {
 'Existing bulk + local': [dict(c=2040e-6,r=.01,l=23e-9),dict(c=7.81e-6*.5,r=.005,l=3e-9)],
 '20 ceramics': [ceramic(20)],
 '40 ceramics': [ceramic(40)],
 '80 ceramics': [ceramic(80)],
 '40 ceramics + 1000uF': [ceramic(40),dict(c=1000e-6,r=.03,l=30e-9)],
}

def three_phase(steps_per_pwm=512):
    fsw,fe,irms,m,phi=20000,250,40,.8,np.deg2rad(30)
    n=80*steps_per_pwm
    t=np.arange(n)/(fsw*steps_per_pwm)
    phase=2*np.pi*fe*t[:,None]-np.array([0,2*np.pi/3,4*np.pi/3])
    currents=irms*np.sqrt(2)*np.cos(phase-phi)
    duties=.5+.5*m*np.cos(phase)
    carrier=2*np.abs((t*fsw)%1-.5)
    q=(carrier[:,None]<duties).astype(float)
    load=(q*currents).sum(axis=1)
    # Finite edge proxy: first-order 80 ns time constant. This is not MOSFET switching physics.
    # Exact sampled first-order recurrence; settle one periodic pass first.
    # Unlike truncating a continuous-time filter spectrum, this cannot create
    # artificial undershoot outside the supplied current levels.
    a=np.exp(-(t[1]-t[0])/80e-9)
    previous=0.
    for value in load: previous=a*previous+(1-a)*value
    smooth=np.empty_like(load)
    for j,value in enumerate(load):
        previous=a*previous+(1-a)*value;smooth[j]=previous
    load=smooth;f=np.fft.rfftfreq(n,t[1]-t[0]);fft=np.fft.rfft(load)
    return t,load,f,fft,currents,q

def periodic_result(branches, steps=512):
    t,load,f,F,_,_=three_phase(steps)
    z,zs,zc=network(f[1:],branches)
    VF=np.zeros(len(F),complex)
    VF[0]=(36-.05*load.mean())*len(t)
    VF[1:]=-z*F[1:]
    v=np.fft.irfft(VF,len(t))
    branch_curr=[]
    for zz in zc:
        cf=np.zeros_like(F); cf[1:]=VF[1:]/zz
        branch_curr.append(np.fft.irfft(cf,len(t)))
    source=load+sum(branch_curr)
    rms=[float(np.sqrt(np.mean(i*i))) for i in branch_curr]
    return t,v,load,source,branch_curr,{
      'bus_pp_V':float(np.ptp(v)), 'bus_min_V':float(v.min()), 'bus_max_V':float(v.max()),
      'input_mean_A':float(load.mean()), 'branch_rms_A':rms,
      'estimated_ESR_loss_W':float(sum(i*i*b['r'] for i,b in zip(rms,branches))),
      'effective_C_uF':sum(b['c'] for b in branches)*1e6}

def rlc_response(c=94e-6, rc=.0015, rs=.05, ls=1e-6, vs=36, step_a=20, startup=False):
    # States [cable current, ideal capacitor voltage]. No capacitor ESL in this model.
    A=np.array([[-(rs+rc)/ls,-1/ls],[1/c,0]])
    B=np.array([[1/ls,rc/ls],[0,-1/c]])
    C=np.array([[rc,1],[1,0]])
    D=np.array([[0,-rc],[0,0]])
    t=np.linspace(0,.002,4001)
    u=np.column_stack([np.full(len(t),vs),np.full(len(t),0 if startup else step_a)])
    _,out,_=signal.lsim((A,B,C,D),u,t,X0=[0,0 if startup else vs])
    return t,out

def half_bridge(v=36,d=.5,fsw=20000,l=100e-6,r=.1,mean_i=20):
    # Buck-equivalent R-L-back-EMF load, exact periodic solution, positive current convention.
    T=1/fsw; emf=d*v-r*mean_i; tau=l/r
    a=np.exp(-d*T/tau); b=np.exp(-(1-d)*T/tau)
    ion=(v-emf)/r; ioff=-emf/r
    i0=(ioff*(1-b)+ion*(1-a)*b)/(1-a*b)
    ih=ion+(i0-ion)*a
    t=np.arange(1800)/600*T; local=t%T
    q=(local<d*T).astype(float)
    cur=np.where(q>0,ion+(i0-ion)*np.exp(-local/tau),ioff+(ih-ioff)*np.exp(-(local-d*T)/tau))
    return t,q*v,cur,q*cur,emf

def build():
    source=PROJECT/'ShiroFOC/ShiroFOC_KiCad/outputs/revision_P1/netlist.xml'
    analysis=json.loads((DATA/'schematic_analysis.json').read_text())
    refs=['C101','C102','C103','C104','C105','C106','C108','R103','R104','R105','R106',
          'C301','C302','C303','C304','C305','C306','C307','C312','C313',
          'C411','C412','C414','C415','R411','R412','R416','R417','R418','R419','R410','R441','U301']
    components={c['reference']:{k:c.get(k) for k in ('value','mpn','dnp','pin_nets')}
                for c in analysis['components'] if c['reference'] in refs}
    inputs={'snapshot':'2026-09-19','scope':'Educational model of P1 schematic / P0 unrouted placement',
      'components':components,
      'design_targets':{'bus_V':[18,42],'phase_continuous_Arms':[25,40], 'short_peak_A':80,
        'initial_PWM_Hz':20000,'current_gain':28,'shunt_ohm':.0005,'ADC_reference_V':3.3,
        'initial_deadtime_s':500e-9,'brake_firmware_start_V':43,'brake_nominal_hardware_rise_V':45.9194},
      'assumptions':{'example_bus_V':36,'motor_R_ohm':.1,'motor_L_H':100e-6,
        'supply_loop_R_ohm':.05,'supply_loop_L_H':1e-6,'ceramic_retention_fraction':.5,
        'ceramic_ESR_per_part_ohm':.02,'ceramic_ESL_per_part_H':1e-9,
        'shared_bank_connection_L_H':3e-9,'shared_bank_connection_R_ohm':.001,
        'electrolytic_ESR_per_680uF_ohm':.03,'current_edge_filter_tau_s':80e-9,
        'three_phase_modulation_index':.8,'three_phase_displacement_deg':30,'electrical_frequency_Hz':250},
      'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
      'source':'ShiroFOC/ShiroFOC_KiCad/outputs/revision_P1/netlist.xml',
      'warning':'ESR/ESL, motor, cable and ceramic retention are assumed; no extracted routed parasitics or measured curves.'}
    (DATA/'board_inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')

    t,v,i,load,e=half_bridge(); ic=load.mean()-load
    fig,axs=plt.subplots(3,1,figsize=(10,8),sharex=True)
    axs[0].plot(t*1e6,v,color=COLORS[0]);axs[0].set_ylabel('Switch node (V)')
    axs[1].plot(t*1e6,i,label='Winding',color=COLORS[0]);axs[1].plot(t*1e6,load,label='Bridge bus draw',color=COLORS[1]);axs[1].legend();axs[1].set_ylabel('Current (A)')
    axs[2].plot(t*1e6,ic,color=COLORS[2]);axs[2].set_ylabel('Into capacitor (A)');axs[2].set_xlabel('Time (µs)')
    fig.suptitle('One half bridge: smooth winding current, pulsed bus demand\n36 V · 20 kHz · D=0.5 · 100 µH · 0.1 Ω · 20 A mean; example load')
    fig.tight_layout();savefig('01_half_bridge')
    csvout('half_bridge.csv',['time_s','switch_V','winding_A','bridge_A','capacitor_A'],zip(t,v,i,load,ic))

    f=np.logspace(1,8,1800)
    fig,axs=plt.subplots(2,1,figsize=(10,8),sharex=True)
    for (name,b),color in zip(SCENARIOS.items(),COLORS):
        z,_,_=network(f,b);axs[0].loglog(f,abs(z),label=name,color=color)
        axs[1].semilogx(f,np.angle(z,deg=True),color=color)
    axs[0].set_ylabel('|Bus impedance| (Ω)');axs[0].legend(ncol=2)
    axs[1].set_ylabel('Impedance phase (°)');axs[1].set_xlabel('Frequency (Hz)')
    fig.suptitle('How much voltage disturbance does one amp create?\nAssumed R/L and 50% ceramic capacitance retention; values are examples')
    fig.tight_layout();savefig('02_bus_impedance')

    results={};fig,axs=plt.subplots(2,1,figsize=(10,8))
    for (name,b),color in zip(SCENARIOS.items(),COLORS):
        t,v,load,src,bc,metrics=periodic_result(b);results[name]=metrics
        mask=(t>=.001)&(t<.00115)
        axs[0].plot((t[mask]-.001)*1e6,v[mask],label=name,color=color)
        csvout('pwm_'+name.lower().replace(' ','_').replace('+','plus')+'.csv',
               ['time_s','bus_V','bridge_A','source_A']+['cap_branch_%d_A'%j for j in range(len(bc))],
               zip(t[::8],v[::8],load[::8],src[::8],*[j[::8] for j in bc]))
    axs[0].set_ylabel('Bus voltage (V)');axs[0].set_xlabel('Time in selected 3 PWM periods (µs)');axs[0].legend(fontsize=9,ncol=2)
    for name,color in [('Existing bulk + local',COLORS[0]),('40 ceramics',COLORS[2])]:
        t,v,load,src,bc,metrics=periodic_result(SCENARIOS[name]);mask=(t>=.001)&(t<.00115)
        axs[1].plot((t[mask]-.001)*1e6,src[mask],label='Cable: '+name,color=color)
    axs[1].plot((t[mask]-.001)*1e6,load[mask],label='Bridge draw',alpha=.6,color='#666666')
    axs[1].set_ylabel('Current (A)');axs[1].set_xlabel('Time (µs)');axs[1].legend(fontsize=9)
    fig.suptitle('Three-phase SPWM example: 40 Arms, m=0.8, 30° displacement\n36 V source · 20 kHz PWM · 250 Hz electrical · 0.05 Ω / 1 µH cable loop')
    fig.tight_layout();savefig('03_capacitor_comparison')
    (DATA/'comparison.json').write_text(json.dumps(results,indent=2)+'\n')
    (DATA/'comparison.js').write_text('window.ComparisonData = '+json.dumps(results,indent=2)+';\n')
    csvout('comparison.csv',['scenario','effective_C_uF','bus_pp_V','bus_min_V','bus_max_V','input_mean_A','estimated_ESR_loss_W'],
           [[k]+[v[x] for x in ['effective_C_uF','bus_pp_V','bus_min_V','bus_max_V','input_mean_A','estimated_ESR_loss_W']] for k,v in results.items()])

    fig,axs=plt.subplots(1,2,figsize=(12,4.8))
    for c,rc,label in [(94e-6,.0015,'94 µF ceramic example'),(2040e-6,.01,'2040 µF bulk example')]:
        for j,start in enumerate([False,True]):
            t,out=rlc_response(c,rc,startup=start);axs[j].plot(t*1e3,out[:,0],label=label)
    for a in axs:a.set_xlabel('Time (ms)');a.set_ylabel('Bus voltage (V)');a.legend(fontsize=9)
    axs[0].set_title('20 A load step, initially charged');axs[1].set_title('Uncharged connection to 36 V')
    fig.suptitle('Same cable R/L, two different events — linear model without clamps')
    fig.tight_layout();savefig('04_step_and_connection')

    fig,axs=plt.subplots(1,2,figsize=(12,4.8))
    for l,lab in [(3,'Short connection: 3 nH shared'),(30,'Longer connection: 30 nH shared')]:
        z=cap_z(f,**ceramic(40,connection_nh=l));axs[0].loglog(f,abs(z),label=lab)
    axs[0].set_xlabel('Frequency (Hz)');axs[0].set_ylabel('|Capacitor branch impedance| (Ω)');axs[0].legend(fontsize=9)
    tr=np.linspace(20,250,400)
    for l in [3,10,30]:axs[1].plot(tr,l*40/tr,label=f'{l} nH at 40 A transition')
    axs[1].set_xlabel('Current transition time (ns)');axs[1].set_ylabel('L × ΔI / Δt (V)');axs[1].legend(fontsize=9)
    fig.suptitle('Placement changes connection inductance; more capacitance cannot remove it')
    fig.tight_layout();savefig('05_placement_inductance')

    f=np.logspace(1,6,900);tau=((540000*27000)/(540000+27000)+1000)*10e-9
    Hbus=1/(1+2j*np.pi*f*tau)
    # Optional feedback capacitor: exact ideal-opamp signal path when sense-minus is fixed.
    Hcurrent=(28/29)*(1+28/(1+2j*np.pi*f*28000*47e-12))/28
    Hexample=1/(1+2j*np.pi*f*1000*10e-9)
    fig,axs=plt.subplots(2,1,figsize=(10,8),sharex=True)
    for h,label,c in [(Hbus,'Actual bus filter (DC-normalised)',COLORS[0]),(Hcurrent,'Optional 47 pF feedback, NOT fitted',COLORS[1]),(Hexample,'Illustrative 1 kΩ / 10 nF low-pass',COLORS[2])]:
        axs[0].semilogx(f,20*np.log10(abs(h)),label=label,color=c)
        axs[1].semilogx(f,np.angle(h,deg=True),color=c)
    axs[0].set_ylabel('Normalised magnitude (dB)');axs[0].legend(fontsize=9)
    axs[1].set_ylabel('Phase (°)');axs[1].set_xlabel('Frequency (Hz)')
    fig.suptitle('Three different circuits — do not confuse the bus filter with current sensing')
    fig.tight_layout();savefig('06_sensing_filters')

    # Sampling edge artifact, not an extracted waveform.
    t=np.linspace(0,50e-6,5001);truth=20+.8*np.sin(2*np.pi*t/50e-6)
    noise=np.zeros_like(t)
    for edge in [5e-6,30e-6]:
        dt=t-edge;noise+=np.where(dt>=0,3*np.exp(-np.maximum(dt,0)/1e-6)*np.cos(2*np.pi*2e6*dt),0)
    fig,ax=plt.subplots(figsize=(10,4.5));ax.plot(t*1e6,truth,label='Underlying current');ax.plot(t*1e6,truth+noise,label='Illustrative measurement artifact',alpha=.8)
    for pos,col in [(5.1,COLORS[1]),(20,COLORS[3])]:
        ix=np.argmin(abs(t-pos*1e-6));ax.scatter(pos,(truth+noise)[ix],color=col,s=55,zorder=4)
    ax.set(xlabel='Time within PWM period (µs)',ylabel='Current reading (A)',title='Sampling time can matter more than adding another filter');ax.legend()
    savefig('07_sampling')

    # Real P0 component centres; overview drawing is NOT copper or a proposed route.
    placement=json.loads((PROJECT/'ShiroFOC/ShiroFOC_KiCad/outputs/placement/placement_manifest.json').read_text())['components']
    fig,axs=plt.subplots(1,2,figsize=(12,6.5))
    highlights={'C101','C102','C103','Q401','Q402','Q403','J401','U301','U601','R416','R426','R436','C412','C422','C432','J101','U201','L201','L301'}
    for ax,side,title in zip(axs,['F','B'],['Top: existing P0 placement','Bottom: viewed through board from top']):
        ax.add_patch(FancyBboxPatch((0,0),80,80,boxstyle='round,pad=0,rounding_size=5',fill=False,lw=1.5))
        for ref,p in placement.items():
            if p['side']!=side:continue
            x,y=p['x_mm'],p['y_mm'];ax.scatter(x,y,s=8,color='#aab4bb',alpha=.7)
            if ref in highlights:
                ax.scatter(x,y,s=55,color=COLORS[0]);ax.annotate(ref,(x,y),xytext=(0,6),textcoords='offset points',ha='center',fontsize=9)
            if ref in ['C101','C102','C103']:ax.add_patch(Circle((x,y),9,fill=False,color=COLORS[1],lw=1))
        ax.set(xlim=(-3,83),ylim=(83,-3),aspect='equal',xlabel='Board-local x (mm)',ylabel='Board-local y (mm)',title=title)
    fig.suptitle('Actual component centres, schematic placement overview\nUnrouted · 80 × 80 mm · P1 changes and mounting holes still pending on PCB')
    fig.tight_layout();savefig('08_actual_placement')

    # Hypothetical curves: parameterised sensitivity, NOT an extracted part curve.
    vb=np.linspace(0,54,300);fig,ax=plt.subplots(figsize=(10,4.5))
    for retention in [.2,.5,.8]:
        effective=188/(1+(1/retention-1)*(vb/42)**2)
        ax.plot(vb,effective,label=f'Assumed {retention:.0%} retention at 42 V')
    ax.axvline(42,color='#777777',lw=1,ls=':')
    ax.set(xlabel='Applied DC voltage (V)',ylabel='Effective bank capacitance (µF)',title='Illustrative bias sensitivity: 40 × 4.7 µF nominal\nCurve family chosen for teaching; not data for a real MPN')
    ax.legend();savefig('09_bias_sensitivity')

    # Sensitivity around 40-ceramic example: shifting resonance can change ranking.
    sensitivity=[]
    for retention in [.2,.5,.8,1.0]:
        for cable_l in [.2e-6,1e-6,3e-6]:
            tt,ll,ff,FF,_,_=three_phase();bb=[ceramic(40,retention)]
            zz,_,_=network(ff[1:],bb,ls=cable_l)
            vf=np.zeros_like(FF);vf[0]=(36-.05*ll.mean())*len(tt);vf[1:]=-zz*FF[1:]
            vv=np.fft.irfft(vf,len(tt));sensitivity.append([retention,cable_l*1e6,float(np.ptp(vv))])
    csvout('sensitivity.csv',['retention_fraction','cable_loop_uH','bus_pp_V'],sensitivity)
    fig,ax=plt.subplots(figsize=(9,4.5))
    for retention in [.2,.5,.8,1.0]:
        rr=[x for x in sensitivity if x[0]==retention];ax.plot([x[1] for x in rr],[x[2] for x in rr],marker='o',label=f'{retention:.0%} retention')
    ax.set(xlabel='Assumed cable loop inductance (µH)',ylabel='Bus variation (V p-p)',title='Sensitivity of the 40-ceramic study case\nSame prescribed three-phase current; high-ripple cases exceed small-ripple model credibility')
    ax.legend();savefig('10_sensitivity')

    # Input power path diagram.
    fig,ax=plt.subplots(figsize=(12,4.8));ax.set(xlim=(0,12),ylim=(-.7,4.8));ax.axis('off')
    for x,y,w,h,txt in [(0.2,1.5,1.6,1,'Battery\n18–42 V'),(2.5,1.5,1.8,1,'Cable loop\nR + L'),(7,1.5,2,1,'3 half bridges\nQ401–403'),(10,1.5,1.7,1,'Motor\nR, L, back EMF'),(4.5,.1,2,1,'DC-link capacitors\nVM ↔ GND'),(7,3,2,0.8,'Brake chopper\nexternal resistor')]:
        ax.add_patch(Rectangle((x,y),w,h,fill=False,color=COLORS[0],lw=1.4));ax.text(x+w/2,y+h/2,txt,ha='center',va='center')
    for a,b in [((1.8,2),(2.5,2)),((4.3,2),(7,2)),((9,2),(10,2)),((5.5,1.1),(5.5,2)),((6,2),(8,3))]:ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'<->','color':COLORS[1]})
    ax.text(.2,4.4,'Energy can flow both ways. The capacitor supplies brief differences between source and bridge current.',fontsize=11)
    ax.text(.2,-.5,'Logic supplies branch from VM: 5 V buck → power mux → 3.3 V LDO; gate drive uses STSPIN VCC.',fontsize=10)
    savefig('00_power_path')

    # Validation: independent identities, conservation, and discretisation sensitivity.
    t,load,f,F,cur,q=three_phase()
    expected=3*.8*(40*np.sqrt(2))*np.cos(np.pi/6)/4
    tests={
      'three_phase_mean_current_error_fraction':abs(load.mean()-expected)/expected,
      'phase_current_sum_max_A':float(abs(cur.sum(axis=1)).max()),
      'half_bridge_mean_current_error_A':abs(float(i.mean())-20),
      'current_sense_V_per_A':28*.0005,
      'bus_filter_tau_s':tau,'bus_filter_fc_Hz':1/(2*np.pi*tau),
      'capacitor_energy_2040uF_42V_J':.5*2040e-6*42**2,
      'charge_formula_20A_D05_20kHz_100uF_pp_V':20*.5*.5/(20000*100e-6),
    }
    conv={}
    for name in ('40 ceramics','Existing bulk + local'):
        a=periodic_result(SCENARIOS[name],512);b=periodic_result(SCENARIOS[name],1024)
        conv[name]={'pp_512':a[-1]['bus_pp_V'],'pp_1024':b[-1]['bus_pp_V'],
          'relative_pp_difference':abs(a[-1]['bus_pp_V']-b[-1]['bus_pp_V'])/b[-1]['bus_pp_V'],
          'charge_balance_max_mean_A':float(max(abs(x.mean()) for x in a[4])),
          'KCL_residual_max_A':float(abs(a[3]-a[2]-sum(a[4])).max())}
    tests['resolution_check']=conv
    assert tests['three_phase_mean_current_error_fraction']<.01
    assert tests['phase_current_sum_max_A']<1e-10
    assert tests['half_bridge_mean_current_error_A']<.03
    for x in conv.values():assert x['relative_pp_difference']<.08 and x['KCL_residual_max_A']<1e-10
    (ROOT/'qa/numerical_checks.json').write_text(json.dumps(tests,indent=2)+'\n')
    print(json.dumps(results,indent=2));print('Numerical identities and resolution checks passed.')

if __name__=='__main__': build()
