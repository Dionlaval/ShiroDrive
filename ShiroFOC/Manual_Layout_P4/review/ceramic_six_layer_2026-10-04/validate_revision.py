"""Read-only connectivity and preservation audit of this revision.

Run with Python 3.10+ and the KiCad skill's sexp_parser installed/on sys.path.
CLI netlists/ERC/DRC are saved snapshots; regenerate them after further edits.
This checks the requested change, not full electrical or fabrication readiness.
"""
from pathlib import Path
from collections import Counter
import gzip
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, str(Path.home() / '.codex/skills/kicad/scripts'))
from sexp_parser import parse, parse_file, find_all as all_, find_first as one, get_property

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
SNAP = HERE / 'validation'
BACKUP = PROJECT / 'ShiroFOC_Manual-backups/ShiroFOC_Manual-before-ceramic-six-layer-2026-10-04.zip'
archive = zipfile.ZipFile(BACKUP)
before = parse(archive.read('ShiroFOC_Manual.kicad_pcb').decode())
after = parse_file(str(PROJECT / 'ShiroFOC_Manual.kicad_pcb'))
manifest = json.loads((HERE / 'change_manifest.json').read_text())
placement = json.loads((HERE / 'placement_manifest.json').read_text())
renames = placement['net_renames']
checks = []


def check(name, passed, details=None):
    checks.append({'check': name, 'passed': bool(passed), 'evidence': details})


def netlist(name):
    root = ET.fromstring(gzip.decompress((SNAP / name).read_bytes()))
    components = {c.get('ref'): c for c in root.findall('./components/comp')}
    pins, groups = {}, {}
    for n in root.findall('./nets/net'):
        group = {(v.get('ref'), v.get('pin')) for v in n.findall('node')}
        groups[n.get('name')] = group
        for pin in group:
            pins[pin] = n.get('name')
    return components, pins, groups


bc, bp, bg = netlist('before-netlist.xml.gz')
ac, ap, ag = netlist('after-netlist.xml.gz')
oldpins = set(bp)
oldgroups = {frozenset(g) for g in bg.values() if g}
newgroups = {frozenset(g & oldpins) for g in ag.values() if g & oldpins}
check('All original schematic components and pin connectivity preserved',
      set(bc) <= set(ac) and oldpins <= set(ap) and oldgroups == newgroups,
      {'original_components': len(bc), 'original_pins': len(bp),
       'changed_original_net_partitions': len(oldgroups ^ newgroups), 'net_renames': renames})

bf = {get_property(f, 'Reference'): f for f in all_(before, 'footprint')}
af = {get_property(f, 'Reference'): f for f in all_(after, 'footprint')}
bn = {n[1]: n[2] for n in all_(before, 'net')}
an = {n[1]: n[2] for n in all_(after, 'net')}


def canonical(node, nets):
    # KiCad renumbers nets while saving. Compare names, accepting only the
    # three schematic aliases added to existing source-above-shunt nets.
    if isinstance(node, list):
        if node[0] == 'net':
            name = node[2] if len(node) > 2 else nets[node[1]]
            return ['net', renames.get(name, name)]
        return [canonical(c, nets) for c in node]
    return node


modified = sorted(r for r in bf if r in af and canonical(bf[r], bn) != canonical(af[r], an))
check('Only intended existing footprints changed', set(bf) <= set(af) and set(modified) ==
      {'C101', 'C102', 'C103', 'C3', 'C7', 'JP601'}, modified)
for ref in ['U4', 'U601', 'R102', 'C107']:
    check(ref + ' complete footprint preserved', canonical(bf[ref], bn) == canonical(af[ref], an))
check('Encoder locked on bottom at origin', one(af['U601'], 'at')[1:3] == ['0', '0'] and
      one(af['U601'], 'layer')[1] == 'B.Cu' and one(af['U601'], 'locked')[1] == 'yes')
bd = [n for n in before if isinstance(n, list) and n[0].startswith('gr_')]
ad = [n for n in after if isinstance(n, list) and n[0].startswith('gr_')]
check('Outline, mounting guides and all board graphics preserved', bd == ad,
      {'board_graphics': len(ad), 'comparison_rectangles': len(all_(after, 'gr_rect'))})

