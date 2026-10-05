# ShiroFOC Rev A Design Constraints

Status: A0 architecture baseline, reconciled with the layout release. Current and power ratings remain prototype goals until verified by thermal and fault testing. [DESIGN_REVIEW_REV_A.md](DESIGN_REVIEW_REV_A.md) records final values, calculation results, deviations and operating limits.

The proposed GPIO allocation and interface details are maintained separately in [MCU_PINOUT_AND_INTERFACE_PLAN.md](MCU_PINOUT_AND_INTERFACE_PLAN.md).

## Product intent

ShiroFOC is a compact, single-axis FOC motor-drive module for consumer and research robotics, including small robotic arms, quadrupeds, balancing platforms, mobile robots, and compact servo actuators.

Each module closes its own current, velocity, and position loops. A motherboard coordinates multiple modules over CAN.

## Fixed architecture

- One STSPIN32G4 only; use its embedded STM32G431 MCU, three gate drivers, op-amps, comparators, and internal VM-to-VCC buck regulator. Bypass its internal 3.3 V regulator and supply the MCU/logic from the external 3.3 V rail.
- One external N-channel MOSFET three-phase bridge (six MOSFET positions minimum).
- Three low-side shunts with Kelvin sensing for phase-current reconstruction and true three-shunt FOC.
- Hardware overcurrent shutdown independent of firmware, using the integrated comparator/break path.
- CAN bus is the primary command, configuration, telemetry, and update transport.
- Integrated 6-axis BMI323 IMU over 4-wire SPI.
- Integrated on-axis magnetic encoder over SPI, subject to mechanical alignment with the shaft magnet.
- External feedback connector supporting Hall U/V/W and at least one configurable encoder interface.
- Three power-stage NTCs, one per half-bridge.
- DC-bus voltage monitoring.
- Temperature telemetry and overtemperature warnings over CAN for system-level cooling control.
- USB-C service interface through a USB-to-UART bridge.
- Mandatory SWD programming/debug connector.
- No second application MCU.

## Electrical rating target

### Battery and DC bus

- Battery range: 6S to 10S LiPo/Li-ion.
- Recommended design point: 8S, 29.6 V nominal and 33.6 V fully charged.
- Maximum supported pack: 10S, 37.0 V nominal and 42.0 V fully charged.
- Normal DC-bus operating target: approximately 18 V to 42.0 V.
- Rev A power stage: three TI CSD88599Q5DC 60 V DualCool half-bridge power blocks, one package per phase. Parallel packages are deferred to a possible Pro version.
- The design must control regenerative rise and switching overshoot with meaningful margin below the MOSFETs' 60 V absolute maximum; 10S support depends on measured switching behavior and a validated clamp/brake strategy.
- DC-link capacitors: 63 V minimum. Their ripple-current, temperature, lifetime, and transient margin must be validated; a 63 V capacitor rating does not justify allowing the bus to approach 60 V.
- Include local ceramic DC-link capacitance immediately adjacent to each half-bridge and bulk capacitance at the power entry.
- Rev A omits onboard reverse-polarity protection. Use a keyed/polarized battery connection and clearly mark polarity; reverse battery connection is an unsupported fault condition.
- Include bus-voltage measurement and reserve an optional input TVS/clamp footprint. Any populated clamp must be coordinated with the brake-chopper threshold and the 42 V maximum charged pack voltage.
- Keep the VM path bidirectional so intentional regenerative current can return to a battery.
- Provide a local brake-chopper switch and external brake-resistor connector on every ShiroFOC so one module can operate safely without a motherboard. In a multi-axis system a central chopper may be the primary dump, while local choppers use a slightly higher threshold as independent backup protection.
- A battery may absorb regeneration only if its BMS, charge state, temperature, and wiring permit it. A bench or industrial PSU must be assumed unable to sink energy unless explicitly specified otherwise.

### Auxiliary power architecture

