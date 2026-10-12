"""Read-only targeted VBUS placement geometry; native KiCad Python."""
import hashlib
import json
import math
from pathlib import Path
import pcbnew as p

out = Path(__file__).resolve().parent
source = out.parent / 'before/ShiroFOC_Manual.kicad_pcb'
old = out.parent.parent / 'placement_pass1_2026-10-11/final/ShiroFOC_Manual.kicad_pcb'
b = p.LoadBoard(str(source))
previous = p.LoadBoard(str(old))
refs = ['R103', 'R105', 'R106', 'C108', 'U602', 'U4', 'J502']

def xy(v):
    return [p.ToMM(v.x), p.ToMM(v.y)]

def footprint(f):
    return {
        'ref': f.GetReference(), 'value': f.GetValue(),
        'position_mm': xy(f.GetPosition()), 'rotation_deg': f.GetOrientationDegrees(),
        'layer': b.GetLayerName(f.GetLayer()),
        'pads': [{'number': a.GetNumber(), 'net': a.GetNetname(),
                  'position_mm': xy(a.GetPosition())} for a in f.Pads()]
    }

def gap_mm(s1, s2):
    # Native shape collision monotone in clearance; precision 1 um.
    lo, hi = 0, p.FromMM(50)
    if s1.Collide(s2, 0):
        return 0.0
    while hi - lo > 1000:
        mid = (lo + hi) // 2
        if s1.Collide(s2, mid):
            hi = mid
        else:
            lo = mid
    return round(p.ToMM(hi), 3)

ids = {'18ff63e2-7daf-4616-934d-d753322ca6e7',
       '3cdf0cd6-13a2-4d3f-96e9-2a5bf21c73de',
       'a1fd5174-15d9-4ab9-b27c-6934df88d367'}
stubs = []
for t in b.GetTracks():
    if t.m_Uuid.AsString() not in ids:
        continue
    distances = []
    shape = t.GetEffectiveShape()
    for f in b.GetFootprints():
        for pad in f.Pads():
            if not pad.IsOnLayer(p.B_Cu):
                continue
            d = gap_mm(shape, pad.GetEffectiveShape(p.B_Cu))
            distances.append({'ref': f.GetReference(), 'pad': pad.GetNumber(),
                              'net': pad.GetNetname(), 'edge_gap_mm': d})
    stubs.append({'uuid': t.m_Uuid.AsString(), 'net': t.GetNetname(),
                  'start_mm': xy(t.GetStart()), 'end_mm': xy(t.GetEnd()),
                  'nearest_back_pads': sorted(distances, key=lambda d:d['edge_gap_mm'])[:5]})

result = {
    'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'previous_source': str(old),
    'current': {r:footprint(b.FindFootprintByReference(r)) for r in refs},
    'previous': {r:footprint(previous.FindFootprintByReference(r)) for r in refs},
    'reassigned_stubs_geometry': stubs,
    'measurement_note': 'Native KiCad effective copper shapes; edge gaps rounded up to nearest 0.001 mm. No source changes.'
}
(out / 'geometry.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'reassigned_stubs_geometry':stubs}, indent=2))
