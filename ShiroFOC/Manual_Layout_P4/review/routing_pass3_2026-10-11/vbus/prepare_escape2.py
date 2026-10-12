from pathlib import Path
import json,shutil
import pcbnew as p

r=Path(__file__).resolve().parent.parent
src=r/'before/ShiroFOC_Manual.kicad_pcb';dst=r/'vbus/prepared2/ShiroFOC_Manual.kicad_pcb'
dst.parent.mkdir(parents=True,exist_ok=True)
for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:
    shutil.copy2(src.parent/name,dst.parent/name)
for name in ['libs']:
    if (src.parent/name).exists() and not (dst.parent/name).exists():(dst.parent/name).symlink_to((src.parent/name).resolve(),target_is_directory=True)
manager=p.SETTINGS_MANAGER();manager.LoadProject(str(src.with_suffix('.kicad_pro')))
b=p.LoadBoard(str(src));b.SetProject(manager.GetProject(str(src.with_suffix('.kicad_pro'))));b.SynchronizeNetsAndNetClasses(False)
uid=lambda q:q.m_Uuid.AsString();vec=lambda q:p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1]))
f=next(f for f in b.GetFootprints() if f.GetReference()=='C108');old=f.GetPosition()
move={'uuid':uid(f),'reference':f.GetReference(),'old':{'position_nm':[old.x,old.y],'angle_deg':f.GetOrientationDegrees()},'new':{'position_nm':[old.x,old.y],'angle_deg':f.GetOrientationDegrees()}}
f.SetPosition(p.VECTOR2I(*move['new']['position_nm']))
removed=['981ec8e4-fca2-4402-9b73-0ac75e3b8ae3','ecf12b11-f579-47f3-be16-080c6b7ad46c']
objects=[t for t in b.GetTracks() if uid(t) in removed]
assert len(objects)==2 and all(t.GetNetname()=='FEEDBACK_I_H3' for t in objects)
for t in objects:b.Remove(t)
net=next(n for n in b.GetNetInfo().NetsByNetcode().values() if n.GetNetname()=='FEEDBACK_I_H3')
points=[(-8.899999,5.5),(-9.55,5.5),(-10.875,6.825),(-10.875,12.975),(-10.225,13.625)]
new=[]
for a,c in zip(points,points[1:]):
    t=p.PCB_TRACK(b);t.SetStart(vec(a));t.SetEnd(vec(c));t.SetLayer(8);t.SetWidth(p.FromMM(.1524));t.SetNet(net);b.Add(t);new.append(uid(t))
via=p.PCB_VIA(b);via.SetPosition(vec((-10.21,7.45)));via.SetWidth(p.FromMM(.5));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetFrontTentingMode(p.TENTING_MODE_TENTED);via.SetBackTentingMode(p.TENTING_MODE_TENTED)
via.SetNet(next(n for n in b.GetNetInfo().NetsByNetcode().values() if n.GetNetname()=='VBUS_SENSE'));b.Add(via)
b.BuildConnectivity();p.SaveBoard(str(dst),b)
manifest={'source':str(src),'candidate':str(dst),'allowed_replacement_uuids':removed,'footprint_moves':[],
          'groups':[{'id':'feedback_I_escape_detour','net':'FEEDBACK_I_H3','removed_items':removed,'new_items':new},
                    {'id':'VBUS_MCU_escape_via','net':'VBUS_SENSE','new_items':[uid(via)]}]}
(dst.parent/'delta.json').write_text(json.dumps(manifest,indent=2)+'\n')
(r/'vbus/allowed_replacements2.json').write_text(json.dumps(removed,indent=2)+'\n')
(r/'vbus/allowed_footprint_moves2.json').write_text(json.dumps({'footprint_moves':[]},indent=2)+'\n')
print(dst)
