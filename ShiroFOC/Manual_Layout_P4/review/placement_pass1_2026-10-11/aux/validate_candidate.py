from pathlib import Path
import pcbnew as p,json,math
r=Path(__file__).resolve().parent;root=r.parents[2]
(r/'fp-lib-table').write_text((root/'fp-lib-table').read_text().replace('${KIPRJMOD}',str(root)))
b=p.LoadBoard(str(r/'candidate.kicad_pcb')); b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(r/'candidate.kicad_pcb'),b)
old=p.LoadBoard(str(r/'baseline.kicad_pcb'));o={f.GetReference():f for f in old.GetFootprints()};n={f.GetReference():f for f in b.GetFootprints()}
changes=[]
for ref,q in n.items():
 a=o[ref]
 if a.GetPosition()!=q.GetPosition() or a.GetOrientationDegrees()!=q.GetOrientationDegrees() or a.GetLayer()!=q.GetLayer():changes.append(ref)
assert sorted(changes)==['C203','R503']
assert len(n)==len(o)
def pads(f):return [(a.GetNumber(),a.GetNetname()) for a in f.Pads()]
assert all(pads(n[r])==pads(o[r]) for r in n)
metrics={}
def length(fa,na,fb,nb,board):
 f={x.GetReference():x for x in board.GetFootprints()}
 p1=next(a for a in f[fa].Pads() if a.GetNumber()==str(na)).GetPosition();p2=next(a for a in f[fb].Pads() if a.GetNumber()==str(nb)).GetPosition()
 return round(math.hypot(p.ToMM(p1.x-p2.x),p.ToMM(p1.y-p2.y)),4)
for name,pair in {'driver_OUT_to_resistor':('U501',5,'R503',1),'resistor_to_gate':('R503',2,'Q501',4)}.items():metrics[name]={'before_mm':length(*pair,old),'after_mm':length(*pair,b)}
res={'only_moved_refs':changes,'component_count_preserved':len(n),'pad_nets_preserved':True,'metrics':metrics,'U205_keepouts_preserved':len(list(n['U205'].Zones()))==len(list(o['U205'].Zones())),'refilled':True}
(r/'validation.json').write_text(json.dumps(res,indent=2));print(json.dumps(res))
