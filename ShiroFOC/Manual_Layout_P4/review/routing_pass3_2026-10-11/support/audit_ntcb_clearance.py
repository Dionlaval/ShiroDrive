from pathlib import Path
import pcbnew as p,json,math
r=Path(__file__).resolve().parents[1];src=r/'support/precise_b_simplified/ShiroFOC_Manual.kicad_pcb';b=p.LoadBoard(str(src));m=json.loads((r/'support/precise_b_simplified/delta.json').read_text());old=json.loads((r/'support/precise_b/delta.json').read_text());ids=set(old['new_ids'])-set(m['removed_ids'])|set(m['new_ids']);tracks=[t for t in b.GetTracks()if t.m_Uuid.AsString()in ids];layers=list(b.GetEnabledLayers().CuStack());h=[]
for t in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]:
 n=t.GetNetname()
 if n=='VM'or n.startswith(('PHASE_','GHS','GLS','BOOTSTRAP','HS_RETURN_'))or n in['Net-(U201-SW)','/5 V / 3.3 V power/U205_SW']:
  ll=[x for x in layers if t.IsOnLayer(x)]
  if ll:h.append((t,ll))

def distance(a,c,limit):
 if a.Collide(c,0):return 0
 high=p.FromMM(limit)
 if not a.Collide(c,high):return limit
 lo=0
 for _ in range(23):
  mid=(lo+high)//2
  if a.Collide(c,mid):high=mid
  else:lo=mid+1
 return p.ToMM(high)

def info(t):
 return {'uuid':t.m_Uuid.AsString(),'net':t.GetNetname(),'position_mm':[p.ToMM(t.GetPosition().x),p.ToMM(t.GetPosition().y)],'kind':t.GetClass()}
closest_same={};closest_projected={};allproj=[]
for t in tracks:
 tll=[x for x in layers if t.IsOnLayer(x)]
 for other,ll in h:
  typ='VM'if other.GetNetname()=='VM'else 'phase'if other.GetNetname().startswith('PHASE_')else 'switch'if'SW'in other.GetNetname()else'gate/bootstrap'
  common=[x for x in tll if x in ll]
  for layer in common:
   current=closest_same.get(typ,{'distance_mm':50})['distance_mm'];dd=distance(t.GetEffectiveShape(layer),other.GetEffectiveShape(layer),current)
   if dd<current:closest_same[typ]={'distance_mm':dd,'layer':b.GetLayerName(layer),'ntcb':info(t),'hazard':info(other)}
  current=closest_projected.get(typ,{'distance_mm':50})['distance_mm'];dd=distance(t.GetEffectiveShape(tll[0]),other.GetEffectiveShape(ll[0]),current)
  if dd<current:closest_projected[typ]={'distance_mm':dd,'ntcb_layer':b.GetLayerName(tll[0]),'hazard_layer':b.GetLayerName(ll[0]),'ntcb':info(t),'hazard':info(other)}
planes=[{'net':z.GetNetname(),'layer':b.GetLayerName(l),'regions':z.GetFilledPolysList(l).OutlineCount()}for z in b.Zones()for l in z.GetLayerSet().CuStack()if z.GetNetname()=='GND']
a={'source':str(src),'new_trace_length_mm':sum(t.GetLength()/1e6 for t in tracks if t.Type()==p.PCB_TRACE_T),'new_vias':[info(t)for t in tracks if t.Type()==p.PCB_VIA_T],'same_layer_copper_edge_closest':closest_same,'projected_any_layer_closest':closest_projected,'ground_planes':planes,'note':'Projected overlap across layers is not a copper clearance violation; reference planes are assessed separately.'};(src.parent/'clearance_audit.json').write_text(json.dumps(a,indent=2));print(json.dumps(a,indent=2))
