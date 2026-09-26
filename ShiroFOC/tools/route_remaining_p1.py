#!/usr/bin/env python3
"""Candidate-only routing assistance using native copper shapes and bounded A*.

Power motor conductors, gate pairs, USB, and existing critical routes are excluded.
DRC after every batch is mandatory; no automatic acceptance of the output.
"""
import pcbnew as p
import numpy as np
import ctypes as ct
import json,sys,shutil,time,os
from pathlib import Path
src,drc,dst=map(Path,sys.argv[1:4]);only=sys.argv[4:] or None
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
b=p.LoadBoard(str(src));mm=p.FromMM;step=.05;n=1601;nn=n*n;layers=[p.F_Cu,p.B_Cu]
lib=ct.CDLL(str(Path(__file__).with_name('grid_route_native.dylib')))
byte=np.ctypeslib.ndpointer(dtype=np.uint8,flags='C_CONTIGUOUS');ints=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS');floats=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
lib.raster.argtypes=[byte,ct.c_int,floats,ints,ct.c_int,ct.c_double]
lib.route.argtypes=[byte,byte,byte,byte,ct.c_int,ct.c_int,ct.c_int,ints,ct.c_int]
byid={i.m_Uuid.AsString():i for i in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]+list(b.Zones())}
nets={a.GetNetname():a for a in b.GetNetInfo().NetsByNetcode().values()}
def drawpoly(img,poly):
 for i in range(poly.OutlineCount()):
  pts=[];counts=[]
  for j in [-1]+list(range(poly.HoleCount(i))):
   ring=poly.COutline(i)if j==-1 else poly.CHole(i,j);counts.append(ring.PointCount())
   pts.extend((p.ToMM(ring.CPoint(k).x)-100,p.ToMM(ring.CPoint(k).y)-100)for k in range(ring.PointCount()))
  if pts:lib.raster(img,n,np.array(pts,np.float64).ravel(),np.array(counts,np.int32),len(counts),step)
def shape(item,layer,amount=0):
 if item.Type()==p.PCB_VIA_T:item=p.Cast_to_PCB_VIA(item)
 poly=p.SHAPE_POLY_SET()
 if isinstance(item,p.ZONE):
  poly=p.SHAPE_POLY_SET(item.Outline() if item.GetIsRuleArea() else item.GetFilledPolysList(layer))
  if amount:poly.Inflate(mm(amount),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,mm(.005))
 else:item.TransformShapeToPolygon(poly,layer,mm(amount),mm(.004),p.ERROR_OUTSIDE)
 return poly
escape=[(36.6,43.7,47.4,54.3),(38.5,40.8,48.5,45.7)]+[(60.2,y-3.5,67.5,y+5.25)for y in [28,42,56]]
if any(z.GetZoneName()=='C412_LOCAL_ESCAPE'for z in b.Zones()):escape +=[(60.2,y+3.4,67.6,y+7.5,.2)for y in [28,42,56]]
def scoped(item):
 box=item.GetBoundingBox();x1=p.ToMM(box.GetX())-100;y1=p.ToMM(box.GetY())-100;x2=x1+p.ToMM(box.GetWidth());y2=y1+p.ToMM(box.GetHeight())
 return next((r for r in escape if x1>=r[0] and y1>=r[1] and x2<=r[2] and y2<=r[3]),None)
def copperclear(item):
 try:return .5 if item.GetNetClassName()=='Power' else .2
 except:return .2
def circle(img,x,y,r):
 x0=max(0,int((x-r)/step));x1=min(n-1,int((x+r)/step)+1);y0=max(0,int((y-r)/step));y1=min(n-1,int((y+r)/step)+1)
 if x1<x0 or y1<y0:return
 yy,xx=np.ogrid[y0:y1+1,x0:x1+1];img[y0:y1+1,x0:x1+1]|=(((xx*step-x)**2+(yy*step-y)**2)<r*r).astype(np.uint8)
