#!/usr/bin/env python3
"""Build connected A1 drawings from the unchanged A0 circuit definitions."""
from __future__ import annotations
import json, shutil, argparse
from pathlib import Path
from redraw_engine import *
from redraw_core import build_core,build_gate
from redraw_power import build_dc,build_aux,build_brake
from redraw_interfaces import build_can,build_usb,build_spi
from redraw_analog import build_inverter,build_sensing,build_feedback

def overview(pages):
 # Navigable hierarchy arranged around the controller. Graphic arrows describe
 # system relationships; they do not add electrical nets to the circuit.
 p=Page('Overview','ShiroFOC A1 - connected schematic overview','A3')
 p.heading(12,12,'ShiroFOC - CONNECTED FUNCTIONAL SCHEMATIC')
 p.note(12,19,'A0 electrical circuit preserved | 18-42 V target | Prototype current / thermal limits remain applicable',1.143)
 # Keyed by the unchanged builder order. Titles sit inside boxes so a link
 # entering a top edge never crosses a sheet-name field.
 positions=[(15,35,54,22),(100,35,58,22),(135,85,70,65),
            (80,175,55,22),(155,175,55,22),(230,175,70,22),
            (260,35,55,22),(15,90,55,22),(15,130,55,22),
            (260,95,55,22),(180,35,55,22)]
 short=['DC link / input','5 V / 3.3 V power','MCU / clock / SWD',
        'Gate driver / VCC','Three-phase bridge','Current / temperature',
        'Brake chopper','SPI sensors','Feedback selection','CAN interface','USB service']
 notes=['VM, bulk capacitors, sensing','Battery / USB priority mux','STSPIN32G4',
        'Startup 8 V; firmware 10 V','Three identical power legs','Kelvin amplifiers + NTCs',
        'Independent OV backup','Encoder + IMU on one bus','ABI/Hall + VM isolation',
        'Protection + termination','USB-C / UART bridge']
 for i,(s,(x,y,w,h)) in enumerate(zip(pages,positions)):
  p.items.append(f'(sheet(at {fmt(x)} {fmt(y)})(size {fmt(w)} {fmt(h)})(stroke(width .254)(type default))(fill(color 0 0 0 0))(uuid {q(s.childid)}){field("Sheetname",short[i],x+w/2,y-3,True,size=1.5)}{field("Sheetfile",s.name+".kicad_sch",x+w/2,y+h+3,True)}(instances(project {q(PROJECT)}(path {q("/"+ROOTID)}(page {q(i+2)})))))')
  p.note(x+3,y+3,short[i],1.5)
  p.note(x+3,y+9,notes[i],1.016)
  p.note(x+3,y+h-5,f'Sheet {i+2}',1.016)
 p.note(140,113,'SPI3 / FDCAN / UART\nTimer feedback and ADC\nGate and brake control',1.143)
 def arrow(a,b):
  dx=b[0]-a[0];dy=b[1]-a[1]
  if dx:p.line((b[0]-(2 if dx>0 else -2),b[1]-1),b,(b[0]-(2 if dx>0 else -2),b[1]+1))
  else:p.line((b[0]-1,b[1]-(2 if dy>0 else -2)),b,(b[0]+1,b[1]-(2 if dy>0 else -2)))
 def link(points,label,at,both=False):
  p.line(*points);arrow(points[-2],points[-1])
  if both:arrow(points[1],points[0])
  if label:p.note(*at,label,1.016)
 # Short power-tree links. USB and brake are above their controller interfaces.
 link([(69,46),(100,46)],'VM',(77,41))
 link([(180,46),(158,46)],'USB 5 V',(161,40))
 link([(129,57),(129,73),(145,73),(145,85)],'3V3 control rail',(130,64))
 link([(207,57),(207,69),(180,69),(180,85)],'UART',(185,64),both=True)
 link([(195,85),(195,78),(280,78),(280,57)],'Brake PWM',(232,73))
 # VM has a separate outer route; it never passes through a signal sheet.
 link([(85,46),(85,27),(288,27),(288,35)],'VM',(245,22))
 p.line((85,46),(85,68),(10,68),(10,205),(182,205))
 p.note(13,62,'VM distribution',1.016)
 link([(10,170),(65,170),(65,186),(80,186)],'VM',(66,180))
 link([(182,205),(182,197)],'VM',(169,207))
 # Direct controller relationships: no link crosses an unrelated sheet box.
 link([(70,101),(135,101)],'SPI3',(94,96),both=True)
 link([(42,112),(42,130)],'ABI',(45,118))
 link([(70,141),(135,141)],'TIM4 / VM ADC',(85,135))
 link([(205,106),(260,106)],'FDCAN',(226,101),both=True)
 link([(145,150),(145,162),(107,162),(107,175)],'Driver control',(109,156))
 link([(135,186),(155,186)],'Gates',(139,180))
 link([(210,186),(230,186)],'Kelvin',(212,180))
 link([(265,175),(265,157),(195,157),(195,150)],'Current / NTC ADC',(216,151))
 link([(199,197),(199,214)],'Motor U/V/W',(202,207))
 p.note(15,157,'Open any sheet box to inspect its circuit.\nArrows show system relationships.\nShared power rails feed the interface sheets.',1.016)
 p.note(82,107,'4 x M3 / 3.2 mm NPTH',1.016)
 # Mechanical-only additions: no electrical pins, chassis or ground connection.
 # Preserve the official KiCad symbol definition for portable regeneration.
 mechanical = (Path(__file__).parent/'templates/mounting_hole_symbol.sexpr').read_text()
 for i,(x,y) in enumerate([(88,116),(116,116),(88,129),(116,129)],1):
  ref=f'H{i}'
  p.items.append(f'(symbol(lib_id "Mechanical:MountingHole")(at {fmt(x)} {fmt(y)} 0)(unit 1)(in_bom no)(on_board yes)(dnp no)(uuid {q(uid("mechanical/"+ref))}){field("Reference",ref,x,y-3)}{field("Value","M3 NPTH",x,y+3,size=1.016)}{field("Footprint","MountingHole:MountingHole_3.2mm_M3",x,y,True)}(instances(project {q(PROJECT)}(path {q("/"+ROOTID)}(reference {q(ref)})(unit 1)))))')
 p.note(12,222,'Layout: ../docs/PCB_LAYOUT_HANDOFF.md | Firmware: ../docs/FIRMWARE_BRINGUP_CONTRACT.md\nA0 electrical circuit retained; H1-H4 added for P1 mounting revision.',1.016)
 return f'(kicad_sch(version 20250114)(generator "eeschema")(uuid {q(ROOTID)})(paper "A3")(title_block(title "ShiroFOC - connected functional overview")(rev "P1-Mechanical")(date "2026-09-17"))(lib_symbols {mechanical}){"".join(p.items)}(sheet_instances(path "/"(page "1")))(embedded_fonts no))\n'

