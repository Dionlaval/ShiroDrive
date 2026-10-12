from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parent.parent;src=r/'digital/ShiroFOC_Manual.kicad_pcb';out=r/'engine/optimized/base/ShiroFOC_Manual.kicad_pcb';out.parent.mkdir(parents=True,exist_ok=True)
selected=['Net-(U601-MISO)','SPI3_SCK_MCU','SPI3_MOSI_MCU']
rows=[x for x in json.loads(src.with_suffix('.routes.json').read_text())['connections'] if x['net'] in selected]
remove={u for x in rows for u in x['new_items']}
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),out.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,out.parent/name)
for name in ['libs','lib','footprints','symbols']:
 if (src.parent/name).exists() and not (out.parent/name).exists():(out.parent/name).symlink_to((src.parent/name).resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));project=m.GetProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False)
tracks=list(b.GetTracks())
for t in tracks:
 if t.m_Uuid.AsString() in remove:b.Remove(t)
b.BuildConnectivity();p.SaveBoard(str(out),b)
(out.parent.parent/'removed_connections.json').write_text(json.dumps(rows,indent=2));print(out)
