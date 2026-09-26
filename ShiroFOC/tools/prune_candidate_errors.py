#!/usr/bin/env python3
"""Remove only unlocked candidate route fragments implicated by native DRC errors.
Does not suppress rules or remove footprints, zones, or protected manual routing.
"""
from pathlib import Path
import pcbnew as p
import json,sys,shutil
src,report,dst=map(Path,sys.argv[1:4]);b=p.LoadBoard(str(src));ts={t.m_Uuid.AsString():t for t in b.GetTracks()};remove=set()
for v in json.loads(report.read_text())['violations']:
 if v['severity']!='error':continue
 for a in v['items']:
  t=ts.get(a['uuid'])
  if t is not None and not t.IsLocked():remove.add(a['uuid'])
for uid in remove:b.RemoveNative(ts[uid])
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b);print('Removed',len(remove),'unlocked conflicting segments/vias')
