from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parents[1];s=r/'merged_03/ShiroFOC_Manual.kicad_pcb';d=r/'support/current_int2_prepare/ShiroFOC_Manual.kicad_pcb';d.parent.mkdir(exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(s.with_suffix(ext),d.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(s.parent/name,d.parent/name)
if not(d.parent/'libs').exists():(d.parent/'libs').symlink_to((s.parent/'libs').resolve(),target_is_directory=True)
b=p.LoadBoard(str(s));ret=[];removed=json.loads((r/'support/ntc_unfenced/delta.json').read_text())['removed_ids'];cd=json.loads((r/'vbus/final/delta.json').read_text());removed+=next(g['new_items']for g in cd['groups']if g['net']=='NTC_PHASE_C'); removed+=['ca36d2e8-4852-4876-810f-5e8669891dec','b93268c2-6589-4d32-ada2-02cb3f04a629','9d232b3a-86e3-4f7a-86de-9d7d5d8861af','e0b84bb2-e410-4874-97bd-78d57ce9f971'];tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
for u in removed:t=tracks[u];ret.append(t);b.Remove(t)
nr=r/'mcu_left/nrst_fixed/ShiroFOC_Manual.kicad_pcb';nb=p.LoadBoard(str(nr));ids=[u for c in json.loads(nr.with_suffix('.routes.json').read_text())['connections']for u in c['new_items']];net={n.GetNetname():n for n in b.GetNetInfo().NetsByNetcode().values()}
for t in nb.GetTracks():
 if t.m_Uuid.AsString() not in ids:continue
 q=t.Duplicate();q.m_Uuid.Clone(t.m_Uuid);q.SetParent(b);q.SetNet(net[t.GetNetname()]);b.Add(q);ret.append(q)
(d.parent/'changes.json').write_text(json.dumps(dict(source=str(s.resolve()),removed_ids=removed,new_ids=ids),indent=2));p.SaveBoard(str(d),b)
