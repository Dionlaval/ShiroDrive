"""P3 placement-only candidate. Run with KiCad 9's bundled Python.

Always starts from the checkpoint. Never writes the working PCB. Existing
in-outline footprints/copper are immutable. Off-board local routing moves
with the same rigid transformation as its owning subcircuit.
"""
from pathlib import Path
from collections import defaultdict
import pcbnew as p
import json, math, shutil, hashlib

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parent.parent
BASE=HERE/'baseline.kicad_pcb'
DEST=HERE/'candidate'
DEST.mkdir(exist_ok=True)
for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:
    shutil.copy2(PROJECT/name,DEST/name)
if not (DEST/'libs').exists(): (DEST/'libs').symlink_to(PROJECT/'libs',target_is_directory=True)
b=p.LoadBoard(str(BASE)); b.BuildConnectivity()
fps={f.GetReference():f for f in b.GetFootprints()}
ox,oy=73.660312,63.936331
def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def pos(x,y):return vec(x+ox,y+oy)
def xy(item):return (p.ToMM(item.GetPosition().x)-ox,p.ToMM(item.GetPosition().y)-oy)
def uid(item):return item.m_Uuid.AsString()
def on_board(item):
    x,y=xy(item);return 0<=x<=80 and 0<=y<=80
fixed={r for r,f in fps.items() if on_board(f)}
initial={r:{'xy':xy(f),'angle':f.GetOrientationDegrees(),'side':f.GetLayerName(),'uuid':uid(f)} for r,f in fps.items()}
fixed_copper={uid(t) for t in b.GetTracks() if on_board(t)}
outside=[t for t in b.GetTracks() if not on_board(t)]
assigned=set(fixed);changes={};copper_moves={};group_records=[]

def bbox(f):
    layer=p.B_CrtYd if f.IsFlipped() else p.F_CrtYd
    boxes=[g.GetBoundingBox() for g in f.GraphicalItems() if g.GetLayer()==layer]
    if not boxes:
        boxes=[q.GetBoundingBox() for q in f.Pads()]
        boxes += [g.GetBoundingBox() for g in f.GraphicalItems() if g.GetLayer()==(p.B_Fab if f.IsFlipped() else p.F_Fab) and isinstance(g,p.PCB_SHAPE)]
    return (p.ToMM(min(a.GetLeft() for a in boxes))-ox,p.ToMM(min(a.GetTop() for a in boxes))-oy,p.ToMM(max(a.GetRight() for a in boxes))-ox,p.ToMM(max(a.GetBottom() for a in boxes))-oy)
def padbox(q):
    bb=q.GetBoundingBox();return (p.ToMM(bb.GetLeft())-ox,p.ToMM(bb.GetTop())-oy,p.ToMM(bb.GetRight())-ox,p.ToMM(bb.GetBottom())-oy)
def overlap(a,c,g=.12):return a[0]<c[2]+g and a[2]+g>c[0] and a[1]<c[3]+g and a[3]+g>c[1]
def errors(refs):
    refs=set(refs);bad=[]
    for r in sorted(refs):
        f=fps[r];bb=bbox(f)
        if min(bb[:2])<.5 or max(bb[2:])>79.5:bad.append([r,'edge'])
        for hr in ['H1','H2','H3','H4']:
            hx,hy=xy(fps[hr]);d=math.hypot(max(bb[0],min(hx,bb[2]))-hx,max(bb[1],min(hy,bb[3]))-hy)
            if d<4.05:bad.append([r,hr,'hardware'])
        for rr in sorted(assigned-refs):
            q=fps[rr]
            if rr.startswith('H'):continue
            if f.GetLayer()==q.GetLayer():
                if overlap(bb,bbox(q)):
                    # Three separated circular terminal courtyards, not one filled rectangle.
                    if rr=='J1' and not any(overlap(bb,padbox(pad),.5) for pad in q.Pads()):continue
                    bad.append([r,rr,'courtyard'])
            else:
                if any(overlap(bb,padbox(pad),.2) for pad in q.Pads() if pad.GetAttribute() in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH]):bad.append([r,rr,'through pad'])
    return bad

