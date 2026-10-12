from pathlib import Path
import json,shutil,subprocess
import pcbnew as p
R=Path(__file__).resolve().parent;src=R/'optimized/ShiroFOC_Manual.kicad_pcb';d=R/'ntc_base';d.mkdir(exist_ok=True)
m=json.loads((R/'mux/ShiroFOC_Manual.routes.json').read_text());rows=[x for x in m['connections']if x['net']=='/Current / temperature/NTC_A_RAW'and x['length_mm']>5 and x['new_items']];assert len(rows)==1
remove=set(rows[0]['new_items']);b=p.LoadBoard(str(src));items=[t for t in b.GetTracks()if t.m_Uuid.AsString()in remove];assert len(items)==len(remove)
for t in items:b.Remove(t)
p.SaveBoard(str(d/src.name),b)
for fn in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table','drc.json']:shutil.copy2(src.parent/fn,d/fn)
if not(d/'libs').exists():(d/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
(d/'removed_ntc_route.json').write_text(json.dumps(rows,indent=2))
P='/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3';C='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli';dst=R/'signal_final/ShiroFOC_Manual.kicad_pcb'
subprocess.run([P,str(R/'engine/route_p4.py'),str(d/src.name),str(d/'drc.json'),str(dst),'/Current / temperature/NTC_A_RAW','--layers','F,B,L3','--width','.1524','--max-length','37','--max-vias','3','--via-cost','2200','--step','.025'],check=True)
subprocess.run([C,'pcb','drc','--format','json','--output',str(dst.parent/'drc.json'),str(dst)],check=True)
subprocess.run([P,str(R/'validation/validate_routing.py'),'--baseline',str(R/'before/ShiroFOC_Manual.kicad_pcb'),'--candidate',str(dst),'--baseline-drc',str(R/'before/drc.json'),'--candidate-drc',str(dst.parent/'drc.json'),'--output',str(dst.parent/'validation.json')],check=False)
