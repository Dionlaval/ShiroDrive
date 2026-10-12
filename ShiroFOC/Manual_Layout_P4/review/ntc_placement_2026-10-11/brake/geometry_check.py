"""Check moved pads against every F.Cu pad/track/via, including same-net copper."""
from pathlib import Path
import pcbnew as p
import json

HERE=Path(__file__).resolve().parent
b=p.LoadBoard(str(HERE/'ShiroFOC_Manual.kicad_pcb'))
fps={f.GetReference():f for f in b.GetFootprints()}
moving=['R511','R512']
def uid(q):return q.m_Uuid.AsString()
objects=[]
for f in b.GetFootprints():
    for q in f.Pads():
        if q.IsOnLayer(p.F_Cu):objects.append((q, f.GetReference()+'.'+q.GetNumber()))
for q in b.GetTracks():
    if q.IsOnLayer(p.F_Cu):objects.append((q,q.GetClass()+':'+uid(q)))

violations=[];nearest=[]
for r in moving:
    for pad in fps[r].Pads():
        shape=pad.GetEffectiveShape(p.F_Cu)
        ranked=[]
        for q,name in objects:
            if uid(q)==uid(pad):continue
            other=q.GetEffectiveShape(p.F_Cu)
            if shape.Collide(other,p.FromMM(.2)):
                violations.append(dict(pad=r+'.'+pad.GetNumber(),other=name,net=q.GetNetname(),same_net=pad.GetNetname()==q.GetNetname()))
            if not shape.Collide(other,p.FromMM(2)):continue
            lo,hi=0,p.FromMM(2)
            while hi-lo>1000:
                mid=(lo+hi)//2
                if shape.Collide(other,mid):hi=mid
                else:lo=mid
            ranked.append(dict(other=name,net=q.GetNetname(),same_net=pad.GetNetname()==q.GetNetname(),gap_mm=round(p.ToMM(lo),3)))
        nearest.append(dict(pad=r+'.'+pad.GetNumber(),closest=sorted(ranked,key=lambda x:x['gap_mm'])[:4]))

def bbox(q):
    bb=q.GetBoundingBox();return [bb.GetLeft(),bb.GetTop(),bb.GetRight(),bb.GetBottom()]
def envelope(f):
    layer=p.B_CrtYd if f.IsFlipped() else p.F_CrtYd
    boxes=[bbox(q) for q in f.GraphicalItems() if q.GetLayer()==layer]
    if not boxes:return bbox(f)
    return [min(q[0] for q in boxes),min(q[1] for q in boxes),max(q[2] for q in boxes),max(q[3] for q in boxes)]
def overlap(a,c):return a[0]<c[2] and a[2]>c[0] and a[1]<c[3] and a[3]>c[1]
outline=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(outline)
courtyard=[]
for r in moving:
    f=fps[r];bb=envelope(f)
    if not all(outline.Contains(p.VECTOR2I(x,y)) for x in [bb[0],bb[2]] for y in [bb[1],bb[3]]):courtyard.append([r,'board_edge'])
    for rr,q in fps.items():
        if r!=rr and f.IsFlipped()==q.IsFlipped() and overlap(bb,envelope(q)):courtyard.append([r,rr])
result=dict(required_copper_gap_mm=.2,all_nets_including_same_net=True,copper_violations=violations,courtyard_or_edge_collisions=courtyard,nearest_copper=nearest)
(HERE/'geometry.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
assert not violations and not courtyard