def note(r,group):
    changes[r]={'from':initial[r],'to':{'xy':xy(fps[r]),'angle':fps[r].GetOrientationDegrees(),'side':fps[r].GetLayerName()},'group':group}

def put(r,x,y,angle=None,side=None,group='',search=0):
    assert r not in fixed and r not in assigned, r
    f=fps[r]
    if side and f.IsFlipped()!=(side=='B'):f.Flip(f.GetPosition(),False)
    if angle is not None:f.SetOrientationDegrees(angle)
    f.SetPosition(pos(x,y))
    if search and errors([r]):
        found=False
        for n in range(1,int(search/.25)+1):
            offsets=[(dx*.25,dy*.25) for dx in range(-n,n+1) for dy in range(-n,n+1) if max(abs(dx),abs(dy))==n]
            for dx,dy in sorted(offsets,key=lambda z:z[0]*z[0]+z[1]*z[1]):
                f.SetPosition(pos(x+dx,y+dy))
                if not errors([r]):found=True;break
            if found:break
        if not found:raise RuntimeError('No nearby position for '+r+': '+str(errors([r])))
    assigned.add(r);note(r,group)

def translate_group(name,refs,anchor,target,copper_filter=None):
    assert not(set(refs)&assigned), name
    sx,sy=xy(fps[anchor]);delta=vec(target[0]-sx,target[1]-sy)
    objs=[t for t in outside if copper_filter and copper_filter(t)]
    for t in objs:
        assert uid(t) not in copper_moves
        before=[t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y]
        t.Move(delta);copper_moves[uid(t)]={'group':name,'translation_nm':[delta.x,delta.y],'before':before}
    for r in refs:
        fps[r].Move(delta);assigned.add(r);note(r,name)
    group_records.append({'name':name,'references':refs,'translation_nm':[delta.x,delta.y],'copper_uuids':[uid(t) for t in objs]})

# Routed power and comparator subcircuits retain all relative geometry.
translate_group('5 V converter',['U205','C214','C215','C218','C219','R216','R217','R218','R219'],'U205',(21,55),lambda t:18<xy(t)[1]<31)
translate_group('Power mux',['U203','C208','C209','C210','C211']+['R'+str(n) for n in range(206,216)],'U203',(26,66),lambda t:31<xy(t)[1]<44)
translate_group('3.3 V LDO',['U204','C212','C213'],'U204',(16,73))
translate_group('Brake gate stage',['Q501','U501','C501','C502','D501','R503','R504','R505'],'Q501',(26,28))
translate_group('Brake comparator',['U502','C503','C504','D503','R506','R509','R510'],'U502',(26.8,37),lambda t:80<xy(t)[1]<96)

# The high-voltage buck has one existing PG via and no routed traces. Its
# component placement is arranged on the front within the approved power area.
u=fps['U201'];old=u.GetPosition()
via=next(t for t in outside if uid(t) not in copper_moves)
assert isinstance(via,p.PCB_VIA) and via.GetNetname().endswith('/10V_GOOD')
v0=via.GetPosition();rel=v0-old
put('U201',10.5,47,0,'F','10 V buck')
via.SetPosition(pos(10.5+p.ToMM(rel.x),47-p.ToMM(rel.y)))
copper_moves[uid(via)]={'group':'10 V buck','reflection':'Y about U201, same as B-to-F footprint flip','before':[v0.x,v0.y,v0.x,v0.y]}
for r,x,y,a in [('C201',3.4,46,90),('C202',5.2,49.4,0),('C203',15.1,46.1,90),('C204',14.6,49.1,90),('L201',21.5,46.8,0),('C205',28,44.4,90),('C206',28,49,90),('R201',17.2,51.7,0),('R202',14.8,51.7,180)]:put(r,x,y,a,'F','10 V buck',search=1.5)

