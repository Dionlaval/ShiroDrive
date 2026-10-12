"""Read-only structural and DRC-delta audit for the isolated phase candidate."""
from pathlib import Path
import hashlib
import json
import re
from collections import Counter

import pcbnew as p

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'before' / 'ShiroFOC_Manual.kicad_pcb'
CANDIDATE = HERE / 'ShiroFOC_Manual.kicad_pcb'
ALLOWED = {'R701', 'R702', 'R703', 'R711', 'R712', 'R713'}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def parse(path):
    # Tokenize strings atomically so quoted parentheses cannot alter nesting.
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', path.read_text())
    stack = []
    root = None
    for token in tokens:
        if token == '(':
            node = []
            if stack:
                stack[-1].append(node)
            else:
                root = node
            stack.append(node)
        elif token == ')':
            stack.pop()
        else:
            stack[-1].append(token)
    assert not stack
    return root

def fp_blocks(tree):
    result = {}
    for child in tree[1:]:
        if isinstance(child, list) and child[0] == 'footprint':
            ref = next(x[2] for x in child if isinstance(x, list) and x[:2] == ['property', '"Reference"'])
            result[json.loads(ref)] = child
    return result

def uid(obj):
    return obj.m_Uuid.AsString()

def identity(fp):
    return {'uuid': uid(fp), 'path': fp.GetPath().AsString(),
            'pads': {uid(q): [q.GetNumber(), q.GetNetname()] for q in fp.Pads()}}

def drc_key(v):
    return (v['type'], tuple(sorted(i['uuid'] for i in v['items'])))

a_tree, b_tree = parse(SOURCE), parse(CANDIDATE)
a_fp, b_fp = fp_blocks(a_tree), fp_blocks(b_tree)
changed = sorted(r for r in a_fp.keys() & b_fp.keys() if a_fp[r] != b_fp[r])
a_board, b_board = p.LoadBoard(str(SOURCE)), p.LoadBoard(str(CANDIDATE))
a_native = {f.GetReference(): f for f in a_board.GetFootprints()}
b_native = {f.GetReference(): f for f in b_board.GetFootprints()}
identity_mismatches = sorted(r for r in a_native.keys() & b_native.keys()
                             if identity(a_native[r]) != identity(b_native[r]))
element_types = ['segment', 'arc', 'via', 'zone', 'gr_line', 'gr_arc', 'gr_circle',
                 'gr_rect', 'gr_poly', 'gr_curve', 'gr_text', 'dimension', 'net']
elements = {}
for tag in element_types:
    aa = [v for v in a_tree[1:] if isinstance(v, list) and v[0] == tag]
    bb = [v for v in b_tree[1:] if isinstance(v, list) and v[0] == tag]
    elements[tag] = {'before_count': len(aa), 'after_count': len(bb), 'unchanged': aa == bb}

before_drc = json.loads((HERE / 'drc_before.json').read_text())
after_drc = json.loads((HERE / 'drc_candidate.json').read_text())
baseline = {drc_key(v) for v in before_drc['violations']}
introduced = [v for v in after_drc['violations'] if drc_key(v) not in baseline]
manifest = json.loads((HERE / 'manifest.json').read_text())
checks = {
    'source_hash_matches_manifest': digest(SOURCE) == manifest['source_sha256'],
    'same_footprint_reference_set': a_fp.keys() == b_fp.keys(),
    'only_six_authorized_footprints_changed': set(changed) == ALLOWED,
    'all_existing_uuids_pad_nets_and_schematic_paths_preserved': not identity_mismatches,
    'all_copper_zones_outline_and_board_drawings_unchanged': all(v['unchanged'] for v in elements.values()),
    'no_courtyard_body_through_hole_or_edge_conflicts_in_placement_check': not manifest['geometry_collisions'],
    'zero_new_drc_errors': not any(v['severity'] == 'error' for v in introduced),
    'unconnected_count_unchanged': len(before_drc['unconnected_items']) == len(after_drc['unconnected_items']),
}
result = {
    'source': str(SOURCE), 'source_sha256': digest(SOURCE),
    'candidate': str(CANDIDATE), 'candidate_sha256': digest(CANDIDATE),
    'result': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks,
    'changed_footprints': changed, 'identity_mismatches': identity_mismatches,
    'board_elements': elements,
    'drc': {
        'before': dict(Counter(v['severity'] for v in before_drc['violations'])),
        'candidate': dict(Counter(v['severity'] for v in after_drc['violations'])),
        'unconnected_before': len(before_drc['unconnected_items']),
        'unconnected_candidate': len(after_drc['unconnected_items']),
        'introduced_violations': introduced,
    },
    'limitations': ['Placement only; the NTC paths still require routing.',
                    'Five new silkscreen-only overlap warnings remain: four 0.17 mm row gaps and R703/D801 symbol overlap.',
                    'ADC capacitors C711/C712/C713 and phase thermistors TH701/TH702/TH703 remain unchanged.'],
}
(HERE / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'result': result['result'], 'checks': checks, 'candidate_sha256': result['candidate_sha256']}, indent=2))
assert result['result'] == 'PASS'
