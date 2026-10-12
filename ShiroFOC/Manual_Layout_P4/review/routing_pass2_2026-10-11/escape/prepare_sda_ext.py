from pathlib import Path
import json,shutil,pcbnew as p
r=Path(__file__).resolve().parent;source=r.parent/'before/ShiroFOC_Manual.kicad_pcb';out=r/'sda_ext_ripped/ShiroFOC_Manual.kicad_pcb';out.parent.mkdir(parents=True,exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(source.with_suffix(ext),out.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(source.parent/name,out.parent/name)
for name in ['libs','lib','footprints','symbols']:
 if (source.parent/name).exists() and not (out.parent/name).exists():(out.parent/name).symlink_to((source.parent/name).resolve(),target_is_directory=True)
nets=['I2C2_SDA','EXT_FEEDBACK_SELECT']
manager=p.SETTINGS_MANAGER();manager.LoadProject(str(source.with_suffix('.kicad_pro')));project=manager.GetProject(str(source.with_suffix('.kicad_pro')));b=p.LoadBoard(str(source));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False)
tracks=list(b.GetTracks());removed=[]
for t in tracks:
 if t.GetNetname() in nets:
  removed.append({'uuid':t.m_Uuid.AsString(),'net':t.GetNetname(),'layer':t.GetLayer(),'start':[p.ToMM(t.GetStart().x),p.ToMM(t.GetStart().y)],'end':[p.ToMM(t.GetEnd().x),p.ToMM(t.GetEnd().y)],'type':'via' if t.Type()==p.PCB_VIA_T else 'track'});b.Remove(t)
b.BuildConnectivity();p.SaveBoard(str(out),b);(r/'sda_ext_ripped/removed.json').write_text(json.dumps(removed,indent=2));print('Removed',len(removed),'selected signal items')
