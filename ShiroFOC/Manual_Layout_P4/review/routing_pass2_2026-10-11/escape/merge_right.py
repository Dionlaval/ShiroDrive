import pcbnew as p,json,shutil
from pathlib import Path
r=Path(__file__).resolve().parent;before=r.parent/'before/ShiroFOC_Manual.kicad_pcb';right=r/'right/ShiroFOC_Manual.kicad_pcb';source=r.parent/'combined1/ShiroFOC_Manual.kicad_pcb';out=r/'right_merged/ShiroFOC_Manual.kicad_pcb';out.parent.mkdir(parents=True,exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(source.with_suffix(ext),out.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(source.parent/name,out.parent/name)
for name in ['libs','lib','footprints','symbols']:
 if (source.parent/name).exists() and not (out.parent/name).exists():(out.parent/name).symlink_to((source.parent/name).resolve(),target_is_directory=True)
manager=p.SETTINGS_MANAGER();manager.LoadProject(str(source.with_suffix('.kicad_pro')));project=manager.GetProject(str(source.with_suffix('.kicad_pro')))
old=p.LoadBoard(str(before));candidate=p.LoadBoard(str(right));original={t.m_Uuid.AsString() for t in old.GetTracks()};ct=list(candidate.GetTracks());newids={t.m_Uuid.AsString() for t in ct};removed=original-newids;added=newids-original
b=p.LoadBoard(str(source));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False);tracks=list(b.GetTracks());keep=[]
assert removed <= {t.m_Uuid.AsString() for t in tracks}
for t in tracks:
 if t.m_Uuid.AsString() in removed:b.Remove(t)
for t in ct:
 if t.m_Uuid.AsString() in added:
  a=t.Duplicate();a.m_Uuid.Clone(t.m_Uuid);a.SetParent(b);a.SetNetCode(t.GetNetCode());b.Add(a);keep.append(a)
b.BuildConnectivity();filler=p.ZONE_FILLER(b);filler.Fill(b.Zones());p.SaveBoard(str(out),b)
delta={'source':str(before),'candidate':str(right),'delete_ids':sorted(removed),'new_ids':sorted(added),'removed_nets':sorted(set(t.GetNetname() for t in old.GetTracks() if t.m_Uuid.AsString() in removed)),'reason':'Reroute the I2C SDA and external-feedback select barriers to reserve legal FDCAN TX/RX MCU fanouts while preserving all prior connected pads.'};(r/'right/delta.json').write_text(json.dumps(delta,indent=2));print('Deleted',len(removed),'Added',len(added))
