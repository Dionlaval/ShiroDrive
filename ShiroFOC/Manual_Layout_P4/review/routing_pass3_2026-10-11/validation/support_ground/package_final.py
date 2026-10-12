from pathlib import Path
import pcbnew as p,json,shutil,hashlib
r=Path(__file__).resolve().parent;src=r/'existing_extended/ShiroFOC_Manual.kicad_pcb';dst=r/'final/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro').resolve()));project=m.GetProject(str(src.with_suffix('.kicad_pro').resolve()));b=p.LoadBoard(str(src));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False);ts=list(b.GetTracks());t=next(t for t in ts if t.m_Uuid.AsString()=='aff2b8be-d5b7-4fe9-8fe9-3e53eb430dea');t.SetWidth(p.FromMM(.1524));b.BuildConnectivity();filler=p.ZONE_FILLER(b);assert filler.Fill(b.Zones());assert p.SaveBoard(str(dst),b)
d1=json.loads((r/'cleaned/ShiroFOC_Manual.ground_manifest.json').read_text());d2=json.loads(src.with_suffix('.ground_manifest.json').read_text());groups=d1['groups']+d2['groups']
for g in groups:
 if g['pad']=='R209.2':g['width_mm']=.1524
new=[u for g in groups for u in g['new_items']];manifest={'source':d1['source'],'candidate':str(dst),'candidate_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'removed_ids':[],'new_ids':new,'footprint_moves':[],'groups':groups,'skipped':d2['skipped'],'note':'R905 and initial U602.11 via groups were rejected because refill split the 3V3 network. R209 uses 6 mil to maintain board-edge clearance. All additions stay outside the shared MCU rectangle.'};(dst.parent/'delta.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'sha256':manifest['candidate_sha256'],'groups':len(groups),'items':len(new),'accepted':[g['pad']for g in groups]}))
