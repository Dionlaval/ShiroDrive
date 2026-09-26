#!/usr/bin/env python3
"""Apply documented P0 rule defaults without changing schematic settings."""
import json,re,copy
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'ShiroFOC_KiCad';out=root/'outputs/placement'
p=root/'ShiroFOC_KiCad.kicad_pro';backup=out/'project_before_placement.json'
if not backup.exists():backup.write_text(p.read_text())
j=json.loads(p.read_text());d=j['board']['design_settings'];rules=d.setdefault('rules',{})
rules.update(min_clearance=.15,min_track_width=.15,min_connection=.15,min_via_diameter=.45,min_through_hole_diameter=.20,min_via_annular_width=.1,min_hole_to_hole=.20,min_copper_edge_clearance=.50,min_hole_clearance=.25,min_silk_clearance=.20,min_text_height=1.0,min_text_thickness=.15,solder_mask_clearance=.05,solder_mask_min_width=.10)
d['track_widths']=[0,.15,.20,.25,.4,.5,1,2,3]
d['via_dimensions']=[{'diameter':.6,'drill':.3},{'diameter':.45,'drill':.2}]
base=j['net_settings']['classes'][0];base.update(track_width=.25,clearance=.2)
classes=[base];patterns=[]
for name,width,clear,patterns_in in [('Analog',.2,.2,['*SHUNT_*_SENSE_*','*OPP_*','*OPN_*','OPO_*','VREF+','VDDA','VBUS_SENSE','NTC_*']),('Gate',.4,.2,['GHS*','GLS*','Net-(Q40*-G*)']),('LogicPower',.5,.2,['3V3','5V*','VCC']),('Power',2,.5,['VM','OUT*','BOOT*','*SHUNT_*_FORCE_P','Net-(D504-A)']),('USB',.2,.2,['*USB_D*'])]:
 c=copy.deepcopy(base);c.update(name=name,track_width=width,clearance=clear,priority=len(classes));classes.append(c)
 for pat in patterns_in:patterns.append({'netclass':name,'pattern':pat})
j['net_settings']['classes']=classes;j['net_settings']['netclass_patterns']=patterns
p.write_text(json.dumps(j,indent=2)+'\n')
# Package-internal clearances retain the 0.15 mm manufacturing floor while
# the 0.50 mm Power class governs open-board routing. No violation exclusions.
custom = ['(version 1)', '(rule "Component pad drill separation" (condition "A.Type == \'Pad\' || B.Type == \'Pad\'") (constraint hole_to_hole (min 0.45mm)))']
custom.append("(rule \"U901 thermal-via drill web\" (condition \"A.memberOfFootprint('U901') && B.memberOfFootprint('U901') && A.Pad_Number == '21' && B.Pad_Number == '21'\") (constraint hole_to_hole (min 0.20mm)))")
for ref in ['Q401','Q402','Q403','U301','U201','C415','C425','C435']:
 custom.append(f"(rule \"{ref} package internal copper\" (condition \"A.memberOfFootprint('{ref}') && B.memberOfFootprint('{ref}')\") (constraint clearance (min 0.15mm)))")
for q,c in [('Q401','C415'),('Q402','C425'),('Q403','C435')]:
 custom.append(f"(rule \"{q} local package bypass\" (condition \"(A.memberOfFootprint('{q}') && B.memberOfFootprint('{c}')) || (A.memberOfFootprint('{c}') && B.memberOfFootprint('{q}'))\") (constraint clearance (min 0.20mm)))")
(root/'ShiroFOC_KiCad.kicad_dru').write_text('\n'.join(custom)+'\n')
# pcbnew does not expose stackup editing in this KiCad build. Insert native data.
f=root/'ShiroFOC_KiCad.kicad_pcb';s=f.read_text()
stack='''
 (stackup
  (layer "F.SilkS" (type "Top Silk Screen"))
  (layer "F.Paste" (type "Top Solder Paste"))
  (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
  (layer "F.Cu" (type "copper") (thickness 0.07))
  (layer "dielectric 1" (type "prepreg") (thickness 0.18) (material "FR4") (epsilon_r 4.3) (loss_tangent 0.02))
  (layer "In1.Cu" (type "copper") (thickness 0.0175))
  (layer "dielectric 2" (type "core") (thickness 1.065) (material "FR4") (epsilon_r 4.3) (loss_tangent 0.02))
  (layer "In2.Cu" (type "copper") (thickness 0.0175))
  (layer "dielectric 3" (type "prepreg") (thickness 0.18) (material "FR4") (epsilon_r 4.3) (loss_tangent 0.02))
  (layer "B.Cu" (type "copper") (thickness 0.07))
  (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
  (layer "B.Paste" (type "Bottom Solder Paste"))
  (layer "B.SilkS" (type "Bottom Silk Screen"))
  (copper_finish "None")
  (dielectric_constraints no)
 )'''
# 1.6 mm copper + dielectric, excluding soldermask; provisional dielectric model.
if '(stackup' not in s:s=s.replace('(setup','(setup'+stack,1)
f.write_text(s)
print('Saved 4-layer stack model and placement DRC defaults. Dielectrics remain provisional; USB dimensions not approved.')
