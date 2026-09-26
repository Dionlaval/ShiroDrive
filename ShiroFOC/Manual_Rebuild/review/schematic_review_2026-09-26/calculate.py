from pathlib import Path
import json,math,re,xml.etree.ElementTree as E,subprocess
p=Path(__file__).resolve().parent
x=E.parse(p/'netlist.xml');cs={c.get('ref'):c for c in x.findall('.//components/comp')}
def v(r):
 s=cs[r].findtext('value');m=re.match(r'([\d.]+)\s*([kMuµnm]?)',s);return float(m[1])*{'':1,'k':1e3,'M':1e6,'u':1e-6,'µ':1e-6,'n':1e-9,'m':1e-3}[m[2]]
def ov(top):
 bot=v('R211');lo=top*.99;hi=top*1.01;bhi=bot*1.01;blo=bot*.99
 return [1.01*(1+lo/bhi)-.1e-6*lo,1.06*(1+top/bot),1.1*(1+hi/blo)+.1e-6*hi]
r={'mux_ov_existing_V':ov(v('R210')),'mux_ov_22k_candidate_V':ov(22000),'10V_nominal':1*(1+v('R201')/v('R202')),'5V_nominal':.798*(1+v('R216')/v('R217')),'current_V_per_A':28*.0005,'current_zero_V':1.65,'current_25Arms_peak_outputs_V':[1.65-25*2**.5*.014,1.65+25*2**.5*.014],'OPP_zero_V':3.3/58,'OPP_V_per_A':28/29*.0005,'VM_ratio':27/(540+27),'VM_tau_s':(540e3*27e3/(540e3+27e3)+1000)*10e-9,'NTC25_filter_Hz':1/(2*math.pi*(4700*10000/(4700+10000)+1000)*10e-9),'bulk_energy_42V_J':.5*2040e-6*42**2}
(p/'calculations.json').write_text(json.dumps(r,indent=2))
# Reconstruct loaded networks rather than trust automatic isolated pairs.
cir='''Actual network DC checks, ideal amplifier, not switching/short-circuit validation
Vref ref 0 3.3
Vsense sp 0 0
Rplus sp pp 1k
Rbias ref pp 56k
Rbiasg pp 0 56k
Rminus 0 pn 1k
Rfeedback out pn 28k
Eamp out 0 pp pn 1e8
Vvm vm 0 42
Rvm1 vm vma 270k
Rvm2 vma vmb 270k
Rvm3 vmb 0 27k
Rvm4 vmb vmadc 1k
Cvm vmadc 0 10n
Rntct ref ntc 4.7k
Rntc ntc 0 10k
Rntcf ntc ntcadc 1k
Cntc ntcadc 0 10n
Vbuck10 buck10 0 10.009009009
Rf10 buck10 fb10 100k
Rb10 fb10 0 11.1k
Vbuck5 buck5 0 4.978585516
Rf5 buck5 fb5 34k
Rb5 fb5 0 6.49k
Vbrake bus 0 45.91942322834647
Vcmd cmd 0 0
Rbr1 bus a 150k
Rbr2 a b 150k
Rbr3 b sense 150k
Rbr4 sense 0 12.7k
Rbr5 cmd sense 1meg
.control
op
print v(out) v(pp) v(vmadc) v(ntcadc) v(fb10) v(fb5) v(sense)
alter Vsense 0.01767766953
op
print v(out) v(pp)
alter Vsense -0.01767766953
alter Vbrake 44.21312480314962
alter Vcmd 3.3
op
print v(out) v(pp) v(sense)
quit
.endc
.end
'''
(p/'actual_networks.cir').write_text(cir)
z=subprocess.run(['/Users/dionlava/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3','/Users/dionlava/Documents/GitHub/ShiroDrive/ShiroFOC/tools/ngspice_local.py',str(p/'actual_networks.cir')],text=True,capture_output=True)
(p/'actual_networks.log').write_text(z.stdout+z.stderr)
print(json.dumps(r,indent=2));print(z.stdout[-3200:])
