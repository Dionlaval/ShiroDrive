from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parent.parent;src=r/'brake/brake_path/ShiroFOC_Manual.kicad_pcb';dst=r/'brake/sck_seed/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
b=p.LoadBoard(str(src));vec=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y));uid=lambda q:q.m_Uuid.AsString()
tracks=list(b.GetTracks());removed=next(t for t in tracks if uid(t)=='5d3b3fae-7066-40be-8764-90d371ba9333');b.Remove(removed)
net=next(n for n in b.GetNetInfo().NetsByNetcode().values() if n.GetNetname()=='SPI3_SCK_MCU')
v=p.PCB_VIA(b);v.SetPosition(vec(-7.85,3.95));v.SetWidth(p.FromMM(.5));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetFrontTentingMode(p.TENTING_MODE_TENTED);v.SetBackTentingMode(p.TENTING_MODE_TENTED);v.SetNet(net);b.Add(v)
pts=[(-7.85,3.95),(-7.2,3.3),(-7.2,3.21)]
for a,c in zip(pts,pts[1:]):
 t=p.PCB_TRACK(b);t.SetStart(vec(*a));t.SetEnd(vec(*c));t.SetWidth(p.FromMM(.1524));t.SetLayer(p.B_Cu);t.SetNet(net);b.Add(t)
b.BuildConnectivity();p.SaveBoard(str(dst),b)