old_dc = parse(archive.read('01_DC_Link.kicad_sch').decode())
new_dc = parse_file(str(PROJECT / '01_DC_Link.kicad_sch'))
for ref in ['R102', 'C107']:
    old_symbol = next(s for s in all_(old_dc, 'symbol') if get_property(s, 'Reference') == ref)
    new_symbol = next(s for s in all_(new_dc, 'symbol') if get_property(s, 'Reference') == ref)
    check(ref + ' battery damping symbol and DNP state preserved', old_symbol == new_symbol and
          ac[ref].find("property[@name='dnp']") is not None and 'dnp' in one(af[ref], 'attr'))

fitted = [r for g in manifest['capacitor_groups'].values() for r in g['fit']]
dnp = [r for g in manifest['capacitor_groups'].values() for r in g['dnp']]
cap_errors = []
for ref in fitted + dnp:
    c, f = ac[ref], af[ref]
    fields = {v.get('name'): v.text for v in c.findall('./fields/field')}
    if fields.get('MPN') != 'CL32Y106KCVZNWE' or fields.get('Voltage Rating') != '100 V':
        cap_errors.append([ref, 'rating/MPN'])
    if ap[ref, '1'] != 'VM' or ap[ref, '2'] != 'GND':
        cap_errors.append([ref, 'connectivity'])
    if (c.find("property[@name='dnp']") is not None) != (ref in dnp) or ('dnp' in one(f, 'attr')) != (ref in dnp):
        cap_errors.append([ref, 'population'])
check('48 fitted and 6 DNP 100 V ceramic capacitors', len(fitted) == 48 and len(dnp) == 6 and not cap_errors,
      {'fitted': fitted, 'DNP': dnp, 'errors': cap_errors,
       'placement_sides': dict(Counter(one(af[r], 'layer')[1] for r in fitted + dnp))})

new_refs = set(manifest['new_symbols'] + manifest['restored_pcb_symbols'] + ['C101', 'C102', 'C103'])
mismatches = []
for ref in sorted(new_refs):
    if ref not in af:
        mismatches.append([ref, 'missing PCB footprint'])
        continue
    for pad in all_(af[ref], 'pad'):
        net = one(pad, 'net')
        actual = net[2] if net else ''
        if actual != ap.get((ref, pad[1]), ''):
            mismatches.append([ref, pad[1], actual, ap.get((ref, pad[1]), '')])
check('Every added/replaced/restored PCB pad matches the schematic netlist', not mismatches,
      {'footprints_checked': len(new_refs), 'mismatches': mismatches})

for phase, resistor, cap, fet, shunt in [
    ('U', 'R415', 'C413', 'U1', 'R3'), ('V', 'R425', 'C423', 'U2', 'R1'), ('W', 'R435', 'C433', 'U3', 'R5')
]:
    src = ap[cap, '2']
    mid = ap[resistor, '2']
    ok = (ap[resistor, '1'] == 'PHASE_' + phase and mid == ap[cap, '1'] and
          ag[mid] == {(resistor, '2'), (cap, '1')} and
          src == ap[fet, '12'] == ap[shunt, '1'] and
          src not in {'GND', ap[shunt, '2'], ap[shunt, '3']})
    for ref in [resistor, cap]:
        ok &= ac[ref].find("property[@name='dnp']") is not None and 'dnp' in one(af[ref], 'attr')
    check('Phase ' + phase + ' series RC is DNP and returns before shunt', ok, {'return': src, 'midpoint': mid})

tracks = lambda board: {one(n, 'uuid')[1]: n for n in board if isinstance(n, list) and n[0] in ['segment', 'via', 'arc']}
bt, at = tracks(before), tracks(after)
removed = set(bt) - set(at)
allowed_removed = {'aa20e6f2-a48d-459a-ab5c-523c183aa7c6', 'd20060e9-1ca7-49fb-a2e9-3720f5cab397'}
layer_moves, unexpected = [], []
for uid in set(bt) & set(at):
    old, new = canonical(bt[uid], bn), canonical(at[uid], an)
    if one(old, 'layer') and one(old, 'layer')[1] == 'In1.Cu':
        one(old, 'layer')[1] = 'In2.Cu'
        layer_moves.append(uid)
    if old != new:
        unexpected.append(uid)
