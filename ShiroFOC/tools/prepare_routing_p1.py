#!/usr/bin/env python3
"""Apply the pin-local analog and brake-connector revisions before first routing."""
from pathlib import Path
import zipfile, json, math
import pcbnew as p
root=Path(__file__).resolve().parents[1];proj=root/'ShiroFOC_KiCad_P1';out=proj/'outputs/routing_P1'
# Always build from the dated placement checkpoint; never overwrite a routed board.
target=proj/'ShiroFOC_KiCad.kicad_pcb'
import re
assert not re.search(r'\n\t\((segment|via|zone)\b',target.read_text()), 'Routing exists; edit it incrementally'
with zipfile.ZipFile(root/'backups/ShiroFOC_P1_before_routing_2026-09-20.zip') as z:
 (out/'placement_baseline.kicad_pcb').write_bytes(z.read('ShiroFOC_KiCad_P1/ShiroFOC_KiCad.kicad_pcb'))
b=p.LoadBoard(str(out/'placement_baseline.kicad_pcb'));fs={f.GetReference():f for f in b.GetFootprints()}
v=lambda x,y:p.VECTOR2I(p.FromMM(100+x),p.FromMM(100+y))
changes={}
def put(r,x,y,a=0,side=None):
 f=fs[r]
 if side and f.IsFlipped()!=(side=='B'):f.Flip(f.GetPosition(),False)
 f.SetOrientationDegrees(a);f.SetPosition(v(x,y));changes[r]=(x,y,a,'B' if f.IsFlipped() else 'F')
put('J501',5.5,13,-90)
# W and V ratio networks. Orient input 1k resistors toward incoming Kelvin pairs.
for base,oy in [(430,46.0),(420,51.1)]:
 for r,x,y,a in [(f'R{base+9}',54.4,oy,0),(f'C{base+4}',54.4,oy-1.7 if base==430 else oy+1.7,0),
  (f'R{base+8}',57.6,oy,180),(f'R{base+7}',57.6,oy+1.7,180),
  (f'R{base}',54.4,oy+3.4,0),(f'R{443 if base==430 else 442}',57.6,oy+3.4,0)]:put(r,x,y,a)
# U channel faces the south analog pins.
for r,x,y,a in [('R419',51,53.3,0),('C414',51,55,0),('R418',54.4,56.2,180),('R417',51,56.7,0),('R410',51,58.4,0),('R441',54.4,58.4,0)]:put(r,x,y,a)
# The two fastest analog decouplers get direct same-side pin access.
put('C303',55,44.2,0,'F');put('C305',55,46.3,0,'F')
put('C304',54.2,41.0,0);put('C306',57.6,42.6,0)
# Local reservoir/zero-ohm branches outside the op-amp feedback cells.
put('R301',51,42,0);put('R302',57.6,40.4,0)
# Leave a real power-bus corridor between the controller's analog cells and bridges.
# Move the controller with its pin-local circuits, preserving the relative analog geometry.
core=['U301','Y301','L301','D302','C108','C411','C421','C431']+[f'C{n}' for n in range(301,315)]+[f'R{n}' for n in range(301,315) if n!=308]
for i in range(3):
 n=410+i*10
 core += [f'R{n}',f'R{n+7}',f'R{n+8}',f'R{n+9}',f'C{n+4}',f'R{441+i}',f'R{701+i}',f'R{711+i}',f'C{711+i}']
for r in core:
 f=fs[r];pt=f.GetPosition();put(r,p.ToMM(pt.x)-106,p.ToMM(pt.y)-98,f.GetOrientationDegrees())
for r in ['U701','C701','C702','R309','R714']:
 if r in core:continue
 f=fs[r];pt=f.GetPosition();put(r,p.ToMM(pt.x)-100,p.ToMM(pt.y)-110,f.GetOrientationDegrees())
for r,cy in [('R310',45.5),('R311',47.3),('R312',49.1),('C314',50.9)]:put(r,35,cy,0,'F')
put('R307',35,43,0,'F');put('C108',43.8,53.5,0)
for r in ['U701','C701','C702','R309','R714']:
 f=fs[r];pt=f.GetPosition();put(r,p.ToMM(pt.x)-102,p.ToMM(pt.y)-99,f.GetOrientationDegrees())
# Reposition only interfering noncritical parts around fixed critical networks.
def bounds(f):
 lay=p.B_CrtYd if f.IsFlipped() else p.F_CrtYd
 a=[g.GetBoundingBox() for g in f.GraphicalItems() if g.GetLayer()==lay]
 if not a:a=[z.GetBoundingBox() for z in f.Pads()]
 return tuple(z/1e6-100 for z in (min(q.GetLeft() for q in a),min(q.GetTop() for q in a),max(q.GetRight() for q in a),max(q.GetBottom() for q in a)))
