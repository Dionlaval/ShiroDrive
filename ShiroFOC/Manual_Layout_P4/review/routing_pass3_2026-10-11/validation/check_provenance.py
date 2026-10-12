"""Read-only exact copper provenance audit across declared routing deltas."""
import argparse,json,hashlib
from pathlib import Path
import pcbnew as p
from validate_routing import copper_state,uid
ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--delta',type=Path,action='append',required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
boards=[]
def load(path):
 b=p.LoadBoard(str(path.resolve()));boards.append(b);return {uid(t):copper_state(t)for t in b.GetTracks()}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
expected=load(a.baseline);original=set(expected);provenance={u:str(a.baseline.resolve())for u in expected};failures=[];declared_removed=[];declared_added=[];source_reports=[]
for path in a.delta:
 d=json.loads(path.read_text());source=Path(d['candidate']);items=load(source);source_reports.append({'manifest':str(path.resolve()),'candidate':str(source.resolve()),'sha256':sha(source)})
 if d.get('candidate_sha256')and d['candidate_sha256']!=sha(source):failures.append({'type':'source_hash_mismatch','source':str(source)})
 for u in d.get('removed_ids',d.get('delete_ids',[])):
  if u not in expected:failures.append({'type':'removed_uuid_not_in_predecessor','uuid':u})
  expected.pop(u,None);provenance.pop(u,None);declared_removed.append(u)
 for u in d['new_ids']:
  if u in expected:failures.append({'type':'new_uuid_already_present','uuid':u})
  if u not in items:failures.append({'type':'new_uuid_absent_from_source','uuid':u});continue
  expected[u]=items[u];provenance[u]=str(source.resolve());declared_added.append(u)
actual=load(a.candidate)
for u in sorted(set(expected)|set(actual)):
 if u not in actual:failures.append({'type':'expected_uuid_missing','uuid':u,'accepted_source':provenance[u]});continue
 if u not in expected:failures.append({'type':'unexpected_uuid','uuid':u,'candidate_state':actual[u]});continue
 if actual[u]!=expected[u]:failures.append({'type':'copper_provenance_mismatch','uuid':u,'accepted_source':provenance[u],'differences':{k:{'expected':expected[u].get(k),'actual':actual[u].get(k)}for k in set(expected[u])|set(actual[u])if expected[u].get(k)!=actual[u].get(k)}})
report={'status':'FAIL'if failures else'PASS','baseline':str(a.baseline.resolve()),'baseline_sha256':sha(a.baseline),'candidate':str(a.candidate.resolve()),'candidate_sha256':sha(a.candidate),'accepted_sources':source_reports,'baseline_copper_count':len(original),'candidate_copper_count':len(actual),'unchanged_baseline_uuid_count':len(original&set(actual)),'declared_old_uuid_removals':len(declared_removed),'declared_new_uuid_count':len(declared_added),'fields_checked':['class','net name','layer','layer set','start/end coordinates','arc midpoint','width','per-layer via diameters','via drill','via type','locked'],'failures':failures}
a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(bool(failures))
