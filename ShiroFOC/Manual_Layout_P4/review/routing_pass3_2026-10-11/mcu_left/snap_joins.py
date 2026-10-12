from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parent;src=r/'input_b_raw/ShiroFOC_Manual.kicad_pcb';dst=r/'input_b_clean/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
for n in ['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/n,dst.parent/n)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(m.GetProject(str(src.with_suffix('.kicad_pro'))));b.SynchronizeNetsAndNetClasses(False)
old={t.m_Uuid.AsString():t for t in b.GetTracks()};ret=[];new=[]
changes={
'57250b9f-c681-4d21-a3b7-d6c51df907f9':((-10825000,4875000),(-10825000,4425000)),
'42384102-861b-432b-b856-229d232054cb':((-10825000,4425000),(-10850000,4400000)),
'a54c6ec6-7223-4c52-b5f4-7b64a83f92ec':((-9899999,5350000),(-9949999,5300000)),
'42158abe-2bd3-408f-983b-14509e3850ac':((-9949999,5300000),(-10399999,5300000)),
'8b18f3b9-ccc6-476c-a979-a364c06959bd':((-7850000,10875000),(-7850000,13450000)),
'a4ba40a5-7640-4ed3-a7dc-03c1d92900d4':((-7850000,13450000),(-7899999,13500000))}
for uid,(a,c) in changes.items():
 t=old[uid];newt=p.PCB_TRACK(b);newt.SetNetCode(t.GetNetCode());newt.SetLayer(t.GetLayer());newt.SetWidth(t.GetWidth());newt.SetStart(p.VECTOR2I(*a));newt.SetEnd(p.VECTOR2I(*c));b.Remove(t);b.Add(newt);ret.append(t);new.append(newt)
b.BuildConnectivity();fill=p.ZONE_FILLER(b);assert fill.Fill(b.Zones());p.SaveBoard(str(dst),b)
(dst.parent/'cleanup_delta.json').write_text(json.dumps(dict(source=str(src),candidate=str(dst),removed_ids=list(changes),new_ids=[t.m_Uuid.AsString() for t in new],reason='Snap six newly-added NTC_BRAKE/H2 track endpoints exactly to existing copper, eliminating75um residual gaps and narrow contacts without changing nets or widths.'),indent=2))
print(dst)
