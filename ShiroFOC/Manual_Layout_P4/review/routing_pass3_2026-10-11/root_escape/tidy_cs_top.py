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
margin=.014

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
    if layer==p.F_Cu and np.any(u4mask):
     raw=np.zeros((n,n),np.uint8);drawpoly(raw,shape(it,layer))
     if np.any(raw & u4mask):
      local=np.zeros((n,n),np.uint8);drawpoly(local,shape(it,layer,.15+width/2+margin));normal=(normal & (1-u4mask))|local
    blocks[li]|=normal
  # A through via has copper on every enabled layer. All internal tracks/pads
  # are considered even when routing only on F/B. Planes refill around vias.
  for layer in alllayers:
   if not it.IsOnLayer(layer):continue
   if not own:drawpoly(via,shape(it,layer,cl+.25+margin))
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


changes={'6b63f445-7454-4226-9b52-4a3a279c1558':None,'d940b6a0-b9df-4565-8b01-93d352528e1e':((-11.375,-.424999),(-8.75,-2.899999)), '914b2a57-85ea-40b7-a954-85fb8003cafb':((4.05,4.025),(5.425,5.4)), '7c8dad06-7a2c-4482-96b2-9b4b5901f337':((4.525,1.45),(4.525,3.55)), 'be2cd675-4aea-4e63-aabe-ffc0d8134c79':((4.525,3.55),(4.05,4.025)), 'd9ea8eec-338b-4ea8-9c74-1bf26ce70dcb':((-.449999,2.1),(-.199999,2.35))}
for t in oldtracks:
 u=t.m_Uuid.AsString()
 if u not in changes:continue
 b.Remove(t)
 if changes[u] is None:continue
 q=t.Duplicate();q.SetParent(b);q.SetStart(p.VECTOR2I(*(mm(v)for v in changes[u][0])));q.SetEnd(p.VECTOR2I(*(mm(v)for v in changes[u][1])));b.Add(q);added.append(q)
b.BuildConnectivity();fill=p.ZONE_FILLER(b);fill.Fill(b.Zones());p.SaveBoard(str(dst),b)
