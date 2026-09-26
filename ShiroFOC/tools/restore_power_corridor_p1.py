#!/usr/bin/env python3
"""Remove ordinary routing that fragments the fixed front VM distribution bar."""
import pcbnew as p
import sys,shutil,json
from pathlib import Path
src,dst=map(Path,sys.argv[1:3]);b=p.LoadBoard(str(src));mm=p.FromMM
z=next(z for z in b.Zones()if z.GetZoneName()=='VM_VERTICAL_FRONT');removed=[]
for t in list(b.GetTracks()):
 if t.IsLocked()or isinstance(t,p.PCB_VIA)or t.GetLayer()!=p.F_Cu or t.GetNetname()=='VM':continue
 if z.Outline().Collide(t.GetEffectiveShape(p.F_Cu),mm(.5)):
  # Local gate pulls and source branches may enter the right edge, but signal
  # routes may not make long cuts through the bus.
  if 'FORCE_P' in t.GetNetname()or t.GetNetname().startswith('Net-(Q40'):continue
  removed.append([t.m_Uuid.AsString(),t.GetNetname()]);b.RemoveNative(t)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b)
dst.with_suffix('.removed.json').write_text(json.dumps(removed,indent=2));print('Removed',len(removed),'fragments')
