# ShiroFOC A1-Drawing redraw review

Date: 2026-09-16. Status: complete for first-prototype PCB layout, subject to the unchanged electrical and hardware limits in [DESIGN_REVIEW_REV_A.md](DESIGN_REVIEW_REV_A.md).

The A0 electrical design has been redrawn as connected functional circuits. Capacitors, dividers, feedback paths, gate loops and interface protection are now wired beside the devices they serve. This closes the presentation issues recorded in [SCHEMATIC_READABILITY_PLAN.md](SCHEMATIC_READABILITY_PLAN.md).

## What changed

- Global labels reduced from 731 to 109 (85% fewer). Named ports identify circuit boundaries; ordinary wires, junction dots and shared power symbols show local connections.
- The ten A2 circuit pages were replaced by nine A3 and two A4 circuit pages, plus an A3 overview. Total sheet area is approximately 48% smaller. Dense controller, gate-drive and current-amplifier functions remain separate to keep each drawing readable.
- Component reference and value text uses 1.27 mm. Smaller pin names, interface labels and short notes retain room around dense pins. No components were removed to obtain a smaller drawing.
- U301 is split into digital, supply, gate-driver and three amplifier units. All six units remain one STSPIN32G4 package. The dual MOSFETs show half-bridge structure and four-terminal shunts show force versus sense connections.
- The USB connector, protection, bulk power and UART bridge share one page. The encoder and IMU share one visibly wired SPI bus with separate chip selects. CAN termination visibly spans CANH/CANL.
- Test points sit at their measured nodes. The standalone test-point inventory page is gone. The original prohibition on a PB8/BOOT0 test stub is preserved.
- DNP parts remain in their actual circuit branches. The custom package footprints and all pin assignments are unchanged.

## Sheet map

| PDF page | Function | Size |
|---|---|---|
| 1 | Navigable system overview and power/signal relationships | A3 |
| 2 | Battery, DC-link capacitor bank and bus divider | A4 |
| 3 | Battery 5 V buck, USB-priority mux and 3.3 V LDO | A3 |
| 4 | Controller, clock, reset, SWD and MCU supplies | A3 |
| 5 | STSPIN gate outputs, VCC converter and SCREF divider | A3 |
| 6 | Three power legs, gate loops, snubbers and Kelvin shunts | A3 |
| 7 | Three current amplifiers and phase NTC dividers | A3 |
| 8 | Brake comparator, diode OR, gate driver and MOSFET | A3 |
| 9 | Shared SPI encoder and IMU | A3 |
| 10 | External feedback protection and source/bus-ADC selection | A3 |
| 11 | CAN transceiver, protection, termination and connectors | A4 |
| 12 | USB-C service and UART bridge | A3 |

The overview's arrows are graphics describing system relationships. Child sheets use named global interface ports and shared power rails. This differs from the initial proposal for wired hierarchical ports; the complete physical connectivity is checked directly from KiCad's exported netlist. Native child sheet boxes remain navigable.

## Verification

- KiCad 9.0.4 ERC: zero violations across all 12 sheets, with no ERC exclusions.
- All 260 physical components and 761 pins match the frozen A0 release, including 42 separate NC pins.
- All 190 physical pin groups match exactly: 148 connected nets plus 42 NC groups. A split, short or swapped connection fails validation, even when its net name changes.
- Values, MPNs, footprints, assembly choices and 18 native DNP states match the original release.
- KiCad's footprint loader resolves all 44 footprint types; 895 pad/aperture records retain the package checks and custom orientation sentinels.
- Every final PDF page was rendered and inspected. The native hierarchy was also opened in KiCad and the CAN circuit inspected. Exact PDF and render hashes are recorded in `outputs/visual_review.json`.

Ninety internal net names acquire a hierarchy prefix or KiCad-generated name. `outputs/net_name_aliases.json` maps those names back to the A0 names used by the layout notes. The exported netlist itself is unmodified. Frozen comparison files are supplied under `review_baselines/A0_before_redraw/`.

## Handoff and remaining work

Open `ShiroFOC_KiCad/ShiroFOC_KiCad.kicad_pro` and begin placement/routing using [PCB_LAYOUT_HANDOFF.md](PCB_LAYOUT_HANDOFF.md). The A1 drawing package includes native schematics and libraries, PDF, BOM, netlist, release checks and rebuild scripts. The original A0 archive remains available separately.

This redraw adds no hardware qualification. PCB outline and mechanics, routing/DRC, copper and thermal sizing, assembly-process review, firmware implementation and physical testing remain the subsequent PCB and prototype work described in the existing handoff.
