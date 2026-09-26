#!/usr/bin/env python3
"""Create first power-copper draft from the unrouted pin-local placement.
Candidate outputs only. Native DRC and routing review are mandatory after generation.
"""
from pathlib import Path
import pcbnew as p
import json,math,shutil
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'ShiroFOC_KiCad_P1';O=P/'outputs/routing_P1';O.mkdir(exist_ok=True)
b=p.LoadBoard(str(P/'ShiroFOC_KiCad.kicad_pcb'))
assert not list(b.GetTracks()) and not list(b.Zones()), 'Use an unrouted placement'
fs={f.GetReference():f for f in b.GetFootprints()};nets={n.GetNetname():n for n in b.GetNetInfo().NetsByNetcode().values()}
mm=p.FromMM
v=lambda x,y:p.VECTOR2I(mm(x+100),mm(y+100))
layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
# Clear the force-via land from the preceding phase's gate pull-down.
for r,y in [('R414',36.7),('R424',50.7)]:fs[r].SetPosition(v(58.5,y))
# Clamp diode sits beside, rather than under, the brake drain thermal land.
fs['D501'].SetPosition(v(34,30))
fs['D504'].SetOrientationDegrees(270)
# Bring the STSPIN buck input ceramic to its VM pin on the underside.
fs['C311'].Flip(fs['C311'].GetPosition(),False)
fs['C311'].SetOrientationDegrees(90)
fs['C311'].SetPosition(v(38.4,48.4))
fs['TP102'].SetPosition(v(31,26.5))
fs['TP903'].SetPosition(v(31,52))
fs['TP204'].SetPosition(v(28,56))
fs['TP1006'].SetPosition(v(46,70))
fs['C108'].SetOrientationDegrees(90)
fs['C108'].SetPosition(v(43.85,52.95))
fs['C313'].Flip(fs['C313'].GetPosition(),False)
fs['C313'].SetOrientationDegrees(180)
fs['C313'].SetPosition(v(35.5,54.5))
fs['C303'].SetPosition(v(49,47.6))
fs['C305'].SetPosition(v(49,49.8))
# Preserve pin order from OUT/BOOT pairs; this avoids crossed bootstrap routes.
for r,x in [('C411',40),('C421',43.4),('C431',46.8)]:
 fs[r].SetOrientationDegrees(180);fs[r].SetPosition(v(x,41.9))
# Test access stays with its circuit; do not carry ADC/logic probe stubs through the inverter.
tp_moves={'TP1018':(42,55.8),'TP1019':(46,52.2),'TP1020':(45.7,46),
'TP302':(33,46.5),'TP103':(37,58),'TP701':(37,64),'TP702':(40,65),'TP703':(43,65),
'TP901':(9,66.5),'TP902':(10.5,70),'TP1008':(61,69),'TP1009':(69,69),
'TP1014':(34,70),'TP1013':(31,70),'TP1022':(37,70),'TP1015':(29,44),'TP1016':(29,47),
'TP1011':(32.5,48.5),'TP1012':(30.5,49),'TP1007':(42,60),'TP303':(55,69),
'TP1021':(44,72),'TP1023':(47,72),'TP1024':(50,72),'TP501':(32,32.5),'TP502':(30,25),
'TP301':(29,61),'TP1002':(29,64),'TP101':(18,25.5)}
for ref,xy in tp_moves.items():fs[ref].SetPosition(v(*xy))
# Find nearby probe-pad sites using actual component courtyards and pad copper.
# Preserve electrical function and side; only move the selected test points.
for f in fs.values():f.BuildCourtyardCaches()
fitlog=[]
for ref in list(tp_moves)+['TP102']:
 f=fs[ref];base=f.GetPosition();layer=p.B_Cu if f.IsFlipped() else p.F_Cu;clayer=p.B_CrtYd if f.IsFlipped() else p.F_CrtYd
 q=next(iter(f.Pads()));ownnet=q.GetNetname();rad=p.ToMM(q.GetSize().x)/2
 ok=False
 offsets=sorted([(dx/4,dy/4) for dx in range(-40,41) for dy in range(-40,41)],key=lambda xy:xy[0]**2+xy[1]**2)
 for dx,dy in offsets:
  pos=p.VECTOR2I(base.x+mm(dx),base.y+mm(dy));x,y=p.ToMM(pos.x)-100,p.ToMM(pos.y)-100
  if min(x,y)<2 or max(x,y)>78:continue
  if 39.4-rad<x<44.6+rad and 46.4-rad<y<51.6+rad:continue
  if any(math.hypot(x-hx,y-hy)<4.5+rad for hx,hy in [(6,6),(74,6),(74,74),(6,74)]):continue
  safe=True
  for other in fs.values():
   if other==f:continue
   court=other.GetCourtyard(clayer)
   if court.OutlineCount() and court.Collide(pos,mm(rad+.50)):
    safe=False;break
   for pad in other.Pads():
    if pad.GetNetname()!=ownnet and pad.IsOnLayer(layer) and pad.GetEffectiveShape(layer).Collide(pos,mm(rad+(.51 if pad.GetNetname() in ['VM','OUT1','OUT2','OUT3','Net-(D504-A)'] else .21))):
     safe=False;break
   if not safe:break
  if not safe:continue
  # Reserve the pin-local amplifier and driver transition vias before they exist.
  for vx,vy in [(45.75,48.75),(45.25,49.25),(45.75,49.75),(45.25,50.25),(45.25,51.25),(44.75,54.35),(46.25,54.2),(40.75,45.3),(42.25,43.5),(43.75,45.3)]:
   if math.hypot(x-vx,y-vy)<rad+.45:safe=False;break
  if not safe:continue
  f.SetPosition(pos);f.BuildCourtyardCaches();fitlog.append([ref,x,y]);ok=True;break
 assert ok,'No local probe site '+ref
