"""Hand-routed schematic drawing primitives; coordinates are a 1.27 mm grid."""
from __future__ import annotations
import json, uuid, math
from pathlib import Path
import generate_rev_a as g
import native_rev_a as old
ROOT=g.ROOT
old.assign_types()
SOURCE_SHEETS=[getattr(g,f'make_{i:02}')() for i in range(1,11)]
PARTS={c.ref:c for s in SOURCE_SHEETS for c in s.components}
NETS={(c.ref,p.number):s.connections.get((c.ref,p.number)) for s in SOURCE_SHEETS for c in s.components for p in c.sym.pins}
G=1.27
q=old.q
uid=old.uid
ROOTID=old.ROOTID
PROJECT=old.PROJECT
def fmt(x):return f'{x*G:.5f}'.rstrip('0').rstrip('.') or '0'
def effect(size=1.27,just=''):
 return f'(effects(font(size {size} {size})){f"(justify {just})" if just else ""})'
def poly(points,width=.254,fill='none'):
 return f'(polyline(pts{"".join(f"(xy {fmt(x)} {fmt(-y)})" for x,y in points)})(stroke(width {width})(type default))(fill(type {fill})))'
def rect(x1,y1,x2,y2):return f'(rectangle(start {fmt(x1)} {fmt(-y1)})(end {fmt(x2)} {fmt(-y2)})(stroke(width .254)(type default))(fill(type background)))'
def field(name,value,x,y,hide=False,size=1.27,just=''):
 return f'(property {q(name)} {q(value)}(at {fmt(x)} {fmt(y)} 0)(effects(font(size {size} {size})){f"(justify {just})" if just else ""}{"(hide yes)" if hide else ""}))'
