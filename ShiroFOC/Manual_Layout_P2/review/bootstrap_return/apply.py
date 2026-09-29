from pathlib import Path
import sys,copy,zipfile,json
sys.path.insert(0,'/tmp/cascade_work');from edit import *
P=Path('/Users/dionlava/Documents/GitHub/ShiroDrive/ShiroFOC/Manual_Layout_P2');O=P/'review/bootstrap_return';O.mkdir(exist_ok=True)
assert not (O/'before.zip').exists()
files=[P/'Three-phase bridge.kicad_sch',P/'04_Gate_Driver.kicad_sch',P/'ShiroFOC_Manual.kicad_pcb',P/'ShiroFOC_Manual.kicad_pro',P/'07_Brake_Chopper.kicad_sch']
with zipfile.ZipFile(O/'before.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in files:z.write(f,f.name)
gate=read(files[1]);bridge=read(files[0]);pcb=read(files[2]);rootdoc=read(P/'ShiroFOC_Manual.kicad_sch'); sheet_ids={val(x,'Sheetname'):one(x,'uuid')[1] for x in children(rootdoc,'sheet')}; new_sheet=sheet_ids['Gate driver / VCC'];old_sheet=sheet_ids['Three-phase bridge']
# Transfer capacitor symbols, preserving their UUIDs; use vertical orientation so cap pin2 is BOOT.
lib=next(x for x in children(one(bridge,'lib_symbols'),'symbol') if x[1]=='Device:C')
if not any(x[1]=='Device:C' for x in children(one(gate,'lib_symbols'),'symbol')):one(gate,'lib_symbols').append(copy.deepcopy(lib))
for phase,c,bx,yb,yo in [('U','C4',86.36,132.08,139.7),('V','C8',172.72,149.86,157.48),('W','C12',261.62,167.64,175.26)]:
 s=ref(bridge,c);cx=float(one(s,'at')[1]);bridge.remove(s)
 # Replace SH-cap-BOOT chain with a direct dedicated return label.
 for w in list(children(bridge,'wire')):
  pts=children(one(w,'pts'),'xy')
  if all(abs(float(pt[2])-50.8)<.001 for pt in pts) and any(abs(float(pt[1])-(cx-3.81))<.001 or abs(float(pt[1])-(cx+3.81))<.001 for pt in pts):bridge.remove(w)
 bridge.append(['wire',['pts',['xy',str(round(cx-5.08,2)),'50.8'],['xy',str(bx),'50.8']],['stroke',['width','0'],['type','default']],['uuid',uid()]])
 for l in children(bridge,'global_label'):
  if l[1]=='BOOTSTRAP'+str('UVW'.index(phase)+1):l[1]=Q('HS_RETURN_'+phase)
 # Both existing named power labels on the bridge become PHASE names.
 for l in children(bridge,'global_label'):
  if l[1]=='OUT'+str('UVW'.index(phase)+1):l[1]=Q('PHASE_'+phase)
 for l in children(gate,'global_label'):
  if l[1]=='OUT'+str('UVW'.index(phase)+1):l[1]=Q('HS_RETURN_'+phase)
 x=172.72;y=round((yb+yo)/2,2);one(s,'at')[1:]=[str(x),str(y),'180']
 for pr in children(s,'property'):
  at=one(pr,'at');at[1:]=[str(x-5.08),str(y+(-1.27 if pr[1]=='Reference' else 1.27)),'180']
 for project in children(one(s,'instances'),'project'):
  for path in children(project,'path'):path[1]=Q(path[1].replace(old_sheet,new_sheet))
 gate.append(s)
 for wy in [yb,yo]:
  for w in list(children(gate,'wire')):
   pts=children(one(w,'pts'),'xy');a,b=pts
   if abs(float(a[2])-wy)<.001 and abs(float(b[2])-wy)<.001 and min(float(a[1]),float(b[1]))<x<max(float(a[1]),float(b[1])):
    oldend=copy.deepcopy(b);b[1]=str(x);n=copy.deepcopy(w);one(n,'uuid')[1]=uid();one(n,'pts')[1:]=[['xy',str(x),str(wy)],oldend];gate.append(n);break
  gate.append(['junction',['at',str(x),str(wy)],['diameter','0'],['color','0','0','0','0'],['uuid',uid()]])
for d,t,xy in [(gate,'C4/C8/C12: place at BOOTx / OUTx pins. HS_RETURN_U/V/W go directly to MOSFET SH, paired with gate traces.',(20.32,269.24)),(bridge,'SH = dedicated high-side gate return. PHASE_U/V/W carry motor current. Keep these PCB routes separate; joined inside MOSFET package.',(20.32,266.7))]:
 d.append(['text',Q(t),['at',*map(str,xy),'0'],['effects',['font',['size','1.016','1.016']],['justify','left','top']],['uuid',uid()]])
write(files[0],bridge);write(files[1],gate)
rename={};codes={}
for n in children(pcb,'net'):
 for i,phase in enumerate('UVW',1):
  if n[2]=='OUT'+str(i):rename[n[2]]='PHASE_'+phase
  if n[2]==f'Net-(U{i}-SH)':rename[n[2]]='HS_RETURN_'+phase
for n in children(pcb,'net'):
 if n[2] in rename:n[2]=Q(rename[n[2]])
 codes[n[2]]=n[1]
def walk(x):
 if not isinstance(x,list):return
 if x and x[0]=='net' and len(x)==3 and x[2] in rename:x[2]=Q(rename[x[2]])
 for v in x:walk(v)
walk(pcb)
for f in children(pcb,'footprint'):
 r=val(f,'Reference')
 if r=='U4':
  for pad in children(f,'pad'):
   if pad[1] in ['42','39','36']:
    phase={'42':'U','39':'V','36':'W'}[pad[1]];one(pad,'net')[1:]=[codes['HS_RETURN_'+phase],Q('HS_RETURN_'+phase)]
 if r in ['C4','C8','C12']:
  one(f,'path')[1]=Q(one(f,'path')[1].replace(old_sheet,new_sheet))
  if prop(f,'Sheetfile'):prop(f,'Sheetfile')[2]=Q('04_Gate_Driver.kicad_sch')
  if prop(f,'Sheetname'):prop(f,'Sheetname')[2]=Q('Gate driver / VCC')
write(files[2],pcb)
pro=json.loads(files[3].read_text());pats=pro['net_settings']['netclass_patterns'];pats[:]=[x for x in pats if x['pattern'] not in ['HS_RETURN_*','PHASE_*']];pats += [{'netclass':'Gate','pattern':'HS_RETURN_*'},{'netclass':'Power','pattern':'PHASE_*'}];files[3].write_text(json.dumps(pro,indent=2)+'\n')
print('Applied schematic return-path correction; capacitor placement preserved from latest user save')

# Repair the prior NTC addition's annotation using its preserved symbol UUIDs.
d=read(P/'07_Brake_Chopper.kicad_sch');names={x['uuid']:x['ref'] for x in json.loads((P/'review/brake_ntc/new_components.json').read_text())}
for sym in syms(d):
 if one(sym,'uuid')[1] in names:
  r=names[one(sym,'uuid')[1]];update(sym,'Reference',r)
  for pr in children(one(sym,'instances'),'project'):
   for pa in children(pr,'path'):
    pa[1]=Q('/'+one(rootdoc,'uuid')[1]+'/'+sheet_ids['Brake chopper']);one(pa,'reference')[1]=Q(r)
write(P/'07_Brake_Chopper.kicad_sch',d)
