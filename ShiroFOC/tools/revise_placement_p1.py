#!/usr/bin/env python3
"""Create P1 from immutable P0. KiCad Python; placement only, never run after routing."""
from pathlib import Path
import pcbnew as p

import json, math, re, hashlib, xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'ShiroFOC_KiCad'; DEST=ROOT/'ShiroFOC_KiCad_P1'; OUT=DEST/'outputs/placement_P1'
SOURCE_HASH='199d052530e0e359f049a839891653e5bbcbe091f8ede0724fa191cd88128ae4'
source=SRC/'ShiroFOC_KiCad.kicad_pcb'; target=DEST/source.name
assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_HASH, 'P0 changed; review before regenerating'
if target.exists():
 assert not re.search(r'\n\t\((segment|via|zone)\b',target.read_text()), 'Refusing to overwrite routing'
b=p.LoadBoard(str(source)); fps={f.GetReference():f for f in b.GetFootprints()}
mm=p.FromMM
vec=lambda x,y:p.VECTOR2I(mm(x),mm(y))
pos=lambda x,y:vec(100+x,100+y)
xy=lambda f:(p.ToMM(f.GetPosition().x)-100,p.ToMM(f.GetPosition().y)-100)
initial={r:(*xy(f),f.GetOrientationDegrees()) for r,f in fps.items()}
fixed=set(); changed=set(); moves=[]
holes=[(6,6),(74,6),(74,74),(6,74)]
def setpos(r,x,y,a=None,lock=False):
 f=fps[r]
 if a is not None:f.SetOrientationDegrees(a)
 f.SetPosition(pos(x,y)); changed.add(r)
 if lock:fixed.add(r)
def translate(refs,dx,dy,lock=False):
 for r in refs:
  x,y=xy(fps[r]);setpos(r,x+dx,y+dy,lock=lock)
def bounds(f):
 layer=p.B_CrtYd if f.IsFlipped() else p.F_CrtYd
 items=f.GraphicalItems()
 if not hasattr(items,'__iter__'):raise RuntimeError('Bad graphics for '+f.GetReference()+' '+str(type(items)))
 boxes=[g.GetBoundingBox() for g in items if g.GetLayer()==layer]
 if not boxes:boxes=[q.GetBoundingBox() for q in f.Pads()]
 return tuple(z/1e6-100 for z in (min(a.GetLeft() for a in boxes),min(a.GetTop() for a in boxes),max(a.GetRight() for a in boxes),max(a.GetBottom() for a in boxes)))
def pbounds(pad):
 a=pad.GetBoundingBox();return tuple(z/1e6-100 for z in (a.GetLeft(),a.GetTop(),a.GetRight(),a.GetBottom()))
def overlap(a,c,g=.1):return a[0]<c[2]+g and a[2]+g>c[0] and a[1]<c[3]+g and a[3]+g>c[1]
def hardware_clear(a):
 return all(math.hypot(max(a[0],min(cx,a[2]))-cx,max(a[1],min(cy,a[3]))-cy)>=4 for cx,cy in holes)
# Preserve all three existing cans; a 20 mm pitch clears the upper screws.
for i,x in enumerate((20,40,60)):setpos('C'+str(101+i),x,12,lock=True)
# Repeat the local cell geometry at the same 14 mm pitch as the phase terminals.
for i,y in enumerate((28,42,56)):
 n=410+10*i
 for r,dx,dy,angle in [(f'Q{401+i}',0,0,180),(f'C{n+5}',-3.5,0,90),
  (f'R{n+6}',1.65,-6,0),(f'C{n+2}',0,5.9,90),(f'R{n+1}',3,5.5,90),
  (f'R{n+2}',-3,5.5,90),(f'R{n+3}',5,4.0,90),(f'R{n+4}',-3,8.7,90),
  (f'C{n+3}',5,0,90),(f'R{n+5}',11.5,-7,0),(f'TH{701+i}',4,1,90)]:
  if r==f'R{n+5}' and not fps[r].IsFlipped():fps[r].Flip(fps[r].GetPosition(),False)
  setpos(r,64+dx,y+dy,angle,True)
