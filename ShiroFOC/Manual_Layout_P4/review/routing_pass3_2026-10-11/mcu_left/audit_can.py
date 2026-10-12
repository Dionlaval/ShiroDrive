from pathlib import Path
import json, math, sys, pcbnew as p
root=Path(__file__).resolve().parent
src=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'can_return/ShiroFOC_Manual.kicad_pcb'
b=p.LoadBoard(str(src)); tracks=list(b.GetTracks()); pads=[q for f in b.GetFootprints() for q in f.Pads()]
uid=lambda q:q.m_Uuid.AsString()
xy=lambda q:[round(p.ToMM(q.x),6),round(p.ToMM(q.y),6)]
can=[q for q in tracks if q.GetNetname()=='CAN_TERM_DISABLE' and q.GetClass()!='PCB_VIA']
canvias=[q for q in tracks if q.GetNetname()=='CAN_TERM_DISABLE' and q.GetClass()=='PCB_VIA']
switches={'PHASE_U','PHASE_V','PHASE_W','Net-(U501-OUT)','Net-(U201-SW)','/5 V / 3.3 V power/U205_SW'}
gate={'GHS1','GHS2','GHS3','GLS1','GLS2','GLS3','BOOTSTRAP1','BOOTSTRAP2','BOOTSTRAP3','Net-(U201-BOOT)'}
groups={'switch_nodes':switches,'gate_bootstrap':gate,'VM':{'VM'}}
cu=list(b.GetEnabledLayers().CuStack());out=p.SHAPE_POLY_SET();b.GetBoardPolygonOutlines(out)
def shapes(q):
    return [(l,q.GetEffectiveShape(l)) for l in cu if q.IsOnLayer(l)]
def clearance(a,c):
    if a.Collide(c,0):return 0.0
    lo=0;hi=p.FromMM(80)
    while hi-lo>1000:
        mid=(lo+hi)//2
        if a.Collide(c,mid):hi=mid
        else:lo=mid
    return p.ToMM(lo)
separation=[]
for category,nets in groups.items():
    obs=[q for q in tracks+pads if q.GetNetname() in nets and out.Contains(q.GetPosition())]
    projected=[];same=[]
    for t in can:
        ts=t.GetEffectiveShape(t.GetLayer())
        for q in obs:
            for layer,qs in shapes(q):
                d=clearance(ts,qs)
                row={'can_uuid':uid(t),'can_layer':t.GetLayerName(),'obstacle_uuid':uid(q),'obstacle_net':q.GetNetname(),'obstacle_layer':b.GetLayerName(layer),'copper_edge_gap_mm':round(d,3)}
                projected.append(row)
                if layer==t.GetLayer():same.append(row)
    separation.append({'category':category,'minimum_xy_projection':min(projected,key=lambda r:r['copper_edge_gap_mm']) if projected else None,'minimum_same_layer':min(same,key=lambda r:r['copper_edge_gap_mm']) if same else None})
ground={l:[z for z in b.Zones() if z.GetNetname()=='GND' and z.IsOnLayer(l)] for l in [4,10]}
refs={0:4,2:10,6:4,8:10}
rows=[]
for t in can:
    a=t.GetStart();c=t.GetEnd();length=p.ToMM(t.GetLength());count=max(1,math.ceil(length/.025));layer=refs[t.GetLayer()]
    uncovered=[];away=[]
    for i in range(count+1):
        q=p.VECTOR2I(round(a.x+(c.x-a.x)*i/count),round(a.y+(c.y-a.y)*i/count))
        if not any(z.HitTestFilledArea(layer,q) for z in ground[layer]):
            uncovered.append(i)
            if not any(math.hypot(q.x-v.GetPosition().x,q.y-v.GetPosition().y)<=p.FromMM(.6) for v in canvias):away.append(i)
    intervals=[]
    for i in away:
        if intervals and i==intervals[-1][-1]+1:intervals[-1].append(i)
        else:intervals.append([i])
    rows.append({'uuid':uid(t),'layer':t.GetLayerName(),'reference':b.GetLayerName(layer),'length_mm':round(length,4),'start':xy(a),'end':xy(c),'sample_step_mm':round(length/count,6),'uncovered_samples':len(uncovered),'uncovered_samples_away_from_same_net_vias':len(away),'uncovered_intervals_away_from_same_net_vias_mm':[round((v[-1]-v[0]+1)*length/count,4) for v in intervals]})
result={'source':str(src),'separation':separation,'ground_reference_sampling':rows,'notes':'Native copper-shape distances. XY projection also compares copper on different layers and is not a DRC clearance. Ground reference sampled along track centre every <=0.025 mm; own via antipads excluded within0.6mm. This is geometry evidence, not an EMC simulation.'}
output=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else src.parent/'route_audit.json'
output.write_text(json.dumps(result,indent=2))
print(json.dumps({'separation':separation,'reference_gaps':[r for r in rows if r['uncovered_samples_away_from_same_net_vias']]},indent=2))
