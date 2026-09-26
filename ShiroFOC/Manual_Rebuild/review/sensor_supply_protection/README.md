# External Hall/encoder supply protection

26 September2026. User-authorized implementation of R6; replaces the direct0ohm feed.

## Circuit and behavior

JP601 selects3V3 or5V_SYS. Its common pin feeds **U604 TPS2553DBVR** IN, EN and ILIM. Tying ILIM to IN selects75mA nominal current limiting (50–100mA specified). OUT supplies J601.1 and optional R608–R610 Hall pull-ups. Normal accessory load budget remains25mA. The selected supply is declared powered to ERC only when the appropriate JP601 solder bridge is closed; the power flag is not an electrical bypass of that jumper.

C6064.7µF16VX7R bypasses IN; C607100nF16VX7R bypasses OUT. These use existing standard0603 passive associations; exact purchasing/CAD review can occur in the final pass. Former supply-link reference **R604** is now a10k pull-up from FAULT to3V3. **PC13/pad3** is assigned EXT_SENSOR_FAULT_N; TP1023 is renamed and reused. PC15 remains spare.

The switch is the constant-current version, not the -1 latch-off version. It limits a cable short, thermally protects itself if necessary and automatically recovers after fault removal. Hardware protection is independent of MCU code. Firmware must latch a motor-stop condition when relying on failed external feedback; switch recovery must not restart the motor. FAULT has internal deglitch delay and does not detect every unplugged/invalid sensor. Firmware requirements FW-EXT-02 through04 capture these behaviors.

## Verification

**Native ERC:0 violations.254 components.** Exact net checks cover all six IC pins, selector, connector, three optional pull-ups, decoupling and PC13/TP1023. Only the intended five pre-existing pin-to-net assignments change (R604x2, JP601common, PC13,TP1023); unrelated circuits and the draft PCB are unchanged. Both modified sheets were rendered for visual inspection.

TI DBV pinout:1IN,2GND,3EN,4FAULT,5ILIM,6OUT. [Manufacturer datasheet](https://www.ti.com/lit/ds/symlink/tps2553.pdf), pin tablep5/current-limit tablep20. KiCad symbol added to the local library and embedded cache; **footprint/model association deliberately blank until the final CAD pass**. No custom footprint/model generated.

This is a scoped schematic implementation, not a full board review. No stock/fabricator checks, PCB routing, switching/short-circuit simulation or prototype measurements. The design aims to preserve MCU power under an accessory short; confirm transient droop, thermal behavior and source headroom on hardware at both supply settings. No protection against VM/motor voltage being applied to signal pins is claimed.

Original files:before.zip. Before/after native netlists, ERC and validation JSON are beside this note. The earlier schematic-review R6 deferral is superseded by this implementation.
