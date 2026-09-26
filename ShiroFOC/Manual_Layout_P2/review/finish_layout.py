from pathlib import Path
import sys,json,copy,re,xml.etree.ElementTree as E
sys.path.insert(0,'/tmp/cascade_work');from edit import parse,dump,read,write,children,one,val,Q
P=Path(__file__).resolve().parents[1];board=P/'ShiroFOC_Manual.kicad_pcb';d=read(board)
# Preserve imported copper geometry; make its ownership explicit to KiCad.
def convert(f,netmap=None):
 count=0
 for poly in list(children(f,'fp_poly')):
  if one(poly,'layer')!=['layer','F.Cu']:continue
  points=children(one(poly,'pts'),'xy');cx=(min(float(q[1]) for q in points)+max(float(q[1]) for q in points))/2;cy=(min(float(q[2]) for q in points)+max(float(q[2]) for q in points))/2
  num='3' if cx<0 else '12'
  pts=[['xy',str(round(float(q[1])-cx,6)),str(round(float(q[2])-cy,6))] for q in points]
  pad=['pad',Q(num),'smd','custom',['at',str(cx),str(cy)],['size','.1','.1'],['layers',Q('F.Cu')],['options',['clearance','outline'],['anchor','rect']],['primitives',['gr_poly',['pts']+pts,['width','0'],['fill','yes']]]]
  # Custom pad primitives have their own orientation; match the footprint angle.
  if one(f,'at') and len(one(f,'at'))>3:one(pad,'at').append(one(f,'at')[3])
  if netmap is not None:pad.append(copy.deepcopy(netmap[num]))
  if one(poly,'uuid'):pad.append(copy.deepcopy(one(poly,'uuid')))
  f.remove(poly);f.append(pad);count+=1
 return count
lf=P/'libs/Manual.pretty/DMM0022A.kicad_mod';lib=read(lf);assert convert(lib)==4;write(lf,lib)
for f in children(d,'footprint'):
 if val(f,'Reference') in ['U1','U2','U3']:
  netmap={p[1]:one(p,'net') for p in children(f,'pad')};assert convert(f,netmap)==4
# Correct net-name escaping required by native KiCad PCB parity.
drc=json.loads((P/'review/drc.json').read_text());rename={}
for violation in drc.get('schematic_parity',[]):
 m=re.match(r'Pad net \((.*?)\) doesn.t match net given by schematic \((.*?)\)\.',violation['description'])
 if m:rename[m[1]]=m[2]
def walk(x):
 if isinstance(x,list):
  if x and x[0]=='net' and len(x)==3 and x[2] in rename:x[2]=Q(rename[x[2]])
  for a in x:walk(a)
walk(d)
comps={c.get('ref'):c for c in E.parse(P/'review/current.xml').findall('.//components/comp')}
for f in children(d,'footprint'):
 props={x.get('name') for x in comps[val(f,'Reference')].findall('property')};attr=one(f,'attr')
 if attr and 'exclude_from_bom' in attr and 'exclude_from_bom' not in props:attr.remove('exclude_from_bom')
write(board,d)
# Saving a board constructed from a temporary outline copied temporary project
# defaults; restore the explicit P1 rules now, without further native SaveBoard.
pf=P/'ShiroFOC_Manual.kicad_pro';pro=json.loads(pf.read_text());old=json.loads((P.parent/'ShiroFOC_KiCad_P1/ShiroFOC_KiCad.kicad_pro').read_text());pro['board']['design_settings']=old['board']['design_settings'];pro['net_settings']=old['net_settings']
patterns=pro['net_settings']['netclass_patterns'];patterns[:]=[x for x in patterns if not any(w in x['pattern'] for w in ['Q40','BOOT','SHUNT_*_FORCE'])]
for cl,pat in [('Gate','Net-(U*-GH)'),('Power','BOOTSTRAP*'),('Power','Net-(R*-POWER+)'),('Power','BRK_SW'),('LogicPower','10V*'),('LogicPower','*/EXT_VCC'),('LogicPower','*/EXT_SUPPLY_SELECTED')]:patterns.append({'netclass':cl,'pattern':pat})
pf.write_text(json.dumps(pro,indent=2)+'\n')
f=P/'ShiroFOC_Manual.kicad_dru';s=f.read_text();s+='\n(rule "U603 VSSOP internal pad spacing" (condition "A.memberOfFootprint(\'U603\') && B.memberOfFootprint(\'U603\')") (constraint clearance (min 0.15mm)))\n';f.write_text(s)
(P/'review/library_adjustments.json').write_text(json.dumps({'DMM0022A':'4 F.Cu graphic polygons converted to same-geometry custom pads 3/12; net assignment only; original Manual_Rebuild library unchanged','escaped_net_names':rename,'U604':'Standard SOT-23-6 assigned only in new layout revision'},indent=2))
print('Fixed net ownership/escaping, matched BOM flags, restored saved layout rules')
