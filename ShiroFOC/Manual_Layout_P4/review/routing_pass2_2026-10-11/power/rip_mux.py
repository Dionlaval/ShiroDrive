from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parent.parent;s=r/'power_6mil/ShiroFOC_Manual.kicad_pcb';d=r/'power_mux_ripped/ShiroFOC_Manual.kicad_pcb';d.parent.mkdir(exist_ok=True)
for n in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(s.parent/n,d.parent/n)
if not(d.parent/'libs').exists():(d.parent/'libs').symlink_to((s.parent/'libs').resolve(),target_is_directory=True)
b=p.LoadBoard(str(s));old=list(b.GetTracks());removed=[]
for t in old:
 if t.GetNetname()=='VBUS_MUX_IN' and t.m_Uuid.AsString()!='ed132d44-0729-4fd3-95af-b76c9c122225':removed.append(t.m_Uuid.AsString());b.Remove(t)
p.SaveBoard(str(d),b);(d.parent/'removed.json').write_text(json.dumps(removed,indent=2));print(len(removed))