(O/'testpoint_sites.json').write_text(json.dumps(fitlog,indent=2)+'\n')

allpads=[q for f in fs.values() for q in f.Pads()]
via_intents={}
skipped=[]
def zone(name,net,layer,points,priority=0):
 z=p.ZONE(b);z.SetLayer(layer);z.SetZoneName(name);z.SetNet(nets[net]);z.SetLocalClearance(mm(.5 if net!='GND' else .2));z.SetMinThickness(mm(.2));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetAssignedPriority(priority)
 poly=z.Outline();poly.NewOutline()
 for x,y in points:poly.Append(v(x,y))
 b.Add(z);return z
rect=lambda x1,y1,x2,y2:[(x1,y1),(x2,y1),(x2,y2),(x1,y2)]
def via(net,x,y,diam=.6,drill=.3):
 pt=v(x,y)
 for pad in allpads:
  if pad.GetDrillSize().x and pad.GetEffectiveHoleShape().Collide(pt,mm(drill/2+.451)):
   skipped.append((net,x,y,'hole',pad.GetParentFootprint().GetReference()));return None
  if pad.GetNetname()==net or not pad.IsOnCopperLayer():continue
  if any(pad.IsOnLayer(l) and pad.GetEffectiveShape(l).Collide(pt,mm(diam/2+.51)) for l in layers):
   skipped.append((net,x,y,pad.GetParentFootprint().GetReference(),pad.GetNumber()));return None
 for other in b.GetTracks():
  if isinstance(other,p.PCB_VIA) and math.hypot(p.ToMM(other.GetPosition().x-pt.x),p.ToMM(other.GetPosition().y-pt.y))<(drill+p.ToMM(other.GetDrill()))/2+.201:return None
 q=p.PCB_VIA(b);q.SetFrontTentingMode(p.TENTING_MODE_TENTED);q.SetBackTentingMode(p.TENTING_MODE_TENTED);q.SetPosition(pt);q.SetWidth(mm(diam));q.SetDrill(mm(drill));q.SetViaType(p.VIATYPE_THROUGH);q.SetLayerPair(p.F_Cu,p.B_Cu);q.SetNet(nets[net]);q.SetLocked(True);b.Add(q);via_intents[q.m_Uuid.AsString()]=net;return q
def trace(net,points,width,layer=p.F_Cu):
 for a,c in zip(points,points[1:]):
  if a==c:continue
  q=p.PCB_TRACK(b);q.SetStart(v(*a));q.SetEnd(v(*c));q.SetWidth(mm(width));q.SetLayer(layer);q.SetNet(nets[net]);q.SetLocked(True);b.Add(q)
# Continuous reference planes; outer ground supports the power return and thermal spreading.
for layer in layers:zone('GND_'+b.GetLayerName(layer),'GND',layer,rect(.5,.5,79.5,79.5),0)
# Mounting hardware reservations on every copper layer.
for i,(cx,cy) in enumerate([(6,6),(74,6),(74,74),(6,74)],1):
 z=p.ZONE(b);ls=p.LSET()
 for layer in layers:ls.AddLayer(layer)
 z.SetLayerSet(ls);z.SetIsRuleArea(True);z.SetZoneName('M3_HARDWARE_'+str(i));z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowCopperPour(True);z.SetDoNotAllowFootprints(False);z.SetDoNotAllowPads(False)
 poly=z.Outline();poly.NewOutline()
 for k in range(64):poly.Append(v(cx+4*math.cos(2*math.pi*k/64),cy+4*math.sin(2*math.pi*k/64)))
 b.Add(z)