# Connector placement follows P1's bottom-edge interfaces while respecting the
# narrower space left by P3's fixed bridge and control layout.
for r,x,y,a,s,g in [
 ('J801',29.5,75,180,'F','CAN'),('J802',41.5,75,180,'F','CAN'),
 ('J601',55.5,75,180,'F','External feedback'),('J502',4.5,47,90,'B','Brake NTC'),
 ('U801',35.5,66,-90,'F','CAN'),('U603',51.8,66.3,0,'F','External feedback'),
 ('U602',51.5,73,90,'B','External feedback'),('U604',58.5,69,0,'F','Sensor power'),
 ('JP601',57.5,65.6,0,'B','Sensor power'),('SW301',53,28,0,'F','Reset / status'),
 ('D301',51,31.2,180,'F','Reset / status'),('R304',54,31.2,0,'F','Reset / status'),
 ('D101',16,13,0,'B','DC link'),('C107',27,10,90,'B','DC link'),('R102',27,19,90,'B','DC link'),
]:put(r,x,y,a,s,g,search=1)

seeds=[
 # CAN decoupling, protection, termination and accessible solder jumper.
 ('C801',32.2,66,90,'F','CAN'),('C802',30.6,66,90,'F','CAN'),
 ('R801',39.5,63.5,90,'F','CAN'),('R805',35.5,60.5,0,'F','CAN'),
 ('D801',29,69.5,-90,'F','CAN'),('R802',39.5,70.2,180,'F','CAN'),
 ('R803',39.5,66,-90,'F','CAN'),('R804',39.5,68,-90,'F','CAN'),
 ('JP801',24.5,68,90,'F','CAN'),
 # External port / ESD / Schmitt buffer. Optional pulls stay with their channels.
 ('D601',52.9,70.4,180,'F','External feedback'),('C604',49.1,70.7,90,'F','External feedback'),
 ('C605',54.8,65.5,90,'F','External feedback'),
 ('R605',48.5,64.7,0,'F','External feedback'),('R606',48.5,66.1,0,'F','External feedback'),('R607',48.5,67.5,0,'F','External feedback'),
 ('R608',45.8,64.7,0,'F','External feedback'),('R609',45.8,66.1,0,'F','External feedback'),('R610',45.8,67.5,0,'F','External feedback'),
 ('R604',53.5,63.3,90,'F','Sensor power'),('C606',56.2,68,90,'F','Sensor power'),('C607',61.4,68,90,'F','Sensor power'),
 ('C603',48.7,76.2,0,'B','Feedback mux'),('R305',49.4,68.1,0,'B','Feedback mux'),('R306',54.4,68.1,0,'B','Feedback mux'),
 ('R307',50.3,69.5,0,'F','Feedback mux'),
 ('R615',47.9,65.2,0,'B','External feedback'),('R616',47.9,66.6,0,'B','External feedback'),('R617',47.9,68,0,'B','External feedback'),
 # Bus divider: HV resistor near VM, lower leg and filter adjacent to mux.
 ('R103',55.8,71.5,90,'B','Bus sensing'),('R105',55.8,74.4,0,'B','Bus sensing'),('R106',55.8,75.9,0,'B','Bus sensing'),
 # Unplaced driver supply bypass. The already-placed C4/C8/C12 and MCU R/C stay fixed.
 ('C311',44.75,42.2,0,'F','Gate-driver supply'),('C312',40.7,42.6,0,'F','Gate-driver supply'),('C313',43,44.1,0,'F','Gate-driver supply'),
 # Brake command steering near the gate driver.
 ('D502',37.5,29,90,'F','Brake control'),('R502',40,29,90,'F','Brake control'),('R501',42,29,90,'F','Brake control'),
 # Temperature inputs; existing R713 and all MCU-local analog parts are immutable.
 ('R701',34,58.3,0,'B','Temperature ADC'),('R702',34,60.4,0,'B','Temperature ADC'),('R703',34,62.5,0,'B','Temperature ADC'),
 ('R711',37,58.3,0,'B','Temperature ADC'),('R712',37,60.4,0,'B','Temperature ADC'),
 ('C711',39.7,59.3,0,'B','Temperature ADC'),('C712',39.7,61.4,0,'B','Temperature ADC'),('C713',42.4,59.3,0,'B','Temperature ADC'),
 ('R511',35,65.5,0,'B','Brake NTC'),('R512',37.7,65.5,0,'B','Brake NTC'),
 ('D505',42,64.5,0,'B','Brake NTC'),('C505',39.7,63.5,0,'B','Brake NTC'),
]
for r,x,y,a,s,g in seeds:put(r,x,y,a,s,g,search=2.5)
assert assigned==set(fps), 'Unplaced: '+str(set(fps)-assigned)
assert set(copper_moves)=={uid(t) for t in outside}

