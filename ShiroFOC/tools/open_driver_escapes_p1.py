#!/usr/bin/env python3
"""Open the driver pin escapes while keeping the compact bootstrap circuits."""
from pathlib import Path
import pcbnew as p
import sys,shutil
src,dst=map(Path,sys.argv[1:3]);b=p.LoadBoard(str(src));fs={f.GetReference():f for f in b.GetFootprints()};mm=p.FromMM
v=lambda x,y:p.VECTOR2I(mm(100+x),mm(100+y))
abi={q.GetNetname()for q in fs['R602'].Pads()};oldpads=list(fs['R301'].Pads())
for t in list(b.GetTracks()):
 net=t.GetNetname();a=t.GetPosition();x,y=p.ToMM(a.x)-100,p.ToMM(a.y)-100
 remove=net in ['GHS1','GHS3']
 if net=='OUT1'and t.GetLayer()==p.F_Cu and x<43 and 40<y<46:remove=True
 if not t.IsLocked() and net in abi:remove=True
 if not t.IsLocked()and t.IsOnLayer(p.B_Cu)and net in ['3V3','VDDA']and any(q.GetEffectiveShape(p.B_Cu).Collide(t.GetEffectiveShape(p.B_Cu),mm(.1))for q in oldpads):remove=True
 if remove:b.RemoveNative(t)
fs['R602'].SetPosition(v(40.35,45.6))
fs['R301'].SetPosition(v(45,42.4));fs['R301'].SetOrientationDegrees(90)
for t in list(b.GetTracks()):
 if t.IsLocked()or not t.IsOnLayer(p.B_Cu):continue
 if any(q.GetNetname()!=t.GetNetname()and q.GetEffectiveShape(p.B_Cu).Collide(t.GetEffectiveShape(p.B_Cu),mm(.21))for ref in ['R602','R301']for q in fs[ref].Pads()):b.RemoveNative(t)
def track(net,pts,w=.2):
 for a,c in zip(pts,pts[1:]):
  t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*c));t.SetWidth(mm(w));t.SetLayer(p.F_Cu);t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
def via(net,x,y):
 t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(mm(.45));t.SetDrill(mm(.2));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet(net));t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);t.SetLocked(True);b.Add(t)
track('OUT1',[(41.25,44.5625),(41.25,43.5),(41.15,43.4),(39.725,43.4),(39.225,42.9),(39.225,41.9)],.25)
for net,x in [('GHS1',40.75),('GHS3',43.75)]:track(net,[(x,44.5625),(x,43.95)]);via(net,x,43.95)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b);print(dst)
