"""Apply the approved revision using KiCad 9's native board API.

Run using the Python bundled with KiCad. Starts from the backed-up board;
preserves all existing copper and footprints except the three replaced cans
and the explicitly recorded small placement adjustments.
"""
from pathlib import Path
import json, math, uuid, xml.etree.ElementTree as ET
import pcbnew as p
HERE=Path(__file__).resolve().parent; PROJECT=HERE.parent.parent
TEMP=Path('/tmp/shiro-ceramic-six-layer-20261004')
BASE=TEMP/'before'/'ShiroFOC_Manual.kicad_pcb'
STD=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
manifest=json.loads((HERE/'change_manifest.json').read_text())
b=p.LoadBoard(str(BASE)); fps={f.GetReference():f for f in b.GetFootprints()}
NS=uuid.UUID('af8d3de9-9aa5-4b28-9fb4-ed2810937804')
def uid(s):return str(uuid.uuid5(NS,s))
def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def xy(q):return [p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y)]
def box(q):
    a=q.GetBoundingBox();return (p.ToMM(a.GetLeft()),p.ToMM(a.GetTop()),p.ToMM(a.GetRight()),p.ToMM(a.GetBottom()))
def courtyard(f):
    shapes=[g for g in f.GraphicalItems() if g.GetLayer()==(p.B_CrtYd if f.IsFlipped() else p.F_CrtYd)]
    if not shapes:shapes=list(f.Pads())
    bb=[box(g) for g in shapes]
    return (min(a[0] for a in bb),min(a[1] for a in bb),max(a[2] for a in bb),max(a[3] for a in bb))
def overlaps(a,c,g=.06):return a[0]<c[2]+g and a[2]+g>c[0] and a[1]<c[3]+g and a[3]+g>c[1]

def readnet(path):
    t=ET.parse(path);comps={c.get('ref'):c for c in t.findall('./components/comp')};pins={}
    for n in t.findall('./nets/net'):
        for v in n.findall('node'):pins[v.get('ref'),v.get('pin')]=n.get('name')
    return comps,pins
comps,pins=readnet(TEMP/'after.xml');oldcomps,oldpins=readnet(TEMP/'before.xml')
renames={oldpins[k]:pins[k] for k in oldpins if k in pins and oldpins[k]!=pins[k]}
nets={str(k):v for k,v in b.GetNetsByName().items()}
for name in set(pins.values()):
    if name not in nets:
        n=p.NETINFO_ITEM(b,name,max(v.GetNetCode() for v in nets.values())+1);b.Add(n);nets[name]=n
for f in fps.values():
    for q in f.Pads():
        if q.GetNetname() in renames:q.SetNet(nets[renames[q.GetNetname()]])
for t in b.GetTracks():
    if t.GetNetname() in renames:t.SetNet(nets[renames[t.GetNetname()]])
    if not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.In1_Cu:t.SetLayer(p.In2_Cu)
# These two GND segments only joined the obsolete electrolytic pads. Their
# endpoints became dangling when those footprints were replaced.
obsolete_can_tracks={'aa20e6f2-a48d-459a-ab5c-523c183aa7c6','d20060e9-1ca7-49fb-a2e9-3720f5cab397'}
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in obsolete_can_tracks:
        assert t.GetNetname()=='GND' and t.GetLayer()==p.F_Cu
        b.Remove(t)
b.SetCopperLayerCount(6)
enabled=b.GetEnabledLayers();enabled.AddLayer(p.In3_Cu);enabled.AddLayer(p.In4_Cu);b.SetEnabledLayers(enabled)
for lid,name in [(p.In1_Cu,'GND L2'),(p.In2_Cu,'Signals L3'),(p.In3_Cu,'Power L4'),(p.In4_Cu,'GND L5')]:b.SetLayerName(lid,name)

