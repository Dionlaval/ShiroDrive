from pathlib import Path
import pcbnew as p, json, shutil, math
r=Path(__file__).resolve().parent
b=p.LoadBoard(str(r/'baseline.kicad_pcb'))
f={x.GetReference():x for x in b.GetFootprints()}
def xy(v):return [p.ToMM(v.x),p.ToMM(v.y)]
def pt(v):return p.VECTOR2I(p.FromMM(v[0]),p.FromMM(v[1]))
moves=[];added=[]
def move(ref,x=None,y=None,angle=None):
 q=f[ref];before={'position':xy(q.GetPosition()),'angle':q.GetOrientationDegrees(),'side':q.GetLayerName()}
 if angle is not None:q.SetOrientationDegrees(angle)
 if x is not None:q.SetPosition(pt([x,y]))
 moves.append({'reference':ref,'uuid':q.m_Uuid.AsString(),'before':before,'after':{'position':xy(q.GetPosition()),'angle':q.GetOrientationDegrees(),'side':q.GetLayerName()}})
def pad(ref,no):return next(a for a in f[ref].Pads() if a.GetNumber()==str(no))
def track(net,points,layer=p.F_Cu,width=.254):
 for a,z in zip(points,points[1:]):
  if math.dist(a,z)<.000002:continue
  t=p.PCB_TRACK(b);t.SetStart(pt(a));t.SetEnd(pt(z));t.SetLayer(layer);t.SetWidth(p.FromMM(width));t.SetNetCode(b.GetNetsByName()[net].GetNetCode());b.Add(t)
  added.append({'uuid':t.m_Uuid.AsString(),'type':'track','net':net,'layer':b.GetLayerName(layer),'points':[a,z],'width_mm':width})
def via(net,pos):
 v=p.PCB_VIA(b);v.SetPosition(pt(pos));v.SetWidth(p.FromMM(.5));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(b.GetNetsByName()[net].GetNetCode());b.Add(v)
 added.append({'uuid':v.m_Uuid.AsString(),'type':'via','net':net,'position':pos,'diameter_mm':.5,'drill_mm':.3})
move('C203',angle=180)




move('R503',angle=90)
# Local input commutation loop, directly down from adjacent VIN / PGND pins.
vin=xy(pad('U201',3).GetPosition());gnd=xy(pad('U201',1).GetPosition());cv=xy(pad('C202',1).GetPosition());cg=xy(pad('C202',2).GetPosition())
track('VM',[vin,[vin[0],cv[1]-abs(cv[0]-vin[0])],cv])
track('VM',[vin,xy(pad('U201',2).GetPosition())])
track('GND',[gnd,[gnd[0],cg[1]-abs(cg[0]-gnd[0])],cg])
bv=xy(pad('C201',1).GetPosition());bg=xy(pad('C201',2).GetPosition())
track('VM',[cv,[bv[0],cv[1]+abs(bv[0]-cv[0])],bv])
track('GND',[cg,[cg[0],bg[1]-abs(bg[0]-cg[0])],bg])
# Brake driver bypass: front-side capacitors sit over the back-side supply pins.
for n in ['1','2']:
 cp=pad('C502',n);vpos=xy(cp.GetPosition());via(cp.GetNetname(),vpos)
 cpbulk=pad('C501',n);pbulk=xy(cpbulk.GetPosition());dx=abs(pbulk[0]-vpos[0]);track(cp.GetNetname(),[vpos,[vpos[0],pbulk[1]-dx],pbulk])
# Complete short driver/gate/source loop; resistor end orientation now faces its counterpart.
o=xy(pad('U501',5).GetPosition());rp=xy(pad('R503',1).GetPosition())
track(pad('R503',1).GetNetname(),[o,[o[0]+abs(rp[1]-o[1]),rp[1]],rp],p.B_Cu)
gate=xy(pad('Q501',4).GetPosition());gate[0]+=.10;via(pad('Q501',4).GetNetname(),gate)
rg=xy(pad('R503',2).GetPosition());track(pad('Q501',4).GetNetname(),[rg,[gate[0]+abs(rg[1]-gate[1]),rg[1]],gate],p.B_Cu)
source=xy(pad('Q501',1).GetPosition());via('GND',source)
dg=xy(pad('U501',4).GetPosition());track('GND',[dg,[dg[0],source[1]+abs(source[0]-dg[0])],source],p.B_Cu)
# Local clamp paths, front side.
for n,target in [('1',gate),('2',source)]:
 q=pad('D501',n);start=xy(q.GetPosition());track(q.GetNetname(),[start,[start[0],target[1]+abs(target[0]-start[0])],target])
# Comparator bypass uses supply directly above its IC pin and the existing ground via.
vc=xy(pad('U502',6).GetPosition());via('3V3',vc)
start=xy(pad('C503',2).GetPosition());end=xy(pad('U502',2).GetPosition());track('GND',[start,[start[0]-abs(end[1]-start[1]),end[1]],end])
# The lower divider resistor and filter share the IN+ point already carrying its via.
a=xy(pad('R509',1).GetPosition());z=xy(pad('C504',1).GetPosition());track(pad('R509',1).GetNetname(),[a,[a[0],z[1]-abs(z[0]-a[0])],z],width=.1524)
p.SaveBoard(str(r/'candidate.kicad_pcb'),b)
root=r.parents[2]
for base in ['candidate','baseline']:
 for ext in ['kicad_pro','kicad_dru']:
  shutil.copy2(root/('ShiroFOC_Manual.'+ext),r/(base+'.'+ext))
manifest={'baseline':'baseline.kicad_pcb','candidate':'candidate.kicad_pcb','moves':moves,'added_copper':added,'removed_copper':[],'notes':['All source footprints preserve UUIDs/pad nets. No zones or footprint-integrated keepouts modified.','Existing main IC block placement retained after pad-level loop inspection.','C206/C215 retained: moving toward top conflicts with 10V_GOOD via; parent must leave J502 courtyard below y=-6.6.','R511/R512/D505/J502 are owned by parent and unchanged here.']}
(r/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('moves',len(moves),'added copper',len(added))
