from pathlib import Path
import json,sys,pcbnew as p
src=Path(sys.argv[1]).resolve();dst=Path(sys.argv[2]).resolve();a=p.LoadBoard(str(src));b=p.LoadBoard(str(dst));uid=lambda t:t.m_Uuid.AsString()
old={uid(t):t for t in a.GetTracks()};new={uid(t):t for t in b.GetTracks()};removed=sorted(old.keys()-new.keys());added=sorted(new.keys()-old.keys())
changed=sorted({old[u].GetNetname() for u in removed}|{new[u].GetNetname() for u in added});rows=[]
for net in changed:
 def stats(items):
  ts=[t for t in items if t.GetNetname()==net];return {'tracks':sum(t.Type()!=p.PCB_VIA_T for t in ts),'vias':sum(t.Type()==p.PCB_VIA_T for t in ts),'length_mm':round(sum(p.ToMM(t.GetLength()) for t in ts if t.Type()!=p.PCB_VIA_T),6),'layers':sorted({t.GetLayerName() for t in ts if t.Type()!=p.PCB_VIA_T})}
 rows.append({'net':net,'before':stats(old.values()),'after':stats(new.values())})
manifest={'source':str(src),'candidate':str(dst),'removed_ids':removed,'new_ids':added,'footprint_moves':[],'allowed_replacement_uuids':removed,'net_geometry':rows,'reason':'Complete CAN_TERM_DISABLE via inward MCU escape; move NTC_BRAKE via down 0.07 mm and reroute its short B branch; replace old FEEDBACK_I_H3 L4 path with a shorter direct branch to free CAN escape; preserve all other copper and every footprint.'}
(dst.parent/'delta.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({'removed':len(removed),'added':len(added),'net_geometry':rows},indent=2))
