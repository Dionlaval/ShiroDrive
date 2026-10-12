from pathlib import Path
import pcbnew as p,shutil,json
R=Path(__file__).resolve().parent.parent;src=R/'ntc_l4/ShiroFOC_Manual.kicad_pcb';dst=R/'power_plane/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for fn in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/fn,dst.parent/fn)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));project=m.GetProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False)
n=next(n for n in b.GetNetInfo().NetsByNetcode().values()if n.GetNetname()=='3V3')
z=p.ZONE(b);z.SetLayer(8);z.SetNet(n);z.SetZoneName('3V3 support distribution L4');z.SetLocalClearance(p.FromMM(.2));z.SetMinThickness(p.FromMM(.2));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
poly=z.Outline();poly.NewOutline()
for x,y in [(-21.8,-16.5),(-12,-16.5),(-12,-14.5),(8.2,-14.5),(8.2,21.8),(-21.8,21.8)]:poly.Append(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
b.Add(z);b.BuildConnectivity();f=p.ZONE_FILLER(b);assert f.Fill(b.Zones());p.SaveBoard(str(dst),b)
(dst.parent/'zone_manifest.json').write_text(json.dumps({'new_zone_uuid':z.m_Uuid.AsString(),'net':'3V3','layer':8,'islands':z.GetFilledPolysList(8).OutlineCount(),'direct_via_connection':True},indent=2));print('3V3 distribution regions',z.GetFilledPolysList(8).OutlineCount())
