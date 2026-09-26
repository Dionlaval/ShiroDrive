from pathlib import Path
import sys,copy,json,zipfile,hashlib,math
sys.path.insert(0,'/tmp/cascade_work')
from edit import *
P=Path(__file__).resolve().parents[2];OUT=P/'review/brake_ntc';S=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols')
backup=OUT/'before.zip'
assert not backup.exists(),'Already applied; do not rerun'
paths=list(P.glob('*.kicad_sch'))+[P/'ShiroFOC_Manual.kicad_pcb',P/'ShiroFOC_Manual.kicad_pro',P/'libs/Manual.kicad_sym',P.parent/'requirements/FIRMWARE_REQUIREMENTS.md']
with zipfile.ZipFile(backup,'w',zipfile.ZIP_DEFLATED) as z:
 for path in paths:z.write(path,str(path.relative_to(P.parent)))
(OUT/'before_hashes.json').write_text(json.dumps({str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths},indent=2))
# Change the functional-symbol pin types consistently in the project library and every embedded copy.
def pin_types(lib):
 for unit in children(lib,'symbol'):
  for pin in children(unit,'pin'):
   num=one(pin,'number')[1]
   if num=='11':pin[1]='input'
   elif num=='5':pin[1]='output'
for path in P.glob('*.kicad_sch'):
 d=read(path);changed=False
 for lib in children(one(d,'lib_symbols') or [],'symbol'):
  if lib[1]=='Manual:STSPIN32G4_Functional':pin_types(lib);changed=True
 if changed:write(path,d)
lp=P/'libs/Manual.kicad_sym';d=read(lp)
for lib in children(d,'symbol'):
 if lib[1]=='STSPIN32G4_Functional':pin_types(lib)
write(lp,d)
def wire(d,a,b):
 d.append(['wire',['pts',['xy',*map(str,a)],['xy',*map(str,b)]],['stroke',['width','0'],['type','default']],['uuid',uid()]])
def label(d,name,xy,glob=False,angle=0):
 x=['global_label' if glob else 'label',Q(name)]
 if glob:x.append(['shape','bidirectional'])
 x += [['at',*map(str,xy),str(angle)],['effects',['font',['size','1.016','1.016']],['justify','left' if angle==0 else 'right']+([] if glob else ['bottom'])],['uuid',uid()]]
 d.append(x)
def text(d,t,xy,size=1.27):d.append(['text',Q(t),['at',*map(str,xy),'0'],['effects',['font',['size',str(size),str(size)]],['justify','left','top']],['uuid',uid()]])
def junction(d,xy):d.append(['junction',['at',*map(str,xy)],['diameter','0'],['color','0','0','0','0'],['uuid',uid()]])
# Relocate the existing LED drawing into the free right-hand area; physical LED placement unchanged.
p=P/'MCUclockSWD.kicad_sch';d=read(p)
for refname in ['D301','R304','#PWR03Controller8']:shift(ref(d,refname),116.84,0)
for w in list(children(d,'wire')):
 pts=[tuple(map(float,x[1:])) for x in children(one(w,'pts'),'xy')]
 if pts==[(163.83,99.06),(175.26,99.06)]:d.remove(w)
 elif pts in [[(185.42,99.06),(201.93,99.06)],[(212.09,92.71),(212.09,99.06)]]:shift(w,116.84,0)
for l in children(d,'label'):
 if l[1]=='SPARE_GPIO_1':l[1]=Q('STATUS_LED_N')
wire(d,(283.21,99.06),(292.1,99.06));label(d,'STATUS_LED_N',(283.21,99.06))
wire(d,(163.83,99.06),(179.07,99.06));label(d,'NTC_BRAKE',(179.07,99.06),True)
text(d,'STATUS LED: PC15, active low / open drain.\nR304 limits LED sink current; keep LSE disabled.\nPC2 is now ADC12_IN8 for the external brake NTC.',(279.4,109.22),1.016)
# 2.2k bounds LED current below 1.65mA even with a shorted LED, leaving room for PC14.
update(ref(d,'R304'),'Value','2.2k');pr=prop(ref(d,'R304'),'Procurement')
if pr:pr[2]=Q('2.2k 1%, 0603; low-current active-low status LED')
write(p,d)
# New block on brake sheet.
p=P/'07_Brake_Chopper.kicad_sch';d=read(p);libstore=one(d,'lib_symbols');root=one(read(P/'ShiroFOC_Manual.kicad_sch'),'uuid')[1];sheet=one(d,'uuid')[1]
def std(lib,name):
 id=lib+':'+name
 if not any(x[1]==id for x in children(libstore,'symbol')):
  x=copy.deepcopy(next(x for x in children(read(S/(lib+'.kicad_sym')),'symbol') if x[1]==name));assert not one(x,'extends');x[1]=Q(id);libstore.append(x)
 return id
