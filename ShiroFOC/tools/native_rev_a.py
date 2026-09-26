#!/usr/bin/env python3
"""Native KiCad 9 serializer. UUIDs are stable across rebuilds; no GUI conversion."""
from __future__ import annotations
import json, re, uuid
from pathlib import Path
import generate_rev_a as g

NS=uuid.UUID('a8db7f90-dd1f-49cb-a2af-b5e27c2426a1')
PROJECT='ShiroFOC_KiCad'
ROOTID=str(uuid.uuid5(NS,PROJECT))
def uid(key): return str(uuid.uuid5(NS,str(key)))
def q(s): return json.dumps(str(s),ensure_ascii=False)
def mm(v): return f'{v*.0254:.5f}'.rstrip('0').rstrip('.') or '0'
def prop(name,value,x,y,hide=False,size=1.27):
 return f'(property {q(name)} {q(value)} (at {x} {y} 0) (effects (font (size {size} {size})){" (hide yes)" if hide else ""}))'
def effects(size=1.27,justify=''):
 return f'(effects (font (size {size} {size})){(" (justify "+justify+")") if justify else ""})'
def line(x1,y1,x2,y2,width=.254):
 return f'(polyline (pts (xy {x1} {y1})(xy {x2} {y2})) (stroke (width {width})(type default))(fill (type none)))'
def symbol_text(s,libid=None):
 body=[]
 if s.name in ('CAPACITOR','CAP_POL'):
  body=[line(-3.81,0,-1.27,0),line(1.27,0,3.81,0),line(-1.27,-2.54,-1.27,2.54),line(1.27,-2.54,1.27,2.54)]
  if s.name=='CAP_POL':body += [line(-3.8,2.54,-2.3,2.54),line(-3.05,1.8,-3.05,3.3)]
 elif s.name in ('DIODE','LED'):
  body=[line(-3.81,0,-1.27,0),line(1.27,0,3.81,0),line(-1.27,-2.54,-1.27,2.54),f'(polyline (pts (xy -1.27 0)(xy 1.27 2.54)(xy 1.27 -2.54)(xy -1.27 0))(stroke(width .254)(type default))(fill(type none)))']
  if s.name=='LED':body +=[line(1,3,3,5),line(2,2.5,4,4.5)]
 elif s.name=='SWITCH': body=[line(-3.81,0,-1.5,0),line(1.5,0,3.81,0),line(-1.5,0,1.5,2.54)]
 elif s.name=='INDUCTOR':
  body=[f'(arc (start {x} 0)(mid {x+.9525} 1.5)(end {x+1.905} 0)(stroke(width .254)(type default))(fill(type none)))' for x in (-3.81,-1.905,0,1.905)]
 elif s.name=='TESTPOINT':body=[f'(circle (center 0 0)(radius 1.5)(stroke(width .254)(type default))(fill(type none)))',line(-2.54,0,-1.5,0)]
 else:body=[f'(rectangle (start {mm(-s.width/2)} {mm(s.height/2)})(end {mm(s.width/2)} {mm(-s.height/2)})(stroke(width .254)(type default))(fill(type background)))']
 pins=[]
 types={'P':'passive','I':'input','O':'output','B':'bidirectional','T':'tri_state','W':'power_in','w':'power_out','N':'no_connect','C':'open_collector'}
 for p in s.pins:
  angle={'R':0,'L':180,'U':90,'D':270}[p.orient]
  pins.append(f'(pin {types[p.etype]} line (at {mm(p.x)} {mm(p.y)} {angle})(length {mm(p.length)}){ " (hide yes)" if not p.visible else ""}(name {q(p.name)} {effects(1.016)})(number {q(p.number)} {effects(.889)}))')
 return f'''(symbol {q(libid or s.name)} (pin_names (offset 1.016)){" (pin_numbers hide)" if s.name in ('RESISTOR','CAPACITOR','INDUCTOR') else ""} (in_bom yes)(on_board yes)
 {prop('Reference',s.ref,0,mm(s.height/2+180))}
 {prop('Value',s.name,0,mm(-s.height/2-180))}
 (symbol {q(s.name+'_0_1')} {''.join(body)})
 (symbol {q(s.name+'_1_1')} {''.join(pins)}))'''

