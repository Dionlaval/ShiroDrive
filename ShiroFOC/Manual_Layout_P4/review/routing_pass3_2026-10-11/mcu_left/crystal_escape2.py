from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parent;src=r.parent/'before/ShiroFOC_Manual.kicad_pcb';dst=r/'crystal_shift2/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(parents=True,exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not (dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));project=m.GetProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False)
f=next(f for f in b.GetFootprints() if f.GetReference()=='Y301');pos=f.GetPosition();old=[pos.x,pos.y];angle=f.GetOrientationDegrees();f.SetPosition(p.VECTOR2I(pos.x-p.FromMM(.6),pos.y));moves=[{'uuid':f.m_Uuid.AsString(),'reference':'Y301','old':{'position_nm':old,'angle_deg':angle},'new':{'position_nm':[f.GetPosition().x,f.GetPosition().y],'angle_deg':angle}}]
removed=['bb565293-f95d-4add-b81d-2d4a5ab603cc','cccf689b-950b-4732-8d29-02a786d9f3ca','d9b664c4-7905-4726-8709-4cbafbb3df83','ed8d0836-ddc0-44db-96ba-e4eba16254c0'];tracks=list(b.GetTracks());oldlength=sum(p.ToMM(t.GetLength()) for t in tracks if t.m_Uuid.AsString() in removed)
net=next(t.GetNet() for t in tracks if t.m_Uuid.AsString()==removed[0])
for t in tracks:
 if t.m_Uuid.AsString() in removed:b.Remove(t)
coords=[(-9.545,5.949685),(-10.725,5.949685),(-10.925,5.749685),(-10.925,4.825),(-11.46,4.29)];added=[]
for a,c in zip(coords,coords[1:]):
 t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));t.SetEnd(p.VECTOR2I(p.FromMM(c[0]),p.FromMM(c[1])));t.SetLayer(p.F_Cu);t.SetWidth(p.FromMM(.1524));t.SetNet(net);b.Add(t);added.append(t)
# Relocate the intermediate IMU return via above the shifted crystal.
imu_old=['d04e1ded-c943-4c81-aa4f-c115969ee95d','45457d05-838e-4522-9d90-511cfb65d0ba','1b4f795c-e389-45e0-8123-8eb1a9875948']
for t in tracks:
 if t.m_Uuid.AsString() in imu_old:
  v=t.Duplicate();v.SetParent(b)
  if t.Type()==p.PCB_VIA_T:v=p.Cast_to_PCB_VIA(v);v.SetPosition(p.VECTOR2I(p.FromMM(-12.299999),p.FromMM(2.5)))
  elif t.GetLayer()==p.B_Cu:v.SetStart(p.VECTOR2I(p.FromMM(-12.299999),p.FromMM(2.5)))
  else:v.SetEnd(p.VECTOR2I(p.FromMM(-12.299999),p.FromMM(2.5)))
  b.Remove(t);b.Add(v);added.append(v)
removed.extend(imu_old)
b.BuildConnectivity();filler=p.ZONE_FILLER(b);filler.Fill(b.Zones());p.SaveBoard(str(dst),b);(dst.parent/'delta.json').write_text(json.dumps({'source':str(src),'candidate':str(dst),'removed_ids':removed,'new_ids':[t.m_Uuid.AsString() for t in added],'footprint_moves':moves,'clock_track_length_before_mm':oldlength,'clock_track_length_after_mm':sum(p.ToMM(t.GetLength()) for t in added)},indent=2));print(dst)
