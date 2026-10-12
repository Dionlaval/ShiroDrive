"""Merge isolated placement/copper changes while retaining other source objects."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,'/Users/dionlava/.codex/skills/kicad/scripts')
from sexp_parser import parse,find_first
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'before/ShiroFOC_Manual.kicad_pcb'
def blocks(text):
 depth=0;quoted=False;escaped=False;start=None;out=[]
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
    raw=text[start:i+1];node=parse(raw);u=find_first(node,'uuid')
    ref=next((v[2] for v in node if isinstance(v,list) and v[:2]==['property','Reference']),'') if node[0]=='footprint' else ''
    out.append(dict(start=start,end=i+1,kind=node[0],uuid=u[1] if u else '',ref=ref,raw=raw,node=node));start=None
 assert depth==0 and not quoted
 return out
def fpgeometry(o):
 n=o['node'];return [find_first(n,'at'),find_first(n,'layer')]
text=SOURCE.read_text();original=blocks(text);old={q['uuid']:q for q in original if q['uuid']}
changes={};removals={};added={};summary={}
files=[HERE/'brake/ShiroFOC_Manual.kicad_pcb',HERE/'phase/ShiroFOC_Manual.kicad_pcb']
for path in files:
 candidate=blocks(path.read_text());byid={q['uuid']:q for q in candidate if q['uuid']}
 updates=[];deleted=[];new=[]
 for u,o in old.items():
  if o['kind'] not in ['footprint','segment','arc','via']:continue
  if u not in byid:
   assert o['kind']!='footprint',('Unexpected footprint deletion',o['ref'])
   assert u not in changes,('merge conflict',u)
   removals[u]=str(path);deleted.append(u);continue
  n=byid[u]
  changed=fpgeometry(o)!=fpgeometry(n) if o['kind']=='footprint' else o['node']!=n['node']
  if changed:
   assert u not in removals
   assert u not in changes or changes[u]['node']==n['node'],('conflicting update',u)
   changes[u]=n;updates.append(o['ref'] or u)
 for u,n in byid.items():
  if u in old or n['kind'] not in ['footprint','segment','arc','via']:continue
  assert u not in added;added[u]=n;new.append(n['ref'] or u)
 summary[str(path.relative_to(HERE))]={'updated':updates,'removed_copper':deleted,'added':new}
parts=[];cursor=0
for o in original:
 parts.append(text[cursor:o['start']]);u=o['uuid']
 if u in changes:parts.append(changes[u]['raw'])
 elif u not in removals:parts.append(o['raw'])
 cursor=o['end']
parts.append(text[cursor:]);result=''.join(parts);last=result.rfind(')')
result=result[:last]+''.join('\n\t'+q['raw'] for q in added.values())+'\n'+result[last:]
(HERE/'merged.kicad_pcb').write_text(result)
manifest={'source_sha256':hashlib.sha256(text.encode()).hexdigest(),'candidates':summary,'updated_objects':list(changes),'removed_objects':list(removals),'added_objects':list(added)}
(HERE/'merge_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(summary,indent=2))
