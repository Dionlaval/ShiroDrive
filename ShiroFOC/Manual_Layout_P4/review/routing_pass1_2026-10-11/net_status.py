from pathlib import Path
import pcbnew as p,json
R=Path(__file__).resolve().parent;b=p.LoadBoard(str(R/'final/ShiroFOC_Manual.kicad_pcb'));b.BuildConnectivity();conn=b.GetConnectivity();poly=p.SHAPE_POLY_SET();b.GetBoardPolygonOutlines(poly)
plans=json.loads((R/'planned_groups.json').read_text());wanted=set(n for nets in plans.values()for n in nets);pads={}
for f in b.GetFootprints():
 if not poly.Contains(f.GetPosition())or f.IsDNP():continue
 for q in f.Pads():
  if q.GetNetname()in wanted:pads.setdefault(q.GetNetname(),[]).append(q)
out={}
for net,pp in pads.items():
 seen=set();clusters=[];names={q.m_Uuid.AsString():q.GetParentFootprint().GetReference()+'.'+q.GetNumber()for q in pp}
 for pad in pp:
  if pad.m_Uuid.AsString()in seen:continue
  pending=[pad];group=set()
  while pending:
   q=pending.pop();u=q.m_Uuid.AsString()
   if u in seen:continue
   seen.add(u)
   if u in names:group.add(names[u])
   pending.extend(t for t in list(conn.GetConnectedTracks(q))+list(conn.GetConnectedPads(q))if t.GetNetname()==net and t.m_Uuid.AsString()not in seen)
  clusters.append(sorted(group))
 out[net]={'onboard_pads':len(pp),'physical_pad_clusters':clusters,'complete_between_onboard_pads':len(clusters)==1}
(R/'final/net_status.json').write_text(json.dumps(out,indent=2))
print('Selected nets fully connected between onboard pads',sum(n['complete_between_onboard_pads']for n in out.values()),'of',len(out))
print('Open selected nets:',*[n for n,d in out.items()if not d['complete_between_onboard_pads']],sep='\n')
