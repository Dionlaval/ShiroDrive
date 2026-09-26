"""One-time placement migration, not an autorouter. Refuses to overwrite a board."""
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as k
import xml.etree.ElementTree as E,json,math,re
P=Path(__file__).resolve().parents[1];ROOT=P.parent
DEST=P/'ShiroFOC_Manual.kicad_pcb';assert not DEST.exists(),'Do not overwrite user layout'
source=ROOT/'ShiroFOC_KiCad_P1/ShiroFOC_KiCad.kicad_pcb'
source_board=k.LoadBoard(str(source));old={f.GetReference():f for f in source_board.GetFootprints()}
b=k.LoadBoard(str(P/'review/outline_base.kicad_pcb'))
netlist=E.parse(P/'review/current.xml');comps=netlist.findall('.//components/comp')
rootuuid=re.search(r'\(uuid "([^"]+)"', (P/'ShiroFOC_Manual.kicad_sch').read_text()).group(1)
mm=k.FromMM;v=lambda x,y:k.VECTOR2I(mm(x),mm(y));nets={};pinmap={}
for n in netlist.findall('.//nets/net'):
 name=n.get('name');ni=k.NETINFO_ITEM(b,name);b.Add(ni);nets[name]=ni
 for x in n.findall('node'):pinmap[x.get('ref'),x.get('pin')]=name
mapping={'U4':'U301','U1':'Q401','U2':'Q402','U3':'Q403','J1':'J401','R3':'R416','R1':'R426','R5':'R436','R2':'R411','R4':'R421','R6':'R431','C1':'C415','C2':'C412','C5':'C425','C6':'C422','C9':'C435','C10':'C432'}
newpos={'R7':(196,112,0,'F'),'U205':(134,160,0,'F'),'U603':(150,166,0,'F'),'U604':(156,166,0,'F'),'JP601':(159,170,0,'F'),'C605':(150,163,0,'F'),'C606':(155,163,0,'F'),'C607':(158,163,0,'F'),'C214':(130,157,0,'F'),'C215':(134,155,0,'F'),'C218':(136,165,0,'F'),'C219':(140,165,0,'F'),'R216':(135,157,0,'B'),'R217':(138,157,0,'B'),'R218':(130,160,0,'B'),'R219':(130,162,0,'B'),'R715':(131,152,0,'F'),'R615':(153,168,0,'B'),'R616':(153,170,0,'B'),'R617':(153,172,0,'B')}
for i,y in enumerate([128,142,156]):
 newpos['C'+str(3+4*i)]=(164,y+6,90,'F');newpos['C'+str(4+4*i)]=(160,y+3,90,'F')
fps={};provenance={}
libroot=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
def padcenter(f):
 ps=list(f.Pads());xs=[k.ToMM(p.GetPosition().x) for p in ps];ys=[k.ToMM(p.GetPosition().y) for p in ps];return ((min(xs)+max(xs))/2,(min(ys)+max(ys))/2)
def setcenter(f,x,y):
 cx,cy=padcenter(f);f.Move(v(x-cx,y-cy))
for c in comps:
 ref=c.get('ref');libid=c.findtext('footprint');assert libid,ref
 lib,fn=libid.split(':',1);ld=P/'libs/Manual.pretty' if lib=='Manual' else libroot/(lib+'.pretty')
 f=k.FootprintLoad(str(ld),fn);assert f,(ref,libid);b.Add(f);f.SetFPID(k.LIB_ID(lib,fn));f.SetReference(ref);f.SetValue(c.findtext('value',''))
 f.SetPath(k.KIID_PATH('/'+rootuuid+c.find('sheetpath').get('tstamps')+c.findtext('tstamps').split()[0]))
 f.SetSheetname(c.find('sheetpath').get('names'));props={x.get('name'):x.get('value','') for x in c.findall('property')};f.SetSheetfile(props.get('Sheetfile',''))
 for x in c.findall('fields/field'):f.SetField(x.get('name'),x.text or '')
 # Fields may include Footprint: preserve FPID explicitly.
 f.SetFPID(k.LIB_ID(lib,fn));f.SetDNP('dnp' in props)
 if 'exclude_from_bom' in props:f.SetAttributes(f.GetAttributes()|k.FP_EXCLUDE_FROM_BOM|k.FP_EXCLUDE_FROM_POS_FILES)
 prev=mapping.get(ref,ref)
 if ref in newpos:x,y,a,side=newpos[ref];provenance[ref]='new rough position'
 elif prev in old:
  o=old[prev];x,y=padcenter(o);a=o.GetOrientationDegrees();side='B' if o.IsFlipped() else 'F';provenance[ref]='P1:'+prev
 else:raise RuntimeError('No placement for '+ref)
 if side=='B':f.Flip(f.GetPosition(),False)
 f.SetOrientationDegrees(a);setcenter(f,x,y);f.SetLocked(False)
 for pad in f.Pads():
  net=pinmap.get((ref,pad.GetNumber()))
  if net:pad.SetNet(nets[net])
 f.Value().SetVisible(False)
 for field in f.GetFields():
  if field.GetName()!='Reference':field.SetVisible(False)
 fps[ref]=f
