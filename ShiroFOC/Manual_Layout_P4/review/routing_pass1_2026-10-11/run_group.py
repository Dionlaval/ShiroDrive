from pathlib import Path
import subprocess,sys,json,shutil
R=Path(__file__).resolve().parent
PYTHON='/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3'
CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
group,srcdir,dstdir=sys.argv[1:4]
src=R/srcdir/'ShiroFOC_Manual.kicad_pcb';dst=R/dstdir/'ShiroFOC_Manual.kicad_pcb'
nets=json.loads((R/'planned_groups.json').read_text())[group]
cmd=[PYTHON,str(R/'engine/route_p4.py'),str(src),str(src.parent/'drc.json'),str(dst),*nets,*sys.argv[4:]]
subprocess.run(cmd,check=True)
subprocess.run([CLI,'pcb','drc','--format','json','--output',str(dst.parent/'drc.json'),str(dst)],check=True)
subprocess.run([PYTHON,str(R/'validation/validate_routing.py'),'--baseline',str(R/'before/ShiroFOC_Manual.kicad_pcb'),'--candidate',str(dst),'--baseline-drc',str(R/'before/drc.json'),'--candidate-drc',str(dst.parent/'drc.json'),'--output',str(dst.parent/'validation.json')],check=False)
d=json.loads((dst.parent/'validation.json').read_text())
print(json.dumps({k:d[k]for k in ['status','failures','new_routing_by_layer','baseline_drc','candidate_drc']},indent=2),flush=True)
