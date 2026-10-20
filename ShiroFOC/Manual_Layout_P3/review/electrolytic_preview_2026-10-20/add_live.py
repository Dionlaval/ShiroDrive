"""Run in KiCad's scripting console; add only three board-only NC previews."""
from pathlib import Path
import json
import pcbnew as p

root = Path('/Users/dionlava/Documents/GitHub/ShiroDrive/ShiroFOC/Manual_Layout_P3')
out = root / 'review/electrolytic_preview_2026-10-20'
b = p.GetBoard()
expected = root / 'ShiroFOC_Manual.kicad_pcb'
assert Path(b.GetFileName()).resolve() == expected.resolve(), b.GetFileName()
refs = ['C_PREVIEW_BULK1', 'C_PREVIEW_BULK2', 'C_PREVIEW_BULK3']
existing = list(b.GetFootprints())
assert not set(refs) & {f.GetReference() for f in existing}, 'Previews already present'
assert not (out / 'live_before.kicad_pcb').exists(), 'Preserve the previous backup'
name = 'Panasonic_EEVFK_K16_18x16.5'
fps = [p.FootprintLoad(str(root / 'libs/ShiroFOCLib.pretty'), name) for _ in refs]
assert all(fps)
box = b.GetBoardEdgesBoundingBox()
cx = p.ToMM(box.GetCenter().x)
start_y = p.ToMM(box.GetBottom()) + 15
existing_boxes = [f.GetBoundingBox() for f in existing]
for step in range(20):
    y = start_y + 24 * step
    for f, x in zip(fps, [cx-24, cx, cx+24]):
        f.SetPosition(p.VECTOR2I(p.FromMM(x), p.FromMM(y)))
    if not any(f.GetBoundingBox().Intersects(e) for f in fps for e in existing_boxes):
        break
else:
    raise RuntimeError('No clear staging area found')
for ref, f in zip(refs, fps):
    f.SetReference(ref)
    f.SetValue('680uF 63V - placement preview')
    f.SetFPID(p.LIB_ID('ShiroFOCLib', name))
    f.SetAttributes(p.FP_SMD | p.FP_BOARD_ONLY | p.FP_EXCLUDE_FROM_BOM | p.FP_EXCLUDE_FROM_POS_FILES)
    f.Reference().SetVisible(True)
    f.Reference().SetTextSize(p.VECTOR2I(p.FromMM(.8), p.FromMM(.8)))
    f.Value().SetVisible(True)
    for pad in f.Pads():
        pad.SetNetCode(0)
    for model in f.Models():
        model.m_Filename = model.m_Filename.replace('${KICAD9_3DMODEL_DIR}', '/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels')
        assert Path(model.m_Filename).exists(), model.m_Filename
out.mkdir(parents=True, exist_ok=True)
p.SaveBoard(str(out / 'live_before.kicad_pcb'), b)
for f in fps:
    b.Add(f)
p.Refresh()
assert len(list(b.GetFootprints())) == len(existing) + 3
assert all(pad.GetNetCode() == 0 for f in fps for pad in f.Pads())
p.SaveBoard(str(out / 'live_after.kicad_pcb'), b)
p.SaveBoard(str(expected), b)
result = dict(added=[dict(reference=f.GetReference(), value=f.GetValue(),
    x_mm=p.ToMM(f.GetPosition().x), y_mm=p.ToMM(f.GetPosition().y),
    nets=[pad.GetNetCode() for pad in f.Pads()]) for f in fps],
    original_footprint_count=len(existing), new_footprint_count=len(list(b.GetFootprints())),
    source='P2 C101-C103: EEVFK1J681M, 680uF 63V',
    model_note='Existing library uses an approximate 18x17.5 mm envelope for the 18x16.5 mm part.')
(out / 'placement.json').write_text(json.dumps(result, indent=2))
print('Added and saved three 680uF / 63V NC placement previews at y=%.2f mm' % y)
