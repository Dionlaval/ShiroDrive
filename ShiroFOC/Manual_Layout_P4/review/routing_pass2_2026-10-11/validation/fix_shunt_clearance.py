"""Shorten the isolated free end of a preliminary sense segment to restore clearance."""
from pathlib import Path
import json
import shutil
import pcbnew as p

root=Path(__file__).resolve().parent.parent
out=root/'validation/shunt'
out.mkdir(exist_ok=True)
for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:
    shutil.copy2(root/'before'/name,out/name)
if not (out/'libs').exists():
    (out/'libs').symlink_to((root/'before/libs').resolve(),target_is_directory=True)
b=p.LoadBoard(str(root/'before/ShiroFOC_Manual.kicad_pcb'))
b.BuildConnectivity()
old_id='9eea7e47-98c4-4188-864e-c62034cbf76a'
old=next(t for t in b.GetTracks() if t.m_Uuid.AsString()==old_id)
connected=b.GetConnectivity()
assert not list(connected.GetConnectedPads(old))
assert not list(connected.GetConnectedTracks(old))
offset=p.VECTOR2I(p.FromMM(.125),p.FromMM(.125))
new=p.PCB_TRACK(b)
new.SetStart(old.GetStart()+offset);new.SetEnd(old.GetEnd())
new.SetWidth(p.FromMM(.1524));new.SetLayer(old.GetLayer());new.SetNetCode(old.GetNetCode())
xy=lambda v:[p.ToMM(v.x),p.ToMM(v.y)]
manifest={'source':str(root/'before/ShiroFOC_Manual.kicad_pcb'),
          'reason':'Eliminate the existing P-to-N sense-guide clearance violation by shortening its isolated P free end 0.1768 mm along the existing diagonal; the remaining path is unchanged.',
          'prior_pad_connections':0,'prior_copper_connections':0,
          'removed_items':[old_id],'allowed_replacement_uuids':[old_id],
          'new_items':[new.m_Uuid.AsString()],
          'before':{'start_mm':xy(old.GetStart()),'end_mm':xy(old.GetEnd())},
          'after':{'start_mm':xy(new.GetStart()),'end_mm':xy(new.GetEnd())},
          'limitation':'This repairs clearance only. Both preliminary Kelvin sense branches still need completion.'}
b.Remove(old);b.Add(new)
b.BuildConnectivity()
assert not list(b.GetConnectivity().GetConnectedPads(new))
assert not list(b.GetConnectivity().GetConnectedTracks(new))
p.SaveBoard(str(out/'ShiroFOC_Manual.kicad_pcb'),b)
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
