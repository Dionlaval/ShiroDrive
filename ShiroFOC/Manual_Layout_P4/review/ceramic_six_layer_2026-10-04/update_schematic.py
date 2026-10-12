"""Apply the approved ceramic-bank revision to the saved pre-change checkpoint.

Only selected top-level S-expressions are rewritten. Existing symbol UUIDs,
wiring and library definitions are retained outside this revision.
"""
from pathlib import Path
import copy, json, re, uuid

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
BASE = Path('/tmp/shiro-ceramic-six-layer-20261004/before')
ROOT = '2c8b7510-9664-4afd-8f00-ac42aa791be9'
NS = uuid.UUID('826a4d6c-5662-4a58-9817-0a0242d4c085')
def uid(name): return str(uuid.uuid5(NS, name))
class Q(str): pass
def parse(s):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', s)
    stack=[]; root=None
    for t in tokens:
        if t=='(':
            n=[]
            if stack: stack[-1].append(n)
            else: root=n
            stack.append(n)
        elif t==')': stack.pop()
        else: stack[-1].append(Q(json.loads(t)) if t.startswith('"') else t)
    return root
def dump(n, level=0):
    if not isinstance(n,list): return json.dumps(str(n),ensure_ascii=False) if isinstance(n,Q) else str(n)
    if not any(isinstance(x,list) for x in n): return '('+' '.join(dump(x) for x in n)+')'
    h=[]; tail=[]
    for x in n:
        (tail if isinstance(x,list) or tail else h).append(x)
    return '('+' '.join(dump(x) for x in h)+''.join('\n'+'\t'*(level+1)+dump(x,level+1) for x in tail)+'\n'+'\t'*level+')'
def all_(n,k): return [v for v in n if isinstance(v,list) and v and v[0]==k]
def one(n,k): return next((v for v in all_(n,k)),None)
def prop(n,k): return next((v for v in all_(n,'property') if v[1]==k),None)
def properties(n): return {v[1]:v[2] for v in all_(n,'property')}

class Sheet:
    def __init__(self,name):
        self.path=PROJECT/name; self.s=(BASE/name).read_text(); self.parts=[]; self.extra=[]
        depth=0; quoted=False; esc=False; start=0
        for i,c in enumerate(self.s):
            if quoted:
                if esc: esc=False
                elif c=='\\': esc=True
                elif c=='"': quoted=False
                continue
            if c=='"': quoted=True
            elif c=='(':
                if depth==1:start=i
                depth+=1
            elif c==')':
                depth-=1
                if depth==1:self.parts.append([start,i+1,parse(self.s[start:i+1]),None])
        self.symbols={properties(p[2]).get('Reference'):p for p in self.parts if p[2][0]=='symbol'}
        self.sheetpath=one(one(one(self.symbols[next(r for r in self.symbols if not r.startswith('#'))][2],'instances'),'project'),'path')[1]
    def nodes(self,k):return [p for p in self.parts if p[2][0]==k]
    def replace(self,part,node):part[3]=dump(node,1)
    def remove(self,part):part[3]=''
    def add(self,node):self.extra.append(node)
    def lib(self,key,other=None):
        part=self.nodes('lib_symbols')[0]; n=part[2]
        if any(v[1]==key for v in all_(n,'symbol')):return
        src=other.nodes('lib_symbols')[0][2]
        n.append(copy.deepcopy(next(v for v in all_(src,'symbol') if v[1]==key)))
        self.replace(part,n)
    def save(self):
        s=self.s
        for start,end,n,replacement in reversed(self.parts):
            if replacement is not None:s=s[:start]+replacement+s[end:]
        end=s.rfind(')');s=s[:end]+''.join('\n\t'+dump(n,1) for n in self.extra)+'\n'+s[end:]
        s=re.sub(r'(?m)^[ \t]+$', '', s)
        parse(s);self.path.write_text(s)

def property_(key,val,x,y,visible=False,size=1.0):
    return ['property',Q(key),Q(val),['at',x,y,0],['effects',['font',['size',size,size]],['justify','left']]+([] if visible else [['hide','yes']])]
