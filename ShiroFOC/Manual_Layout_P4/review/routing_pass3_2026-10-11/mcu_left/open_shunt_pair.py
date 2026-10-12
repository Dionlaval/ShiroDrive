from pathlib import Path
import json, shutil, pcbnew as p
root=Path(__file__).resolve().parent;src=root/'input_latest_partial/ShiroFOC_Manual.kicad_pcb';dst=root/'input_pair_open/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(m.GetProject(str(src.with_suffix('.kicad_pro'))));b.SynchronizeNetsAndNetClasses(False)
tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};codes={q.GetNetname():q.GetNetCode()for q in b.GetNetInfo().NetsByNetcode().values()};v=lambda xy:p.VECTOR2I(p.FromMM(xy[0]),p.FromMM(xy[1]));added=[]
replacements=[('e9b342cd-6612-4c32-9f67-a79191e29514','SHUNT_W_SENSE_P',[(-2.973616,10.9466),(-2.325,10.9466),(-2.1,11.1716),(-1.25,11.1716),(-1.025,10.9466),(-.703616,10.9466)]),('d6640f10-c6a6-40eb-9e7a-39395bbe8f14','SHUNT_W_SENSE_N',[(-3.13,11.3),(-2.475,11.3),(-2.25,11.525),(-1.1,11.525),(-.875,11.3),(-.85,11.3)])]
for u,net,pts in replacements:
    original=tracks[u];assert original.GetWidth()==p.FromMM(.1524);b.Remove(original)
    for a,c in zip(pts,pts[1:]):
        t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(c));t.SetLayer(6);t.SetWidth(p.FromMM(.1524));t.SetNetCode(codes[net]);b.Add(t);added.append(t)
b.BuildConnectivity();fill=p.ZONE_FILLER(b);fill.Fill(b.Zones());p.SaveBoard(str(dst),b)
(dst.parent/'pair_delta.json').write_text(json.dumps({'candidate':str(dst),'removed_ids':[r[0]for r in replacements],'new_ids':[t.m_Uuid.AsString()for t in added],'footprint_moves':[]},indent=2))
