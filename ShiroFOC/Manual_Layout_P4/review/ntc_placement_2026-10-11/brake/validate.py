from pathlib import Path
import pcbnew as p
import json,re

HERE=Path(__file__).resolve().parent
a=p.LoadBoard(str(HERE.parent/'before/ShiroFOC_Manual.kicad_pcb'))
b=p.LoadBoard(str(HERE/'ShiroFOC_Manual.kicad_pcb'))
def pt(q):return(q.x,q.y)
def fp_record(f):
 return dict(uuid=f.m_Uuid.AsString(),ref=f.GetReference(),value=f.GetValue(),pos=pt(f.GetPosition()),angle=f.GetOrientationDegrees(),layer=f.GetLayer(),locked=f.IsLocked(),path=f.GetPath().AsString(),pads=sorted([(q.m_Uuid.AsString(),q.GetNumber(),q.GetNetname(),pt(q.GetPosition()),pt(q.GetSize()),pt(q.GetDrillSize())) for q in f.Pads()]))
def track_record(t):
 return dict(uuid=t.m_Uuid.AsString(),type=t.GetClass(),net=t.GetNetname(),start=pt(t.GetStart()),end=pt(t.GetEnd()),layer=t.GetLayer(),width=t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth(),drill=t.GetDrillValue() if isinstance(t,p.PCB_VIA) else None)
af={f.GetReference():fp_record(f) for f in a.GetFootprints()};bf={f.GetReference():fp_record(f) for f in b.GetFootprints()}
at={t.m_Uuid.AsString():track_record(t) for t in a.GetTracks()};bt={t.m_Uuid.AsString():track_record(t) for t in b.GetTracks()}
changed_fp=[r for r in af if af[r]!=bf.get(r)]
changed_tracks=[u for u in at if at[u]!=bt.get(u)]
pa={(r,q[1],q[0]):q[2] for r,f in af.items() for q in f['pads']};pb={(r,q[1],q[0]):q[2] for r,f in bf.items() for q in f['pads']}
old=json.loads((HERE/'baseline_drc.json').read_text());new=json.loads((HERE/'drc.json').read_text())
key=lambda v:(v['type'],tuple(sorted(i['uuid'] for i in v['items'])))
before={key(v) for v in old['violations']}
added=[v for v in new['violations'] if key(v) not in before]
scoped=[v for v in new['violations'] if any(re.search(r'\b(R511|R512)\b',i['description']) for i in v['items'])]
result=dict(changed_footprints=changed_fp,footprint_additions=sorted(set(bf)-set(af)),footprint_removals=sorted(set(af)-set(bf)),changed_track_via_uuids=changed_tracks,track_via_count_before=len(at),track_via_count_after=len(bt),all_pad_net_assignments_preserved=pa==pb,connector_J502_unchanged=af['J502']==bf['J502'],C505_D505_unchanged=all(af[r]==bf[r] for r in ['C505','D505']),drc_before=len(old['violations']),drc_after=len(new['violations']),new_drc_findings=added,moved_footprint_drc_findings=scoped,notes=['DRC comparison keys type + involved UUIDs.','Zone filling is refreshed in candidate and may alter connectivity counts; no routed copper was added or removed.'])
assert changed_fp==['R511','R512'] or set(changed_fp)=={'R511','R512'}
assert not changed_tracks and at.keys()==bt.keys() and pa==pb
assert not added and not scoped
(HERE/'validation.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
