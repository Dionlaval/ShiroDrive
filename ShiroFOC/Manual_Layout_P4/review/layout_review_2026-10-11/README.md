# P4 layout assessment — 11 October 2026

**P4 is a complete copy of the current saved P3 project. The layout is still at placement/routing stage and is not ready for fabrication.** The 45 × 45 mm concept has a clear functional arrangement, but significant parts are still staged outside the outline. Complete the physical fit before committing to final copper routing.

The working project is [ShiroFOC_Manual.kicad_pro](../../ShiroFOC_Manual.kicad_pro). Its existing basename is retained, matching the P2/P3 folder convention. All 185 source files were copied, including current edits, local libraries, models, backups and earlier reviews. [Copy manifest](copy_manifest.json) and [preservation check](preservation_check.json) record that P3 and the primary P4 project files remain unchanged. Only review artifacts were added. The STEP file and inherited reports are historical; use the new images below for this assessment.

## Current layout and design language

| Feature | Current saved design |
|---|---|
| Outline | 45 × 45 mm, centred on (0, 0), 3 mm corner radii |
| Mounting | Four M2 mounting footprints at (±19.5, ±19.5), 39 mm pitch |
| Copper stack | Six layers, nominal 1.60 mm; 70 µm outer / 17.5 µm inner copper |
| Components | 277 PCB footprints; 331 unique schematic references including 47 test points |
| Placement | 179 footprint origins inside the outline's bounding square; 98 outside |
| Routing | 528 straight segments, 123 standalone vias; only two copper zones, both GND |
| Planes | In1.Cu / L2 and In4.Cu / L5; L3 signals, L4 nominal power allocation |

The footprint-origin count is a staging measure, not a full body/connector clearance test. Some in-board origins still have courtyards crossing the outline or mounting envelopes.

The style is a compact, functional motor module with a strong repeated phase pattern. U1/U2/U3 form a vertical column on the right, at x = 12.85 mm and y = 1.2 / 8.7 / 16.2 mm. Their shunts R3/R1/R5 align at x = 5.85 mm. Power connectors occupy the right edge; auxiliary conversion and braking occupy the top; low-voltage connectors occupy the left and bottom. U4 sits left of the phase cells, with dense analog/support circuitry on the underside. The locked underside encoder U601 at (0, 0) establishes the shaft axis.

Preserve this repeated phase geometry, functional grouping, perimeter access and central encoder alignment. Continue the consistent component orientation and direct 45-degree routing where practical. The missing capacitor bank should be integrated with the commutation paths of the three phase cells; its apparent geometric fit alone will not establish a good power layout. Reassess the 45 mm envelope if the complete assembly cannot meet these needs.

- [Front placement, including staged parts](placement_front_all.png)
- [Front board detail](placement_front_board.png)
- [Back board detail, with encoder overlaps highlighted](placement_back_board.png)
- [Current top 3D view](visual_top_3d.png) and [bottom 3D view](visual_bottom_3d.png)

The placement drawings use top-view coordinates on both sides. The bottom 3D view is viewed from underneath. 3D views omit staged parts and may omit models; notably, J1's custom MR60 footprint has no model, so that view cannot establish its body or mating clearance.

## Prioritised completion work

