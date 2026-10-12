import json, sys, xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict, Counter
sys.path.insert(0,'/Users/dionlava/.codex/skills/kicad/scripts')
from sexp_parser import parse_file, find_all, find_first, get_value
root=Path('ShiroFOC/Manual_Layout_P4')
out=root/'review/layout_review_2026-10-11'
x=ET.parse(out/'schematic_netlist.xml').getroot()
comp={c.attrib['ref']:c for c in x.find('components')}
sch={}; snets={}
for n in x.find('nets'):
 name=n.attrib['name']; pins={(p.attrib['ref'],p.attrib['pin']) for p in n}
 snets[name]=pins
 for p in pins: sch[p]=name
pcb=parse_file(str(root/'ShiroFOC_Manual.kicad_pcb'))
fps={}; pads=defaultdict(list)
for f in find_all(pcb,'footprint'):
 props={p[1]:p[2] for p in find_all(f,'property')}
 ref=props.get('Reference'); fps[ref]={'footprint':f[1],'props':props,'pads':[]}
 for p in find_all(f,'pad'):
  net=find_first(p,'net'); pn=str(p[1]); name=str(net[2]) if net and len(net)>2 else None
  fps[ref]['pads'].append(pn)
  if pn: pads[(ref,pn)].append(name)
missing=[]; different=[]; pad_missing=[]; extra=[]; propertydiff=[]
for ref,c in comp.items():
 if ref not in fps: missing.append(ref); continue
 for prop,tag in [('Value','value'),('Footprint','footprint')]:
  a=c.findtext(tag); b=fps[ref]['props'].get(prop) if prop=='Value' else fps[ref]['footprint']
  if a!=b: propertydiff.append({'ref':ref,'property':prop,'schematic':a,'pcb':b})
for pin,net in sch.items():
 if pin not in pads: pad_missing.append({'pin':pin,'net':net}); continue
 for bn in set(pads[pin]):
  if bn!=net:
   different.append({'pin':pin,'schematic_net':net,'pcb_net':bn})
for pin,nets in pads.items():
 if pin not in sch and any(nets): extra.append({'pin':pin,'pcb_nets':nets})
sdata=json.load(open(out/'schematic.json'))
res={'native_component_count':len(comp),'native_nets':len(snets),'analyzer_component_count':len({c['reference'] for c in sdata['components']}),'analyzer_nets':len(sdata['nets']),'pcb_footprints':len(fps),'missing_components':missing,'pcb_only_components':sorted(set(fps)-set(comp)),'missing_schematic_pins_on_pcb':pad_missing,'extra_pcb_pad_assignments':extra,'pin_net_name_differences':different,'property_differences':propertydiff,'schematic_components_without_bom':[{ 'ref':r,'properties':[n.attrib for n in c.findall('property')]} for r,c in comp.items() if any(p.attrib.get('name')=='exclude_from_bom' for p in c.findall('property'))]}
json.dump(res,open(out/'schematic_parity.json','w'),indent=2)
print('Saved',out/'schematic_parity.json')
