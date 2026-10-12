"""Merge explicit routing UUID deltas into a candidate; no main project writes."""
from pathlib import Path
import pcbnew as p,json,shutil,sys
src=Path(sys.argv[1]).resolve();dst=Path(sys.argv[2]).resolve();assert src!=dst;dst.parent.mkdir(parents=True,exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
for n in ['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/n,dst.parent/n)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));proj=m.GetProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(proj);b.SynchronizeNetsAndNetClasses(False)
retained=[];sources=[];log=[]
net_codes={n.GetNetname():n.GetNetCode() for n in b.GetNetInfo().NetsByNetcode().values()}
for arg in sys.argv[3:]:
 d=json.loads(Path(arg).read_text());c=p.LoadBoard(d['candidate']);sources.append(c);old={t.m_Uuid.AsString():t for t in b.GetTracks()};other={t.m_Uuid.AsString():t for t in c.GetTracks()}
 removed=[];added=[]
 for move in d.get('footprint_moves',[]):
  f=next(f for f in b.GetFootprints()if f.m_Uuid.AsString()==move['uuid']);target=next(f for f in c.GetFootprints()if f.m_Uuid.AsString()==move['uuid'])
  oldmove=move['old'];oldxy=oldmove.get('position_nm',[p.FromMM(v)for v in oldmove.get('position_mm',[])])
  assert [f.GetPosition().x,f.GetPosition().y]==oldxy,('Footprint already changed',f.GetReference())
  assert abs(f.GetOrientationDegrees()-oldmove['angle_deg'])<.00001
  f.SetOrientation(target.GetOrientation());f.SetPosition(target.GetPosition())
 for u in d.get('removed_ids',d.get('delete_ids',[])):
  assert u in old,('Missing item to remove',u);t=old[u];retained.append(t);b.Remove(t);removed.append(u)
 for u in d['new_ids']:
  assert u not in old,('Already exists',u);t=other[u];new=t.Duplicate();new.m_Uuid.Clone(t.m_Uuid);new.SetParent(b);new.SetNetCode(net_codes[t.GetNetname()]);b.Add(new);retained.append(new);added.append(u)
 log.append(dict(manifest=arg,removed_ids=removed,new_ids=added))
b.BuildConnectivity();fill=p.ZONE_FILLER(b);assert fill.Fill(b.Zones());p.SaveBoard(str(dst),b)
(dst.parent/'merge_manifest.json').write_text(json.dumps(dict(source=str(src),candidate=str(dst),deltas=log),indent=2));print('Merged',sum(len(x['new_ids'])for x in log),'new and',sum(len(x['removed_ids'])for x in log),'removed items')
