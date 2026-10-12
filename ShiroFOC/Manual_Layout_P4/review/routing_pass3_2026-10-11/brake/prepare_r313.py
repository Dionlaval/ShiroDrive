from pathlib import Path
import pcbnew as p,json,shutil
r=Path(__file__).resolve().parent.parent;src=r/'merged_03/ShiroFOC_Manual.kicad_pcb';dst=r/'brake/r313_open/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for name in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
b=p.LoadBoard(str(src));vec=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y));uid=lambda q:q.m_Uuid.AsString()
f=next(f for f in b.GetFootprints() if f.GetReference()=='R313');pos=f.GetPosition();move={'uuid':uid(f),'reference':'R313','old':{'position_nm':[pos.x,pos.y],'angle_deg':f.GetOrientationDegrees()},'new':{'position_nm':[pos.x,pos.y-600000],'angle_deg':f.GetOrientationDegrees()}};f.SetPosition(p.VECTOR2I(*move['new']['position_nm']))
tracks=list(b.GetTracks());rem=[]
for t in tracks:
 if t.GetNetname()=='SPI3_SCK_MCU' and t.GetLayer()==p.B_Cu and not isinstance(t,p.PCB_VIA):rem.append(uid(t));b.Remove(t)
 if uid(t) in ['774e8f9b-d154-4edc-ab7b-66c4fa396b3f','b2434500-dfaf-4508-b420-e5668994c0f4']:rem.append(uid(t));b.Remove(t)
net=next(n for n in b.GetNetInfo().NetsByNetcode().values() if n.GetNetname()=='BRAKE_PWM');new=[]
t=p.PCB_TRACK(b);t.SetStart(vec(-6.850441,2.755));t.SetEnd(vec(-6.85,4.05));t.SetWidth(p.FromMM(.1524));t.SetLayer(p.F_Cu);t.SetNet(net);b.Add(t);new.append(uid(t))
v=p.PCB_VIA(b);v.SetPosition(vec(-6.85,4.05));v.SetWidth(p.FromMM(.5));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetFrontTentingMode(p.TENTING_MODE_TENTED);v.SetBackTentingMode(p.TENTING_MODE_TENTED);v.SetNet(net);b.Add(v);new.append(uid(v))
b.BuildConnectivity();p.SaveBoard(str(dst),b)
(r/'brake/r313_replacements.json').write_text(json.dumps(rem,indent=2)+'\n');(r/'brake/r313_moves.json').write_text(json.dumps({'footprint_moves':[move]},indent=2)+'\n');(dst.parent/'delta.json').write_text(json.dumps({'source':str(src),'candidate':str(dst),'removed_ids':rem,'new_ids':new,'footprint_moves':[move]},indent=2)+'\n')
