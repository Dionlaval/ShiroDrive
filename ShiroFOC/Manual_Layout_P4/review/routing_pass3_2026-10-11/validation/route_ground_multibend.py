#!/usr/bin/env python3
"""Candidate-only P4 router. Native KiCad DRC and review MUST precede acceptance.

Usage: native-kicad-python route_p4.py SRC DRC_JSON DST [NET ...]
Options: --layers F,B[,L3] --width .1524|.254 --max-length 45 --max-distance 40
         --max-vias 3 --max-connections 1000 --exclude NET [repeat] --no-fill
Manifest records every added connection and its individual item UUIDs for pruning.
"""
import argparse,ctypes as ct,json,math,shutil,time
from pathlib import Path
import pcbnew as p
import numpy as np

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('src',type=Path);ap.add_argument('drc',type=Path);ap.add_argument('dst',type=Path);ap.add_argument('nets',nargs='*')
ap.add_argument('--layers',default='F,B');ap.add_argument('--width',type=float,choices=[.1524,.254],default=.1524)
ap.add_argument('--max-length',type=float,default=60);ap.add_argument('--max-distance',type=float,default=45);ap.add_argument('--max-vias',type=int,default=3);ap.add_argument('--max-connections',type=int,default=1000);ap.add_argument('--exclude',action='append',default=[]);ap.add_argument('--no-fill',action='store_true');ap.add_argument('--step',type=float,default=.05);ap.add_argument('--via-cost',type=int,default=6000)
args=ap.parse_args();src=args.src.resolve();dst=args.dst.resolve()
if src==dst:raise SystemExit('Source and destination must differ; candidate-only tool.')
dst.parent.mkdir(parents=True,exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:
 s=src.with_suffix(ext);d=dst.with_suffix(ext)
 if s.exists() and s!=d:shutil.copy2(s,d)
for name in ['fp-lib-table','sym-lib-table']:
 s=src.parent/name;d=dst.parent/name
 if s.exists() and s!=d:shutil.copy2(s,d)
for name in ['libs','lib','footprints','symbols']:
 s=src.parent/name;d=dst.parent/name
 if s.exists() and not d.exists():d.symlink_to(s.resolve(),target_is_directory=s.is_dir())
# Project must remain alive throughout board operations: no implicit dummy settings.
manager=p.SETTINGS_MANAGER();manager.LoadProject(str(src.with_suffix('.kicad_pro')))
project=manager.GetProject(str(src.with_suffix('.kicad_pro')))
b=p.LoadBoard(str(src));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity()
mm=p.FromMM;step=args.step;origin=-22.5;n=int(round(45/step))+1;nn=n*n
layernames={'F':p.F_Cu,'B':p.B_Cu,'L3':6,'L4':8};layers=[layernames[a] for a in args.layers.split(',')]
alllayers=list(b.GetEnabledLayers().CuStack());nl=len(layers)
lib=ct.CDLL(str(Path(__file__).resolve().parent.parent/'engine/grid_route_native.dylib'))
byte=np.ctypeslib.ndpointer(dtype=np.uint8,flags='C_CONTIGUOUS');ints=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS');floats=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
lib.raster.argtypes=[byte,ct.c_int,floats,ints,ct.c_int,ct.c_double]
lib.route.argtypes=[byte,byte,byte,byte,ct.c_int,ct.c_int,ct.c_int,ct.c_int,ints,ct.c_int]
netobjs={a.GetNetname():a for a in b.GetNetInfo().NetsByNetcode().values()}
footprints=list(b.GetFootprints());pads=[a for f in footprints for a in f.Pads()]
# Keep wrappers and boards alive: KiCad/SWIG owns all these C++ objects.
oldtracks=list(b.GetTracks());oldids={t.m_Uuid.AsString() for t in oldtracks};added=[]
boardpoly=p.SHAPE_POLY_SET();validoutline=b.GetBoardPolygonOutlines(boardpoly)
if not validoutline:raise SystemExit('Cannot obtain closed board outline.')


def drawpoly(img,poly):
 for i in range(poly.OutlineCount()):
  pts=[];counts=[]
  for j in [-1]+list(range(poly.HoleCount(i))):
   ring=poly.COutline(i) if j==-1 else poly.CHole(i,j);counts.append(ring.PointCount())
   pts.extend((p.ToMM(ring.CPoint(k).x)-origin,p.ToMM(ring.CPoint(k).y)-origin) for k in range(ring.PointCount()))
  if pts:lib.raster(img,n,np.array(pts,np.float64).ravel(),np.array(counts,np.int32),len(counts),step)

def shape(item,layer,amount=0):
 if item.Type()==p.PCB_VIA_T:item=p.Cast_to_PCB_VIA(item)
 poly=p.SHAPE_POLY_SET()
 if isinstance(item,p.ZONE):
  poly=p.SHAPE_POLY_SET(item.Outline() if item.GetIsRuleArea() else item.GetFilledPolysList(layer))
  if amount:poly.Inflate(mm(amount),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,mm(.005))
 else:item.TransformShapeToPolygon(poly,layer,mm(amount),mm(.003),p.ERROR_OUTSIDE)
 return poly

def clear(item):
 try:return .5 if item.GetNetClassName()=='Power' else .2
 except:return .2

def circle(img,x,y,r):
 x-=origin;y-=origin;x0=max(0,int((x-r)/step));x1=min(n-1,int((x+r)/step)+1);y0=max(0,int((y-r)/step));y1=min(n-1,int((y+r)/step)+1)
 if x1<x0 or y1<y0:return
 yy,xx=np.ogrid[y0:y1+1,x0:x1+1];img[y0:y1+1,x0:x1+1]|=(((xx*step-x)**2+(yy*step-y)**2)<=r*r).astype(np.uint8)

def onboard(item):
 pos=item.GetPosition();return boardpoly.Contains(pos)

eligiblepads=[]
for f in footprints:
 if f.IsDNP() or 'DNP' in f.GetValue().upper() or not onboard(f):continue
 eligiblepads.extend(pad for pad in f.Pads() if onboard(pad) and pad.GetNetname() and not pad.GetNetname().startswith('unconnected-'))
eligibleids={pad.m_Uuid.AsString() for pad in eligiblepads}
# Existing exact custom rule: U4 courtyard allows 0.15 clearance locally. The
# raster applies it only where routing and obstacle copper both intersect it.
u4=next((f for f in footprints if f.GetReference()=='U4'),None);u4mask=np.zeros((n,n),np.uint8)
if u4:
 u4.BuildCourtyardCaches();drawpoly(u4mask,u4.GetCourtyard(p.F_Cu))
margin=.001

def boundary(rad):
 poly=p.SHAPE_POLY_SET(boardpoly);poly.Inflate(-mm(rad+.5+margin),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,mm(.005));out=np.zeros((n,n),np.uint8);drawpoly(out,poly);return 1-out
trackedge=boundary(args.width/2);viaedge=boundary(.25)

def masks(net,width):
 blocks=np.zeros((nl,n,n),np.uint8);via=viaedge.copy()
 nc=next((clear(x) for x in eligiblepads if x.GetNetname()==net),.2)
 items=list(b.GetTracks())+pads
 for it in items:
  own=it.GetNetname()==net
  cl=max(nc,clear(it))
  if not own:
   for li,layer in enumerate(layers):
    if not it.IsOnLayer(layer):continue
    normal=np.zeros((n,n),np.uint8);drawpoly(normal,shape(it,layer,cl+width/2+margin))
    if np.any(u4mask):
     raw=np.zeros((n,n),np.uint8);drawpoly(raw,shape(it,layer))
     if np.any(raw & u4mask):
      local=np.zeros((n,n),np.uint8);drawpoly(local,shape(it,layer,.15+width/2+margin));normal=(normal & (1-u4mask))|local
    blocks[li]|=normal
  # A through via has copper on every enabled layer. All internal tracks/pads
  # are considered even when routing only on F/B. Planes refill around vias.
  for layer in alllayers:
   if not it.IsOnLayer(layer):continue
   if not own:
    normal=np.zeros((n,n),np.uint8);drawpoly(normal,shape(it,layer,cl+.25+margin))
    if np.any(u4mask):
     raw=np.zeros((n,n),np.uint8);drawpoly(raw,shape(it,layer))
     if np.any(raw & u4mask):
      area=p.SHAPE_POLY_SET(u4.GetCourtyard(p.F_Cu));area.Inflate(mm(.25),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,mm(.003));area_mask=np.zeros((n,n),np.uint8);drawpoly(area_mask,area)
      local=np.zeros((n,n),np.uint8);drawpoly(local,shape(it,layer,.15+.25+margin));normal=(normal & (1-area_mask))|local
    via|=normal
   elif isinstance(it,p.PAD):drawpoly(via,shape(it,layer,.25+.025))
  # Universal 0.45 mm drill web, including same-net holes and through slots.
  if isinstance(it,p.PAD) and it.HasDrilledHole():
   hole=p.SHAPE_POLY_SET();it.TransformHoleToPolygon(hole,mm(.15+.45+margin),mm(.003),p.ERROR_OUTSIDE);drawpoly(via,hole)
  elif it.Type()==p.PCB_VIA_T:
   vi=p.Cast_to_PCB_VIA(it);xy=vi.GetPosition();circle(via,p.ToMM(xy.x),p.ToMM(xy.y),p.ToMM(vi.GetDrill())/2+.15+.45+margin)
 for z in list(b.Zones())+[z for f in footprints for z in f.Zones()]:
  if z.GetIsRuleArea():
   if z.GetDoNotAllowVias():drawpoly(via,shape(z,p.F_Cu,.25+margin))
   if z.GetDoNotAllowTracks():
    for li,layer in enumerate(layers):
     if z.IsOnLayer(layer):drawpoly(blocks[li],shape(z,layer,width/2+margin))
  elif z.GetNetname() not in ['GND','3V3',net]:
   for li,layer in enumerate(layers):
    if z.IsOnLayer(layer):drawpoly(blocks[li],shape(z,layer,max(nc,.2)+width/2+margin))
 blocks|=trackedge[None,:,:]
 return blocks,via

def component(seed):
 conn=b.GetConnectivity();seen={};queue=[seed]
 while queue:
  q=queue.pop();uid=q.m_Uuid.AsString()
  if q.Type()==p.PCB_VIA_T:q=p.Cast_to_PCB_VIA(q)
  if uid in seen:continue
  seen[uid]=q
  queue.extend(a for a in list(conn.GetConnectedTracks(q))+list(conn.GetConnectedPads(q)) if a.GetNetname()==seed.GetNetname() and a.m_Uuid.AsString() not in seen)
 return seen

def gridpoint(pos):return round((p.ToMM(pos.x)-origin)/step),round((p.ToMM(pos.y)-origin)/step)

def terminals(items):
 arr=np.zeros((nl,n,n),np.uint8);centres={}
 for uid,item in items.items():
  if not onboard(item):continue
  for li,layer in enumerate(layers):
   if not item.IsOnLayer(layer):continue
   if isinstance(item,p.PAD):
    if uid not in eligibleids:continue
    x,y=gridpoint(item.GetPosition())
    if 0<=x<n and 0<=y<n:arr[li,y,x]=1;centres[li*nn+y*n+x]=item.GetPosition()
   elif item.Type() in [p.PCB_TRACE_T,p.PCB_ARC_T,p.PCB_VIA_T]:drawpoly(arr[li],shape(item,layer))
 return arr,centres

def addpath(path,net,width,centres):
 xyz=[(i//nn,(i%nn)%n,(i%nn)//n) for i in path];points=[xyz[0]]
 for i in range(1,len(xyz)-1):
  a,c,d=xyz[i-1:i+2]
  if (c[0]-a[0],c[1]-a[1],c[2]-a[2])!=(d[0]-c[0],d[1]-c[1],d[2]-c[2]):points.append(c)
 points.append(xyz[-1]);ids=[]
 def vec(a):
  idx=a[0]*nn+a[2]*n+a[1]
  if (a==xyz[0] or a==xyz[-1]) and idx in centres:return centres[idx]
  return p.VECTOR2I(mm(origin+a[1]*step),mm(origin+a[2]*step))
 for a,c in zip(points,points[1:]):
  if a==c:continue
  if a[0]!=c[0]:
   t=p.PCB_VIA(b);t.SetPosition(vec(a));t.SetWidth(mm(.5));t.SetDrill(mm(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu)
   t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED)
  else:
   if vec(a)==vec(c):continue
   t=p.PCB_TRACK(b);t.SetStart(vec(a));t.SetEnd(vec(c));t.SetWidth(mm(width));t.SetLayer(layers[a[0]])
  t.SetNet(netobjs[net]);b.Add(t);added.append(t);ids.append(t.m_Uuid.AsString())
 return ids

# Scoped support-ground routing. Each new connection reaches a filled ground
# plane through an existing or one new via, with per-group IDs for pruning.
gndnet=netobjs['GND'];gndcode=gndnet.GetNetCode();planes=[(z,l)for z in b.Zones()if z.GetNetname()=='GND'for l in z.GetLayerSet().CuStack()if l not in[p.F_Cu,p.B_Cu]]
def has_plane(it):return any(it.IsOnLayer(l)and z.HitTestFilledArea(l,it.GetPosition())for z,l in planes)
def connected(q):
 seen=component(q);return any(has_plane(x)for x in seen.values())
def outside_shared(q):
 bb=q.GetBoundingBox();return bb.GetRight()<mm(-14)or bb.GetLeft()>mm(-3)or bb.GetBottom()<mm(2)or bb.GetTop()>mm(14)
refs=args.nets or ['U601','U901','U602','U801','U202','U603','U604','U502','U204','C601','C602','C603','C604','C605','C606','C607','C801','C802','C901','C902','C903','C904','C503','C504','C505']
if not args.nets:
 for f in footprints:
  if f.GetReference().startswith('R')and f.GetReference()not in refs:refs.append(f.GetReference())
priority={ref:i for i,ref in enumerate(refs)}
candidates=[q for q in eligiblepads if q.GetNetname()=='GND'and q.GetParentFootprint().GetReference()in priority and max(q.GetSize().x,q.GetSize().y)<=mm(2)and outside_shared(q)]
candidates.sort(key=lambda q:(priority[q.GetParentFootprint().GetReference()],q.GetNumber()))
yy,xx=np.ogrid[:n,:n];xxmm=origin+xx*step;yymm=origin+yy*step;shared=((xxmm>=-14.13)&(xxmm<=-2.87)&(yymm>=1.87)&(yymm<=14.13))
plane_sites=np.ones((n,n),np.uint8)
for layer in sorted({l for z,l in planes}):
 mask=np.zeros((n,n),np.uint8)
 for z,l in planes:
  if l==layer:drawpoly(mask,z.GetFilledPolysList(l))
 plane_sites&=mask
cache={}
for width in [.254,.1524]:
 block,via=masks('GND',width);block[:,shared]=1;via[shared]=1;cache[width]=(block,via)
power_shapes=[p.SHAPE_POLY_SET(z.GetFilledPolysList(l)) for z in b.Zones() if z.GetNetname()=='3V3' for l in z.GetLayerSet().CuStack()]
def power_cut(point):
 v=p.PCB_VIA(b);v.SetPosition(point);v.SetWidth(mm(.5));v.SetDrill(mm(.3));shape=p.SHAPE_POLY_SET();v.TransformShapeToPolygon(shape,8,mm(.275),mm(.003),p.ERROR_OUTSIDE)
 result=[]
 for poly in power_shapes:
  cut=p.SHAPE_POLY_SET(poly);cut.BooleanSubtract(shape);cut.Simplify()
  if cut.OutlineCount()>poly.OutlineCount():return None
  result.append(cut)
 return result
logs=[];output=np.zeros(100000,np.int32)
for pad in candidates:
 b.BuildConnectivity();ref=pad.GetParentFootprint().GetReference();label=ref+'.'+pad.GetNumber();starttime=time.time()
 if connected(pad):logs.append({'pad':label,'skipped':'already reaches GND plane'});continue
 limit=3 if ref.startswith('R') or ref=='U601' else 2
 start=pad.GetPosition();gx,gy=gridpoint(start);local=((xxmm-p.ToMM(start.x))**2+(yymm-p.ToMM(start.y))**2<=limit**2)
 targets=[t for t in list(b.GetTracks())if isinstance(t,p.PCB_VIA)and t.GetNetname()=='GND'and has_plane(t)and math.hypot(t.GetPosition().x-start.x,t.GetPosition().y-start.y)<=mm(limit+.01)]
 source=np.zeros((nl,n,n),np.uint8);source_centres={}
 for li,layer in enumerate(layers):
  if pad.IsOnLayer(layer):source[li,gy,gx]=1;source_centres[li*nn+gy*n+gx]=start
 accepted=None
 for mode in ['existing','new']:
  if mode=='existing'and not targets:continue
  for width in [.254,.1524]:
   block,via=cache[width];block=block.copy();block[:,~local]=1;goal=np.zeros((nl,n,n),np.uint8);centres=dict(source_centres)
   if mode=='existing':
    for target in targets:
     x,y=gridpoint(target.GetPosition())
     for li,layer in enumerate(layers):goal[li,y,x]=1;centres[li*nn+y*n+x]=target.GetPosition()
   else:
    allowed=(1-via)&plane_sites&local
    for li,layer in enumerate(layers):
     if pad.IsOnLayer(layer):goal[li]=allowed
   # Surface-layer only search: no inter-layer transitions are permitted.
   novias=np.ones((n,n),np.uint8);rc=-2;guard_shapes=None
   for site_attempt in range(80):
    rc=lib.route(block,novias,source,goal,n,nl,1500000,args.via_cost,output,len(output))
    if rc<=0:break
    path=list(reversed(output[:rc].tolist()));xyz=[(v//nn,(v%nn)%n,(v%nn)//n)for v in path];length=sum(math.hypot(a[1]-c[1],a[2]-c[2])*step for a,c in zip(xyz,xyz[1:]))
    if length>limit+.001:rc=-2;break
    if mode=='existing':break
    li,x,y=xyz[-1];point=p.VECTOR2I(mm(origin+x*step),mm(origin+y*step));guard_shapes=power_cut(point)
    if guard_shapes is not None:break
    forbidden=((xx-x)**2+(yy-y)**2<=9)
    goal[:,forbidden]=0
    rc=-2
   if rc<=0:continue
   ids=addpath(path,'GND',width,centres);viauid=None;endindex=path[-1];li,x,y=xyz[-1];end=centres.get(endindex,p.VECTOR2I(mm(origin+x*step),mm(origin+y*step)))
   if mode=='new':
    v=p.PCB_VIA(b);v.SetPosition(end);v.SetWidth(mm(.5));v.SetDrill(mm(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetFrontTentingMode(p.TENTING_MODE_TENTED);v.SetBackTentingMode(p.TENTING_MODE_TENTED);v.SetNetCode(gndcode);b.Add(v);added.append(v);viauid=v.m_Uuid.AsString();ids.append(viauid)
    for _,vm in cache.values():circle(vm,p.ToMM(end.x),p.ToMM(end.y),.751)
    power_shapes=guard_shapes
   accepted={'id':'ground_'+label,'net':'GND','pad':label,'pad_uuid':pad.m_Uuid.AsString(),'new_items':ids,'length_mm':length,'width_mm':width,'new_via_uuid':viauid,'target_mode':mode,'start_mm':[p.ToMM(start.x),p.ToMM(start.y)],'end_mm':[p.ToMM(end.x),p.ToMM(end.y)]};break
  if accepted:break
 if accepted:logs.append(accepted);p.SaveBoard(str(dst),b);print(label,'accepted',round(accepted['length_mm'],3),accepted['target_mode'],accepted['width_mm'],flush=True)
 else:logs.append({'pad':label,'skipped':f'no legal surface path <= {limit} mm to existing ground via or new via site'});print(label,'no route',round(time.time()-starttime,2),flush=True)
 dst.with_suffix('.ground_manifest.json').write_text(json.dumps({'source':str(src),'candidate':str(dst),'groups':[q for q in logs if q.get('new_items')],'skipped':[q for q in logs if not q.get('new_items')]},indent=2)+'\n')
b.BuildConnectivity();filler=p.ZONE_FILLER(b);filler.Fill(b.Zones());p.SaveBoard(str(dst),b)
print('groups',len([q for q in logs if q.get('new_items')]),'newitems',len(added),flush=True)
