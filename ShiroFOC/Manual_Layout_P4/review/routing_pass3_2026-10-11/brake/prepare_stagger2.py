from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parent.parent;src=r/'brake/source/ShiroFOC_Manual.kicad_pcb';dst=r/'brake/stagger2/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
b=p.LoadBoard(str(src));tracks=list(b.GetTracks());items={t.m_Uuid.AsString():t for t in tracks};vec=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y));new=[]
replacements={
 '7120371e-58cd-4c00-a0af-19ab917e254b':[(-4.25,2.85),(-4.25,3.05)],
 'a5235df3-adb8-4bed-bf9a-e357cde95d45':[(-4.25,3.05),(-3.25,4.05)],
 '829ac1c9-1dde-4f03-be29-ad973c260c6f':[(-3.25,4.05),(-2.449999,4.05)]}
for identifier,(a,c) in replacements.items():
 t=items[identifier];q=p.PCB_TRACK(b);q.SetStart(vec(*a));q.SetEnd(vec(*c));q.SetWidth(p.FromMM(.1524));q.SetLayer(p.F_Cu);q.SetNet(t.GetNet());b.Add(q);new.append(q);b.Remove(t)
items['ff23011b-82ab-4d15-9634-1d7b1334ecff'].SetEnd(vec(-4.849937,3.0))
items['2cd7b438-1cb1-49f8-8488-a3df1f5ddd02'].SetStart(vec(-4.849937,3.0));items['2cd7b438-1cb1-49f8-8488-a3df1f5ddd02'].SetEnd(vec(-4.15,3.7))
items['db303283-9d70-43a3-8773-ecfeb93fec2b'].SetStart(vec(-4.15,3.7))
for t in tracks:
 if t.GetNetname()!='Net-(U601-MOSI)':continue
 if isinstance(t,p.PCB_VIA) and t.GetPosition()==vec(-4.7,4.1):t.SetPosition(vec(-4.7,3.85))
 elif not isinstance(t,p.PCB_VIA):
  if t.GetStart()==vec(-4.7,4.1):t.SetStart(vec(-4.7,3.85))
  if t.GetEnd()==vec(-4.7,4.1):t.SetEnd(vec(-4.7,3.85))
b.BuildConnectivity();p.SaveBoard(str(dst),b)
(dst.parent/'additional_replacements.json').write_text(json.dumps(list(replacements),indent=2)+'\n')
print(dst)
