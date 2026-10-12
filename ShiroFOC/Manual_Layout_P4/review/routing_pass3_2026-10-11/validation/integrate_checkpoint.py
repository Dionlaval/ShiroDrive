"""Merge declared additions into merged_08 and validate, without writing main P4."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import pcbnew as p

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / 'merged_08/ShiroFOC_Manual.kicad_pcb'
BEFORE = ROOT / 'before/ShiroFOC_Manual.kicad_pcb'
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('destination', type=Path)
ap.add_argument('deltas', type=Path, nargs='+')
args = ap.parse_args()
dst = args.destination.resolve()
assert dst.parent.parent == ROOT and dst.parent.name.startswith('merged_')
assert not dst.exists(), 'A frozen checkpoint must never be overwritten'
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == '50472e0a2f1a7ba792589dc73dc0080b39ec80e8b543991150fb515b0d1c73aa'

def run(name, command):
    with (dst.parent / (name + '.log')).open('w') as out:
        result = subprocess.run([str(x) for x in command], stdout=out, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(name + ' failed; see its log')
    return name

dst.parent.mkdir(parents=True, exist_ok=True)
run('merge', [sys.executable, ROOT/'merge_deltas.py', BASE, dst, *args.deltas])
allow = json.loads((BASE.parent/'allowed_changes.json').read_text())
all_removed = set(allow['all_accepted_replacement_uuids'])
moves = {x['uuid']: x for x in allow['footprint_moves']}
for manifest in args.deltas:
    delta = json.loads(manifest.read_text())
    all_removed.update(delta.get('removed_ids', delta.get('delete_ids', [])))
    for move in delta.get('footprint_moves', []):
        if move['uuid'] in moves:
            assert moves[move['uuid']]['new'] == move['old']
            moves[move['uuid']]['new'] = move['new']
        else:
            moves[move['uuid']] = move
baseline = p.LoadBoard(str(BEFORE))
baseline_ids = {t.m_Uuid.AsString() for t in baseline.GetTracks()}
allow.update(all_accepted_replacement_uuids=sorted(all_removed),
             allowed_replacement_uuids=sorted(all_removed & baseline_ids),
             footprint_moves=list(moves.values()))
allow_path = dst.parent / 'allowed_changes.json'
allow_path.write_text(json.dumps(allow, indent=2)+'\n')
commands = [
    ('drc', [CLI, 'pcb', 'drc', '--format', 'json', '-o', dst.parent/'drc.json', dst]),
    ('connectivity', [sys.executable, HERE/'connectivity_regression.py', BEFORE, dst, dst.parent/'connectivity.json']),
    ('provenance', [sys.executable, HERE/'check_provenance.py', '--baseline', BASE, '--candidate', dst,
                    *[v for d in args.deltas for v in ('--delta', d)], '--output', dst.parent/'provenance.json']),
    ('planes', [sys.executable, HERE/'plane_and_returns.py', '--baseline', BEFORE, '--candidate', dst,
                '--output', dst.parent/'planes.json']),
    ('quality', [sys.executable, HERE/'route_quality.py', '--baseline', BEFORE, '--candidate', dst,
                 '--output', dst.parent/'quality.json']),
]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    tasks = [pool.submit(run, name, command) for name, command in commands]
    for task in tasks:
        print(task.result(), 'completed', flush=True)
run('validation', [sys.executable, HERE/'validate_routing.py', '--baseline', BEFORE, '--candidate', dst,
    '--baseline-drc', BEFORE.parent/'drc.json', '--candidate-drc', dst.parent/'drc.json',
    '--allow-replaced-uuids', allow_path, '--allow-footprint-moves', allow_path,
    '--output', dst.parent/'validation.json'])
v = json.loads((dst.parent/'validation.json').read_text())
c = json.loads((dst.parent/'connectivity.json').read_text())
print(json.dumps({'candidate': str(dst), 'sha256': hashlib.sha256(dst.read_bytes()).hexdigest(),
                  'structural_status': v['status'], 'drc': v['candidate_drc'],
                  'connectivity_status': c['status']}, indent=2))
