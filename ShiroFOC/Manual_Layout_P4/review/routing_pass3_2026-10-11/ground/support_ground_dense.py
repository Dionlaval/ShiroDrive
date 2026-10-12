"""Candidate-only local GND stitches. Run with KiCad's pcbnew Python.

Usage: python add_ground_stitches.py SRC.kicad_pcb DST.kicad_pcb [--refs C305,U701]
Signal returns only: add --signal-returns --returns-only --baseline BEFORE.kicad_pcb
Includes reused vias whose connected signal layers now change GND reference.
B-to-L4 transitions retaining L5 reference are skipped. Optional --force-signal-vias UUIDS.json.
Never overwrite SRC. Emits DST.ground_manifest.json for per-group pruning.
Does not refill zones: source fills are used only to find existing plane copper;
the combined candidate must be refilled and checked by native KiCad DRC.
"""
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
import pcbnew as p

M = p.FromMM
def uid(o): return o.m_Uuid.AsString()
def xy(v): return [round(p.ToMM(v.x), 6), round(p.ToMM(v.y), 6)]
def vec(x, y): return p.VECTOR2I(int(round(x)), int(round(y)))
def distance(a, b): return math.hypot(a.x-b.x, a.y-b.y)
def box(shape):
    q=shape.BBox()
    return (q.GetLeft(),q.GetTop(),q.GetRight(),q.GetBottom())
