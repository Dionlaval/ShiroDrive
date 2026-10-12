from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parent;src=r.parent/'merged_03/ShiroFOC_Manual.kicad_pcb';dst=r/'can_manual/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(parents=True,exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not (dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));project=m.GetProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False);tracks=list(b.GetTracks());removed=[];added=[]
for t in tracks:
 if t.m_Uuid.AsString() in ['cc45d318-8def-4b11-b57d-774ac1bf1666','5852aa90-7e54-483b-8639-8f266cf23650','ca28b5e6-436d-4c9f-8d26-a4ccbe7cd93e']:
  v=t.Duplicate();v.SetParent(b);new=p.VECTOR2I(p.FromMM(-8.649999),p.FromMM(6.12))
  if t.Type()==p.PCB_VIA_T:v=p.Cast_to_PCB_VIA(v);v.SetPosition(new)
  elif t.GetLayer()==p.F_Cu:v.SetEnd(new)
  else:
   removed.append(t.m_Uuid.AsString());b.Remove(t);continue
  removed.append(t.m_Uuid.AsString());b.Remove(t);b.Add(v);added.append(v)
for t in tracks:
 if t.GetNetname()=='FEEDBACK_I_H3' and t.GetLayer()==8 and p.ToMM(t.GetStart().y)==5.5 and p.ToMM(t.GetEnd().y)==5.5:
  removed.append(t.m_Uuid.AsString());b.Remove(t)
nets={a.GetNetname():a for a in b.GetNetInfo().NetsByNetcode().values()}
def path(net,layer,coords):
 for a,c in zip(coords,coords[1:]):
  t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));t.SetEnd(p.VECTOR2I(p.FromMM(c[0]),p.FromMM(c[1])));t.SetLayer(layer);t.SetWidth(p.FromMM(.1524));t.SetNet(nets[net]);b.Add(t);added.append(t)
def via(net,xy):
 t=p.PCB_VIA(b);t.SetPosition(p.VECTOR2I(p.FromMM(xy[0]),p.FromMM(xy[1])));t.SetWidth(p.FromMM(.5));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(nets[net]);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(t);added.append(t)
path('FEEDBACK_I_H3',8,[(-7.199999,5.5),(-7.65,5.5),(-8.0,5.15),(-8.0,4.21),(-9.25,4.21),(-9.55,4.51),(-9.55,5.5)])
path('NTC_BRAKE',p.B_Cu,[(-8.649999,6.12),(-9.35,6.12),(-9.65,5.82),(-9.65,5.35)])
path('CAN_TERM_DISABLE',p.F_Cu,[(-9.545,5.449559),(-8.924559,5.449559),(-8.875,5.4)])
via('CAN_TERM_DISABLE',(-8.875,5.4))
b.BuildConnectivity();filler=p.ZONE_FILLER(b);filler.Fill(b.Zones());p.SaveBoard(str(dst),b);(dst.parent/'delta.json').write_text(json.dumps({'source':str(src),'candidate':str(dst),'removed_ids':removed,'new_ids':[t.m_Uuid.AsString() for t in added],'footprint_moves':[]},indent=2));print(dst)
