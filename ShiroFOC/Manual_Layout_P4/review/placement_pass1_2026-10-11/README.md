# P4 — first IC and support placement pass

11 October 2026. This pass is saved in `../../ShiroFOC_Manual.kicad_pcb`, with routing presets in the matching `.kicad_pro`. The original P4 files are backed up in `before/`. P3 and the schematics were not edited.

## Result

All 18 ICs are within the 45 × 45 mm board outline. Forty existing footprints have changed position or orientation, and the schematic's fitted R618 has been added. The MCU and centred, locked encoder retain their original positions. The outline, mounting holes, power wire pads and six-layer stack are preserved.

There are now 212 footprint origins on the board, up from 179. Sixty-six remain staged: 50 fitted/default parts, 15 DNP parts and the SWD programming footprint. Fifty of these staged footprints belong to the DC-link capacitor bank (44 fitted, six DNP); the remaining input capacitors, bleeder and interfaces still need space. This pass therefore completes the IC placement, not the entire component placement.

[Front/back placement preview](preview/final/overview.png) shows actual footprint geometry and references. Both views use top-view coordinates; the back view is not mirrored. Copper fills are omitted for clarity. J1/J101 are intentionally shown as wire pads without the unused connector plastics.

## Placement decisions

- Preserve the repeated three-phase arrangement at the right, MCU below centre, auxiliary supplies above, and interfaces along the left and lower edges.
- Place U701 and its decoupling/I²C support between the MCU and auxiliary section, with access to the MCU's upper pins. Clear the centred encoder by moving the interfering resistors.
- Keep U602/U603 at the lower side, improve U602's position and nearby support, and bring C603/C605 close to their ICs. Add R618, 49.9 kΩ, between U604 ILIM and GND, matching its existing schematic symbol and path.
- Put C3/C7/C11 on the back alongside their phase stages, with VM pads facing the bridge's plated VM connections. Place TH701/TH702/TH703 beside their respective stages. Place C101/C102/C103/C110 as the first local DC-link ceramic bank.
- Bring reset, brake-input and temperature-divider support onto the board near the MCU/quiet analogue area. Leave the reset switch with the remaining interface placement rather than force it into the phase region.
- Rotate C203 to correct the existing bootstrap pad-to-track mismatch. Rotate R503 to shorten the brake-driver output/gate connection and add short local auxiliary/driver connections.

These are placement choices intended to support short loops and accessible routing. Final loop areas and return paths still depend on completing the copper.

## Routing setup and copper changes

Standard selectable trace widths are 0.1524 mm and 0.254 mm (6 and 10 mil). Default/analogue classes use 6 mil; gate and logic-power classes use 10 mil. Standalone through vias use 0.5 mm pads with 0.3 mm drills. Embedded plated thermal pads in the power footprints retain their native geometry.

The existing power-width and USB differential-pair settings are retained; their final sizing needs the power routing and final impedance stack. Existing preliminary traces were not globally resized.

Eighteen obsolete or obstructing copper guide objects were removed, and 32 short local track/via objects were added. Remaining half-bridge traces continue to indicate routing intent. See the individual manifests and `integration_repairs.json` for the exact changes.

## Verification

Native KiCad 9 DRC used the project rules and freshly filled zones. The comparison baseline was also refilled with the project settings.

The structural check passed: all existing electrical pad identities and schematic paths are preserved, R618 matches the schematic, and the MCU/encoder, board outline, four mounting holes and rule-area keepouts are unchanged. Four unused unnumbered mechanical locating pads belonging to J1/J101 were removed for the wire-only arrangement; their electrical pads are unchanged. All 18 IC envelopes fit; U1/U2/U3 have no courtyard polygons, so their native body/pad bounds were checked instead. Details are in `validation/final_structural_validation.json`.

| Native result | Before | After |
| --- | ---: | ---: |
| Errors | 64 | 33 |
| Warnings | 331 | 401 |
| Unconnected items | 456 | 444 |

No new error pairs were introduced, comparing violation type and item UUIDs. The remaining errors are 22 clearances, nine copper-to-edge clearances, and the two intentional connector-plastic courtyard overlaps at J1/J101. The latter are not physical conflicts for the planned soldered wires. New warnings are unfinished silkscreen and dangling ends left by guide removal; they have not been suppressed. See `final/drc.json` and `drc_comparison.json`.

Confidence: geometry, identities, dimensions and DRC results are verified from the native files. Routing quality remains a provisional placement assessment; this is not a completed routing or manufacturing release.

## Next layout pass

1. Finish the remaining DC-link bank/protection and service-interface placement, including reset/SWD and external temperature connections. Resolve the space required by the staged bulk capacitors before locking the power region. Optional DNP snubbers remain staged.
2. Route each phase's switching and gate/source-return loops, then the Kelvin shunt pairs; replace the preliminary copper as needed. Keep temperature and other quiet analogue traces clear of the switching nodes.
3. Finish MCU, sensor, feedback-selection and interface connections, with local decoupling returns and ground stitching.
4. Resolve the remaining real clearance/edge findings, finish silkscreen, refill zones, and run full connectivity/DRC checks again.

The primary board and project files are the working deliverables. Candidate files under `aux/`, `digital/`, `power/`, `control/` and `final/` are review history, not alternative project versions to edit.
