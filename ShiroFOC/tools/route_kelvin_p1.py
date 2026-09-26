#!/usr/bin/env python3
"""Dedicated shunt sense pairs. Refill and native DRC required after this candidate."""
from pathlib import Path
import pcbnew as p
import shutil,sys,json
src=Path(sys.argv[1]);dst=Path(sys.argv[2]);b=p.LoadBoard(str(src));nets={n.GetNetname():n for n in b.GetNetInfo().NetsByNetcode().values()};mm=p.FromMM;v=lambda x,y:p.VECTOR2I(mm(x+100),mm(y+100))
for t in list(b.GetTracks()):
 if t.GetNetname().startswith('SHUNT_')and'SENSE_'in t.GetNetname():b.RemoveNative(t)
next(f for f in b.GetFootprints()if f.GetReference()=='R417').SetOrientationDegrees(180)
added={}
def track(net,pts,layer):
 for a,z in zip(pts,pts[1:]):
  t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*z));t.SetWidth(mm(.2));t.SetLayer(layer);t.SetNet(nets[net]);t.SetLocked(True);b.Add(t);added[t.m_Uuid.AsString()]=net

def via(net,x,y):
 t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(mm(.45));t.SetDrill(mm(.2));t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetViaType(p.VIATYPE_THROUGH);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);t.SetNet(nets[net]);t.SetLocked(True);b.Add(t);added[t.m_Uuid.AsString()]=net
# Shorten gate fanouts before the reserved sense corridor.
for t in list(b.GetTracks()):
 if t.GetNetname() in ['GLS1','GLS2','GLS3'] and not isinstance(t,p.PCB_VIA):
  if abs(p.ToMM(t.GetEnd().x)-151.5)<.001:t.SetEnd(p.VECTOR2I(mm(150.6),t.GetEnd().y))
# Relocate one capacitor return via outside that corridor, retaining a direct plane return.
for t in list(b.GetTracks()):
 if t.GetNetname()!='GND':continue
 pts=[t.GetPosition()]if isinstance(t,p.PCB_VIA)else[t.GetStart(),t.GetEnd()]
 if any((abs(p.ToMM(pt.x)-153.225)<.001 and abs(p.ToMM(pt.y)-144.6)<.001) or (abs(p.ToMM(pt.x)-151.1375)<.001 and abs(p.ToMM(pt.y)-132.125)<.001) for pt in pts):b.RemoveNative(t)
track('GND',[(51.1375,32.725),(49.9,32.1)],p.B_Cu);via('GND',49.9,32.1)
track('GND',[(52.375,44.6),(54.9,44.0)],p.B_Cu);via('GND',54.9,44)

# Keep the main top-side VM spine continuous. V/W sense pairs cross its
# bottom reinforcement; stitching at the phase cells carries current between faces.
for phase,sy,ny,py,nx,px,ndest,pdest in [
 ('U',18.8,17.5,18.8,51.2,51.8,(49.225,58.2),(45.825,58.7)),
 ('V',32.8,31,31.7,52.4,53.0,(52.425,53.1),(52.425,54.8)),
 ('W',46.8,45,45.7,53.6,54.2,(52.425,48),(52.425,49.7))]:
 n='SHUNT_'+phase+'_SENSE_N';q='SHUNT_'+phase+'_SENSE_P'
 npts=[(69.675,sy),(69.675,ny),(nx,ny)]
 ppts=[(61.625,sy),(61.625,py),(px,py)]
 nv=(nx,26)if phase=='U'else(nx,ny);pv=(px,26.8)if phase=='U'else(px,py)
 if phase=='U':npts.append(nv);ppts.append(pv)
 track(n,npts,p.B_Cu);track(q,ppts,p.B_Cu);via(n,*nv);via(q,*pv)
 for net,start,endpoint in [(n,nv,ndest),(q,pv,pdest)]:
  ex,ey=endpoint;x,y=start
  # Amplifier U's positive input sits left of its negative input.
  finish=(x,59.5)if phase=='U'and net.endswith('_P')else(x,ey)
  track(net,[start,finish],p.F_Cu);via(net,*finish);tail=[finish,(45.825,59.5),endpoint]if phase=='U'and net.endswith('_P')else[finish,endpoint];track(net,tail,p.B_Cu)
# Re-route ordinary signals if they obstruct the reserved sense corridor.
new=[t for t in b.GetTracks()if t.m_Uuid.AsString()in added]
removed=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString()in added or t.IsLocked():continue
 for q in new:
  if t.GetNetname()==q.GetNetname():continue
  bb=t.GetBoundingBox();bb.Inflate(mm(.21))
  if not bb.Intersects(q.GetBoundingBox()):continue
  if any(t.IsOnLayer(ly)and q.IsOnLayer(ly)and t.GetEffectiveShape(ly).Collide(q.GetEffectiveShape(ly),mm(.201))for ly in [p.F_Cu,p.B_Cu]):
   removed.append(t.m_Uuid.AsString());b.RemoveNative(t);break
print('Removed ordinary conflicts',len(removed))
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
# Save without changing assignments. DRC will expose collisions for correction.
p.SaveBoard(str(dst),b);b=p.LoadBoard(str(dst));b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b)
assert all(t.GetNetname()==added[t.m_Uuid.AsString()]for t in b.GetTracks()if t.m_Uuid.AsString()in added),'New sense route was shorted'
dst.with_suffix('.kelvin.json').write_text(json.dumps(added,indent=2))
print(dst)
