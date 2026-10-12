from pathlib import Path
import pcbnew as p,json,shutil,sys
r=Path(__file__).resolve().parent;s=r/'ntc_prepare/ShiroFOC_Manual.kicad_pcb';d=r/('ntc_imu_'+sys.argv[1])/ 'ShiroFOC_Manual.kicad_pcb';d.parent.mkdir(exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(s.with_suffix(ext),d.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(s.parent/name,d.parent/name)
if not (d.parent/'libs').exists():(d.parent/'libs').symlink_to((s.parent/'libs').resolve(),target_is_directory=True)
b=p.LoadBoard(str(s));removed=[];added=[];keep=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() not in ['d04e1ded-c943-4c81-aa4f-c115969ee95d','45457d05-838e-4522-9d90-511cfb65d0ba','1b4f795c-e389-45e0-8123-8eb1a9875948']:continue
 removed.append(t.m_Uuid.AsString());b.Remove(t);continue
 q=t.Duplicate();keep.extend([t,q]);pos=p.VECTOR2I(p.FromMM(-12.3),p.FromMM(float(sys.argv[1])))
 if isinstance(t,p.PCB_VIA):q.SetPosition(pos)
 else:
  for method,pt in [('SetStart',t.GetStart()),('SetEnd',t.GetEnd())]:
   if abs(pt.x/1e6+12.3)<.001 and abs(pt.y/1e6-4.8)<.001:getattr(q,method)(pos)
 b.Add(q);added.append(q.m_Uuid.AsString());removed.append(t.m_Uuid.AsString());b.Remove(t)
(d.parent/'imu_changes.json').write_text(json.dumps(dict(removed_ids=removed,new_ids=added),indent=2));p.SaveBoard(str(d),b)
