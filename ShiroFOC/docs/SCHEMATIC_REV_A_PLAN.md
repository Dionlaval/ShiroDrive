# ShiroFOC Rev A Schematic Plan

**A0 status:** implemented; final release evidence, actual population, reviewed deviations and remaining hardware qualification are in [DESIGN_REVIEW_REV_A.md](DESIGN_REVIEW_REV_A.md). This document records the original workflow; the release review is authoritative for completion status.

## Objective

Create a complete, readable KiCad schematic for a first-build ShiroFOC PCB. The schematic must implement the architecture in `DESIGN_CONSTRAINTS.md` and the assignments in `MCU_PINOUT_AND_INTERFACE_PLAN.md`, pass the reviews below, and contain enough part, rating, and assembly information to begin PCB layout without inventing missing circuits during placement.

This plan targets a working prototype, not a production-certified controller. Tuning components may remain selectable or DNP, but power topology, protection, default states, pin assignments, and component voltage/current ratings must be resolved before layout.

## Hierarchical schematic structure

Use a simple root sheet containing functional blocks and the major inter-sheet buses. Keep every hierarchical label unique and use the same net names throughout the project.

### 00 — System overview

- Root sheet with one block per functional sheet.
- Show the primary flow: `BAT+ -> VM`, `VM -> inverter`, `VM -> 5V_BAT`, `USB -> 5V_USB`, `5V_BAT/5V_USB -> 5V_SYS -> 3V3`, and `VM -> STSPIN VCC buck`.
- Show control paths between the STSPIN, inverter, sensors, CAN, USB-UART, SWD, encoder mux, and brake chopper.
- Put connector names and externally visible signals on this sheet.
- Add project-wide notes for the 6S–10S range, 42 V maximum, 60 V phase MOSFET limit, and common GND/PGND net strategy.

### 01 — Battery input and DC link

- Keyed battery connector and clearly marked polarity.
- VM and power-return distribution.
- Three 680 uF / 63 V bulk capacitors and the selected board-level ceramic bypass capacitors.
- Bleeder resistor with checked voltage and power rating.
- VM test point and power-return test point.
- Optional input TVS/clamp footprint, normally DNP until selected.
- Optional input series-RC damping footprint, initially DNP.
- No reverse-polarity or onboard precharge circuit in Rev A.

### 02 — Auxiliary power and USB power mux

- LMR36510F VM-to-`5V_BAT` buck with datasheet-recommended input/output capacitors, inductor, feedback network, enable state, exposed-pad connection, and useful test points.
- USB-C receptacle providing `5V_USB`, USB 2.0 data, shield, CC1/CC2 sink resistors, and connector-adjacent ESD protection.
- TPS2121 power mux configured for `5V_USB` priority and automatic fallback to `5V_BAT`.
- Explicit current-limit, priority, switchover, soft-start, and overvoltage-divider values.
- `5V_SYS` output capacitance and test point.
- TLV75533P 5 V-to-3.3 V LDO with enable, thermal pad, required capacitors, and `3V3` test point.
- Prevent either source, USB-UART signals, or peripheral signals from back-powering an unpowered rail.

### 03 — STSPIN32G4 core and gate-driver supply

- STSPIN32G4 power pins, grounds, exposed pad, external-3.3 V bypass configuration, VDDA/VREF filtering, VBAT treatment, and all required local decoupling.
- Internal VM-to-VCC buck starting at its 8 V hardware default, with SW catch diode, inductor, local capacitors, and firmware configuration to 10 V after each VM start/return. The STSPIN VCC setting is internal; no external feedback divider is used.
- NRST, BOOT0 behavior, status LED, oscillator/crystal provision, and test points.
- Every unused GPIO explicitly marked no-connect or reserved; never leave ambiguous dangling pins.
- Net labels must match the MCU pinout plan.

### 04 — Three-phase inverter and current sensing

