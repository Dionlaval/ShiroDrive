# ShiroFOC P1 — parallel phase cells and M3 mounting

2026-09-19. **Component-placement checkpoint; routing is still to be done.**

## Open this revision

- [New P1 project](../ShiroFOC_KiCad_P1/ShiroFOC_KiCad.kicad_pro) · [PCB](../ShiroFOC_KiCad_P1/ShiroFOC_KiCad.kicad_pcb)
- [Original P0 project](../ShiroFOC_KiCad/ShiroFOC_KiCad.kicad_pro), retained unchanged.
- [P0 backup ZIP](../backups/ShiroFOC_P0_before_parallel_bridges_2026-09-19.zip), containing the saved project, schematic, PCB, rules and local libraries before this revision.

The two project directories deliberately retain the same KiCad basename. Work in **ShiroFOC_KiCad_P1** for subsequent layout. The P0 backup contains the original 260-footprint PCB and the already-updated schematic with four hole symbols; that historical PCB predates importing the holes.

## Changes

- Retained **C101–C103, three 680 µF electrolytics**, with all component values and footprint associations unchanged. Shifted their centres to x = 20, 40, 60 mm to clear both upper screws.
- Q401–Q403 form a vertical column at x = 64 mm, y = 28, 42, 56 mm. Their OUT pads face the corresponding U/V/W wire terminals at x = 75 mm and the **same y coordinates**. Both columns have 14 mm pitch.
- All three OUT pad banks are 8.65 mm horizontally from their terminal centres. This is equal *placement geometry*, not a routed length measurement. The intervening snubber footprints still need consideration when drawing the broad output copper.
- Repeated the local gate/bypass placement for each phase. Shunts remain on the back at x = 65.65 mm, y = 22, 36, 50 mm. The DNP snubber resistors occupy the back-side gaps between phase terminals; their capacitors remain by the corresponding phase outputs.
- Added **H1–H4, 3.2 mm non-plated M3 clearance holes**. Centres are (6,6), (74,6), (74,74), (6,74) mm: a 68 × 68 mm mounting pattern. Each has an 8 mm screw-head/washer envelope, clear of front and back component courtyards. These envelopes are drawings and checked placement reservations; they are not automatic copper keepout zones.
- Retained the **80 × 80 mm rounded-square outline, R5 corners**, and 2 / 0.5 / 0.5 / 2 oz stackup. Both inner layers remain reserved for ground.
- Kept AS5047 U601 locked at the back-side board centre (40,40). Removed the obsolete blanket top-side magnet envelope.
- Moved MCU U301 to (48,47), with its local power and analog networks moved as a group and adjusted locally. Its underside remains available for decoupling and current-sense circuitry; its thermal-via area clears bottom components. Bootstrap capacitors sit immediately above the controller.
- Moved the brake block into the space released by the old bridge row: Q501 at (28,29), U501 at (22,29), U502 at (22,36), D504 at (38,30), and J501 at (46,27). J501's wire solder pads are accessible from above; they are now inboard, rather than on the right edge. Plan the brake-wire exit over this region when packaging the board.
- Adjusted nearby passives and test pads where needed. Preserved the corrected U204 land and U901 thermal-hole sizes, and the existing electrical net assignments.

All coordinates are board-local millimetres, viewed from the top, with (0,0) at the upper-left outline corner. The native KiCad coordinate origin is offset by (100,100) mm.

## Validation

| Check | Result |
|---|---|
| Native KiCad schematic/PCB comparison | **0 issues** |
| References, values, footprint associations and DNP states | All **264** footprints match the schematic |
| Electrical pads | **833** physical pads / **761** distinct component-pin pairs match the native XML netlist |
| Native clearance, shorts, courtyard overlap, copper-to-edge and hole spacing | **0 violations** |
| Opposite-side component bodies against through-pad exits | **0 overlaps** in conservative bounding checks |
| 8 mm corner hardware envelopes on both faces | **0 component-courtyard collisions** |
| Original saved project | All recorded source file hashes unchanged; backup archive tested |
| Routing | 0 tracks, 0 copper zones; **499 unconnected DRC items** expected |
| Remaining warnings | The same **9** as P0: 4 connector-silk edge clips, 4 MOSFET silk/mask overlaps, 1 intentional U901 library difference |

Evidence: [native DRC](../ShiroFOC_KiCad_P1/outputs/placement_P1/drc_final.json), [independent validation](../ShiroFOC_KiCad_P1/outputs/placement_P1/validation.json), [positions and local adjustments](../ShiroFOC_KiCad_P1/outputs/placement_P1/placement_manifest.json), [backup hashes](../ShiroFOC_KiCad_P1/outputs/placement_P1/backup_manifest.json).

These checks establish placement and file consistency. Routing must still establish the actual power-loop geometry, gate/return paths, Kelvin sensing, ground continuity, thermal performance and sensor noise. They do not establish fabrication readiness. Part availability and external fabricator validation were skipped as requested. The inherited 3D-model coverage is incomplete, so model views are visual aids rather than complete height/interference certification.

## Next routing work

1. Route the three wide OUT connections and the VM/GND distribution, retaining the short local capacitor loops. Check available copper around the DNP snubbers before freezing their exact positions.
2. Build shunt force-via banks clear of the resistor bodies and live MOSFET thermal vias. Route the two Kelvin sense connections separately from high-current copper to the analog networks.
3. Route each gate together with its appropriate return; refine gate-resistor and bootstrap placement against actual pin escapes.
4. Refine pin-local decoupling and ADC networks, then route the remaining power and interface circuits over continuous inner ground planes. Preserve the mounting reservations and keep large switching currents away from U601.
5. Finish test-point access and legends, resolve the U901 library-copy warning deliberately, and run the complete routed-board review.

## Regeneration

`tools/revise_placement_p1.py` loads the saved P0 PCB and writes only the P1 PCB. It preserves existing footprint UUIDs and nets and imports H1–H4 with their schematic paths. It checks the original PCB hash and refuses to overwrite a PCB containing routing or zones. **Do not rerun after manual placement edits without first making a checkpoint**: it rebuilds P1 placement from P0.

`tools/validate_placement_p1.py` checks P1 against a fresh native XML export and its native DRC report. It also checks the mounting dimensions, equal phase placement geometry, opposite-side body interference and original-file hashes.
