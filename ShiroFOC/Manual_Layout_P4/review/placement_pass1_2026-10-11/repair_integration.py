from pathlib import Path
import pcbnew as p
import json,math
HERE=Path(__file__).resolve().parent;OUT=HERE/'final';PATH=OUT/'ShiroFOC_Manual.kicad_pcb'
b=p.LoadBoard(str(PATH))
fps={f.GetReference():f for f in b.GetFootprints()};mm=p.ToMM
for f in fps.values():f.BuildCourtyardCaches()
removed=[]
original_tracks=list(b.GetTracks())
for t in original_tracks:
 if t.m_Uuid.AsString()=='490b6bfa-fc45-4090-a2bd-17b34667c89a':
  removed.append(t.m_Uuid.AsString());b.Remove(t)
def geom(item,layer):
 q=p.SHAPE_POLY_SET();item.TransformShapeToPolygon(q,layer,0,p.FromMM(.005),p.ERROR_INSIDE);return q
tracks={ly:[] for ly in [p.F_Cu,p.B_Cu]}
for t in b.GetTracks():
 for ly in tracks:
  if t.IsOnLayer(ly):tracks[ly].append((t.GetNetname(),geom(t,ly)))
def valid(f):
 ly=f.GetLayer();cy=p.B_CrtYd if f.IsFlipped() else p.F_CrtYd;poly=f.GetCourtyard(cy);bb=poly.BBox()
 for x,y in [(bb.GetX(),bb.GetY()),(bb.GetRight(),bb.GetBottom()),(bb.GetRight(),bb.GetY()),(bb.GetX(),bb.GetBottom())]:
  xx,yy=mm(x),mm(y)
  if abs(xx)>22.2 or abs(yy)>22.2 or max(abs(xx)-19.5,0)**2+max(abs(yy)-19.5,0)**2>2.7**2:return False
 for other in fps.values():
  if other==f or other.GetReference() in ['J1','J101'] or other.IsFlipped()!=f.IsFlipped():continue
  if poly.Collide(other.GetCourtyard(cy),p.FromMM(.025)):return False
 for pad in f.Pads():
  shape=geom(pad,ly)
  for net,track in tracks[ly]:
   if net!=pad.GetNetname() and shape.Collide(track,p.FromMM(.21)):return False
 return True
changes=[]
for ref in ['SW301','R303','R711','R713']:
 f=fps[ref];x,y=mm(f.GetPosition().x),mm(f.GetPosition().y);a=f.GetOrientationDegrees()
 radius=120 if ref=='SW301' else 24
 choices=[(x+i*.25,y+j*.25,(a+da)%360) for i in range(-radius,radius+1) for j in range(-radius,radius+1) for da in [0,90,180,270]]
 choices.sort(key=lambda q:(q[0]-x)**2+(q[1]-y)**2+(.1 if q[2]!=a else 0))
 found=None
 for nx,ny,na in choices:
  f.SetPosition(p.VECTOR2I(p.FromMM(nx),p.FromMM(ny)));f.SetOrientationDegrees(na);f.BuildCourtyardCaches()
  if valid(f):found=(nx,ny,na);break
 if found is None:raise RuntimeError('No copper-safe placement '+ref)
 changes.append({'ref':ref,'before':[x,y,a],'after':found})
b.BuildConnectivity();p.SaveBoard(str(PATH),b)
(HERE/'integration_repairs.json').write_text(json.dumps({'moves':changes,'removed_preliminary_guide_tracks':removed},indent=2)+'\n')
print(json.dumps(changes,indent=2))
