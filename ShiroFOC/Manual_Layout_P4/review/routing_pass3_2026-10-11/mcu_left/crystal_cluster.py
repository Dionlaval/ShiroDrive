from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parent;src=r/'nrst_fixed/ShiroFOC_Manual.kicad_pcb';dst=r/'cluster_shift/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(parents=True,exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not (dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));project=m.GetProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False);tracks=list(b.GetTracks());removed=[];added=[];moves=[];via_moves=[]
for f in b.GetFootprints():
 if f.GetReference() in ['Y301','C308','C309']:
  pos=f.GetPosition();old=[pos.x,pos.y];angle=f.GetOrientationDegrees();f.SetPosition(p.VECTOR2I(pos.x-p.FromMM(.8),pos.y));moves.append({'uuid':f.m_Uuid.AsString(),'reference':f.GetReference(),'old':{'position_nm':old,'angle_deg':angle},'new':{'position_nm':[f.GetPosition().x,f.GetPosition().y],'angle_deg':angle}})
via_ids=['512746a0-c6a0-4f66-8bdc-8fdd04ea34b0','718a50de-5417-4e3d-af01-9ca05f58ee79','2a9103fe-9ed1-428f-8ac4-cc06da31b085','76cb84be-a027-4fa7-92c2-aa1f01c36af4']
for t in tracks:
 if t.m_Uuid.AsString() in via_ids:
  v=p.Cast_to_PCB_VIA(t.Duplicate());v.SetParent(b);old=t.GetPosition();v.SetPosition(p.VECTOR2I(old.x-p.FromMM(.8),old.y));b.Remove(t);b.Add(v);removed.append(t.m_Uuid.AsString());added.append(v);via_moves.append({'old_uuid':t.m_Uuid.AsString(),'new_uuid':v.m_Uuid.AsString(),'net':v.GetNetname(),'old_position_nm':[old.x,old.y],'new_position_nm':[v.GetPosition().x,v.GetPosition().y]})
for t in tracks:
 if t.Type()==p.PCB_TRACE_T and t.GetLayer()==p.F_Cu and t.GetNetname() in ['Net-(U4A-PF0)','Net-(U4A-PF1)']:b.Remove(t);removed.append(t.m_Uuid.AsString())
nets={a.GetNetname():a for a in b.GetNetInfo().NetsByNetcode().values()}
def path(net,layer,coords):
 for a,c in zip(coords,coords[1:]):
  t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));t.SetEnd(p.VECTOR2I(p.FromMM(c[0]),p.FromMM(c[1])));t.SetLayer(layer);t.SetWidth(p.FromMM(.1524));t.SetNet(nets[net]);b.Add(t);added.append(t)
def via(net,xy):
 t=p.PCB_VIA(b);t.SetPosition(p.VECTOR2I(p.FromMM(xy[0]),p.FromMM(xy[1])));t.SetWidth(p.FromMM(.5));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(nets[net]);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(t);added.append(t)
path('Net-(U4A-PF0)',p.F_Cu,[(-9.545,5.949685),(-10.932674,5.949685),(-11.1328,5.749559),(-11.1328,4.8972),(-12.11,3.92)])
path('Net-(U4A-PF1)',p.F_Cu,[(-9.545,6.449811),(-9.592389,6.4972),(-13.4328,6.4972),(-14.31,5.62)])
path('INPUT_MUX_ENABLE_N',p.F_Cu,[(-9.545,4.949433),(-10.150567,4.949433),(-10.45,4.65)]);via('INPUT_MUX_ENABLE_N',(-10.45,4.65))
path('CAN_TERM_DISABLE',p.F_Cu,[(-9.545,5.449559),(-10.45,5.449559)]);via('CAN_TERM_DISABLE',(-10.45,5.449559))
b.BuildConnectivity();filler=p.ZONE_FILLER(b);filler.Fill(b.Zones());p.SaveBoard(str(dst),b);(dst.parent/'delta.json').write_text(json.dumps({'source':str(src),'candidate':str(dst),'removed_ids':removed,'new_ids':[t.m_Uuid.AsString() for t in added],'footprint_moves':moves,'existing_via_moves':via_moves},indent=2));print(dst)
