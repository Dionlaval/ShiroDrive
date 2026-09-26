# ShiroFOC A1-Drawing / A0 electrical release review

**Release scope: ready to begin first-prototype PCB layout in KiCad 9.** This release contains a complete schematic and resolved footprints. PCB routing, fabrication release, firmware implementation, and hardware qualification are subsequent work. The 18–42 V and 25/40 Arms objectives are design targets, not demonstrated ratings.

Electrical review date: 2026-09-15. Connected redraw review: 2026-09-16; see [redraw review](SCHEMATIC_REDRAW_REVIEW.md). Review method: manufacturer documentation, circuit calculations, KiCad 9.0.4 ERC/export, actual PCB footprint loading, full pin/net comparison, and rendered-sheet inspection. This is an agent-assisted engineering review; no human sign-off, SPICE switching simulation, STM32CubeMX run, or hardware test is represented as completed.

## Release evidence

The authoritative artifacts are in `ShiroFOC_KiCad/outputs/`:

| Gate | Result / evidence |
|---|---|
| Native hierarchy | Root plus 11 functional sheets; editable `.kicad_sch` and local `.kicad_sym` |
| Electrical rules | 0 violations across all 12 sheets; `erc_rev_a.json`; no ERC exclusions |
| Connectivity | 260 references, 148 connected nets, 761 symbol pins, including 42 explicit NC pins; `validation_report.json` |
| Footprints | 44 distinct footprint types loaded by `pcbnew`; all symbol pin numbers resolve to package pads; `footprint_audit.json` |
| Physical pad traceability | 895 pad/aperture entries, including repeated thermal-pad numbers and paste-only apertures; `footprint_pad_audit.csv` |
| Assembly | Complete ungrouped BOM including 18 explicit DNP references; native DNP attributes match BOM |
| Visual inspection | Every rendered PDF page; exact reviewed PDF hash in `visual_review.json` |
| Reproducibility | Native build, KiCad exports and checks scripted; `release_manifest.json` hashes the released sources and artifacts |
| Redraw equivalence | Every physical net partition, value, footprint, MPN and DNP state matches the frozen A0 release; local net-name changes are recorded |

ERC uses meaningful input/output/power types for ICs. Power flags identify external connector sources, passive-filtered supply outputs, and internal bootstrap supplies. They do not establish regulator stability or safe transient behavior. Analog MOSFET/shunt paths require the separate pin and package checks.

## Corrections incorporated

- Corrected CSD88599 side-pad numbering and VIN exposed-pad assignment; corrected the brake MOSFET to TI's Q5A copper/stencil pattern. A similarly sized generic SON footprint was electrically incompatible.
- Corrected TLV755 **DYD** land pattern and ground thermal pad. DYD is the thermally enhanced five-lead package; the exposed pad is intentionally numbered 2/GND.
- Corrected diode polarity, crystal pads 1/3 versus case pads 2/4, CAN ESD pin count, and high-frequency DC-link return placement.
- Completed all CP2102N QFN20 physical pins, including pins 10–14. VDD and VREGIN share the external 3V3 rail in documented regulator-bypass mode; UART and MCU no longer have independently sequenced logic rails.
- Added matched bipolar current-sense bias: 1 kΩ inputs, 28 kΩ feedback, and two 56 kΩ bias resistors per phase, all 0.1%. Zero current is midscale.
- Used TMUX channel 4 to isolate the live VM divider from an unpowered MCU. Both inputs carry the same divided voltage, so feedback-source selection does not alter VM sensing.
- Isolated the external-feedback ESD rail from 3V3 with its own 100 nF capacitor. External signal support remains **0–3.3 V**, including while board power is off.
- Assigned PB10 to CAN_STB, with a standby pull-up and recessive TX pull-up. Removed the PB8/BOOT0 test-point stub.
- Added a fitted TLV3012B overvoltage comparator, diode-OR control of the brake driver, and 100 V flyback diode across the external brake connection. The comparator works without executing MCU firmware when 3V3 and VCC are present.
- Assigned documented Wurth 74437349220 inductors to both buck converters, including the manufacturer's central copper keepout. Replaced the obsolete bulk-capacitor MPN with Panasonic EEVFK1J681M.

## Electrical review and operating envelope

### Current sensing and protection

`VOUT = VREF/2 + 28 × (VSENSE_P − VSENSE_N)`. With 0.5 mΩ shunts, gain is 14 mV/A: −80/0/+80 A gives 0.53/1.65/2.77 V at VREF=3.3 V. The shunt dissipates 0.8 W at 40 Arms and 3.2 W instantaneously at 80 A, subject to its terminal-temperature rating and pulse curve. The amplifier's calculated resistor-only zero-current offset spans 1.6436–1.6564 V. Calibrate actual offset/gain and temperature drift.

