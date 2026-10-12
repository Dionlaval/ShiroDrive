from pathlib import Path
import pcbnew as p,shutil
r=Path(__file__).resolve().parent;src=r/'final/ShiroFOC_Manual.kicad_pcb';dst=r/'cleaned/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
b=p.LoadBoard(str(src));items={t.m_Uuid.AsString():t for t in b.GetTracks()};vec=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
items['4514634a-99aa-4715-91df-857eec07cbd0'].SetStart(vec(-6.549999,2.05));items['e018b9c3-452c-4ada-a973-384789a422eb'].SetStart(vec(-7.85,.6));b.BuildConnectivity();p.SaveBoard(str(dst),b)
