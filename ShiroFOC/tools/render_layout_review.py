#!/usr/bin/env python3
"""Evidence diagrams from native KiCad coordinates; no invented circuit geometry."""
from pathlib import Path
from html import escape
import pcbnew as p
import sys,re,json,hashlib
src=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True);b=p.LoadBoard(str(src));mm=lambda n:p.ToMM(n)-100
colors={'bus':'#c58a1e','aux':'#2f76ac','mcu':'#7751b5','bridge':'#d74e47','sense':'#129c96','brake':'#d57c2d','encoder':'#ac479b','imu':'#529e48','can':'#22739d','usb':'#5b6cb3','debug':'#71828c','mechanical':'#4c535b'}
names={'bus':'DC link','aux':'5 V / 3.3 V','mcu':'MCU / gate driver','bridge':'Inverter / shunts','sense':'Current amplifiers','brake':'Brake chopper','encoder':'Position feedback','imu':'IMU / temperature','can':'CAN','usb':'USB / UART','debug':'Debug / probes','mechanical':'Mounts'}
def group(f):
 r=f.GetReference();n=int(re.search(r'\d+',r).group())
 if r.startswith('H'):return'mechanical'
 if r in ['R410','R417','R418','R419','R420','R427','R428','R429','R430','R437','R438','R439','R441','R442','R443','C414','C424','C434']:return'sense'
 if r.startswith('TP'):
  ns={q.GetNetname()for q in f.Pads()}
  if any('OPO_'in x or 'SENSE_'in x for x in ns):return'sense'
  if any('NTC_'in x for x in ns):return'imu'
  if any('CAN_'in x for x in ns):return'can'
  if any('UART' in x for x in ns):return'usb'
  if n<1000:return{1:'bus',2:'aux',3:'mcu',5:'brake',7:'imu',9:'usb'}.get(n//100,'debug')
  return'debug'
 return {1:'bus',2:'aux',3:'mcu',4:'bridge',5:'brake',6:'encoder',7:'imu',8:'can',9:'usb',10:'debug'}.get(n//100,'debug')
def path(poly):
 a=[]
 for i in range(poly.OutlineCount()):
  for j in [-1]+list(range(poly.HoleCount(i))):
   ln=poly.COutline(i)if j==-1 else poly.CHole(i,j);pts=[ln.CPoint(k)for k in range(ln.PointCount())]
   if pts:a.append('M'+' L'.join(f'{mm(q.x):.4f},{mm(q.y):.4f}'for q in pts)+' Z')
 return' '.join(a)
def polyshape(o,ly):
 ps=p.SHAPE_POLY_SET();o.TransformShapeToPolygon(ps,ly,0,p.FromMM(.008),p.ERROR_INSIDE);return path(ps)
meta=[]
for f in b.GetFootprints():
 f.BuildCourtyardCaches();meta.append({'ref':f.GetReference(),'value':f.GetValue(),'function':group(f),'side':'B'if f.IsFlipped()else'F','x':mm(f.GetPosition().x),'y':mm(f.GetPosition().y)})
for layer,side,cy,fb in [(p.F_Cu,'F',p.F_CrtYd,p.F_Fab),(p.B_Cu,'B',p.B_CrtYd,p.B_Fab)]:
 for variant in ['wireframe','functions']:
  a=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-2 -3 84 86" width="1680" height="1720">','<rect x="-2" y="-3" width="84" height="86" fill="#f9fafc"/>','<rect x="0" y="0" width="80" height="80" rx="5" fill="#fff" stroke="#243448" stroke-width=".15"/>']
  if variant=='functions':
   # Broad regional tint is interpretive; every individual part retains its own category.
   regions=[(9,1,61,23,'bus'),(2,11,37,27,'brake'),(3,41,25,18,'aux'),(30,40,23,24,'mcu'),(55,19,23,44,'bridge'),(44,45,9,17,'sense'),(30,32,20,11,'encoder'),(25,47,10,7,'imu'),(25,65,21,13,'can'),(2,60,21,17,'usb')]
   for x,y,w,h,g in regions:a.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="1" fill="{colors[g]}" fill-opacity=".075"/>')
  for f in b.GetFootprints():
   if (f.IsFlipped())!=(side=='B')and not f.GetReference().startswith(('J','H')):continue
   c=colors[group(f)]if variant=='functions'else'#435160';ref=f.GetReference()
   cp=f.GetCourtyard(cy)
   if cp.OutlineCount():a.append(f'<path d="{path(cp)}" fill="{c}" fill-opacity=".075" stroke="{c}" stroke-opacity=".5" stroke-width=".055" stroke-dasharray=".25 .15"/>')
   for sh in f.GraphicalItems():
    if isinstance(sh,p.PCB_SHAPE)and sh.GetLayer()==fb:a.append(f'<path d="{polyshape(sh,fb)}" fill="{c}"/>')
   for pad in f.Pads():
    if pad.IsOnLayer(layer):
     a.append(f'<path d="{polyshape(pad,layer)}" fill="{c if variant=="functions" else "#fff"}" fill-opacity=".25" stroke="{c}" stroke-width=".07"/>')
     if pad.GetDrillSize().x:
      pos=pad.GetPosition();a.append(f'<circle cx="{mm(pos.x)}" cy="{mm(pos.y)}" r="{p.ToMM(pad.GetDrillSize().x)/2}" fill="#fff" stroke="{c}" stroke-width=".07"/>')
   xy=f.GetPosition();sz=.8 if ref[0]in'UQJH'else .58
   a.append(f'<text x="{mm(xy.x)}" y="{mm(xy.y)-.9}" text-anchor="middle" fill="{c}" stroke="#fff" stroke-width=".10" paint-order="stroke" font-family="sans-serif" font-weight="bold" font-size="{sz}">{ref}</text>')
  a.append(f'<text x="1" y="-1.2" font-family="sans-serif" font-size="1.15" fill="#243448">{side} side · top-view coordinates · {"functional map"if variant=="functions"else"native pads, bodies and courtyards"}</text></svg>')
  (out/f'{variant}_{side}.svg').write_text('\n'.join(a))
(out/'components.json').write_text(json.dumps({'board':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'legend':names,'colors':colors,'components':meta},indent=2))
print(out)