records={};assigned=set(fps)-{'C101','C102','C103'}
old_can_ids={r:fps[r].m_Uuid.AsString() for r in ['C101','C102','C103']}
for r in old_can_ids:b.Remove(fps[r]);del fps[r]
def load(ref):
    c=comps[ref];lib,name=c.findtext('footprint').split(':',1)
    folder=STD/(lib+'.pretty') if lib!='Manual' else PROJECT/'libs'/'Manual.pretty'
    f=p.FootprintLoad(str(folder),name);assert f, (ref,str(folder),name)
    f.SetFPID(p.LIB_ID(lib,name))
    f.SetReference(ref);f.SetValue(c.findtext('value'))
    f.SetPath(p.KIID_PATH(c.find('sheetpath').get('tstamps')+c.findtext('tstamps')))
    attrs=f.GetAttributes()
    if c.find("property[@name='dnp']") is not None:attrs|=p.FP_DNP
    if ref.startswith('TP'):attrs|=p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES
    f.SetAttributes(attrs)
    for fld in c.findall('./fields/field'):
        if fld.get('name') not in ['Footprint','Description','Datasheet']:f.SetField(fld.get('name'),fld.text or '')
    f.SetField('Datasheet',c.findtext('datasheet') or '')
    for q in f.Pads():
        net=pins.get((ref,q.GetNumber()))
        if net:q.SetNet(nets[net])
    for g in list(f.GraphicalItems())+list(f.GetFields()):
        if hasattr(g,'SetVisible'):g.SetVisible(False)
    f.Reference().SetVisible(False);f.Value().SetVisible(False)
    b.Add(f);fps[ref]=f;return f

def errors(ref):
    f=fps[ref];bb=courtyard(f);bad=[]
    if min(bb[:2]) < -39 or max(bb[2:]) > 39:bad.append('edge')
    for hr in ['H1','H2','H3','H4']:
        hx,hy=xy(fps[hr]);d=math.hypot(max(bb[0],min(hx,bb[2]))-hx,max(bb[1],min(hy,bb[3]))-hy)
        if d<4.05:bad.append(hr)
    for rr in assigned-{ref}:
        q=fps[rr]
        if rr.startswith('H'):continue
        if f.GetLayer()==q.GetLayer() and overlaps(bb,courtyard(q)):
            if rr=='J1' and not any(overlaps(bb,box(pad),.5) for pad in q.Pads()):continue
            bad.append(rr)
        elif f.GetLayer()!=q.GetLayer():
            # Bare probe pads have no mounted body. Check their actual copper
            # with the power-net gap, rather than treating their 2 mm probe
            # courtyard as a body that cannot overhang a flat thermal land.
            testbb=box(next(iter(f.Pads()))) if ref.startswith('TP') else bb
            gap=.5 if ref.startswith('TP') else .2
            if any(overlaps(testbb,box(pad),gap) for pad in q.Pads() if pad.GetAttribute() in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH]):bad.append(rr+' PTH')
    # Avoid existing tracks and vias under new copper pads. Rectangular
    # bounds are conservative; native DRC is the final geometric check.
    for pad in f.Pads():
        pb=box(pad)
        for t in b.GetTracks():
            if t.GetNetCode()==pad.GetNetCode():continue
            if not isinstance(t,p.PCB_VIA) and t.GetLayer()!=f.GetLayer():continue
            if overlaps(pb,box(t),.2) and t.HitTest(pad.GetBoundingBox(),False,p.FromMM(.2)):bad.append('existing copper');break
    return bad

def put(ref,x,y,a=0,side='F',search=0,group=''):
    f=fps.get(ref) or load(ref);before={'xy':xy(f),'side':f.GetLayerName(),'angle':f.GetOrientationDegrees()} if ref in assigned else None
    if f.IsFlipped() != (side=='B'):f.Flip(f.GetPosition(),False)
    f.SetOrientationDegrees(a);f.SetPosition(vec(x,y))
    if search and errors(ref):
        candidates=[]
        for dx in range(-int(search/.25),int(search/.25)+1):
            for dy in range(-int(search/.25),int(search/.25)+1):
                if math.hypot(dx,dy)*.25<=search:candidates.append((dx*.25,dy*.25))
        for dx,dy in sorted(candidates,key=lambda q:q[0]*q[0]+q[1]*q[1]):
            f.SetPosition(vec(x+dx,y+dy))
            if not errors(ref):break
    bad=errors(ref)
    if bad:raise RuntimeError((ref,xy(f),bad))
    assigned.add(ref);records[ref]={'before':before,'xy':xy(f),'side':f.GetLayerName(),'angle':a,'group':group}

