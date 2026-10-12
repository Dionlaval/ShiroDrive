from pathlib import Path
import json,shutil,pcbnew as p
r=Path(__file__).resolve().parent.parent;source=r/'digital/ShiroFOC_Manual.kicad_pcb';candidate=r/'engine/optimized/fine/ShiroFOC_Manual.kicad_pcb';out=r/'engine/optimized/final/ShiroFOC_Manual.kicad_pcb';out.parent.mkdir(parents=True,exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(source.with_suffix(ext),out.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(source.parent/name,out.parent/name)
for name in ['libs','lib','footprints','symbols']:
 if (source.parent/name).exists() and not (out.parent/name).exists():(out.parent/name).symlink_to((source.parent/name).resolve(),target_is_directory=True)
manager=p.SETTINGS_MANAGER();manager.LoadProject(str(source.with_suffix('.kicad_pro')));project=manager.GetProject(str(source.with_suffix('.kicad_pro')))
b=p.LoadBoard(str(candidate));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False)
old=p.LoadBoard(str(source));tracks=list(old.GetTracks());rows=json.loads(source.with_suffix('.routes.json').read_text())['connections'];restore={x for a in rows if a['net'] in ['SPI3_SCK_MCU','SPI3_MOSI_MCU'] for x in a['new_items']};add=[]
for t in tracks:
 if t.m_Uuid.AsString() in restore:
  new=t.Duplicate();new.m_Uuid.Clone(t.m_Uuid);new.SetParent(b);new.SetNetCode(t.GetNetCode());b.Add(new);add.append(new)
b.BuildConnectivity();filler=p.ZONE_FILLER(b);filler.Fill(b.Zones());p.SaveBoard(str(out),b)
removed=[x for a in rows if a['net']=='Net-(U601-MISO)' for x in a['new_items']]
newrows=[a for a in json.loads(candidate.with_suffix('.routes.json').read_text())['connections'] if a['net']=='Net-(U601-MISO)' and a['new_items']]
delta={'source':str(source),'candidate':str(out),'net':'Net-(U601-MISO)','delete_ids':removed,'new_ids':[u for a in newrows for u in a['new_items']],'old_length_mm':15.240306627408021,'new_length_mm':sum(a['length_mm'] for a in newrows),'old_vias':0,'new_vias':sum(a['vias'] for a in newrows),'connections':newrows}
(out.parent/'delta.json').write_text(json.dumps(delta,indent=2));print(out)