def assign_types():
 maps={
 'STSPIN32G4':{'W':[1,2,26,27,32,35,38,41,61,63,64,65],'w':[62],'O':[29,30,31,37,40,43,15,19,24,28,4,11,21,45,48,51,53,54,56,60], 'I':[9,10,12,13,14,16,17,18,20,22,23,25,46,47,50,52,55,57,58,59],'B':[3,5,6,7,8,44,49],'N':[33,34]},
 'LMR36510FADDA':{'W':[1,2,9,7],'w':[8,6],'I':[3,5],'C':[4]},
 'TPS2121RUXR':{'W':[2,7,12],'w':[1],'I':[3,4,5,6,10],'C':[9]},
 'TLV75533PDYDR':{'W':[1,2],'w':[5],'I':[3],'N':[4]},
 'UCC27517ADBVR':{'W':[1,2],'I':[3,4],'O':[5]},
 'TLV3012BIDBVR':{'W':[2,6],'I':[3,4],'O':[1,5]},
 'AS5047P':{'W':[11,12,13],'I':[1,2,4,5],'T':[3],'O':[6,7,8,9,10,14]},
 'BMI323':{'W':[5,6,7,8],'I':[12,13,14],'T':[1],'O':[4,9],'N':[2,3,10,11]},
 'TMUX1574PW':{'W':[8,16],'I':[1,15]},
 'TCAN3413DR':{'W':[2,3,5],'I':[1,8],'O':[4],'B':[6,7]},
 'CP2102N-A02-GQFN20':{'W':[3,6,7,12,21],'I':[8,13,15,17],'O':[11,14,16,18],'B':[1,2,4,5,9,19,20],'N':[10]},
 'CSD19531Q5A':{'I':[4]},'CSD88599Q5DC':{'I':[1,22],'N':[21,23,24,25,26]},
 }
 for name,classes in maps.items():
  for typ,nums in classes.items():
   for p in g.SYMS[name].pins:
    if int(p.number) in nums:p.etype=typ
 for sym in (g.DIODE,g.LED):
  sym.pins[0].name='K';sym.pins[1].name='A'
 for sym in (g.RES,g.CAP,g.IND,g.SW):
  for p in sym.pins:p.name='~'

# Groups remain at the architecture's positions with added space between blocks.
SX=1.35; SY=1.30

