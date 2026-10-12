from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parent;s=r/'ov2_route/ShiroFOC_Manual.kicad_pcb';d=r/'ov2_fixed/ShiroFOC_Manual.kicad_pcb';d.parent.mkdir(exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(s.with_suffix(ext),d.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(s.parent/name,d.parent/name)
if not (d.parent/'libs').exists():(d.parent/'libs').symlink_to((s.parent/'libs').resolve(),target_is_directory=True)
b=p.LoadBoard(str(s)); removed=[];added=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() not in ['67985fa4-c7a0-4094-be6c-c7f7ded5c078','1d864028-d5be-48d4-8c71-06595e4f8c39','012c38e1-822b-4d7f-b919-2bae112dc796']:continue
 q=t.Duplicate()
 if isinstance(t,p.PCB_VIA):q.SetPosition(p.VECTOR2I(p.FromMM(-16.275),p.FromMM(-21.6)))
 else:
  for method,pt in [('SetStart',t.GetStart()),('SetEnd',t.GetEnd())]:
   if abs(pt.x/1e6+15.774999)<.001 and abs(pt.y/1e6+21.6)<.001:getattr(q,method)(p.VECTOR2I(p.FromMM(-16.275),p.FromMM(-21.6)))
 b.Add(q);added.append(q.m_Uuid.AsString());removed.append(t.m_Uuid.AsString());b.Remove(t)
man=p.SETTINGS_MANAGER();man.LoadProject(str(s.with_suffix('.kicad_pro')));pr=man.GetProject(str(s.with_suffix('.kicad_pro')));b.SetProject(pr);b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity();f=p.ZONE_FILLER(b);f.Fill(b.Zones());p.SaveBoard(str(d),b)
c=json.loads((r/'ov2_prepare/changes.json').read_text());c['allowed_replacement_uuids']+=removed;c['ov1_via_shift_added']=added;(d.parent/'changes.json').write_text(json.dumps(c,indent=2))
