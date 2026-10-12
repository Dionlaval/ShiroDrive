import ctypes as ct,numpy as np
from PIL import Image,ImageDraw
from pathlib import Path
r=Path(__file__).resolve().parents[1];d=np.load(r/'support/c310_pbdebug/debug-NTC_PHASE_B.npz');lib=ct.CDLL(str((r/'engine/grid_route_native.dylib').resolve()));by=np.ctypeslib.ndpointer(dtype=np.uint8,flags='C_CONTIGUOUS');lib.flood.argtypes=[by,by,by,by,ct.c_int];n=d['via'].shape[0];step=float(d['step']);origin=float(d['origin']);xp=[-16,-6,-3,12];x0,x1,y0,y1=[round((x-origin)/step)for x in xp];w=x1-x0;h=y1-y0;outimg=Image.new('RGB',(w*2,h*2+60),'white');draw=ImageDraw.Draw(outimg)
for i,l in enumerate(d['layers']):
 block=np.stack([d['block'][i],np.ones((n,n),np.uint8)]);st=np.stack([d['go'][i],np.zeros((n,n),np.uint8)]);out=np.zeros_like(block);lib.flood(block,np.ones((n,n),np.uint8),st,out,n)
 im=np.full((n,n,3),230,np.uint8);im[block[0]>0]=[70,70,70];im[out[0]>0]=[90,150,245];im[(out[0]>0)&(d['via']==0)]=[0,255,100];im[d['st'][i]>0]=[255,70,0];im[d['go'][i]>0]=[255,0,255]
 crop=Image.fromarray(im[y0:y1,x0:x1]);px=i%2*w;py=i//2*(h+30);outimg.paste(crop,(px,py+30));draw.text((px+10,py+5),str(l)+' x:-16..-6 y:-3..12',fill='black')
 for xv in range(-16,-5):
  xx=round((xv+16)/step)+px;draw.line((xx,py+30,xx,py+h+30),fill=(170,170,170),width=1);draw.text((xx,py+31),str(xv),fill='red')
 for yv in range(-3,13):
  yy=round((yv+3)/step)+py+30;draw.line((px,yy,px+w,yy),fill=(170,170,170),width=1);draw.text((px,yy),str(yv),fill='red')
outimg.save(r/'support/parallel_pocket.png');print('via access',np.sum(out[0]& (1-d['via'])))
