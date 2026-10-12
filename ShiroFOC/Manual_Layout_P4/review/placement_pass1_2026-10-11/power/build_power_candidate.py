"""Isolated power support placement candidate; no writes to the working PCB."""
from pathlib import Path
import pcbnew as p
import json, hashlib, shutil, math

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
SRC=PROJECT/'ShiroFOC_Manual.kicad_pcb'
BASE=HERE/'baseline.kicad_pcb'
if not BASE.exists(): shutil.copy2(SRC,BASE)
for ext in ['kicad_pro','kicad_dru']:
    shutil.copy2(PROJECT/f'ShiroFOC_Manual.{ext}', HERE/f'candidate.{ext}')
b=p.LoadBoard(str(BASE))
fps={f.GetReference():f for f in b.GetFootprints()}
def xy(v):return [round(p.ToMM(v.x),6),round(p.ToMM(v.y),6)]
def state(f):return dict(xy=xy(f.GetPosition()),angle=f.GetOrientationDegrees(),side='B' if f.IsFlipped() else 'F',uuid=f.m_Uuid.AsString(),
                        reference_field=dict(xy=xy(f.Reference().GetPosition()),angle=f.Reference().GetTextAngle().AsDegrees(),size=xy(f.Reference().GetTextSize()),visible=f.Reference().IsVisible()))
before={r:state(f) for r,f in fps.items()}
positions={
 'C3': (8.55,2.50,180,'B'),
 'C7': (8.55,10.00,180,'B'),
 'C11':(8.55,17.50,180,'B'),
 'TH701':(15.85,1.2,90,'B'),
 'TH702':(15.85,8.7,90,'B'),
 'TH703':(15.85,16.2,90,'B'),
 'C101':(12.85,-4.4,180,'F'),
 'C102':(8.55,-3.5,180,'B'),
 'C103':(8.55,5.85,180,'B'),
 'C110':(8.55,13.35,180,'B'),
}
for r,(x,y,a,side) in positions.items():
    f=fps[r]
    if f.IsFlipped()!=(side=='B'): f.Flip(f.GetPosition(),False)
    f.SetOrientationDegrees(a)
    f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))

# Keep the newly placed capacitor references clear of adjacent pads and bodies.
for r,x,y in [('C101',9.8,-4.4),('C103',5.6,5.85),('C110',5.6,13.35)]:
    text=fps[r].Reference()
    text.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
    text.SetTextAngle(p.EDA_ANGLE(90,p.DEGREES_T))
    text.SetTextSize(p.VECTOR2I(p.FromMM(.8),p.FromMM(.8)))

removals=json.loads((HERE/'guide_removals.json').read_text()) if (HERE/'guide_removals.json').exists() else {}
removed=[]
to_remove=[]
for t in list(b.GetTracks()):
    uid=t.m_Uuid.AsString()
    if uid in removals:
        removed.append(dict(uuid=uid,net=t.GetNetname(),start=xy(t.GetStart()),end=xy(t.GetEnd()),
                            layer=t.GetLayerName(),width_mm=p.ToMM(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth()),**removals[uid]))
        to_remove.append(t)

def box(q):
    z=q.GetBoundingBox()
    return [p.ToMM(z.GetLeft()),p.ToMM(z.GetTop()),p.ToMM(z.GetRight()),p.ToMM(z.GetBottom())]
def bounds(f):
    boxes=[box(q) for q in f.GraphicalItems() if q.GetLayer()==(p.B_CrtYd if f.IsFlipped() else p.F_CrtYd)]
    if not boxes: boxes=[box(q) for q in f.Pads()]
    return [min(z[0] for z in boxes),min(z[1] for z in boxes),max(z[2] for z in boxes),max(z[3] for z in boxes)]
def overlap(a,c,margin=0):
    return a[0]<c[2]+margin and a[2]+margin>c[0] and a[1]<c[3]+margin and a[3]+margin>c[1]

collisions=[]
for r in positions:
    f=fps[r];bb=bounds(f)
    if min(bb)<-22.25 or max(bb)>22.25:collisions.append([r,'edge',bb])
    for rr,q in fps.items():
        if r==rr:continue
        if rr in ['J1','J101']:
            for pad in q.Pads():
                if pad.GetNumber() and overlap(bb,box(pad),.2):collisions.append([r,rr+'.'+pad.GetNumber(),'wire solder pad'])
            continue
        if f.IsFlipped()==q.IsFlipped() and overlap(bb,bounds(q)):
            collisions.append([r,rr,'courtyard/body'])
        elif f.IsFlipped()!=q.IsFlipped():
            for pad in q.Pads():
                if pad.GetAttribute() in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH] and overlap(bb,box(pad),.05):
                    collisions.append([r,rr+'.'+pad.GetNumber(),'opposite plated/hole'])

manifest=dict(source=str(SRC),baseline_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),
 source_sha256_at_build=hashlib.sha256(SRC.read_bytes()).hexdigest(),
 moved_footprints={r:{'from':before[r],'to':state(fps[r])} for r in positions},
 removed_copper=removed,added_copper=[],
 unchanged_core=['U1','U2','U3','R3','R1','R5','R2','R4','R6','C1','C2','C5','C6','C9','C10','C4','C8','C12'],
 deferred=['R415','C413','R425','C423','R435','C433','C120','C130','C140','C150','C160'],
 filter_resistors_parent_owned=['R701','R702','R703','R711','R712','R713'],
 geometry_conflicts=collisions,
 capacitor_pad_geometry={r:[dict(number=q.GetNumber(),xy=xy(q.GetPosition()),net=q.GetNetname()) for q in fps[r].Pads()] for r in positions if r.startswith('C')})
for t in to_remove: b.Remove(t)
p.SaveBoard(str(HERE/'candidate.kicad_pcb'),b)
(HERE/'move_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'moved':list(positions),'conflicts':collisions,'cap_pads':manifest['capacitor_pad_geometry']},indent=2))
