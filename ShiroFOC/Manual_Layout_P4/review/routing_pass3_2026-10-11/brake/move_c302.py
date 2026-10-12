from pathlib import Path
import pcbnew as p,shutil,json
r=Path(__file__).resolve().parent.parent;src=r/'brake/imu2_bow/ShiroFOC_Manual.kicad_pcb';dst=r/'brake/c302_shift/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
b=p.LoadBoard(str(src));fs=list(b.GetFootprints());f=next(f for f in fs if f.GetReference()=='C302');pos=f.GetPosition();move={'uuid':f.m_Uuid.AsString(),'reference':'C302','old':{'position_nm':[pos.x,pos.y],'angle_deg':f.GetOrientationDegrees()},'new':{'position_nm':[pos.x-400000,pos.y],'angle_deg':f.GetOrientationDegrees()}};f.SetPosition(p.VECTOR2I(*move['new']['position_nm']));b.BuildConnectivity();p.SaveBoard(str(dst),b)
ms=json.loads((r/'brake/r313_moves.json').read_text());ms['footprint_moves'].append(move);(r/'brake/moves.json').write_text(json.dumps(ms,indent=2)+'\n')