def build_sheet(s,index):
 sid=uid(s.filename); childid=uid('child/'+s.filename)
 used={c.sym.name:c.sym for c in s.components}
 # Polarized bulk capacitors have visible positive terminals.
 for c in s.components:
  if c.ref in ('C101','C102','C103'):
   c.sym=g.Symbol('CAP_POL','C',300,200,[g.Pin('+','1',-350,0,200,'R'),g.Pin('-','2',350,0,200,'L')]);used[c.sym.name]=c.sym
 items=[]
 for c in s.components:
  x=round(c.x*SX/50)*50;y=round(c.y*SY/50)*50
  if c.ref.startswith("TP10"): x+=800
  # Keep CP2102 body clear of power capacitors after adding all physical pins.
  cid=uid(c.ref)
  fields={'Reference':c.ref,'Value':c.value,'Footprint':c.footprint,'Datasheet':c.datasheet,**c.fields}
  fields.setdefault('Assembly','FIT')
  if c.ref.startswith(('TP','JP')):fields.setdefault('MPN','PCB feature')
  if not fields.get('MPN'):
   fields['MPN']=''
   fields['Procurement']='Select to specification: '+c.value+'; '+c.footprint.split(':')[-1]
  fields.setdefault('Rating','See Value; generic low-voltage passives: R >=0.1 W / 50 V, C >=16 V X7R unless specified')
  parts=[]
  for name,val in fields.items():
   fy=y-c.sym.height//2-180 if name=='Reference' else y+max(c.sym.height//2,max(-p.y for p in c.sym.pins))+200 if name=='Value' else y
   parts.append(prop(name,val,mm(x),mm(fy),name not in ('Reference','Value'),1.27 if name!='Value' else 1.143))
  # Every pin is either connected or explicitly NC. Missing package pins are a failure.
  for pin in c.sym.pins:
   key=(c.ref,pin.number)
   assert key in s.connections or key in s.no_connects, f'Unspecified pin {key}'
   px=x+pin.x;py=y-pin.y
   if key in s.no_connects:
    items.append(f'(no_connect(at {mm(px)} {mm(py)})(uuid {q(uid(str(key)+"/nc"))}))')
   else:
    net=s.connections[key]
    # A short visible wire makes the electrical attachment unambiguous.
    dx=-100 if pin.orient=='R' else 100 if pin.orient=='L' else 0
    dy=100 if pin.orient=='U' else -100 if pin.orient=='D' else 0
    ex=px+dx;ey=py+dy
    items.append(f'(wire(pts(xy {mm(px)} {mm(py)})(xy {mm(ex)} {mm(ey)}))(stroke(width 0)(type default))(uuid {q(uid(str(key)+"/wire"))}))')
    angle=0 if pin.orient=='R' else 180 if pin.orient=='L' else 90
    just='right' if angle==0 else 'left'
    items.append(f'(global_label {q(net)} (shape bidirectional)(at {mm(ex)} {mm(ey)} {angle}){effects(1.016,just)}(uuid {q(uid(str(key)+"/label"))}))')
  items.append(f'''(symbol(lib_id {q('ShiroFOC_KiCad:'+c.sym.name)})(at {mm(x)} {mm(y)} 0)(unit 1)(in_bom yes)(on_board yes)(dnp {'yes' if fields['Assembly']=='DNP' else 'no'})(uuid {q(cid)})
  {''.join(parts)}
  (instances(project {q(PROJECT)}(path {q('/'+ROOTID+'/'+childid)}(reference {q(c.ref)})(unit 1)))))''')
 for i,note in enumerate(s.items):
  m=re.match(r'Text Notes (\d+) (\d+) 0\s+(\d+).*?\n(.*)',note,re.S)
  if not m:continue
  nx,ny,size=map(int,m.group(1,2,3));text=m.group(4)
  if ny < 600: ny=850/SY
  # Notes wrap predictably into a readable width.
  import textwrap
  text='\n'.join(textwrap.wrap(text,155,break_long_words=False))
  items.append(f'(text {q(text)} (at {mm(nx*SX)} {mm(ny*SY)} 0){effects(mm(size),'left bottom')}(uuid {q(uid(s.filename+"/note/"+str(i)))}))')
 # Power flags are explicit boundary/source declarations, not silent ERC exclusions.
 flags={1:['VM','GND'],2:['5V_BAT','5V_USB_RAW','5V_USB','5V_BOOT'],3:['VCC','VDDA','VREF+','BOOT1','BOOT2','BOOT3']}.get(index,[])
 if flags:
  flag=g.Symbol('POWER_FLAG','#FLG',100,100,[g.Pin('pwr','1',0,0,0,'R',etype='w')]);used[flag.name]=flag
  for k,net in enumerate(flags):
   x=2000+k*2000;y=14700;ref=f'#FLG{index}{k}'
   items.append(f'(symbol(lib_id "ShiroFOC_KiCad:POWER_FLAG")(at {mm(x)} {mm(y)} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid {q(uid(ref))}){prop("Reference",ref,mm(x),mm(y),True)}{prop("Value","POWER_FLAG",mm(x),mm(y),True)}(instances(project {q(PROJECT)}(path {q("/"+ROOTID+"/"+childid)}(reference {q(ref)})(unit 1)))))')
   items.append(f'(global_label {q(net)}(shape bidirectional)(at {mm(x)} {mm(y)} 0){effects(1.016,"right")}(uuid {q(uid(ref+"label"))}))')
  items.append(f'(text "ERC sources: connector input / passive-filtered regulator outputs / internal bootstrap supplies."(at 20 381 0){effects(1.27,"left")}(uuid {q(uid(s.filename+"flagsnote"))}))')
 title=f'(title_block(title {q(s.title)})(date "2026-09-15")(rev "A0")(company "ShiroFOC")(comment 1 "PCB layout release; prototype ratings require hardware validation")(comment 2 "GND is common; preserve Kelvin and power-return routing"))'
 return f'(kicad_sch(version 20250114)(generator "eeschema")(uuid {q(sid)})(paper "A2"){title}(lib_symbols {"".join(symbol_text(sym,"ShiroFOC_KiCad:"+sym.name) for sym in used.values())}){"".join(items)}(embedded_fonts no))\n',used