- Generate `5V_BAT` directly from VM with an external wide-input switching regulator rated for the complete 10S bus and its permitted transients. Current Rev A choice: LMR36510F, 5 V / 1 A, forced-PWM variant.
- Accept USB-C VBUS as `5V_USB`. Battery and USB-C may be connected simultaneously.
- Feed `5V_BAT` and `5V_USB` into a reverse-current-blocking power mux. USB-C is the preferred source whenever valid; otherwise select `5V_BAT`. The sources must never be tied directly together.
- Name the mux output `5V_SYS`. It powers the external 3.3 V LDO. CP2102N `VREGIN` and `VDD` both use `3V3` in regulator-bypass mode. The bridge's USB-presence `VBUS` pin senses raw USB VBUS through the manufacturer-recommended divider.
- Generate `3V3` from `5V_SYS` with the external TLV75533P LDO. This rail powers the embedded MCU, IMU, selected encoder/Hall interface, feedback mux, CAN transceiver, and other low-voltage logic.
- Configure the STSPIN32G4 for externally supplied 3.3 V according to its regulator-bypass requirements; do not connect two active 3.3 V regulator outputs together.
- Independently use the STSPIN32G4 internal buck from VM to generate gate-driver `VCC`. The supported setting is 8 V to 15 V; use 10 V as the Rev A starting point and validate gate loss, MOSFET enhancement, bootstrap behavior, and STSPIN temperature before changing it.
- USB-only operation powers control, communications, and sensors but not VM, VCC, the inverter, or the brake-chopper gate driver. Firmware must detect that VM is absent and inhibit all power-stage commands.
- Budget `5V_SYS` and `3V3` for worst-case simultaneous loads, including dominant CAN transmission, the onboard AS5047P, and the maximum permitted external feedback load. The feedback mux does not switch sensor power.
- If VM returns while USB has kept `5V_SYS` and the MCU alive, firmware must perform a full power-stage reinitialization before enabling inverter or brake PWM.

### Local brake chopper

- Implement the Rev A brake chopper as a low-side N-channel MOSFET switch: raw `VM` to the external brake resistor, resistor return to `BRK_SW`, brake MOSFET drain to `BRK_SW`, and brake MOSFET source to PGND.
- Provide a clearly keyed two-pin external resistor connector carrying raw `VM` and `BRK_SW`. Both pins can be hazardous at the full DC-bus voltage; do not use a connector that can be confused with a low-voltage sensor interface.
- Drive the brake MOSFET through a dedicated low-side gate-driver IC powered from 10 V VCC. Do not drive the power MOSFET gate directly from a 3.3 V MCU pin.
- Use PB9 `BRAKE_PWM` / TIM17_CH1 as the control output. Add a physical pull-down at the gate-driver input and a gate-source pull-down so the software command defaults off. The fitted hardware OV comparator can command braking during reset when VM exceeds its threshold and both 3V3/VCC are present. USB-only or an unpowered gate driver cannot switch the chopper.
- Select the brake MOSFET with more voltage margin than the 60 V phase power blocks; start the search at 80 V. Validate repetitive pulse SOA, avalanche behavior, switching loss, package thermal impedance, and resistor-current fault behavior rather than selecting only from low RDS(on).
- Size the external resistor from both instantaneous power and braking energy. At a given bus voltage, chopper current is approximately `VBUS / RBRK` and instantaneous resistor power is approximately `VBUS^2 / RBRK`. Motor/load energy that must be removed is approximately `0.5 * J * (omega_start^2 - omega_end^2)`.
- Firmware must use bus-voltage hysteresis and PWM duty control rather than uncontrolled rapid on/off chatter. Thresholds must remain configurable for the installed battery/PSU and resistor.
- Set the normal local-chopper threshold above the maximum expected charged-battery voltage but comfortably below the voltage allowed by the MOSFETs, capacitors, regulator inputs, and ADC protection. A 10S system cannot wait until close to 60 V before beginning to dump energy.
- Reserve a footprint or control path for a hardware overvoltage backup that can command the brake driver independently of normal firmware. This is backup protection, not a substitute for correct firmware, a TVS, or adequate DC-link capacitance.
- A TVS handles short spikes; the brake resistor handles sustained regenerative energy. Do not size either component as though it performs both jobs.

