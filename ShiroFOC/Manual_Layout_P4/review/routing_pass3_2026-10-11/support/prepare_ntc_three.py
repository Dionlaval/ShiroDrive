from pathlib import Path
import pcbnew as p,json,shutil,math
r=Path(__file__).resolve().parents[1];s=r/'support/new_shared_h2/ShiroFOC_Manual.kicad_pcb';d=r/'support/three_lanes_open/ShiroFOC_Manual.kicad_pcb';d.parent.mkdir(exist_ok=True)
for ext in['.kicad_pro','.kicad_dru']:shutil.copy2(s.with_suffix(ext),d.with_suffix(ext))
for name in['fp-lib-table','sym-lib-table']:shutil.copy2(s.parent/name,d.parent/name)
if not(d.parent/'libs').exists():(d.parent/'libs').symlink_to((s.parent/'libs').resolve(),target_is_directory=True)
b=p.LoadBoard(str(s));ret=[];removed=[];added=[];replace={
'NTC_PHASE_A':[((-9.275,7.025),(-10.1,6.2)),((-9.275,8.325),(-9.275,7.025)),((-8.65,8.95),(-9.275,8.325))],
'NTC_PHASE_C':[((-9.95,6.9),(-9.65,7.2)),((-9.65,7.2),(-9.65,8.95)),((-9.65,8.95),(-8.675,9.925))]};replace_count={k:0 for k in replace}
for t in list(b.GetTracks()):
 net=t.GetNetname()
 if net not in replace or t.GetLayer()!=6:continue
 a,c=tuple(map(p.ToMM,t.GetStart())),tuple(map(p.ToMM,t.GetEnd()))
 if any((math.dist(a,x)<.00001 and math.dist(c,y)<.00001)or(math.dist(a,y)<.00001 and math.dist(c,x)<.00001)for x,y in replace[net]):ret.append(t);removed.append(t.m_Uuid.AsString());b.Remove(t);replace_count[net]+=1
assert all(v==3 for v in replace_count.values()),replace_count
paths={'NTC_PHASE_A':[(-10.1,6.2),(-9.3625,6.9375),(-9.3625,8.2375),(-8.65,8.95)],'NTC_PHASE_C':[(-9.95,6.9),(-9.675,7.175),(-9.675,8.925),(-8.675,9.925)]}
for net,path in paths.items():
 ni=next(x for x in b.GetNetInfo().NetsByNetcode().values()if x.GetNetname()==net)
 for a,c in zip(path,path[1:]):
  t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*[p.FromMM(v)for v in a]));t.SetEnd(p.VECTOR2I(*[p.FromMM(v)for v in c]));t.SetWidth(p.FromMM(.1524));t.SetLayer(6);t.SetNet(ni);b.Add(t);ret.append(t);added.append(t.m_Uuid.AsString())
(d.parent/'changes.json').write_text(json.dumps({'source':str(s),'removed_ids':removed,'new_ids':added},indent=2));p.SaveBoard(str(d),b)
