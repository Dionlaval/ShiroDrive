from pathlib import Path
import shutil,json
import pcbnew as p
root=Path(__file__).resolve().parents[1]; src=root/'before/ShiroFOC_Manual.kicad_pcb';dst=root/'support/ov2_prepare/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
for name in ['libs']:
 if not (dst.parent/name).exists():(dst.parent/name).symlink_to((src.parent/name).resolve(),target_is_directory=True)
b=p.LoadBoard(str(src));moves=[]
for f in b.GetFootprints():
 if f.GetReference() in ('R208','R209'):
  pos=f.GetPosition();a=f.GetOrientationDegrees();old=[pos.x,pos.y];f.SetPosition(p.VECTOR2I(pos.x-p.FromMM(.45),pos.y));new=f.GetPosition();moves.append(dict(uuid=f.m_Uuid.AsString(),reference=f.GetReference(),old=dict(position_nm=old,angle_deg=a),new=dict(position_nm=[new.x,new.y],angle_deg=a)))
removed=[]
for t in list(b.GetTracks()):
 if t.GetNetname()=='Net-(U203-CP2)':removed.append(t.m_Uuid.AsString());b.Remove(t)
p.SaveBoard(str(dst),b)
(dst.parent/'changes.json').write_text(json.dumps(dict(footprint_moves=moves,allowed_replacement_uuids=removed),indent=2))
print(dst, len(removed),moves)
