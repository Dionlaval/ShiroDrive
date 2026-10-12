# Candidate routing engine for P4

This helper writes separate candidates. It never accepts or merges them into the working board. Every candidate needs native KiCad DRC and visual review before acceptance.

Run with KiCad's bundled Python:

```sh
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 route_p4.py SOURCE.kicad_pcb BASELINE_DRC.json CANDIDATE.kicad_pcb 'NET NAME' --layers F,B --width .1524 --max-length 45 --max-vias 3
```

The positional net names are optional. If omitted the helper excludes power, ground, gate/bootstraps and USB data and attempts reported-unconnected support/signal nets. Explicit scoped net lists are preferred. `--layers F` or `B` prevents transitions; `F,B,L3` permits routing on the dedicated signal layer. Ground L2/L5 and power L4 never receive routed tracks.

Geometry and rule handling:

- Copies the project's `.kicad_pro`, `.kicad_dru`, library tables, and library links alongside the candidate; loads the same-basename source project before routing.
- Uses native pad/track polygons, board outline, rule areas, and connectivity; preserves placement and all existing copper.
- Default 0.20 mm and Power-class 0.50 mm copper clearance, with only the existing U4 0.15 mm courtyard exception. Power-package exceptions are conservatively not exploited.
- Trace widths are restricted to 0.1524 or 0.254 mm; all added vias are through vias with 0.50 mm pads and 0.30 mm drills.
- Tracks/vias observe 0.50 mm edge clearance plus a raster tolerance. Through vias check foreign copper on all six layers. Solid planes are refilled around new copper.
- Every via is excluded from every same-net pad's copper area, and retains a 0.45 mm web from all existing drill holes including same-net vias and slots.
- Offboard and DNP footprints are excluded. Targets must be actual eligible pad components; loose preliminary copper is never an independent routing destination.
- Routing starts and ends at exact pad centers unless already-connected existing copper provides an endpoint.
- Uses a 0.05 mm search grid by default, with 0.014 mm obstacle safety margin. Native DRC remains authoritative.

The `.routes.json` manifest records every attempted connection, source/target pads, route length and via count, and added item UUIDs. Individual connections can be removed when native DRC rejects them. The board and manifest are checkpointed after each connection. Final zone fill can be disabled with `--no-fill` for intermediate work, but must be performed before final checks.

Smoke verification: a 1.03 mm R103-divider link added two segments, reduced unconnected items from 433 to 432, and retained 33 baseline errors with zero new error pairs. See `smoke/`.
