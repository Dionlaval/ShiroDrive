from pathlib import Path
import pcbnew as p,json
r=Path(__file__).resolve().parent
board_path=r/'ShiroFOC_Manual.kicad_pcb'
project_path=r/'ShiroFOC_Manual.kicad_pro'
settings=p.GetSettingsManager()
assert settings.LoadProject(str(project_path))
project=settings.GetProject(str(project_path))
board=p.LoadBoard(str(board_path))
board.SetProject(project)
board.SynchronizeNetsAndNetClasses(False)
netclasses={str(name):p.ToMM(nc.GetClearance()) for name,nc in board.GetNetClasses().items()}
print('clearance mm',netclasses)
board.BuildConnectivity()
filler=p.ZONE_FILLER(board)
print('filled',filler.Fill(board.Zones()))
p.SaveBoard(str(board_path),board)
(r/'refill_result.json').write_text(json.dumps({'project':str(project_path),'classes_clearance_mm':netclasses,'filled':True},indent=2))
