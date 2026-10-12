from pathlib import Path
import json, shutil
import pcbnew as p

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
SOURCE=PROJECT/'ShiroFOC_Manual.kicad_pcb'
board=p.LoadBoard(str(SOURCE)); fps={f.GetReference():f for f in board.GetFootprints()}
mm=p.ToMM
def xy(q):return [mm(q.x),mm(q.y)]
def uid(q):return q.m_Uuid.AsString()

# Front-facing programming/reset and brake-temperature access. The support
# resistors are positioned at the actual U4 analog input side, on the back.
moves={
 'SW301':(-2.1,16.4,0,'F'),
 'R303':(-12.0,10.8,90,'F'),
 'R511':(-13.15,6.85,0,'B'),
 'R512':(-10.7,6.85,0,'B'),
 'D505':(-12.9,4.65,0,'B'),
 'R702':(-13.15,8.15,0,'B'),
 'R712':(-10.7,8.15,0,'B'),
 'R701':(-13.15,9.45,0,'B'),
 'R711':(-10.7,9.45,0,'B'),
 'R703':(-13.15,10.75,0,'B'),
 'R713':(-10.7,10.75,0,'B'),
}
board.BuildConnectivity();con=board.GetConnectivity()
attached={}
for ref in moves:
 for pad in fps[ref].Pads():
  for t in con.GetConnectedTracks(pad):attached[uid(t)]=t
before={ref:{'pos':xy(fps[ref].GetPosition()),'angle':fps[ref].GetOrientationDegrees(),'side':'B' if fps[ref].IsFlipped() else 'F'} for ref in moves}
removed=[]
for u,t in attached.items():
 removed.append({'uuid':u,'net':t.GetNetname(),'start':xy(t.GetStart()),'end':xy(t.GetEnd()),'reason':'Directly attached to previously staged component; obsolete placement guide stub.'})
 board.Remove(t)
for f in fps.values():f.BuildCourtyardCaches()
placed=set()
for ref,(x,y,a,side) in list(moves.items()):
 f=fps[ref]
 if f.IsFlipped()!=(side=='B'): f.Flip(f.GetPosition(),False)
 choices=[(x,y,a)]
 if side=='B':
  choices=[(i/4,j/4,angle) for i in range(-59,-12) for j in range(10,45) for angle in [a,(a+90)%360]]
  choices.sort(key=lambda q:(q[0]-x)**2+(q[1]-y)**2+(.2 if q[2]!=a else 0))
 selected=None
 for cx,cy,ca in choices:
  f.SetOrientationDegrees(ca);f.SetPosition(p.VECTOR2I(p.FromMM(cx),p.FromMM(cy)));f.BuildCourtyardCaches()
  ly=p.B_CrtYd if f.IsFlipped() else p.F_CrtYd;poly=f.GetCourtyard(ly)
  occupied=[other for other in fps.values() if other.GetReference()!=ref and other.IsFlipped()==f.IsFlipped() and other.GetReference() not in ['J1','J101'] and (other.GetReference() not in moves or other.GetReference() in placed)]
  if not any(poly.Collide(other.GetCourtyard(ly),p.FromMM(.04)) for other in occupied):selected=(cx,cy,ca,side);break
 if selected is None:raise RuntimeError('No valid placement for '+ref)
 moves[ref]=selected;placed.add(ref)

collisions=[]
for f in fps.values():f.BuildCourtyardCaches()
for ref in moves:
 f=fps[ref];layer=p.B_CrtYd if f.IsFlipped() else p.F_CrtYd;poly=f.GetCourtyard(layer)
 for other in fps.values():
  if other==f or other.IsFlipped()!=f.IsFlipped() or other.GetReference() in ['J1','J101']:continue
  if poly.Collide(other.GetCourtyard(layer)):
   pair=sorted([ref,other.GetReference()])
   if pair not in collisions:collisions.append(pair)

out=HERE/'ShiroFOC_Manual.kicad_pcb';p.SaveBoard(str(out),board)
for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(PROJECT/name,HERE/name)
if not (HERE/'libs').exists():(HERE/'libs').symlink_to(PROJECT/'libs',target_is_directory=True)
manifest={'source':str(SOURCE),'candidate':str(out),'moved':{r:{'from':before[r],'to':{'pos':[v[0],v[1]],'angle':v[2],'side':v[3]}} for r,v in moves.items()},'removed_copper':removed,'courtyard_collisions_involving_moved':collisions}
(HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'moved':len(moves),'removed_copper':len(removed),'collisions':collisions},indent=2))