# Keep sensor aligned to the board centre using its body/land-pattern centre.
setcenter(fps['U601'],140,140)
# New bridge pinout uses an imported land pattern; maintain parallel cells.
for ref,y in [('U1',128),('U2',142),('U3',156)]:setcenter(fps[ref],164,y)
# Retain the MCU anchor while reserving its underside for analog components.
setcenter(fps['U4'],142,149)
# Imported interfaces can have different origins. Centre-to-centre mapping above
# preserves body vicinity; final mating envelopes belong to the user placement pass.
# Remove gross body/courtyard overlaps introduced by changed packages.
def bounds(f):
 layer=k.B_CrtYd if f.IsFlipped() else k.F_CrtYd
 boxes=[g.GetBoundingBox() for g in f.GraphicalItems() if g.GetLayer()==layer]
 if not boxes:boxes=[p.GetBoundingBox() for p in f.Pads()]
 return min(k.ToMM(x.GetLeft()) for x in boxes),min(k.ToMM(x.GetTop()) for x in boxes),max(k.ToMM(x.GetRight()) for x in boxes),max(k.ToMM(x.GetBottom()) for x in boxes)
def overlap(a,c,g=.15):return a[0]<c[2]+g and a[2]+g>c[0] and a[1]<c[3]+g and a[3]+g>c[1]
holes=[(106,106),(174,106),(174,174),(106,174)]
fixed=['H1','H2','H3','H4','U601','U1','U2','U3','U4','J1','J101','J201','J501','C101','C102','C103','R7']
placed={ref:fps[ref] for ref in fixed};moves=[]
def conflict(f):
 ref=f.GetReference();a=bounds(f)
 if min(a[:2])<100.5 or max(a[2:])>179.5:return True
 if any(math.hypot(max(a[0],min(x,a[2]))-x,max(a[1],min(y,a[3]))-y)<4 for x,y in holes):return True
 for rr,o in placed.items():
  if rr in ['R7',ref] or rr.startswith('H'):continue
  ob=bounds(o)
  if f.IsFlipped()==o.IsFlipped():
   if rr=='J1':
    if any(overlap(a,(k.ToMM(q.GetBoundingBox().GetLeft()),k.ToMM(q.GetBoundingBox().GetTop()),k.ToMM(q.GetBoundingBox().GetRight()),k.ToMM(q.GetBoundingBox().GetBottom())),.5) for q in o.Pads()):return True
   elif overlap(a,ob):return True
  else:
   for q in o.Pads():
    if q.GetAttribute() in [k.PAD_ATTRIB_PTH,k.PAD_ATTRIB_NPTH]:
     box=q.GetBoundingBox()
     if overlap(a,tuple(k.ToMM(x) for x in [box.GetLeft(),box.GetTop(),box.GetRight(),box.GetBottom()]),.2):return True
 return False
remaining=[ref for ref in fps if ref not in placed]
remaining.sort(key=lambda ref:(ref.startswith('TP'),not ref.startswith(('U','L','J','Q')), -(bounds(fps[ref])[2]-bounds(fps[ref])[0])*(bounds(fps[ref])[3]-bounds(fps[ref])[1]),ref))
for ref in remaining:
 f=fps[ref];x,y=padcenter(f)
 if conflict(f):
  found=False
  for radius in range(1,25):
   offsets=[(dx*.5,dy*.5) for dx in range(-radius,radius+1) for dy in range(-radius,radius+1) if max(abs(dx),abs(dy))==radius]
   for dx,dy in sorted(offsets,key=lambda q:q[0]*q[0]+q[1]*q[1]):
    setcenter(f,x+dx,y+dy)
    if not conflict(f):found=True;break
   if found:break
  if not found:setcenter(f,x,y)
  else:moves.append({'reference':ref,'from':[x,y],'to':padcenter(f)})
 placed[ref]=f
