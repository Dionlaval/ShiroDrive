from pathlib import Path
import pcbnew as p,json,shutil,hashlib
r=Path(__file__).resolve().parent.parent;src=r/'combined_can_brake/grounded/ShiroFOC_Manual.kicad_pcb';dst=r/'combined_can_brake/final/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True);cfg=r/'combined_can_brake/sequential'
for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(cfg/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((cfg/'libs').resolve(),target_is_directory=True)

for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(cfg/name,src.parent/name)
if not(src.parent/'libs').exists():(src.parent/'libs').symlink_to((cfg/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro').resolve()));b=p.LoadBoard(str(src));b.SetProject(m.GetProject(str(src.with_suffix('.kicad_pro').resolve())));b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b)
base=r/'merged_03/ShiroFOC_Manual.kicad_pcb';bb=p.LoadBoard(str(base));uid=lambda t:t.m_Uuid.AsString();oldids={uid(t)for t in bb.GetTracks()};newids={uid(t)for t in b.GetTracks()};moves=json.loads((r/'brake/final/moves.json').read_text())['footprint_moves'];manifest={'source':str(base),'candidate':str(dst),'candidate_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'removed_ids':sorted(oldids-newids),'new_ids':sorted(newids-oldids),'footprint_moves':moves,'groups':[]}
for netname in sorted({t.GetNetname()for t in b.GetTracks()if uid(t)in newids-oldids}):
 items=[t for t in b.GetTracks()if t.GetNetname()==netname and uid(t)in newids-oldids];manifest['groups'].append({'id':netname,'net':netname,'new_items':[uid(t)for t in items],'new_length_mm':sum(p.ToMM(t.GetLength())for t in items if not isinstance(t,p.PCB_VIA)),'new_vias':sum(isinstance(t,p.PCB_VIA)for t in items)})
(dst.parent/'delta.json').write_text(json.dumps(manifest,indent=2)+'\n');(dst.parent/'replacements.json').write_text(json.dumps(manifest['removed_ids'],indent=2)+'\n');(dst.parent/'moves.json').write_text(json.dumps({'footprint_moves':moves},indent=2)+'\n');print(manifest['candidate_sha256'])
