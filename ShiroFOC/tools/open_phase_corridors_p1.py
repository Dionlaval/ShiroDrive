#!/usr/bin/env python3
"""Rotate local bus capacitors to open between-phase routing channels."""
from pathlib import Path
import pcbnew as p
import sys,shutil,json
src,dst=map(Path,sys.argv[1:3]);b=p.LoadBoard(str(src));mm=p.FromMM;v=lambda x,y:p.VECTOR2I(mm(x+100),mm(y+100));fs={f.GetReference():f for f in b.GetFootprints()};rules=[]
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
removed=[]
for i,cy in enumerate([28,42,56]):
 ref='C'+str(412+i*10);f=fs[ref];old=[q.GetPosition()for q in f.Pads()]
 for t in list(b.GetTracks()):
  if t.GetNetname()not in ['GND','VM']:continue
  points=[t.GetPosition()]if isinstance(t,p.PCB_VIA)else[t.GetStart(),t.GetEnd()]
  if all(any(abs(p.ToMM(a.x-q.x))<1.05 and abs(p.ToMM(a.y-q.y))<1.05 for q in old)for a in points):removed.append(t.m_Uuid.AsString());b.RemoveNative(t)
 f.SetOrientationDegrees(0);f.SetPosition(v(64,cy+5.4))
 # Clear 0.1 mm courtyard overlap created by the capacitor rotation.
 for rr,dx in [(411+i*10,.2),(412+i*10,-.2)]:
  rf=fs['R'+str(rr)];oldpts=[q.GetPosition()for q in rf.Pads()]
  for t in b.GetTracks():
   if isinstance(t,p.PCB_VIA):continue
   for getter,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
    a=getter()
    if any(a==q for q in oldpts):setter(p.VECTOR2I(a.x+mm(dx),a.y))
  a=rf.GetPosition();rf.SetPosition(p.VECTOR2I(a.x+mm(dx),a.y))
 for pin,x,net in [(1,62.525,'VM'),(2,65.475,'GND')]:
  pad=next(q for q in f.Pads()if q.GetNumber()==str(pin));assert pad.GetNetname()==net
  for dx in ([-.25,.25]if net=='GND'else[.875,1.475]):
   for dy in [4.6,5.1]:
    t=p.PCB_VIA(b);t.SetPosition(v(x+dx,cy+dy));t.SetWidth(mm(.6));t.SetDrill(mm(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
  if net=='VM':
   pts=[(62.525,cy+5.4),(63.4,cy+5.1),(64,cy+5.1),(64,cy+4.6),(63.4,cy+4.6),(63.4,cy+5.1)]
   for a,c in zip(pts,pts[1:]):
    t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*c));t.SetWidth(mm(.5));t.SetLayer(p.F_Cu);t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
 # Only an exception for the populated capacitor / gate-resistor area.
 name=ref+'_LOCAL_ESCAPE';z=p.ZONE(b);s=p.LSET();s.AddLayer(p.F_Cu);s.AddLayer(p.B_Cu);z.SetLayerSet(s);z.SetIsRuleArea(True);z.SetZoneName(name)
 for setter in [z.SetDoNotAllowTracks,z.SetDoNotAllowVias,z.SetDoNotAllowCopperPour,z.SetDoNotAllowFootprints,z.SetDoNotAllowPads]:setter(False)
 poly=z.Outline();poly.NewOutline()
 for a,c in [(60.2,cy+3.4),(67.6,cy+3.4),(67.6,cy+7.5),(60.2,cy+7.5)]:poly.Append(v(a,c))
 b.Add(z);rules.append(f'''(rule "{name}" (condition "A.enclosedByArea('{name}') && B.enclosedByArea('{name}')") (constraint clearance (min 0.2mm)))''')
for t in list(b.GetTracks()):
 if 'NTC_'in t.GetNetname()and '_RAW'in t.GetNetname()and not isinstance(t,p.PCB_VIA):
  if any(p.ToMM(a.x)>165 and p.ToMM(a.x)<168 and 131<p.ToMM(a.y)<162 for a in[t.GetStart(),t.GetEnd()]):b.RemoveNative(t)
for z in b.Zones():
 if z.GetZoneName()=='VM_LOCAL_C432':
  poly=z.Outline();poly.RemoveAllContours();poly.NewOutline()
  for a,c in [(61.8,59),(66,59),(66,64.5),(61.8,64.5)]:poly.Append(v(a,c))
dst.with_suffix('.kicad_dru').write_text(dst.with_suffix('.kicad_dru').read_text()+'\n'+'\n'.join(rules)+'\n')
p.SaveBoard(str(dst),b);b=p.LoadBoard(str(dst));b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b);print('rotated C412 C422 C432, removed',len(removed),'former cap route items')
