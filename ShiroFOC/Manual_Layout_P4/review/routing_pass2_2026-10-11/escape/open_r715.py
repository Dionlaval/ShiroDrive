from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parent;source=r/'right_merged/ShiroFOC_Manual.kicad_pcb';out=r/'r715_open/ShiroFOC_Manual.kicad_pcb';out.parent.mkdir(parents=True,exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(source.with_suffix(ext),out.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(source.parent/name,out.parent/name)
for name in ['libs','lib','footprints','symbols']:
 if (source.parent/name).exists() and not (out.parent/name).exists():(out.parent/name).symlink_to((source.parent/name).resolve(),target_is_directory=True)
rows=json.loads((r/'right/ShiroFOC_Manual.routes.json').read_text())['connections'];remove=set(next(a['new_items'] for a in rows if a['net']=='I2C2_SDA' and a['length_mm']<3.0))
manager=p.SETTINGS_MANAGER();manager.LoadProject(str(source.with_suffix('.kicad_pro')));project=manager.GetProject(str(source.with_suffix('.kicad_pro')));b=p.LoadBoard(str(source));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False);tracks=list(b.GetTracks())
for t in tracks:
 if t.m_Uuid.AsString() in remove:b.Remove(t)
b.BuildConnectivity();p.SaveBoard(str(out),b);(r/'r715_open/removed_new_sda.json').write_text(json.dumps(sorted(remove),indent=2))
