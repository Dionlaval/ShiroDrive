#!/usr/bin/env python3
import pcbnew as p
from pathlib import Path
import sys,shutil
src,dst=map(Path,sys.argv[1:3])
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
b=p.LoadBoard(str(src));mm=p.FromMM
for net,x,y in [('OUT2',42.625,41.9),('GLS1',50.6,46.4)]:
 t=p.PCB_VIA(b);t.SetPosition(p.VECTOR2I(mm(100+x),mm(100+y)));t.SetWidth(mm(.45));t.SetDrill(mm(.2));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b)
