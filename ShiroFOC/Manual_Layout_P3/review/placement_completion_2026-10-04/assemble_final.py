"""Build final P3 by replacing only explicitly movable native PCB objects.

Run with Python 3.12. Writes a review artifact, never the working file. Original
text for protected footprints, protected copper, outline, setup, nets, groups
and layers is retained byte-for-byte.
"""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,'/Users/dionlava/.codex/skills/kicad/scripts')
from sexp_parser import parse,find_first

HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'placement_manifest.json').read_text())
source=(HERE/'baseline.kicad_pcb').read_text()
candidate=(HERE/'candidate/ShiroFOC_Manual.kicad_pcb').read_text()
assert hashlib.sha256(source.encode()).hexdigest()==manifest['source_sha256']

def blocks(text):
    depth=0;quoted=False;escaped=False;start=None;result=[]
    for i,ch in enumerate(text):
        if quoted:
            if escaped:escaped=False
            elif ch=='\\':escaped=True
            elif ch=='"':quoted=False
            continue
        if ch=='"':quoted=True
        elif ch=='(':
            if depth==1:start=i
            depth+=1
        elif ch==')':
            depth-=1
            if depth==1 and start is not None:
                raw=text[start:i+1];node=parse(raw)
                uuid=find_first(node,'uuid');ref=''
                if node[0]=='footprint':
                    ref=next(v[2] for v in node if isinstance(v,list) and v[:2]==['property','Reference'])
                result.append({'start':start,'end':i+1,'kind':node[0],'uuid':uuid[1] if uuid else '', 'ref':ref,'raw':raw})
                start=None
    assert depth==0 and not quoted
    return result

original=blocks(source);modified=blocks(candidate)
old={q['uuid']:q for q in original if q['uuid']};new={q['uuid']:q for q in modified if q['uuid']}
move_ids=set(manifest['moved_copper'])|{rec['from']['uuid'] for rec in manifest['moved_references'].values()}
remove_ids=set(manifest['removed_drawings']);add_ids=set(manifest['added_drawings'])
assert move_ids<=old.keys() and move_ids<=new.keys()
assert add_ids==new.keys()-old.keys()
assert remove_ids==old.keys()-new.keys()
assert all(new[u]['kind'] in ['gr_line','gr_text','gr_circle'] for u in add_ids)
assert all(old[u]['kind'] in ['gr_text'] for u in remove_ids)
result=[];cursor=0
for item in original:
    result.append(source[cursor:item['start']])
    if item['uuid'] in move_ids:result.append(new[item['uuid']]['raw'])
    elif item['uuid'] not in remove_ids:result.append(item['raw'])
    cursor=item['end']
result.append(source[cursor:]);final=''.join(result)
ending=final.rfind(')')
annotations=''.join('\n\t'+(q['raw'].replace('(type default)','(type dash)').replace('(type solid)','(type dash)') if q['kind'] in ['gr_line','gr_circle'] else q['raw']) for q in modified if q['uuid'] in add_ids)
final=final[:ending]+annotations+'\n'+final[ending:]
final_blocks=blocks(final);final_byid={q['uuid']:q for q in final_blocks if q['uuid']}
unchanged=set(old)-move_ids-remove_ids
assert all(final_byid[u]['raw']==old[u]['raw'] for u in unchanged)
assert {q['ref'] for q in final_blocks if q['kind']=='footprint'}=={q['ref'] for q in original if q['kind']=='footprint'}
assert not any(q['ref'].startswith('TP') for q in final_blocks if q['kind']=='footprint')
target=HERE/'final.kicad_pcb';target.write_text(final)
report={'protected_native_objects_retained_byte_for_byte':len(unchanged),'protected_footprints':len(manifest['protected_references']),'protected_tracks_and_vias':len(manifest['fixed_copper_uuids']),'changed_footprints':len(manifest['moved_references']),'relocated_tracks_and_vias':len(manifest['moved_copper']),'new_copper_items':0,'new_footprints':0,'test_points':0,'non_copper_guides_added':len(add_ids),'obsolete_labels_removed':len(remove_ids),'source_sha256':manifest['source_sha256'],'final_sha256':hashlib.sha256(final.encode()).hexdigest()}
(HERE/'preservation_check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
