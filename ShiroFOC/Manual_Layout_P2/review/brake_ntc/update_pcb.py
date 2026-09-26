from pathlib import Path
import json,xml.etree.ElementTree as E
import wx
app=wx.App(False)
import pcbnew as k
P=Path(__file__).resolve().parents[2];O=P/'review/brake_ntc';path=P/'ShiroFOC_Manual.kicad_pcb';pro=P/'ShiroFOC_Manual.kicad_pro';settings=pro.read_bytes()
b=k.LoadBoard(str(path));before={f.GetReference():(f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.IsFlipped()) for f in b.GetFootprints()}
root=E.parse(O/'current.xml');parts={c.get('ref'):c for c in root.findall('.//components/comp')};nets={n.GetNetname():n for n in b.GetNetInfo().NetsByNetcode().values()};by_pad={}
def esc(s):return s.replace('PA13/SWDIO','PA13{slash}SWDIO').replace('PA14/SWCLK','PA14{slash}SWCLK').replace('I/PWM','I{slash}PWM').replace('W/PWM','W{slash}PWM')
for n in root.findall('.//nets/net'):
 name=esc(n.get('name'))
 if name not in nets:net=k.NETINFO_ITEM(b,name);b.Add(net);nets[name]=net
 for node in n.findall('node'):by_pad[node.get('ref'),node.get('pin')]=(nets[name],node)
placements={'J502':(103.5,149,90),'R511':(109,150,0),'R512':(136.5,143.5,0),'C505':(139,145,0),'D505':(143,145,0)}
for item in json.loads((O/'new_components.json').read_text()):
 r=item['ref'];assert r not in before
 lib,name=item['footprint'].split(':');folder=P/'libs'/f'{lib}.pretty' if lib=='Manual' else Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')/f'{lib}.pretty'
 fp=k.FootprintLoad(str(folder),name);assert fp
 fp.SetReference(r);fp.SetValue(parts[r].findtext('value'));fp.SetFPID(k.LIB_ID(lib,name));b.Add(fp)
 x,y,ang=placements[r];fp.SetPosition(k.VECTOR2I(k.FromMM(x),k.FromMM(y)));fp.Flip(fp.GetPosition(),False);fp.SetOrientationDegrees(ang)
 sp=parts[r].find('sheetpath');fp.SetPath(k.KIID_PATH(sp.get('tstamps')+item['uuid']));fp.SetSheetfile('07_Brake_Chopper.kicad_sch');fp.SetSheetname('Brake chopper')
 fp.Reference().SetLayer(k.B_Fab);fp.Reference().SetTextSize(k.VECTOR2I(k.FromMM(.8),k.FromMM(.8)));fp.Reference().SetTextThickness(k.FromMM(.12));fp.Value().SetVisible(False)
 fp.SetAttributes(fp.GetAttributes() & ~k.FP_EXCLUDE_FROM_BOM)
for fp in b.GetFootprints():
 r=fp.GetReference();fp.SetValue(parts[r].findtext('value'))
 for pad in fp.Pads():
  entry=by_pad.get((r,pad.GetNumber()))
  if entry:
   net,node=entry;pad.SetNet(net)
   pad.SetPinFunction(node.get('pinfunction',''));pad.SetPinType(node.get('pintype',''))
for f in b.GetFootprints():
 if f.GetReference() in before:assert before[f.GetReference()]==(f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.IsFlipped())
# Outside-board guide; bottom-side connector is optional and polarity labelled on silkscreen.
t=k.PCB_TEXT(b);t.SetText('BACK: J502 brake NTC\n1 = NTC / 2 = GND\nTwisted, insulated probe pair');t.SetPosition(k.VECTOR2I(k.FromMM(86),k.FromMM(148)));t.SetLayer(k.User_3);t.SetTextSize(k.VECTOR2I(k.FromMM(.8),k.FromMM(.8)));t.SetTextThickness(k.FromMM(.15));b.Add(t)
k.SaveBoard(str(path),b);pro.write_bytes(settings)
(O/'pcb_placement_check.json').write_text(json.dumps({'existing_footprints_preserved':len(before),'new_bottom_placements':placements,'unchanged_existing_positions_orientations_sides':True},indent=2))
print('Added five bottom-side parts; all existing footprint placements preserved; project settings preserved')
