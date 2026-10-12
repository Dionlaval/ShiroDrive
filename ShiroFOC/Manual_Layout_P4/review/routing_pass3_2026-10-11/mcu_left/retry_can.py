from pathlib import Path
import json, shutil, pcbnew as p
root=Path(__file__).resolve().parent;src=root/'can_return/ShiroFOC_Manual.kicad_pcb';dst=root/'can_retry_open/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(m.GetProject(str(src.with_suffix('.kicad_pro'))));b.SynchronizeNetsAndNetClasses(False)
keep={'20c4d97f-78cc-4960-b204-77fd0724cb01','218d591d-fb1a-42c8-a97f-35fce554cc4b','775a4041-16d3-45d1-8c0b-8bf65be169bb','3cd693bc-5d0e-4f10-9680-8769383d33a9'}
tracks=list(b.GetTracks());removed=[]
for t in tracks:
    if t.GetNetname()=='CAN_TERM_DISABLE' and t.m_Uuid.AsString() not in keep:
        removed.append(t);b.Remove(t)
b.BuildConnectivity();fill=p.ZONE_FILLER(b);fill.Fill(b.Zones());p.SaveBoard(str(dst),b)
(dst.parent/'removed.json').write_text(json.dumps([t.m_Uuid.AsString() for t in removed],indent=2))
print(len(removed))