def symbol(sheet,ref,lib,x,y,value,footprint,pins,fields=None,dnp=False,old_uuid=None,bom=True):
    n=['symbol',['lib_id',Q(lib)],['at',x,y,0],['unit',1],['exclude_from_sim','no'],['in_bom','yes' if bom else 'no'],['on_board','yes'],['dnp','yes' if dnp else 'no'],['uuid',Q(old_uuid or uid(ref))]]
    n += [property_('Reference',ref,x+2.54,y-1.27,True,.95),property_('Value',value,x+2.54,y+1.27,True,.95),property_('Footprint',footprint,x,y),property_('Datasheet','',x,y)]
    for k,v in (fields or {}).items():
        p=prop(n,k)
        if p:p[2]=Q(v)
        else:n.append(property_(k,v,x,y))
    n += [['pin',Q(str(p)),['uuid',Q(uid(ref+':pin'+str(p)))]] for p in pins]
    n += [['instances',['project',Q('ShiroFOC_Manual'),['path',Q(sheet.sheetpath),['reference',Q(ref)],['unit',1]]]]]
    return n
def wire(sheet,x1,y1,x2,y2):
    assert (x1,y1)!=(x2,y2)
    sheet.add(['wire',['pts',['xy',round(x1,4),round(y1,4)],['xy',round(x2,4),round(y2,4)]],['stroke',['width',0],['type','default']],['uuid',Q(uid(f'{sheet.path.name}:w:{x1},{y1}:{x2},{y2}'))]])
def label(sheet,name,x,y,global_=True,angle=0):
    n=['global_label' if global_ else 'label',Q(name)]
    if global_:n.append(['shape','bidirectional'])
    n += [['at',round(x,4),round(y,4),angle],['effects',['font',['size',1,1]],['justify','left' if angle==0 else 'right']],['uuid',Q(uid(f'{sheet.path.name}:l:{name}:{x},{y}'))]]
    sheet.add(n)
def junction(sheet,x,y):sheet.add(['junction',['at',round(x,4),round(y,4)],['diameter',0],['color',0,0,0,0],['uuid',Q(uid(f'{sheet.path.name}:j:{x},{y}'))]])
def text(sheet,s,x,y,size=1.27):sheet.add(['text',Q(s),['at',x,y,0],['effects',['font',['size',size,size]],['justify','left','top']],['uuid',Q(uid(f'{sheet.path.name}:text:{s}'))]])

dc=Sheet('01_DC_Link.kicad_sch'); bridge=Sheet('Three-phase bridge.kicad_sch'); sense=Sheet('06_Current_Temperature.kicad_sch')
dc.lib('Device:C',bridge)
dc.replace(dc.nodes('paper')[0],['paper',Q('A3')])
title=dc.nodes('title_block')[0]
one(title[2],'date')[1]=Q('2026-10-04');one(title[2],'rev')[1]=Q('A2-Ceramic')
one(title[2],'comment')[2]=Q('48 fitted MLCCs; six optional positions; battery damping retained')
dc.replace(title,title[2])
for p in dc.nodes('text'):
    if '3 × 680' in p[2][1]:
        p[2][1]=Q('Ceramic DC link: bank below; local high-frequency bypass retained');dc.replace(p,p[2])

# Remove only the six old capacitor pin stubs. Keep battery / bypass rails.
for p in dc.nodes('wire'):
    pts=all_(one(p[2],'pts'),'xy'); a,b=[(float(v[1]),float(v[2])) for v in pts]
    if a[0]==b[0] and a[0] in [63.5,93.98,124.46] and any(y in [67.31,77.47] for _,y in [a,b]):dc.remove(p)
