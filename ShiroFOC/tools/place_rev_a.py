#!/usr/bin/env python3
"""Build the first unrouted floorplan with KiCad's native pcbnew footprint loader.
Run with KiCad's bundled Python. Existing output is backed up by the caller.
Coordinates are board-local millimetres; outline is 80 x 80 at (100,100).
This generator is for the initial placement only: do not rerun after manual routing.
"""
import json, math, re, csv, os, sys, xml.etree.ElementTree as E
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
PROJ=ROOT/'ShiroFOC_KiCad'; OUT=PROJ/'outputs/placement';OUT.mkdir(parents=True,exist_ok=True)
NET=Path(sys.argv[1]) if len(sys.argv)>1 else PROJ/'outputs/ShiroFOC_Rev_A.net'
STD=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
x=E.parse(NET).getroot(); comps={c.attrib['ref']:c for c in x.find('components')}
board=p.BOARD();board.SetCopperLayerCount(4)
mm=p.FromMM
vec=lambda x,y:p.VECTOR2I(mm(x),mm(y))
pos=lambda x,y:vec(100+x,100+y)
netmap={};pinmap={}
for n in x.find('nets'):
 name=n.attrib['name'];name=name.replace('/', '{slash}') if name.startswith(('Net-(','unconnected-(')) else name;net=p.NETINFO_ITEM(board,name);board.Add(net);netmap[name]=net
 for pin in n: pinmap[(pin.attrib['ref'],pin.attrib['pin'])]=name
fps={};placed={};groups={}; cached={}; boths={}
rootuuid=re.search(r'\(uuid "?([0-9a-f-]{36})', (PROJ/'ShiroFOC_KiCad.kicad_sch').read_text()).group(1)
for ref,c in comps.items():
 lib,name=c.findtext('footprint').split(':');folder=PROJ/'libs/ShiroFOC.pretty' if lib=='ShiroFOC_Footprints' else STD/(lib+'.pretty')
 f=p.FootprintLoad(str(folder),name);assert f is not None,ref
 f.SetAttributes(f.GetAttributes() & ~p.FP_EXCLUDE_FROM_BOM)
 f.SetReference(ref);f.SetValue(c.findtext('value'));f.SetFPID(p.LIB_ID(lib,name))
 f.SetPath(p.KIID_PATH('/'+rootuuid+c.find('sheetpath').attrib['tstamps']+c.findtext('tstamps').split()[0]))
 f.SetSheetname(c.find('sheetpath').attrib['names'])
 for pr in c.findall('property'):
  if pr.attrib['name']=='Sheetfile': f.SetSheetfile(pr.attrib.get('value',''))
 for field in c.findall('fields/field'):
  if field.attrib['name'] not in ['Footprint','Value','Reference']:f.SetField(field.attrib['name'],field.text or '')
 f.SetDNP(any(pr.attrib.get('name')=='dnp' for pr in c.findall('property')) or any(fl.attrib.get('name')=='Assembly' and fl.text=='DNP' for fl in c.findall('fields/field')))
 for pad in f.Pads():
  # U901 thermal vias: 0.45 mm pitch needs <=0.25 mm drills for 0.20 mm web.
  if ref=='U901' and pad.GetNumber()=='21' and pad.GetAttribute()==p.PAD_ATTRIB_PTH:
   pad.SetDrillSize(vec(.25,.25))
  n=pinmap.get((ref,pad.GetNumber()))
  if n:pad.SetNet(netmap[n])
 board.Add(f);fps[ref]=f
 f.Value().SetVisible(False)
 for field in f.GetFields():
  if field.GetName()!='Reference':field.SetVisible(False)

def bounds(f):
 layer=p.B_CrtYd if f.IsFlipped() else p.F_CrtYd
 boxes=[g.GetBoundingBox() for g in f.GraphicalItems() if g.GetLayer()==layer]
 if not boxes: boxes=[q.GetBoundingBox() for q in f.Pads()]
 return (min(b.GetLeft() for b in boxes)/1e6-100,min(b.GetTop() for b in boxes)/1e6-100,max(b.GetRight() for b in boxes)/1e6-100,max(b.GetBottom() for b in boxes)/1e6-100)
def physical_both(f):
 r=f.GetReference()
 if r not in boths:boths[r]=any(q.GetAttribute() in (p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH) for q in f.Pads())
 return boths[r]
