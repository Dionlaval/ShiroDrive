from pathlib import Path
import json,sys,pcbnew as p
src,dst=map(lambda s:Path(s).resolve(),sys.argv[1:3]);nets=sys.argv[3:]
def get(path):
 b=p.LoadBoard(str(path));b.BuildConnectivity();conn=b.GetConnectivity();poly=p.SHAPE_POLY_SET();b.GetBoardPolygonOutlines(poly);pp=[a for f in b.GetFootprints() if not f.IsDNP() and poly.Contains(f.GetPosition()) for a in f.Pads() if poly.Contains(a.GetPosition())];groups={};seen=set()
 for a in pp:
  net=a.GetNetname()
  if (nets and net not in nets) or not net or a.m_Uuid.AsString() in seen:continue
  q=[a];cluster={}
  while q:
   i=q.pop();uid=i.m_Uuid.AsString()
   if uid in cluster:continue
   cluster[uid]=i;seen.add(uid);q.extend(x for x in list(conn.GetConnectedPads(i))+list(conn.GetConnectedTracks(i)) if x.GetNetname()==net and x.m_Uuid.AsString() not in cluster)
  groups.setdefault(net,[]).append(sorted(x.GetParentFootprint().GetReference()+'.'+x.GetNumber() for x in cluster.values() if isinstance(x,p.PAD) and poly.Contains(x.GetParentFootprint().GetPosition())))
 return groups
old=get(src);new=get(dst);regress=[]
for net,groups in old.items():
 for group in groups:
  if len(group)<2:continue
  if not any(set(group)<=set(g) for g in new.get(net,[])):regress.append({'net':net,'old_connected_pads':group,'new_groups':new.get(net)})
print(json.dumps({'regressions':regress,'before':old,'after':new},indent=2))