# Move the two ERC power flags into the otherwise-empty upper right of A3.
for p in dc.parts:
    n=p[2]
    if n[0] not in ['symbol','wire','global_label','junction']:continue
    at=one(n,'at'); pts=one(n,'pts')
    match=(at and float(at[2])==187.96) or (pts and all(float(v[2])==187.96 for v in all_(pts,'xy')))
    if not match:continue
    def move(node):
        if isinstance(node,list):
            if node[0] in ['at','xy']:
                node[1]=round(float(node[1])+299.72,4);node[2]=round(float(node[2])-125.73,4)
            else:
                for x in node:move(x)
    move(n);dc.replace(p,n)

groups=[['C101']+['C'+str(n) for n in range(110,127)],['C102']+['C'+str(n) for n in range(127,144)],['C103']+['C'+str(n) for n in range(144,161)]]
manifest={'capacitor_groups':{},'new_symbols':[],'restored_pcb_symbols':['C414','C424','C434','TP101','TP102','TP1018','TP1019','TP1020']}
datasheet='https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/3563/CL32Y106KCVZNWE_Tech_Article.pdf'
for gi,refs in enumerate(groups):
    phase='UVW'[gi]; y=190.5+26.67*gi
    manifest['capacitor_groups'][phase]={'fit':refs[:16],'dnp':refs[16:]}
    text(dc,f'BANK {phase}: 16 FIT + 2 DNP   |   10 uF / 100 V / X7S / 1210   |   CL32Y106KCVZNWE',17.78,round(y-14,4),1.1)
    for i,r in enumerate(refs):
        x=25.4+19.05*i;dn=i>=16
        fields={'Manufacturer':'Samsung Electro-Mechanics','MPN':'CL32Y106KCVZNWE','LCSC':'C3840810','Datasheet':datasheet,'Voltage Rating':'100 V','Dielectric':'X7S','Tolerance':'10%','Assembly':'DNP' if dn else 'FIT','Bank':phase,'BOM Comments':'Prototype ceramic DC link. Approximately 3.3 uF typical at 42 V per manufacturer DC-bias curve, before temperature, tolerance and aging. Validate bus ripple, hot-plug and regeneration.'}
        old=dc.symbols.get(r); oldid=one(old[2],'uuid')[1] if old else None
        n=symbol(dc,r,'Device:C',round(x,4),round(y,4),'10uF'+(' DNP' if dn else ''),'Capacitor_SMD:C_1210_3225Metric',[1,2],fields,dn,oldid)
        if old:dc.replace(old,n)
        else:dc.add(n);manifest['new_symbols'].append(r)
        wire(dc,x,y-7.62,x,y-3.81);wire(dc,x,y+3.81,x,y+7.62)
        if i:
            wire(dc,x-19.05,y-7.62,x,y-7.62);wire(dc,x-19.05,y+7.62,x,y+7.62)
        if 0<i<17:junction(dc,x,y-7.62);junction(dc,x,y+7.62)
    label(dc,'VM',25.4,round(y-7.62,4),True,180);label(dc,'GND',25.4,round(y+7.62,4),True,180)
text(dc,'48 fitted = 480 uF nominal; approximately 160 uF typical at 42 V before tolerances.\nSix optional positions add 60 uF nominal. This bank replaces C101-C103 electrolytics.\nValidate cable resonance, regeneration, ripple heating and transient margin on hardware.',17.78,267.97,1.15)

# Rework access: two large solder pads, with separate small VM/GND scope pads retained.
for r,net,x in [('TP104','VM',322.58),('TP105','GND',358.14)]:
    dc.add(symbol(dc,r,'Manual:COMP_TP101',x,95.25,net+' BULK','TestPoint:TestPoint_Pad_D3.0mm',[1],{'MPN':'PCB feature','Manufacturer':'PCB','Assembly':'PCB','Test_Net':net,'Description':'External bulk capacitor attachment; use short paired conductors'},bom=False))
    wire(dc,x,95.25,x,102.87);label(dc,net,x,102.87,True,180);manifest['new_symbols'].append(r)
text(dc,'OPTIONAL EXTERNAL BULK\nShort VM/GND connection for bring-up tuning',307.34,78.74,1.1)

