import numpy as np

def response(L,C,R,fs,Ipk=1):
 A=np.array([[-R/L,-1/L],[1/C,0.]])
 ev,V=np.linalg.eig(A)
 def exp(t):return np.real_if_close(V@np.diag(np.exp(ev*t))@np.linalg.inv(V)).real
 h=1/(4*fs); E=exp(h)
 def forced(u,t):return np.linalg.solve(A,(exp(t)-np.eye(2))@np.array([0.,-u/C]))
 bp=forced(Ipk/2,h); bm=forced(-Ipk/2,h)
 x0=np.linalg.solve(np.eye(2)-E@E,E@bp+bm)
 x1=E@x0+bp
 tt=np.linspace(0,h,1001)
 a=np.array([exp(t)@x0+forced(Ipk/2,t) for t in tt]);b=np.array([exp(t)@x1+forced(-Ipk/2,t) for t in tt])
 return np.ptp(np.r_[a[:,1],b[:,1]])
if __name__=='__main__':
 C=33e-6;f=20e3;Ip=10*np.sqrt(2)
 for lu in [.1,.2,.5,1.,2.]:
  print(lu,'f0',1/(2*np.pi*np.sqrt(lu*1e-6*C))/1e3,'Vpp',response(lu*1e-6,C,.05,f,Ip))