setpos('J401',75,28,-90,True)
# The freed former bridge area now houses the brake circuit. Its wire terminals
# remain accessible from above, close to the bulk bank and brake MOSFET.
translate([r for r in fps if re.fullmatch('[RCUDQ]50[0-9]|R510',r)],-42,-25)
setpos('Q501',28,29,180,True);setpos('U501',22,29,180,True)
setpos('U502',22,36,0,True);setpos('J501',46,27,-90,True)
setpos('D504',38,30,90,True)
# Shift the controller and its analog/decoupling cluster together, keeping the
# back-side pin-local parts out of the new shunt strip.
core=['U301','Y301','L301','D302']+[f'C{n}' for n in range(301,315)]+[f'R{n}' for n in range(301,315) if n!=308]+['C108','C411','C421','C431']
for i in range(3):
 n=410+i*10
 core += [f'R{n}',f'R{n+7}',f'R{n+8}',f'R{n+9}',f'C{n+4}',f'R{441+i}',f'R{701+i}',f'R{711+i}',f'C{711+i}']
translate(core,-6,2)
for r,cx in [('C411',46),('C421',48),('C431',50)]:setpos(r,cx,39.9,90,True)
setpos('D503',25,39,90);setpos('D502',25,33,90);setpos('R502',24,26,90)
fixed.update(['U601','U301','J101','J201','J601','J801','J802'])
# Match the four mounting symbols already present in the mechanical schematic.
x=E.parse(OUT/'source_netlist.xml').getroot();comps={c.attrib['ref']:c for c in x.find('components')}
rootuuid=re.search(r'\(uuid "?([0-9a-f-]{36})',(DEST/'ShiroFOC_KiCad.kicad_sch').read_text()).group(1)
for i,(cx,cy) in enumerate(holes,1):
 r='H'+str(i);c=comps[r]
 f=p.FootprintLoad('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty','MountingHole_3.2mm_M3')
 f.SetReference(r);f.SetValue(c.findtext('value'));f.SetFPID(p.LIB_ID('MountingHole','MountingHole_3.2mm_M3'))
 f.SetPath(p.KIID_PATH('/'+rootuuid+c.find('sheetpath').attrib['tstamps']+c.findtext('tstamps').split()[0]))
 f.SetSheetname(c.find('sheetpath').attrib['names']);f.SetSheetfile('ShiroFOC_KiCad.kicad_sch')
 f.SetAttributes(f.GetAttributes()|p.FP_EXCLUDE_FROM_BOM);f.SetDNP(False)
 for field in c.findall('fields/field'):f.SetField(field.attrib['name'],field.text or '')
 b.Add(f);fps[r]=f;setpos(r,cx,cy,lock=True);f.SetLocked(True)
# Remove obsolete planning annotations, including the top-side magnet envelope.
for d in list(b.GetDrawings()):
 if d.GetLayer()==p.Dwgs_User or isinstance(d,p.PCB_TEXT) and d.GetText()=='SHIROFOC P0':b.RemoveNative(d)
# Resolve only displaced/interfering small parts. Keep large/functional anchors explicit.
placed={r:fps[r] for r in sorted(fixed)}
cached_b={r:bounds(f) for r,f in placed.items()}
cached_v={r:[pbounds(v) for v in f.Pads() if v.GetAttribute() in (p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH)] for r,f in placed.items()}
def conflicts(f):
 r=f.GetReference();a=bounds(f);bad=[]
 if r not in ('J101','J201','J401','C101','C102','C103','R415','R425','R435') and (min(a[:2])<1 or max(a[2:])>79):bad.append('edge')
 if not r.startswith('H') and not hardware_clear(a):bad.append('screw envelope')
 for rr,q in placed.items():
  if rr==r:continue
  if rr.startswith('H') or r.startswith('H'):continue # explicit diameter-8 hardware envelope above
  if f.GetLayer()==q.GetLayer():
   if overlap(a,cached_b[rr]):
    # J401 has three separate courtyards: use individual terminal pads + courtyard margin.
    if rr=='J401' and not any(overlap(a,pbounds(v),.5) for v in q.Pads()):continue
    if r=='J401' and not any(overlap(cached_b[rr],pbounds(v),.5) for v in f.Pads()):continue
    bad.append(rr)
  else:
   if any(overlap(a,v,.15) for v in cached_v[rr]):bad.append(rr+' through pad')
   if any(overlap(cached_b[rr],pbounds(v),.15) for v in f.Pads() if v.GetAttribute() in (p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH)):bad.append(rr+' body')
 if f.IsFlipped() and r!='U601' and overlap(a,(45.7,44.7,50.3,49.3),.1):bad.append('MCU thermal area')
 return bad