### Power entry, long cables, and inrush

- Expect the DC cable inductance and local low-ESR input capacitance to form an LC resonant circuit. Hot-plugging, abrupt current changes, a released short, or regenerative current can excite it and produce a local VM peak much higher than the battery/PSU voltage.
- Rev A does not include an onboard active precharge/inrush MOSFET. Characterize connector arcing and capacitor-charging current with the final populated DC-link bank (P3: 48 × 10 uF / 100 V ceramics; substantial DC-bias derating); add a system-level anti-spark/precharge solution where the application requires frequent hot-plugging.
- Provide footprints near the power connector for an input damping branch consisting of a series R-C network across VM and PGND. Final values depend on cable inductance, installed bus capacitance, and measured hot-plug response; do not populate arbitrary values before characterization.
- Include some intentional damping through a suitable bulk capacitor/ESR strategy. Do not add a series input inductor or ferrite merely to reduce noise: without damping it can worsen the resonance.
- A TVS is a short-transient clamp, not an inrush limiter or regenerative-energy dump. Select its working and clamping voltages against the 42 V maximum pack, 60 V MOSFET limit, pulse current, and temperature.
- Validate the driver at the maximum intended cable length and wire gauge, including hot-plug, motor braking, supply disconnection, and BMS opening events.

### DC-bus monitoring

- Measure motor VBUS with a dedicated STM32 ADC input.
- Size the resistor divider so the ADC remains below its absolute maximum at the highest possible clamped fault voltage, not merely at the 42.0 V maximum charged-pack voltage.
- Use sufficiently voltage-rated series resistors in the upper divider leg; split the resistance across multiple packages when required for voltage rating, creepage, and fault tolerance.
- Add a local RC anti-alias/noise filter at the ADC input.
- Add an ADC-input protection/clamp strategy that cannot back-power `3V3` during an unpowered or fault condition.
- Use tolerance appropriate to bus protection and calibrate divider gain in production firmware if accurate power telemetry is required.
- Firmware must implement configurable undervoltage, overvoltage, and regenerative-overvoltage thresholds.
- Hardware transient protection must remain effective without firmware; ADC monitoring is not a substitute for the bus clamp or correctly rated components.

### Current and power goals

- Passive/free-air continuous phase current goal: 25 Arms.
- Continuous phase current goal with a defined heatsink or forced airflow: 40 Arms.
- Short peak phase current goal: 80 A peak for no more than 2 seconds, subject to junction-temperature and shunt limits.
- Initial hardware overcurrent trip target: below 90 A peak, finalized from MOSFET SOA, shunt range, amplifier saturation, and comparator tolerance.
- Current ratings refer to motor phase current, not battery current.
- Honest initial product class: approximately 1 kW continuous without aggressive cooling, approximately 1.5–2 kW with a validated thermal solution, and higher short-duration peak power. Exact mechanical output depends on motor speed, winding, modulation, and efficiency.
- Do not publish a continuous power rating until tested at maximum ambient temperature in the intended enclosure.

The STSPIN32G4 architecture is not intrinsically limited to 40 A because it drives external MOSFETs. ST demonstrates the same architecture at up to 3 kW and 63 Arms with additional cooling. The limiting factors are the MOSFETs, switching losses, copper, connectors, shunts, capacitors, thermal path, and transient protection.

## Power-stage constraints

- Select MOSFETs using total loss, not RDS(on) alone: conduction loss, gate charge, switching loss, reverse recovery, output capacitance, and thermal resistance all matter.
- Size the STSPIN gate-drive voltage and gate resistors from the selected MOSFET, target PWM frequency, EMI, and switching-loss measurements.
- Default PWM-frequency design point: 20 kHz. Keep 30 kHz feasible if losses and thermals permit.
- A0 fits one series resistor per gate and reserves phase RC snubbers. Diode-assisted independent turn-on/turn-off paths are deferred; tune the fitted resistors from measurements.
- Provide gate-source pull-down resistors and tight gate-drive loops.
- Place ceramic bus capacitors directly across the high-current bridge supply loop.
- Keep switch nodes compact and away from current-sense, encoder, IMU, CAN, and SWD circuitry.
- Reserve a series R-C snubber footprint from each phase switch node to the appropriate local power return, placed immediately beside its CSD88599Q5DC. Start DNP and tune from measured ringing; do not copy values from another PCB.
- Gate-resistor tuning and phase-node R-C snubbing are complementary: slower gate edges reduce excitation, while a correctly tuned snubber dissipates energy in the parasitic LC resonance. Both trade reduced ringing/EMI against additional switching loss.
- Provide real heatsink attachment or a defined chassis conduction path; copper area alone is not assumed sufficient at 40 Arms.