def masks(net,width):
 blocks=np.zeros((2,n,n),np.uint8);vb=np.zeros((2,n,n),np.uint8)
 netclear=.5 if net in ['VM','OUT1','OUT2','OUT3','Net-(D504-A)'] or 'FORCE_P' in net else .2
 items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]
 for it in items:
  if it.GetNetname()==net:continue
  cl=max(netclear,copperclear(it));scope=scoped(it)
  for li,layer in enumerate(layers):
   if not it.IsOnLayer(layer):continue
   for img,rad in [(blocks[li],width/2),(vb[li],.225)]:
    if scope:
     temp=np.zeros((n,n),np.uint8);drawpoly(temp,shape(it,layer,cl+rad+.012))
     x1,y1,x2,y2=scope[:4];a,c=int((x1+rad+.035)/step)+1,int((x2-rad-.035)/step);d,e=int((y1+rad+.035)/step)+1,int((y2-rad-.035)/step)
     temp[d:e,a:c]=0;drawpoly(temp,shape(it,layer,(scope[4]if len(scope)>4 else .15)+rad+.012));img|=temp
    else:drawpoly(img,shape(it,layer,cl+rad+.03))
 for z in list(b.Zones())+[z for f in b.GetFootprints()for z in f.Zones()]:
  isrule=z.GetIsRuleArea()
  if not isrule and z.GetNetname()in['GND',net]:continue
  if isrule and not(z.GetDoNotAllowTracks()or z.GetDoNotAllowVias()):continue
  for li,layer in enumerate(layers):
   if not z.IsOnLayer(layer):continue
   if not isrule and z.GetNetname()=='VM' and net.startswith(('GHS','GLS','OUT')):continue
   for img,rad in [(blocks[li],width/2),(vb[li],.225)]:drawpoly(img,shape(z,layer,rad+(.01 if isrule else max(.5,netclear)+.012)))
 via=vb[0]|vb[1]
 # Through vias must retain drill web even on their own net.
 for it in items:
  if isinstance(it,p.PCB_VIA):dr=p.ToMM(it.GetDrill());extra=.2
  elif isinstance(it,p.PAD):dr=p.ToMM(max(it.GetDrillSize().x,it.GetDrillSize().y));extra=.45
  else:continue
  if dr:
   xy=it.GetPosition();circle(via,p.ToMM(xy.x)-100,p.ToMM(xy.y)-100,dr/2+.1+extra+.01)
 # Conservative edge envelope, in addition to explicit mounting rule areas.
 for a in [blocks[0],blocks[1],via]:a[:20,:]=1;a[-20:,:]=1;a[:,:20]=1;a[:,-20:]=1
 return blocks,via
def terminal(item):
 arr=np.zeros((2,n,n),np.uint8)
 for li,layer in enumerate(layers):
  if item.IsOnLayer(layer):drawpoly(arr[li],shape(item,layer))
 return arr
def component(seed):
 conn=b.GetConnectivity();seen={};queue=[seed]
 while queue:
  q=queue.pop();uid=q.m_Uuid.AsString()
  if q.Type()==p.PCB_VIA_T:q=p.Cast_to_PCB_VIA(q)
  if uid in seen:continue
  seen[uid]=q
  queue.extend(a for a in list(conn.GetConnectedTracks(q))+list(conn.GetConnectedPads(q))if a.GetNetname()==seed.GetNetname()and a.m_Uuid.AsString()not in seen)
 return seen
