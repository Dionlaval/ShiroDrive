from pathlib import Path
import subprocess,shutil,json,sys
R=Path(__file__).resolve().parent;src=R/sys.argv[1]/'ShiroFOC_Manual.kicad_pcb';dst=R/sys.argv[2]/src.name
P='/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3';C='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
dst.parent.mkdir(exist_ok=True)
for fn in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/fn,dst.parent/fn)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
subprocess.run([P,str(R/'ground/add_ground_stitches.py'),str(src),str(dst),*sys.argv[3:]],check=True)
f=dst.with_suffix('.ground_manifest.json');d=json.loads(f.read_text())
for row in d['groups']:row['new_items']=row['added_uuids']
f.write_text(json.dumps(d,indent=2))
subprocess.run([P,str(R.parent/'ntc_placement_2026-10-11/refill_board.py'),str(dst)],check=True)
subprocess.run([C,'pcb','drc','--format','json','--output',str(dst.parent/'drc.json'),str(dst)],check=True)
subprocess.run([P,str(R/'validation/validate_routing.py'),'--baseline',str(R/'before/ShiroFOC_Manual.kicad_pcb'),'--candidate',str(dst),'--baseline-drc',str(R/'before/drc.json'),'--candidate-drc',str(dst.parent/'drc.json'),'--output',str(dst.parent/'validation.json')],check=False)