# Bulk positive bar and an outer-layer vertical feed; ground is retained everywhere else.
zone('VM_BULK','VM',p.F_Cu,[(10,14),(69,14),(69,24),(22,24),(20,31),(12,31),(12,24),(10,24)],5)
zone('VM_VERTICAL_FRONT','VM',p.F_Cu,rect(55,23.5,60,59.5),7)
zone('VM_VERTICAL_BACK','VM',p.B_Cu,rect(55,22,66,59.5),5)
zone('VM_LOCAL_C432','VM',p.B_Cu,rect(63,59,66,64.5),8)
# Bulk capacitor negative pads receive parallel vias into the broad ground return.
for ref in ['C101','C102','C103']:
 pad=next(q for q in fs[ref].Pads() if q.GetNetname()=='GND');pt=pad.GetPosition();cx,cy=p.ToMM(pt.x)-100,p.ToMM(pt.y)-100
 for dx in [-1.5,-.5,.5,1.5]:
  for dy in [-1.5,-.5,.5,1.5]:via('GND',cx+dx,cy+dy)
# Phase terminals face their packages. These polygon boundaries will be reviewed
# for neck-downs after native filling; the router must not substitute thin tracks.
arrays=[]
for i,y in enumerate([28,42,56]):
 out='OUT'+str(i+1);force=f'/Three-phase bridge/SHUNT_{"UVW"[i]}_FORCE_P';n=410+10*i
 zone('PHASE_'+str(i+1),out,p.F_Cu,rect(66.25,y-2.9,78.8,y+2.35),10)
 zone('VM_EP_'+str(i+1),'VM',p.F_Cu,rect(62.15,y-2.9,65.85,y+2.9),6)
 zone('SOURCE_FRONT_'+str(i+1),force,p.F_Cu,[(58.5,y-3.95),(60,y-3.95),(60,y-7.2),(63,y-7.2),(63,y-2.7),(62.1,y+1.85),(60,y+1.85),(60,y-1.8),(58.5,y-1.8)],10)
 zone('SOURCE_BACK_'+str(i+1),force,p.B_Cu,[(60.1,y-7.2),(63.2,y-7.2),(63.2,y-1.8),(58.5,y-1.8),(58.5,y-3.95),(60.1,y-3.95)],10)
 # Filled/capped via-in-pad arrays in the shunt force lands; never touch Kelvin pads.
 sh=fs[f'R{n+6}']
 for number,net in [('1',force),('4','GND')]:
  pad=next(q for q in sh.Pads() if q.GetNumber()==number);pt=pad.GetPosition();cx,cy=p.ToMM(pt.x)-100,p.ToMM(pt.y)-100
  size=pad.GetSize();sx,sy=p.ToMM(size.x),p.ToMM(size.y)
  print(sh.GetReference(),number,'land',sx,sy,flush=True)
  count=0
  for dx in [-.7,0,.7]:
   for dy in [-2.1,-1.4,-.7,0,.7,1.4,2.1]:
    if abs(dx)+.3>sx/2 or abs(dy)+.3>sy/2:continue
    if via(net,cx+dx,cy+dy):count+=1
  arrays.append({'ref':sh.GetReference(),'pad':number,'net':net,'vias':count,'diameter_mm':.6,'drill_mm':.3,'process':'filled and capped via-in-pad required'})
 extra=0
 for xx in [58.9,59.6,60.3]:
  for yy in [y-3.6,y-2.9,y-2.2]:
   if via(force,xx,yy):extra+=1
 arrays[-2]['adjacent_vias']=extra
 # Direct package bypass to source and VM, with exactly the schematic's two return nets.
 cap=fs[f'C{n+5}']
 for pad in cap.Pads():
  pt=pad.GetPosition();cx,cy=p.ToMM(pt.x)-100,p.ToMM(pt.y)-100
  if pad.GetNetname()=='VM':trace('VM',[(cx,cy),(59,cy)],.3)
 # Connect the top VM bar to the bottom spine using spaced power vias.
 for xx in [56,56.8,57.6,58.4]:
  for yy in [y-1,y,y+1]:via('VM',xx,yy)
