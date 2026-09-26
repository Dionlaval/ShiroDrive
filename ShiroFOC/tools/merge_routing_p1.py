#!/usr/bin/env python3
"""Retain previously checked ordinary signal routing where the new placement permits it."""
import pcbnew as p
from pathlib import Path
import shutil,json,math
O=Path(__file__).resolve().parents[1]/'ShiroFOC_KiCad_P1/outputs/routing_P1'
b=p.LoadBoard(str(O/'local_candidate.kicad_pcb'));old=p.LoadBoard(str(O/'analog_raw.kicad_pcb'))
nets={n.GetNetname():n for n in b.GetNetInfo().NetsByNetcode().values()};pads=[q for f in b.GetFootprints()for q in f.Pads()];locked=list(b.GetTracks())
critical=set(t.GetNetname()for t in locked)
critical.update(n for n in nets if 'SENSE_'in n or 'OPN_'in n or 'OPP_'in n or 'OPO_'in n or n.startswith(('GHS','GLS','OUT','BOOT')) or 'Q40'in n or 'FORCE_P'in n)
# No long brake switch/gate stubs, nor obsolete supply-cap routes.
critical.update(['Net-(D504-A)','Net-(D501-K)','VM','VCC','VDDA','VREF+'])
accepted=[];rejected=[]
for t in old.GetTracks():
 net=t.GetNetname()
 if net in critical or net not in nets:continue
 l=t.GetLayer();ls=[p.F_Cu,p.B_Cu]if isinstance(t,p.PCB_VIA)else[l]
 cl=.201;safe=True
 box=t.GetBoundingBox();box.Inflate(p.FromMM(.52))
 for q in pads:
  if q.GetNetname()==net or not box.Intersects(q.GetBoundingBox()):continue
  clear=.501 if q.GetNetname()in['VM','OUT1','OUT2','OUT3']or'FORCE_P'in q.GetNetname()else cl
  for ly in ls:
   if q.IsOnLayer(ly) and q.GetEffectiveShape(ly).Collide(t.GetEffectiveShape(ly),p.FromMM(clear)):
    safe=False;break
  if not safe:break
 if safe:
  for q in locked:
   if q.GetNetname()==net or not box.Intersects(q.GetBoundingBox()):continue
   for ly in ls:
    if q.IsOnLayer(ly) and q.GetEffectiveShape(ly).Collide(t.GetEffectiveShape(ly),p.FromMM(cl)):
     safe=False;break
   if not safe:break
 if not safe:rejected.append(net);continue
 if isinstance(t,p.PCB_VIA):
  q=p.PCB_VIA(b);q.SetPosition(t.GetPosition());q.SetWidth(t.GetWidth(p.F_Cu));q.SetDrill(t.GetDrill());q.SetViaType(p.VIATYPE_THROUGH);q.SetLayerPair(p.F_Cu,p.B_Cu);q.SetFrontTentingMode(p.TENTING_MODE_TENTED);q.SetBackTentingMode(p.TENTING_MODE_TENTED)
 else:
  q=p.PCB_TRACK(b);q.SetStart(t.GetStart());q.SetEnd(t.GetEnd());q.SetWidth(t.GetWidth());q.SetLayer(l)
 q.SetNet(nets[net]);q.SetLocked(False);b.Add(q);accepted.append(q.m_Uuid.AsString())
name='merged_candidate'
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(O/('local_candidate'+ext),O/(name+ext))
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(O/(name+'.kicad_pcb')),b)
(O/'merged_tracks.json').write_text(json.dumps(accepted))
print('Accepted',len(accepted),'rejected',len(rejected),'total',len(list(b.GetTracks())))