## Current sensing

- Use three four-terminal/Kelvin shunts where sourcing permits.
- Preliminary shunt range: 0.5 to 1.0 milliohm. Final value follows ADC range, op-amp gain, minimum measurable current, power dissipation, and overcurrent threshold analysis.
- Route each differential sense pair directly from the shunt sense terminals to the assigned integrated op-amp inputs.
- Never share sense traces with force-current copper or general ground-return paths.
- Match input filtering and gain networks across all three channels.
- Sample synchronously with center-aligned PWM.
- Use the integrated comparator and timer break input for cycle-independent hardware shutdown.

## Thermal monitoring and cooling

### Power-stage temperature sensing

- Fit three NTC thermistors, one per half-bridge. One sensor for the entire bridge is not sufficient for the 40 Arms design target because phase loading, airflow, solder quality, gate faults, and heatsink contact can produce asymmetric temperatures.
- Place each NTC as close as practical to the thermally representative MOSFET copper for its phase, preferably between or immediately beside the high-side and low-side devices without enlarging the switching loop.
- Do not place an NTC directly on a switch-node copper island if its divider would create an unsafe high-dV/dt coupling path. Maintain electrical isolation while maximizing thermal coupling.
- Connect each NTC divider to a separate ADC channel where pin allocation permits.
- Use identical NTCs and divider networks across all phases.
- Preliminary choice: 10 kohm NTC at 25 degrees C, 1% B-value tolerance where available, with the fixed divider resistor selected to maximize useful resolution in the expected 40 to 120 degrees C range.
- Firmware must use the hottest of the three readings for CAN thermal telemetry, current derating, and shutdown.
- Preliminary policy targets: issue an early thermal warning near 50 degrees C, begin current derating near 90 degrees C, and shut down near 110 degrees C. Final thresholds must be derived from the selected MOSFET, PCB-to-sensor thermal lag, capacitor ratings, connector ratings, and heatsink tests.
- Detect open-circuit and short-circuit NTC faults and fail to a conservative current limit.

### MCU and STSPIN temperature

- Do not add a separate external NTC for the MCU in Rev A.
- Use the STM32 internal temperature sensor for telemetry and software derating, and rely on the STSPIN32G4's internal thermal shutdown as the final device-level protection.
- Keep the option to add a board-temperature test footprint near the STSPIN32G4 if prototype measurements show that its local temperature is not represented adequately by the internal sensor.

### System-level cooling

- Rev A does not generate fan power and does not include a fan connector, fan PWM output, or tachometer input.
- Size and rate the motor-driver module for a defined passive heatsink or chassis-conduction path without relying on a fan.
- Broadcast all three power-stage temperatures, the hottest temperature, thermal-warning state, and derating state over CAN.
- A motherboard may control enclosure or system fans from this telemetry, but local current derating and shutdown must remain autonomous and must not depend on CAN or a motherboard response.

## Communications

### CAN

- CAN is mandatory and is the normal external interface.
- Use the STM32G431 FDCAN peripheral with a 3.3 V CAN transceiver rated for the selected bus speed.
- Initial interoperability target: Classical CAN at 1 Mbit/s. Preserve CAN-FD capability in the hardware.
- Connector signals: CANH, CANL, signal ground, and shield/chassis provision where applicable.
- Fit ESD protection close to the connector.
- Rev A uses fitted 0 ohm CANH/CANL links. A true common-mode choke is deferred unless EMC testing shows it is required.
- Provide selectable 120 ohm termination; default DNP because only the two physical bus ends are terminated.
- Provide unique node identification by firmware-configurable ID, resistor straps, or a commissioning protocol.
- Configuration and telemetry must work over CAN. Plan for a CAN firmware-update bootloader after initial SWD bring-up.

