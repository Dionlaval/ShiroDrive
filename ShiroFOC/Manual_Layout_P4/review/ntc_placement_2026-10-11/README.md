# P4 NTC placement and VBUS-sense review

11 October 2026. Targeted follow-up to the first placement pass, based on the user's latest saved KiCad edits. Those edits are backed up in `before/`.

## Saved change

Eight existing resistors moved; no component values, electrical pad identities, schematic paths, tracks, vias or routing rules changed.

| Group | Placement |
| --- | --- |
| Brake NTC R511/R512 | Front, just above the user's J502 connector: centres (-2.3, 15.4) and (-0.1, 15.4) mm. |
| Phase bias R701/R702/R703 | Back, x = -16.4 mm; y = -1.55, -0.50, +0.55 mm. |
| Phase series R711/R712/R713 | Back, x = -14.0 mm; matching three rows. |

The six phase resistors occupy the quiet gap between the USB and CAN sections. C505 and C711/C712/C713 remain at the MCU ADC end, and D505 remains at the MCU side. The phase thermistors retain their positions beside the bridges. This frees the crowded analogue area without putting the resistor networks among the phase switching copper. The longer sensor connections still need routing over a continuous ground reference, clear of switching nodes and gate loops; placement alone does not establish noise performance.

[Updated front/back preview](preview/final/overview.png). Back is shown in top-view coordinates, not mirrored.

## User edits retained

- J502 stays at (-1.555, 19.29) mm on the front.
- R103/R105/R106 stay in the user's new back-side positions.
- The user's removal of the six optional phase-snubber footprints and four off-board copper fragments is preserved.
- **Do not place DNP tuning footprints.** No tuning footprints were restored or brought onto the board. The nine remaining DNP footprints remain staged; none are included in the on-board placement plan.

## VBUS-sense review

**Verified from native geometry and DRC:** no local short, clearance or courtyard errors affect J502 or R103/R105/R106. The divider remains a compact group near U602. C108 remains 1.23 mm pad-centre to pad-centre from the MCU ADC pad and is retained there.

**Placement judgement:** the new location is reasonable. R106 to U602 pin 13 increases from 2.03 to 4.80 mm straight-line distance, but remains a local interconnect and leaves room for the connector. There is no placement reason to undo the user's move.

The divider and mux connections remain unfinished: VM → R103; R103/R105/R106 common node; R106 → U602 pins 13/14; U602 pin 12 → C108/MCU ADC; and the ground returns. Three nearby pre-existing guide fragments are disconnected and do not complete these routes. They have no accidental pad contacts and were preserved for the routing pass. See `vbus/findings.json` for the circuit path and evidence.

## Checks

Native KiCad 9 DRC used freshly filled zones and the project rules for both baseline and final candidate. Errors remain **33**, with **zero newly introduced error pairs**. Warnings decrease from 398 to 395; unconnected items remain 433. Existing errors and silkscreen work remain outside this placement change.

`validation.json` records a structural PASS: exactly the eight intended footprint moves, all 272 footprints and their electrical identities retained, every track/via unchanged, and the user's connector/VBUS positions preserved. The six already deleted tuning footprints remain absent. All moved resistor pads were also checked against same-net vias to avoid unintended via-in-pad overlap. Component placement quality beyond geometric checks is an engineering judgement; this is not a completed-routing assessment.

The working deliverable is `../../ShiroFOC_Manual.kicad_pcb`. Files in `phase/`, `brake/` and `final/` are audit candidates. Schematics and project settings were not edited.
