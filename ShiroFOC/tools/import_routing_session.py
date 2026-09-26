#!/usr/bin/env python3
import pcbnew as p
import shutil,sys
from pathlib import Path
src,ses,dst=map(Path,sys.argv[1:4]);b=p.LoadBoard(str(src));coords={f.GetReference():(f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.IsFlipped()) for f in b.GetFootprints()};pins={(f.GetReference(),q.GetNumber(),q.GetPosition().x,q.GetPosition().y):q.GetNetname() for f in b.GetFootprints() for q in f.Pads()}
print('Before',len(list(b.GetTracks())),flush=True)
assert p.ImportSpecctraSES(b,str(ses))
print('Imported',len(list(b.GetTracks())),flush=True)
assert coords=={f.GetReference():(f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.IsFlipped()) for f in b.GetFootprints()}
assert pins=={(f.GetReference(),q.GetNumber(),q.GetPosition().x,q.GetPosition().y):q.GetNetname() for f in b.GetFootprints() for q in f.Pads()}
for suffix in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(suffix),dst.with_suffix(suffix))
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b);print(dst)
