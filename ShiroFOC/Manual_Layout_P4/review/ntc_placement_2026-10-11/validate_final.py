"""Validate the eight-resistor placement change against the saved user edits."""
from pathlib import Path
import pcbnew as p
import json,hashlib
R=Path(__file__).resolve().parent
a=p.LoadBoard(str(R/'before/ShiroFOC_Manual.kicad_pcb'))
b=p.LoadBoard(str(R/'final/ShiroFOC_Manual.kicad_pcb'))
af={f.GetReference():f for f in a.GetFootprints()}
bf={f.GetReference():f for f in b.GetFootprints()}
allowed={'R511','R512','R701','R702','R703','R711','R712','R713'}
fail=[]
def uid(o):return o.m_Uuid.AsString()
def xy(v):return [round(p.ToMM(v.x),6),round(p.ToMM(v.y),6)]
def loc(f):return [xy(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayerName()]
def electrical(f):
 return {'uuid':uid(f),'value':f.GetValue(),'footprint':f.GetFPID().GetUniStringLibId(),
 'path':f.GetPath().AsString(),'dnp':f.IsDNP(),
 'fields':{q.GetName():q.GetText() for q in f.GetFields()},
 'pads':{uid(q):[q.GetNumber(),q.GetNetname(),xy(q.GetSize()),xy(q.GetDrillSize())] for q in f.Pads()}}
assert set(af)==set(bf),'Footprint set changed'
moves={}
for ref in af:
 if electrical(af[ref])!=electrical(bf[ref]):fail.append('Electrical/identity change: '+ref)
 if loc(af[ref])!=loc(bf[ref]):moves[ref]={'before':loc(af[ref]),'after':loc(bf[ref])}
if set(moves)!=allowed:fail.append('Unexpected move set: '+str(set(moves)))
def copper(board):
 result={}
 for t in board.GetTracks():
  width=t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth()
  row=[t.GetClass(),t.GetNetname(),t.GetLayerName(),xy(t.GetStart()),xy(t.GetEnd()),width]
  if isinstance(t,p.PCB_VIA):row+=[t.GetDrillValue(),t.GetLayerSet().FmtHex()]
  if isinstance(t,p.PCB_ARC):row+=[xy(t.GetMid())]
  result[uid(t)]=row
 return result
if copper(a)!=copper(b):fail.append('Track/via change')
outline=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(outline)
dnp=[]
for ref,f in bf.items():
 fields={q.GetName():q.GetText() for q in f.GetFields()}
 if f.IsDNP() or fields.get('Assembly','').upper()=='DNP':
  dnp.append(ref)
  if outline.Contains(f.GetPosition()):fail.append('DNP placed on board: '+ref)
for ref in allowed:
 f=bf[ref];f.BuildCourtyardCaches();poly=f.GetCourtyard(p.B_CrtYd if f.IsFlipped() else p.F_CrtYd)
 for j in range(poly.OutlineCount()):
  ring=poly.COutline(j)
  for i in range(ring.PointCount()):
   if not outline.Contains(ring.CPoint(i)):fail.append('Moved courtyard outside board: '+ref)
old=json.loads((R/'baseline_refilled/drc.json').read_text())
new=json.loads((R/'final/drc.json').read_text())
key=lambda v:(v['type'],tuple(sorted(i['uuid'] for i in v['items'])))
base={key(v) for v in old['violations']}
introduced=[v for v in new['violations'] if v['severity']=='error' and key(v) not in base]
if introduced:fail.append('New DRC errors: '+str(len(introduced)))
def stats(d):return {'errors':sum(v['severity']=='error' for v in d['violations']),'warnings':sum(v['severity']=='warning' for v in d['violations']),'unconnected':len(d['unconnected_items'])}
result={'status':'PASS' if not fail else 'FAIL','failures':fail,'moves':moves,
 'footprints':len(bf),'all_electrical_identities_unchanged':not any('Electrical' in x for x in fail),
 'copper_unchanged':copper(a)==copper(b),'dnp_remaining_staged':sorted(dnp),
 'preserved_user_placements':{ref:loc(bf[ref]) for ref in ['J502','R103','R105','R106']},
 'before_drc':stats(old),'after_drc':stats(new),'introduced_errors':introduced,
 'final_sha256':hashlib.sha256((R/'final/ShiroFOC_Manual.kicad_pcb').read_bytes()).hexdigest()}
(R/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','failures','footprints','copper_unchanged','before_drc','after_drc','final_sha256']},indent=2))
assert not fail,fail
