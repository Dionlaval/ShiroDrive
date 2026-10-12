"""Read-only filled-plane source contact and signal return transition audit."""
from pathlib import Path
import argparse, hashlib, json, math
import pcbnew as p
ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True)
ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
a=ap.parse_args();b=p.LoadBoard(str(a.candidate));base=p.LoadBoard(str(a.baseline));b.BuildConnectivity()
uid=lambda x:x.m_Uuid.AsString()
xy=lambda x:[round(p.ToMM(x.x),6),round(p.ToMM(x.y),6)]
old={uid(x) for x in base.GetTracks()};old_tracks=list(base.GetTracks());old_vias={uid(x):x for x in old_tracks if isinstance(x,p.PCB_VIA)};old_pads=[q for f in base.GetFootprints() for q in f.Pads()];tracks=list(b.GetTracks());pads=[(f,q) for f in b.GetFootprints() for q in f.Pads()]
zones=[z for z in b.Zones() if z.GetNetname() in ('3V3','GND')]
plane_rows=[{'net':z.GetNetname(),'uuid':uid(z),'layers':[{'name':b.GetLayerName(l),'id':l,'filled_regions':z.GetFilledPolysList(l).OutlineCount()} for l in z.GetLayerSet().Seq()]} for z in zones]
power=[(z,l) for z in zones if z.GetNetname()=='3V3' for l in z.GetLayerSet().Seq()]
source=next(q for f,q in pads if f.GetReference()=='U204' and q.GetNumber()=='5')
todo=[(source,[uid(source)])];seen=set();contact=None
while todo:
    item,path=todo.pop()
    if uid(item) in seen:continue
    seen.add(uid(item))
    if any(item.IsOnLayer(l) and z.HitTestFilledArea(l,item.GetPosition()) for z,l in power):
        contact={'item_uuid':uid(item),'position_mm':xy(item.GetPosition()),'physical_path_uuids':path};break
    if item.GetNetname()!='3V3':continue
    for nextitem in list(b.GetConnectivity().GetConnectedTracks(item))+list(b.GetConnectivity().GetConnectedPads(item)):
        if nextitem.GetNetname()=='3V3' and uid(nextitem) not in seen:todo.append((nextitem,path+[uid(nextitem)]))
grounds=[(z,l) for z in zones if z.GetNetname()=='GND' for l in z.GetLayerSet().Seq()]
stack=list(b.GetEnabledLayers().CuStack())
def references(layer):
    return {l for z,l in grounds if abs(stack.index(l)-stack.index(layer))==1}
gnd=[]
for item,label in [(t,'via') for t in tracks if isinstance(t,p.PCB_VIA)]+[(q,f.GetReference()+'.'+q.GetNumber()) for f,q in pads if q.GetAttribute()==p.PAD_ATTRIB_PTH]:
    if item.GetNetname()=='GND':gnd.append((item,label))
returns=[]
def touched_layers(via,track_list,pad_list):
    touched={track.GetLayer() for track in track_list if not isinstance(track,p.PCB_VIA) and track.GetNetname()==via.GetNetname() and via.GetEffectiveShape(track.GetLayer()).Collide(track.GetEffectiveShape(track.GetLayer()),0)}
    for pad in pad_list:
        if pad.GetNetname()!=via.GetNetname():continue
        for layer in stack:
            if pad.IsOnLayer(layer) and via.GetEffectiveShape(layer).Collide(pad.GetEffectiveShape(layer),0):touched.add(layer)
    return touched
for via in tracks:
    if not isinstance(via,p.PCB_VIA) or via.GetNetname() in ('GND','3V3','VCC','VREF+','VDDA'):continue
    touched=touched_layers(via,tracks,[q for f,q in pads])
    previous=touched_layers(old_vias[uid(via)],old_tracks,old_pads) if uid(via) in old_vias else set()
    if uid(via) in old and touched==previous:continue
    refs=set().union(*(references(l) for l in touched)) if touched else set()
    candidates=[(item,label) for item,label in gnd if all(item.IsOnLayer(l) and any(z.HitTestFilledArea(l,item.GetPosition()) for z,ll in grounds if ll==l) for l in refs)]
    nearest=min(candidates,key=lambda row:math.hypot(row[0].GetPosition().x-via.GetPosition().x,row[0].GetPosition().y-via.GetPosition().y)) if candidates else None
    returns.append({'via_uuid':uid(via),'new_via':uid(via) not in old,'previous_touching_signal_layers':[base.GetLayerName(l) for l in sorted(previous)],'net':via.GetNetname(),'position_mm':xy(via.GetPosition()),
                    'touching_signal_layers':[b.GetLayerName(l) for l in sorted(touched)],
                    'adjacent_reference_layers':[b.GetLayerName(l) for l in sorted(refs)],
                    'changes_ground_reference_plane':len(refs)>1,
                    'nearest_ground_interconnect_uuid':uid(nearest[0]) if nearest else None,
                    'nearest_ground_interconnect_type':nearest[1] if nearest else None,
                    'nearest_ground_interconnect_mm':round(p.ToMM(math.hypot(nearest[0].GetPosition().x-via.GetPosition().x,nearest[0].GetPosition().y-via.GetPosition().y)),3) if nearest else None})
returns.sort(key=lambda r:-(r['nearest_ground_interconnect_mm'] or 0))
result={'candidate':str(a.candidate.resolve()),'sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest(),
        'planes':plane_rows,'source_U204_5_net':source.GetNetname(),'source_U204_5_reaches_3V3_fill':contact is not None,
        'source_contact_evidence':contact,'new_signal_via_returns':returns,
        'reference_change_gaps_over_2mm':[r for r in returns if r['changes_ground_reference_plane'] and (r['nearest_ground_interconnect_mm'] is None or r['nearest_ground_interconnect_mm']>2)],
        'notes':'Direct same-net copper contacts traced to filled power copper. Reference assignment uses immediate adjacent GND planes. Via proximity is geometric, not an impedance or EMI guarantee.'}
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'planes':plane_rows,'source_present':contact is not None,'reference_changes_over2mm':result['reference_change_gaps_over_2mm'],'all_returns':returns},indent=2))