# Brake loop: left edge wiring and a short local driver/MOSFET return.
trace('VM',[(5.5,13),(9,13),(14,18),(20,18.75)],2)
# Brake switch route stays in the upper-left power section, away from the sensor.
brake_net=next(q.GetNetname() for q in fs['J501'].Pads() if q.GetNumber()=='2')
trace(brake_net,[(5.5,20.8),(5.5,22),(26,22),(28.3,24.3),(28.3,29)],2,p.B_Cu)
zone('BRAKE_DRAIN',brake_net,p.F_Cu,[(26,26),(32,26),(32,29.5),(38.8,32.6),(38.8,34.2),(37.2,34.2),(31,31.5),(26,31.5)],10)
trace('VM',[(38,26.6),(38,23.5)],2)
zone('BRAKE_DRAIN_BACK',brake_net,p.B_Cu,rect(26.7,27.5,29.9,30.5),10)
for xx in [27.3,28.3,29.3]:
 for yy in [28,29,30]:via(brake_net,xx,yy)
# The local DC-link ceramics feed directly into VM and ground on the back.
for ref in ['C412','C422','C432']:
 for pad in fs[ref].Pads():
  pt=pad.GetPosition();cx,cy=p.ToMM(pt.x)-100,p.ToMM(pt.y)-100
  for dx in [-.55,.55]:
   for dy in [-.35,.35]:via(pad.GetNetname(),cx+dx,cy+dy)
# Low-inductance ground returns for each IC/capacitor. Via beside pad, not in it.
def clear_segment(net,a,c,width,layer):
 seg=p.SEG(v(*a),v(*c))
 for pad in allpads:
  if pad.GetNetname()==net or not pad.IsOnLayer(layer):continue
  cl=.51 if pad.GetNetname()=='VM' or pad.GetNetname().startswith(('OUT','BOOT')) or 'FORCE_P' in pad.GetNetname() else .21
  if pad.GetEffectiveShape(layer).Collide(seg,mm(width/2+cl)):return False
 for t in b.GetTracks():
  if t.GetNetname()!=net and t.IsOnLayer(layer) and t.GetEffectiveShape(layer).Collide(seg,mm(width/2+.51)):return False
 return True
ground_returns=[]
for ref,f in sorted(fs.items()):
 if not ref.startswith(('C','U','D')) or ref=='C301':continue
 layer=p.B_Cu if f.IsFlipped() else p.F_Cu
 for pad in f.Pads():
  if pad.GetNetname()!='GND' or pad.GetAttribute()!=p.PAD_ATTRIB_SMD:continue
  pos=pad.GetPosition();cx,cy=p.ToMM(pos.x)-100,p.ToMM(pos.y)-100
  if any(isinstance(t,p.PCB_VIA) and t.GetNetname()=='GND' and math.hypot(p.ToMM(t.GetPosition().x)-100-cx,p.ToMM(t.GetPosition().y)-100-cy)<1.1 for t in b.GetTracks()):continue
  found=False
  size=pad.GetBoundingBox();hx,hy=p.ToMM(size.GetWidth())/2,p.ToMM(size.GetHeight())/2
  candidates=[]
  for delta in [.4,.7,1.0]:
   candidates.extend([(cx+sx*(hx+delta),cy) for sx in [-1,1]]+[(cx,cy+sy*(hy+delta)) for sy in [-1,1]])
  for x,y in sorted(candidates,key=lambda a:math.hypot(a[0]-cx,a[1]-cy)):
   if max(abs(x-cx),abs(y-cy))>2 or x<1 or y<1 or x>79 or y>79:continue
   if not clear_segment('GND',(cx,cy),(x,y),.25,layer):continue
   if via('GND',x,y):
    trace('GND',[(cx,cy),(x,y)],.25,layer);ground_returns.append([ref,pad.GetNumber(),round(x,3),round(y,3)]);found=True;break
# Keep project constraints next to the candidate board when loading it later.
name='power_v2'
for suffix in ['.kicad_pro','.kicad_dru']:shutil.copy2(P/('ShiroFOC_KiCad'+suffix),O/(name+suffix))
(O/'fp-lib-table').write_text((P/'fp-lib-table').read_text().replace('${KIPRJMOD}',str(P)))
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());
assert all(t.GetNetname()==via_intents[t.m_Uuid.AsString()] for t in b.GetTracks() if t.m_Uuid.AsString() in via_intents), 'Connectivity reassigned a shorted via'
p.SaveBoard(str(O/(name+'.kicad_pcb')),b)
(O/'power_via_arrays.json').write_text(json.dumps(arrays,indent=2)+'\n')
print('Saved candidate',len(list(b.GetTracks())),'tracks/vias',len(list(b.Zones())),'zones/rule areas')

print('Accepted force arrays',[(a['ref'],a['pad'],a['vias']) for a in arrays]);print('Skipped colliding via sites',len(skipped))

(O/'ground_returns_v2.json').write_text(json.dumps(ground_returns,indent=2)+'\n')
