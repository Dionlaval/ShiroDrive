#!/usr/bin/env python3
"""Rebuild and validate the A1 drawing with KiCad; refresh hashes on success.

Requires Python 3.12+, KiCad 9 CLI, and a Python interpreter with pcbnew.
Set KICAD_CLI / KICAD_PYTHON / KICAD9_FOOTPRINT_DIR for another installation.
The final PDF must also be visually reviewed; automation cannot approve that.
"""
import hashlib, json, os, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'ShiroFOC_KiCad'; O=P/'outputs'; SCH=P/'ShiroFOC_KiCad.kicad_sch'
CLI=os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
KP=os.environ.get('KICAD_PYTHON') or '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9'
def run(args):
 result=subprocess.run([str(a) for a in args],cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},text=True,capture_output=True)
 if result.returncode:
  raise RuntimeError(f'{args}\n{result.stdout}\n{result.stderr}')
 print(result.stdout.strip())
def manifest():
 paths=list(P.glob('*.kicad_sch'))+list(P.glob('*.kicad_pro'))+list(P.glob('*-lib-table'))
 paths+=list((P/'libs').rglob('*.kicad_mod'))+list((P/'libs').glob('*.kicad_sym'))
 paths+=list((ROOT/'tools').glob('*.py'))+list(ROOT.glob('*.md'))+list((ROOT/'docs').rglob('*.md'))+[P/'README.md']
 paths+=list((ROOT/'DataSheets').glob('*.pdf'))
 paths+=list((ROOT/'review_baselines/A0_before_redraw').glob('*.*'))
 paths += [p for p in O.iterdir() if p.is_file() and p.name!='release_manifest.json']
 visual=json.loads((O/'visual_review.json').read_text()) if (O/'visual_review.json').exists() else {}
 visual_ok=visual.get('status')=='PASS' and visual.get('pdf_sha256')==hashlib.sha256((O/'ShiroFOC_Rev_A_Schematic.pdf').read_bytes()).hexdigest()
 data={'revision':'A1-Drawing','status':'LAYOUT_RELEASE' if visual_ok else 'MACHINE_CHECKS_PASS_VISUAL_REVIEW_PENDING','generated_utc':datetime.now(timezone.utc).isoformat(),'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))},'note':'A0 electrical circuit, redrawn with functional wiring. Machine checks plus visual_review.json record release evidence. Rebuild invalidates prior visual review if the PDF hash changes.'}
 (O/'release_manifest.json').write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':
 O.mkdir(exist_ok=True)
 if '--manifest-only' in sys.argv:
  run([sys.executable,ROOT/'tools/validate_rev_a.py'])
  visual=json.loads((O/'visual_review.json').read_text())
  assert visual['status']=='PASS' and visual['pdf_sha256']==hashlib.sha256((O/'ShiroFOC_Rev_A_Schematic.pdf').read_bytes()).hexdigest(), 'Visual review is absent or stale'
  manifest();sys.exit()
 (O/'release_manifest.json').unlink(missing_ok=True)
 run([sys.executable,ROOT/'tools/native_rev_a.py'])
 run([CLI,'sch','erc','--format','json','--severity-all','--exit-code-violations','-o',O/'erc_rev_a.json',SCH])
 run([CLI,'sch','export','netlist','--format','kicadxml','-o',O/'ShiroFOC_Rev_A.net',SCH])
 fields='Reference,Value,Footprint,MPN,Assembly,Rating,Procurement,Datasheet,${DNP}'
 labels='Reference,Value,Footprint,MPN,Assembly,Rating,Procurement,Datasheet,DNP'
 run([CLI,'sch','export','bom','--fields',fields,'--labels',labels,'-o',O/'ShiroFOC_Rev_A_BOM.csv',SCH])
 run([CLI,'sch','export','pdf','-o',O/'ShiroFOC_Rev_A_Schematic.pdf',SCH])
 run([KP,ROOT/'tools/audit_footprints.py'])
 run([sys.executable,ROOT/'tools/validate_rev_a.py'])
 manifest()