def near(a,b,c): return a[0]-c<=b[2] and a[2]+c>=b[0] and a[1]-c<=b[3] and a[3]+c>=b[1]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('src',type=Path);ap.add_argument('dst',type=Path)
    ap.add_argument('--refs',default='',help='Optional comma-separated subset of supported references')
    ap.add_argument('--signal-returns',action='store_true',help='Add adjacent GND plane-transition vias for new signal vias')
    ap.add_argument('--returns-only',action='store_true',help='Skip capacitor/IC ground stubs; requires --signal-returns')
    ap.add_argument('--baseline',type=Path,help='Original board used to identify new vias and reused vias whose connected signal layers changed')
    ap.add_argument('--force-signal-vias',type=Path,help='Optional JSON list of via UUIDs (or object signal_via_uuids) to audit even when unchanged from baseline')
    args=ap.parse_args()
    assert args.src.resolve()!=args.dst.resolve(), 'Candidate destination must differ from source'
    if args.returns_only and not args.signal_returns:ap.error('--returns-only requires --signal-returns')
    if args.signal_returns and not args.baseline:ap.error('--signal-returns requires --baseline')
    # Same-basename project load is needed for custom net-class assignment. Geometry
    # checks below conservatively use .20 default and .50 for known power nets.
    mgr=p.SETTINGS_MANAGER();project=None
    pro=args.src.with_suffix('.kicad_pro')
    if pro.exists():
        mgr.LoadProject(str(pro.resolve()));project=mgr.GetProject(str(pro.resolve()))
    b=p.LoadBoard(str(args.src.resolve()))
    if project:
        b.SetProject(project);b.SynchronizeNetsAndNetClasses(False)
    layers=list(b.GetEnabledLayers().CuStack())
    u4=next(f for f in b.GetFootprints()if f.GetReference()=='U4');u4.BuildCourtyardCaches();localcourt=u4.GetCourtyard(p.F_Cu)
    def local_clearance(a,sa,q,sq):
        if localcourt.Collide(sa,0) and localcourt.Collide(sq,0):return M(.150001)
        return M(.500001 if power(q.GetNetname()) else .200001)
    planes=[(z,l) for z in b.Zones() if z.GetNetname()=='GND' for l in z.GetLayerSet().CuStack() if l not in (p.F_Cu,p.B_Cu)]
    assert planes,'No existing filled internal GND zones'
    outline=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(outline)
    allpads=[q for f in b.GetFootprints() for q in f.Pads()]
    tracks=list(b.GetTracks())
    edges=[d.GetEffectiveShape(p.Edge_Cuts) for d in b.GetDrawings() if d.GetLayer()==p.Edge_Cuts]
    edges=[(s,box(s)) for s in edges]
    objects={l:[] for l in layers}
    pads_by_layer={l:[] for l in layers}
    holes=[];added=[]
    def power(net):
        return net=='VM' or net.startswith('PHASE_') or net=='BRK_SW' or net=='Net-(D504-A)' or 'LS_SOURCE_' in net
    def register(o):
        for l in layers:
            if o.IsOnLayer(l):
                s=o.GetEffectiveShape(l)
                objects[l].append((o,s,box(s)))
                if o.GetClass()=='PAD':pads_by_layer[l].append((o,s,box(s)))
        drill=(o.GetDrillSize().x if o.GetClass()=='PAD' else o.GetDrillValue() if o.GetClass()=='PCB_VIA' else 0)
        if drill:
            s=o.GetEffectiveHoleShape();holes.append((o,s,box(s)))
    for o in allpads+tracks:register(o)
    def in_plane(point): return any(z.HitTestFilledArea(l,point) for z,l in planes)
    plane_layers=sorted(set(l for z,l in planes))
    def in_all_planes(point):
        return all(any(z.HitTestFilledArea(l,point) for z,ll in planes if ll==l) for l in plane_layers)
    def copper_edge_ok(shape, points):
        if not all(outline.Contains(q) for q in points):return False
        bb=box(shape)
        return not any(near(bb,eb,M(.500001)) and shape.Collide(es,M(.500001)) for es,eb in edges)
    def via_valid(v):
        point=v.GetPosition();shape=v.GetEffectiveShape(p.F_Cu);bb=box(shape)
        if not in_plane(point) or not copper_edge_ok(shape,[point]):return False
        # No via-in-pad, including GND pads and pads on the opposite board side.
        for l in layers:
            for q,s,qb in pads_by_layer[l]:
                if near(bb,qb,1) and shape.Collide(s,1):return False
            for q,s,qb in objects[l]:
                if q.GetNetname()=='GND':continue
                clearance=local_clearance(v,shape,q,s)
                if near(bb,qb,clearance) and shape.Collide(s,clearance):return False
        hole=v.GetEffectiveHoleShape();hb=box(hole)
        if any(near(hb,qb,M(.450001)) and hole.Collide(s,M(.450001)) for q,s,qb in holes):return False
        return True
    def path_variants(a,c):
        dx=c.x-a.x;dy=c.y-a.y;ax=abs(dx);ay=abs(dy)
        if not dx or not dy or ax==ay:return [[a,c]]
        sx=1 if dx>0 else -1;sy=1 if dy>0 else -1
        if ax>ay:return [[a,vec(c.x-sx*ay,a.y),c],[a,vec(a.x+sx*ay,c.y),c]]
        return [[a,vec(a.x,c.y-sy*ax),c],[a,vec(c.x,a.y+sy*ax),c]]
    def build_path(a,c,layer,net):
        for width in [.254,.1524]:
            for pts in path_variants(a,c):
                length=sum(distance(x,y) for x,y in zip(pts,pts[1:]))
                if length>M(1.500001):continue
                result=[];okay=True
                for x,y in zip(pts,pts[1:]):
                    if distance(x,y)<1:continue
                    t=p.PCB_TRACK(b);t.SetStart(x);t.SetEnd(y);t.SetWidth(M(width));t.SetLayer(layer);t.SetNetCode(net)
                    s=t.GetEffectiveShape(layer);bb=box(s)
                    if not copper_edge_ok(s,[x,y]):okay=False;break
                    for q,qs,qb in objects[layer]:
                        if q.GetNetname()=='GND':continue
                        clearance=local_clearance(t,s,q,qs)
                        if near(bb,qb,clearance) and s.Collide(qs,clearance):okay=False;break
                    if not okay:break
                    # Drill voids on other nets and NPTH holes remain obstacles.
                    for q,hs,hb in holes:
                        if q.GetNetname()=='GND':continue
                        if near(bb,hb,M(.200001)) and s.Collide(hs,M(.200001)):okay=False;break
                    if not okay:break
                    result.append(t)
                if okay:return result,length
        return None,None
    # Caps whose returns form small support/filter loops. Exclude switching
    # regulators, bulk DC-link/output capacitors and all VM-connected parts.
    caps=(['C'+str(x) for x in range(301,311)]+['C312','C313','C314','C108']+
          ['C503','C504','C505']+['C'+str(x) for x in range(601,608)]+
          ['C701','C702','C711','C712','C713','C801','C802']+
          ['C'+str(x) for x in range(901,905)]+['C208','C209','C211','C212','C213'])
    ics=['U4','U601','U701','U901','U202','U801','U602','U603','U604','U502','U204']
    refs=caps+ics+['Y301']+[f.GetReference() for f in b.GetFootprints() if f.GetReference().startswith('R')]+['Q301','Q801','D801','J801','J802','J601','J502','TH701','TH702','TH703']
    if args.refs:refs=[r for r in refs if r in set(args.refs.split(','))]
    if args.returns_only:refs=[]
    fps={f.GetReference():f for f in b.GetFootprints()}
    b.BuildConnectivity()
    def connected_plane(q):
        # Traverse physical same-net contacts, not all pads sharing a net name.
        connectivity=b.GetConnectivity();seen=set();todo=[q]
        while todo:
            curr=todo.pop();u=uid(curr)
            if u in seen:continue
            seen.add(u)
            if curr.GetClass() in ('PCB_VIA','PAD') and any(curr.IsOnLayer(l) for z,l in planes) and in_plane(curr.GetPosition()):return True
            todo.extend(t for t in connectivity.GetConnectedTracks(curr) if uid(t) not in seen and t.GetNetname()=='GND')
            todo.extend(t for t in connectivity.GetConnectedPads(curr) if uid(t) not in seen and t.GetNetname()=='GND')
        return False
    groups=[];skipped=[]
    for ref in refs:
        f=fps.get(ref)
        if f is None:continue
        # No off-board staging parts or DNP tuning footprints.
        if not outline.Contains(f.GetPosition()) or f.GetAttributes() & p.FP_DNP:continue
        for pad in f.Pads():
            if pad.GetNetname()!='GND':continue
            tag=ref+'.'+pad.GetNumber()
            if max(pad.GetSize().x,pad.GetSize().y)>M(2):
                skipped.append(dict(pad=tag,reason='large exposed/thermal pad intentionally excluded'));continue
            if connected_plane(pad):
                skipped.append(dict(pad=tag,reason='already reaches existing GND plane'));continue
            layer=f.GetLayer();start=pad.GetPosition();accepted=None;via=None;reuse=None
            existing=[q for q in list(b.GetTracks()) if q.GetClass()=='PCB_VIA' and q.GetNetname()=='GND' and q.IsOnLayer(layer) and distance(start,q.GetPosition())<=M(1.5) and in_plane(q.GetPosition())]
            for q in sorted(existing,key=lambda q:distance(start,q.GetPosition())):
                result,length=build_path(start,q.GetPosition(),layer,pad.GetNetCode())
                if result is not None:accepted=result;reuse=q;break
            if accepted is None:
                points=[]
                for ix in range(-30,31):
                    for iy in range(-30,31):
                        dx,dy=M(ix*.05),M(iy*.05)
                        if M(.4)<=math.hypot(dx,dy)<=M(1.5):points.append(vec(start.x+dx,start.y+dy))
                points.sort(key=lambda q:distance(start,q))
                for target in points:
                    v=p.PCB_VIA(b);v.SetPosition(target);v.SetWidth(M(.5));v.SetDrill(M(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(pad.GetNetCode())
                    if not via_valid(v):continue
                    result,length=build_path(start,target,layer,pad.GetNetCode())
                    if result is not None:accepted=result;via=v;break
            if accepted is None:
                skipped.append(dict(pad=tag,reason='no legal <=1.5 mm local plane stitch'));continue
            members=([via] if via else [])+accepted
            for q in members:b.Add(q);added.append(q);register(q)
            b.BuildConnectivity()
            groups.append(dict(group_id='ground_'+ref+'_'+pad.GetNumber(),kind='pad_ground_stitch',pad=tag,pad_uuid=uid(pad),net='GND',layer=b.GetLayerName(layer),start_mm=xy(start),end_mm=xy((via or reuse).GetPosition()),stub_length_mm=round(p.ToMM(length),6),added_uuids=[uid(q) for q in members],new_items=[uid(q) for q in members],added_via_uuid=uid(via) if via else None,reused_via_uuid=uid(reuse) if reuse else None,track_widths_mm=sorted(set(round(p.ToMM(q.GetWidth()),6) for q in accepted))))
    return_audit=None
    if args.signal_returns:
        assert len(plane_layers)>=2,'Signal return mode requires at least two filled internal GND layers'
        baseline=p.LoadBoard(str(args.baseline.resolve()))
        old_tracks=list(baseline.GetTracks())
        old_pads=[q for f in baseline.GetFootprints() for q in f.Pads()]
        old_ids={uid(q) for q in old_tracks}
        old_vias={uid(q):q for q in old_tracks if q.GetClass()=='PCB_VIA'}
        current_tracks=list(b.GetTracks())
        forced=set()
        if args.force_signal_vias:
            raw=json.loads(args.force_signal_vias.read_text())
            if isinstance(raw,dict):raw=raw.get('signal_via_uuids',[])
            assert isinstance(raw,list) and all(isinstance(x,str) for x in raw), 'Forced signal vias must be a UUID list'
            forced=set(raw)
            assert forced<={uid(q) for q in current_tracks if q.GetClass()=='PCB_VIA'}, 'Forced UUID not present as candidate via'
        def touching_layers(via,rows,pad_rows):
            touched={q.GetLayer() for q in rows if q.GetClass()!='PCB_VIA' and q.GetNetname()==via.GetNetname() and via.GetEffectiveShape(q.GetLayer()).Collide(q.GetEffectiveShape(q.GetLayer()),0)}
            for pad in pad_rows:
                if pad.GetNetname()!=via.GetNetname():continue
                for layer in layers:
                    if pad.IsOnLayer(layer) and via.GetEffectiveShape(layer).Collide(pad.GetEffectiveShape(layer),0):touched.add(layer)
            return touched
        def ground_references(signal_layers):
            return {layer for layer in plane_layers if any(abs(layers.index(layer)-layers.index(signal_layer))==1 for signal_layer in signal_layers)}
        transition_info={}
        def is_signal(q):
            if q.GetClass()!='PCB_VIA' or q.GetViaType()!=p.VIATYPE_THROUGH:return False
            touched=touching_layers(q,current_tracks,allpads)
            prior=touching_layers(old_vias[uid(q)],old_tracks,old_pads) if uid(q) in old_vias else set()
            refs=ground_references(touched)
            if uid(q) not in forced:
                if uid(q) in old_ids and touched==prior:return False
                if len(refs)<2:return False
            transition_info[uid(q)]={'new_via':uid(q) not in old_ids,'forced':uid(q) in forced,'previous_signal_layers':[b.GetLayerName(x) for x in sorted(prior)],'current_signal_layers':[b.GetLayerName(x) for x in sorted(touched)],'reference_layers':[b.GetLayerName(x) for x in sorted(refs)]}
            n=q.GetNetname()
            if not n or n.startswith('unconnected-') or n=='GND' or power(n):return False
            if n in ('3V3','VCC','VDDA','VREF+') or n.startswith('5V') or n.endswith('/EXT_VCC'):return False
            if n.startswith(('GHS','GLS','HS_RETURN_','BOOTSTRAP')) or n in ('Net-(U1-GH)','Net-(U2-GH)','Net-(U3-GH)','Net-(U501-OUT)'):return False
            if n in ('Net-(U201-SW)','Net-(U201-BOOT)','Net-(U201-VCC)') or n.endswith(('/U205_SW','/U205_AGND')):return False
            return outline.Contains(q.GetPosition())
        signals=[q for q in b.GetTracks() if is_signal(q)]
        ground_vias=[q for q in b.GetTracks() if q.GetClass()=='PCB_VIA' and q.GetNetname()=='GND' and all(q.IsOnLayer(l) for l in plane_layers) and in_all_planes(q.GetPosition())]
        gnd_code=next(q.GetNetCode() for q in allpads if q.GetNetname()=='GND')
        def nearest_gnd(q):
            if not ground_vias:return None,None
            v=min(ground_vias,key=lambda v:distance(q.GetPosition(),v.GetPosition()))
            return v,distance(q.GetPosition(),v.GetPosition())
        before=[]
        for q in signals:
            gv,d=nearest_gnd(q)
            before.append(dict(signal_via_uuid=uid(q),net=q.GetNetname(),position_mm=xy(q.GetPosition()),nearest_ground_mm=round(p.ToMM(d),6) if d is not None else None,transition=transition_info[uid(q)]))
        # Address the largest return-path gaps first. One new GND via may cover
        # more than one signal transition; re-evaluate after every addition.
        signals.sort(key=lambda q:nearest_gnd(q)[1] or float('inf'),reverse=True)
        for signal in signals:
            gv,gdist=nearest_gnd(signal)
            if gdist is not None and gdist<=M(1.5):
                skipped.append(dict(signal_via_uuid=uid(signal),net=signal.GetNetname(),reason='existing GND via joins all reference planes within 1.5 mm',ground_via_uuid=uid(gv),distance_mm=round(p.ToMM(gdist),6)))
                continue
            start=signal.GetPosition();accepted=None
            # A via-only return transition needs no angled surface stub. Search
            # a 50um grid in rings, requiring the exact final distance .8..1.5.
            seen=set();points=[]
            for radius in [.8+.05*k for k in range(15)]:
                for step in range(32):
                    angle=2*math.pi*step/32
                    xx=round((start.x+M(radius)*math.cos(angle))/M(.05))*M(.05)
                    yy=round((start.y+M(radius)*math.sin(angle))/M(.05))*M(.05)
                    point=vec(xx,yy);key=(point.x,point.y);d=distance(start,point)
                    if key not in seen and M(.8)<=d<=M(1.5):points.append(point);seen.add(key)
            points.sort(key=lambda q:distance(start,q))
            for target in points:
                if not in_all_planes(target):continue
                v=p.PCB_VIA(b);v.SetPosition(target);v.SetWidth(M(.5));v.SetDrill(M(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(gnd_code)
                if via_valid(v):accepted=v;break
            if accepted is None:
                skipped.append(dict(signal_via_uuid=uid(signal),net=signal.GetNetname(),position_mm=xy(start),reason='no legal .8..1.5 mm return via contacting every GND reference plane',nearest_ground_mm=round(p.ToMM(gdist),6) if gdist is not None else None))
                continue
            b.Add(accepted);added.append(accepted);register(accepted);ground_vias.append(accepted)
            groups.append(dict(group_id='signal_return_'+uid(signal),kind='signal_return_via',net='GND',signal_net=signal.GetNetname(),signal_via_uuid=uid(signal),signal_position_mm=xy(start),end_mm=xy(accepted.GetPosition()),distance_to_signal_mm=round(p.ToMM(distance(start,accepted.GetPosition())),6),required_ground_planes=[b.GetLayerName(l) for l in plane_layers],all_plane_fills_contain_site=True,added_uuids=[uid(accepted)],new_items=[uid(accepted)],added_via_uuid=uid(accepted),stub_length_mm=0,track_widths_mm=[]))
        after=[]
        for signal in signals:
            gv,d=nearest_gnd(signal)
            after.append(dict(signal_via_uuid=uid(signal),net=signal.GetNetname(),position_mm=xy(signal.GetPosition()),nearest_ground_via_uuid=uid(gv) if gv else None,nearest_ground_mm=round(p.ToMM(d),6) if d is not None else None,covered_within_1_5mm=d is not None and d<=M(1.5)))
        return_audit=dict(baseline=str(args.baseline.resolve()),baseline_sha256=hashlib.sha256(args.baseline.read_bytes()).hexdigest(),new_signal_vias=sum(transition_info[uid(q)]['new_via'] for q in signals),reused_signal_vias=sum(not transition_info[uid(q)]['new_via'] for q in signals),audited_signal_vias=len(signals),required_ground_planes=[b.GetLayerName(l) for l in plane_layers],before=before,after=after,uncovered=[row for row in after if not row['covered_within_1_5mm']])
    args.dst.parent.mkdir(parents=True,exist_ok=True)
    p.SaveBoard(str(args.dst.resolve()),b)
    report=dict(source=str(args.src.resolve()),source_sha256=hashlib.sha256(args.src.read_bytes()).hexdigest(),destination=str(args.dst.resolve()),groups=groups,skipped=skipped,signal_returns=return_audit,added_counts=dict(Counter(q.GetClass() for q in added)),checks=dict(native_effective_shapes=True,all_enabled_copper_layers_for_vias=True,min_default_clearance_mm=.2,min_power_clearance_mm=.5,min_hole_web_mm=.45,min_copper_edge_mm=.5,max_stub_length_mm=1.5,no_new_via_in_pad=True,plane_refill_and_native_drc_required=True))
    manifest=args.dst.with_suffix('.ground_manifest.json');manifest.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(groups=len(groups),added=report['added_counts'],skipped=len(skipped),manifest=str(manifest))))

if __name__=='__main__':main()
