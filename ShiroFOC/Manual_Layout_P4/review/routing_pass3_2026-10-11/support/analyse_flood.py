import ctypes as ct,numpy as np
from pathlib import Path
r=Path(__file__).resolve().parents[1];d=np.load(r/'support/h2_bdebug/debug-NTC_PHASE_B.npz');lib=ct.CDLL(str((r/'engine/grid_route_native.dylib').resolve()));by=np.ctypeslib.ndpointer(dtype=np.uint8,flags='C_CONTIGUOUS');lib.flood.argtypes=[by,by,by,by,ct.c_int];n=d['via'].shape[0];step=float(d['step']);origin=float(d['origin']);out=d['st'].copy()
for it in range(8):
 old=out.sum()
 for a in range(4):
  for c in range(a+1,4):
   block=np.stack([d['block'][a],d['block'][c]]);st=np.stack([out[a],out[c]]);res=np.zeros_like(st);lib.flood(block,d['via'],st,res,n);out[a]|=res[0];out[c]|=res[1]
 print('iteration',it,int(out.sum()))
 if out.sum()==old:break
for i,l in enumerate(d['layers']):
 y,x=np.where(out[i]);vy,vx=np.where(out[i]&(1-d['via']));print('layer',l,'count',len(x),'bounds',(x.min()*step+origin,x.max()*step+origin,y.min()*step+origin,y.max()*step+origin),'viaaccess',len(vx))
 if len(vx):print([(round(a*step+origin,3),round(b*step+origin,3))for a,b in zip(vx[::max(1,len(vx)//10)],vy[::max(1,len(vx)//10)])])
np.save(r/'support/h2_bdebug/reachable.npy',out)