COMP1/2/4 observe PA1/PA7/PB0. Their positive-input voltage is `(56 × 0.0005 × I + VREF)/58` when the negative Kelvin terminal is near analog ground. A nominal +60 A threshold is 85.86 mV, about code 107 of a 12-bit DAC at 3.3 V. This is an initial engineering target, not a guaranteed trip current: comparator offset, DAC accuracy, filtering, shunt tolerance, and temperature require calibration. These are **one-sided** trips; negative-current limits also need ADC supervision. Preserve VDS protection as the independent short-circuit mechanism. SCREF ≈0.30 V is a VDS fault threshold, not an accurately calibrated phase-current limit.

The internal comparator and timer-break path acts without CPU intervention **after firmware configures it**. It is not active protection in a blank MCU; reset keeps PWM inactive instead. See [firmware contract](FIRMWARE_BRINGUP_CONTRACT.md).

### Bus, gate drive and DC link

The VM divider is 540 kΩ / 27 kΩ: 2.00 V at 42 V and 2.857 V at 60 V. Its nominal RC time constant is 267 µs; allow at least 2 ms after enabling the mux. A 60 V divider calculation does not authorize 60 V bus operation.

The three 680 µF capacitors store about 1.80 J at 42 V. Their summed nameplate ripple rating is only **5.07 Arms at 100 kHz**, before temperature/frequency correction and unequal sharing. This is a potentially limiting item for the 25/40 Arms goal. Measure capacitor ripple and temperature during the current ramp; additional parallel bulk capacitance or a lower operating-current limit may be necessary. The PCB must preserve access to VM/GND for an external low-inductance capacitor bank during characterization.

STSPIN VCC starts at 8 V; firmware selects 10 V. The 22 µH L301 is a deliberate prototype substitution for ST's typical 18 µH example, with ample saturation-current margin; verify startup, regulation and ripple on hardware. The external 5 V converter also uses 22 µH. LMR36510 output is approximately 5.016 V from its 100 kΩ/24.9 kΩ divider. Review effective ceramic capacitance at operating bias during procurement.

Use 20 kHz initial center-aligned PWM, interlocking enabled and a conservative initial MCU deadtime (500 ns, then characterize). For a conservative 56 nC per MOSFET, six gates at 20 kHz consume about 6.72 mA average charge current. A 100 nF bootstrap capacitor loses 0.56 V for 56 nC before leakage and DC-bias derating. Enforce a low-side refresh interval; 100% static high-side duty is unsupported. TI's 4.7 Ω GH / 0 Ω GL starting resistors and separate gate-source pull-downs are fitted. Independent diode-assisted turn-on/turn-off paths from the early wishlist are not populated in this revision; per-gate resistor substitution and DNP phase snubbers provide tuning.

### Brake energy and overvoltage

Nominal hardware thresholds are **45.92 V rising / 44.21 V falling**. The conservative component-corner estimate is 44.19–47.51 V rising and 42.58–45.96 V falling, including reference tolerance plus extra temperature drift allowance, comparator offset/hysteresis, resistor tolerances and output swing. It does not include wiring inductance or dynamic overshoot. Firmware should begin normal braking earlier (43 V starting point for 10S); stop motoring on overvoltage and control regenerated energy.

Defined prototype example: a 0.01 kg·m² load at 2,000 rpm contains 219 J. A **10 Ω external resistor**, at least **250 W on its specified heatsink** and independently rated for **500 J over 5 s**, covers this example with energy margin. At 48 V it draws 4.8 A and dissipates 230 W. This does not cover gravitational work, externally driven motion, repeated stops without cooldown, or every motor. Select the actual resistor from the application's worst energy and repetition rate before regenerative operation.

Use short twisted brake leads. D504 (100 V / 5 A) recirculates lead inductance; it does not dissipate the motor's sustained regenerative energy. If the resistor is open/absent, braking is unavailable. A shorted resistor is a destructive fault unless the upstream fuse/current-limited source clears it. The backup also cannot work with VCC or 3V3 absent. No battery-reverse or onboard precharge protection is claimed.

### Control power and interfaces

The planning allowance is 250 mA at 3V3 (320 mA during a CAN bus fault), including 25 mA maximum external-feedback load. LDO loss is about 0.488 W at 5.25 V input and 250 mA, or 0.624 W during that fault allowance. Connect the DYD thermal pad and validate junction temperature, especially in an enclosed hot power stage. The 1 A buck and 500 mA LDO have current margin; thermal margin depends on layout.

USB-only service requires a 5 V source that permits at least 500 mA. The board does not implement USB pre-enumeration/suspend load shedding or USB-PD/current-advertisement control. Do not claim arbitrary legacy PC-port bus-power compliance. Use an appropriately powered service source/hub, or a service setup that provides the required current allowance. CP2102 configuration must match the intended self-/bus-powered mode and descriptor current.

The 5 V mux has reverse-current blocking and selects USB when both valid inputs are present. The STSPIN power stage stays unpowered with USB alone. SWD VTREF is sense-only; a debugger must not feed 3V3. J601 supply is an output, not an external power-injection point. External inputs above 3.3 V or negative voltages are unsupported; the mux is not a level translator.

