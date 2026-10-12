from pathlib import Path
import json,shutil,pcbnew as p
r=Path(__file__).resolve().parent;src=r/'mosi_direct/ShiroFOC_Manual.kicad_pcb';dst=r/'sensor_open/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(parents=True,exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));project=m.GetProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False);tracks=list(b.GetTracks());remove=['77dfdfc9-1396-4153-9e22-1abb364fdd0b','7101b557-cdb5-4525-9871-e1d5676a693b','bb645252-ebca-4d23-bb1c-5b503bb52685','ea4bf122-a06b-4bc1-8974-6db1395ef27c','cb382197-e25d-4d1c-8c8f-542e3cf1568b']
for t in tracks:
 if t.m_Uuid.AsString() in remove:b.Remove(t)
b.BuildConnectivity();p.SaveBoard(str(dst),b);(dst.parent/'removed.json').write_text(json.dumps(remove,indent=2))