check('Original copper preserved apart from obsolete can links and three signal-layer moves',
      removed == allowed_removed and not (set(at) - set(bt)) and not unexpected and len(layer_moves) == 3,
      {'removed_obsolete_GND_segments': sorted(removed), 'L2_to_L3_segments': sorted(layer_moves),
       'unexpected_changes': unexpected, 'segments_after': len(all_(after, 'segment')),
       'vias_after': len(all_(after, 'via'))})
unrouted_moves = json.loads((SNAP / 'moved-footprint-copper.json').read_text())
check('Three repositioned passives had no original routed copper touching their pads',
      all(not v['nearby_original_copper'] for v in unrouted_moves.values()), unrouted_moves)

cu = [n[1] for n in one(after, 'layers')[1:] if n[1].endswith('.Cu')]
stack = all_(one(one(after, 'setup'), 'stackup'), 'layer')
copper = [float(one(n, 'thickness')[1]) for n in stack if one(n, 'type')[1] == 'copper']
thickness = sum(float(one(n, 'thickness')[1]) for n in stack if one(n, 'thickness'))
zones = all_(after, 'zone')
check('Six layers and requested nominal copper weights recorded',
      cu == ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu'] and
      copper == [.07, .0175, .0175, .0175, .0175, .07] and abs(thickness - 1.6) < 1e-9,
      {'copper_mm': copper, 'nominal_total_mm_including_mask': thickness,
       'status': 'geometry target, not a fabricator-approved stackup'})
check('Filled GND reference zones on L2 and L5', len(zones) == 2 and
      {one(z, 'layer')[1] for z in zones} == {'In1.Cu', 'In4.Cu'} and
      all(one(z, 'net_name')[1] == 'GND' and all_(z, 'filled_polygon') for z in zones))

bdrc = json.loads((SNAP / 'before-drc.json').read_text())
adrc = json.loads((SNAP / 'after-drc.json').read_text())
signature = lambda v: (v['type'], tuple(sorted(i['uuid'] for i in v.get('items', []))))
known = {signature(v) for v in bdrc['violations']}
new_violations = [v for v in adrc['violations'] if signature(v) not in known]
check('No newly introduced native PCB DRC violations', not new_violations,
      {'before_violations': len(bdrc['violations']), 'after_violations': len(adrc['violations']),
       'before_unconnected': len(bdrc['unconnected_items']), 'after_unconnected': len(adrc['unconnected_items']),
       'remaining_by_type': dict(Counter(v['type'] for v in adrc['violations'])), 'new': new_violations})
berc = json.loads((SNAP / 'before-erc.json').read_text())
aerc = json.loads((SNAP / 'after-erc.json').read_text())
erc_items = lambda r: [v for s in r['sheets'] for v in s['violations']]
old_erc, new_erc = erc_items(berc), erc_items(aerc)
check('ERC retains baseline warnings with no errors or new findings',
      {signature(v) for v in new_erc} == {signature(v) for v in old_erc} and
      all(v['severity'] != 'error' for v in new_erc),
      {'before': len(old_erc), 'after': len(new_erc), 'severity': dict(Counter(v['severity'] for v in new_erc))})

report = {'status': 'pass' if all(c['passed'] for c in checks) else 'fail',
          'scope': 'Revision invariants only; PCB remains partially routed and is not ready for fabrication.',
          'checks': checks,
          'checked_sha256': {str(p.relative_to(PROJECT)): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in sorted(PROJECT.glob('*.kicad_*')) if p.suffix in ['.kicad_pcb', '.kicad_sch']}}
(HERE / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(report['status'], len(checks), 'checks')
for c in checks:
    if not c['passed']:
        print('FAIL:', c['check'], c['evidence'])
sys.exit(0 if report['status'] == 'pass' else 1)