| Priority | Finding and evidence | Completion action |
|---|---|---|
| 1 — physical fit | **98 footprint origins remain outside the board.** These include the complete 54-position ceramic bank C101–C103/C110–C160, U701's IMU cluster, J1001 SWD, SW301 reset, TH701–TH703, phase snubbers and several support circuits. Native geometry and current placement images. | Finish placement of every retained part. Preserve the 48 fitted / 6 optional bank distinction. Resolve remaining mechanical/cooling access and capacitor placement before routing the power stage. Do not infer completion from the populated-looking 3D view. |
| 1 — short circuit | **Two BOOT/SW shorts at C203**, on B.Cu near (1.0, −20.54) mm. The BOOT via at (1.635, −20.5375) overlaps C203's SW pad; the SW via at (0.365, −20.5375) overlaps its BOOT pad. Both survive zone refill. Native DRC, high confidence. | Rework this local bootstrap connection so each via reaches the correct capacitor pad with clearance to the other net. Recheck copper, drill and mask clearance together. |
| 1 — physical collision | **U601 overlaps R309, R313 and R314 on the same side.** R313 and R314 also overlap one another. Native courtyard DRC and current back placement view, high confidence. | Keep U601 centred and relocate these resistors around its package/magnet envelope. Resolve Q301/J802/R304 courtyard overlaps too. |
| 1 — omitted fitted part | **R618, 49.9 kΩ, is absent from PCB.** The current schematic marks it FIT and connects U604 ILIM to GND. Native netlist versus PCB comparison, high confidence. | Import/place and route R618. This is distinct from optional DNP parts and intentionally omitted test points. |
| 1 — functional copper | **456 unconnected items after refill.** Includes GND 182, VM 80, 3V3 36, VCC 10 and 5V_SYS 9 reported gaps, plus gate/sense, phase, sensor, brake and debug nets. These are native DRC connection entries, not a routing percentage. | Complete connectivity, prioritising supply/ground, bootstrap and gate returns, Kelvin sense, phase/VM/return copper, then remaining digital interfaces. Resolve 40 dangling-track and 24 dangling-via reports as routing progresses. |
| 1 — ground connection | **U4 exposed pad 65 has no same-net GND via within its pad area.** Nearest standalone GND via is approximately 4.94 mm away. Native geometry. STSPIN32G4 datasheet DS13630 Rev 2 p13 Table 6 identifies EPAD as control-logic ground; p14 Table 7 says MCU grounds, including VSSA, connect through it. | Provide a short local connection from EP65 to the ground planes and an appropriate thermal-via arrangement. Ground integrity is essential here, not just cooling. The datasheet does not establish a minimum via count in the cited sections. |
| 2 — power geometry | Only GND zones exist. VM has four 0.254 mm segments totalling about 3.68 mm; the main phase paths have no completed track/zone distribution. | Build the actual VM, phase, low-side force-return and brake current paths, with broad copper and deliberate layer transitions. Preserve separate Kelvin paths and paired gate returns. Determine bottlenecks and losses from the completed geometry. |
| 2 — clearances | Refilled native DRC reports **28 copper-clearance entries**. Examples: GLS1 to C6 VM pad 0.025 mm; GLS1 to HS_RETURN_U 0.0383 mm; SHUNT_W sense pair 0.0548 mm. | Correct local geometry; do not globally loosen rules to hide these. Some repeated entries report the same via/pad pair on multiple layers. |
| 2 — edges and mounting | **11 copper-to-edge entries**, including L201, R905, R207/R209/R211/R213, U602 and R615. J101/H2 and J1/H3 courtyards intersect. | Move edge-adjacent copper to meet the current 0.5 mm edge constraint and check connector bodies, cable exit, screws, washers and tool access against the actual assembly. Connector overhang may be deliberate; mounting interference still needs resolution. |
| 2 — local supplies/returns | No nearby 3V3-to-GND bypass is present for U602 VDD16 or U603 VCC8; nearest suitable C802 is about 18.56 / 11.24 mm away respectively. D801's nearest standalone GND via is about 5.45 mm away. Geometry-derived, incomplete-layout assessment. | Finish local supply bypassing and short protection-device ground paths. Review return transitions against filled L2/L5 planes. For high-side drive, follow HS_RETURN_U/V/W rather than treating GND as the gate-loop return. |
| 2 — manufacturing rules | Seven 0.250 mm drills violate the project's 0.254 mm minimum. Presets/netclasses include 0.20/0.25 mm drills; **43 hole-to-hole warnings** use a 0.45 mm minimum. | Reconcile presets, actual drills and constraints with the chosen fabrication process. Then correct remaining physical violations. Current nominal stackup is not a fabrication-approved stack. |
| 3 — documentation/finish | No board-level silkscreen text exists; 134 silk-overlap, 66 silk-over-copper and other text/edge warnings remain, including staged components. No fiducials detected. | After placement, add board name/P4 revision, connector functions/polarity, phase labels, relevant orientation marks, debug access and assembly fiducials if needed. Clean silkscreen after final routing. Refresh the old section guides and layer-intent annotations. |

**Recommended work order:** complete physical fit and mechanical checks → reconcile fitted/optional parts → repair shorts and local collisions → finish critical gate/Kelvin/decoupling routing → construct power copper and local ground/thermal connections → finish interfaces → refill and resolve DRC/ERC → silkscreen, fabrication stack and output review.

## Electrical consistency and deliberate exceptions

The native schematic export and current PCB agree on the pin/net assignments, values and footprint names of all present components checked. The schematic analyzer was cross-checked against 933 native pin memberships across 199 nets. This is internal consistency, not a blanket manufacturer-pinout approval.

The 54 missing footprints comprise **R618**, six optional DNP parts (C414/C424/C434 and R608/R609/R610), and **47 test points**. Prior work explicitly omitted test-point placement. Reconcile the intended test access and optional footprints with the schematic; do not automatically add all 47 test points solely to clear parity warnings.

