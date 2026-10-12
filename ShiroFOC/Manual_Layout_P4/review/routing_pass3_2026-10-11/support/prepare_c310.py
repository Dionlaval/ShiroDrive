from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parents[1];s=r/'support/current_fullimu_prepare/ShiroFOC_Manual.kicad_pcb';d=r/'support/c310_prepare/ShiroFOC_Manual.kicad_pcb';d.parent.mkdir(exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(s.with_suffix(ext),d.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(s.parent/name,d.parent/name)
if not(d.parent/'libs').exists():(d.parent/'libs').symlink_to((s.parent/'libs').resolve(),target_is_directory=True)
b=p.LoadBoard(str(s));ret=[];removed=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() in ['628de718-7888-4c07-afdb-ac2d2ebd1fa0','7a5414be-6896-4532-8206-ed422527ff06','f6d6e2e4-dbe9-4f49-a216-421fc152ac28','48c3f2f8-bf20-4f0d-a01a-9cb17d46382f','713719c8-4669-42bc-ae7a-c30e8a8e67ca']:
  removed.append(t.m_Uuid.AsString());ret.append(t);b.Remove(t)
f=next(f for f in b.GetFootprints()if f.GetReference()=='C310');pos=f.GetPosition();op=[pos.x,pos.y];oa=f.GetOrientationDegrees();gp=next(q for q in f.Pads()if q.GetNetname()=='GND');groundpos=p.VECTOR2I(gp.GetPosition());f.SetOrientationDegrees(oa+180);newgp=gp.GetPosition();f.SetPosition(p.VECTOR2I(pos.x+groundpos.x-newgp.x,pos.y+groundpos.y-newgp.y));np=f.GetPosition();move=dict(uuid=f.m_Uuid.AsString(),reference=f.GetReference(),old=dict(position_nm=op,angle_deg=oa),new=dict(position_nm=[np.x,np.y],angle_deg=f.GetOrientationDegrees()));print(move)
net=next(n for n in b.GetNetInfo().NetsByNetcode().values()if n.GetNetname()=='/MCU / clock / SWD/NRST');added=[]
paths=[[(-9.602137,6.8928),(-11.1053,6.8928),(-12.5,8.2875),(-12.5,8.85),(-11.98,9.37),(-11.835,9.37)],[(-11.835,9.37),(-12.75,10.285),(-12.75,10.54)]]
for path in paths:
 for a,c in zip(path,path[1:]):
  t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));t.SetEnd(p.VECTOR2I(p.FromMM(c[0]),p.FromMM(c[1])));t.SetWidth(p.FromMM(.1524));t.SetLayer(p.F_Cu);t.SetNet(net);b.Add(t);ret.append(t);added.append(t.m_Uuid.AsString())
(d.parent/'changes.json').write_text(json.dumps(dict(footprint_moves=[move],removed_ids=removed,new_ids=added),indent=2));p.SaveBoard(str(d),b)
