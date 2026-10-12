from pathlib import Path
import json, shutil, pcbnew as p
root=Path(__file__).resolve().parent;src=root/'input_rebased/ShiroFOC_Manual.kicad_pcb';dst=root/'input_opened/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(m.GetProject(str(src.with_suffix('.kicad_pro'))));b.SynchronizeNetsAndNetClasses(False)
tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};v=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
site=v(-8.425,4.465)
tracks['5705f432-6436-4b20-b30d-4c580bfcc5c4'].SetPosition(site)
for u,end in [('d6465c5c-f5d1-487d-8675-14d323484017',(-8.440693,4.449307)),('0f1d8ff7-1307-4a87-80dd-845e57ba97b9',(-8.51,4.55)),('7d1f178a-9d3f-4124-aa8f-9abd091d49f0',(-8.64,4.68))]:tracks[u].SetEnd(v(*end))
for u,start in [('43f9e7bd-03cd-42db-a879-e383870c6965',(-8.440693,4.449307)),('18cf990f-4706-42f8-9440-93d45213bb0b',(-8.51,4.55)),('0a818ab7-68c6-4c5d-9dab-7f999cf2da0a',(-8.64,4.68))]:tracks[u].SetStart(v(*start));tracks[u].SetEnd(site)
b.BuildConnectivity();fill=p.ZONE_FILLER(b);fill.Fill(b.Zones());p.SaveBoard(str(dst),b)
print(dst)
