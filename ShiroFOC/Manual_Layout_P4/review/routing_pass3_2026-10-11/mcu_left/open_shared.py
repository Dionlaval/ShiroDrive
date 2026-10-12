from pathlib import Path
import json, shutil, pcbnew as p
root=Path(__file__).resolve().parent;src=root/'input_fanout/ShiroFOC_Manual.kicad_pcb';dst=root/'shared_open/ShiroFOC_Manual.kicad_pcb';dst.parent.mkdir(exist_ok=True)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(src.with_suffix(ext),dst.with_suffix(ext))
for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/name,dst.parent/name)
if not(dst.parent/'libs').exists():(dst.parent/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
m=p.SETTINGS_MANAGER();m.LoadProject(str(src.with_suffix('.kicad_pro')));b=p.LoadBoard(str(src));b.SetProject(m.GetProject(str(src.with_suffix('.kicad_pro'))));b.SynchronizeNetsAndNetClasses(False)
tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
imu=['2e9cd881-75fe-4d3f-afa9-28277271da01','4b8b9ef5-3913-4790-86df-40588a6d60fb','951b0106-eb22-4192-b47a-d42f11661e04','b5982e32-8440-43e5-ac4c-7656149dfd79','e0b84bb2-e410-4874-97bd-78d57ce9f971','ff7a6237-2c7d-4d65-97e8-ecb08d48df82']
h2=['11f127f5-1f65-4bc9-a942-7c63f2b483ca','182c4982-3bf6-4793-9d68-54ce52194f26','2c24da2d-be42-4da7-ada0-13c8c0fc2e9a','6fc895db-e67a-49ea-995d-ae42046e4a07','a87817ea-68e5-4c4d-bdb8-445c2139987e','d4d12dac-b64d-4198-a933-b623c6946def','e4584974-0384-47af-95ca-76ba8ba36159']
for u in imu+h2:b.Remove(tracks[u])
tiny=[t for t in tracks.values()if t.GetNetname()=='IMU_INT2'and t.GetClass()=='PCB_TRACK'and t.GetLength()<p.FromMM(.00001)]
for t in tiny:b.Remove(t)
b.BuildConnectivity();fill=p.ZONE_FILLER(b);fill.Fill(b.Zones());p.SaveBoard(str(dst),b)
(dst.parent/'removed.json').write_text(json.dumps(imu+h2+[t.m_Uuid.AsString()for t in tiny],indent=2))
