from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parent;src=r.parent/'before/ShiroFOC_Manual.kicad_pcb';dst=r/'mosi_direct/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(parents=True,exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not (dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));project=m.GetProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False)
removed=[t.m_Uuid.AsString() for t in b.GetTracks() if t.GetNetname()=='SPI3_MOSI_MCU' and (t.GetLayer() in [p.F_Cu,6]) and t.m_Uuid.AsString()!='046a681f-c7bc-48dc-bce1-59542cd1d109'];tracks=list(b.GetTracks());assert set(removed)<={t.m_Uuid.AsString() for t in tracks}
for t in tracks:
 if t.m_Uuid.AsString() in removed:b.Remove(t)
net=next(n for n in b.GetNetInfo().NetsByNetcode().values() if n.GetNetname()=='SPI3_MOSI_MCU');coords=[(-4.849937,2.755),(-4.849937,3.950062),(-4.449999,4.35)];added=[]
for a,c in zip(coords,coords[1:]):
 t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));t.SetEnd(p.VECTOR2I(p.FromMM(c[0]),p.FromMM(c[1])));t.SetLayer(p.F_Cu);t.SetWidth(p.FromMM(.1524));t.SetNet(net);b.Add(t);added.append(t)
b.BuildConnectivity();filler=p.ZONE_FILLER(b);filler.Fill(b.Zones());p.SaveBoard(str(dst),b);(dst.parent/'delta.json').write_text(json.dumps({'source':str(src),'candidate':str(dst),'removed_ids':removed,'new_ids':[t.m_Uuid.AsString() for t in added],'footprint_moves':[]},indent=2));print(dst)