# Visible references belong to fabrication layers, so silkscreen is not cluttered.
for ref,f in fps.items():
 f.Reference().SetLayer(k.B_Fab if f.IsFlipped() else k.F_Fab);f.Reference().SetTextSize(v(.8,.8));f.Reference().SetTextThickness(mm(.12));f.Reference().SetTextAngle(k.EDA_ANGLE(0,k.DEGREES_T));a=bounds(f);f.Reference().SetPosition(v((a[0]+a[2])/2,a[1]-.6))
# Mechanical circles and non-copper visual guidance, no copper/tracks/zones.
def line(x1,y1,x2,y2,layer=k.Dwgs_User,width=.15):
 s=k.PCB_SHAPE();s.SetShape(k.SHAPE_T_SEGMENT);s.SetStart(v(x1,y1));s.SetEnd(v(x2,y2));s.SetLayer(layer);s.SetWidth(mm(width));b.Add(s)
def text(s,x,y,layer=k.Dwgs_User,size=1):
 t=k.PCB_TEXT(b);t.SetText(s);t.SetPosition(v(x,y));t.SetLayer(layer);t.SetTextSize(v(size,size));t.SetTextThickness(mm(.15));b.Add(t)
def box(x1,y1,x2,y2,layer):
 for a,c in [((x1,y1),(x2,y1)),((x2,y1),(x2,y2)),((x2,y2),(x1,y2)),((x1,y2),(x1,y1))]:line(*a,*c,layer,.1)
for x,y in holes:
 s=k.PCB_SHAPE();s.SetShape(k.SHAPE_T_CIRCLE);s.SetCenter(v(x,y));s.SetEnd(v(x+4,y));s.SetLayer(k.Dwgs_User);s.SetWidth(mm(.1));b.Add(s)
text('P2 | MANUAL ROUTING START | 80 x 80 mm',140,93,size=1.5)
text('4 layers: 2 / 0.5 / 0.5 / 2 oz | In1 + In2: continuous GND',140,96,size=1)
text('Rough placement only - no traces or filled planes',140,99,size=.85)
# Group guides are deliberately coarse, non-binding envelopes.
box(110,102,170,122,k.User_1);text('DC LINK / BULK',140,104,k.User_1,.8)
box(157,122,172,164,k.User_1);text('3 PHASE CELLS',165,166,k.User_1,.8)
box(117,123,132,140,k.User_1);text('BRAKE STAGE',125,124,k.User_1,.8)
box(103,140,138,166,k.User_2);text('AUX POWER + USB',117,143,k.User_2,.8)
box(135,142,155,162,k.User_3);text('MCU / ANALOG BELOW',145,160,k.User_3,.7)
box(121,165,173,179,k.User_2);text('CAN / HALL / SWD',145,178,k.User_2,.8)
text('BACK: ENCODER CENTRE',140,137,k.User_3,.7)
# Gate/sense paths are direction hints, not approved routes.
for y in [128,142,156]:
 line(156,y,150,y,k.User_3,.18)
text('KELVIN: paired routes to MCU analog pins\nStay out of phase / VM / brake current paths',197,147,k.Dwgs_User,.9)
text('POWER: short local capacitor -> bridge -> shunt -> capacitor loop\nKeep VM and GND broad and close; phase exits to the right',140,185,k.Dwgs_User,.9)
text('GATES: short drive + source return; resistor at GH pin\nANALOG: input/feedback parts near U4 pins; decouplers below',140,190,k.Dwgs_User,.9)
text('R7 BVR4026\nCOMPARISON ONLY\nDNP / keep off-board\nRemove before fabrication',196,123,k.Dwgs_User,.9)
text('Guide layers: User.1 power | User.2 interfaces | User.3 quiet/sense\nHide guides while routing. Footprint F.Fab / B.Fab show references.',140,196,k.Dwgs_User,.9)
b.BuildConnectivity();k.SaveBoard(str(DEST),b)
manifest={'source':str(source),'footprints':len(fps),'mapping':mapping,'provenance':provenance,'rough_relocations':moves,'positions':{ref:{'x':padcenter(f)[0],'y':padcenter(f)[1],'side':'B' if f.IsFlipped() else 'F','bounds':bounds(f)} for ref,f in fps.items()},'unmapped_schematic_pins':[]}
for c in comps:
 ref=c.get('ref');pads={p.GetNumber() for p in fps[ref].Pads()}
 for rr,pin in pinmap:
  if rr==ref and pin not in pads:manifest['unmapped_schematic_pins'].append([ref,pin,pinmap[ref,pin]])
(P/'review/placement_manifest.json').write_text(json.dumps(manifest,indent=2));print('Saved',DEST,'footprints',len(fps),'rough moves',len(moves),'unmapped pins',manifest['unmapped_schematic_pins'])