def cluster_terminal(items):
 arr=np.zeros((2,n,n),np.uint8)
 for item in items.values():
  for li,layer in enumerate(layers):
   if item.IsOnLayer(layer):drawpoly(arr[li],shape(item,layer))
 # An existing filled phase polygon is also a valid endpoint. Native track/
 # pad adjacency does not enumerate every pad connected through its zone.
 net=next(iter(items.values())).GetNetname()
 if net in ['OUT1','OUT2','OUT3']:
  for z in b.Zones():
   if z.GetIsRuleArea()or z.GetNetname()!=net:continue
   for li,layer in enumerate(layers):
    if not z.IsOnLayer(layer):continue
    poly=z.GetFilledPolysList(layer)
    for idx in range(poly.OutlineCount()):
     one=p.SHAPE_POLY_SET();one.AddOutline(poly.COutline(idx))
     for hi in range(poly.HoleCount(idx)):one.AddHole(poly.CHole(idx,hi))
     copper=np.zeros((n,n),np.uint8);drawpoly(copper,one)
     if np.any(copper & arr[li]):arr[li]|=copper
 return arr
def addpath(path,net,width):
 xyz=[(i//nn,(i%nn)%n,(i%nn)//n)for i in path];points=[xyz[0]]
 for i in range(1,len(xyz)-1):
  a,c,d=xyz[i-1:i+2]
  if(c[0]-a[0],c[1]-a[1],c[2]-a[2])!=(d[0]-c[0],d[1]-c[1],d[2]-c[2]):points.append(c)
 points.append(xyz[-1]);uu=[]
 def vec(a):return p.VECTOR2I(mm(100+a[1]*step),mm(100+a[2]*step))
 # Split near local-clearance boundary so a long segment cannot claim a local
 # exception outside the area's physical extent.
 expanded=[points[0]]
 for a,c in zip(points,points[1:]):
  if a[0]==c[0] and any(min(a[1],c[1])*step<r[2]and max(a[1],c[1])*step>r[0]and min(a[2],c[2])*step<r[3]and max(a[2],c[2])*step>r[1]for r in escape):
   span=max(abs(a[1]-c[1]),abs(a[2]-c[2]));parts=int(np.ceil(span/8))
   for k in range(1,parts):expanded.append((a[0],round(a[1]+(c[1]-a[1])*k/parts),round(a[2]+(c[2]-a[2])*k/parts)))
  expanded.append(c)
 for a,c in zip(expanded,expanded[1:]):
  if a==c:continue
  if a[0]!=c[0]:
   t=p.PCB_VIA(b);t.SetPosition(vec(a));t.SetWidth(mm(.45));t.SetDrill(mm(.2));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED)
  else:t=p.PCB_TRACK(b);t.SetStart(vec(a));t.SetEnd(vec(c));t.SetWidth(mm(width));t.SetLayer(layers[a[0]])
  t.SetNet(nets[net]);b.Add(t);uu.append(t.m_Uuid.AsString())
 return uu
if os.environ.get('SHIRO_STITCH'):
 block,via=masks('GND',.2);added=[]
 existing=[q.GetPosition()for q in b.GetTracks()if isinstance(q,p.PCB_VIA)and q.GetNetname()=='GND']
 existing +=[q.GetPosition()for f in b.GetFootprints()for q in f.Pads()if q.GetNetname()=='GND'and q.GetAttribute()==p.PAD_ATTRIB_PTH]
 def insert_ground(x,y,why):
  t=p.PCB_VIA(b);t.SetPosition(p.VECTOR2I(mm(x+100),mm(y+100)));t.SetWidth(mm(.45));t.SetDrill(mm(.2));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(nets['GND']);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);t.SetLocked(True);b.Add(t);existing.append(t.GetPosition());circle(via,x,y,.411);added.append([x,y,why])
 for z in list(b.Zones()):
  if z.GetIsRuleArea()or z.GetNetname()!='GND'or z.GetLayer()not in layers:continue
  polys=z.GetFilledPolysList(z.GetLayer())
  for index in range(polys.OutlineCount()):
   poly=p.SHAPE_POLY_SET();poly.AddOutline(polys.COutline(index))
   for hi in range(polys.HoleCount(index)):poly.AddHole(polys.CHole(index,hi))
   if any(poly.Contains(pt)for pt in existing):continue
   mask=np.zeros((n,n),np.uint8);drawpoly(mask,poly);ys,xs=np.where(mask&(1-via))
   if not len(xs):print('No stitch site',z.GetZoneName(),index,flush=True);continue
   cx=xs.mean();cy=ys.mean();k=np.argmin((xs-cx)**2+(ys-cy)**2);insert_ground(float(xs[k]*step),float(ys[k]*step),z.GetZoneName()+' island '+str(index))
 # Provide nearby plane-to-plane return transitions around signal vias.
 signals=[t for t in list(b.GetTracks())if isinstance(t,p.PCB_VIA)and t.GetNetname()!='GND'and copperclear(t)<.5]
 for t in signals:
  pt=t.GetPosition();x=p.ToMM(pt.x)-100;y=p.ToMM(pt.y)-100
  if any((p.ToMM(q.x)-100-x)**2+(p.ToMM(q.y)-100-y)**2<1.5**2 for q in existing):continue
  found=False
  for radius in [.85,1.15,1.5,1.9]:
   for angle in np.arange(0,2*np.pi,np.pi/8):
    xx=round((x+radius*np.cos(angle))/step);yy=round((y+radius*np.sin(angle))/step)
    if 0<=xx<n and 0<=yy<n and not via[yy,xx]:insert_ground(xx*step,yy*step,'return beside '+t.GetNetname());found=True;break
   if found:break
 b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b);dst.with_suffix('.stitches.json').write_text(json.dumps(added,indent=2));print('Ground stitches',len(added));sys.exit(0)
