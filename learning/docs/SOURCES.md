# Evidence and reading

## Project evidence

| Source | What it establishes |
|---|---|
| [Native schematic](../../ShiroFOC/ShiroFOC_KiCad/ShiroFOC_KiCad.kicad_sch) | Actual component values, fitted/DNP state and connections |
| [P1 exported netlist](../../ShiroFOC/ShiroFOC_KiCad/outputs/revision_P1/netlist.xml) | Pin/net cross-check, including separate shunt-force and Kelvin nodes |
| [Firmware bring-up contract](../../ShiroFOC/docs/FIRMWARE_BRINGUP_CONTRACT.md) | Initial PWM, deadtime and control/protection intentions |
| [Electrical calculations](../../ShiroFOC/ShiroFOC_KiCad/outputs/electrical_calculations.json) | Existing gain, divider, brake and energy arithmetic |
| [Design review](../../ShiroFOC/docs/DESIGN_REVIEW_REV_A.md) | Target envelope and engineering limitations; not measured ratings |
| [P0 placement manifest](../../ShiroFOC/ShiroFOC_KiCad/outputs/placement/placement_manifest.json) | Actual component-centre coordinates and layer sides |
| [P1 revision list](../../ShiroFOC/docs/PCB_REVISION_LIST_P1.md) | Pending mechanical and placement intentions; capacitor architecture discussions evolved after this document |
| [Extracted schematic snapshot](../data/schematic_analysis.json) | Automated extraction, used as supporting data rather than unreviewed electrical verdicts |

The netlist hash used for this package is recorded in [board_inputs.json](../data/board_inputs.json). Read raw native/netlist evidence ahead of heuristic analyzer conclusions. This educational task is not a full hardware design review.

## Primary external references

1. [TI, Bulk Capacitor Sizing for DC Motor Drive Applications, SLVAFT0](https://www.ti.com/lit/pdf/slvaft0). Context for supply inductance, current changes and capacitor sizing. Our single-leg and three-phase equations are explicitly derived for their own assumptions; they are not represented as a literal implementation of the note's sizing heuristic.
2. [TI, Best Practices for Board Layout of Motor Drivers, SLVA959B](https://www.ti.com/lit/an/slva959b/slva959b.pdf). Reference for current paths and physical layout priorities.
3. [Murata, DC-bias capacitance FAQ](https://www.murata.com/en-sg/support/faqs/capacitor/ceramiccapacitor/char/0005). Supports the need to use effective rather than only nominal ceramic capacitance. We did not obtain a measured bias curve for a candidate part; plotted retention curves are illustrative.
4. [ST, STSPIN32G4 product information](https://www.st.com/en/motor-drivers/stspin32g4.html) and [local datasheet](../../ShiroFOC/DataSheets/STSPIN32G4.pdf). Integrated MCU, driver and analog resources. Circuit values still come from our design.
5. [ST, STM32G4 ADC use tips and recommendations, AN5346](https://www.st.com/resource/en/application_note/an5346-stm32g4-adc-use-tips-and-recommendations-stmicroelectronics.pdf). Acquisition-time/source-impedance relationship and ADC usage.
6. [ST, Operational Amplifier usage in STM32G4, AN5306](https://www.st.com/resource/en/application_note/an5306-operational-amplifier-opamp-usage-in-stm32g4-series-stmicroelectronics.pdf). Background for internal op-amp configuration. The lab does not claim a characterised op-amp transfer function.
7. [TI CSD88599Q5DC datasheet](https://www.ti.com/lit/ds/symlink/csd88599q5dc.pdf), also [local](../../ShiroFOC/DataSheets/CSD88599Q5DC.pdf). Device-specific switching/layout reference; do not substitute the lab's illustrative gate parameters for its data.
8. [moteus-n1 r1.3 published schematic](https://github.com/mjbots/moteus/blob/main/hw/n1/r1.3/moteus_n1.sch). C47–C86 list 40 × 4.7 µF, 100 V, Murata GRJ31CC72A475KE01K across V+/V−. Nominal total is 188 µF. This demonstrates an actual ceramic-bank architecture; it does not establish our required count or the part's effective capacitance at 42 V.
9. [moteus electrical setup](https://mjbots.github.io/moteus/guides/electrical-setup/). Documents power-connection and returned-energy considerations around the controller.

External references were consulted for technical grounding. No distributor stock, pricing, part-availability or fabricator-capability validation was performed.
