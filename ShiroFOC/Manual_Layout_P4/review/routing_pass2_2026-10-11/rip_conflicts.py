from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parent;s=r/'combined2/ShiroFOC_Manual.kicad_pcb';d=r/'conflicts_ripped/ShiroFOC_Manual.kicad_pcb';d.parent.mkdir(exist_ok=True)
for n in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(s.parent/n,d.parent/n)
if not(d.parent/'libs').exists():(d.parent/'libs').symlink_to((s.parent/'libs').resolve(),target_is_directory=True)
ids=set()
for path,nets in [('ntc_l4/ShiroFOC_Manual.routes.json',['/Current / temperature/NTC_B_RAW','/Current / temperature/NTC_C_RAW']),('escape/l4/delta.json',['FEEDBACK_B_H2']),('power_mux_done/ShiroFOC_Manual.routes.json',['VBUS_MUX_IN']),('escape/right/ShiroFOC_Manual.routes.json',['FDCAN1_RX'])]:
 for g in json.loads((r/path).read_text())['connections']:
  if g['net']in nets:ids.update(g['new_items'])
for g in json.loads((r/'ancillary/delta.json').read_text())['groups']:
 if g['id']=='uart_bridge_rx':ids.update(g['new_items'])
b=p.LoadBoard(str(s));old=list(b.GetTracks());found=set()
for t in old:
 if t.m_Uuid.AsString()in ids:found.add(t.m_Uuid.AsString());b.Remove(t)
assert found==ids;p.SaveBoard(str(d),b);(d.parent/'removed.json').write_text(json.dumps(sorted(ids),indent=2));print(len(ids))
