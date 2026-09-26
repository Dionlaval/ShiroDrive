#!/usr/bin/env python3
"""Short explicit amplifier feedback loops; candidate only until native DRC."""
from pathlib import Path
import pcbnew as p
import sys,shutil,json
src=Path(sys.argv[1]);dst=Path(sys.argv[2]);b=p.LoadBoard(str(src));mm=p.FromMM;v=lambda x,y:p.VECTOR2I(mm(x+100),mm(y+100));nets={n.GetNetname():n for n in b.GetNetInfo().NetsByNetcode().values()};added={}
def tr(net,pts,ly=p.B_Cu):
 for a,c in zip(pts,pts[1:]):
  t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*c));t.SetWidth(mm(.2));t.SetLayer(ly);t.SetNet(nets[net]);t.SetLocked(True);b.Add(t);added[t.m_Uuid.AsString()]=net

def vi(net,x,y):
 t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(mm(.45));t.SetDrill(mm(.2));t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetViaType(p.VIATYPE_THROUGH);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);t.SetNet(nets[net]);t.SetLocked(True);b.Add(t);added[t.m_Uuid.AsString()]=net
P=lambda phase:'/Current / temperature/OPP_'+phase+'1'
N=lambda phase:'/Current / temperature/OPN_'+phase+'1'
# Move the two local ground vias clear of the short underside feedback traces.
for t in list(b.GetTracks()):
 if t.GetNetname()=='GND':
  if isinstance(t,p.PCB_VIA):
   x,y=p.ToMM(t.GetPosition().x)-100,p.ToMM(t.GetPosition().y)-100
   if abs(x-50.4)<.001 and abs(y-47.1)<.001:t.SetPosition(v(50.6,47.05))
   if abs(x-49.775)<.001 and abs(y-49.8)<.001:t.SetPosition(v(49.775,50.4))
  elif abs(p.ToMM(t.GetEnd().x)-150.4)<.001 and abs(p.ToMM(t.GetEnd().y)-147.1)<.001:t.SetEnd(v(50.6,47.05))
 if isinstance(t,p.PCB_VIA)and t.GetNetname()in[P('U'),P('V')]:b.RemoveNative(t)
 elif t.GetNetname()==P('V')and t.GetLayer()==p.F_Cu:b.RemoveNative(t)
tr('GND',[(49.775,49.8),(49.775,50.4)],p.F_Cu)
# W network
tr(N('W'),[(45.75,48.75),(46.2,48.85),(49.925,48.85),(49.925,48),(49.225,48)])
tr(N('W'),[(49.925,48),(50.775,48)])
tr(N('W'),[(49.175,46.3),(49.925,46.3),(49.925,48)])
tr('OPO_W1',[(45.25,49.25),(45,49.25),(45,47),(45.7,46),(47.625,46.3),(47.575,48)])
tr(P('W'),[(45.75,49.75),(50.775,49.7),(50.775,51.4),(49.225,51.4)])
# V network
tr(N('V'),[(45.25,50.25),(46.2,50.25),(46.8,50.85),(46.8,52.25),(49.925,52.25),(49.925,53.1),(49.225,53.1)])
tr(N('V'),[(49.925,53.1),(50.775,53.1)])
tr(N('V'),[(49.925,53.1),(49.925,54.8),(49.175,54.8)])
tr('OPO_V1',[(45.75,51.75),(46.05,52.25),(46.05,53.1),(47.575,53.1),(47.625,54.8)])
tr('OPO_V1',[(45.75,51.75),(45.75,52.2)])
tr(P('V'),[(46.4375,51.25),(47.3,51.25),(47.3,51.6),(50.5,54.8)],p.F_Cu);vi(P('V'),50.5,54.8)
tr(P('V'),[(50.5,54.8),(50.775,54.8),(50.775,56.5),(49.225,56.5)])
# U network
tr(N('U'),[(46.25,54.2),(46.25,55.3),(45.825,55.3),(45.775,57),(46.65,57),(47.575,57.925),(47.575,58.2)])
tr('OPO_U1',[(45.25,53),(45.5,53.25),(45.5,54.35),(44.55,55.3),(44.175,55.3),(44.225,57)])
tr('OPO_U1',[(44.175,55.3),(43.675,55.8),(42,55.8)])
tr(P('U'),[(44.8,54.4),(46,54.8),(46,57.2),(44.5,58.15),(44.175,58.25)],p.F_Cu);vi(P('U'),44.175,58.25)
tr(P('U'),[(44.175,58.25),(44.175,58.7),(44.175,59.4),(45.3,59.4),(45.3,60.4),(45.825,60.4),(47.575,60.4)])
# Re-route only pre-existing ordinary signals that conflict with these local loops.
new=[t for t in b.GetTracks()if t.m_Uuid.AsString()in added];removed=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString()in added or t.IsLocked():continue
 for q in new:
  if t.GetNetname()==q.GetNetname():continue
  bb=t.GetBoundingBox();bb.Inflate(mm(.21))
  if not bb.Intersects(q.GetBoundingBox()):continue
  if any(t.IsOnLayer(ly)and q.IsOnLayer(ly)and t.GetEffectiveShape(ly).Collide(q.GetEffectiveShape(ly),mm(.201))for ly in[p.F_Cu,p.B_Cu]):removed.append(t.m_Uuid.AsString());b.RemoveNative(t);break
for ext in['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
p.SaveBoard(str(dst),b);b=p.LoadBoard(str(dst));b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b)
assert all(t.GetNetname()==added[t.m_Uuid.AsString()]for t in b.GetTracks()if t.m_Uuid.AsString()in added)
dst.with_suffix('.amplifiers.json').write_text(json.dumps(added,indent=2));print('Saved',dst,'removed ordinary conflicts',len(removed))
