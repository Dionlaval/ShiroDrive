from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parents[1];s=r/'merged_08/ShiroFOC_Manual.kicad_pcb';d=r/'support/uart_l4_open/ShiroFOC_Manual.kicad_pcb';d.parent.mkdir(exist_ok=True)
for ext in['.kicad_pro','.kicad_dru']:shutil.copy2(s.with_suffix(ext),d.with_suffix(ext))
for name in['fp-lib-table','sym-lib-table']:shutil.copy2(s.parent/name,d.parent/name)
if not(d.parent/'libs').exists():(d.parent/'libs').symlink_to((s.parent/'libs').resolve(),target_is_directory=True)
b=p.LoadBoard(str(s));ret=[];removed=[]
for t in list(b.GetTracks()):
 if t.GetNetname()=='USB_UART_RX'and t.GetLayer()==6 and max(t.GetStart().y,t.GetEnd().y)>p.FromMM(2):ret.append(t);removed.append(t.m_Uuid.AsString());b.Remove(t)
(d.parent/'changes.json').write_text(json.dumps({'source':str(s),'removed_ids':removed,'new_ids':[]},indent=2));p.SaveBoard(str(d),b)
