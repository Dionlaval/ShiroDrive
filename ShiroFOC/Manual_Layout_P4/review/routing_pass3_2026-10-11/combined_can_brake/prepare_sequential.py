from pathlib import Path
import pcbnew as p,shutil,json
r=Path(__file__).resolve().parent.parent;src=r/'combined_can_brake/ShiroFOC_Manual.kicad_pcb';dst=r/'combined_can_brake/seeded/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
b=p.LoadBoard(str(src));ts=list(b.GetTracks());uid=lambda t:t.m_Uuid.AsString();keep={'20c4d97f-78cc-4960-b204-77fd0724cb01','218d591d-fb1a-42c8-a97f-35fce554cc4b','775a4041-16d3-45d1-8c0b-8bf65be169bb'}
cannew=set(json.loads((r/'mcu_left/can_final/delta.json').read_text())['new_ids']);brakeroute=json.loads((r/'brake/brake_path/ShiroFOC_Manual.routes.json').read_text());remove=set(u for c in brakeroute['connections']for u in c['new_items']);remove.update(uid(t)for t in ts if uid(t)in cannew and t.GetNetname()=='CAN_TERM_DISABLE' and uid(t)not in keep)
for t in ts:
 if uid(t)in remove:b.Remove(t)
b.BuildConnectivity();p.SaveBoard(str(dst),b);(dst.parent/'pruned_connections.json').write_text(json.dumps({'removed_new_ids':sorted(remove)},indent=2))
