# P3 — centred encoder and MCU shift for review

P3 was rebuilt from the saved P2 on 27 September 2026. The previous P3 placement trial was deleted. P2 is unchanged.

## Scope completed

- Retained the corrected 80 × 80 mm rounded outline, parallel to the MCU, from the latest P2.
- Placed U601 on B.Cu at the board centre: **X 113.660312, Y 103.936331 mm**.
- Translated U4 and 35 supporting footprints **7 mm down**, with no rotation or change to their relative positions. This includes the placed op-amp networks, ADC filter capacitors, bootstrap/VCC components, crystal and its load capacitors, and placed MCU decoupling.
- Kept the half-bridges, shunts, bulk capacitors, phase terminals and the other 222 footprints unchanged.
- Adjusted the connected gate and Kelvin routes. Local op-amp wiring moved with the components; the shunt pickup vias stayed fixed. No vias were added.
- Added a few User.Comments labels and an encoder centre marker. General placement of the other sections has **not** resumed.

## Routing details to review

- U/V Kelvin pairs retain their parallel geometry on In1.Cu, with longer straight sections.
- The W Kelvin pair turns around the lower shunt to approach its existing pickup vias without crossing the two sense traces. This makes its path longer; inspect this area before committing the power copper.
- The B.Cu GHS1/GHS2 and corresponding HS_RETURN_U/V traces now use **0.20 mm width** to retain the existing 0.20 mm clearance through the shifted corridor. The other track widths were retained. These are gate-drive paths, not phase-current paths.
- Encoder SPI wiring and its currently unplaced support parts await the next placement stage.

## Checks

- All 259 footprints retained; exactly 36 footprints translated, U601 centred, and the other 222 unchanged.
- Schematic, library assignments, project design rules and electrical net assignments unchanged.
- Native KiCad DRC: **zero new violations compared with P2**. The same 81 existing findings remain, mainly silk/library issues, plus existing clearance/drill/edge findings and dangling vias.
- The unfinished board still has 450 unconnected items, unchanged from P2. This is a scoped placement/routing adjustment, not a fabrication release.
- 283 → 301 track segments; 64 → 64 vias. Extra segments form the adjusted bends.

Review the MCU/encoder positions and revised routes before authorizing any further component placement. Review view preferences hide the ratsnest and enable User.Comments; use the Appearance panel to toggle them.
