import numpy as np

def sweep(m,phi,theta):
    a=theta[...,None]+np.array([0,-2*np.pi/3,2*np.pi/3])
    v=m*np.cos(a)
    d=.5+.5*(v-(np.max(v,axis=-1)+np.min(v,axis=-1))[...,None]/2)
    i=np.cos(a-phi[...,None])
    t=np.sort(np.concatenate([np.zeros(d.shape[:-1]+(1,)),(1-d)/2,(1+d)/2,np.ones(d.shape[:-1]+(1,))],axis=-1),axis=-1)
    dt=np.diff(t,axis=-1); mid=(t[...,1:]+t[...,:-1])/2
    s=(mid[...,None]>(1-d[...,None,:])/2)&(mid[...,None]<(1+d[...,None,:])/2)
    ib=(s*i[...,None,:]).sum(axis=-1)
    avg=(d*i).sum(axis=-1)
    ic=avg[...,None]-ib
    q=np.concatenate([np.zeros(dt.shape[:-1]+(1,)),np.cumsum(ic*dt,axis=-1)],axis=-1)
    k=np.ptp(q,axis=-1); rms=np.sqrt(np.sum(ic*ic*dt,axis=-1))
    return k,rms,t,ib,avg
if __name__=='__main__':
    theta,phi=np.meshgrid(np.linspace(0,np.pi/3,121),np.linspace(0,np.pi,181))
    best=(0,None); br=(0,None)
    for m in np.linspace(0,2/np.sqrt(3),201):
        k,r,*_=sweep(m,phi,theta)
        idx=np.unravel_index(np.argmax(k),k.shape)
        if k[idx]>best[0]:best=(float(k[idx]),[float(m),float(phi[idx]),float(theta[idx])])
        if r.max()>br[0]:br=(float(r.max()),float(m))
    print('max all',best,'cap rms coefficient',br)
    for m in [.05,.1,.2,.4,.6,.8,1,2/np.sqrt(3)]:
        th=np.linspace(0,np.pi/3,1001)
        k,r,*_=sweep(m,np.zeros_like(th),th)
        print(m,'pf1 max k',k.max(),'rms',r.max())
