"""Refill a same-basename project/PCB copy using native project rules."""
import sys
from pathlib import Path
import pcbnew as p
path=Path(sys.argv[1]).resolve()
settings=p.GetSettingsManager()
assert settings.LoadProject(str(path.with_suffix('.kicad_pro')))
project=settings.GetProject(str(path.with_suffix('.kicad_pro')))
board=p.LoadBoard(str(path))
board.SetProject(project)
board.SynchronizeNetsAndNetClasses(False)
board.BuildConnectivity()
filler=p.ZONE_FILLER(board)
assert filler.Fill(board.Zones())
p.SaveBoard(str(path),board)
print('Refilled',path)
