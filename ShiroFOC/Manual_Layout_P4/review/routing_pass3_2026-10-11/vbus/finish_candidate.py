from pathlib import Path
import pcbnew as p,json,shutil,hashlib
r=Path(__file__).resolve().parent.parent
src=r/'vbus/guided/ShiroFOC_Manual.kicad_pcb';dst=r/'vbus/final/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
manager=p.SETTINGS_MANAGER();manager.LoadProject(str(src.with_suffix('.kicad_pro')))
b=p.LoadBoard(str(src));b.SetProject(manager.GetProject(str(src.with_suffix('.kicad_pro'))));b.SynchronizeNetsAndNetClasses(False)
items={t.m_Uuid.AsString():t for t in b.GetTracks()};vec=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
items['96c7fb5e-9bd6-46c4-ac1f-d43e5d1db948'].SetEnd(vec(-11.7,9.575))
items['3730c1ca-8197-49c3-b535-c5d557555f67'].SetStart(vec(-12.875,1.775))
items['3730c1ca-8197-49c3-b535-c5d557555f67'].SetEnd(vec(-12.95,1.7))
items['9ebfffb5-726f-4ce0-9027-e3b61352e3ec'].SetEnd(vec(-12.875,1.775))
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b)
base=p.LoadBoard(str(r/'before/ShiroFOC_Manual.kicad_pcb'));old={t.m_Uuid.AsString() for t in base.GetTracks()};now={t.m_Uuid.AsString() for t in b.GetTracks()}
manifest={'source':str(r/'before/ShiroFOC_Manual.kicad_pcb'),'candidate':str(dst),
 'candidate_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'footprint_moves':[],
 'allowed_replacement_uuids':sorted(old-now),'removed_items':sorted(old-now),
 'groups':[]}
for net in ['VBUS_SENSE','FEEDBACK_I_H3','NTC_PHASE_C']:
 ts=[t for t in b.GetTracks() if t.GetNetname()==net and t.m_Uuid.AsString() in now-old]
 manifest['groups'].append({'id':net,'net':net,'new_items':[t.m_Uuid.AsString() for t in ts],
   'new_length_mm':sum(p.ToMM(t.GetLength()) for t in ts if not isinstance(t,p.PCB_VIA)),
   'new_vias':sum(isinstance(t,p.PCB_VIA) for t in ts)})
(dst.parent/'delta.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
