"""Isolated relocation of the brake NTC pull-up/series resistors only."""
from pathlib import Path
import pcbnew as p
import json,shutil,hashlib

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'before'
SRC=SOURCE/'ShiroFOC_Manual.kicad_pcb'
for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:
    shutil.copy2(SOURCE/name,HERE/name)
if not (HERE/'libs').exists():(HERE/'libs').symlink_to(SOURCE/'libs',target_is_directory=True)

settings=p.GetSettingsManager()
assert settings.LoadProject(str(HERE/'ShiroFOC_Manual.kicad_pro'))
project=settings.GetProject(str(HERE/'ShiroFOC_Manual.kicad_pro'))
b=p.LoadBoard(str(SRC));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity()
fs={f.GetReference():f for f in b.GetFootprints()}
xy=lambda q:[p.ToMM(q.x),p.ToMM(q.y)]
def record(f):return dict(uuid=f.m_Uuid.AsString(),xy_mm=xy(f.GetPosition()),angle_deg=f.GetOrientationDegrees(),side='B' if f.IsFlipped() else 'F',pads=[dict(number=q.GetNumber(),net=q.GetNetname(),xy_mm=xy(q.GetPosition())) for q in f.Pads()])
before={r:record(fs[r]) for r in ['R511','R512']}
attached={r:[t.m_Uuid.AsString() for q in fs[r].Pads() for t in b.GetConnectivity().GetConnectedTracks(q)] for r in before}
assert not any(attached.values()), attached

# RAW ends face each other in a compact row immediately above J502 pin 1.
# The row clears the preserved preliminary GLS2 escape at y=14.13 mm.
for ref,x,y,angle in [('R511',-2.3,15.4,0),('R512',-.1,15.4,0)]:
    f=fs[ref]
    if f.IsFlipped():f.Flip(f.GetPosition(),False)
    f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));f.SetOrientationDegrees(angle)

b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones())
dst=HERE/'ShiroFOC_Manual.kicad_pcb';p.SaveBoard(str(dst),b)
manifest=dict(source=str(SRC),source_sha256=hashlib.sha256(SRC.read_bytes()).hexdigest(),candidate=str(dst),footprint_edits={r:dict(before=before[r],after=record(fs[r])) for r in before},new_footprints=[],removed_copper=[],moved_copper=[],attached_copper_before=attached,zone_fill='Refilled in candidate with copied project rules; selective integration only needs the two footprint blocks, then refill combined board.',preserved=['User J502 position/side/orientation','All other footprints including C505 and D505','Every track and via','Schematic pad-net assignments'],rationale='Connector-local 10k pull-up establishes the raw divider; 4.7k series resistor makes the ADC-bound route originate behind input resistance. The existing 100nF capacitor and BAT54SW clamp stay at MCU end. Final ADC-node routing must stay away from PWM and switch nodes; connector-side series resistance does not make the following trace immune to coupled noise.')
(HERE/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest['footprint_edits'],indent=2))
