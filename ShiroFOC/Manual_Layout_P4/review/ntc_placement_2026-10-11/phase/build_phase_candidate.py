"""Read-only source / isolated phase-NTC resistor relocation candidate."""
from pathlib import Path
import pcbnew as p
import json, shutil, hashlib, math

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'before'
for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:
    if (SOURCE/name).exists():shutil.copy2(SOURCE/name,HERE/name)
if not (HERE/'libs').exists():(HERE/'libs').symlink_to(SOURCE/'libs',target_is_directory=True)
src=SOURCE/'ShiroFOC_Manual.kicad_pcb'
b=p.LoadBoard(str(src));fps={f.GetReference():f for f in b.GetFootprints()}
outline=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(outline)
def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def xy(v):return [round(p.ToMM(v.x),6),round(p.ToMM(v.y),6)]
def uid(q):return q.m_Uuid.AsString()
def state(f):
    return dict(uuid=uid(f),position=xy(f.GetPosition()),angle=f.GetOrientationDegrees(),side='B' if f.IsFlipped() else 'F',
                reference_field=dict(position=xy(f.Reference().GetPosition()),angle=f.Reference().GetTextAngle().AsDegrees(),size=xy(f.Reference().GetTextSize())),
                pad_nets={uid(q):dict(number=q.GetNumber(),net=q.GetNetname()) for q in f.Pads()},path=f.GetPath().AsString())
initial={r:state(f) for r,f in fps.items()}
positions={}
for suffix,y in [(1,-1.55),(2,-.5),(3,.55)]:
    positions['R70'+str(suffix)]=(-16.4,y,0)
    positions['R71'+str(suffix)]=(-14.0,y,0)
for r,(x,y,a) in positions.items():
    f=fps[r]
    assert f.IsFlipped()
    f.SetOrientationDegrees(a);f.SetPosition(vec(x,y))
    f.Reference().SetPosition(vec(-19.4 if r.startswith('R70') else -11.8,y))
    f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
    f.Reference().SetTextSize(vec(.8,.8))

def bbox(obj):
    q=obj.GetBoundingBox();return [p.ToMM(q.GetLeft()),p.ToMM(q.GetTop()),p.ToMM(q.GetRight()),p.ToMM(q.GetBottom())]
def envelope(f):
    cy=p.B_CrtYd if f.IsFlipped() else p.F_CrtYd
    boxes=[bbox(q) for q in f.GraphicalItems() if q.GetLayer()==cy]
    if not boxes:
        q=f.GetBoundingBox(False,False);return [p.ToMM(q.GetLeft()),p.ToMM(q.GetTop()),p.ToMM(q.GetRight()),p.ToMM(q.GetBottom())]
    return [min(x[0] for x in boxes),min(x[1] for x in boxes),max(x[2] for x in boxes),max(x[3] for x in boxes)]
def overlap(a,c,gap=0):return a[0]<c[2]+gap and a[2]+gap>c[0] and a[1]<c[3]+gap and a[3]+gap>c[1]
collisions=[]
for r in positions:
    f=fps[r];bb=envelope(f)
    if not all(outline.Contains(vec(x,y)) for x in [bb[0],bb[2]] for y in [bb[1],bb[3]]):collisions.append([r,'edge'])
    for rr,q in fps.items():
        if r==rr:continue
        if f.IsFlipped()==q.IsFlipped() and overlap(bb,envelope(q)):collisions.append([r,rr,'courtyard/body'])
        elif f.IsFlipped()!=q.IsFlipped():
            for pad in q.Pads():
                if pad.GetAttribute() in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH] and overlap(bb,bbox(pad),.1):collisions.append([r,rr+'.'+pad.GetNumber(),'through-hole/pad'])

manifest=dict(source=str(src),source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
              moved={r:dict(before=initial[r],after=state(fps[r])) for r in positions},
              unchanged_references=sorted(set(fps)-set(positions)),removed_copper=[],added_copper=[],geometry_collisions=collisions,
              rationale='Three aligned bias/series resistor rows in the quiet USB/CAN service-side gap. ADC capacitors and phase thermistors stay fixed; the series-resistor/filter-cap path requires later routing.')
assert all(initial[r]['pad_nets']==state(fps[r])['pad_nets'] and initial[r]['path']==state(fps[r])['path'] for r in positions)
p.SaveBoard(str(HERE/'ShiroFOC_Manual.kicad_pcb'),b)
(HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'moved':positions,'geometry_collisions':collisions},indent=2))