## Fault and startup disposition

| Condition | Hardware behavior / required response |
|---|---|
| Erased MCU, reset, or USB alone | Inverter inputs default low; mux disabled; PB8 low; CAN standby. Brake input is low below its OV threshold; no brake gate drive without VCC. |
| Battery alone / both sources | External 3V3 powers logic; VM separately powers VCC. Mux prefers valid USB. Validate power switchover brownout behavior. |
| VM disappears and returns with USB attached | MCU survives; invalidate motor state and reinitialize the STSPIN driver, VCC setting and protections before torque. |
| Regeneration / BMS opens / nonsinking PSU | Fit and qualify the external brake resistor. Hardware OV backup may assert during reset. Neither the DNP TVS nor a battery is assumed to absorb all energy. |
| Bus hot-plug | External fuse and precharge/current limiting required for first tests. D101/R102/C107 are unqualified tuning positions. |
| Phase short / stall | Configured comparator/TIM1 break plus STSPIN VDS faults; latch off. Hardware short-circuit performance requires measured testing before high energy. |
| Feedback loss / invalid Hall states | Inhibit PWM, then isolate feedback if needed. Disabling the mux also invalidates VM sensing. |
| NTC open / short | Read near full-scale / zero; declare fault and inhibit torque. Calibrate real temperature and lag. |
| External feedback powered, board off | TMUX isolates MCU; floating ESD supply rail avoids a DC path into 3V3. 0–3.3 V signal contract still applies. |
| CAN cable before power / bus fault | TCAN bus protection and power-off behavior apply; standby held through reset. Verify actual network EMC and bus faults. |
| USB cable before power | CP2102 VBUS divider and same-rail UART eliminate the previous split-rail issue. Verify attach/detach and descriptors. |
| VCC, 3V3 or 5V_SYS fault | Driver UVLO/default pulls prevent intended switching; firmware brownout/reset inhibits torque. Backup braking is unavailable without its supplies. |

## Source basis

- [STSPIN32G4 DS13630 Rev 2](https://www.st.com/resource/en/datasheet/stspin32g4.pdf): exposed pins, bypass power, internal driver connections, VCC and protection. Local PDF retained. Exposed peripheral choices were checked against its pin-description table. [ST EVSPIN UM2850](https://www.st.com/resource/en/user_manual/um2850-getting-started-with-the-evspin32g4-evspin32g4nh-stmicroelectronics.pdf), current-sense protection example; [ST G4 LL comparator header](https://github.com/STMicroelectronics/stm32g4xx-hal-driver/blob/master/Inc/stm32g4xx_ll_comp.h), internal DAC choices.
- [TI CSD88599Q5DC SLPS597D](https://www.ti.com/lit/ds/symlink/csd88599q5dc.pdf), DMM0022A drawing 4222731/B; [CSD19531Q5A SLPS406B](https://www.ti.com/lit/ds/symlink/csd19531q5a.pdf), Q5A/DQJ copper and stencil; [TLV755P](https://www.ti.com/lit/ds/symlink/tlv755p.pdf), DYD0005A drawing 4228946/A.
- [LMR36510](https://www.ti.com/lit/ds/symlink/lmr36510.pdf), [TPS2121](https://www.ti.com/lit/ds/symlink/tps2121.pdf), [Wurth 74437349220](https://www.we-online.com/components/products/datasheet/74437349220.pdf), [Panasonic EEVFK1J681M](https://industrial.panasonic.com/tw/products/pt/aluminum-cap-smd/models/EEVFK1J681M), [BVR shunt](https://www.isabellenhuette.com/hubfs/143808517/files/Data%20sheets/BVR.pdf).
- [TLV3012B](https://www.ti.com/lit/ds/symlink/tlv3012.pdf), [UCC27517A](https://www.ti.com/lit/ds/symlink/ucc27517a.pdf), [B5100C](https://www.diodes.com/datasheet/download/B5100C.pdf), [TMUX1574](https://www.ti.com/lit/ds/symlink/tmux1574.pdf), [TPD3E001](https://www.ti.com/lit/ds/symlink/tpd3e001.pdf). Specify the **B** comparator for fail-safe inputs and power-on behavior.
- [CP2102N Rev 1.5](https://www.silabs.com/documents/public/data-sheets/cp2102n-datasheet.pdf), Fig. 2.3 and QFN20 pin table; [TCAN3413](https://www.ti.com/lit/ds/symlink/tcan3413.pdf). Sensor and connector sources remain in their schematic Datasheet fields.

## Remaining stage gates

There are no known unresolved schematic connectivity or assigned-footprint blockers in this release. Before fabrication: finish placement/routing, stack-up/current/thermal design, mechanical fit, DRC, printed footprint checks and fabricator review of via-in-pad/stencil details. Before raising power: verify regulation, fault shutdown, brake energy, switching overshoot, capacitor ripple and temperature. Raising the 25/40 Arms or 10S targets to guaranteed ratings can require another hardware revision.
