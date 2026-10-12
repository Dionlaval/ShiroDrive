import pcbnew as p,json,shutil
from pathlib import Path
r=Path(__file__).resolve().parent;src=r/'guarded/ShiroFOC_Manual.kicad_pcb';dst=r/'cleaned/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
print("source",src,"destination",dst,flush=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro').resolve()));b=p.LoadBoard(str(src));b.SetProject(m.GetProject(str(src.with_suffix('.kicad_pro').resolve())));b.SynchronizeNetsAndNetClasses(False);d=json.loads(src.with_suffix('.ground_manifest.json').read_text());removed=set(u for g in d['groups']if g['pad']=='R905.2'for u in g['new_items']);ts=list(b.GetTracks())
for t in ts:
 if t.m_Uuid.AsString()in removed:b.Remove(t)
print("pruned",len(removed),"remaining",len(list(b.GetTracks())),flush=True)
b.BuildConnectivity();filler=p.ZONE_FILLER(b);result=filler.Fill(b.Zones());print("filled",result,flush=True);saved=p.SaveBoard(str(dst),b);print("saved",saved,"exists",dst.exists(),flush=True);d['groups']=[g for g in d['groups']if g['pad']!='R905.2'];d['skipped'].append({'pad':'R905.2','skipped':'Both tested via sites split the 3V3 network; entire connection group pruned'});d['candidate']=str(dst);dst.with_suffix('.ground_manifest.json').write_text(json.dumps(d,indent=2)+'\n')
