# P3 placement completion — 4 October 2026

The existing 219-footprint P3 PCB is now placed inside the original 80 × 80 mm outline. No test points, footprints, tracks, vias or copper pours were added. This is a placement completion, not a routing or fabrication release.

## Preserved work

- All 103 footprints already inside the outline are retained byte-for-byte, including their positions, rotations, sides, pads, fields and graphics. This covers the half-bridges, shunts, local passives, MCU/op-amp networks, crystal, placed decoupling, IMU, USB, bulk capacitors, connectors and mounting holes.
- All 286 pre-existing in-board track/via objects are retained byte-for-byte.
- U601 remains locked on B.Cu at the board centre: X 113.660312, Y 103.936331 mm. Its placed C601/C602 remain unchanged and locked.
- Board outline, net assignments, stackup, project rules, schematics and libraries are unchanged.

## Placement completed

116 previously parked footprints were placed by function:

- Brake MOSFET and gate driver below the bulk bank, with the comparator below them. Local comparator routing moved rigidly with its components.
- 10 V buck on the front left, with its input capacitors, bootstrap/VCC capacitors, inductor, output capacitors and feedback divider. Its existing PG via moved with U201 when the footprint changed from back to front.
- 5 V converter, supply mux and 3.3 V regulator on the back left. Their existing local routing moved rigidly with the corresponding subcircuits.
- CAN transceiver, protection and termination above the two bottom-edge CAN connectors.
- External encoder/Hall connector, ESD device, buffer and sensor power switch along the lower-right edge; feedback mux and compact bus-sense divider on the back nearby.
- Remaining ADC/temperature input filters beside the fixed MCU analog area, plus the brake NTC connector at the left edge on the back.
- Reset switch and status indicator above SWD; previously parked gate-driver supply capacitors beside the relevant MCU supply pins.
- DC-link protection and optional damping components on the back near the input/bulk region.

39 existing off-board copper objects moved with their owning parts; their shapes, widths, layers and net assignments were preserved. The sole reflection was the existing through via on U201's PG pin, following U201's B-to-F footprint flip. There was no rerouting.

## Section guides and layer intent

The PCB contains labelled non-copper section boundaries:

| KiCad layer | Contents |
| --- | --- |
| User.1 | Front sections: DC link, input, brake, auxiliary power, MCU/analog, IMU, half-bridges, USB/UART, CAN, external feedback, reset/status and SWD |
| User.2 | Back sections: DC-link protection, supplies, centred encoder, fixed MCU/op-amp network, temperature filters, brake NTC, feedback mux and fixed bridge routing |
| User.Comments | Placement scope and copper-layer intent |
| User.Drawings | 8 mm mounting-hardware envelopes |

Enable User.1 or User.2 in KiCad's Appearance panel to inspect a side's guides. They are visual aids, not copper zones or enforced keepouts. Front and back preview images use the same top-view coordinates.

Copper-layer intent follows the user's instruction: F.Cu for high-power distribution; In1.Cu for internal signals and low-voltage power; In2.Cu reserved for GND; B.Cu for signals and GND. No planes were created or filled during this pass.

## Checks

| Check | Result |
| --- | --- |
| Footprints | 219 retained; 103 fixed and 116 moved |
| Test points | 0 on PCB; none added |
| Existing routing | 252 segments and 73 vias retained |
| Protected footprint/copper native text | Exact byte-for-byte preservation |
| Physical copper connectivity | All 601 connected components identical before/after |
| Present PCB pad-net assignments vs native schematic netlist | 0 mismatches |
| New DRC violations | 0 |
| Existing DRC findings | 144 → 127; 17 resolved |
| Shorts / overlapping courtyards | 0 / 0 in final native DRC |
| Unconnected items | 412 → 412, expected for this unrouted placement stage |
| Newly placed components | Inside the outline; hardware and opposite-side through-pad interference checked |

The 127 remaining findings are inherited: 11 clearances, 34 dangling vias, 20 dangling tracks, 17 library-footprint mismatches, 37 silk overlaps, 5 silk-over-copper findings and 3 silk-edge clearances. Protected work and design rules were not changed to suppress them.

The schematic contains 33 test points and feedback capacitors C414/C424/C434 that were absent from the starting PCB. They remain absent; the user explicitly requested no test-point placement. No schematic-to-PCB import was performed.

## Evidence and recovery

- [Front sections](sections_front.png) and [back sections](sections_back.png)
- [Front geometry](placement_front.png) and [back geometry](placement_back.png)
- [Native final DRC](final_drc.json) and [comparison with baseline](drc_comparison.json)
- [Byte preservation](preservation_check.json) and [native geometry/connectivity validation](geometry_validation.json)
- [Placement manifest](placement_manifest.json)
- [Pre-placement project backup](before_placement.zip) and [exact baseline PCB](baseline.kicad_pcb)

`build_placement.py` generates a review candidate from the checkpoint using KiCad 9's bundled Python. `assemble_final.py` uses Python 3.12 to replace only the explicitly movable objects and add guide drawings, preserving the remaining native source text. `validate_geometry.py` checks the result using native KiCad geometry/connectivity. These scripts do not overwrite the working board. Re-running them rebuilds the review outputs from the checkpoint; it does not incorporate subsequent manual edits.