def overlap(a,b,gap=.10):return a[0]<b[2]+gap and a[2]+gap>b[0] and a[1]<b[3]+gap and a[3]+gap>b[1]
def valid(f,ref):
 b=bounds(f)
 # Edge connectors may overhang only their assigned mating edge.
 if ref not in ['J101','J201'] and (min(b[:2])<1 or max(b[2:])>79):return False
 for r in placed:
  q=fps[r]
  qb,ql,qboth=cached[r]
  if f.GetLayer()==ql:
   if overlap(b,qb):return False
  elif qboth:
   for pad in q.Pads():
    if pad.GetAttribute() not in (p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH):continue
    pb=pad.GetBoundingBox(); bb=tuple(p.ToMM(z)-100 for z in (pb.GetLeft(),pb.GetTop(),pb.GetRight(),pb.GetBottom()))
    if overlap(b,bb,.15):return False
 # Provisional mounting hardware envelopes, no holes committed yet.
 for cx,cy in [(75,5),(5,75),(75,75)]:
  if overlap(b,(cx-3,cy-3,cx+3,cy+3),0):return False
 # Centre sensor environment; only encoder and its local passive circuit enter.
 if not ref.startswith(('U601','C601','C602','R601','R602','R603','R611','R308')):
  nx=max(b[0],min(40,b[2]));ny=max(b[1],min(40,b[3]))
  if math.hypot(nx-40,ny-40)<7.5:return False
 # Thermal through-vias below U301 must remain clear of bottom passives.
 if f.IsFlipped() and ref!='U601' and overlap(b,(51.7,42.7,56.3,47.3),.1):return False
 return True

def put(ref,x,y,angle=0,side='F',group=None,fixed=False):
 f=fps[ref]
 if side=='B' and not f.IsFlipped():f.Flip(f.GetPosition(),False)
 f.SetOrientationDegrees(angle);f.SetPosition(pos(x,y))
 if not fixed and not valid(f,ref):
  found=False
  for radius in [i*.5 for i in range(1,33)]:
   candidates=[]
   for dx in range(-int(radius*2),int(radius*2)+1):
    for dy in [-int(radius*2),int(radius*2)]:candidates.append((dx*.5,dy*.5))
   for dy in range(-int(radius*2)+1,int(radius*2)):
    for dx in [-int(radius*2),int(radius*2)]:candidates.append((dx*.5,dy*.5))
   for dx,dy in sorted(candidates,key=lambda z:z[0]**2+z[1]**2):
    f.SetPosition(pos(x+dx,y+dy))
    if valid(f,ref):found=True;break
   if found:break
  if not found:
   print('FAILED',ref,bounds(f));raise RuntimeError('No legal placement for '+ref)
 pxy=f.GetPosition();xx=p.ToMM(pxy.x)-100;yy=p.ToMM(pxy.y)-100
 placed[ref]={'ref':ref,'x_mm':round(xx,3),'y_mm':round(yy,3),'rotation_deg':angle,'side':side,'group':group or comps[ref].find('sheetpath').attrib['names'],'fixed_anchor':fixed}
 cached[ref]=(bounds(f),f.GetLayer(),physical_both(f))
 f.SetLocked(ref=='U601')
 f.Reference().SetTextSize(vec(.8,.8));f.Reference().SetTextThickness(mm(.12));f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
 f.Reference().SetLayer(p.B_Fab if side=='B' else p.F_Fab);f.Reference().SetMirrored(side=='B')
 for g in f.GraphicalItems():
  if isinstance(g,p.PCB_TEXT) and g.GetText() in ['${REFERENCE}','%R']:g.SetVisible(False)
 b=bounds(f);f.Reference().SetPosition(pos((b[0]+b[2])/2,b[1]-.65))

# Mechanical anchors and main components.
for args in [('U601',40,40,0,'B','Encoder'),('C101',12,12,90,'F','DC link'),('C102',34,12,90,'F','DC link'),('C103',56,12,90,'F','DC link'),('J401',75,14,270,'F','Phase outputs'),('J101',16,36,90,'F','DC input'),('J201',2.5,61,270,'F','USB service'),('U301',54,45,90,'F','MCU / gate driver')]:put(*args,fixed=True)
for i,cx in enumerate([24,38,52]):put(f'C{415+i*10}',cx-3.5,29,90,'F',fixed=True)
for i,cx in enumerate([24,38,52]):put('Q'+str(401+i),cx,29,180,'F',f'Phase {"UVW"[i]}',True)
# All three gate terminals face toward the MCU below the bridge bank.
for i,cx in enumerate([24,38,52]):
 n=410+i*10
 put('R'+str(n+6),cx,23,0,'B',f'Phase {"UVW"[i]} shunt',True)

 put('C'+str(n+2),cx,24,0,'F')
 put('R'+str(n+1),cx+2.5,33.3,90,'F')
 put('R'+str(n+2),cx-2.5,33.3,90,'F')
 put('R'+str(n+3),cx+5,32.0,90,'F')
 put('R'+str(n+4),cx-5,32.0,90,'F')
 put('C'+str(n+3),cx+5,27,90,'F')
 put('R'+str(n+5),cx+6,23,0,'F')
 put('TH'+str(701+i),cx+3.5,29,90,'B')
