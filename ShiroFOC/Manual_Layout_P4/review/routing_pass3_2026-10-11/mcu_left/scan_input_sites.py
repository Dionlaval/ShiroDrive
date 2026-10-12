from pathlib import Path
import json, math, pcbnew as p, numpy as np
r=Path(__file__).resolve().parent;f=r/'input_latest_partial/ShiroFOC_Manual.kicad_pcb'
m=p.SETTINGS_MANAGER();m.LoadProject(str(f.with_suffix('.kicad_pro')));b=p.LoadBoard(str(f));b.SetProject(m.GetProject(str(f.with_suffix('.kicad_pro'))));b.SynchronizeNetsAndNetClasses(False)
mm=p.FromMM;via=p.PCB_VIA(b);via.SetWidth(mm(.5));via.SetDrill(mm(.3));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(0,2)
u4=next(f for f in b.GetFootprints()if f.GetReference()=='U4');u4.BuildCourtyardCaches();court=u4.GetCourtyard(0)
objects=[];holes=[];pads=[];refs={q.m_Uuid.AsString():f.GetReference()+'.'+q.GetNumber()for f in b.GetFootprints()for q in f.Pads()}
for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]:
    if q.GetClass()=='PAD' or q.GetClass()=='PCB_VIA':
        if q.GetClass()=='PCB_VIA' or q.HasDrilledHole():holes.append(q.GetEffectiveHoleShape())
    for l in b.GetEnabledLayers().CuStack():
        if not q.IsOnLayer(l):continue
        s=q.GetEffectiveShape(l);bb=s.BBox();row=(q,l,s,(bb.GetLeft(),bb.GetTop(),bb.GetRight(),bb.GetBottom()),court.Collide(s,0));objects.append(row)
        if q.GetClass()=='PAD':pads.append(row)
seen=np.load(r/'input_point/reached_2.npy');rows=[]
for yy in range(0,seen.shape[0],4):
    for xx in range(0,seen.shape[1],4):
        if not seen[yy,xx]:continue
        x=mm(-22.5+xx*.025);y=mm(-22.5+yy*.025);pos=p.VECTOR2I(x,y);via.SetPosition(pos);vs=via.GetEffectiveShape(0);hs=via.GetEffectiveHoleShape();local=court.Collide(vs,0)
        if any(hs.Collide(h,mm(.450001))for h in holes):continue
        blocked={};padblock=False;sourceblock=False
        for q,l,s,bb,inside in objects:
            if q.GetNetname()=='INPUT_MUX_ENABLE_N':continue
            cl=.150001 if local and inside else .500001 if q.GetNetClassName()=='Power' else .200001
            rad=mm(.25+cl)
            if x<bb[0]-rad or x>bb[2]+rad or y<bb[1]-rad or y>bb[3]+rad:continue
            if not vs.Collide(s,mm(cl)):continue
            if l==2:sourceblock=True;break
            if q.GetClass()!='PCB_TRACK':padblock=True;break
            blocked[q.m_Uuid.AsString()]={'uuid':q.m_Uuid.AsString(),'net':q.GetNetname(),'layer':b.GetLayerName(l),'start':[p.ToMM(q.GetStart().x),p.ToMM(q.GetStart().y)],'end':[p.ToMM(q.GetEnd().x),p.ToMM(q.GetEnd().y)]}
            if len(blocked)>2:break
        if padblock or sourceblock or len(blocked)>2:continue
        rows.append({'position':[round(p.ToMM(x),4),round(p.ToMM(y),4)],'blockers':list(blocked.values())})
rows.sort(key=lambda q:(len(q['blockers']),-q['position'][1]));(r/'input_site_scan.json').write_text(json.dumps(rows,indent=2));print(json.dumps({'count':len(rows),'best':rows[:30]},indent=2))
