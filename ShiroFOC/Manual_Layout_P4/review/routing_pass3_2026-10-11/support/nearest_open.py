import numpy as np
from PIL import Image,ImageFilter
from pathlib import Path
r=Path(__file__).resolve().parents[1];d=np.load(r/'support/h2_bdebug/debug-NTC_PHASE_B.npz');out=np.load(r/'support/h2_bdebug/reachable.npy');n=d['via'].shape[0];step=float(d['step']);origin=float(d['origin']);y0,y1,x0,x1=[round((v-origin)/step)for v in[-2,20,-18,3]];cur=out[3,y0:y1,x0:x1].copy();want=(d['via'][y0:y1,x0:x1]==0);outside=~(cur>0)
for i in range(1,201):
 cur=np.array(Image.fromarray(cur*255).filter(ImageFilter.MaxFilter(3)))//255
 hit=cur&want&outside
 if hit.any():
  yy,xx=np.where(hit);print('nearest distance Cheb',i*step,'points',[(round(origin+(x+x0)*step,3),round(origin+(y+y0)*step,3))for y,x in zip(yy,xx)][::max(1,len(xx)//25)]);break
