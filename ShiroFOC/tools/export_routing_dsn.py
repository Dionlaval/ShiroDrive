#!/usr/bin/env python3
"""Export filled power shapes, keeping outer ground pour refillable for routing."""
import pcbnew as p
from pathlib import Path
import sys
source=Path(sys.argv[1]);target=Path(sys.argv[2]);b=p.LoadBoard(str(source))
for z in list(b.Zones()):
 if z.GetIsRuleArea():
  # KiCad DSN exports even permissive rule areas as hard keepouts.
  # Remove only clearance-scoping areas from this temporary export board.
  # Real hardware keepouts remain; the native PCB and its DRC rules are unchanged.
  if not(z.GetDoNotAllowTracks() or z.GetDoNotAllowVias() or z.GetDoNotAllowCopperPour()):b.RemoveNative(z)
  continue
 layer=z.GetLayer()
 if layer in [p.F_Cu,p.B_Cu]:
  if z.GetNetname()=='GND':b.RemoveNative(z)
  else:
   filled=z.GetFilledPolysList(layer)
   replacement=p.SHAPE_POLY_SET(filled)
   replacement.thisown=False
   z.SetOutline(replacement)
assert p.ExportSpecctraDSN(b,str(target))
print(target)