# Snubber return is the FET source side of each shunt, never the sense stub.
bridge.lib('Manual:COMP_TP101',dc)
for part in bridge.nodes('text'):
    if str(part[2][1]).startswith('SH:'):
        one(part[2],'at')[2]='82.55';bridge.replace(part,part[2])
for phase,x,sx,r,c,gt,st,pt,gatenet in [
    ('U',45.72,34.29,'R415','C413','TP411','TP412','TP413','GLS1'),
    ('V',127.0,120.65,'R425','C423','TP421','TP422','TP423','GLS2'),
    ('W',195.58,209.55,'R435','C433','TP431','TP432','TP433','GLS3')]:
    src='LS_SOURCE_'+phase
    label(bridge,src,sx,55.88,False,180)
    for ref,lib,y,val,fp in [(r,'Device:R',111.76,'TUNE DNP','Resistor_SMD:R_1206_3216Metric'),(c,'Device:C',127.0,'TUNE DNP','Capacitor_SMD:C_1206_3216Metric')]:
        fields={'Assembly':'DNP','MPN':'','Manufacturer':'','Procurement':'Select after measured switch-node ringing; keep DNP until tuned','Rating':'Pulse-rated resistor, >=100 V working-voltage class; verify dissipation' if ref.startswith('R') else 'C0G/NP0, >=100 V; value selected from measured ringing','BOM Comments':'Series RC from PHASE_'+phase+' to low-side source, before shunt. Minimize loop area.'}
        bridge.add(symbol(bridge,ref,lib,x,y,val,fp,[1,2],fields,True));manifest['new_symbols'].append(ref)
    wire(bridge,x,104.14,x,107.95);label(bridge,'PHASE_'+phase,x,104.14,True,180)
    wire(bridge,x,115.57,x,123.19);wire(bridge,x,130.81,x,134.62);label(bridge,src,x,134.62,False)
    text(bridge,'PHASE '+phase+' / OPTIONAL RC',x-12.7,95.25,1.1)
    # Low-side Vgs and phase probing; all separate nodes, no ground short.
    for ref,net,dx,glob in [(gt,gatenet,-12.7,True),(st,src,5.08,False),(pt,'PHASE_'+phase,22.86,True)]:
        tx=x+dx;ty=147.32
        bridge.add(symbol(bridge,ref,'Manual:COMP_TP101',tx,ty,net,'TestPoint:TestPoint_Pad_D1.0mm',[1],{'MPN':'PCB feature','Manufacturer':'PCB','Assembly':'PCB','Test_Net':net},bom=False))
        # Short value label avoids overlap; full net name remains in Test_Net.
        prop(bridge.extra[-1],'Value')[2]=Q('GL' if ref==gt else ('SOURCE' if ref==st else 'PHASE'))
        wire(bridge,tx,ty,tx,ty+5.08);label(bridge,net,tx,ty+5.08,glob,90)
        manifest['new_symbols'].append(ref)
text(bridge,'RC snubbers: all DNP. Tune from measured ringing; verify resistor pulse/average power.\nReturn each RC to the local MOSFET PGND power pad BEFORE the shunt.\nGL/SOURCE pads measure low-side Vgs; PHASE is a switching node.',20.32,177.8,1.1)

# Ground probe pad for each of the three existing current-sense output points.
sense.lib('Manual:COMP_TP101',dc)
for ref,x in [('TP414',118.11),('TP424',248.92),('TP434',379.73)]:
    y=130.81
    sense.add(symbol(sense,ref,'Manual:COMP_TP101',x,y,'SCOPE GND','TestPoint:TestPoint_Pad_D1.0mm',[1],{'MPN':'PCB feature','Manufacturer':'PCB','Assembly':'PCB','Test_Net':'GND'},bom=False))
    wire(sense,x,y,x,y+5.08);label(sense,'GND',x,y+5.08,True,180);manifest['new_symbols'].append(ref)

for s in [dc,bridge,sense]:s.save()
(HERE/'change_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Updated three sheets; 48 fitted and 6 DNP ceramics; three DNP phase RCs; probe and bulk pads.')
