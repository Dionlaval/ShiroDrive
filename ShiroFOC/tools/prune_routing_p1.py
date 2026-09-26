#!/usr/bin/env python3
"""Remove only imported abandoned stubs/conflicts using native DRC; preserve manual work."""
import pcbnew as p
import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parents[1]/'ShiroFOC_KiCad_P1/outputs/routing_P1';pcb=O/'merged_candidate.kicad_pcb';report=O/'merged_drc.json'
imported=set(json.loads((O/'merged_tracks.json').read_text()))
for iteration in range(12):
 subprocess.run(['/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli','pcb','drc','--format','json','--output',str(report),str(pcb)],check=True,capture_output=True)
 drc=json.loads(report.read_text());remove=set()
 for v in drc['violations']:
  if v['type'] in ['track_dangling','via_dangling','clearance','hole_clearance','shorting_items','solder_mask_bridge']:
   for i in v['items']:
    if i['uuid'] in imported:remove.add(i['uuid'])
 print(iteration,'prune',len(remove),'unconnected',len(drc['unconnected_items']),flush=True)
 if not remove:break
 b=p.LoadBoard(str(pcb))
 for t in list(b.GetTracks()):
  if t.m_Uuid.AsString()in remove:b.RemoveNative(t)
 b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(pcb),b)
else:print('Stopped bounded prune; inspect remaining stubs')
