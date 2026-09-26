#!/usr/bin/env python3
"""Open an underside gate corridor; candidate, native DRC required."""
import pcbnew as p
from pathlib import Path
import sys,shutil,json
src,dst=map(Path,sys.argv[1:3])
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
b=p.LoadBoard(str(src));fs={f.GetReference():f for f in b.GetFootprints()};mm=p.FromMM;v=lambda x,y:p.VECTOR2I(mm(x+100),mm(y+100))
removed=[]
# Remove only the former dedicated C304/C306 ground stubs and vias.
for t in list(b.GetTracks()):
 if t.GetNetname()!='GND':continue
 pt=t.GetPosition();x,y=p.ToMM(pt.x)-100,p.ToMM(pt.y)-100
 if any(abs(x-a)<.03 and abs(y-c)<.03 for a,c in [(48.975,43.875),(48.975,43),(52.375,44.6),(54.9,44)]):removed.append(t.m_Uuid.AsString());b.RemoveNative(t)
fs['C306'].SetPosition(v(51.6,40.2))
fs['R301'].SetPosition(v(45,40.8))
fs['R602'].SetPosition(v(40.35,45.6))
def via(x,y):
 t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(mm(.45));t.SetDrill(mm(.2));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet('GND'));t.SetLocked(True);b.Add(t)
def tr(a,c):
 t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*c));t.SetWidth(mm(.25));t.SetLayer(p.B_Cu);t.SetNet(b.FindNet('GND'));t.SetLocked(True);b.Add(t)
tr((48.975,43),(49.55,43));via(49.55,43)
tr((52.375,40.2),(54.25,40.2));via(54.25,40.2)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b);print('moved C306 R301 R602, removed ground items',len(removed))
