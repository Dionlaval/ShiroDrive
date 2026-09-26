import wx
app=wx.App(False)
import pcbnew as k,json,xml.etree.ElementTree as E
from pathlib import Path
P=Path('/Users/dionlava/Documents/GitHub/ShiroDrive/ShiroFOC/Manual_Rebuild');R=P/'review/schematic_review_2026-09-26/implementation';rows=json.loads((R/'cad_inventory.json').read_text());net=E.parse(R/'netlist.xml');b=k.BOARD();nets={};pinmap={}
for n in net.findall('.//nets/net'):
 name=n.get('name')
 if name.startswith('unconnected-'):continue
 item=k.NETINFO_ITEM(b,name);b.Add(item);nets[name]=item
 for x in n.findall('node'):pinmap[x.get('ref'),x.get('pin')]=name
for i,row in enumerate(rows):
 p=Path(row['path']);fp=k.FootprintLoad(str(p.parent),p.stem);assert fp
 b.Add(fp);fp.SetReference(row['ref']);fp.SetValue(row['value']);fp.SetPosition(k.VECTOR2I(k.FromMM(20+50*(i%12)),k.FromMM(20+30*(i//12))))
 for pad in fp.Pads():
  name=pinmap.get((row['ref'],pad.GetNumber()))
  if name:pad.SetNet(nets[name])
fn=R/'pad_mapping_fixture.kicad_pcb';k.SaveBoard(str(fn),b);r=k.LoadBoard(str(fn));count=0;bridge={}
for fp in r.GetFootprints():
 for pad in fp.Pads():
  expected=pinmap.get((fp.GetReference(),pad.GetNumber()),'');assert pad.GetNetname()==expected,(fp.GetReference(),pad.GetNumber(),pad.GetNetname(),expected);count+=1
 if fp.GetReference() in ['U1','U2','U3']:
  bridge[fp.GetReference()]=[{'pad':p.GetNumber(),'net':p.GetNetname()} for p in fp.Pads()]
report={'native_pcb_roundtrip':True,'footprints':len(list(r.GetFootprints())),'pads_checked':count,'bridge_pad_nets':bridge,'note':'Validation fixture only; netlist assignments made programmatically, no placement/routing/DFM claim. Actual draft PCB untouched.'}
(R/'pad_fixture_validation.json').write_text(json.dumps(report,indent=2));print('Native PCB fixture reloaded:',report['footprints'],'footprints',count,'pads verified')
