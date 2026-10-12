from pathlib import Path
from html import escape
import pcbnew as p,sys,hashlib
b=p.LoadBoard(sys.argv[1]);out=Path(sys.argv[2]);x,y,w,h=map(float,sys.argv[3:7]);layers=[0,2];nets={};palette=['#4169b1','#c7462e','#55813d','#853ea0','#a87b14','#07918a','#cf5696','#644933','#617681']
def color(net):
 if net not in nets:nets[net]=palette[len(nets)%len(palette)]
 return nets[net]
def path(q,l):
 poly=p.SHAPE_POLY_SET();q.TransformShapeToPolygon(poly,l,0,p.FromMM(.003),p.ERROR_INSIDE);a=[]
 for i in range(poly.OutlineCount()):
  for j in [-1]+list(range(poly.HoleCount(i))):
   ln=poly.COutline(i)if j==-1 else poly.CHole(i,j);pts=[(p.ToMM(ln.CPoint(k).x),p.ToMM(ln.CPoint(k).y))for k in range(ln.PointCount())]
   if pts:a.append('M'+' L'.join(f'{xx},{yy}'for xx,yy in pts)+' Z')
 return' '.join(a)
def near(q):
 bb=q.GetBoundingBox();return p.ToMM(bb.GetRight())>=x and p.ToMM(bb.GetLeft())<=x+w and p.ToMM(bb.GetBottom())>=y and p.ToMM(bb.GetTop())<=y+h
panels=[]
for l in layers:
 a=[]
 for t in b.GetTracks():
  if t.IsOnLayer(l)and near(t):
   a.append(f'<path d="{path(t,l)}" fill="{color(t.GetNetname())}"/>')
   if isinstance(t,p.PCB_VIA):
    xx,yy=p.ToMM(t.GetPosition().x),p.ToMM(t.GetPosition().y);a.append(f'<circle cx="{xx}" cy="{yy}" r=".15" fill="white"/>')
 for f in b.GetFootprints():
  for q in f.Pads():
   if q.IsOnLayer(l)and near(q):
    xx,yy=p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y);a.append(f'<path d="{path(q,l)}" fill="{color(q.GetNetname())}" fill-opacity=".3" stroke="{color(q.GetNetname())}" stroke-width=".02"/><text x="{xx}" y="{yy}" font-size=".12" text-anchor="middle">{escape(f.GetReference()+"."+q.GetNumber())}</text>')
 for xx in range(int(x),int(x+w)+1):a.append(f'<path d="M{xx},{y}v{h}" stroke="#666" stroke-opacity=".2" stroke-width=".01"/><text x="{xx}" y="{y+.13}" font-size=".15">{xx}</text>')
 for yy in range(int(y),int(y+h)+1):a.append(f'<path d="M{x},{yy}h{w}" stroke="#666" stroke-opacity=".2" stroke-width=".01"/><text x="{x}" y="{yy}" font-size=".15">{yy}</text>')
 panels.append(f'<svg x="{len(panels)*(w+.5)}" y=".3" width="{w}" height="{h}" viewBox="{x} {y} {w} {h}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white"/>'+''.join(a)+'</svg>')
svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="2200" height="{int(2200*(h+3)/(2*w+.5))}" viewBox="0 0 {2*w+.5} {h+3}"><rect width="100%" height="100%" fill="#f8f8f8"/>'+''.join(panels)
for i,(net,c)in enumerate(nets.items()):svg+=f'<text x="{(i%3)*(2*w+.5)/3}" y="{h+.6+(i//3)*.25}" font-size=".15" fill="{c}">{escape(net)}</text>'
svg+='</svg>';out.write_text(svg)
