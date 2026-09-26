#!/usr/bin/env python3
"""Candidate-only removal of ordinary routes obstructing critical MCU escapes."""
import pcbnew as p
from pathlib import Path
import json,sys,shutil,os
src,dst=map(Path,sys.argv[1:3])
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
b=p.LoadBoard(str(src));removed=[]
critical=lambda net: net in ['GND','VM','VCC','OUT1','OUT2','OUT3'] or net.startswith(('GHS','GLS','BOOT')) or 'SENSE_' in net or 'FORCE_' in net or '/Current ' in net or net.startswith('OPO_')
for t in list(b.GetTracks()):
 if t.IsLocked() or critical(t.GetNetname()):continue
 box=t.GetBoundingBox();x=p.ToMM(box.GetX())-100;y=p.ToMM(box.GetY())-100;w=p.ToMM(box.GetWidth());h=p.ToMM(box.GetHeight())
 bounds=(70,35,67,25)if os.environ.get('SHIRO_CLEAR_DRIVER_REGION')else(52,35,56,38)
 if x<=bounds[0] and x+w>=bounds[1] and y<=bounds[2] and y+h>=bounds[3]:
  removed.append({'uuid':t.m_Uuid.AsString(),'net':t.GetNetname()});b.RemoveNative(t)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b)
dst.with_suffix('.removed.json').write_text(json.dumps(removed,indent=2));print('Removed',len(removed),'ordinary items from',len(set(t['net']for t in removed)),'nets')
