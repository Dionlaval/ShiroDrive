import re,json,uuid,copy
from pathlib import Path
P=Path('/Users/dionlava/Documents/GitHub/ShiroDrive/ShiroFOC/Manual_Rebuild')
class Q(str): pass
def parse(s):
 t=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',s); i=0
 def rec():
  nonlocal i
  x=t[i];i+=1
  if x=='(':
   r=[]
   while t[i]!=')':r.append(rec())
   i+=1;return r
  return Q(json.loads(x)) if x.startswith('"') else x
 return rec()
def dump(x,n=0):
 if not isinstance(x,list):return json.dumps(str(x),ensure_ascii=False) if isinstance(x,Q) else str(x)
 if all(not isinstance(z,list) for z in x):return '('+' '.join(dump(z) for z in x)+')'
 return '('+' '.join(dump(z) for z in x[:next((i for i,z in enumerate(x) if isinstance(z,list)),len(x))])+''.join('\n'+'\t'*(n+1)+dump(z,n+1) for z in x[next((i for i,z in enumerate(x) if isinstance(z,list)),len(x)):])+')'
def children(x,k):return [a for a in x if isinstance(a,list) and a and a[0]==k]
def one(x,k):return next(iter(children(x,k)),None)
def prop(x,k):return next((a for a in children(x,'property') if a[1]==k),None)
def val(x,k):return prop(x,k)[2] if prop(x,k) else None
def syms(x):return children(x,'symbol')
def ref(x,r):return next(a for a in syms(x) if val(a,'Reference')==r)
def read(f):return parse(Path(f).read_text())
def write(f,x):Path(f).write_text(dump(x)+'\n')
def uid():return Q(str(uuid.uuid4()))
def update(x,k,v):prop(x,k)[2]=Q(v)
def shift(x,dx,dy):
 for a in x:
  if isinstance(a,list):
   if a[0] in ('at','xy'):
    a[1]=str(round(float(a[1])+dx,4));a[2]=str(round(float(a[2])+dy,4))
   else:shift(a,dx,dy)
def clone(x,newref,xy):
 y=copy.deepcopy(x);at=one(y,'at');shift(y,xy[0]-float(at[1]),xy[1]-float(at[2]));update(y,'Reference',newref)
 def rec(a):
  if a[0]=='uuid':a[1]=uid()
  if a[0]=='reference':a[1]=Q(newref)
  for b in a:
   if isinstance(b,list):rec(b)
 rec(y);return y
aux=read(P/'02_Auxiliary_Power.kicad_sch');gate=read(P/'04_Gate_Driver.kicad_sch')
