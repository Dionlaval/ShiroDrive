from pathlib import Path
import json,shutil,pcbnew as p
r=Path(__file__).resolve().parent;src=r/'crystal_shift/ShiroFOC_Manual.kicad_pcb';dst=r/'crystal_imu_open/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(parents=True,exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));project=m.GetProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False);tracks=list(b.GetTracks());remove=['d04e1ded-c943-4c81-aa4f-c115969ee95d','45457d05-838e-4522-9d90-511cfb65d0ba','1b4f795c-e389-45e0-8123-8eb1a9875948']
for t in tracks:
 if t.m_Uuid.AsString() in remove:b.Remove(t)
b.BuildConnectivity();p.SaveBoard(str(dst),b);(dst.parent/'removed.json').write_text(json.dumps(remove,indent=2))
