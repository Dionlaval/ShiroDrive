from pathlib import Path
import pcbnew as p,json,shutil,hashlib
r=Path(__file__).resolve().parent.parent;src=r/'brake/bridge_fine/ShiroFOC_Manual.kicad_pcb';dst=r/'brake/final/ShiroFOC_Manual.kicad_pcb';shutil.copy2(src,dst)
b=p.LoadBoard(str(dst));base=r/'merged_03/ShiroFOC_Manual.kicad_pcb';bb=p.LoadBoard(str(base));uid=lambda t:t.m_Uuid.AsString();oldids={uid(t)for t in bb.GetTracks()};newids={uid(t)for t in b.GetTracks()};moves=json.loads((r/'brake/moves.json').read_text())['footprint_moves'];manifest={'source':str(base),'candidate':str(dst),'candidate_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'removed_ids':sorted(oldids-newids),'new_ids':sorted(newids-oldids),'footprint_moves':moves,'groups':[]}
for netname in sorted({t.GetNetname()for t in b.GetTracks()if uid(t)in newids-oldids}):
 items=[t for t in b.GetTracks()if t.GetNetname()==netname and uid(t)in newids-oldids]
 manifest['groups'].append({'id':netname,'net':netname,'new_items':[uid(t)for t in items],'new_length_mm':sum(p.ToMM(t.GetLength())for t in items if not isinstance(t,p.PCB_VIA)),'new_vias':sum(isinstance(t,p.PCB_VIA)for t in items)})
(dst.parent/'delta.json').write_text(json.dumps(manifest,indent=2)+'\n');(dst.parent/'replacements.json').write_text(json.dumps(manifest['removed_ids'],indent=2)+'\n');(dst.parent/'moves.json').write_text(json.dumps({'footprint_moves':moves},indent=2)+'\n');print(json.dumps({'sha256':manifest['candidate_sha256'],'groups':[{k:v for k,v in g.items()if k!='new_items'}for g in manifest['groups']]}))