- Three CSD88599Q5DC half-bridge power blocks.
- Phase A/B/C gate connections, bootstrap capacitors/diodes, gate-source pull-downs, and configurable gate resistors.
- Reserve independent turn-on/turn-off resistor and diode options where practical.
- Three low-side shunts with true Kelvin sense connections.
- STSPIN op-amp/current-sense inputs with correct polarity, gain-setting parts, and anti-alias filtering.
- Motor phase connector and high-current net naming.
- One DNP series-RC snubber footprint per phase, placed logically at each switching node.
- Local high-frequency VM-to-PGND ceramic capacitors assigned to each half-bridge.

### 05 — Brake chopper

- External brake-resistor connector carrying raw `VM` and `BRK_SW`.
- TI CSD19531Q5A 100 V low-side N-channel brake MOSFET and UCC27517A dedicated low-side gate driver.
- Gate resistor, gate-source pull-down, driver-input pull-down, and gate-source Zener/TVS protection.
- `BRAKE_PWM` control from PB9 with guaranteed default-off behavior during reset, USB-only power, and loss of MCU control.
- Driver supply decoupling and local power-return routing notes.
- Reserve a hardware bus-overvoltage backup/control footprint if the selected implementation is practical.
- Mark the external resistor value as application-dependent; document the allowable resistance/current range instead of assigning an arbitrary universal value.

### 06 — Position feedback

- Onboard AS5047P with local decoupling, SPI programming/diagnostic connection, chip-select pull-up, and ABI outputs.
- External six-pin encoder/Hall connector: `3V3`, GND, A/U, B/V, I/W, and optional shield/drain assignment if retained.
- Connector-adjacent low-capacitance ESD array and series resistors on the external signal lines.
- Three-channel 2:1 feedback mux selecting onboard ABI or external ABI/Hall signals.
- Safe mux-select default and explicit `FEEDBACK_ENABLE_N` behavior so PB8/BOOT0 cannot be driven during reset.
- Confirm the selected mux accepts 3.3 V logic, passes the required edge rates, and presents high impedance when disabled/unpowered.
- Route selected A/B/I signals to PB6/PB7/PB8 and document both quadrature and Hall firmware modes.

### 07 — IMU and temperature sensing

- BMI323 on SPI3 with its own chip select, INT1, INT2, required supply capacitors, and any mandatory interface-strapping pins.
- Physical orientation axes clearly marked in the schematic notes and later on silkscreen.
- Three identical NTC divider/filter channels, one per half-bridge, routed to their assigned ADC pins.
- Define nominal NTC resistance, beta value, pull-up/down arrangement, ADC range, fail-open behavior, and fail-short behavior.
- Keep optional test points on all three temperature channels.

### 08 — CAN interface

- Selected 3.3 V CAN transceiver and local decoupling.
- FDCAN TX/RX connections to the assigned MCU pins.
- CAN connector with CANH, CANL, and reference ground; use two connectors only if physical daisy chaining is a firm mechanical requirement.
- Connector-side CAN ESD/TVS protection. Rev A fits 0 ohm CANH/CANL links; a true common-mode choke is deferred unless EMC testing justifies it.
- Selectable 120 ohm termination, default DNP, with unmistakable assembly option.
- Check transceiver standby/silent pin defaults and prevent unwanted bus driving during reset or USB-only operation.

### 09 — USB-UART service interface

- CP2102N-A02 USB-to-UART bridge with `VREGIN` and `VDD` powered together from `3V3` in regulator-bypass mode, local bypassing, and raw USB presence sensed on VBUS through its required divider.
- D+/D- from the protected USB-C connector.
- USART1 TX/RX, optional hardware reset/boot control, and series resistor footprints.
- Manual BOOT0 and NRST access must remain available regardless of bridge state.
- Prevent back-powering through TX, RX, NRST, or BOOT0.
- Add UART TX/RX/GND test points.

### 10 — SWD, test points, and assembly options

