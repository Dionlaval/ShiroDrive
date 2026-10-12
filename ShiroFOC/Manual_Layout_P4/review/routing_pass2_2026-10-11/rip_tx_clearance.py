from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parent;s=r/'conflicts_rerouted/ShiroFOC_Manual.kicad_pcb';d=r/'tx_clearance_ripped/ShiroFOC_Manual.kicad_pcb';d.parent.mkdir(exist_ok=True)
for n in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(s.parent/n,d.parent/n)
if not(d.parent/'libs').exists():(d.parent/'libs').symlink_to((s.parent/'libs').resolve(),target_is_directory=True)
ids={'558d9ff0-8afe-443d-b474-d7cfbd42b5a7'}
b=p.LoadBoard(str(s));old=list(b.GetTracks());found=set()
for t in old:
 if t.m_Uuid.AsString()in ids:found.add(t.m_Uuid.AsString());b.Remove(t)
assert found==ids;p.SaveBoard(str(d),b);(d.parent/'removed.json').write_text(json.dumps(sorted(ids),indent=2));print(len(ids))