def legacy_main():
 assign_types()
 g.ROOT.mkdir(exist_ok=True);g.LIBDIR.mkdir(exist_ok=True);g.FPDIR.mkdir(exist_ok=True)
 g.custom_footprints()
 for path in g.FPDIR.glob('*.kicad_mod'):
  content=path.read_text()
  fields=prop('Reference','REF**',0,-4,False).replace('(effects','(layer "F.SilkS") (effects')+prop('Value',path.stem,0,4,False).replace('(effects','(layer "F.Fab") (effects')
  content=content.replace('(attr smd)','(attr smd)'+fields)
  path.write_text(content)

 sheets=[getattr(g,f'make_{i:02d}')() for i in range(1,11)]
 (g.ROOT/'fp-lib-table').write_text('(fp_lib_table(lib(name "ShiroFOC_Footprints")(type "KiCad")(uri "${KIPRJMOD}/libs/ShiroFOC.pretty")(options "")(descr "Datasheet-derived local packages")))\n')
 settings=g.ROOT/(PROJECT+'.kicad_pro')
 data=json.loads(settings.read_text()) if settings.exists() else {'meta':{'filename':settings.name,'version':3}}
 data['sheets']=[[ROOTID,'Root']]+[[uid('child/'+s.filename),s.title] for s in sheets]
 settings.write_text(json.dumps(data,indent=2)+'\n')
 allsyms={}
 for i,s in enumerate(sheets,1):
  native,syms=build_sheet(s,i);allsyms.update(syms)
  (g.ROOT/s.filename.replace('.sch','.kicad_sch')).write_text(native)
 (g.LIBDIR/'ShiroFOC_KiCad.kicad_sym').write_text('(kicad_symbol_lib(version 20241209)(generator "kicad_symbol_editor")'+''.join(symbol_text(s) for s in allsyms.values())+')\n')
 (g.ROOT/'sym-lib-table').write_text('(sym_lib_table(lib(name "ShiroFOC_KiCad")(type "KiCad")(uri "${KIPRJMOD}/libs/ShiroFOC_KiCad.kicad_sym")(options "")(descr "Project symbols; typed electrical pins")))\n')
 items=[]
 for i,s in enumerate(sheets):
  x=30+(i%2)*190;y=65+(i//2)*39;cid=uid('child/'+s.filename)
  items.append(f'''(sheet(at {x} {y})(size 165 25)(stroke(width .254)(type default))(fill(color 0 0 0 0))(uuid {q(cid)})
  {prop('Sheetname',s.title,x+82.5,y-2.5,size=1.27)}{prop('Sheetfile',s.filename.replace('.sch','.kicad_sch'),x+82.5,y+27.5,size=1.016)}
  (instances(project {q(PROJECT)}(path {q('/'+ROOTID)}(page {q(i+2)})))))''')
 for i,t in enumerate(['ShiroFOC A0 - PCB layout release','18-42 V bus target | 3-phase inverter | STSPIN32G4 | 3 x Kelvin current sense', 'USB-priority control power | CAN | onboard encoder + external ABI/Hall | BMI323', 'Read ../docs/DESIGN_REVIEW_REV_A.md and ../docs/PCB_LAYOUT_HANDOFF.md before placement.']):
  items.append(f'(text {q(t)}(at 25 {20+i*9} 0){effects(2 if i==0 else 1.5,"left")}(uuid {q(uid("overview"+str(i)))}))')
 (g.ROOT/(PROJECT+'.kicad_sch')).write_text(f'(kicad_sch(version 20250114)(generator "eeschema")(uuid {q(ROOTID)})(paper "A3")(title_block(title "ShiroFOC Rev A0")(date "2026-09-15")(rev "A0"))(lib_symbols){"".join(items)}(sheet_instances(path "/"(page "1")))(embedded_fonts no))\n')
 # Keep the explicit design connectivity independent of KiCad's exported netlist.
 data={c.ref:{'pins':{p.number:s.connections.get((c.ref,p.number)) for p in c.sym.pins},'footprint':c.footprint,'value':c.value,'assembly':c.fields.get('Assembly','FIT')} for s in sheets for c in s.components}
 (g.ROOT/'outputs').mkdir(exist_ok=True)
 (g.ROOT/'outputs'/'source_connectivity.json').write_text(json.dumps(data,indent=2)+'\n')
 print(f'Generated {len(sheets)+1} native sheets; {len(data)} physical components')
def main():
 # Keep shared type/UUID helpers, but the supported build uses functional wiring.
 from redraw_rev_a import main as redraw_main
 redraw_main()
if __name__=='__main__':main()