The two other native parity entries concern U205 pins 19/20. **These are intentional no-land NC positions, not missing thermal pads.** MPM3620A datasheet p12 identifies them as NC; its package drawing on p24 excludes electrical or mechanical metal connection in their area. U205 retains a footprint-level B.Cu rule area prohibiting tracks, vias, pads and copper pour. Preserve that exception and keepout.

Native ERC has **1 error and 16 warnings**: duplicate PWR_FLAG outputs #FLG11/#FLG12 on one auxiliary-power net; nine symbol/library mismatch entries; six off-grid entries around TP1015/TP1016; and the 5V_USB/5V_USB_RAW naming warning. Reconcile these while preserving actual connectivity. Library differences include changed U4 pin positions and connector/protection symbol graphics: blindly refreshing from an older library could disturb the current circuit.

Current power architecture is the external U201 VM-to-VCC/10 V stage, U205 downstream 5V_BAT stage, battery/USB selection into 5V_SYS and the 3V3 regulator. The old internal-STSPIN-buck narrative is stale. The firmware requirements also still assign PC15 to the status LED, whereas the current netlist assigns PC15/pad 5 to CAN_TERM_DISABLE; old sensor current-limit and no-fan descriptions no longer match U604/R618 and the current accessory/fan intent. Update the handoff documents before bring-up.

## Check results and interpretation

| Native KiCad 9.0.4 check | Saved board | Isolated assessment after zone refill |
|---|---:|---:|
| Non-connectivity DRC errors | 646 | 64 |
| Other DRC warnings | 307 | 331 |
| Unconnected items | 457 | 456 |
| Schematic parity entries | 56 | Not rerun on diagnostic copy; use saved-board check |

The saved ground fills still extended to ±32 mm despite the ±22.5 mm outline. Refilling the isolated assessment copy reduced total non-connectivity violations from 953 to 395. The primary P4 remains the exact copied baseline. **The 64 remaining errors exclude the 456 unconnected errors.** Error counts are report entries, not independent root causes; several C203 and multi-layer items describe the same physical problem.

Both current ground fills cover approximately 1,630 mm² within the actual board. Their oversized old zone boundary remains ±39.5 mm. The EMC analyzer's roughly 26% fill figure divides by that obsolete boundary; it is not the board's actual ground coverage. Similarly, reported hundreds of GND “islands” include disconnected pads, and do not prove the filled planes are fragmented into that many regions.

Other rejected automated claims: named GND layers classified as adjacent signal layers; Kelvin shunt pairs assigned high-speed digital skew limits; thermal vias counted without requiring the same net; automatic supply-current and thermal scores based on guessed loads. These were not elevated into blockers. Correct pin-net-aware geometry and native DRC take precedence.

Earlier October placement reports describe an 80 mm board and 219/298-footprint checkpoints. The current 45 mm arrangement, 277-footprint count and off-board staging supersede those completion claims. Because the geometry and population have changed, the older DRC totals are not a like-for-like progress metric.

## Verification basis and limits

Ran native DRC on saved and refilled copies, native ERC/netlist export, full schematic/PCB analyzers, cross-domain, EMC and thermal analyzers, plus fresh placement and 3D views. Retained all results here. Manufacturer datasheets were used selectively for the U205 exception and U4 ground requirement; local datasheets exist, but this was not a full all-part electrical requalification. Partial MPN coverage also limits automated datasheet checks.

The thermal analyzer assessed only U201 with a guessed small load; it does not establish bridge, brake or board temperature. The intended phase-current ratings, cooling solution, ceramic-bank effective capacitance/ripple, switching overshoot and regenerative braking remain to be validated with the completed design and hardware. Existing ceramic-revision notes already identify these as prototype targets.

LTspice was found and simulation attempted, but all 35 candidate cases were skipped/failed by the available batch integration. No SPICE result is claimed as a pass. No current Gerber/drill release was present, so fabrication-output analysis was not applicable. Lifecycle/pricing/sourcing were outside this layout assessment and were not run.

Key evidence: [native saved DRC](drc_saved.json), [refilled DRC](drc_refilled.json), [DRC summary](drc_summary.json), [ERC](erc.json), [native schematic comparison](schematic_parity.json), [PCB analysis](pcb_refilled.json), [EMC](emc.json), [thermal](thermal.json), [simulation attempt](spice.json).

**Readiness: further placement and substantial routing are required. Preserve the current functional design language, but settle the complete 45 mm physical fit first.**
