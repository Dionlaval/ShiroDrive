#!/usr/bin/env python3
"""Package the exact reviewed release, refusing stale files."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
manifest=ROOT/'ShiroFOC_KiCad/outputs/release_manifest.json'
data=json.loads(manifest.read_text())
assert data['status']=='LAYOUT_RELEASE','Visual review is not complete'
for name,digest in data['files'].items():
 assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,f'Stale release file: {name}'
out=ROOT/'releases';out.mkdir(exist_ok=True)
archive=out/'ShiroFOC_A1_Drawing_layout_handoff.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name in sorted(data['files']):z.write(ROOT/name,'ShiroFOC/'+name)
 z.write(manifest,'ShiroFOC/'+str(manifest.relative_to(ROOT)))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None,'Archive integrity failure'
 for name,digest in data['files'].items():
  assert hashlib.sha256(z.read('ShiroFOC/'+name)).hexdigest()==digest,name
digest=hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix('.zip.sha256').write_text(f'{digest}  {archive.name}\n')
print(f'PASS: {len(data["files"])+1} files; {archive.stat().st_size/1048576:.2f} MiB; all archived hashes verified\n{archive}')
