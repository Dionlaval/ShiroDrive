#!/usr/bin/env python3
"""Read-only additive routing validation using native KiCad 9 pcbnew.

Run with KiCad's bundled Python. All arguments are explicit; writes only JSON
unless --prune-output is supplied. Pruning writes a *different candidate copy*,
never an input or the working P4 board. Refill and rerun DRC after pruning.

Manifest groups may be {"groups": [{"id": ..., "new_items": [UUID, ...]}]},
or nested connection dictionaries containing their own new_items array.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import pcbnew as p


def uid(obj):
    return obj.m_Uuid.AsString()


def xy(vec):
    return [int(vec.x), int(vec.y)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def footprint_state(f):
    return {
        'uuid': uid(f), 'reference': f.GetReference(), 'value': f.GetValue(),
        'footprint': f.GetFPID().GetUniStringLibId(), 'path': f.GetPath().AsString(),
        'position_nm': xy(f.GetPosition()), 'angle_deg': f.GetOrientationDegrees(),
        'layer': f.GetLayerName(), 'dnp': f.IsDNP(), 'locked': f.IsLocked(),
        'fields': {q.GetName(): q.GetText() for q in f.GetFields()},
        'pads': {uid(q): {
            'number': q.GetNumber(), 'net': q.GetNetname(),
            'position_nm': xy(q.GetPosition()), 'angle_deg': q.GetOrientationDegrees(),
            'size_nm': xy(q.GetSize()), 'drill_nm': xy(q.GetDrillSize()),
            'layers': q.GetLayerSet().FmtHex(), 'shape': int(q.GetShape()),
            'attribute': int(q.GetAttribute()), 'offset_nm': xy(q.GetOffset()),
        } for q in f.Pads()},
    }


def copper_state(t):
    via = isinstance(t, p.PCB_VIA)
    d = {
        'class': t.GetClass(), 'net': t.GetNetname(), 'layer': t.GetLayerName(),
        'start_nm': xy(t.GetStart()), 'end_nm': xy(t.GetEnd()),
        'width_nm': t.GetWidth(p.F_Cu) if via else t.GetWidth(),
        'layers': t.GetLayerSet().FmtHex(), 'locked': t.IsLocked(),
    }
    if via:
        d.update(drill_nm=t.GetDrillValue(), via_type=int(t.GetViaType()),
                 diameters_nm={str(layer): t.GetWidth(layer) for layer in t.GetLayerSet().Seq()
                               if p.IsCopperLayer(layer)})
    if isinstance(t, p.PCB_ARC):
        d['mid_nm'] = xy(t.GetMid())
    return d


def violation_key(v):
    return (v.get('type'), tuple(sorted(i.get('uuid', '') for i in v.get('items', []))))


def drc_stats(d):
    return {'errors': sum(v.get('severity') == 'error' for v in d.get('violations', [])),
            'warnings': sum(v.get('severity') == 'warning' for v in d.get('violations', [])),
            'unconnected': len(d.get('unconnected_items', []))}


def introduced_errors(old, new):
    # An old warning promoted to an error must not silently pass.
    old_errors = {violation_key(v) for v in old.get('violations', []) if v.get('severity') == 'error'}
    return [v for v in new.get('violations', [])
            if v.get('severity') == 'error' and violation_key(v) not in old_errors]


def validate(baseline, candidate, baseline_drc, candidate_drc):
    a, b = p.LoadBoard(str(baseline)), p.LoadBoard(str(candidate))
    if a is None or b is None:
        raise ValueError('Could not load one of the PCB files')
    af = {uid(f): footprint_state(f) for f in a.GetFootprints()}
    bf = {uid(f): footprint_state(f) for f in b.GetFootprints()}
    at = {uid(t): copper_state(t) for t in a.GetTracks()}
    bt = {uid(t): copper_state(t) for t in b.GetTracks()}
    failures = []
    if set(af) != set(bf):
        failures.append('Footprint UUID set changed')
    changed_footprints = [{'uuid': i, 'reference': af[i]['reference'],
                           'changed_fields': [k for k in af[i] if af[i][k] != bf[i][k]]}
                          for i in af.keys() & bf.keys() if af[i] != bf[i]]
    if changed_footprints:
        failures.append('Footprint identity, placement, fields or pad geometry/net changed')
    removed_old_copper = sorted(at.keys() - bt.keys())
    changed_old_copper = sorted(i for i in at.keys() & bt.keys() if at[i] != bt[i])
    if removed_old_copper or changed_old_copper:
        failures.append('Existing copper was removed or modified')

    new_ids = set(bt) - set(at)
    new_objects = [t for t in b.GetTracks() if uid(t) in new_ids]
    outline = p.SHAPE_POLY_SET()
    outline_ok = b.GetBoardPolygonOutlines(outline)
    if not outline_ok:
        failures.append('Board outline is invalid')
    invalid_widths, invalid_vias, outside, via_pad_overlaps = [], [], [], []
    per_net, per_layer = {}, {}
    widths = collections.Counter()
    pad_rows = [(f.GetReference(), q) for f in b.GetFootprints() for q in f.Pads()]
    for t in new_objects:
        via = isinstance(t, p.PCB_VIA)
        if via:
            layers = [layer for layer in t.GetLayerSet().Seq() if p.IsCopperLayer(layer)]
            if (t.GetDrillValue() != p.FromMM(.3) or
                    any(t.GetWidth(layer) != p.FromMM(.5) for layer in layers) or
                    t.GetViaType() != p.VIATYPE_THROUGH or
                    not t.IsOnLayer(p.F_Cu) or not t.IsOnLayer(p.B_Cu)):
                invalid_vias.append({'uuid': uid(t), **bt[uid(t)]})
            for ref, pad in pad_rows:
                overlap_layers = []
                for layer in layers:
                    if pad.IsOnLayer(layer):
                        circle = p.SHAPE_CIRCLE(t.GetPosition(), t.GetWidth(layer) // 2)
                        if pad.GetEffectiveShape(layer).Collide(circle, 0):
                            overlap_layers.append(b.GetLayerName(layer))
                if overlap_layers:
                    via_pad_overlaps.append({'via_uuid': uid(t), 'via_net': t.GetNetname(),
                                             'pad_uuid': uid(pad), 'reference': ref,
                                             'pad': pad.GetNumber(), 'pad_net': pad.GetNetname(),
                                             'layers': overlap_layers})
        else:
            widths[str(round(p.ToMM(t.GetWidth()), 6))] += 1
            if t.GetWidth() not in (p.FromMM(.1524), p.FromMM(.254)):
                invalid_widths.append({'uuid': uid(t), 'width_mm': p.ToMM(t.GetWidth()),
                                       'net': t.GetNetname()})
        if outline_ok:
            # Convert the entire copper shape, not just the endpoints. KiCad's
            # conservative 1 um polygonization also catches routes across cutouts.
            copper_poly = p.SHAPE_POLY_SET()
            t.TransformShapeToPolygon(copper_poly, p.F_Cu if via else t.GetLayer(),
                                      0, p.FromMM(.001), p.ERROR_OUTSIDE)
            copper_poly.BooleanSubtract(outline)
            if copper_poly.OutlineCount():
                outside.append({'uuid': uid(t), 'net': t.GetNetname(), 'class': t.GetClass()})
        length = 0.0 if via else p.ToMM(t.GetLength())
        for stats, key in ((per_net, t.GetNetname()),
                           (per_layer, 'through' if via else t.GetLayerName())):
            row = stats.setdefault(key, {'tracks': 0, 'vias': 0, 'length_mm': 0.0})
            row['vias' if via else 'tracks'] += 1
            row['length_mm'] += length
    for stats in (per_net, per_layer):
        for row in stats.values():
            row['length_mm'] = round(row['length_mm'], 6)
    if invalid_widths:
        failures.append('New tracks have widths other than 6 or 10 mil')
    if invalid_vias:
        failures.append('New vias differ from 0.5 mm pad / 0.3 mm hole through vias')
    if outside:
        failures.append('New copper extends outside the board outline')
    if via_pad_overlaps:
        failures.append('New vias overlap footprint copper pads (same net included)')
    introduced = introduced_errors(baseline_drc, candidate_drc)
    if introduced:
        failures.append('New DRC errors appeared')
    return {
        'status': 'PASS' if not failures else 'FAIL', 'failures': failures,
        'baseline': str(Path(baseline).resolve()), 'candidate': str(Path(candidate).resolve()),
        'baseline_sha256': sha(baseline), 'candidate_sha256': sha(candidate),
        'footprint_count': len(bf), 'changed_footprints': changed_footprints,
        'removed_old_copper': removed_old_copper, 'changed_old_copper': changed_old_copper,
        'existing_copper_unchanged': not (removed_old_copper or changed_old_copper),
        'new_item_count': len(new_ids), 'new_items': sorted(new_ids),
        'new_track_widths_mm': dict(widths), 'invalid_new_widths': invalid_widths,
        'invalid_new_vias': invalid_vias, 'outside_board_copper': outside,
        'via_pad_overlaps': via_pad_overlaps,
        'new_routing_by_net': dict(sorted(per_net.items())),
        'new_routing_by_layer': dict(sorted(per_layer.items())),
        'baseline_drc': drc_stats(baseline_drc), 'candidate_drc': drc_stats(candidate_drc),
        'introduced_errors': introduced,
        'introduced_error_item_uuids': sorted({i.get('uuid', '') for v in introduced
                                              for i in v.get('items', [])}),
        'project_schematic_rules_hash_check': 'External responsibility; this script does not modify them',
        'scope': 'Additive routing and native DRC regression; does not claim circuit or signal-integrity verification',
    }


def manifest_groups(data):
    """Extract innermost dictionaries with new_items, avoiding global unions."""
    rows = []
    def walk(node, path='root'):
        if isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, path + '/' + str(i))
        elif isinstance(node, dict):
            descendants_before = len(rows)
            for key, value in node.items():
                if key != 'new_items':
                    walk(value, path + '/' + key)
            if 'new_items' in node and len(rows) == descendants_before:
                items = node['new_items']
                if isinstance(items, dict):
                    items = list(items.keys())
                ids = {item if isinstance(item, str) else item.get('uuid', item.get('id', ''))
                       for item in items}
                ids.discard('')
                rows.append({'id': str(node.get('id', node.get('name', path))), 'items': ids})
    walk(data)
    return rows


def prune_connections(candidate, baseline, report, manifest, output):
    output = Path(output).resolve()
    working = Path(__file__).resolve().parents[3] / 'ShiroFOC_Manual.kicad_pcb'
    if output in {Path(candidate).resolve(), Path(baseline).resolve(), working.resolve()}:
        raise ValueError('Prune output must be a separate review candidate, not any input or working board')
    groups = manifest_groups(manifest)
    if not groups:
        raise ValueError('Manifest contains no connection groups with new_items')
    added = set(report['new_items'])
    offenders = set(report['introduced_error_item_uuids']) & added
    offenders |= {x['uuid'] for key in ('invalid_new_widths', 'invalid_new_vias', 'outside_board_copper')
                  for x in report[key]}
    offenders |= {x['via_uuid'] for x in report['via_pad_overlaps']}
    chosen, remove = [], set()
    # A shared item in two groups causes both full connections to be pruned.
    while True:
        previous = set(remove)
        for group in groups:
            if group['items'] & (offenders | remove):
                if group['id'] not in chosen:
                    chosen.append(group['id'])
                remove |= group['items']
        if remove == previous:
            break
    if offenders - remove:
        raise ValueError('Some offending items have no manifest group: ' + str(sorted(offenders - remove)))
    if remove - added:
        raise ValueError('Refusing prune: manifest group contains pre-existing copper')
    board = p.LoadBoard(str(candidate))
    # Hold SWIG references while removing items from board.
    objects = [t for t in board.GetTracks() if uid(t) in remove]
    for obj in objects:
        board.Remove(obj)
    output.parent.mkdir(parents=True, exist_ok=True)
    p.SaveBoard(str(output), board)
    return {'output': str(output), 'groups_removed': chosen, 'items_removed': sorted(remove),
            'requires_refill_and_drc': True}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline', required=True, type=Path)
    ap.add_argument('--candidate', required=True, type=Path)
    ap.add_argument('--baseline-drc', required=True, type=Path)
    ap.add_argument('--candidate-drc', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--manifest', type=Path)
    ap.add_argument('--prune-output', type=Path)
    args = ap.parse_args()
    if args.output.resolve() in {args.baseline.resolve(), args.candidate.resolve()}:
        ap.error('JSON output cannot replace either input PCB')
    result = validate(args.baseline, args.candidate,
                      json.loads(args.baseline_drc.read_text()),
                      json.loads(args.candidate_drc.read_text()))
    if args.prune_output:
        if not args.manifest:
            ap.error('--prune-output requires --manifest')
        result['prune'] = prune_connections(args.candidate, args.baseline, result,
                                             json.loads(args.manifest.read_text()), args.prune_output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('status', 'failures', 'new_item_count',
                                                 'baseline_drc', 'candidate_drc')}, indent=2))
    raise SystemExit(0 if result['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