# Bootstrap at driver, not beside remote MOSFET.
for r,xx in [('C411',52),('C421',54),('C431',56)]:put(r,xx,38.5,90)
put('U602',54,35,0,'B','Feedback mux')
# Remaining large anchors, deliberately separate quiet and power sections.
for args in [('U201',10,45,0),('L201',20,44,0),('U203',16,54,0),('U204',24,54,0),('L301',46,56.5,180),('D302',44.8,50.5,180),('U701',33,58,0),('U901',12,62,0),('U801',33,69,180),('J601',54,74,180),('J801',27,75,180),('J802',39,75,180),('J1001',65,71,0),('Q501',70,54,180),('J501',73,63,270),('D504',74,47,90),('U501',64,54,180),('U502',63,61,0),('Y301',53,52.5,0),('SW301',60,66,0),('SW1001',14,74,0),('SW1002',15,68,0)]:put(*args)
# Pin-local underside decouplers; exposed-pad centre deliberately vacant.
for r,xx,yy,a in [('C301',50,48.5,90),('C302',48,47,90),('C303',59,44,0),('C304',59,42,0),('C305',61.5,44,0),('C306',61.5,42,0),('C307',48,47,90),('C310',54,49,90),('R301',60,40,0),('R302',62,40,0),('C108',57,49.5,90)]:put(r,xx,yy,a,'B','MCU underside')
# Analog feedback networks clustered at corresponding physical op-amp pins.
for i,(cx,cy) in enumerate([(56,52),(60,48),(63,45)]):
 n=410+i*10
 for r,dx,dy in [(f'R{n+7}',0,0),(f'R{n+8}',0,1.6),(f'R{n+9}',3.2,0),(f'C{n+4}',3.2,1.6),(f'R{n}',0,3.2),(f'R{441+i}',3.2,3.2)]:put(r,cx+dx,cy+dy,0,'B',f'Current sense {"UVW"[i]}')
for i in range(3):
 for prefix,base,xx in [('R',701,48),('R',711,51),('C',711,54)]:put(f'{prefix}{base+i}',xx,52+i*1.7,0,'B','Temperature ADC')
