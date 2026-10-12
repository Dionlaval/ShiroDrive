from pathlib import Path
import json,shutil,pcbnew as p
r=Path(__file__).resolve().parent;src=r/'brake_stagger/ShiroFOC_Manual.kicad_pcb';dst=r/'stagger_bopen/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(parents=True,exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));project=m.GetProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False);tracks=list(b.GetTracks());remove=[t.m_Uuid.AsString() for t in tracks if t.GetNetname()=='SPI3_MOSI_MCU' and t.GetLayer()==p.B_Cu and t.Type()==p.PCB_TRACE_T]
for t in tracks:
 if t.m_Uuid.AsString() in remove:b.Remove(t)
b.BuildConnectivity();p.SaveBoard(str(dst),b);(dst.parent/'removed.json').write_text(json.dumps(remove,indent=2))