def main(output=None):
 pages=[build_dc(),build_aux(),build_core(),build_gate(),build_inverter(),build_sensing(),build_brake(),build_spi(),build_feedback(),build_can(),build_usb()]
 definitions={}
 for p in pages:
  for name,d in p.defs.items():
   if name not in definitions:definitions[name]={'name':d['name'],'ref':d['ref'],'units':{}}
   for u,v in d['units'].items():
    if u in definitions[name]['units']:assert definitions[name]['units'][u]==v,(name,u)
    definitions[name]['units'][u]=v
 # Physical pin coverage must be exact, including across STSPIN units.
 allpins=[]
 for p in pages:allpins+=list((r,n) for r,n,u in p.points)
 expected=set(NETS)
 assert set(allpins)==expected,f'Missing {sorted(expected-set(allpins))}; extras {set(allpins)-expected}'
 assert len(allpins)==len(set(allpins)),'Physical pins used in more than one unit'
 out=Path(output) if output else ROOT
 out.mkdir(parents=True,exist_ok=True);(out/'libs').mkdir(exist_ok=True);(out/'outputs').mkdir(exist_ok=True)
 # Preserve an archive outside generated files before the first replacement.
 if out==ROOT:
  arc=ROOT.parent/'review_baselines/A0_before_redraw/native'
  if not arc.exists():
   arc.mkdir(parents=True)
   for f in ROOT.glob('*.kicad_sch'):shutil.copy2(f,arc/f.name)
 for f in out.glob('*.kicad_sch'):f.unlink()
 # Power flags declare external/derived rails just as in A0; connect them to visible power symbols.
 flag_rails={0:['VM','GND'],1:['5V_BAT','5V_USB','5V_USB_RAW','5V_BOOT'],2:['VDDA','VREF+'],3:['VCC'],4:['BOOT1','BOOT2','BOOT3']}
 for idx,names in flag_rails.items():
  p=pages[idx]
  for j,net in enumerate(names):
   x=15+j*23;y=222 if p.paper=='A3' else 148;ref=f'#FLG{idx}{j}'
   if net=='5V_BOOT':x,y=p.p('U201',7)
   lib='FLAG';definitions[lib]={'name':'FLAG','ref':'#FLG','units':{1:{'pins':{'1':(0,0,'L','pwr','power_out',False,0)},'body':poly([(-1,0),(0,-1),(1,0),(0,1),(-1,0)]),'w':2,'h':2}}}
   p.defs[lib]=definitions[lib]
   p.items.append(f'(symbol(lib_id "ShiroFOC_Redraw:FLAG")(at {fmt(x)} {fmt(y)} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid {q(uid("redraw/"+ref))}){field("Reference",ref,x,y,True)}{field("Value","PWR_FLAG",x,y,True)}(instances(project {q(PROJECT)}(path {q("/"+ROOTID+"/"+p.childid)}(reference {q(ref)})(unit 1)))))')
   if net!='5V_BOOT':p.label(net,(x,y),'global')
 for p in pages:(out/(p.name+'.kicad_sch')).write_text(p.finalize(definitions))
 (out/'ShiroFOC_KiCad.kicad_sch').write_text(overview(pages))
 (out/'libs/ShiroFOC_Redraw.kicad_sym').write_text('(kicad_symbol_lib(version 20241209)(generator "kicad_symbol_editor")'+''.join(symbol_text(d) for d in definitions.values())+')\n')
 (out/'sym-lib-table').write_text('(sym_lib_table(lib(name "ShiroFOC_Redraw")(type "KiCad")(uri "${KIPRJMOD}/libs/ShiroFOC_Redraw.kicad_sym")(options "")(descr "Functional schematic symbols with complete A0 pin mapping")))\n')
 (out/'fp-lib-table').write_text((ROOT/'fp-lib-table').read_text())
 if out!=ROOT:shutil.copytree(ROOT/'libs/ShiroFOC.pretty',out/'libs/ShiroFOC.pretty',dirs_exist_ok=True)
 settings=json.loads((ROOT/'ShiroFOC_KiCad.kicad_pro').read_text());settings['sheets']=[[ROOTID,'Root']]+[[p.childid,p.title] for p in pages]
 (out/'ShiroFOC_KiCad.kicad_pro').write_text(json.dumps(settings,indent=2)+'\n')
 (out/'outputs/source_connectivity.json').write_text((ROOT.parent/'review_baselines/A0_before_redraw/source_connectivity.json').read_text())
 (out/'outputs/redraw_layout.json').write_text(json.dumps({'sheets':[{'name':p.name,'title':p.title,'paper':p.paper,'references':sorted(p.used),'global_ports':sum(k=='global' for n,pt,k,sd in p.labels),'wire_segments':len(p.wires)} for p in pages]},indent=2)+'\n')
 print(f'Generated {len(pages)+1} connected sheets, {len(PARTS)} physical components, {len(allpins)} physical pins')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--output');ns=a.parse_args();main(ns.output)
