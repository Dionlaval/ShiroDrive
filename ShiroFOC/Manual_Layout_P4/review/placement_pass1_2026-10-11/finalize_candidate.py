"""Apply user routing presets and refill isolated merged placement candidate."""
from pathlib import Path
import pcbnew as p
import json,shutil
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[1];OUT=HERE/'final';OUT.mkdir(exist_ok=True)
board=p.LoadBoard(str(HERE/'merged.kicad_pcb'))
changed=[]
for t in board.GetTracks():
 if isinstance(t,p.PCB_VIA) and (t.GetWidth(p.F_Cu)!=p.FromMM(.5) or t.GetDrillValue()!=p.FromMM(.3)):
  changed.append({'uuid':t.m_Uuid.AsString(),'old_diameter_mm':p.ToMM(t.GetWidth(p.F_Cu)),'old_drill_mm':p.ToMM(t.GetDrillValue())})
  t.SetWidth(p.FromMM(.5));t.SetDrill(p.FromMM(.3))
filler=p.ZONE_FILLER(board);filler.Fill(board.Zones())
p.SaveBoard(str(OUT/'ShiroFOC_Manual.kicad_pcb'),board)
pro=json.loads((PROJECT/'ShiroFOC_Manual.kicad_pro').read_text())
ds=pro['board']['design_settings'];ds['track_widths']=[0,.1524,.254];ds['via_dimensions']=[{'diameter':0,'drill':0},{'diameter':.5,'drill':.3}]
ds['rules']['min_via_diameter']=.5
for nc in pro['net_settings']['classes']:
 nc['via_diameter']=.5;nc['via_drill']=.3
 if nc['name'] in ['Default','Analog']:nc['track_width']=.1524
 elif nc['name'] in ['Gate','LogicPower']:nc['track_width']=.254
 # USB width/gap still require the final fabrication stack calculation.
(OUT/'ShiroFOC_Manual.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
for n in ['ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(PROJECT/n,OUT/n)
if not (OUT/'libs').exists():(OUT/'libs').symlink_to(PROJECT/'libs',target_is_directory=True)
(HERE/'via_preset_changes.json').write_text(json.dumps({'normalised_standalone_vias':changed,'track_presets_mm':[.1524,.254],'via_mm':{'diameter':.5,'drill':.3},'embedded_footprint_plated_pads':'preserved'},indent=2)+'\n')
print('Normalized',len(changed),'standalone vias; candidate saved',OUT)
