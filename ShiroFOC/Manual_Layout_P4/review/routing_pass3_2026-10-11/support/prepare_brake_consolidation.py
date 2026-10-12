from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parents[1];s=r/'merged_08/ShiroFOC_Manual.kicad_pcb';d=r/'support/brake_consolidate/ShiroFOC_Manual.kicad_pcb';d.parent.mkdir(exist_ok=True)
for ext in['.kicad_pro','.kicad_dru']:shutil.copy2(s.with_suffix(ext),d.with_suffix(ext))
for name in['fp-lib-table','sym-lib-table']:shutil.copy2(s.parent/name,d.parent/name)
if not(d.parent/'libs').exists():(d.parent/'libs').symlink_to((s.parent/'libs').resolve(),target_is_directory=True)
b=p.LoadBoard(str(s));ret=[];removed=[];ids=['acf5ed9a-e17c-437c-b160-690d8b1c14b4','933668ef-c32a-4b6b-aaaa-0f8449f49e2f']
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString()in ids:ret.append(t);removed.append(t.m_Uuid.AsString());b.Remove(t)
net=next(n for n in b.GetNetInfo().NetsByNetcode().values()if n.GetNetname()=='NTC_BRAKE');t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(-8.6),p.FromMM(7.0)));t.SetEnd(p.VECTOR2I(p.FromMM(-8.565),p.FromMM(7.24)));t.SetWidth(p.FromMM(.1524));t.SetLayer(p.F_Cu);t.SetNet(net);b.Add(t);ret.append(t);added=[t.m_Uuid.AsString()]
(d.parent/'changes.json').write_text(json.dumps({'source':str(s),'removed_ids':removed,'new_ids':added},indent=2));p.SaveBoard(str(d),b)
