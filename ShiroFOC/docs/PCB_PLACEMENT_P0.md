# ShiroFOC P0 — initial PCB component placement

Date: 2026-09-17. **Placement checkpoint, not a routed or fabrication-ready board.**

Open [ShiroFOC_KiCad.kicad_pro](../ShiroFOC_KiCad/ShiroFOC_KiCad.kicad_pro) and its PCB in KiCad 9. The existing schematic is retained. This checkpoint is separate from the earlier A1 schematic release ZIP and its hashes.

## Result

- 80 × 80 mm rounded square, 5 mm corner radii; board edges run from (100,100) to (180,180) mm.
- 260 footprints: 122 front, 138 back, including 18 DNP footprints. Named KiCad groups separate functional blocks.
- Four copper layers: F.Cu 70 µm, In1.Cu 17.5 µm, In2.Cu 17.5 µm, B.Cu 70 µm — nominally 2 / 0.5 / 0.5 / 2 oz.
- Inner layers reserved for GND. No zones, tracks or routed vias have been created. Through holes built into footprint thermal lands are already present.
- Provisional 1.60 mm copper-plus-dielectric thickness, excluding mask. Dielectric dimensions and USB impedance geometry are provisional.

## Placement map

Positions below are relative to the upper-left board corner, viewed from the top.

| Block | Placement and intent |
|---|---|
| Magnetic encoder U601 | Back, centre (40,40), locked. A diameter-15 mm provisional magnet envelope is drawn on User.Drawings. The sensor's own passives are adjacent. |
| MCU/gate driver U301 | Front at (54,45), rotated 90°. Offset from the encoder; local decoupling and analog components occupy the underside around its exposed-pad area. |
| Three bridge packages | Front, Q401/Q402/Q403 at x = 24/38/52, y = 29. Gate resistors and package bypasses are grouped with each bridge. |
| Four-terminal shunts | Back at x = 24/38/52, y = 23. Their bodies clear all exposed VM thermal-via exits from the bridge packages. Force and Kelvin pads retain distinct nets. |
| DC link | Three bulk capacitors across the upper edge. DC input faces the left edge; motor solder terminals run down the right edge. |
| Auxiliary power | 5 V buck, power mux and 3.3 V LDO on the left. Buck input HF, bootstrap and VCC capacitors are underneath near their corresponding pins. |
| STSPIN VCC converter | Below and left of U301. Inductor rotated so its switch-side terminal faces the driver. |
| Crystal | Directly below U301, with both load capacitors on the front nearby. |
| Brake chopper | Right/lower-right; driver, MOSFET, diode and external resistor terminals grouped together. Comparator and resistor network nearby. |
| IMU | Lower middle, separated from bridge power copper. |
| USB service | Left edge, USB-UART bridge and protection nearby. |
| CAN / feedback / SWD | Along the lower edge, with interface components behind their connectors. |
| Test pads | Back, grouped near the relevant circuits. Their final access and labels need refinement during routing. |

This is a compact starting arrangement, not proof that 80 mm is the smallest routable or thermally adequate board. Routing may justify local moves or a larger outline within the 150 mm limit.

## Checks performed

| Check | Result / evidence |
|---|---|
| Native KiCad schematic parity | 0 issues |
| Footprint references, associations, values and DNP states | All 260 match the native schematic export |
| Pad-to-net comparison | 761 distinct component-pin pairs match; 833 physical electrical pads checked including duplicate thermal pads |
| Native copper clearance, shorts, courtyard overlap, copper-to-edge and hole spacing | 0 violations in these categories |
| Bottom bodies against top through-pad exits | 0 bounding-box overlaps between bottom courtyards and top PTH/NPTH copper extents |
| Native board inspection | Opened in KiCad; front and underside inspected in 3D, plus native top/bottom SVG plots |
| Routing completeness | 499 unconnected DRC items, expected at this placement-only stage |
| Other DRC findings | 9 warnings retained, described below |

Evidence: [validation.json](../ShiroFOC_KiCad/outputs/placement/validation.json), [native DRC](../ShiroFOC_KiCad/outputs/placement/drc_final.json), [opposite-side check](../ShiroFOC_KiCad/outputs/placement/opposite_side_through_pad_check.json), [placement table](../ShiroFOC_KiCad/outputs/placement/placement.csv).

Confidence is high for file consistency and measured placement clearances. This pass does not establish switching performance, current capacity, temperature rise, magnetic accuracy or enclosure fit. The 3D viewer has incomplete model coverage, including some custom packages; it cannot certify all component heights or body geometry. Full routed-board EMC, thermal and fabrication reviews were not performed at this stage. Fabricator and part-availability validation were skipped as requested.