# Existing local 4.7 uF capacitors are unrouted. Shift two to clear the new
# source-to-phase snubbers; preserve the closest 10 nF / 1 uF footprints.
put('C3',17.3,5.56,0,'F',1,'phase U bypass')
put('C7',17.3,19.56,0,'F',1,'phase V bypass')
for idx,(r,c) in enumerate([('R415','C413'),('R425','C423'),('R435','C433')]):
    y=-8.0+14*idx
    # R1 (phase) at right, C2 (source) at left, with RC midpoint adjacent.
    put(c,22.5,y,180,'F',1,'phase RC')
    put(r,27.0,y,180,'F',1,'phase RC')
for r,x,y,a in [('C414',-1.9,14.53,0),('C424',3.1,13.7,90),('C434',9.2,19.2,0)]:put(r,x,y,a,'B',3,'feedback tuning')
for sig,gnd,x,y in [('TP1018','TP414',-3.5,17.5),('TP1019','TP424',3,20),('TP1020','TP434',8,21)]:
    put(sig,x,y,0,'B',3,'current probe');put(gnd,records[sig]['xy'][0]+1.8,records[sig]['xy'][1],0,'B',3,'current probe')
for idx,(gate,src,phase) in enumerate([('TP411','TP412','TP413'),('TP421','TP422','TP423'),('TP431','TP432','TP433')]):
    yc=-3.436+14*idx
    put(gate,23.6,yc+3.0,0,'F',2,'low-side gate probe')
    put(src,records[gate]['xy'][0]-1.8,records[gate]['xy'][1],0,'F',4,'low-side source probe')
    put(phase,31.3,yc-1,0,'B',0,'phase probe')

# Start with local backside positions, using the freed top-side bulk area
# where existing gate/sense routing blocks a backside pad. Regular candidate
# grids maintain reflow access and keep all added capacitors in the power area.
def place_cap(ref,x,y,side,phase):
    f=fps.get(ref) or load(ref)
    candidates=[]
    if side=='B':
        for xx in [13.2,18.4,23.6]:
            for yy in [round(-25.2+3.6*j,4) for j in range(17)]:
                if abs(yy-y)<=7:candidates.append((math.hypot(xx-x,yy-y),'B',xx,yy))
        candidates.append((0,'B',x,y))
    for xx in [round(-23.6+5.2*j,4) for j in range(12)]:
        for yy in [-29.4,-25.8,-22.2,-18.6,-15]:
            candidates.append((math.hypot(xx-x,yy-y)+(25 if side=='B' else 0),'F',xx,yy))
    for score,ss,xx,yy in sorted(candidates):
        if f.IsFlipped()!=(ss=='B'):f.Flip(f.GetPosition(),False)
        f.SetOrientationDegrees(0);f.SetPosition(vec(xx,yy))
        if not errors(ref):
            put(ref,xx,yy,0,ss,0,'DC link '+phase);return
    raise RuntimeError('No legal capacitor placement: '+ref)