### USB/UART

- Fit a USB-C-to-UART service interface on Rev A for direct PC control, commissioning, logs, diagnostics, and interactive commands.
- USB-UART is a local service interface; CAN remains the normal production command, configuration, telemetry, and firmware-update transport.
- A USB-UART bridge can also provide STM32 ROM-UART programming when a supported UART pin pair, BOOT0 entry, and reset control are correctly implemented.
- USB-UART does not replace SWD for recovery and real debugging.
- Prefer a bridge with a separate VIO supply or verified 3.3 V UART levels.
- USB VBUS may power the complete `5V_SYS`/`3V3` control domain through the power mux. It must never energize VM, the STSPIN VCC gate-driver rail, the inverter, or the brake chopper.
- Prevent UART, reset, and boot-control signals from back-powering an unpowered STSPIN32G4 through its GPIO protection diodes. Use appropriate series resistance, isolation, or a bridge power arrangement validated for both power-up orders.
- Include USB-C USB 2.0 sink configuration with the required CC1 and CC2 pull-down resistors, connector-adjacent low-capacitance ESD protection, and controlled D+/D- routing.
- Connect the USB shield using a deliberate chassis/EMI strategy rather than automatically shorting it into a noisy power return at the connector.
- Reserve series-resistor footprints on UART TX and RX for signal integrity and isolation during bring-up.
- Provide manual BOOT0 and NRST access. Automatic bootloader entry using bridge handshake outputs is optional and must not interfere with normal operation.
- Expose UART TX/RX/GND test pads even though USB-UART is fitted.
- Firmware must offer the same core configuration object model over USB-UART and CAN so the two interfaces do not become separate maintenance paths.

## Programming and debug

- Use the 10-pin 1.27 mm Arm Cortex debug connector wired for SWD; a full JTAG interface is not required.
- Required signals: VTREF/3V3, SWDIO, SWCLK, NRST, and GND.
- SWO is not routed in Rev A because PB3 is committed to SPI3_SCK. SWDIO, SWCLK, NRST, VTREF, and GND provide the required debug path.
- Keep SWD traces short and accessible with the power stage assembled.
- SWD is the guaranteed first-programming, recovery, option-byte, and fault-debug path.
- Keep BOOT0 and NRST accessible by pads regardless of the USB-UART circuit state.

## Sensors and feedback

### Integrated magnetic encoder

- Use 4-wire SPI with a dedicated chip-select pull-up.
- The encoder must be mechanically centered on the motor axis within its datasheet tolerance.
- Keep motor phase copper and high-current vias away from the encoder and magnet region.
- If the PCB cannot physically occupy the shaft axis, move the encoder to a small daughterboard rather than compromising alignment.

### BMI323 IMU

- Use 4-wire SPI and connect INT1 to an interrupt-capable MCU GPIO.
- INT2 is optional but should be routed if pin budget allows.
- Power VDD and VDDIO from filtered `3V3` with the mandatory local decoupling.
- Locate the IMU away from MOSFETs, inductors, mounting-hole stress, board edges, and strong thermal gradients.
- Mark the IMU X/Y/Z orientation on silkscreen and in firmware documentation.
- The IMU is for body motion, tilt, impact, and vibration. It is not a substitute for shaft feedback.

### External feedback

- Support Hall U/V/W with configurable pull-ups and input filtering.
- Support incremental A/B/Z inputs at 3.3 V logic.
- External digital feedback in Rev A is ABI/index or Hall U/V/W only. External SPI/SSI feedback is deferred to a later revision.
- External-feedback inputs require ESD protection and series/filter footprints appropriate to cable length.
- Do not expose unprotected STM32 pins directly on a motor cable connector.

## PCB and mechanical constraints

