"""Check prior pad connectivity using individual filled-zone polygons.

Copper-only via/track/via bridges are traversed too. Separate polygons do not
become connected merely because they share a net name or zone UUID.
"""
from pathlib import Path
import pcbnew as p
import json, sys
plan=Path(__file__).resolve().parents[2]/'routing_pass1_2026-10-11/planned_groups.json'
selected={n for group in json.loads(plan.read_text()).values() for n in group}
uid=lambda q:q.m_Uuid.AsString()

def analyse(path, unique_pad_labels=False):
    b=p.LoadBoard(str(path));b.BuildConnectivity();conn=b.GetConnectivity()
    outline=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(outline)
    pads={};tracks=list(b.GetTracks());result={};plane_summary={}
    for f in b.GetFootprints():
        if not outline.Contains(f.GetPosition()) or f.IsDNP() or 'DNP' in f.GetValue().upper():continue
        for q in f.Pads():
            if q.GetNetname():pads.setdefault(q.GetNetname(),[]).append(q)
    for net,pp in pads.items():
        names={uid(q):f'{q.GetParentFootprint().GetReference()}.{q.GetNumber()}' for q in pp}
        if unique_pad_labels:
            names={identifier:label+'#'+identifier for identifier,label in names.items()}
        islands=[]
        for z in b.Zones():
            if z.GetNetname()!=net or z.GetIsRuleArea():continue
            for layer in z.GetLayerSet().CuStack():
                fill=z.GetFilledPolysList(layer)
                for index in range(fill.OutlineCount()):
                    islands.append({'key':(uid(z),layer,index),'shape':fill.UnitSet(index),'layer':layer})
        parent=list(range(len(islands)))
        def find(i):
            while parent[i]!=i:
                parent[i]=parent[parent[i]];i=parent[i]
            return i
        def union(i,j):parent[find(j)]=find(i)
        for i,left in enumerate(islands):
            for j in range(i):
                right=islands[j]
                if left['layer']==right['layer'] and left['shape'].Collide(right['shape'],0):union(i,j)
        seen=set();groups=[]
        seeds=pp+[t for t in tracks if t.GetNetname()==net]
        for seed in seeds:
            if uid(seed) in seen:continue
            todo=[seed];members=set();contacts=set()
            while todo:
                q=todo.pop();identifier=uid(q)
                if identifier in seen:continue
                seen.add(identifier)
                if identifier in names:members.add(names[identifier])
                for index,island in enumerate(islands):
                    layer=island['layer']
                    if q.IsOnLayer(layer) and island['shape'].Collide(q.GetEffectiveShape(layer),0):contacts.add(index)
                todo.extend(t for t in list(conn.GetConnectedTracks(q))+list(conn.GetConnectedPads(q))
                            if t.GetNetname()==net and uid(t) not in seen)
            contacts=list(contacts)
            for index in contacts[1:]:union(contacts[0],index)
            groups.append((members,contacts))
        merged={};isolated=[]
        for members,contacts in groups:
            if not members:continue
            if contacts:merged.setdefault(find(contacts[0]),set()).update(members)
            else:isolated.append(members)
        result[net]=[sorted(g) for g in list(merged.values())+isolated]
        if islands:
            electrical={}
            for index,island in enumerate(islands):
                electrical.setdefault(find(index),[]).append({'zone_uuid':island['key'][0],
                    'layer':b.GetLayerName(island['layer']),'filled_polygon_index':island['key'][2]})
            plane_summary[net]={'filled_polygon_count':len(islands),
                               'electrically_joined_region_groups':list(electrical.values()),
                               'electrical_region_group_count':len(electrical)}
    return result,plane_summary


def main():
    base=Path(sys.argv[1]);cand=Path(sys.argv[2]);out=Path(sys.argv[3])
    a,pa=analyse(base);b,pb=analyse(cand);fail=[]
    for net,groups in a.items():
        for group in groups:
            if len(group)>1 and not any(set(group)<=set(c) for c in b.get(net,[])):
                fail.append(dict(net=net,previous_connected_group=group,candidate_groups=b.get(net,[])))
    sel={net:dict(onboard_pads=sum(len(g) for g in b[net]),physical_pad_clusters=b[net],
                  complete_between_onboard_pads=len(b[net])==1) for net in sorted(selected) if net in b}
    report=dict(status='PASS' if not fail else 'FAIL',prior_connectivity_regressions=fail,
                selected_nets=sel,completed_selected=sum(x['complete_between_onboard_pads'] for x in sel.values()),
                total_selected=len(sel),remaining_selected=[n for n,x in sel.items() if not x['complete_between_onboard_pads']],
                baseline_plane_connectivity=pa,candidate_plane_connectivity=pb,
                method='Native same-net copper contacts plus per-filled-polygon zone contact; includes copper-only island bridges.')
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('selected_nets','baseline_plane_connectivity','candidate_plane_connectivity')},indent=2))
    assert not fail

if __name__ == "__main__":
    main()