TYPES={'P':'passive','I':'input','O':'output','B':'bidirectional','T':'tri_state','W':'power_in','w':'power_out','N':'no_connect','C':'open_collector'}
class Page:
 def __init__(self,name,title,paper='A3'):
  self.name=name;self.title=title;self.paper=paper;self.sid=uid('redraw/'+name);self.childid=uid('child/redraw/'+name)
  self.items=[];self.placements=[];self.points={};self.wires=[];self.labels=[];self.serial=0;self.defs={};self.used=set();self.powerpins={};self.powerpoints=[]
 def _id(self):self.serial+=1;return q(uid(self.name+'/'+str(self.serial)))
 def p(self,ref,pin,unit=1):return self.points[(ref,str(pin),unit)]
 def shift(self,pt,dx=0,dy=0):return(pt[0]+dx,pt[1]+dy)
 def note(self,x,y,text,size=1.27):self.items.append(f'(text {q(text)}(at {fmt(x)} {fmt(y)} 0){effect(size,"left top")}(uuid {self._id()}))')
 def heading(self,x,y,text):self.note(x,y,text,1.8)
 def line(self,*pts,width=.254):self.items.append(f'(polyline(pts{"".join(f"(xy {fmt(x)} {fmt(y)})" for x,y in pts)})(stroke(width {width})(type default))(fill(type none))(uuid {self._id()}))')
 def wire(self,*pts):
  pts=[tuple(p) for p in pts]
  for a,b in zip(pts,pts[1:]):
   assert a[0]==b[0] or a[1]==b[1],f'Diagonal wire {self.name} {a} {b}'
   if a!=b:self.wires.append((a,b))
 def route(self,a,b,via=None):
  if via is None: self.wire(a,(b[0],a[1]),b)
  else:self.wire(a,*via,b)
 def label(self,net,pt,kind='local',side='L'):
  if any(n==net and p==pt and k==kind for n,p,k,sd in self.labels):return
  self.labels.append((net,pt,kind,side))
 def port(self,net,pt,direction='input',side='L'):self.label(net,pt,'global',side)
 def power(self,net,pt,up=True):
  self.powerpoints.append(pt)
  # Project-wide power symbol, connected visibly at supply/return branches.
  ref=f'#PWR{self.name.replace("_","")}{len(self.powerpins)}';key='PWR_'+net.replace('+','plus')
  body=poly([(-1, -1),(0,-2),(1,-1)],.2032) if up else poly([(-1,1),(1,1),(0,2),(-1,1)],.2032)
  line=poly([(0,0),(0,-2 if up else 1)],.2032)
  spec={'name':key,'ref':'#PWR','units':{1:{'pins':{'1':(0,0,'L',net,'power_in',True,0)},'body':body+line,'w':0,'h':0}}}
  self.defs[key]=spec; self.powerpins[ref]=net
  x,y=pt
  self.items.append(f'(symbol(lib_id {q("ShiroFOC_Redraw:"+key)})(at {fmt(x)} {fmt(y)} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid {q(uid(ref))}){field("Reference",ref,x,y,True)}{field("Value",net,x,y+(-3 if up else 3),size=1.016)}(instances(project {q(PROJECT)}(path {q("/"+ROOTID+"/"+self.childid)}(reference {q(ref)})(unit 1)))))')
 def ic(self,ref,x,y,pins,w=20,h=20,kind='box',unit=1,title=None,body=None,fields=None):
  c=PARTS[ref]; name='COMP_'+ref
  definitions=self.defs.setdefault(name,{'name':name,'ref':ref.rstrip('0123456789'),'units':{}})
  ps={}
  for number,v in pins.items():
   p=next(p for p in c.sym.pins if p.number==str(number))
   dx,dy,side=v[:3];visible=v[3] if len(v)>3 else True;pname=v[4] if len(v)>4 else p.name
   # KiCad gives hidden power pins implicit global connectivity by name.
   # A stacked exposed ground pad must therefore be named GND, not EP.
   if not visible and p.etype=='W':pname=NETS[(ref,str(number))] or pname
   length=abs(dx)-w/2 if side in 'LR' else abs(dy)-h/2
   if kind in ('opamp','halfbridge','nmos','passive','tp'):length=2
   ps[str(number)]=(dx,dy,side,pname,TYPES[p.etype],visible,max(0,length))
   self.points[(ref,str(number),unit)]=(x+dx,y+dy)
  if body is None:
   if kind=='opamp':body=poly([(-w/2,-h/2),(-w/2,h/2),(w/2,0),(-w/2,-h/2)],fill='background')
   else:body=rect(-w/2,-h/2,w/2,h/2)
  definitions['units'][unit]={'pins':ps,'body':body,'w':w,'h':h}
  self.placements.append({'ref':ref,'x':x,'y':y,'unit':unit,'name':name,'w':w,'h':h,'title':title,'fields':fields})
  self.used.add(ref)
  for pn in ps:
   if NETS[(ref,pn)] is None:
    px,py=self.p(ref,pn,unit)
    self.items.append(f'(no_connect(at {fmt(px)} {fmt(py)})(uuid {self._id()}))')
  return self
 def part(self,ref,x,y,orient='h',flip=False,value=None):
  c=PARTS[ref]; vertical=orient=='v'
  coords=[(0,-4,'T'),(0,4,'B')] if vertical else [(-4,0,'L'),(4,0,'R')]
  if flip:coords.reverse()
  pins={p.number:coords[i] for i,p in enumerate(c.sym.pins)}
  def tr(a,b):
   if flip:a=-a
   return (b,a) if vertical else(a,b)
  def l(*pts):return poly([tr(*p) for p in pts])
  if c.sym.name in ('CAPACITOR','CAP_POL'):
   body=l((-2,0),(-.6,0))+l((.6,0),(2,0))+l((-.6,-1.6),(-.6,1.6))+l((.6,-1.6),(.6,1.6))
   if ref in ('C101','C102','C103'):body+=l((-1.4,-2),(-.6,-2))+l((-1,-2.4),(-1,-1.6))
  elif c.sym.name in ('DIODE','LED'):
   body=l((-2,0),(-1,0))+l((1,0),(2,0))+l((-1,-1.5),(-1,1.5))+l((-1,0),(1,1.5),(1,-1.5),(-1,0))
   if c.sym.name=='LED':body+=l((.3,-2),(2,-3.7))+l((1,-1.7),(2.7,-3.4))
  elif c.sym.name=='SWITCH':body=l((-2,0),(-1,0))+l((1,0),(2,0))+l((-1,0),(1,-1.5))
  elif c.sym.name=='INDUCTOR':body=l((-2,0),(-1.5,0),(-1,-1),(-.5,0),(0,-1),(.5,0),(1,-1),(1.5,0),(2,0))
  else:body=l((-2,0),(-1.5,0))+l((-1.5,-.65),(1.5,-.65),(1.5,.65),(-1.5,.65),(-1.5,-.65))+l((1.5,0),(2,0))
  self.ic(ref,x,y,pins,w=4 if not vertical else 2,h=2 if not vertical else 4,kind='passive',body=body,title=value)
  self.placements[-1]['orient']='v' if vertical else 'h'
  return self
 def tp(self,ref,pt,net=None):
  # Test point endpoint is precisely the measured node; symbol extends upward.
  body=poly([(0,0),(0,-2)])+f'(circle(center 0 {fmt(3)})(radius {fmt(1)})(stroke(width .2032)(type default))(fill(type none)))'
  self.ic(ref,*pt,{'1':(0,0,'B',False,'~')},w=0,h=0,kind='tp',body=body)
  self.placements[-1]['tp']=True
 def supply(self,ref,pin,net,dy=-5,unit=1):
  a=self.p(ref,pin,unit);b=(a[0],a[1]+dy);self.wire(a,b);self.power(net,b,up=dy<0)
 def out(self,ref,pin,net,dx=8,dy=0,unit=1):
  a=self.p(ref,pin,unit);b=(a[0]+dx,a[1]+dy);self.route(a,b);self.port(net,b,side='L' if dx<0 else 'R')
 def finalize(self,all_defs):
  # Split every segment at terminals/taps. Add junctions at actual 3-way vertices.
  points=set(self.points.values())|{p for _,p,_,_ in self.labels}|set(self.powerpoints)
  for a,b in self.wires:points|={a,b}
  segments=set()
  for a,b in self.wires:
   def on(p):return (a[0]==b[0]==p[0] and min(a[1],b[1])<=p[1]<=max(a[1],b[1])) or (a[1]==b[1]==p[1] and min(a[0],b[0])<=p[0]<=max(a[0],b[0]))
   ps=sorted([p for p in points if on(p)])
   for aa,bb in zip(ps,ps[1:]):segments.add((aa,bb))
  degrees={}
  for a,b in sorted(segments):
   for p in (a,b):degrees[p]=degrees.get(p,0)+1
   self.items.append(f'(wire(pts(xy {fmt(a[0])} {fmt(a[1])})(xy {fmt(b[0])} {fmt(b[1])}))(stroke(width 0)(type default))(uuid {self._id()}))')
  for (x,y),d in degrees.items():
   if d>=3:self.items.append(f'(junction(at {fmt(x)} {fmt(y)})(diameter 0)(color 0 0 0 0)(uuid {self._id()}))')
  for n,(x,y),kind,side in self.labels:
   if kind=='local':self.items.append(f'(label {q(n)}(at {fmt(x)} {fmt(y)} 0){effect(1.016,"left bottom")}(uuid {self._id()}))')
   else:
    angle=0 if side=='L' else 180
    self.items.append(f'(global_label {q(n)}(shape bidirectional)(at {fmt(x)} {fmt(y)} {angle}){effect(1.016,"right" if side=='L' else "left")}(uuid {self._id()}))')
  for c in self.placements:
   ref=c['ref'];part=PARTS[ref];x=c['x'];y=c['y'];u=c['unit'];f={'Reference':ref,'Value':part.value if c['title'] is None else c['title'],'Footprint':part.footprint,'Datasheet':part.datasheet,**part.fields}
   f.setdefault('Assembly','FIT')
   if ref.startswith(('TP','JP')):f.setdefault('MPN','PCB feature')
   if not f.get('MPN'):
    f['MPN']='';f['Procurement']='Select to specification: '+part.value+'; '+part.footprint.split(':')[-1]
   f.setdefault('Rating','See Value; generic low-voltage passives: R >=0.1 W / 50 V, C >=16 V X7R unless specified')
   fparts=[]
   for key,val in f.items():
    if c.get('tp'):fx=x+2;fy=y-4 if key=='Reference' else y;just='left'
    elif c.get('orient')=='v':fx=x+3;fy=y-1 if key=='Reference' else y+1;just='left'
    else:fx=x;fy=y-c['h']/2-2 if key=='Reference' else y+c['h']/2+2;just=''
    custom=c.get('ref_pos' if key=='Reference' else 'value_pos' if key=='Value' else '_hidden_pos')
    if custom:
     fx,fy=custom[:2]
     if len(custom)>2:just=custom[2]
    fparts.append(field(key,val,fx,fy,key not in ('Reference','Value') or (c.get('tp') and key=='Value'),size=1.27,just=just))
   self.items.append(f'(symbol(lib_id {q("ShiroFOC_Redraw:"+c["name"])})(at {fmt(x)} {fmt(y)} 0)(unit {u})(in_bom yes)(on_board yes)(dnp {"yes" if f["Assembly"]=="DNP" else "no"})(uuid {q(uid(ref) if u==1 else uid(ref+"/unit/"+str(u)))}){"".join(fparts)}(instances(project {q(PROJECT)}(path {q("/"+ROOTID+"/"+self.childid)}(reference {q(ref)})(unit {u})))))')
  used=set(self.defs)
  txt=f'(kicad_sch(version 20250114)(generator "eeschema")(uuid {q(self.sid)})(paper {q(self.paper)})(title_block(title {q(self.title)})(date "2026-09-16")(rev "A1-Drawing")(company "ShiroFOC")(comment 1 "Same A0 circuit; connected functional drawing"))(lib_symbols {"".join(symbol_text(all_defs[k],"ShiroFOC_Redraw:"+k) for k in sorted(used))}){"".join(self.items)}(embedded_fonts no))\n'
  return txt

