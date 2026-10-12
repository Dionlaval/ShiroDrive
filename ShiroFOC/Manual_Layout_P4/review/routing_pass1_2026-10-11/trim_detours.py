from pathlib import Path
import json,shutil
import pcbnew as p
r=Path(__file__).resolve().parent;src=r/'local/ShiroFOC_Manual.kicad_pcb';out=r/'local_trimmed';out.mkdir(exist_ok=True)
b=p.LoadBoard(str(src));manifest=json.loads(src.with_suffix('.routes.json').read_text());remove=set()
for row in manifest['connections']:
 if row['new_items'] and ((row['net']=='VREF+' and row['length_mm']>10) or (row['net']=='NTC_BRAKE' and row['length_mm']>18)):
  remove.update(row['new_items']);row['pruned_reason']='Excessive detour; retry on signal layer';row['pruned_items']=row['new_items'];row['new_items']=[]
items=[t for t in b.GetTracks()if t.m_Uuid.AsString()in remove]
for t in items:b.Remove(t)
for fn in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/fn,out/fn)
if not (out/'libs').exists():(out/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
p.SaveBoard(str(out/src.name),b);(out/'ShiroFOC_Manual.routes.json').write_text(json.dumps(manifest,indent=2));print('Trimmed',len(remove),'items from 2 long detours')
