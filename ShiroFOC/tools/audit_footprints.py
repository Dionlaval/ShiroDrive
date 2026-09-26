#!/usr/bin/env python3
"""Run with KiCad's Python interpreter to exercise its actual footprint loader."""
import csv, json, sys, os
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[1]/'ShiroFOC_KiCad'
FP=Path(os.environ.get('KICAD9_FOOTPRINT_DIR','/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'))
source=json.loads((ROOT/'outputs/source_connectivity.json').read_text())
rows=[];problems=[]
for ref,comp in sorted(source.items()):
 lib,name=comp['footprint'].split(':')
 library=ROOT/'libs/ShiroFOC.pretty' if lib=='ShiroFOC_Footprints' else FP/(lib+'.pretty')
 footprint=pcbnew.FootprintLoad(str(library),name)
 if footprint is None:
  problems.append(f'{ref}: failed to load {comp["footprint"]}');continue
 pads=list(footprint.Pads())
 numbers={p.GetNumber() for p in pads if p.GetNumber()}
 expected=set(comp['pins'])
 missing=expected-numbers
 extras=numbers-expected-{'MP','SH'}
 if missing or extras:problems.append(f'{ref}: missing {sorted(missing)}, unexpected {sorted(extras)}')
 for pad in pads:
  n=pad.GetNumber();pos=pad.GetPosition();sz=pad.GetSize()
  rows.append({'Reference':ref,'Footprint':comp['footprint'],'Pad':n,
   'Net':comp['pins'].get(n) or ('NC' if n in expected else 'MECHANICAL/PASTE'),
   'X_mm':pcbnew.ToMM(pos.x),'Y_mm':pcbnew.ToMM(pos.y),'Width_mm':pcbnew.ToMM(sz.x),'Height_mm':pcbnew.ToMM(sz.y)})
# Manufacturer drawing based, independent orientation sentinels.
expected_geometry={
 'CSD88599Q5DC_DMM0022A':{'1':(-2.35,-2.5),'11':(-2.35,2.5),'12':(2.35,2.5),'22':(2.35,-2.5)},
 'CSD19531Q5A_Q5A_DQJ0008A':{'1':(2.7525,1.905),'4':(2.7525,-1.905),'8':(-2.8,1.905)},
 'Texas_DYD0005A_SOT23-5':{'1':(-1.3,-.95),'3':(-1.3,.95),'4':(1.3,.95),'5':(1.3,-.95)},
}
for name,pins in expected_geometry.items():
 f=pcbnew.FootprintLoad(str(ROOT/'libs/ShiroFOC.pretty'),name)
 for number,(x,y) in pins.items():
  assert any(p.GetNumber()==number and abs(pcbnew.ToMM(p.GetPosition().x)-x)<1e-5 and abs(pcbnew.ToMM(p.GetPosition().y)-y)<1e-5 for p in f.Pads()),(name,number)
with (ROOT/'outputs/footprint_pad_audit.csv').open('w',newline='') as h:
 w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
report={'kicad':pcbnew.GetBuildVersion(),'components':len(source),'unique_footprints':len({v['footprint'] for v in source.values()}),'pads_and_apertures':len(rows),'problems':problems}
(ROOT/'outputs/footprint_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
sys.exit(bool(problems))