new=[]
def component(lib,name,r,v,xy,fp,angle=0,mpn='',ds=''):
 id=std(lib,name);x=['symbol',['lib_id',Q(id)],['at',*map(str,xy),str(angle)],['unit','1'],['in_bom','yes'],['on_board','yes'],['dnp','no'],['uuid',uid()]]
 for key,value,offset,hide in [('Reference',r,-5.08,False),('Value',v,-2.54,False),('Footprint',fp,0,True),('Datasheet',ds,0,True),('MPN',mpn,0,True)]:
  x.append(['property',Q(key),Q(value),['at',str(xy[0]+(5.08 if name in ['R','C'] and angle==0 else 0)),str(xy[1]+offset),'0'],['effects',['font',['size','1.016','1.016']]]+([['hide','yes']] if hide else [])])
 x.append(['instances',['project',Q('ShiroFOC_Manual'),['path',Q('/'+root+'/'+sheet),['reference',Q(r)],['unit','1']]]]);d.append(x);new.append({'ref':r,'footprint':fp,'uuid':one(x,'uuid')[1],'sheet':sheet});return x
# connector rotated 180: pin1 at x+5.08,y; pin2 at x+5.08,y-2.54
component('Connector_Generic','Conn_01x02','J502','BRAKE NTC',(218.44,212.09),'Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal',180,'SM02B-GHS-TB(LF)(SN)')
component('Device','R','R511','10k 1%',(241.3,198.12),'Resistor_SMD:R_0603_1608Metric')
component('Device','R','R512','4.7k 1%',(266.7,212.09),'Resistor_SMD:R_0603_1608Metric',90)
component('Device','C','C505','100nF 16V',(289.56,224.79),'Capacitor_SMD:C_0603_1608Metric')
component('Diode','BAT54S','D505','BAT54S',(320.04,212.09),'Package_TO_SOT_SMD:SOT-23',90,'BAT54S,215','https://assets.nexperia.com/documents/data-sheet/BAT54S.pdf')
# 3V3 divider -> series resistor -> filtered/clamped ADC. BAT54S rotated90:1bottom(GND),2top(3V3),3right(signal).
for a,b in [((223.52,212.09),(241.3,212.09)),((241.3,212.09),(262.89,212.09)),((241.3,201.93),(241.3,212.09)),((241.3,190.5),(241.3,194.31)),((270.51,212.09),(289.56,212.09)),((289.56,212.09),(289.56,220.98)),((289.56,228.6),(289.56,232.41)),((289.56,212.09),(297.18,212.09)),((297.18,212.09),(297.18,236.22)),((297.18,236.22),(332.74,236.22)),((332.74,236.22),(332.74,212.09)),((325.12,212.09),(332.74,212.09)),((332.74,212.09),(347.98,212.09)),((320.04,204.47),(320.04,190.5)),((320.04,219.71),(320.04,232.41)),((223.52,209.55),(228.6,209.55)),((228.6,209.55),(228.6,232.41))]:wire(d,a,b)
for xy in [(241.3,212.09),(289.56,212.09),(332.74,212.09)]:junction(d,xy)
label(d,'NTC_BRAKE',(347.98,212.09),True)
label(d,'BRAKE_NTC_RAW',(241.3,212.09))
# Existing project power symbols, cloned into sheet.
for template,r,xy in [('#PWR05BrakeChopper10','#PWR_BRAKE_NTC_1',(241.3,190.5)),('#PWR05BrakeChopper10','#PWR_BRAKE_NTC_2',(320.04,190.5)),('#PWR05BrakeChopper9','#PWR_BRAKE_NTC_3',(228.6,232.41)),('#PWR05BrakeChopper9','#PWR_BRAKE_NTC_4',(289.56,232.41)),('#PWR05BrakeChopper9','#PWR_BRAKE_NTC_5',(320.04,232.41))]:d.append(clone(ref(d,template),r,xy))
for t in children(d,'text'):
 if t[1]=='Internal 1.242 V reference returns directly to IN−.':one(t,'at')[1:3]=['25.4','231.14']
 elif t[1]=='The positive-feedback resistor is wired back to IN+.':one(t,'at')[1:3]=['25.4','224.79']
text(d,'OPTIONAL EXTERNAL BRAKE-RESISTOR TEMPERATURE',(210.82,180.34),1.27)
text(d,'10k NTC at 25C; configure the actual probe curve in firmware.\nJ502: 1 = NTC, 2 = GND. Probe insulated from resistor power terminals.',(210.82,168.91),1.016)
text(d,'Open = high; short = low. Filter/clamps at MCU; twist probe pair.\nThermal warning/derating only: do not disable hardware bus clamp on overtemperature.',(190.5,271.78),1.016)
write(p,d)
(OUT/'new_components.json').write_text(json.dumps(new,indent=2));print('Added brake NTC schematic block; PC2 ADC / PC15 LED remap; five PCB components')