put('JP601',24,36.4,0,'B',3,'clear ceramic bank')
for gi,phase in enumerate('UVW'):
    refs=manifest['capacitor_groups'][phase]['fit']+manifest['capacitor_groups'][phase]['dnp']
    for i,r in enumerate(refs[:12]):
        x=13.2+5.2*(i%3);y=[-21.6,3.6,18][gi]+3.6*(i//3)
        place_cap(r,x,y,'B',phase)
    for i,r in enumerate(refs[12:]):
        # Front copper also distributes bulk along the supply entry. Four
        # fitted + two DNP footprints per group form a regular reserve bank.
        x=7.6+5.2*(i%6);y=-25.8+3.6*gi
        place_cap(r,x,y,'F',phase)

for r,x,y,side,group in [('TP104',-22,-23,'F','external bulk'),('TP105',-17.5,-23,'F','external bulk'),('TP101',-22,-19.5,'F','bus probe'),('TP102',-19.5,-19.5,'F','bus probe')]:put(r,x,y,0,side,2,group)

# Continuous ground reference planes on L2 and L5. The power layer is
# deliberately allocated but awaits completion of the high-current routing.
for layer in [p.In1_Cu,p.In4_Cu]:
    z=p.ZONE(b);z.SetLayer(layer);z.SetNet(nets['GND']);z.SetZoneName('GND reference '+p.LayerName(layer));z.SetLocalClearance(p.FromMM(.3));z.SetMinThickness(p.FromMM(.2));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
    outline=z.Outline();outline.NewOutline()
    for cx,cy,start in [(35,35,0),(-35,35,90),(-35,-35,180),(35,-35,270)]:
        for i in range(9):
            a=math.radians(start+i*90/8);outline.Append(p.FromMM(cx+4.5*math.cos(a)),p.FromMM(cy+4.5*math.sin(a)))
    b.Add(z)
b.BuildConnectivity()
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(PROJECT/'ShiroFOC_Manual.kicad_pcb'),b)
pcbpath=PROJECT/'ShiroFOC_Manual.kicad_pcb'
content=pcbpath.read_text()
for ref,oldid in old_can_ids.items():content=content.replace(fps[ref].m_Uuid.AsString(),oldid)
# Nominal symmetric geometry target, NOT a fabricator stackup identifier.
# 1.60 mm including the two 10 um solder masks; final lamination/impedance
# dimensions must be supplied by the board house before fabrication.
start=content.index('(stackup');depth=0;quote=False;escape=False;end=None
for i in range(start,len(content)):
    c=content[i]
    if quote:
        if escape:escape=False
        elif c=='\\':escape=True
        elif c=='"':quote=False
    elif c=='"':quote=True
    elif c=='(':depth+=1
    elif c==')':
        depth-=1
        if depth==0:end=i+1;break
layers=[('F.SilkS','Top Silk Screen',None),('F.Paste','Top Solder Paste',None),('F.Mask','Top Solder Mask',.01),('F.Cu','copper',.07),('dielectric 1','prepreg',.1),('In1.Cu','copper',.0175),('dielectric 2','core',.13),('In2.Cu','copper',.0175),('dielectric 3','prepreg',.91),('In3.Cu','copper',.0175),('dielectric 4','core',.13),('In4.Cu','copper',.0175),('dielectric 5','prepreg',.1),('B.Cu','copper',.07),('B.Mask','Bottom Solder Mask',.01),('B.Paste','Bottom Solder Paste',None),('B.SilkS','Bottom Silk Screen',None)]
stack='(stackup\n'
for name,kind,th in layers:
    stack+='\t\t\t(layer '+json.dumps(name)+' (type '+json.dumps(kind)+')'
    if th is not None:stack+=' (thickness '+str(th)+')'
    if name.startswith('dielectric'):stack+=' (material "FR4") (epsilon_r 4.3) (loss_tangent 0.02)'
    stack+=')\n'
stack+='\t\t\t(copper_finish "None")\n\t\t\t(dielectric_constraints no)\n\t\t)'
content=content[:start]+stack+content[end:]
pcbpath.write_text(content)
(HERE/'placement_manifest.json').write_text(json.dumps({'placements':records,'net_renames':renames,'copper_layers':6,'ground_planes':['In1.Cu','In4.Cu']},indent=2)+'\n')
print('Saved',len(fps),'footprints;',len(records),'placements;',len(b.Zones()),'ground planes.')
