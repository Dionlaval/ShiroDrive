# MA600A active encoder — 18 October 2026

- U601 is now MA600AGQE-0000-Z (factory-default configuration), replacing AS5047P.
- U601 remains centred at PCB X0/Y0 on B.Cu, 90 degrees. Footprint uses MPS Rev 1.0 page 48: 3x3 mm body, 0.5 mm pitch, 0.70x0.25 mm lands at +/-1.45 mm, floating 1.7x1.7 mm exposed pad. Four paste windows give approximately 73% coverage. Generic matching QFN 3D body is used.
- SPI: PB3 -> SCLK12; PB5 -> COPI4; PB4 <- CIPO7; PA15 -> CS5. Chip-select net renamed ENC_CS_N. Firmware must use MA600A protocol and mode 0 or 3 (not AS5047 mode 1).
- DVDD13 and AVDD14 on 3V3; GND8 and TEST10 grounded. C601 100nF, C602 1uF and R309 10k reused. Unused outputs, NC16 and EP17 unconnected.
- AS5047 circuit retained as U1301 with C1301/C1302/R1301 on sheet 13. Entire sheet and its components are DNP, excluded from BOM/PCB, and use local ALT_ nets. Isolated power flags only document the reference circuit; no connection to active 3V3/GND or SPI.
- MA736 preview U605 removed from schematic, board and local library. Its old footprint is saved here.

## Restoring AS5047

Use sheet 13 as the wiring reference. Replace the active encoder circuit and footprint with AS5047, reconnect the six local reference nets to 3V3, GND, SPI3_SCK_MCU, SPI3_MOSI_MCU, SPI3_MISO and ENC_CS_N, and enable BOM/PCB/fit flags for that circuit. Disable or remove the MA600A circuit. Update firmware to AS5047 mode 1 and its frame/parity protocol. These packages are not pin compatible; updating the PCB and routing is required.

## Layout handoff

Routing and unrelated board objects are untouched. The changed footprint needs local routing adjustments. Keep EP17 and NC16 isolated from copper zones. MPS recommends decoupling capacitors >=5 mm from the sensor centre while maintaining low-impedance paths: existing C601 is about 4.44 mm from centre and C602 about 5.60 mm; reconsider C601 placement during rerouting. Check high-current copper near the sensor for magnetic interference. No board DRC/fabrication approval is implied by schematic ERC.

## Validation

- All 17 active footprint pad nets match the exported schematic netlist.
- AS5047 alternative uses only isolated local nets.
- All unrelated component pin nets and all unrelated PCB objects preserved (apart from the intended CS net rename).
- ERC: same 15 findings before/after; zero added findings. Encoder and alternative sheets have no ERC findings.
- Schematic sheets rendered and inspected.

Source: https://www.monolithicpower.com/en/documentview/productdocument/index/version/2/document_type/Datasheet/lang/en/sku/MA600A/document_id/12989/ (Rev 1.0, 2025-06-05), pages 4–5, 14, 41 and 48. Official PDF copied in this directory.
