from pathlib import Path
import pcbnew as p,json,shutil,hashlib
r=Path(__file__).resolve().parent.parent;src=r/'brake/sck_final/ShiroFOC_Manual.kicad_pcb';dst=r/'brake/final/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(m.GetProject(str(src.with_suffix('.kicad_pro'))));b.SynchronizeNetsAndNetClasses(False)
uid=lambda t:t.m_Uuid.AsString();vec=lambda a:p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1]));ts=list(b.GetTracks());old=next(t for t in ts if uid(t)=='bd195ca8-b0fd-4277-beca-03d5e247e4d5');net=old.GetNet();b.Remove(old)
pts=[(-10.899999,-4),(-10.899999,-.2),(-11.25,.15),(-11.25,2.2),(-10.899999,2.55)]
for a,c in zip(pts,pts[1:]):
 t=p.PCB_TRACK(b);t.SetStart(vec(a));t.SetEnd(vec(c));t.SetWidth(p.FromMM(.1524));t.SetLayer(p.B_Cu);t.SetNet(net);b.Add(t)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b)
base=r/'merged_03/ShiroFOC_Manual.kicad_pcb';bb=p.LoadBoard(str(base));oldids={uid(t)for t in bb.GetTracks()};newids={uid(t)for t in b.GetTracks()};moves=json.loads((r/'brake/moves.json').read_text())['footprint_moves'];manifest={'source':str(base),'candidate':str(dst),'candidate_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'removed_ids':sorted(oldids-newids),'new_ids':sorted(newids-oldids),'footprint_moves':moves,'groups':[]}
for netname in sorted({t.GetNetname()for t in b.GetTracks()if uid(t)in newids-oldids}):
 items=[t for t in b.GetTracks()if t.GetNetname()==netname and uid(t)in newids-oldids]
 manifest['groups'].append({'id':netname,'net':netname,'new_items':[uid(t)for t in items],'new_length_mm':sum(p.ToMM(t.GetLength())for t in items if not isinstance(t,p.PCB_VIA)),'new_vias':sum(isinstance(t,p.PCB_VIA)for t in items)})
(dst.parent/'delta.json').write_text(json.dumps(manifest,indent=2)+'\n');(dst.parent/'replacements.json').write_text(json.dumps(manifest['removed_ids'],indent=2)+'\n');(dst.parent/'moves.json').write_text(json.dumps({'footprint_moves':moves},indent=2)+'\n');print(json.dumps(manifest,indent=2))
