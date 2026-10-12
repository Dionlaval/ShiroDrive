import pcbnew as p,json
from pathlib import Path
r=Path(__file__).resolve().parent;path=r/'sequential/ShiroFOC_Manual.kicad_pcb';b=p.LoadBoard(str(path));new=set(u for c in json.loads(path.with_suffix('.routes.json').read_text())['connections']for u in c['new_items']);tracks=list(b.GetTracks());vec=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y));layers=list(b.GetEnabledLayers().CuStack())
for label,x,y in [('INPUT',-7.8,4.9),('EXT_SENSOR',-8.5,4.475)]:
 v=p.PCB_VIA(b);v.SetPosition(vec(x,y));v.SetWidth(p.FromMM(.5));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);hits=[]
 for t in tracks:
  if t.m_Uuid.AsString()not in new:continue
  for l in layers:
   if t.IsOnLayer(l) and v.GetEffectiveShape(l).Collide(t.GetEffectiveShape(l),p.FromMM(.15)):
    hits.append({'net':t.GetNetname(),'uuid':t.m_Uuid.AsString(),'layer':b.GetLayerName(l),'start':p.ToMM(t.GetStart()),'end':p.ToMM(t.GetEnd())});break
 print(label, json.dumps(hits))
