#!/usr/bin/env python3
"""Check the P1 PCB against an independently exported native XML netlist.

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

project = Path(__file__).resolve().parents[1] / 'ShiroFOC_KiCad_P1'
out = project / 'outputs/placement_P1'
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
    problems.append('P1 unexpectedly contains routing or zones')

drc = json.loads((out / 'drc_final.json').read_text())
fatal_types = {'clearance', 'shorting_items', 'courtyards_overlap',
               'copper_edge_clearance', 'hole_to_hole', 'board_outline', 'unresolved_variable'}
for item in drc['violations']:
    if item['type'] in fatal_types:
        problems.append('DRC: ' + item['description'])
if drc.get('schematic_parity'):
    problems.append('Native schematic parity check failed')
# Compare original saved files against the recorded backup manifest.
backup=json.loads((out/'backup_manifest.json').read_text())
original=Path(backup['original_project'])
changed_original=[]
for name,digest in backup['original_files'].items():
    if hashlib.sha256((original/name).read_bytes()).hexdigest()!=digest:changed_original.append(name)
if changed_original:problems.append('Original project changed: '+str(changed_original))
mechanical=[]
for ref,coord in zip(['H1','H2','H3','H4'],[(106,106),(174,106),(174,174),(106,174)]):
    f=by_ref[ref]; pads=list(f.Pads())
    if len(pads)!=1 or pads[0].GetAttribute()!=p.PAD_ATTRIB_NPTH or pads[0].GetDrillSize()!=p.VECTOR2I(p.FromMM(3.2),p.FromMM(3.2)):problems.append(ref+': incorrect M3 hole')
    if f.GetPosition()!=p.VECTOR2I(p.FromMM(coord[0]),p.FromMM(coord[1])):problems.append(ref+': misplaced mounting hole')
    if not (f.GetAttributes() & p.FP_EXCLUDE_FROM_BOM):problems.append(ref+': not excluded from BOM')
    mechanical.append({'reference':ref,'local_xy_mm':[a-100 for a in coord],'drill_mm':3.2,'washer_envelope_mm':8})
# Same copper-facing geometry for every output; these are placement distances,
# not routed lengths or a proof of equal current-path impedance.
phase_geometry=[]
for i in range(3):
    q=by_ref['Q'+str(401+i)];j=next(z for z in by_ref['J401'].Pads() if z.GetNumber()==str(i+1))
    qp=q.GetPosition();jp=j.GetPosition()
    outer=max(p.ToMM(z.GetPosition().x) for z in q.Pads() if z.GetNetname()=='OUT'+str(i+1))
    record={'phase':'UVW'[i],'mosfet_local_mm':[p.ToMM(qp.x)-100,p.ToMM(qp.y)-100], 'terminal_local_mm':[p.ToMM(jp.x)-100,p.ToMM(jp.y)-100], 'output_bank_to_terminal_centre_mm':round(p.ToMM(jp.x)-outer,3)}
    phase_geometry.append(record)
    if qp.y!=jp.y or p.ToMM(qp.x)!=164:problems.append('Phase '+str(i+1)+' is not aligned')
if len({z['output_bank_to_terminal_centre_mm'] for z in phase_geometry})!=1:problems.append('Unequal phase placement geometry')
# Conservative opposite-face body-to-through-pad and hardware-envelope checks.
import math
def bb_box(a):return (p.ToMM(a.GetLeft()),p.ToMM(a.GetTop()),p.ToMM(a.GetRight()),p.ToMM(a.GetBottom()))
def body(f):
    lay=p.B_CrtYd if f.IsFlipped() else p.F_CrtYd
    a=[bb_box(g.GetBoundingBox()) for g in f.GraphicalItems() if g.GetLayer()==lay]
    return (min(z[0] for z in a),min(z[1] for z in a),max(z[2] for z in a),max(z[3] for z in a))
def overlap(a,c):return a[0]<c[2] and a[2]>c[0] and a[1]<c[3] and a[3]>c[1]
interference=[];hardware=[]
for f in footprints:
    if f.GetReference().startswith('H'):continue
    a=body(f)
    for h in mechanical:
        cx,cy=[z+100 for z in h['local_xy_mm']]
        distance=math.hypot(max(a[0],min(cx,a[2]))-cx,max(a[1],min(cy,a[3]))-cy)
        if distance<4:hardware.append([f.GetReference(),h['reference'],distance])
    for q in footprints:
        if q.GetReference().startswith('H') or q.GetLayer()==f.GetLayer():continue
        for pad in q.Pads():
            if pad.GetAttribute() in (p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH) and overlap(a,bb_box(pad.GetBoundingBox())):interference.append([f.GetReference(),q.GetReference(),pad.GetNumber()])
if hardware:problems.append('Hardware collision: '+str(hardware))
if interference:problems.append('Opposite-side through-pad collision: '+str(interference))
result = {
    'stage': 'P1 component placement; not a routed or fabrication-ready board',
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
    'unconnected_DRC_items_expected_at_P1': len(drc['unconnected_items']),
    'other_DRC_violations': dict(collections.Counter(v['type'] for v in drc['violations'])),
    'original_project_preserved':not changed_original,
    'mounting_holes':mechanical,
    'phase_geometry':phase_geometry,
    'opposite_side_body_to_through_pad_collisions':interference,
    'hardware_envelope_collisions':hardware,
    'problems': problems,
}
(out / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
sys.exit(bool(problems))
