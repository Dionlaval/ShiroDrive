#!/usr/bin/env python3
"""Colour actual filled copper by net for routing inspection, not fabrication output."""
import pcbnew as p
from pathlib import Path
from html import escape
import sys
src=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(exist_ok=True,parents=True);b=p.LoadBoard(str(src))
mm=lambda n:p.ToMM(n)-100
colors={'GND':'#243c42','VM':'#d99921','OUT1':'#e24848','OUT2':'#d74b9b','OUT3':'#9d57d5','Net-(D504-A)':'#eb7028'}
def color(net):
 if net in colors:return colors[net]
 if 'FORCE_P' in net:return '#a56938'
 if 'SENSE_' in net:return '#19dcd0' if net.endswith('P') else '#4e94ff'
 if '/Current ' in net or net.startswith('OPO_'):return '#79e3b3'
 if net.startswith(('GHS','GLS')) or ('Q40' in net):return '#ffc4ff'
 if net.startswith('BOOT'):return '#ecb14c'
 if net in ['3V3','VCC','5V_SYS','VDDA','VREF+']:return '#dedb74'
 return '#b7c0c8'
def path(poly):
 strings=[]
 for i in range(poly.OutlineCount()):
  for j in [-1]+list(range(poly.HoleCount(i))):
   line=poly.COutline(i) if j==-1 else poly.CHole(i,j)
   pts=[line.CPoint(k) for k in range(line.PointCount())]
   if pts:strings.append('M'+' L'.join(f'{mm(q.x):.5f},{mm(q.y):.5f}' for q in pts)+' Z')
 return ' '.join(strings)
for layer in [p.F_Cu,p.B_Cu,p.In1_Cu,p.In2_Cu]:
 a=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-2 -4 84 88" width="1680" height="1760">','<rect x="-2" y="-4" width="84" height="88" fill="#10191e"/>','<rect x="0" y="0" width="80" height="80" rx="5" fill="#172329" stroke="#678" stroke-width=".1"/>']
 def shape(poly,net,opacity=1):
  a.append(f'<path d="{path(poly)}" fill="{color(net)}" fill-opacity="{opacity}" fill-rule="evenodd"><title>{escape(net)}</title></path>')
 for z in sorted(b.Zones(),key=lambda z:z.GetAssignedPriority()):
  if not z.GetIsRuleArea() and z.IsOnLayer(layer):shape(z.GetFilledPolysList(layer),z.GetNetname(),.88)
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA):
   pos=t.GetPosition();a.append(f'<circle cx="{mm(pos.x)}" cy="{mm(pos.y)}" r="{p.ToMM(t.GetWidth(layer))/2}" fill="{color(t.GetNetname())}" stroke="#fff" stroke-width=".035"><title>{escape(t.GetNetname())}</title></circle>');a.append(f'<circle cx="{mm(pos.x)}" cy="{mm(pos.y)}" r="{p.ToMM(t.GetDrill())/2}" fill="#070b10"/>')
  elif t.GetLayer()==layer:
   st,en=t.GetStart(),t.GetEnd();a.append(f'<path d="M{mm(st.x)},{mm(st.y)} L{mm(en.x)},{mm(en.y)}" fill="none" stroke="{color(t.GetNetname())}" stroke-width="{p.ToMM(t.GetWidth())}" stroke-linecap="round"><title>{escape(t.GetNetname())}</title></path>')
 for f in b.GetFootprints():
  for pad in f.Pads():
   if pad.IsOnLayer(layer):
    poly=p.SHAPE_POLY_SET();pad.TransformShapeToPolygon(poly,layer,0,p.FromMM(.008),p.ERROR_INSIDE);shape(poly,pad.GetNetname())
    if pad.GetDrillSize().x:
     pos=pad.GetPosition();a.append(f'<circle cx="{mm(pos.x)}" cy="{mm(pos.y)}" r="{p.ToMM(pad.GetDrillSize().x)/2}" fill="#070b10"/>')
  side=p.B_Cu if f.IsFlipped() else p.F_Cu
  if side==layer and not f.GetReference().startswith('TP'):
   xy=f.GetPosition();ref=f.GetReference();size=.8 if ref[0] in 'UQJH' else .57
   a.append(f'<text x="{mm(xy.x)}" y="{mm(xy.y)-.9}" text-anchor="middle" fill="#fff" stroke="#172329" stroke-width=".10" paint-order="stroke" font-size="{size}" font-family="sans-serif">{ref}</text>')
 a.append(f'<text x="1" y="-1.5" font-family="sans-serif" font-size="1.3" fill="#eee">{b.GetLayerName(layer)} — top view | filled copper by net | GND teal · VM gold</text></svg>')
 (out/(b.GetLayerName(layer).replace('.','_')+'.svg')).write_text('\n'.join(a))
print(out)