fixed_problems={r:conflicts(f) for r,f in placed.items() if conflicts(f)}
print('Fixed-anchor conflicts:',fixed_problems)
# Preserve unaffected parts first. Test pads have the lowest placement priority.
remaining=[r for r in fps if r not in fixed]
remaining.sort(key=lambda r:(r.startswith('TP'),r not in core,r in changed,-(bounds(fps[r])[2]-bounds(fps[r])[0])*(bounds(fps[r])[3]-bounds(fps[r])[1]),r))
for r in remaining:
 f=fps[r];sx,sy=xy(f);why=conflicts(f)
 if why:
  found=False
  for radius in range(1,33):
   offsets=[(dx*.5,dy*.5) for dx in range(-radius,radius+1) for dy in range(-radius,radius+1) if max(abs(dx),abs(dy))==radius]
   for dx,dy in sorted(offsets,key=lambda z:z[0]**2+z[1]**2):
    f.SetPosition(pos(sx+dx,sy+dy))
    if not conflicts(f):found=True;break
   if found:break
  if not found:raise RuntimeError('No position for '+r+' '+str(why))
  moves.append({'ref':r,'from':[sx,sy],'to':xy(f),'reason':why})
 placed[r]=f;cached_b[r]=bounds(f);cached_v[r]=[pbounds(v) for v in f.Pads() if v.GetAttribute() in (p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH)]
# Washer envelopes are mechanical drawings; holes are real NPTH footprints.
for cx,cy in holes:
 sh=p.PCB_SHAPE();sh.SetShape(p.SHAPE_T_CIRCLE);sh.SetCenter(pos(cx,cy));sh.SetEnd(pos(cx+4,cy));sh.SetLayer(p.Dwgs_User);sh.SetWidth(mm(.1));b.Add(sh)
for s,x,y,size in [('ShiroFOC P1 | COMPONENT PLACEMENT | 80 x 80 mm',40,-6,1.2),('2 / 0.5 / 0.5 / 2 oz | L2 + L3 GND | UNROUTED',40,-3,1),('4 x M3 clearance: 3.2 mm NPTH | circles = 8 mm hardware envelope',40,84,.85)]:
 t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(pos(x,y));t.SetLayer(p.Dwgs_User);t.SetTextSize(vec(size,size));t.SetTextThickness(mm(.15));b.Add(t)
for r,f in fps.items():
 f.Value().SetVisible(False)
 for field in f.GetFields():
  if field.GetName()!='Reference':field.SetVisible(False)
 f.Reference().SetLayer(p.B_Fab if f.IsFlipped() else p.F_Fab)
 f.Reference().SetTextSize(vec(.8,.8));f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
 a=bounds(f);f.Reference().SetPosition(pos((a[0]+a[2])/2,a[1]-.65))
b.BuildConnectivity();p.SaveBoard(str(target),b)
record={r:{'x_mm':round(xy(f)[0],3),'y_mm':round(xy(f)[1],3),'angle':f.GetOrientationDegrees(),'side':'B' if f.IsFlipped() else 'F','bounds':bounds(f)} for r,f in fps.items()}
(OUT/'placement_manifest.json').write_text(json.dumps({'original_hash':SOURCE_HASH,'components':record,'collision_relocations':moves,'fixed_conflicts':fixed_problems},indent=2)+'\n')
print('Saved',target,len(fps),'footprints; automatic local adjustments',len(moves))
