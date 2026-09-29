# P2 starting-layout checks and open items

This is an unrouted placement handoff, not a fabrication release. The native reports are `erc.json` and `drc.json`; the cross-check is `validation.json`.

## Passed

- Native schematic ERC: 0 violations.
- All 260 schematic components have their assigned footprints in the PCB.
- Every represented electrical pad matches the exported schematic net; no unexpected missing components.
- Original P1 board and checked Manual_Rebuild source files remain unchanged (SHA-256 comparison).
- No component courtyard overlaps reported. No board tracks, vias or copper zones have been added. Footprint-integrated holes and keepouts remain.
- The imported DMM0022A copper bars now belong to their existing power-pad nets; their geometry was retained. This change is local to this new project.

## Resolve during layout / before fabrication

| Item | Evidence | Action |
|---|---|---|
| U204 / TLV755 imported land pattern | Four copper clearance errors: 0.10 mm between its GND land and neighbouring lands | Review/replace the land pattern against the actual package drawing. This is below the saved 0.15 mm board minimum; do not simply suppress it. |
| U901 / USB bridge thermal vias | Four hole-web errors: 0.15 mm vs the 0.20 mm local minimum | Adjust the thermal-via pattern or select a suitable verified land pattern before routing this area. |
| U205 symbol pins 19/20 | Two native schematic-parity warnings: no matching pads in the imported footprint | These are the symbol's NC/test pins. Retain the recorded exception only after confirming the exact module package; do not invent copper pads just to clear parity. |
| Imported silkscreen | 19 warnings: four edge clips, seven over exposed copper, eight overlaps | Clean silkscreen after placement is settled. Some imported text such as `Designator9` is library clutter. |
| R7 comparison shunt | Disconnected, DNP and off-board | Remove it before production exports; DNP does not remove Gerber copper or paste. |
| Rough placement | Bootstrap/gate/ADC/decoupling loops are not routed or optimized | Adjust these parts at their actual pins as you route; use the README checklist. |

The 499 unconnected items are expected at this stage. They are not a count of complete nets. Final DRC also requires connected ground planes, intentional current paths and completed routing.

No component-stock or fabricator-capability validation was performed. Prior firmware/protection, cooling/current-rating and LR2512D assembly-profile questions remain in scope for the final design review, not evidence of completed qualification here.

## File notes

The scripts in this folder record the migration, not a production build system. They depend on the original projects and the local `/tmp/cascade_work/edit.py` helper and should not be rerun on a manually edited PCB. Work in the native project files instead. `placement_manifest.json` records the initial placement; C1 and C5 were subsequently moved 0.15 mm left to meet the saved power clearance.

The optional brake NTC addition is documented in [brake_ntc/README.md](brake_ntc/README.md); it adds no new DRC findings. The current reports include this addition.

Latest update: [bootstrap return correction](bootstrap_return/README.md). Current DRC has 34 findings from the latest user placement, with no additions from the return-net correction; the NTC annotation issue is repaired.
