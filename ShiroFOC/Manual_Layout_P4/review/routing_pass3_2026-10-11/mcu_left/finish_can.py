from pathlib import Path
import json, shutil, pcbnew as p

root = Path(__file__).resolve().parent
src = root / 'can_checkpoint/ShiroFOC_Manual.kicad_pcb'
dst = root / 'can_final/ShiroFOC_Manual.kicad_pcb'
dst.parent.mkdir(parents=True, exist_ok=True)
for ext in ['.kicad_pro', '.kicad_dru']:
    shutil.copy2(src.with_suffix(ext), dst.with_suffix(ext))
for name in ['fp-lib-table', 'sym-lib-table']:
    shutil.copy2(src.parent/name, dst.parent/name)
if not (dst.parent/'libs').exists():
    (dst.parent/'libs').symlink_to((src.parent/'libs').resolve(), target_is_directory=True)
m = p.SETTINGS_MANAGER()
m.LoadProject(str(src.with_suffix('.kicad_pro')))
project = m.GetProject(str(src.with_suffix('.kicad_pro')))
b = p.LoadBoard(str(src))
b.SetProject(project)
b.SynchronizeNetsAndNetClasses(False)
remove = {
    'a1df0f76-ec85-41bf-a589-e5461c8ccab2',
    'd84561ea-5bbd-470e-9671-39736be58dcf',
    '11661087-23e5-461e-bbed-e72347006f1c',
    'baf52fc5-a4a9-4127-a0ce-ed4da6c712b0',
}
tracks = list(b.GetTracks())
found = [t for t in tracks if t.m_Uuid.AsString() in remove]
assert len(found) == 4
assert all(t.GetNetname() == 'FEEDBACK_I_H3' for t in found)
for t in found:
    b.Remove(t)
b.BuildConnectivity()
filler = p.ZONE_FILLER(b)
filler.Fill(b.Zones())
p.SaveBoard(str(dst), b)
(dst.parent/'obsolete_h3_tail.json').write_text(json.dumps(sorted(remove), indent=2))
print(dst)