# Put only moved-part reference labels on fabrication layers. Fixed footprints
# (including their original labels and graphics) remain completely untouched.
for r in changes:
    f=fps[r];ref=f.Reference();bb=bbox(f)
    ref.SetLayer(p.B_Fab if f.IsFlipped() else p.F_Fab)
    ref.SetTextSize(vec(.75,.75));ref.SetTextThickness(p.FromMM(.12))
    ref.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));ref.SetMirrored(f.IsFlipped())
    ref.SetPosition(pos((bb[0]+bb[2])/2,bb[1]-.65))
    f.Value().SetVisible(False)

# Replace obsolete review text with non-copper functional section guides.
removed_drawings=[]
for d in list(b.GetDrawings()):
    if isinstance(d,p.PCB_TEXT) and (d.GetLayer()==p.Cmts_User or d.GetText()=='${REFERENCE}'):
        removed_drawings.append(uid(d));b.RemoveNative(d)
added_drawings=[]
def guide_text(text,x,y,layer,size=.8):
    d=p.PCB_TEXT(b);d.SetText(text);d.SetPosition(pos(x,y));d.SetLayer(layer)
    d.SetTextSize(vec(size,size));d.SetTextThickness(p.FromMM(.12));b.Add(d);added_drawings.append(uid(d))
def guide_poly(points,layer):
    for a,c in zip(points,points[1:]+points[:1]):
        d=p.PCB_SHAPE();d.SetShape(p.SHAPE_T_SEGMENT);d.SetStart(pos(*a));d.SetEnd(pos(*c))
        d.SetLayer(layer);d.SetWidth(p.FromMM(.1))
        b.Add(d);added_drawings.append(uid(d))
