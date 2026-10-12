from pathlib import Path
import re,xml.etree.ElementTree as E
from PIL import Image,ImageDraw,ImageFont
r=Path(__file__).resolve().parent
for side in ['front','back']:
 root=E.parse(r/f'placement_{side}_aux.svg').getroot();x0,y0,w,h=map(float,root.attrib['viewBox'].split());s=60
 img=Image.new('RGB',(int(w*s),int(h*s)),'#f4f6f9');d=ImageDraw.Draw(img)
 def pt(x,y):return ((x-x0)*s,(y-y0)*s)
 for item in root:
  a=item.attrib;tag=item.tag.split('}')[-1];fill=a.get('fill','#fff');fill=None if fill=='none' else fill;stroke=a.get('stroke');
  if 'fill-opacity' in a:fill=None
  if tag=='path' and fill=='#416278' and stroke is None:stroke=fill;fill=None
  width=max(1,round(float(a.get('stroke-width','.02'))*s))
  if tag=='rect':
   x,y,ww,hh=map(lambda k:float(a[k]),['x','y','width','height']);d.rectangle([pt(x,y),pt(x+ww,y+hh)],fill=fill,outline=stroke,width=width)
  elif tag=='circle':
   x,y,rr=map(lambda k:float(a[k]),['cx','cy','r']);d.ellipse([pt(x-rr,y-rr),pt(x+rr,y+rr)],fill=fill,outline=stroke,width=width)
  elif tag=='path':
   for seg in a['d'].split('M')[1:]:
    nums=[float(t) for t in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',seg)];q=[pt(x,y) for x,y in zip(nums[0::2],nums[1::2])]
    if len(q)>2 and 'Z' in seg:d.polygon(q,fill=fill,outline=stroke)
    elif len(q)>1:d.line(q,fill=stroke or fill,width=width)
  elif tag=='text' and float(a.get('font-size','1'))<1:
   fontsize=max(12,round(float(a['font-size'])*s));font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',fontsize);x,y=pt(float(a['x']),float(a['y']));txt=item.text or ''
   d.text((x,y),txt,font=font,fill=a.get('fill','#334455'),anchor='ms',stroke_width=1,stroke_fill='white')
 img.save(r/f'placement_{side}_aux.png')
