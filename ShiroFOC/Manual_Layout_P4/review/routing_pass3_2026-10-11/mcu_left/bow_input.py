from pathlib import Path
import json, shutil, pcbnew as p
root=Path(__file__).resolve().parent;src=root/'input_opened/ShiroFOC_Manual.kicad_pcb';dst=root/'input_bow/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(m.GetProject(str(src.with_suffix('.kicad_pro'))));b.SynchronizeNetsAndNetClasses(False)
tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};v=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y));codes={q.GetNetname():q.GetNetCode() for q in b.GetNetInfo().NetsByNetcode().values()};added=[]
remove=['3496956d-1784-41e7-abe2-55f09c73f642','914fc82b-7119-4c97-a344-67bb06375b86']
for u in remove:b.Remove(tracks[u])
points=[(-7.35,4.15),(-7.35,4.475),(-7.275,4.55),(-7.275,5.3),(-7.799999,5.824999),(-7.799999,5.825)]
for a,c in zip(points,points[1:]):
    if a==c:continue
    t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*c));t.SetWidth(p.FromMM(.1524));t.SetLayer(6);t.SetNetCode(codes['IMU_INT2']);b.Add(t);added.append(t)
b.BuildConnectivity();fill=p.ZONE_FILLER(b);fill.Fill(b.Zones());p.SaveBoard(str(dst),b)
(dst.parent/'bow_delta.json').write_text(json.dumps({'candidate':str(dst),'removed_ids':remove,'new_ids':[t.m_Uuid.AsString()for t in added]},indent=2))
