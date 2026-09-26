from pathlib import Path
import sys,json,hashlib,collections,xml.etree.ElementTree as ET
sys.path.insert(0,'/tmp/cascade_work')
from edit import read,children,one,val
P=Path(__file__).resolve().parents[1];b=read(P/'ShiroFOC_Manual.kicad_pcb')
fps={val(f,'Reference'):f for f in children(b,'footprint')};xml=ET.parse(P/'review/current.xml');components={c.get('ref'):c for c in xml.findall('.//components/comp')}
assert fps.keys()==components.keys()
rename=json.loads((P/'review/library_adjustments.json').read_text())['escaped_net_names'];expected={}
for n in xml.findall('.//nets/net'):
 name=rename.get(n.get('name'),n.get('name'))
 for node in n.findall('node'):expected[(node.get('ref'),node.get('pin'))]=name
errors=[];missing=[]
for r,f in fps.items():
 assert f[1]==components[r].findtext('footprint'),r
 for p in children(f,'pad'):
  net=one(p,'net');want=expected.get((r,p[1]))
  if want and (not net or net[2]!=want):errors.append([r,p[1],want,net])
 for rr,pin in expected:
  if rr==r and not any(p[1]==pin for p in children(f,'pad')):missing.append([r,pin])
assert not errors,errors
assert sorted(missing)==[['U205','19'],['U205','20']],missing
hashes=json.loads((P/'review/source_hashes.json').read_text());changed=[p for p,h in hashes.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h];assert not changed,changed
assert not children(b,'segment') and not children(b,'via') and not children(b,'zone')
drc=json.loads((P/'review/drc.json').read_text());erc=json.loads((P/'review/erc.json').read_text());erc_count=sum(len(s.get('violations',[])) for s in erc.get('sheets',[]));assert erc_count==0
out={'status':'rough placement for manual routing; not fabrication-ready','footprints':len(fps),'pad_net_errors':errors,'missing_nonphysical_pins':missing,'original_source_files_unchanged':not changed,'erc_violations':erc_count,'board_tracks_vias_zones':0,'drc_categories':dict(collections.Counter(v['type'] for v in drc['violations'])),'unconnected_items':len(drc['unconnected_items']),'schematic_parity_issues':len(drc['schematic_parity']),'final_placement_adjustments':'C1/C5 moved 0.15 mm left after manifest creation to meet power clearance'}
(P/'review/validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
