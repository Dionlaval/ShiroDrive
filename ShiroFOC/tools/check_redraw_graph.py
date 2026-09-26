"""Fast pre-export physical connectivity check against the frozen A0 circuit."""
import collections,json,re
from redraw_engine import NETS,G
from redraw_core import build_core,build_gate
from redraw_power import build_dc,build_aux,build_brake
from redraw_interfaces import build_can,build_usb,build_spi
from redraw_analog import build_inverter,build_sensing,build_feedback

def check_pages(pages):
 parent={}
 def get(a):
  parent.setdefault(a,a)
  if parent[a]!=a:parent[a]=get(parent[a])
  return parent[a]
 def join(a,b):parent[get(a)]=get(b)
 def node(page,p):return(page.name,round(p[0],6),round(p[1],6))
 physical={}
 for page in pages:
  points=set(page.points.values())|{p for _,p,_,_ in page.labels}|set(page.powerpoints)
  for a,b in page.wires:points|={a,b}
  for a,b in page.wires:
   ps=[p for p in points if (a[0]==b[0]==p[0] and min(a[1],b[1])<=p[1]<=max(a[1],b[1])) or (a[1]==b[1]==p[1] and min(a[0],b[0])<=p[0]<=max(a[0],b[0]))]
   for p in ps:join(node(page,a),node(page,p))
  for net,pt,kind,side in page.labels:join(node(page,pt),('GLOBAL' if kind=='global' else page.name,net))
  for item in page.items:
   m=re.match(r'\(symbol\(lib_id "ShiroFOC_Redraw:PWR_[^\"]+"\)\(at ([-\d.]+) ([-\d.]+)',item)
   if m:
    val=re.search(r'\(property "Value" "([^"]+)"',item).group(1)
    join(node(page,(float(m[1])/G,float(m[2])/G)),('GLOBAL',val))
  for (ref,pin,u),pt in page.points.items():physical[(ref,pin)]=node(page,pt)
 groups=collections.defaultdict(list)
 for (ref,pin),pt in physical.items():
  if NETS[(ref,pin)] is not None:groups[get(pt)].append((ref,pin,NETS[(ref,pin)]))
 errors=[]
 for gp,members in groups.items():
  nets={v for _,_,v in members}
  if len(nets)>1:errors.append({'kind':'SHORT','nets':sorted(nets),'members':members})
 bynet=collections.defaultdict(list)
 for gp,members in groups.items():
  for net in {m[2] for m in members}:bynet[net].append([m for m in members if m[2]==net])
 for net,components in bynet.items():
  if len(components)>1:errors.append({'kind':'OPEN','net':net,'groups':components})
 return errors
if __name__=='__main__':
 pages=[build_dc(),build_aux(),build_core(),build_gate(),build_inverter(),build_sensing(),build_brake(),build_spi(),build_feedback(),build_can(),build_usb()]
 errors=check_pages(pages)
 print(json.dumps(errors,indent=2));print('Failures:',len(errors))