# Small groups with deliberate seeds; collision search only adjusts nearby.
seeds={
'C104':(18,25,0),'C105':(18,28,0),'C106':(18,31,0),'C107':(10,9,90),'D101':(11,17,0),'R101':(8,33,0),'R102':(18,10,90),
'R103':(26,40,90),'R104':(26,45,90),'R105':(26,49,0),'R106':(29,49,0),
'C201':(7,38,90),'C202':(7,42,90),'C203':(17,41,90),'C204':(17,38,90),'C205':(28,37,90),'C206':(29,41,90),'R201':(17,44,0),'R202':(17,46,0),
'C209':(18,49,0),'C210':(19,47,0),'C211':(14,49,0),'C212':(21,52,90),'C213':(27,51,90),
'R206':(16,54,90),'R207':(14,54,90),'R208':(18,54,90),'R209':(20,54,90),'R210':(16,57,0),'R211':(19,57,0),'R212':(20,58.5,0),'R213':(17,58.5,0),'R214':(14,47,0),'R215':(11,48,0),
'C311':(47,41,0),'C312':(45,56,0),'C313':(47,44,0),'C314':(49,46,90),'R310':(46,48,0),'R311':(46,49.5,0),'R312':(49,49.5,0),
'C308':(51.5,53,90),'C309':(56.5,53,90),'R303':(57,55,0),'R304':(59,68,90),'D301':(60,71,90),'R1001':(60,62,0),
'C601':(35.5,40,90),'C602':(35.5,37,90),'R308':(44.5,38,90),'R601':(44.5,42,0),'R602':(44.5,43.6,0),'R603':(37,44.5,0),'R611':(44.5,36,0),
'C701':(33,60.5,0),'C702':(36,58,90),'R309':(33,55.5,0),'R714':(30,57,90),'R313':(49,42,0),'R314':(49,40.5,0),
'C603':(51.5,55,0),'R305':(44,55,0),'R306':(44,56.5,0),'R307':(49,48,0),'D601':(53,68,180),'C604':(50,68,90),'R604':(58,70,90),
'R605':(50,64,0),'R606':(50,65.6,0),'R607':(50,67.2,0),'R608':(46.5,64,0),'R609':(46.5,65.6,0),'R610':(46.5,67.2,0),
'U202':(6,61,0),'C208':(5,56,0),'R203':(3,55,90),'R204':(3,67,90),'R205':(7,55,90),'C207':(3,69,90),
'C901':(10,65.5,90),'C902':(12,65.5,90),'C903':(14,65.5,90),'C904':(16,65.5,90),'R901':(16,62,90),'R902':(11,58,0),'R903':(14,58,0),'R904':(14,67.5,0),'R905':(14,69,0),
'C801':(37,67,90),'C802':(39,67,90),'D801':(32,74,90),'R801':(38,70,0),'R802':(35,73,90),'JP801':(36,76,90),'R803':(29,69,0),'R804':(29,70.7,0),'R805':(33,65,0),
'C501':(66,57,0),'C502':(66,58.5,0),'C503':(66,61,90),'C504':(63,64,0),'D501':(66,52,0),'D502':(61,56,90),'D503':(61,60,90),
'R501':(59,57,90),'R502':(61,53,90),'R503':(66,55,90),'R504':(68,52,0),'R505':(60,54,0),'R506':(71,59,0),'R507':(68,59,0),'R508':(65,63,0),'R509':(61,63,90),'R510':(61,65,0),
}
seeds.update({'C104': (19, 33, 90), 'C105': (20, 36, 0), 'C106': (20, 38, 0), 'C201': (5, 44, 90), 'C202': (5, 48, 90), 'C203': (14, 46.5, 90), 'C204': (14, 43, 90), 'C205': (27, 43, 90), 'C206': (27, 48, 90), 'R201': (14, 48, 0), 'R202': (14, 49.6, 0), 'C209': (18.5, 51.5, 90), 'C210': (20, 50, 90), 'C211': (13.5, 53, 90), 'C212': (21, 54, 90), 'C213': (27, 54, 90), 'C314': (49, 42, 0), 'R310': (48, 38.5, 90), 'R311': (50, 38.5, 90), 'R312': (49, 40.3, 0), 'C311': (47, 46, 90), 'C312': (52, 57.5, 90), 'C313': (48, 48.5, 90), 'C308': (52, 51, 90), 'C309': (56, 51, 90), 'R303': (54, 51, 90), 'R307': (49, 44, 0), 'R313': (49, 35.5, 90), 'R314': (47, 35.5, 90), 'C603': (58.5, 34, 90), 'R305': (59, 37, 0), 'R306': (49, 32, 0), 'D501': (68, 54, 0), 'R504': (65, 56, 90), 'R505': (61, 56, 90), 'C501': (64, 52, 0), 'C502': (64, 53.6, 0), 'C503': (64, 60, 0), 'C504': (63, 64, 0), 'R506': (69, 60, 90), 'R507': (69, 65, 90), 'R508': (65, 66, 0), 'R509': (61, 63, 90), 'R510': (61, 65, 0), 'C901': (10, 64, 90), 'C902': (12, 64, 90), 'C903': (14, 64, 90), 'C904': (16, 64, 90), 'R901': (16, 61, 90), 'R902': (11, 58, 0), 'R903': (14, 58, 0), 'R904': (14, 67, 0), 'R905': (14, 68.6, 0)})
seeds.update({'C202':(6,43.5,90),'C203':(14,43.5,0),'C204':(14,45.5,0),'C308':(53,55.3,0),'C309':(56,52.5,90)})
for ref,(xx,yy,a) in seeds.items():
 if ref not in placed:put(ref,xx,yy,a,'B' if ref in ['C601','C602','R308','R601','R602','R603','R611','C107','D101','R102','R101','C104','C105','C106','C314','R310','R311','R312','C202','C203','C204','R303','R307','R313','R314','C603','R305','R306','D501','R504','R505','C501','C502','C503','C504','R506','R507','R508','R509','R510','R201','R202','R901','R902','R903','R904','R905','C901','C902','C903','C904'] else 'F')
