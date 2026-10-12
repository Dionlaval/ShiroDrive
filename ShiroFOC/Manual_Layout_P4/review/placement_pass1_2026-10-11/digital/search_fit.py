from pathlib import Path
import pcbnew as p
import math,json
b=p.LoadBoard(str(Path(__file__).parent/'candidate.kicad_pcb'))
fs={f.GetReference():f for f in b.GetFootprints()}
mm=p.ToMM
def bbox(f):
 layer=p.B_CrtYd if f.IsFlipped() else p.F_CrtYd
 gs=[g.GetBoundingBox() for g in f.GraphicalItems() if g.GetLayer()==layer]
 if not gs:gs=[q.GetBoundingBox() for q in f.Pads()]
 return [mm(min(g.GetLeft() for g in gs)),mm(min(g.GetTop() for g in gs)),mm(max(g.GetRight() for g in gs)),mm(max(g.GetBottom() for g in gs))]
def overlaps(a,c,g=0):return a[0]<c[2]+g and a[2]+g>c[0] and a[1]<c[3]+g and a[3]+g>c[1]
def fits(f):
 bb=bbox(f)
 if min(bb[:2])<-22 or max(bb[2:])>22:return False
 for r,o in fs.items():
  if o==f or r in ['J1','J101']:continue
  if f.GetLayer()==o.GetLayer() and overlaps(bb,bbox(o),.01):return False
 layer=f.GetLayer()
 for q in f.Pads():
  qs=q.GetEffectiveShape(layer)
  for o in fs.values():
   if o==f:continue
   for pad in o.Pads():
    if pad.IsOnLayer(layer) and q.GetNetCode()!=pad.GetNetCode() and qs.Collide(pad.GetEffectiveShape(layer),p.FromMM(.21)):return False
  for t in b.GetTracks():
   if t.IsOnLayer(layer) and q.GetNetCode()!=t.GetNetCode() and qs.Collide(t.GetEffectiveShape(layer),p.FromMM(.21)):return False
 return True

for ref,area,center in [('R313',(-8,-4,2.7,4.3),(-7,3.2)),('C605',(-14,-10,15.5,18.2),(-11.5,17.6)),('Q301',(-15.8,-12.5,6.5,10.5),(-14.5,7.4))]:
 f=fs[ref];old=f.GetPosition();oldang=f.GetOrientationDegrees();points=[]
 for a in [oldang]:
  for ix in range(math.ceil(area[0]*10),int(area[1]*10)+1,2):
   for iy in range(math.ceil(area[2]*10),int(area[3]*10)+1,2):
    x,y=ix/10,iy/10;points.append((math.hypot(x-center[0],y-center[1]),x,y,a))
 found=[]
 for score,x,y,a in sorted(points):
  f.SetOrientationDegrees(a);f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
  if fits(f):found.append([x,y,a]);break
 print(ref,found,flush=True)
 f.SetPosition(old);f.SetOrientationDegrees(oldang)
