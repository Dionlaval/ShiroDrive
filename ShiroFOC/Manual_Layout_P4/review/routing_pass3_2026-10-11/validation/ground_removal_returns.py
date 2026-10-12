#!/usr/bin/env python3
"""Audit return-interconnect loss at unchanged signal vias after GND edits."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import pcbnew as p


def uid(item):
    return item.m_Uuid.AsString()


def xy(item):
    v = item.GetPosition()
    return [round(p.ToMM(v.x), 6), round(p.ToMM(v.y), 6)]


def snapshot(path):
    board = p.LoadBoard(str(path))
    tracks = list(board.GetTracks())
    pads = [q for f in board.GetFootprints() for q in f.Pads()]
    planes = [(z, l) for z in board.Zones() if z.GetNetname() == 'GND'
              for l in z.GetLayerSet().Seq()]
    stack = list(board.GetEnabledLayers().CuStack())
    items_by_net = {}
    for item in tracks + pads:
        items_by_net.setdefault(item.GetNetname(), []).append(item)
    ground = []
    for item in tracks + pads:
        if item.GetNetname() != 'GND':
            continue
        if not (isinstance(item, p.PCB_VIA) or
                isinstance(item, p.PAD) and item.GetAttribute() == p.PAD_ATTRIB_PTH):
            continue
        refs = {l for z, l in planes if item.IsOnLayer(l) and
                z.HitTestFilledArea(l, item.GetPosition())}
        if refs:
            ground.append((item, refs))
    vias = {}
    for via in tracks:
        if not isinstance(via, p.PCB_VIA) or via.GetNetname() in ('GND', '3V3', 'VCC', 'VREF+', 'VDDA'):
            continue
        touched = set()
        for item in items_by_net.get(via.GetNetname(), []):
            if isinstance(item, p.PCB_VIA):
                continue
            layers = stack if isinstance(item, p.PAD) else [item.GetLayer()]
            for layer in layers:
                if item.IsOnLayer(layer) and via.GetEffectiveShape(layer).Collide(item.GetEffectiveShape(layer), 0):
                    touched.add(layer)
        refs = {l for z, l in planes for layer in touched
                if abs(stack.index(l) - stack.index(layer)) == 1}
        eligible = [item for item, covered in ground if refs <= covered]
        point = via.GetPosition()
        dist = lambda q: p.ToMM(math.hypot(q.GetPosition().x-point.x, q.GetPosition().y-point.y))
        nearest = min(eligible, key=dist) if eligible and refs else None
        vias[uid(via)] = {
            'uuid': uid(via), 'net': via.GetNetname(), 'position_mm': xy(via),
            'signal_layers': [board.GetLayerName(l) for l in sorted(touched)],
            'reference_layers': [board.GetLayerName(l) for l in sorted(refs)],
            'reference_change': len(refs) > 1,
            'nearest_ground_uuid': uid(nearest) if nearest else None,
            'nearest_ground_mm': round(dist(nearest), 4) if nearest else None,
        }
    return board, {'vias': vias, 'ground': {uid(q): xy(q) for q, refs in ground}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', type=Path, required=True)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    old_board, old = snapshot(args.baseline)
    new_board, new = snapshot(args.candidate)
    retired = {u: pos for u, pos in old['ground'].items() if new['ground'].get(u) != pos}
    affected = []
    for identifier, row in new['vias'].items():
        prev = old['vias'].get(identifier)
        if not prev or not row['reference_change']:
            continue
        olddist = prev['nearest_ground_mm']
        newdist = row['nearest_ground_mm']
        if prev['nearest_ground_uuid'] not in retired and not (olddist is not None and (newdist is None or newdist > olddist + .001)):
            continue
        affected.append({'before': prev, 'after': row,
                         'old_nearest_ground_removed_or_moved': prev['nearest_ground_uuid'] in retired})
    result = {'candidate': str(args.candidate.resolve()),
              'sha256': hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
              'retired_ground_interconnects': retired,
              'affected_existing_reference_changes': affected,
              'affected_over_2mm': [r for r in affected if r['after']['nearest_ground_mm'] is None or r['after']['nearest_ground_mm'] > 2],
              'all_candidate_signal_vias': list(new['vias'].values()),
              'method': 'All signal-via same-net physical copper contacts, adjacent GND planes and through GND interconnect contacts. Geometric proximity only.'}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'all_candidate_signal_vias'}, indent=2))


if __name__ == '__main__':
    main()
