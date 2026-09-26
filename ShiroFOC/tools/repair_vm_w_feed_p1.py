#!/usr/bin/env python3
"""Route the W gate-pull source branch around the back VM feed it bisected."""
import pcbnew as p
from pathlib import Path
import shutil,sys
src,dst=map(Path,sys.argv[1:3]);b=p.LoadBoard(str(src));mm=p.FromMM
v=lambda x,y:p.VECTOR2I(mm(100+x),mm(100+y));net=b.FindNet('/Three-phase bridge/SHUNT_W_FORCE_P')
removed=0
for t in list(b.GetTracks()):
 if isinstance(t,p.PCB_VIA)or t.GetLayer()!=p.B_Cu or t.GetNetname()!=net.GetNetname():continue
 a,c=t.GetStart(),t.GetEnd()
 if abs(p.ToMM(a.x)-159.45)<.01 and abs(p.ToMM(c.x)-159.45)<.01 and t.GetLength()>mm(8):
  b.RemoveNative(t);removed+=1
assert removed==1,removed
pts=[(59.45,53.125),(54.4,53.125),(54.4,61.959),(59.45,61.959)]
for a,c in zip(pts,pts[1:]):
 t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*c));t.SetWidth(mm(.3));t.SetLayer(p.B_Cu);t.SetNet(net);t.SetLocked(True);b.Add(t)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b);print(dst)
