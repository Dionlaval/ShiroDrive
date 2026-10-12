from pathlib import Path
import pcbnew as p,json,shutil,math,collections
r=Path(__file__).resolve().parents[1];src=r/'support/precise_b/ShiroFOC_Manual.kicad_pcb';dst=r/'support/precise_b_simplified/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for ext in['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
for name in['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
manager=p.SETTINGS_MANAGER();manager.LoadProject(str(src.with_suffix('.kicad_pro')));project=manager.GetProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False)
u=next(f for f in b.GetFootprints()if f.GetReference()=='U4');u.BuildCourtyardCaches();court=u.GetCourtyard(p.F_Cu);boardpoly=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(boardpoly)
ids={u for g in json.loads(src.with_suffix('.routes.json').read_text())['connections']for u in g['new_items']};tracks=list(b.GetTracks());owned=[t for t in tracks if t.m_Uuid.AsString()in ids and t.Type()==p.PCB_TRACE_T];net=owned[0].GetNet();foreign=[t for t in tracks if t.GetNetname()!='NTC_PHASE_B']+[q for f in b.GetFootprints()for q in f.Pads()if q.GetNetname()!='NTC_PHASE_B'];obs={};edge=[e.GetEffectiveShape()for e in b.GetDrawings()if e.GetLayer()==p.Edge_Cuts];ret=[]
for layer in {t.GetLayer()for t in owned}:
 obs[layer]=[]
 for t in foreign:
  if t.IsOnLayer(layer):
   s=t.GetEffectiveShape(layer);obs[layer].append((s,.5 if t.GetNetClassName()=='Power'else .2,s.Collide(court,0)))
 for z in b.Zones():
  if z.IsOnLayer(layer)and not z.GetIsRuleArea()and z.GetNetname()not in['NTC_PHASE_B','3V3','GND']:
   s=z.GetFilledPolysList(layer);obs[layer].append((s,.5 if z.GetNetClassName()=='Power'else .2,s.Collide(court,0)))

def xy(v):return(v.x,v.y)
def length(a,c):return math.dist(a,c)/1e6
def route_ok(a,c,layer):
 if a==c:return True
 t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*a));t.SetEnd(p.VECTOR2I(*c));t.SetWidth(p.FromMM(.1524));t.SetLayer(layer);s=t.GetEffectiveShape(layer);incourt=s.Collide(court,0)
 for other,clear,othercourt in obs[layer]:
  if s.Collide(other,p.FromMM((.15 if incourt and othercourt else clear)+.002)):return False
 if any(s.Collide(e,p.FromMM(.5))for e in edge):return False
 return boardpoly.Contains(p.VECTOR2I(*a))and boardpoly.Contains(p.VECTOR2I(*c))
def paths(a,c):
 dx,dy=c[0]-a[0],c[1]-a[1];sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1;d=min(abs(dx),abs(dy));out=[]
 for corner in[(a[0]+sx*d,a[1]+sy*d),(c[0]-sx*d,c[1]-sy*d)]:
  pts=[a]+([corner]if corner not in[a,c]else[])+[c]
  if pts not in out:out.append(pts)
 return out
removed=[];added=[];logs=[]
for layer in sorted({t.GetLayer()for t in owned}):
 items=[t for t in owned if t.GetLayer()==layer];adj=collections.defaultdict(list)
 for t in items:
  a,c=xy(t.GetStart()),xy(t.GetEnd());adj[a].append((c,t));adj[c].append((a,t))
 assert len([x for x in adj if len(adj[x])==1])==2,(layer,[(x,len(v))for x,v in adj.items()])
 cur=next(x for x in adj if len(adj[x])==1);order=[cur];used=set()
 while True:
  choices=[(n,t)for n,t in adj[cur]if t.m_Uuid.AsString()not in used]
  if not choices:break
  assert len(choices)==1
  cur,t=choices[0];used.add(t.m_Uuid.AsString());order.append(cur)
 assert len(used)==len(items)
 original_length=sum(length(a,c)for a,c in zip(order,order[1:]));new=[order[0]];i=0
 while i<len(order)-1:
  found=False
  for j in range(len(order)-1,i+1,-1):
   candidates=paths(order[i],order[j]);oldlen=sum(length(a,c)for a,c in zip(order[i:j],order[i+1:j+1]))
   for pts in candidates:
    newlen=sum(length(a,c)for a,c in zip(pts,pts[1:]))
    if len(pts)-1<j-i and newlen<=oldlen+.000001 and all(route_ok(a,c,layer)for a,c in zip(pts,pts[1:])):
     new.extend(pts[1:]);i=j;found=True;break
   if found:break
  if not found:i+=1;new.append(order[i])
 newlen=sum(length(a,c)for a,c in zip(new,new[1:]));logs.append({'layer':b.GetLayerName(layer),'old_segments':len(items),'new_segments':len(new)-1,'old_length_mm':original_length,'new_length_mm':newlen})
 if new==order:continue
 for t in items:ret.append(t);removed.append(t.m_Uuid.AsString());b.Remove(t)
 for a,c in zip(new,new[1:]):
  t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*a));t.SetEnd(p.VECTOR2I(*c));t.SetWidth(p.FromMM(.1524));t.SetLayer(layer);t.SetNet(net);b.Add(t);ret.append(t);added.append(t.m_Uuid.AsString())
m={'source':str(src),'candidate':str(dst),'new_ids':added,'removed_ids':removed,'simplification':logs};(dst.parent/'delta.json').write_text(json.dumps(m,indent=2));print(json.dumps(m['simplification'],indent=2));b.BuildConnectivity();filler=p.ZONE_FILLER(b);filler.Fill(b.Zones());p.SaveBoard(str(dst),b)
