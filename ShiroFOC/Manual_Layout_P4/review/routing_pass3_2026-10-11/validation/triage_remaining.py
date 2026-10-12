#!/usr/bin/env python3
"""Read-only routing-scope triage; native geometry, no schematic/device claim."""
import collections
import hashlib
import json
import math
import argparse
from pathlib import Path
import pcbnew as p
from connectivity_regression import analyse, selected

HERE = Path(__file__).resolve().parent
BOARD = HERE.parent / 'before/ShiroFOC_Manual.kicad_pcb'
uid = lambda q: q.m_Uuid.AsString()
xy = lambda v: [p.ToMM(v.x), p.ToMM(v.y)]

def category(net):
    if net == 'GND': return 'ground_connections'
    if net in {'5V_BAT','5V_SYS','5V_USB','VCC','Net-(U201-SW)','/External feedback/EXT_VCC'}:
        return 'auxiliary_power'
    if net.startswith(('GHS','GLS','HS_RETURN_')): return 'gate_drive'
    if net == 'VM' or net.startswith('PHASE_') or net == 'Net-(J501-Pad1)': return 'high_current'
    return 'support'

def main():
    global BOARD
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, default=BOARD)
    parser.add_argument('--drc', type=Path)
    parser.add_argument('--output', type=Path, default=HERE/'remaining_onboard_scope.json')
    args = parser.parse_args()
    BOARD = args.board.resolve()
    groups, planes = analyse(BOARD, unique_pad_labels=True)
    b = p.LoadBoard(str(BOARD))
    outline = p.SHAPE_POLY_SET(); assert b.GetBoardPolygonOutlines(outline)
    objects = {uid(q):q for f in b.GetFootprints() for q in f.Pads()}
    objects.update({uid(q):q for q in b.GetTracks()})
    pads = {}
    for f in b.GetFootprints():
        for q in f.Pads():
            label = f'{f.GetReference()}.{q.GetNumber()}#{uid(q)}'
            pads[label] = {'uuid':uid(q),'reference':f.GetReference(),'pad':q.GetNumber(),
                'value':f.GetValue(),'net':q.GetNetname(),'position_mm':xy(q.GetPosition()),
                'footprint_position_mm':xy(f.GetPosition()),'layer':f.GetLayerName(),
                'dnp':f.IsDNP() or 'DNP' in f.GetValue().upper(),
                'footprint_onboard':outline.Contains(f.GetPosition())}
    drc = json.loads((args.drc or BOARD.parent/'drc.json').read_text())
    by_net = collections.defaultdict(list)
    for issue in drc['unconnected_items']:
        nets = {objects[item['uuid']].GetNetname() for item in issue['items'] if item['uuid'] in objects}
        row = dict(issue)
        row['endpoint_scope'] = []
        for item in issue['items']:
            q = objects.get(item['uuid'])
            if q is None:
                scope='unresolved'
            elif isinstance(q,p.PAD):
                f=q.GetParentFootprint()
                scope='DNP/staged' if f.IsDNP() or 'DNP' in f.GetValue().upper() or not outline.Contains(f.GetPosition()) else 'onboard_pad'
            else: scope='onboard_copper' if outline.Contains(q.GetPosition()) else 'offboard_copper'
            row['endpoint_scope'].append(scope)
        for net in nets: by_net[net].append(row)
    rows=[]
    for net, clusters in sorted(groups.items()):
        if len(clusters)<2 or net in selected:continue
        nearest=[]
        for i,cluster in enumerate(clusters):
            choices=[]
            for j,other in enumerate(clusters):
                if i==j:continue
                for a in cluster:
                    for c in other:
                        choices.append((math.dist(pads[a]['position_mm'],pads[c]['position_mm']),a,c,j))
            distance,a,c,j=min(choices)
            nearest.append({'cluster_index':i,'other_cluster_index':j,
                            'pad_a':a,'pad_b':c,'straight_span_mm':round(distance,3)})
        rows.append({'net':net,'category':category(net),'onboard_pad_clusters':len(clusters),
                     'minimum_joins_to_complete':len(clusters)-1,
                     'onboard_physical_pads':sum(map(len,clusters)),
                     'clusters':[[pads[label] for label in cluster] for cluster in clusters],
                     'nearest_other_cluster':nearest,
                     'native_unconnected_item_count':len(by_net[net]),
                     'native_unconnected_items':by_net[net]})
    summary={}
    for kind in ['auxiliary_power','gate_drive','high_current','support','ground_connections']:
        subset=[row for row in rows if row['category']==kind]
        summary[kind]={'net_count':len(subset),'minimum_pad_cluster_joins':sum(x['minimum_joins_to_complete'] for x in subset),
                       'nets':[x['net'] for x in subset]}
    issue_scope=collections.Counter()
    for issue in [x for entries in by_net.values() for x in entries]:
        scopes=issue['endpoint_scope']
        issue_scope['includes_DNP_or_staged' if any(s in ('DNP/staged','offboard_copper') for s in scopes) else
                    'includes_dangling_or_separate_copper' if 'onboard_copper' in scopes else 'onboard_pad_to_pad']+=1
    report={'board':str(BOARD),'board_sha256':hashlib.sha256(BOARD.read_bytes()).hexdigest(),
            'scope':'Beyond the selected 81 support nets. Native physical connectivity of pads on non-DNP footprints whose centres are inside board outline.',
            'confidence':'high for physical geometry/net membership; suggested grouping is engineering triage, not verified circuit/device functionality',
            'native_drc_unconnected_total':len(drc['unconnected_items']),
            'native_drc_unconnected_scope':dict(issue_scope),
            'remaining_selected_nets':[n for n,g in sorted(groups.items()) if len(g)>1 and n in selected],
            'beyond_selected_net_count':len(rows),
            'minimum_onboard_pad_cluster_joins':sum(x['minimum_joins_to_complete'] for x in rows),
            'categories':summary,'nets':rows,'plane_connectivity':planes,
            'interpretation':['A join count is a topology lower bound, not predicted route segments or native airwire count.',
                'Same-number duplicated footprint pads remain separate physical pads until actual copper joins them.',
                'An overhanging connector body is intentional. Its net pads still require electrical connections.',
                'Existing preliminary power-stage copper and unresolved baseline DRC require their own finishing pass.',
                'Gate paths, Kelvin sensing and power rails require purpose-specific routing; the 6/10 mil signal convention is not evidence of power-current adequacy.']}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('beyond_selected_net_count','minimum_onboard_pad_cluster_joins','native_drc_unconnected_scope','categories')},indent=2))

if __name__=='__main__':main()
