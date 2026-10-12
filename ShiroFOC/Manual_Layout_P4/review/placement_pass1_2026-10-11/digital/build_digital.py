from pathlib import Path
from xml.etree import ElementTree as ET
import pcbnew as p
import json, shutil, hashlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SRC=ROOT/'ShiroFOC_Manual.kicad_pcb'
b=p.LoadBoard(str(SRC)); b.BuildConnectivity()
fs={f.GetReference():f for f in b.GetFootprints()}
xy=lambda q:[p.ToMM(q.x),p.ToMM(q.y)]
pos=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
uid=lambda o:o.m_Uuid.AsString()
def state(f):return dict(uuid=uid(f),xy=xy(f.GetPosition()),angle=f.GetOrientationDegrees(),side='B' if f.IsFlipped() else 'F')
before={r:state(f) for r,f in fs.items()}

plan={
 'U701':(-5,-3.6,-90,'F'), 'C701':(-7.1,-2.4,90,'F'), 'C702':(-7.1,-4.25,-90,'F'),
 'R308':(-2.2,-2.95,0,'F'), 'R715':(-2.2,-4.25,0,'F'),
 'R309':(4.9,-2.4,0,'B'), 'R611':(4.9,-.65,180,'B'),
 'R313':(-7.2,3.3,90,'B'), 'R314':(-6.15,3.15,90,'B'),
 'U602':(-6.1675,18.85,0,'B'),
 'C603':(-.6,20.6,0,'B'), 'C605':(-11.6,18.1,0,'B'),
 'R305':(-1.2,18.2,0,'B'), 'R306':(-.6,19.4,0,'B'), 'R307':(-1.2,16.9,0,'B'),
 'C607':(-10.1,-7.3,90,'F'),
 'Q301':(-14.4,8.1,-90,'F'), 'R304':(-13.25,9.1,-90,'F')
}

# Remove precisely the four segments physically attached to moved Q301/R304.
remove_ids={'924017b5-a6a9-44b5-ac44-51af2976e904','4b873155-98d3-4ccc-af57-9579073efa47','94dbd570-4367-4b8f-8a45-c58c4d22c3f8','0861e07d-549d-4c93-be70-740cadcf26a6'}
removed=[]
for t in list(b.GetTracks()):
 if uid(t) in remove_ids:
  removed.append(dict(uuid=uid(t),net=t.GetNetname(),start=xy(t.GetStart()),end=xy(t.GetEnd()),reason='Q301/R304 moved to clear connector and each other; only directly attached obsolete stubs removed'))
  b.RemoveNative(t)

# U602 has one isolated via attached to pin 10 and no attached tracks.
via_id='f14f4022-ffef-42f9-bcec-a4d18adb697d'
v=next(t for t in b.GetTracks() if uid(t)==via_id)
assert isinstance(v,p.PCB_VIA)
vbefore=dict(xy=xy(v.GetPosition()),diameter=p.ToMM(v.GetWidth()),drill=p.ToMM(v.GetDrillValue()))
v.Move(pos(0,18.85-before['U602']['xy'][1]))
v.SetWidth(p.FromMM(.5));v.SetDrill(p.FromMM(.3))
copper_moves=[dict(uuid=via_id,net=v.GetNetname(),before=vbefore,after=dict(xy=xy(v.GetPosition()),diameter=.5,drill=.3),reason='Isolated pin-10 via follows U602 and adopts requested 0.5/0.3 mm geometry')]

for r,(x,y,a,side) in plan.items():
 f=fs[r]
 if f.IsFlipped() != (side=='B'):f.Flip(f.GetPosition(),False)
 f.SetOrientationDegrees(a);f.SetPosition(pos(x,y))

# Add the actual schematic R618 with matching library footprint, fields, path and pad nets.
netlist=ET.parse(str(ROOT/'review/layout_review_2026-10-11/schematic_netlist.xml'))
c=next(c for c in netlist.findall('.//components/comp') if c.get('ref')=='R618')
lib,name=c.findtext('footprint').split(':')
f=p.FootprintLoad('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/'+lib+'.pretty',name)
assert f is not None
f.SetFPID(p.LIB_ID(lib,name));f.SetReference('R618');f.SetValue(c.findtext('value'))
f.SetPath(p.KIID_PATH(c.find('sheetpath').get('tstamps')+c.findtext('tstamps')))
for field in c.findall('./fields/field'):
 if field.get('name') not in ['Footprint','Description','Datasheet']:f.SetField(field.get('name'),field.text or '')
f.SetField('Datasheet',c.findtext('datasheet') or '')
f.Reference().SetVisible(False);f.Value().SetVisible(False)
nets={n.GetNetname():n for n in b.GetNetsByName().values()}
padnets={node.get('pin'):n.get('name') for n in netlist.findall('.//nets/net') for node in n.findall('node') if node.get('ref')=='R618'}
for q in f.Pads():q.SetNet(nets[padnets[q.GetNumber()]])
f.SetPosition(pos(-12.5,-7.3));f.SetOrientationDegrees(90);b.Add(f);fs['R618']=f

dst=HERE/'candidate.kicad_pcb'
p.SaveBoard(str(dst),b)
for ext in ['kicad_pro','kicad_dru']:
 if (ROOT/('ShiroFOC_Manual.'+ext)).exists():shutil.copy2(ROOT/('ShiroFOC_Manual.'+ext),HERE/('candidate.'+ext))
manifest=dict(source=str(SRC),source_sha256=hashlib.sha256(SRC.read_bytes()).hexdigest(),candidate=str(dst),footprint_edits={r:dict(before=before[r],after=state(fs[r])) for r in plan},footprint_additions={'R618':dict(**state(fs['R618']),schematic_path=fs['R618'].GetPath().AsString(),pad_nets=padnets)},removed_copper=removed,moved_copper=copper_moves,notes=['No primary project file modified.','Existing USB/CAN ICs and their connected geometry retained.','U604/C606 retained, its new ILIM resistor and output capacitor placed adjacent.','U601 stays locked at (0,0) B; U4 and all half bridges remain fixed.','No new routing added; only isolated via moved and obsolete attached stubs removed.'])
(HERE/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(dict(footprints=len(fs),moved=len(plan),added=['R618'],removed_tracks=len(removed),moved_vias=1,candidate=str(dst))))