# Test pads next to their functional blocks, with probing clearance; no copper routes.
for ref,c in comps.items():
 if ref in placed:continue
 if not ref.startswith('TP'):raise RuntimeError('Unassigned component '+ref)
 nets=[pinmap.get((ref,str(i))) for i in [1]];nn=nets[0]
 neighbours=[r for r in placed if not r.startswith('TP') and any(pinmap.get((r,q.GetNumber()))==nn for q in fps[r].Pads())]
 preferred=[r for r in neighbours if r.startswith('U')]
 if not preferred:preferred=[r for r in neighbours if r.startswith(('J','Q'))]
 if preferred:
  anchor=placed[preferred[0]];xx=anchor['x_mm']+6;yy=anchor['y_mm']+6
 else:xx=20;yy=60
 put(ref,xx,yy,0,'B','Test access')
# Rounded-square outline, true arcs.
def line(a,b,layer=p.Edge_Cuts,width=.05):
 sh=p.PCB_SHAPE();sh.SetShape(p.SHAPE_T_SEGMENT);sh.SetStart(pos(*a));sh.SetEnd(pos(*b));sh.SetLayer(layer);sh.SetWidth(mm(width));board.Add(sh)
def arc(a,m,b):
 sh=p.PCB_SHAPE();sh.SetShape(p.SHAPE_T_ARC);sh.SetArcGeometry(pos(*a),pos(*m),pos(*b));sh.SetLayer(p.Edge_Cuts);sh.SetWidth(mm(.05));board.Add(sh)
for a,b in [((5,0),(75,0)),((80,5),(80,75)),((75,80),(5,80)),((0,75),(0,5))]:line(a,b)
k=5-5/math.sqrt(2)
for a,m,b in [((75,0),(80-k,k),(80,5)),((80,75),(80-k,80-k),(75,80)),((5,80),(k,80-k),(0,75)),((0,5),(k,k),(5,0))]:arc(a,m,b)
def text(t,x,y,layer=p.Dwgs_User,size=1):
 tx=p.PCB_TEXT(board);tx.SetText(t);tx.SetPosition(pos(x,y));tx.SetLayer(layer);tx.SetTextSize(vec(size,size));tx.SetTextThickness(mm(.15));board.Add(tx)
def circle(cx,cy,r):
 sh=p.PCB_SHAPE();sh.SetShape(p.SHAPE_T_CIRCLE);sh.SetCenter(pos(cx,cy));sh.SetEnd(pos(cx+r,cy));sh.SetLayer(p.Dwgs_User);sh.SetWidth(mm(.15));board.Add(sh)
for cx,cy in [(75,5),(5,75),(75,75)]:circle(cx,cy,3)
circle(40,40,7.5);line((36,40),(44,40),p.Dwgs_User,.1);line((40,36),(40,44),p.Dwgs_User,.1)
text('PROVISIONAL MAGNET ENVELOPE - DIA 15',40,50,size=.8)
text('ShiroFOC P0 | PLACEMENT ONLY | 80 x 80 mm',40,-6,size=1.4)
text('2 / 0.5 / 0.5 / 2 oz | L2 + L3 GND | NO ROUTING',40,-3)
text('Circles: provisional hardware envelopes; mounting holes still TBD',40,84,size=.9)
text('SHIROFOC P0',38,42,p.F_SilkS,1)
# Groups make subsequent manual placement edits tractable.
for ref,rec in placed.items():
 name=rec['group']
 if name not in groups:g=p.PCB_GROUP(board);g.SetName(name);board.Add(g);groups[name]=g
 groups[name].AddItem(fps[ref])
board.BuildConnectivity()
p.SaveBoard(str(PROJ/'ShiroFOC_KiCad.kicad_pcb'),board)
# Save diagnostics and exact original associations for validation.
(OUT/'placement_manifest.json').write_text(json.dumps({'status':'unrouted provisional placement','size_mm':[80,80],'origin_mm':[100,100],'copper_oz':[2,.5,.5,2],'components':placed},indent=2)+'\n')
with (OUT/'placement.csv').open('w') as fp:
 w=csv.DictWriter(fp,fieldnames=list(next(iter(placed.values())).keys()));w.writeheader();w.writerows(placed.values())
print('Saved',len(placed),'footprints;',sum(f.IsFlipped() for f in fps.values()),'on back')
# Library-polygon bounding checks (native DRC supplies exact geometry separately).
coll=[]
refs=list(fps)
for i,a in enumerate(refs):
 for b in refs[i+1:]:
  if fps[a].GetLayer()==fps[b].GetLayer() and overlap(bounds(fps[a]),bounds(fps[b]),0):coll.append([a,b])
print('Same-side courtyard bounding overlaps:',coll)
(OUT/'placement_bounds.json').write_text(json.dumps({r:bounds(f) for r,f in fps.items()},indent=2))