- Standard 10-pin, 1.27 mm Arm Cortex SWD connector.
- VTREF/3V3, SWDIO, SWCLK, NRST, and GND. SWO is NC because PB3 is SPI3_SCK.
- Clearly grouped test points for VM, VCC, 5V_BAT, 5V_USB, 5V_SYS, 3V3, NRST, BOOT0, CAN, SPI, encoder channels, current-sense outputs, and NTC outputs.
- Central table of DNP/tuning options: gate networks, phase snubbers, input damping, CAN termination, VM clamp, oscillator options, and boot automation.

## Creation sequence

1. Create the hierarchical sheets, global net-name convention, power symbols, and connector reference scheme.
2. Complete battery input, DC-link, auxiliary rails, power mux, and STSPIN VCC generation first.
3. Complete the STSPIN core, pin labels, reset/boot/debug circuits, and decoupling.
4. Add one complete half-bridge and current-sense channel; review it before duplicating it for phases B and C.
5. Add the brake chopper.
6. Add onboard/external position feedback and its safe-start gating.
7. Add IMU, NTC channels, CAN, USB-UART, and SWD.
8. Assign exact manufacturer parts, footprints, ratings, and procurement identifiers.
9. Run ERC and resolve every warning intentionally; use documented exclusions only where electrically justified.
10. Perform the staged design reviews below and freeze schematic revision A0 for PCB layout.

## Review stage 1 — Architecture and requirements

- Every feature in `DESIGN_CONSTRAINTS.md` appears on a sheet or is explicitly deferred.
- Every MCU signal matches `MCU_PINOUT_AND_INTERFACE_PLAN.md` and the STM32 alternate-function mapping.
- No two peripherals unintentionally require the same pin, timer channel, ADC channel, DMA resource, or interrupt function.
- USB-only, battery-only, both-sources-present, and complete-power-off states all have defined behavior.
- USB preference and battery fallback are implemented electrically, not only stated in notes.
- The power stage cannot be enabled without valid VM, control power, and firmware initialization.
- Regen current has an uninterrupted intended path back to VM, while the brake chopper handles a bus that cannot absorb it.

## Review stage 2 — Datasheet compliance

Review each IC against the latest manufacturer datasheet, pin by pin. Record the datasheet revision in a schematic note or review log.

- STSPIN external-3.3 V bypass configuration and prohibited power sequences.
- STSPIN VCC-buck topology, 10 V setting, inductor requirements, REGIN/SW layout needs, and current capability.
- STSPIN bootstrap network, gate-drive limits, SCREF configuration, op-amp constraints, VDDA, VREF+, exposed pad, and NC pins.
- CSD88599Q5DC pinout, orientation, gate-voltage limit, 60 V absolute maximum, thermal pads, and package footprint.
- LMR36510F voltage rating, feedback equation, inductor saturation/RMS current, capacitor derating, enable/PG behavior, forced-PWM operation, and exposed pad.
- TPS2121 source priority, valid-voltage thresholds, current limit, soft start, reverse blocking, and required capacitance.
- TLV75533P capacitor stability, dropout/current/thermal limits, enable default, and thermal pad.
- Brake driver UVLO/output polarity and brake MOSFET VDS, VGS, pulse SOA, avalanche, and thermal limits.
- AS5047P supply mode, interface pulls, ABI electrical outputs, diagnostics, and startup behavior.
- BMI323 SPI mode, VDD/VDDIO limits, decoupling, interface selection, and interrupt pin types.
- CAN transceiver supply, input thresholds, bus-fault rating, standby defaults, and ESD network compatibility.
- USB-UART bridge supply and I/O voltage behavior for every power-order combination.

## Review stage 3 — Fault and startup analysis

For each case, verify component stress, default GPIO state, back-power paths, and resulting firmware-visible condition.