- P3 uses six copper layers; see [ceramic / six-layer revision](PCB_CERAMIC_SIX_LAYER_2026-10-04.md).
- Approved P3 copper: 2 oz top/bottom, 0.5 oz on all four inner layers. L2/L5 GND, L3 signals, L4 power. The nominal dielectric geometry needs a matching fabrication build before impedance signoff.
- Separate power-stage, control/sensing, and connector zones while maintaining deliberate return-current paths.
- No high-current path through thermal-relief spokes.
- Use planes, pours, via arrays, and exposed copper/heatsink interfaces sized from current-density and thermal calculations.
- Minimize the commutation loop: bulk/ceramic capacitor to high-side MOSFET to low-side MOSFET/shunt and back to capacitor.
- Keep CAN and sensor routing out of switching-node regions.
- Target envelope: approximately 50 mm x 80 mm before connector/heatsink optimization, comparable to ST's compact high-power reference-design class.
- Define airflow, heatsink, mounting pressure, insulation, and maximum enclosure ambient as part of the electrical rating.

## Protection and validation gates

- Input surge, ESD, shoot-through, phase short, motor-stall, shunt-open, encoder loss, CAN fault, overtemperature, and regenerative overvoltage must have defined behavior. Reverse battery connection is explicitly outside the Rev A protection envelope.
- Measure MOSFET VDS overshoot with a suitable differential probe at maximum bus voltage and current.
- Validate hardware overcurrent shutdown before closed-loop high-power testing.
- Instrument MOSFET, shunt, capacitor, connector, STSPIN32G4, and PCB temperatures.
- Correlate all three NTC readings with measured MOSFET junction/case temperatures during characterization, including single-phase asymmetric loading and blocked-airflow tests.
- Validate current-sense offset/gain over temperature and under PWM common-mode disturbance.
- Ratings require testing at minimum and maximum battery voltage, intended PWM frequency, maximum ambient, stalled/low-speed operation, and regenerative braking.
- Rev A bring-up begins with a current-limited bench supply and low voltage; LiPo testing comes only after protection functions are proven.

## Prototype validation items

The Rev A schematic fixes the electrical architecture and the first-build component choices. The following items are intentionally completed during PCB layout, bring-up, or characterization rather than left as missing schematic circuits:

- Verify the CSD88599Q5DC, CSD19531Q5A, and TLV75533P custom land patterns against printed 1:1 package drawings and the chosen fabricator's via-in-pad process.
- Confirm the 0.5 milliohm shunts, gain of 28 with midscale bias, VDS/SCREF threshold, ADC range, and comparator hardware overcurrent threshold together before high-current testing.
- Validate the VBUS divider and ADC protection strategy against the measured VM transient ceiling; calibrate its gain in firmware.
- Confirm NTC placement and calibrate temperature thresholds against measured MOSFET case/junction behavior.
- Tune gate resistors, phase snubbers, and any VM damping or clamp population only from measurements on the assembled PCB.
- Validate AS5047P shaft alignment, external encoder/Hall cable behavior, and feedback-mux reset sequencing.
- Finalize heatsink/chassis contact, board outline, stack-up, copper weights, and fabrication current limits during PCB design.
- Confirm the CP2102N ROM-UART programming workflow; SWD remains the guaranteed programming and recovery path.

## A0 release operating constraints

USB-only service requires a 5 V source that permits at least 500 mA; USB pre-enumeration/suspend load shedding is not implemented. External feedback power is limited to 25 mA and signals to 0–3.3 V. Historical A0 used 2040 uF electrolytic bulk. P3 replaces it with 48 fitted CL32Y106KCVZNWE ceramics (480 uF nominal; approximately 160 uF typical at 42 V before temperature/tolerance/aging) plus six DNP positions and external-bulk pads. The new bank is not capacitance- or ripple-rating-equivalent; measure bus ripple, ringing and capacitor heating before extending the current envelope. The fitted hardware brake backup is approximately 45.9 V rising / 44.2 V falling and requires an installed, adequately rated external resistor. See the release review for the defined 219 J example and first-power-up restrictions.