if os.environ.get('SHIRO_FANOUT'):
 b.BuildConnectivity();pins=[]
 for f in b.GetFootprints():
  if not f.GetReference().startswith('U'):continue
  for pad in f.Pads():
   net=pad.GetNetname()
   if not net or net=='GND'or net.startswith('unconnected-')or pad.GetAttribute()!=p.PAD_ATTRIB_SMD:continue
   if only and net not in only:continue
   if not only and list(b.GetConnectivity().GetConnectedTracks(pad)):continue
   pins.append((f.GetReference(),pad))
 log=[];output=np.zeros(100000,np.int32)
 for ref,pad in pins:
  net=pad.GetNetname();width=.2;block,via=masks(net,width);st=cluster_terminal(component(pad)) if only else terminal(pad);go=np.zeros_like(block)
  xy=pad.GetPosition();cx=p.ToMM(xy.x)-100;cy=p.ToMM(xy.y)-100;li=0 if pad.IsOnLayer(p.F_Cu)else 1
  block[1-li]=1
  for radius in ([12.0]if os.environ.get('SHIRO_FANOUT_RECT')else[1.2,1.8,2.4,4.0]):
   go[:]=0;circle(go[li],cx,cy,radius);go[li]&=1-via
   # Prefer a via beside a land rather than inside its solder opening.
   copper=terminal(pad);go[li]&=1-copper[li]
   if os.environ.get('SHIRO_FANOUT_RECT'):
    xx,yy,xx2,yy2=map(float,os.environ['SHIRO_FANOUT_RECT'].split(','));region=np.zeros((n,n),np.uint8);region[int(yy/step):int(yy2/step),int(xx/step):int(xx2/step)]=1;go[li]&=region
   rc=lib.route(block,via,st,go,n,400000,6000,output,len(output))
   if rc>0:break
  if rc>0:
   path=list(reversed(output[:rc].tolist()));end=path[-1];path.append((end+nn)%(2*nn));ids=addpath(path,net,width);log.append({'net':net,'ref':ref,'pin':pad.GetNumber(),'new_items':ids})
  print('fanout',ref,pad.GetNumber(),net,rc,flush=True)
 b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b);dst.with_suffix('.fanouts.json').write_text(json.dumps(log,indent=2));sys.exit(0)
