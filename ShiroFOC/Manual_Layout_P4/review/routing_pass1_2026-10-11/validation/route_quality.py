#!/usr/bin/env python3
"""Read-only route length and filled reference-plane sampling audit."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import pcbnew as p

def uid(x):
    return x.m_Uuid.AsString()

def xy(x):
    return [p.ToMM(x.x),p.ToMM(x.y)]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--baseline',type=Path,required=True)
    ap.add_argument('--manifest',type=Path,action='append',default=[])
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    board=p.LoadBoard(str(a.candidate));base=p.LoadBoard(str(a.baseline))
    old={uid(t) for t in base.GetTracks()}
    tracks={uid(t):t for t in board.GetTracks() if uid(t) not in old}
    all_vias=[t for t in board.GetTracks() if isinstance(t,p.PCB_VIA)]
    stack=list(board.GetEnabledLayers().CuStack())
    planes={}
    for z in board.Zones():
        if z.GetNetname()=='GND':
            for layer in z.GetLayerSet().Seq():
                planes.setdefault(layer,[]).append(z.GetFilledPolysList(layer))
    def reference_layer(layer):
        if layer not in stack:return None
        pos=stack.index(layer)
        # Only immediate adjacent copper planes are accepted as references.
        eligible=[x for x in planes if abs(stack.index(x)-pos)==1]
        return eligible[0] if eligible else None
    rows={}
    for identifier,t in tracks.items():
        if isinstance(t,p.PCB_VIA):continue
        length=p.ToMM(t.GetLength())
        layer=t.GetLayer();reference=reference_layer(layer)
        row={'uuid':identifier,'net':t.GetNetname(),'layer':board.GetLayerName(layer),
             'reference_plane':None if reference is None else board.GetLayerName(reference),
             'length_mm':round(length,6),'start_mm':xy(t.GetStart()),'end_mm':xy(t.GetEnd())}
        if reference is None:
            row.update(unsupported_length_mm=length,longest_gap_mm=length)
            rows[identifier]=row;continue
        # 50 um centerline samples. Plane holes near signal vias are explicitly
        # retained in the data rather than being mislabeled as continuous copper.
        start,end=t.GetStart(),t.GetEnd()
        n=max(1,math.ceil(length/.05));step=length/n
        unsupported=0;run=0;maxrun=0;gaps=[];run_start=None
        for index in range(n):
            alpha=(index+.5)/n
            point=p.VECTOR2I(round(start.x+(end.x-start.x)*alpha),round(start.y+(end.y-start.y)*alpha))
            grounded=any(poly.Contains(point) for poly in planes[reference])
            if not grounded:
                unsupported+=step;run+=step
                if run_start is None:run_start=xy(point)
                maxrun=max(maxrun,run)
            elif run_start is not None:
                gaps.append({'from_mm':run_start,'to_mm':xy(point),'length_mm':round(run,4)})
                run=0;run_start=None
        if run_start is not None:gaps.append({'from_mm':run_start,'to_mm':xy(end),'length_mm':round(run,4)})
        row.update(unsupported_length_mm=round(unsupported,6),longest_gap_mm=round(maxrun,6),gaps=gaps)
        rows[identifier]=row
    connections=[]
    seen=set()
    for path in a.manifest:
        data=json.loads(path.read_text())
        for c in data.get('connections',[]):
            ids=c.get('new_items',[])
            if not ids or not any(i in tracks for i in ids):continue
            key=tuple(ids)
            if key in seen:continue
            seen.add(key)
            parts=[rows[i] for i in ids if i in rows]
            length=sum(x['length_mm'] for x in parts)
            dist=c.get('distance_mm',0)
            connections.append({'net':c['net'],'source':c.get('source_ref','')+'.'+c.get('source_pin',''),
                                'target':c.get('target_ref','')+'.'+c.get('target_pin',''),
                                'manifest':str(path),'all_manifest_items_present':all(i in tracks for i in ids),
                                'length_mm':round(length,5),'direct_distance_mm':dist,
                                'detour_ratio':round(length/dist,3) if dist>.01 else None,
                                'vias':sum(isinstance(tracks[i],p.PCB_VIA) for i in ids if i in tracks),
                                'segments':len(parts),'unsupported_length_mm':round(sum(x['unsupported_length_mm'] for x in parts),5),
                                'max_single_segment_gap_mm':max([x['longest_gap_mm'] for x in parts],default=0)})
    bynet={}
    for row in rows.values():
        target=bynet.setdefault(row['net'],{'length_mm':0,'unsupported_length_mm':0,'max_single_segment_gap_mm':0,'layers':set()})
        target['length_mm']+=row['length_mm'];target['unsupported_length_mm']+=row['unsupported_length_mm']
        target['max_single_segment_gap_mm']=max(target['max_single_segment_gap_mm'],row['longest_gap_mm'])
        target['layers'].add(row['layer'])
    for row in bynet.values():
        row['length_mm']=round(row['length_mm'],5);row['unsupported_length_mm']=round(row['unsupported_length_mm'],5)
        row['coverage_percent']=round(100*(1-row['unsupported_length_mm']/row['length_mm']),2) if row['length_mm'] else 100
        row['layers']=sorted(row['layers'])
    significant=[x for x in rows.values() if x['longest_gap_mm']>=.75]
    report={'candidate':str(a.candidate.resolve()),'sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest(),
            'method':'Native filled GND polygon centerline containment sampled every <= 0.05 mm; adjacent layer only. Includes local antipad gaps. Geometric review only; no rise-time, field-solver, or impedance claim.',
            'stackup':[board.GetLayerName(x) for x in stack],
            'ground_plane_regions':{board.GetLayerName(k):[x.OutlineCount() for x in val] for k,val in planes.items()},
            'connections':connections,'new_routes_by_net':bynet,
            'segments_with_reference_void_at_least_0p75mm':significant,
            'all_new_segment_reference_samples':list(rows.values())}
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'connections':len(connections),'significant_reference_void_segments':len(significant),
                      'worst_reference_gaps':sorted(significant,key=lambda x:-x['longest_gap_mm'])[:15],
                      'detours':sorted([c for c in connections if c['detour_ratio'] is not None],key=lambda x:-x['detour_ratio'])[:12]},indent=2))

if __name__=='__main__':main()
