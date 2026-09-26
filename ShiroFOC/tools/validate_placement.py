#!/usr/bin/env python3
"""Check the P0 PCB against an independently exported native XML netlist.

Run with KiCad's bundled Python. This validates placement consistency only;
it does not establish electrical performance, thermal limits or fabrication readiness.
"""
import collections
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew as p

project = Path(__file__).resolve().parents[1] / 'ShiroFOC_KiCad'
out = project / 'outputs/placement'
netlist = out / 'source_netlist.xml'
root = ET.parse(netlist).getroot()
components = {c.attrib['ref']: c for c in root.find('components')}
expected = {}
for net in root.find('nets'):
    name = net.attrib['name']
    if name.startswith(('Net-(', 'unconnected-(')):
        name = name.replace('/', '{slash}')
    for node in net:
        expected[(node.attrib['ref'], node.attrib['pin'])] = name

pcb_path = project / 'ShiroFOC_KiCad.kicad_pcb'
board = p.LoadBoard(str(pcb_path))
footprints = list(board.GetFootprints())
refs = collections.Counter(f.GetReference() for f in footprints)
problems = []
if set(refs) != set(components) or any(n != 1 for n in refs.values()):
    problems.append('PCB reference inventory differs from schematic')
checked_pads = 0
seen = set()
for f in footprints:
    ref = f.GetReference()
    c = components[ref]
    actual_fpid = str(f.GetFPID().GetLibNickname()) + ':' + str(f.GetFPID().GetLibItemName())
    if actual_fpid != c.findtext('footprint'):
        problems.append(ref + ': footprint name differs')
    if f.GetValue() != c.findtext('value'):
        problems.append(ref + ': value differs')
    dnp = any(q.attrib.get('name') == 'dnp' for q in c.findall('property')) or any(
        q.attrib.get('name') == 'Assembly' and q.text == 'DNP'
        for q in c.findall('fields/field'))
    if bool(f.IsDNP()) != dnp:
        problems.append(ref + ': DNP differs')
    for pad in f.Pads():
        key = ref, pad.GetNumber()
        if not pad.GetNumber():
            continue
        if key in expected:
            checked_pads += 1
            seen.add(key)
            if pad.GetNetname() != expected[key]:
                problems.append(f'{ref}.{key[1]}: net differs')
        elif pad.GetNetname():
            problems.append(f'{ref}.{key[1]}: unexpected assigned net')
for key in expected.keys() - seen:
    problems.append(f'{key}: missing physical pad')

by_ref = {f.GetReference(): f for f in footprints}
encoder = by_ref['U601']
if not encoder.IsFlipped() or encoder.GetPosition() != p.VECTOR2I(p.FromMM(140), p.FromMM(140)):
    problems.append('Encoder is not centred on B.Cu')
for ref in ['U301', 'Q401', 'Q402', 'Q403', 'Q501']:
    if by_ref[ref].IsFlipped():
        problems.append(ref + ': must be on top')
for ref in ['R416', 'R426', 'R436']:
    if not by_ref[ref].IsFlipped():
        problems.append(ref + ': shunt must be underneath its bridge')
if board.GetCopperLayerCount() != 4:
    problems.append('Board is not four layers')
if list(board.GetTracks()) or list(board.Zones()):
    problems.append('P0 unexpectedly contains routing or zones')

drc = json.loads((out / 'drc_final.json').read_text())
fatal_types = {'clearance', 'shorting_items', 'courtyards_overlap',
               'copper_edge_clearance', 'hole_to_hole', 'board_outline', 'unresolved_variable'}
for item in drc['violations']:
    if item['type'] in fatal_types:
        problems.append('DRC: ' + item['description'])
if drc.get('schematic_parity'):
    problems.append('Native schematic parity check failed')
result = {
    'stage': 'P0 component placement; not a routed or fabrication-ready board',
    'pcb_sha256': hashlib.sha256(pcb_path.read_bytes()).hexdigest(),
    'source_netlist_sha256': hashlib.sha256(netlist.read_bytes()).hexdigest(),
    'footprints': len(footprints),
    'front': sum(not f.IsFlipped() for f in footprints),
    'back': sum(f.IsFlipped() for f in footprints),
    'dnp': sum(f.IsDNP() for f in footprints),
    'matched_electrical_pads_including_duplicate_thermal_pads': checked_pads,
    'matched_unique_component_pin_pairs': len(seen),
    'layers': board.GetCopperLayerCount(),
    'tracks_and_routed_vias': len(list(board.GetTracks())),
    'zones': len(list(board.Zones())),
    'schematic_parity_issues': len(drc.get('schematic_parity', [])),
    'unconnected_DRC_items_expected_at_P0': len(drc['unconnected_items']),
    'other_DRC_violations': dict(collections.Counter(v['type'] for v in drc['violations'])),
    'problems': problems,
}
(out / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
sys.exit(bool(problems))