def symbol_text(d,name=None):
 units=[]
 for u,v in sorted(d['units'].items()):
  pins=[]
  for number,(x,y,side,pname,typ,visible,length) in v['pins'].items():
   a={'L':0,'R':180,'T':270,'B':90}[side]
   pins.append(f'(pin {typ} line(at {fmt(x)} {fmt(-y)} {a})(length {fmt(length)}){"(hide yes)" if not visible else ""}(name {q(pname)} {effect(1.016)})(number {q(number)} {effect(.889)}))')
  units.append(f'(symbol {q(d["name"]+"_"+str(u)+"_1")}{v["body"]}{"".join(pins)})')
 power=d['ref']=='#PWR'
 return f'(symbol {q(name or d["name"])}{"(power)" if power else ""}(pin_names(offset .635){" hide" if power else ""}){"(pin_numbers hide)" if power else ""}(in_bom {"no" if power else "yes"})(on_board {"no" if power else "yes"}){field("Reference",d["ref"],0,-4,True)}{field("Value",d["name"][4:] if power else d["name"],0,4,True)}{"".join(units)})'

def pins_lr(left=(),right=(),top=(),bottom=(),w=20,h=None,pitch=2):
 h=h or max(8,(max(len(left),len(right))+1)*pitch)
 out={}
 for seq,side in [(left,'L'),(right,'R')]:
  for i,p in enumerate(seq):out[str(p)]=(-w/2-4 if side=='L' else w/2+4,(i-(len(seq)-1)/2)*pitch,side)
 for seq,side in [(top,'T'),(bottom,'B')]:
  for i,p in enumerate(seq):out[str(p)]=((i-(len(seq)-1)/2)*pitch,-h/2-4 if side=='T' else h/2+4,side)
 return out,w,h

def box(page,ref,x,y,left=(),right=(),top=(),bottom=(),w=20,h=None,pitch=2,unit=1,title=None):
 pins,w,h=pins_lr(left,right,top,bottom,w,h,pitch)
 page.ic(ref,x,y,pins,w,h,unit=unit,title=title)