report=json.loads(drc.read_text());jobs=[]
for u in report['unconnected_items']:
 a,c=[byid.get(z['uuid'])for z in u['items']]
 if a is None or c is None or isinstance(a,p.ZONE)or isinstance(c,p.ZONE):continue
 net=a.GetNetname()
 if net!=c.GetNetname():continue
 if only and net not in only:continue
 if not only and (net in ['GND','VM','VCC','OUT1','OUT2','OUT3'] or net.startswith(('GHS','GLS')) or 'FORCE' in net or 'USB_D' in net):continue
 jobs.append((net,a,c))
def priority(job):
 net,a,c=job;aa=a.GetPosition();cc=c.GetPosition();dist=((aa.x-cc.x)**2+(aa.y-cc.y)**2)**.5/1e6
 # Complete pin-local circuitry before distant diagnostic branches.
 return (only.index(net) if only else (1 if 'SPARE' in net else 0),dist)
jobs.sort(key=priority)
log=[];output=np.zeros(100000,np.int32)
for index,(net,a,c)in enumerate(jobs):
 t0=time.time();width=float(os.environ.get('SHIRO_ROUTE_WIDTH','.3'if net.startswith(('GHS','GLS','OUT'))else '.2'))
 b.BuildConnectivity();ca=component(a)
 if c.m_Uuid.AsString()in ca:
  print(index+1,len(jobs),net,'already connected',flush=True);continue
 cc=component(c)
 block,via=masks(net,width);st=cluster_terminal(ca);go=cluster_terminal(cc)
 partner=os.environ.get('SHIRO_PARTNER_NET')
 if partner:
  allowed=np.zeros((n,n),np.uint8)
  for t in b.GetTracks():
   if t.GetNetname()==partner:
    for lay in layers:
     if t.IsOnLayer(lay):drawpoly(allowed,shape(t,lay,1.2))
  for cluster in [ca,cc]:
   for t in cluster.values():
    for lay in layers:
     if t.IsOnLayer(lay):drawpoly(allowed,shape(t,lay,float(os.environ.get('SHIRO_PAIR_ESCAPE','5'))))
  block|=(1-allowed)[None,:,:]
 if os.environ.get('SHIRO_GRID_DEBUG'):
  np.savez('/tmp/shiro-grid-debug.npz',block=block,via=via,st=st,go=go)
 rc=lib.route(block,via,st,go,n,10000000,6000,output,len(output))
 path=list(reversed(output[:rc].tolist()))if rc>0 else []
 path_xyz=[(q//nn,(q%nn)%n,(q%nn)//n)for q in path]
 if os.environ.get('SHIRO_GRID_DEBUG'):np.save('/tmp/shiro-path.npy',np.array(path_xyz))
 length=sum(((q[1]-r[1])**2+(q[2]-r[2])**2)**.5*step for q,r in zip(path_xyz,path_xyz[1:]))
 via_count=sum(q[0]!=r[0]for q,r in zip(path_xyz,path_xyz[1:]))
 limit=float(os.environ.get('SHIRO_MAX_LENGTH','65'if net.startswith(('GHS','GLS','OUT'))else '160'))
 rejected=rc>0 and (length>limit or via_count>int(os.environ.get('SHIRO_MAX_VIAS','6')))
 uu=addpath(path,net,width)if rc>0 and not rejected else []
 log.append({'net':net,'source':a.m_Uuid.AsString(),'target':c.m_Uuid.AsString(),'path_points':rc,'length_mm':length,'vias':via_count,'rejected':rejected,'new_items':uu})
 if rc>0:print('geometry',round(length,2),'mm',via_count,'vias','REJECTED'if rejected else 'candidate',flush=True)
 print(index+1,len(jobs),net,rc,'steps','expanded',int(output[0])if rc<0 else 0,'terminals',int((st & (1-block)).sum()),int((go & (1-block)).sum()),round(time.time()-t0,2),'s',flush=True)
 if uu:p.SaveBoard(str(dst),b)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b)
dst.with_suffix('.routes.json').write_text(json.dumps(log,indent=2));print(dst)
