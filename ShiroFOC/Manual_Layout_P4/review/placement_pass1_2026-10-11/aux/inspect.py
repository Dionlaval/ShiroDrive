import pcbnew as p,json,pathlib,shutil,xml.etree.ElementTree as E
root=pathlib.Path('ShiroFOC/Manual_Layout_P4');out=root/'review/placement_pass1_2026-10-11/aux'
if not (out/'baseline.kicad_pcb').exists():shutil.copy2(root/'ShiroFOC_Manual.kicad_pcb',out/'baseline.kicad_pcb')
b=p.LoadBoard(str(out/'baseline.kicad_pcb'));refs={'U201','U203','U204','U205','U501','U502','Q501','C203','C201','C202','C205','C206','C204','L201','C214','C215','C218','C219','R216','R217','C208','C209','C210','C211','C212','C213','D505','R511','R512','R506','R507','R508','C504','C503','C501','C502','R509','R510'}
for f in b.GetFootprints():
 if f.GetReference() in refs:
  print('\n',f.GetReference(),f.GetValue(),p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y),f.GetOrientationDegrees(),f.GetLayerName())
  print([(a.GetNumber(),round(p.ToMM(a.GetPosition().x),3),round(p.ToMM(a.GetPosition().y),3),a.GetNetname(),(p.ToMM(a.GetSize().x),p.ToMM(a.GetSize().y))) for a in f.Pads()])
for t in b.GetTracks():
 if -22.6<p.ToMM(t.GetStart().y)<-6 and -22.6<p.ToMM(t.GetEnd().y)<-6:
  print('T',t.m_Uuid.AsString(),t.GetClass(),t.GetLayerName(),tuple(round(p.ToMM(v),4) for v in [t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y]),t.GetNetname(),p.ToMM(t.GetWidth()))
