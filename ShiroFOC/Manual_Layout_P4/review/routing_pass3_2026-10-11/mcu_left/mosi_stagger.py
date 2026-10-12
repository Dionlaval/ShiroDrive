from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parent;src=r/'brake_try/ShiroFOC_Manual.kicad_pcb';dst=r/'brake_stagger/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(parents=True,exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not (dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));project=m.GetProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(project);b.SynchronizeNetsAndNetClasses(False);tracks=list(b.GetTracks());removed=[];added=[]
for t in tracks:
 if t.GetNetname()=='SPI3_MOSI_MCU':removed.append(t.m_Uuid.AsString());b.Remove(t)
nets={a.GetNetname():a for a in b.GetNetInfo().NetsByNetcode().values()}
def path(net,layer,coords):
 for a,c in zip(coords,coords[1:]):
  t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));t.SetEnd(p.VECTOR2I(p.FromMM(c[0]),p.FromMM(c[1])));t.SetLayer(layer);t.SetWidth(p.FromMM(.1524));t.SetNet(nets[net]);b.Add(t);added.append(t)
def via(net,xy):
 t=p.PCB_VIA(b);t.SetPosition(p.VECTOR2I(p.FromMM(xy[0]),p.FromMM(xy[1])));t.SetWidth(p.FromMM(.5));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(nets[net]);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(t);added.append(t)
path('SPI3_MOSI_MCU',p.F_Cu,[(-4.849937,2.755),(-4.849937,3.24),(-4.15,3.94),(-4.15,4.75)])
via('SPI3_MOSI_MCU',(-4.15,4.75))
path('SPI3_MOSI_MCU',p.B_Cu,[(-4.15,4.75),(-4.8,4.75),(-5.25,4.3),(-5.51,4.3),(-6.15,3.66)])
via('Net-(U601-MOSI)',(-4.7,4.1))
path('Net-(U601-MOSI)',p.B_Cu,[(-6.15,2.64),(-5.55,3.25),(-5.2,3.25),(-4.7,3.75),(-4.7,4.1)])
path('Net-(U601-MOSI)',6,[(-3.8,2.65),(-4.7,3.55),(-4.7,4.1)])
b.BuildConnectivity();filler=p.ZONE_FILLER(b);filler.Fill(b.Zones());p.SaveBoard(str(dst),b);(dst.parent/'delta.json').write_text(json.dumps({'source':str(src),'candidate':str(dst),'removed_ids':removed,'new_ids':[t.m_Uuid.AsString() for t in added],'footprint_moves':[]},indent=2));print(dst)
