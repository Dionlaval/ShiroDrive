from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parent;s=r/'ntc_imu_removed/ShiroFOC_Manual.kicad_pcb';d=r/'ntc_r712_prepare/ShiroFOC_Manual.kicad_pcb';d.parent.mkdir(exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(s.with_suffix(ext),d.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(s.parent/name,d.parent/name)
if not(d.parent/'libs').exists():(d.parent/'libs').symlink_to((s.parent/'libs').resolve(),target_is_directory=True)
b=p.LoadBoard(str(s));f=next(f for f in b.GetFootprints()if f.GetReference()=='R712');old=f.GetPosition();oldp=[old.x,old.y];a=f.GetOrientationDegrees();f.SetPosition(p.VECTOR2I(old.x+p.FromMM(.6),old.y));new=f.GetPosition();move=dict(uuid=f.m_Uuid.AsString(),reference=f.GetReference(),old=dict(position_nm=oldp,angle_deg=a),new=dict(position_nm=[new.x,new.y],angle_deg=a));oldtrack=next(t for t in b.GetTracks()if t.m_Uuid.AsString()=='34e073c2-06ac-469d-91f3-62152d68166e');q=oldtrack.Duplicate();q.SetStart(p.VECTOR2I(p.FromMM(-13.91),p.FromMM(-.5)));b.Add(q);b.Remove(oldtrack);(d.parent/'r712_changes.json').write_text(json.dumps(dict(footprint_moves=[move],removed_ids=[oldtrack.m_Uuid.AsString()],new_ids=[q.m_Uuid.AsString()]),indent=2));p.SaveBoard(str(d),b)