def guide_box(x0,y0,x1,y1,layer):guide_poly([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],layer)
F,B=p.User_1,p.User_2
guide_box(10.7,.5,71.7,23.7,F);guide_text('DC LINK / BULK CAPACITORS',41.2,1.8,F,.9)
guide_poly([(20.2,24.3),(48.2,24.3),(48.2,34.1),(33,34.1),(33,41.5),(20.2,41.5)],F)
guide_text('BRAKE CHOPPER',39.5,32.6,F,.8)
guide_box(.3,23.7,19.5,41.2,F);guide_text('DC INPUT',9,40.7,F,.8)
bridge=[(56.8,28.3),(79.6,28.3),(79.6,76.8),(63.2,76.8),(63.2,68.2),(56.8,68.2)]
guide_poly(bridge,F);guide_text('HALF-BRIDGES / SHUNTS - FIXED',67.8,29.3,F,.68)
guide_box(.4,42.2,30.4,53.7,F);guide_text('10 V AUXILIARY POWER',17,53.0,F,.8)
guide_box(32.3,41,54,60.2,F);guide_text('MCU + ANALOG - FIXED',45.3,59.3,F,.8)
guide_text('IMU',35.8,56.5,F,.8)
guide_box(.4,54.5,22,70.5,F);guide_text('USB / UART',11.3,69.8,F,.8)
guide_box(23.1,59.2,46.3,79.2,F);guide_text('CAN INTERFACE',34.5,61.5,F,.8)
external=[(47,61.5),(55.5,61.5),(55.5,69.5),(62.5,69.5),(62.5,79),(47,79)]
guide_poly(external,F);guide_text('EXTERNAL ENCODER / HALL',54.7,78.7,F,.62)
guide_box(49.5,24.8,57,33,F);guide_text('RESET / STATUS',53.3,25.5,F,.58)
guide_text('SWD',53.9,42.2,F,.7)
guide_box(10.7,.5,71.7,23.7,B);guide_text('DC LINK PROTECTION / DAMPING',41,2,B,.85)
guide_poly([(10,40.5),(32,40.5),(32,78.3),(12,78.3),(12,69),(10,69)],B)
guide_text('5 V / POWER MUX / 3.3 V',21,77.6,B,.68)
guide_box(.5,42,9,53,B);guide_text('BRAKE NTC',4.7,52.2,B,.65)
guide_box(31.5,34.3,47.5,43.7,B);guide_text('ENCODER - CENTRED AS5047',39.5,35.3,B,.65)
guide_poly([(36,43.8),(53,43.8),(53,58.5),(40.5,58.5),(40.5,57),(36,57)],B);guide_text('MCU / OP-AMP R + C - FIXED',44.5,44.6,B,.62)
guide_poly([(32,57.1),(40.4,57.1),(40.4,58.7),(45.5,58.7),(45.5,68.1),(32,68.1)],B);guide_text('TEMPERATURE / ADC FILTERS',38.7,67.5,B,.56)
guide_poly([(46.5,62.5),(55.5,62.5),(55.5,69.5),(62.2,69.5),(62.2,78.8),(46.5,78.8)],B)
guide_text('FEEDBACK MUX / BUS SENSE',54.3,78.3,B,.61)
guide_poly(bridge,B);guide_text('BRIDGE ROUTING - FIXED',68.2,29.3,B,.7)
guide_text('P3 PLACEMENT | NO NEW ROUTING | NO TEST POINTS',40,-7,p.Cmts_User,1.1)
guide_text('F.Cu: HIGH POWER | In1.Cu: SIGNALS + LV POWER | In2.Cu: GND | B.Cu: SIGNALS + GND',40,-4.5,p.Cmts_User,.8)
guide_text('User.1: FRONT AREAS | User.2: BACK AREAS | Non-copper placement guides',40,-2.4,p.Cmts_User,.8)
for hr in ['H1','H2','H3','H4']:
    hx,hy=xy(fps[hr]);d=p.PCB_SHAPE();d.SetShape(p.SHAPE_T_CIRCLE);d.SetCenter(pos(hx,hy));d.SetEnd(pos(hx+4,hy))
    d.SetLayer(p.Dwgs_User);d.SetWidth(p.FromMM(.1));b.Add(d);added_drawings.append(uid(d))

problems=errors(changes)
# Raw same-side errors within a rigid group are caught by native DRC; the
# existing U204 pad clearances are not changed by placement.
b.BuildConnectivity();p.SaveBoard(str(DEST/'ShiroFOC_Manual.kicad_pcb'),b,True)
report={'source_sha256':hashlib.sha256(BASE.read_bytes()).hexdigest(),'protected_references':sorted(fixed),'moved_references':changes,'fixed_copper_uuids':sorted(fixed_copper),'moved_copper':copper_moves,'rigid_groups':group_records,'placement_conflicts':problems,'removed_drawings':removed_drawings,'added_drawings':added_drawings,'footprints':len(fps),'copper_items':len(b.GetTracks())}
(HERE/'placement_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print('Candidate:',len(fixed),'fixed footprints;',len(changes),'moved;',len(fixed_copper),'fixed copper;',len(copper_moves),'moved copper')
print('Placement conflicts:',json.dumps(problems))
