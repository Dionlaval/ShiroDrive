#!/usr/bin/env python3
"""Move optional snubbers out of the phase-current exits; candidate + native DRC."""
from pathlib import Path
import pcbnew as p
import shutil,sys
src=Path(sys.argv[1]);dst=Path(sys.argv[2]);b=p.LoadBoard(str(src));mm=p.FromMM;v=lambda x,y:p.VECTOR2I(mm(x+100),mm(y+100));fs={f.GetReference():f for f in b.GetFootprints()};nets={n.GetNetname():n for n in b.GetNetInfo().NetsByNetcode().values()}
# Obsolete autorouted branches to the old snubber resistor positions.
obsolete={'f85b0793-f948-42cf-8531-76dbe081e585','290f0ec9-4945-42b2-9cbd-7965b038ebfb'}
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() in obsolete:
  assert not t.IsLocked()
  b.RemoveNative(t)
for i,y in enumerate([28,42,56]):
 ref=f'C{413+i*10}';f=fs[ref];net=next(q.GetNetname()for q in f.Pads()if q.GetNumber()=='1')
 for t in list(b.GetTracks()):
  if t.GetNetname()==net:b.RemoveNative(t)
 f.SetPosition(v(72,y+7.5));f.SetOrientationDegrees(180)
 # Put the matching resistor beneath the same cell, preserving a compact RC loop.
 r=fs[f'R{415+i*10}'];r.SetPosition(v(75.5,y+7.5));r.SetOrientationDegrees(180)
 def via(net,x,yy):
  q=p.PCB_VIA(b);q.SetPosition(v(x,yy));q.SetWidth(mm(.6));q.SetDrill(mm(.3));q.SetViaType(p.VIATYPE_THROUGH);q.SetLayerPair(p.F_Cu,p.B_Cu);q.SetFrontTentingMode(p.TENTING_MODE_TENTED);q.SetBackTentingMode(p.TENTING_MODE_TENTED);q.SetNet(nets[net]);q.SetLocked(True);b.Add(q)
 def trace(net,points,width=.5,layer=p.F_Cu):
  for a,c in zip(points,points[1:]):
   t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*c));t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(nets[net]);t.SetLocked(True);b.Add(t)
 via(net,73.1,y+7.5)
 out='OUT'+str(i+1);via(out,78.2,y+7.5);trace(out,[(78.2,y+7.5),(78.2,y)],.5)
 # U/V capacitor ground lands already overlap the next shunt's GND via bank.
 if i==2:
  via('GND',70.525,y+8.55);trace('GND',[(70.525,y+7.5),(70.525,y+8.55)],.4)
for ext in['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
p.SaveBoard(str(dst),b);b=p.LoadBoard(str(dst));b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b);print(dst)