def pb(q):
 a=q.GetBoundingBox();return tuple(z/1e6-100 for z in (a.GetLeft(),a.GetTop(),a.GetRight(),a.GetBottom()))
def overlap(a,c,g=.1):return a[0]<c[2]+g and a[2]+g>c[0] and a[1]<c[3]+g and a[3]+g>c[1]
fixed=(set(changes)-{'R701','R702','R703','R711','R712','R713','C711','C712','C713','C108','C313','C701','C702','R714'})|{'U301','U601'}|{r for r in fs if r.startswith(('Q','J','H')) or r in ['C101','C102','C103','C415','C425','C435','C412','C422','C432','C413','C423','C433','R416','R426','R436','R415','R425','R435']}
placed={r:fs[r] for r in sorted(fixed)};cache={r:bounds(f) for r,f in placed.items()};vp={r:[pb(q) for q in f.Pads() if q.GetAttribute() in (p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH)] for r,f in placed.items()}
def bad(f):
 r=f.GetReference();a=bounds(f);errors=[]
 if not r.startswith(('J','H')) and r not in ['C101','C102','C103','R415','R425','R435'] and (min(a[:2])<1 or max(a[2:])>79):errors.append('edge')
 for cx,cy in [(6,6),(74,6),(74,74),(6,74)]:
  if not r.startswith('H') and math.hypot(max(a[0],min(cx,a[2]))-cx,max(a[1],min(cy,a[3]))-cy)<4:errors.append('washer')
 for rr,q in placed.items():
  if r==rr or rr.startswith('H') or r.startswith('H'):continue
  if q.GetLayer()==f.GetLayer():
   if overlap(a,cache[rr]):
    if rr=='J401' and not any(overlap(a,pb(z),.5) for z in q.Pads()):continue
    if r=='J401' and not any(overlap(cache[rr],pb(z),.5) for z in f.Pads()):continue
    errors.append(rr)
  else:
   if any(overlap(a,z,.15) for z in vp[rr]):errors.append(rr+' via')
   if any(overlap(cache[rr],pb(z),.15) for z in f.Pads() if z.GetAttribute() in (p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH)):errors.append(rr+' body')
 if f.IsFlipped() and r!='U601' and overlap(a,(39.7,46.7,44.3,51.3),.1):errors.append('MCU thermal')
 return errors
print('Fixed conflicts', {r:bad(f) for r,f in placed.items() if bad(f)},flush=True)
adjust=[]
for r in sorted(set(fs)-fixed,key=lambda r:(r.startswith('TP'),-(bounds(fs[r])[2]-bounds(fs[r])[0])*(bounds(fs[r])[3]-bounds(fs[r])[1]),r)):
 f=fs[r];pt=f.GetPosition();x,y=p.ToMM(pt.x)-100,p.ToMM(pt.y)-100
 if bad(f):
  why=bad(f);found=False
  for rad in range(1,25):
   offsets=[(dx*.5,dy*.5) for dx in range(-rad,rad+1) for dy in range(-rad,rad+1) if max(abs(dx),abs(dy))==rad]
   for dx,dy in sorted(offsets,key=lambda v:v[0]**2+v[1]**2):
    f.SetPosition(v(x+dx,y+dy))
    if not bad(f):found=True;break
   if found:break
  assert found,r
  adjust.append({'ref':r,'old':[x,y],'new':[p.ToMM(f.GetPosition().x)-100,p.ToMM(f.GetPosition().y)-100],'conflicts':why})
 placed[r]=f;cache[r]=bounds(f);vp[r]=[pb(q) for q in f.Pads() if q.GetAttribute() in (p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH)]
for f in fs.values():
 f.Reference().SetLayer(p.B_Fab if f.IsFlipped() else p.F_Fab);f.Reference().SetMirrored(f.IsFlipped())
 a=bounds(f);f.Reference().SetPosition(v((a[0]+a[2])/2,a[1]-.65));f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
b.BuildConnectivity();p.SaveBoard(str(target),b)
# Saving a board loaded under a temporary basename can write default project
# constraints. Restore the explicit project rules from the placement checkpoint.
with zipfile.ZipFile(root/'backups/ShiroFOC_P1_before_routing_2026-09-20.zip') as z:
 for name in ['ShiroFOC_KiCad.kicad_pro','ShiroFOC_KiCad.kicad_dru']:(proj/name).write_bytes(z.read('ShiroFOC_KiCad_P1/'+name))
(out/'preroute_placement_changes.json').write_text(json.dumps({'intentional_moves':changes,'local_adjustments':adjust},indent=2)+'\n')
print('Saved placement refinements',len(changes),len(adjust),flush=True)