## Footprint corrections and DRC rule interpretation

### U204 thermal land

The previous custom DYD footprint used a 1.3 mm wide thermal rectangle centred at +0.0625 mm, leaving only 0.0375 mm to pins 4/5. TI drawing 4228946/A distinguishes covered thermal copper from the exposed 0.975 × 1.7 mm soldering area.

The project footprint and its source generator now use a 0.975 × 1.7 mm thermal copper land at +0.0625 mm, with the existing pad-2 ground connection, paste aperture and 0.20 mm ground via. This is an NSMD adaptation retaining the drawing's exposed solderable area, rather than a copy of its wider covered copper extension. The right-side copper gap is now 0.20 mm. Ground spreading and LDO temperature still require attention during routing.

Source: [local TLV755P datasheet](../DataSheets/TLV755P.pdf), PDF page 38, drawing 4228946/A; [TI datasheet](https://www.ti.com/lit/ds/symlink/tlv755p.pdf).

### U901 thermal vias

The standard footprint's 0.30 mm holes at 0.45 mm pitch left only 0.15 mm between holes. The PCB copy uses 0.25 mm drills, giving the required 0.20 mm web. Copper lands and electrical pad numbers are unchanged. A narrowly scoped rule applies the via-spacing requirement to U901 pad-21 thermal vias, which KiCad represents as through-hole pads.

**One library-mismatch warning is intentional:** the PCB copy of U901 has this drill modification. Updating U901 from its standard library will overwrite it. Preserve the change or promote it into a named local footprint and update the schematic association before fabrication release; do not dismiss the warning without checking the holes.

### Clearance rules

The 0.50 mm Power-class clearance is the target for open-board routing. Explicit rules permit 0.15 mm clearance within Q401–403, U301, U201 and C415/C425/C435; local bridge-to-bypass pairs use 0.20 mm. These retain the documented manufacturing floor and avoid treating fine-pitch packages as if their leads had 0.50 mm spacing. No DRC violation exclusions were added. Ordinary routing retains the full net-class clearance.

### Remaining silkscreen warnings

- Four connector-outline segments extend across the board edge at J101/J201; trim the plotted silk during final legend cleanup.
- Four MOSFET package markings approach exposed copper: Q401/Q402/Q403/Q501. Move those markings before fabrication.
- Small part references currently reside on F.Fab/B.Fab. Fabrication-layer labels and test-pad text still need a final readability pass; they are not finished production silkscreen.

## Decisions to finish before routing is frozen

1. Fix the actual motor-axis/magnet diameter, air gap and nearby metal constraints. The drawn 15 mm envelope is provisional, not an approved magnetic keepout.
2. Set mounting holes, screw-head envelopes, heatsink/contact surfaces and connector cable access. Three provisional hardware circles are drawings only; no mounting holes were invented.
3. Route the power loops and shunt force paths first, with deliberate via banks clear of the shunt bodies. Route Kelvin pairs independently to the op-amp networks. Check the longer gate/return path to the left bridge before locking U301.
4. Refine pin-local placement during routing: VDDA/VREF capacitors, SPI source resistors, the feedback mux/PB8 path, crystal and buck loops. Geometric fit alone does not establish adequate loop inductance or analog noise performance.
5. Establish continuous L2/L3 GND pours, return vias, thermal spreading and switch-node keepouts. Avoid VM or phase-current paths through the central sensor region.
6. Route interfaces and service signals, set USB dimensions from the actual dielectric geometry, then finish test access and legends.
7. Resolve every remaining DRC item, including all unrouted connections and the U901 library difference, before calling the PCB ready for manufacture.

## Files and regeneration

- [PCB](../ShiroFOC_KiCad/ShiroFOC_KiCad.kicad_pcb)
- [Top placement SVG](../ShiroFOC_KiCad/outputs/placement/top.svg) · [Bottom placement SVG, mirrored](../ShiroFOC_KiCad/outputs/placement/bottom.svg)
- [Top PNG](../ShiroFOC_KiCad/outputs/placement/top.png) · [Bottom PNG](../ShiroFOC_KiCad/outputs/placement/bottom.png)
- `tools/place_rev_a.py`: initial placement generator using KiCad's native footprint loader.
- `tools/setup_placement_rules.py`: project DRC/net classes and initial stackup.
- `tools/validate_placement.py`: independent native-netlist comparison.

Do not rerun the placement generator after manually moving or routing the board: it replaces the PCB. The CSV is a placement review table, not a manufacturing pick-and-place export. Earlier schematic release archives are unchanged and do not include this PCB checkpoint.
