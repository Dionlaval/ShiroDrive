#!/usr/bin/env python3
"""Pin-local routing candidate. Use KiCad DRC before accepting any output."""
from pathlib import Path
import pcbnew as p
import shutil
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'ShiroFOC_KiCad_P1';O=P/'outputs/routing_P1'
b=p.LoadBoard(str(O/'power_v2.kicad_pcb'));fs={f.GetReference():f for f in b.GetFootprints()};nets={n.GetNetname():n for n in b.GetNetInfo().NetsByNetcode().values()}
mm=p.FromMM;v=lambda x,y:p.VECTOR2I(mm(x+100),mm(y+100));rules=[]
def trace(net,points,w=.25,layer=p.F_Cu):
 for a,c in zip(points,points[1:]):
  if a==c:continue
  t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*c));t.SetWidth(mm(w));t.SetLayer(layer);t.SetNet(nets[net]);t.SetLocked(True);b.Add(t)
def via(net,x,y,d=.45,h=.2):
 t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(mm(d));t.SetDrill(mm(h));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);t.SetNet(nets[net]);t.SetLocked(True);b.Add(t)
def pad(ref,pin):return next(q for q in fs[ref].Pads() if q.GetNumber()==str(pin))
def area(name,x1,y1,x2,y2):
 z=p.ZONE(b);s=p.LSET();s.AddLayer(p.F_Cu);s.AddLayer(p.B_Cu);z.SetLayerSet(s);z.SetIsRuleArea(True);z.SetZoneName(name)
 for f in [z.SetDoNotAllowTracks,z.SetDoNotAllowVias,z.SetDoNotAllowCopperPour,z.SetDoNotAllowFootprints,z.SetDoNotAllowPads]:f(False)
 poly=z.Outline();poly.NewOutline()
 for xy in [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]:poly.Append(v(*xy))
 b.Add(z);rules.append(f'''(rule "{name}: 2oz package escape" (condition "A.enclosedByArea('{name}') && B.enclosedByArea('{name}')") (constraint clearance (min 0.15mm)))''')
area('U301_PACKAGE_ESCAPE',36.6,43.7,47.4,54.3)
area('U301_BOOTSTRAP_ESCAPE',38.5,40.8,48.5,45.7)
# Connect the final OUT lead to its main drain bank inside each exact package.
for i,y in enumerate([28,42,56],1):
 area('Q40'+str(i)+'_PACKAGE_ESCAPE',60.2,y-3.5,67.5,y+5.25)
 trace('OUT'+str(i),[(66.35,y+1.5),(66.35,y+2)],.25)
# Compact, same-face capacitor loops with pin ordering preserved.
trace('OUT1',[(41.25,44.5625),(41.25,43.925),(39.225,41.9)])
trace('BOOT1',[(41.75,44.5625),(41.75,42.875),(40.775,41.9)])
trace('OUT2',[(42.75,44.5625),(42.75,42.025),(42.625,41.9)])
trace('BOOT2',[(43.25,44.5625),(43.25,43.6),(44.175,42.675),(44.175,41.9)])
trace('OUT3',[(44.25,44.5625),(44.25,43.4),(46.025,41.9)])
trace('BOOT3',[(44.75,44.5625),(44.75,43.7),(46.9,43.7),(47.575,43.025),(47.575,41.9)])
# Gate fanout retains each net; later gate/OUT paired routes start here.
for net,x,y in [('GHS1',40.75,45.3),('GHS2',42.25,43.5),('GHS3',43.75,45.3)]:
 trace(net,[(x,44.5625),(x,y)],.2);via(net,x,y)
# Low-side gate fanout goes above the analog supply capacitors.
for net,y,outy,sx in [('GLS1',46.75,46.4,48.6),('GLS2',46.25,45.6,48.2),('GLS3',45.75,44.8,47.8)]:
 trace(net,[(46.4375,y),(sx,y),(sx+y-outy,outy),(51.5,outy)],.25)
# Supply loops: no gate trace crosses the analog capacitor-to-pin connections.
trace('VDDA',[(46.4375,47.75),(47.65,47.75),(47.8,47.6),(48.225,47.6)],.25)
trace('VREF+',[(46.4375,48.25),(47.4,48.25),(47.4,48.975),(48.225,49.8)],.25)
trace('GND',[(49.775,47.6),(49.9,47.6),(50.4,47.1)],.3);via('GND',50.4,47.1)
via('GND',49.775,49.8)
# Op-amp inputs/outputs escape inward to the underside ratio networks, keeping
# their high impedance nodes away from the low-side gate fanout outside the IC.
for pin,x in [(25,45.75),(24,45.25),(23,45.75),(22,45.25),(20,45.25),(19,45.75)]:
 q=pad('U301',pin);pt=q.GetPosition();y=p.ToMM(pt.y)-100;n=q.GetNetname()
 trace(n,[(46.4375,y),(x,y)],.2);via(n,x,y)
# Bottom-edge amplifier U has its own staggered fanout.
for pin,xy in [(14,(44.8,54.4)),(15,(45.25,53.0)),(16,(46.25,54.2))]:
 q=pad('U301',pin);pt=q.GetPosition();n=q.GetNetname();st=(p.ToMM(pt.x)-100,p.ToMM(pt.y)-100)
 trace(n,[st,xy],.2);via(n,*xy)
via('GND',39.5,51.7)
trace('GND',[(38,51.725),(39.5,51.7)],.25,p.B_Cu)
# Adjacent VM/VCC capacitor connections and their immediate pin escapes.
trace('VM',[(37.5625,51.25),(38.7,51.25),(38.7,49.35)],.2);via('VM',38.7,49.35)
trace('VCC',[(37.5625,52.25),(39,52.25)],.2);via('VCC',39,52.25)
trace('VCC',[(39,52.25),(39,54.5),(36.275,54.5)],.4,p.B_Cu)
# Gate damping resistors connect directly to their package gates.
for i,y in enumerate([28,42,56],1):
 for terminal,rr,xx in [('GH',410+10*(i-1)+1,67),('GL',410+10*(i-1)+2,61)]:
  q=pad('R'+str(rr),2);net=q.GetNetname();pos=q.GetPosition();end=(p.ToMM(pos.x)-100,p.ToMM(pos.y)-100)
  if terminal=='GH':trace(net,[(66.35,y+2.5),(67,y+2.5),end],.25)
  else:trace(net,[(61.65,y+2.5),(60.7,y+2.5),(60.7,y+4.375),end],.25)
 trace('OUT'+str(i),[(69,y+3.175),(71.2,y+3.175),(71.7,y+2.675),(71.7,y+1.8)],.4)

# Preserve candidate project settings and append only the local escape rules.
name='local_candidate'
shutil.copy2(O/'power_v2.kicad_pro',O/(name+'.kicad_pro'))
(O/(name+'.kicad_dru')).write_text((O/'power_v2.kicad_dru').read_text()+'\n# Local fanout: 0.15 mm remains the supplied 2 oz minimum.\n'+'\n'.join(rules)+'\n')
# Load rules by saving and reopening under this basename before refill.
p.SaveBoard(str(O/(name+'.kicad_pcb')),b)
b=p.LoadBoard(str(O/(name+'.kicad_pcb')));b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(O/(name+'.kicad_pcb')),b)
print('Saved',name)