- Battery connected normally; USB absent.
- USB connected; battery absent.
- Battery and USB connected together, including attachment and removal of either source.
- VM applied while the MCU is held in reset or blank from assembly.
- USB applied to a blank MCU.
- Battery hot-plug into the full DC-link capacitor bank.
- Regeneration into a charged battery, disconnected battery, non-sinking PSU, or BMS that opens.
- Brake resistor absent, open circuit, short circuit, or incorrectly valued.
- Motor phase open/short and gate-driver fault.
- External encoder unplugged, miswired, ESD-struck, or powered while the board is off.
- PB8/BOOT0 during reset with the onboard encoder fitted.
- NTC open and short failures.
- CAN and USB cables connected before board power.
- Any one regulated rail absent, delayed, shorted, or out of tolerance.

## Review stage 4 — Analog, timing, and calculations

- Current-shunt resistance, wattage, pulse rating, Kelvin layout, amplifier gain, ADC full-scale range, and overcurrent threshold are calculated together.
- All three current-sense polarities produce the intended positive current sign.
- PWM frequency, dead time, MOSFET gate charge, STSPIN peak gate current, gate resistor range, and estimated switching loss are mutually compatible.
- Bootstrap capacitance supports the selected MOSFET charge and expected maximum high-side on-time.
- VM divider remains safe at the selected transient/clamp voltage and has suitable ADC settling time.
- NTC dividers cover the required temperature range without saturating the ADC.
- Brake threshold sits above 42 V normal maximum but below unsafe stress; ADC tolerances and reaction delay are included.
- Brake MOSFET and resistor pulse energy are checked against at least one defined worst-case mechanical load.
- `5V_BAT`, TPS2121, and 3V3 LDO budgets include simultaneous worst-case loads and startup peaks.
- CAN timing and oscillator tolerance support the intended bus bitrate and network length.

## Review stage 5 — Schematic quality and PCB readiness

- ERC passes with no unexplained errors or warnings.
- Every component has a verified footprint; check custom pin-one, pad-number, courtyard, paste and mask geometry. A0 custom STEP models are unavailable; use manufacturer drawings and sample/printed checks for mechanical orientation before fabrication.
- Schematic symbol pins match footprint pads and manufacturer package drawings.
- All polarized parts and connectors have visible polarity/pin-one markings.
- Every capacitor and resistor exposed to VM has adequate voltage rating and derating.
- Every power component has a realistic package power/thermal path, not merely an attractive datasheet headline rating.
- High-current paths, Kelvin paths, switching nodes, gate loops, and sensitive analog nets are identified with PCB placement/routing notes.
- Required local capacitors are associated with the exact IC or half-bridge they must be placed beside.
- Nets that are electrically common GND/PGND remain one net while layout notes define quiet and high-current return paths.
- Test points are accessible after assembly and do not create dangerous high-voltage confusion.
- BOM includes manufacturer part number, value, tolerance, voltage/current/power rating, package, and assembly status.
- DNP parts and mutually exclusive assembly options are unambiguous.

## Schematic release gate

The Rev A schematic is ready for PCB layout only when:

- Architecture, datasheet, fault/startup, calculation, and PCB-readiness reviews are complete.
- All unresolved issues are either closed or explicitly documented as prototype tuning items with safe initial population states.
- Power-up defaults keep the inverter and software brake command off; the fitted OV backup intentionally overrides the brake command above its threshold when its supplies are present.
- No connector can apply an unsupported voltage directly to the MCU or a 3.3 V peripheral.
- The complete power tree has been checked for reverse current and back-powering in every source combination.
- Current sensing, bus-voltage sensing, temperature sensing, CAN, SWD, USB-UART, IMU, and both feedback choices each have a complete electrical path.
- A final independent pinout/footprint review has been completed before layout begins.

Passing this gate means the schematic is suitable for a serious first PCB revision. It does not remove the need for conservative bring-up, current-limited initial testing, oscilloscope validation of switching nodes and VM, gate-resistor/snubber tuning, and thermal testing before applying the full current rating.
