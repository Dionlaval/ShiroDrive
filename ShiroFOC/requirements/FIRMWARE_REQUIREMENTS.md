# ShiroFOC firmware requirements — P2 baseline with P3 divider updates

**Baseline:** 27 September 2026, `Manual_Layout_P2/ShiroFOC_Manual.kicad_sch`.
**Revision change:** optional external brake NTC on PC2; status LED moved from PC2 to PC15. The archived Manual_Rebuild project retains the previous pin assignment.
**P3 divider update (4 October 2026):** `Manual_Layout_P3` uses 560 kΩ / 28 kΩ for bus sensing (the nominal ×21 firmware scale is unchanged), and the hardware OV divider now trips nominally at 45.8 V / releases at 44.1 V. P2 files retain their original divider components. The rows and filter timing below describe the revised P3 dividers; other requirements retain the P2 baseline pending revision-specific verification.
**Status:** implementation contract, not implemented or safety-qualified firmware.

This is the current firmware requirements document. It supersedes conflicting instructions in the older A0 bring-up contract, pinout plan and design constraints. **MUST** means required; **PROVISIONAL** means a bring-up starting point that requires measurement before release. An unresolved safety parameter must prevent normal arming, rather than silently receiving a guessed default.

## 1. Hardware the firmware must match

| Item | Current baseline |
|---|---|
| MCU | STSPIN32G4's STM32G431; 128 kB internal program/data flash, 32 kB SRAM |
| Battery target | 10S LiPo, 42.0 V fully charged; separately configured 6S/8S support |
| Current target | Provisional 25 A RMS phase current **with qualified cooling**; not a demonstrated board rating |
| Gate supply | External approximately 10 V: VM → LMR36510 → VCC; SW tied to VM |
| Logic supplies | VCC → MPM3620A → 5V_BAT; USB/battery mux → 5V_SYS → 3V3 LDO |
| Current sensing | Three 0.5 mΩ shunts; external op-amp feedback gain 28; nominal 14 mV/A about VREF/2 |
| Bus measurement | P3: R103 = 560 kΩ (0603, 75 V), R105 = 28 kΩ (0402), both 0.1%; nominal division by 21; R104 removed; R106 = 1 kΩ, C108 = 10 nF |
| Angle | AS5047P absolute-angle SPI3, dedicated bus |
| IMU | BMI323 on I2C2, address 0x68; configuration and data over I²C |
| External feedback | Three buffered 3–5 V single-ended Hall or ABI inputs, selected through TMUX1574 |
| Brake | PB9/TIM17 request ORed with independent hardware overvoltage command |
| Hardware OV backup | P3: nominal 45.8 V on / 44.1 V off using 470 kΩ / 13.3 kΩ and 1 MΩ feedback, all 1%; tolerance and transient overshoot remain to be measured |
| External brake resistor | Provisional 10 Ω, Vishay RH25010R00FE01; thermal rating depends on mounting |
| Brake temperature | Optional 10 kΩ-at-25°C external NTC on J502; PC2/ADC12_IN8; configure actual probe curve |

**FW-HW-01:** Bind the firmware to a board revision and a reviewed schematic/netlist identity. Stop and report a mismatch rather than importing settings from the old reference board. Preserve a generated pin/peripheral map, driver register configuration, configuration schema and test results in the firmware repository.

**FW-HW-02:** The MOSFET symbol/footprint reconciliation and other existing hardware review items remain prerequisites to energizing an assembled board. Firmware cannot establish that the physical board matches the schematic. No firmware setting authorizes 60 V operation, 100 A operation, or a battery configuration inferred from component absolute maximum ratings.

## 2. Persistent BOOT0 configuration and recovery

PB8 is both external index/Hall input and BOOT0. Removing the BOOT button does not change that silicon function.

**FW-BOOT-01 — provision these option bytes:**

| Field | Required setting | Meaning |
|---|---|---|
| `FLASH_OPTR.nSWBOOT0` (bit 26) | **0** | Select BOOT0 from the option byte, ignoring the PB8 level for boot selection |
| `FLASH_OPTR.nBOOT0` (bit 27) | **1** | Select main flash with the setting above |
| NRST mode | Retain external reset function | PG10 must remain usable by SWD connect-under-reset |
| RDP | Level 0 for this development board | Keep debug/recovery available; never program irreversible Level 2 |

ST's HAL names for the first two settings are `OB_BOOT0_FROM_OB` and `OB_nBOOT0_SET`. `nBOOT1` does not determine the main-flash result for this combination; preserve and record its value rather than rewriting unrelated bits. See [ST boot table](https://www.st.com/resource/en/application_note/an5094-migrating-between-stm32f334303-and-stm32g431g474g491-mcus-stmicroelectronics.pdf), table 6, and [ST HAL definitions](https://github.com/STMicroelectronics/stm32g4xx-hal-driver/blob/master/Inc/stm32g4xx_hal_flash.h). The inverted `n...` naming matters.

**FW-BOOT-02:** Program and verify option bytes in the controlled **SWD provisioning process**, preferably with STM32CubeProgrammer. Read the existing option bytes, change only intended fields, perform the required reload/reset, read back, then power-cycle and test boot with external feedback high and low. Use stable control power, stationary motor, inverter disabled and no pending braking requirement. Record the result with the board serial number and firmware version.

**FW-BOOT-03:** These settings persist through loss of power and are not normal RAM variables. Merely writing a GPIO in `main()` is too late to determine that boot's memory selection. Application startup MUST inspect the effective configuration and prohibit arming if it is wrong. Do not automatically rewrite option bytes every boot. A deliberate one-time firmware provisioning routine is possible, but must follow the same disarmed, stable-power, readback and reset procedure.

**FW-BOOT-04:** Retain hardware reset isolation: PC14 mux enable inactive/high, PD2 select low, R307 holding PB8 low. Do not depend exclusively on this isolation instead of provisioning option bytes. Blank/corrupt flash is a recovery case, not a normal flash-boot guarantee. First programming and recovery use SWD; PB8 high will no longer request the ROM bootloader. USB here is a **CP2102N UART bridge**, not a directly wired MCU USB-DFU connection.

**FW-BOOT-05:** Choose and record BOR/PVD settings using the actual MCU supply/clock/flash specifications. Do not invent a BOR code from another STM32 family. Brownout must inhibit torque and flash writes. Retain the option-byte manifest through firmware updates and verify it after programming operations that can affect it.

## 3. Calibration and configuration in nonvolatile memory

**FW-NVM-01:** Use reserved, linker-protected **normal internal flash** for calibration/configuration; no external memory is required for the initial implementation. This is separate from BOOT0 option bytes. Do not put routinely editable calibration in OTP. VBAT is tied to 3V3, so backup RAM/registers are not a substitute for storage across complete power loss.

**FW-NVM-02:** Store versioned records with board identity, motor identity, units, length, monotonic generation, integrity check and a final commit marker. Use two independently erasable storage areas, or a proven wear-levelled journal: keep the old valid record until a new record is written and verified. On interrupted erase/write, recover the newest complete valid record. Verify the exact STM32G431 flash erase/program geometry and ECC rules before choosing addresses; reserve space in the linker and updater. See [ST EEPROM-emulation guidance](https://www.st.com/resource/en/application_note/an4894-eeprom-emulation-techniques-and-software-for-stm32-microcontrollers-stmicroelectronics.pdf).

**FW-NVM-03:** Persist motor pole-pair count, phase order/direction, electrical zero offset, selected feedback type, Hall sequence or ABI scale where applicable, validated gains/limits, battery profile and brake-resistor configuration. Store calibration quality/version and relevant temperature. Never persist “armed”, a live torque request, or automatic permission to resume motion. Re-estimate current offsets with PWM off at startup; a stored offset is a plausibility reference, not proof the live offset is correct.

**FW-NVM-04:** Only save on explicit configuration commit or successful calibration, with wear accounting. No writes from the FOC interrupt and no continuous flash fault logging. Invalid/out-of-range/NaN/CRC-failed data selects an unarmed configuration-required state. Motor identity or schema mismatch invalidates the relevant calibration.

**FW-NVM-05:** Flash erase/program can stall code and interrupts on this MCU. Therefore write/update only with inverter disabled, rotor stationary or mechanically secured, bus stable and no software-braking dependency. “Disarmed” alone is insufficient: an externally driven motor may still regenerate. Defer the write if these conditions cannot be established. Power-fail testing must show recovery of either the old or new record, never a partly accepted record. Preserve calibration across ordinary firmware upgrades, or explicitly invalidate incompatible records.

## 4. Startup, state machine and arming

**FW-STATE-01:** Implement explicit states: `RESET_SAFE`, `SERVICE_ONLY`, `SELF_TEST`, `DISARMED`, `CALIBRATION`, `ARMED`, `FAULT_LATCHED`. CALIBRATION may generate torque and requires its own explicit permission, low limits and abort conditions. No path from reset, restored power, watchdog reset or fault clear may automatically resume motor torque.

**FW-START-01:** Before peripheral initialization, keep TIM1 main-output enable (MOE) cleared; define all six PWM idle levels as inactive and verify complementary-output polarity. PB9 brake request starts low. CAN standby/PB10 remains high. Preload output latches before changing pin modes to avoid enable pulses.

**FW-START-02:** Initialize the 24 MHz HSE/PLL, flash latency and voltage scaling from the exact MCU clock limits. Clock failure must produce a defined inverter-off fault. Keep SWD; configure PB3/PB4/PA15 for SPI rather than competing JTAG/SWO. Set `PWR_CR3.UCPD1_DBDIS = 1` early so USB-C dead-battery loads do not load PB4/PB6. Keep the internal VREFBUF output disabled because VREF+ is externally supplied.

**FW-START-03:** Set PD2 low, configure PC14 as a low-speed open-drain output, then pull PC14 low to enable the input mux. Keep it enabled for VM sensing even when using onboard SPI feedback. Wait **at least 2 ms**, obtain multiple plausible VM samples, and only then accept VM as valid. Mark VM invalid before disabling the mux. Its fourth channel carries the divider regardless of PD2 selection.

**FW-START-04:** Calibrate ADCs and initialize OPAMP1/2/3 for the actual external-feedback networks. With gates off and the motor stationary, acquire offset statistics, check all three channels and validate temperatures/reference voltage. If the motor is being back-driven, wait or enter a defined recovery state; do not learn its current as a zero offset.

**FW-START-05:** Initialize the internal gate-driver I2C3 connection with bounded retries. Apply and read back the board-specific register configuration after every driver power-up/reset, including VM loss while USB keeps the MCU alive. The board uses **external VCC and external 3V3**: configure the documented bypass/disable policy (`POWMNG.VCC_DIS = 1`, `REG3V3_DIS = 1`, standby regulator disabled), using the protected-register sequence and checking resulting READY/UVLO behavior. Do not execute the old “raise internal VCC from 8 V to 10 V” startup procedure. Hardware wiring must already permit safe power-up before firmware runs. Verify this sequence on the prototype; do not use standby modes until external-supply behavior is qualified.

**FW-START-06:** Enable driver interlocking, VDS protection, deadtime and the verified timer-break sources before any gate activity. Check READY, nFAULT, reset status and readable configuration. A high READY alone is insufficient. Do not repeatedly clear a fault to force startup. Establish bootstrap precharge using a bounded, tested sequence with fault monitoring; constrain high-side on-time and PWM modulation to preserve bootstrap refresh and current sampling.

**FW-ARM-01:** Arming requires a fresh explicit command, valid boot/configuration, completed self-test, valid position/current/VM/temperature, verified protection configuration, valid battery/motor limits, and a qualified regeneration-energy path. Require zero initial torque and ramp limits. USB-only operation allows service/configuration but no inverter gate commands. A successful I²C read alone does not prove motor power is present.

## 5. Peripheral ownership and acquisition

| Function | Pins/resources | Required behavior |
|---|---|---|
| Inverter | TIM1; internal PE8–PE13 | Complementary PWM; hardware break; no reuse for unrelated PWM |
| Driver | I2C3 PC8/PC9; PE7 WAKE; PE14 READY; PE15 nFAULT | Reserved internal connections; verified AF/break mapping |
| Current U | PA1 +, PA3 −, PA2 out | OPAMP1 external feedback; ADC1_IN3 |
| Current V | PA7 +, PC5 −, PA6 out | OPAMP2 external feedback; ADC2_IN3 |
| Current W | PB0 +, PB2 −, PB1 out | OPAMP3 external feedback; ADC1_IN12 |
| VM | PA0 | ADC1/2_IN1; mux validity required |
| NTC U/V/W | PC3 / PC0 / PC1 | ADC channels 9 / 6 / 7 |
| Brake NTC | PC2 / STSPIN pad 11 | ADC1 or ADC2 channel 8; regular slow acquisition, no GPIO output |
| Status LED | PC15 / STSPIN pad 5 | Active-low open-drain output, low speed; R304 = 2.2 kΩ; not spare GPIO |
| Angle | PB3 SCK, PB4 MISO, PB5 MOSI; PA15 CS | Dedicated SPI3, mode 1; GPIO CS |
| IMU | PC4 SCL, PA8 SDA; PA4/PA5 interrupts | I2C2, open-drain, 400 kHz; 0x68; EXTI4/5 |
| External feedback | PB6/PB7/PB8 | TIM4 Hall or quadrature; index handled explicitly |
| External sensor supply fault | PC13 / pad 3 | EXT_SENSOR_FAULT_N, active-low input; optional EXTI13; external 10k pull-up to3V3 |
| Input mux | PD2 / PC14 | Select external inputs / active-low enable |
| Brake request | PB9 | TIM17_CH1; do not use TIM4_CH4 here |
| CAN | PA11 RX, PA12 TX; PB10 STB | FDCAN1; TX recessive before releasing standby |
| Service UART | PA9 TX / PA10 RX | USART1 through CP2102N |
| Debug | PA13 / PA14; PG10 NRST | SWD and reset retained |

**FW-ADC-01:** Three op-amps do not provide three simultaneous ADCs. ADC1 is shared by U and W. Schedule synchronized conversions in valid low-side conduction windows; account for deadtime, blanking, op-amp settling, ADC acquisition and channel switching. Reject clipped/out-of-window samples. Reconstruct the third current from two valid samples only under the appropriate three-wire motor assumptions. Limit modulation when sampling windows become too short. Slow VM/NTC/reference measurements must not disrupt current acquisition.

**FW-ADC-02:** Nominal conversion is `I_phase = (V_adc − V_offset) / 0.014`, with sign verified physically for each phase. Use measured VREF and calibrated scaling. Define whether every API limit is instantaneous peak, RMS, dq amplitude or battery current. The 25 A RMS target corresponds to about 35.4 A sinusoidal peak; neither the ADC's approximate ±100 A range nor a MOSFET headline rating is a permissible current limit. Start commissioning at 1–2 A instantaneous and raise limits only against recorded tests.

**FW-OCP-01:** Provide an ISR-independent fast inverter shutdown using verified on-chip comparator/TIM1-break routing and STSPIN VDS protection. The previous proposed COMP1/2/4 paths observe biased op-amp **inputs**, not the amplified ADC outputs. Re-derive DAC thresholds, polarity, offset sensitivity, common-mode validity and exact internal routing from the schematic and MCU reference manual. Do not copy the old illustrative “60 A / DAC code 107” into a release. This path is not automatically a precise bipolar current limit. Require software limits for both polarities and demonstrate low-energy fault injection into each implemented hardware trip path. VDS protection is not a calibrated phase-current measurement.

**FW-ANGLE-01:** Check AS5047P parity, error flags, magnetic diagnostics, transaction timeout, sample age and physical angle/speed plausibility. Account for pipelined replies and angle latency; use mechanical angle × pole pairs + calibrated electrical offset with the verified sign convention. Absolute readout removes cumulative missed ABI counts, but invalid/stale readings remain faults. Do not invent a fallback Hall/sensorless mode on loss of angle. A bounded stale-sample policy must be explicitly validated against maximum electrical speed.

**FW-IMU-01:** Configure and read BMI323 entirely over I²C, including its two dummy read bytes. Start with a 1 ms sample period and nonblocking transfers. IMU traffic/recovery must not block the FOC loop or gate-driver safety handling. For motor-only control, IMU failure may be a reported degraded mode; if a robot's balance/stability controller depends on it, that application must specify a timely safe-stop policy.

**FW-EXT-01:** Hall and ABI are separately configured modes. For Hall, validate the calibrated sequence, illegal states and transition timing. For ABI, validate counts/revolution convention, direction, rollover, index behavior and electrical-angle initialization: incremental data alone gives no absolute angle after power-up. Select PD2 high only while disarmed with timer state reset and inputs checked. Switching sources must not step the torque angle. The JP601 voltage jumper and optional 4.7 kΩ Hall pull-ups are hardware configuration, not software-selectable features.

**FW-EXT-02 — protected sensor supply:** U604 TPS2553DBVR feeds J601.1 and any fitted Hall pull-ups after JP601. It is always enabled when the selected supply is present; firmware does not enable or reset this switch. ILIM is tied to IN for a75mA nominal limit (specified50–100mA); normal total sensor/pull-up budget stays25mA. Configure PC13/pad3 as a digital input named `EXT_SENSOR_FAULT_N`, never drive it. R60410k pulls its open-drain fault output to3V3; TP1023 exposes the same net. PC13 is no longer SPARE_GPIO_3. PC15 remains spare.

**FW-EXT-03 — fault response and recovery:** Sample the fault before arming and monitor during operation (EXTI13 and/or bounded polling). If external Hall/ABI feedback is selected, an asserted fault must inhibit arming or disable motor PWM and latch a reported sensor-supply fault; do not keep applying torque using the lost position feedback. Hardware current limiting is immediate on the device's response timescale; FAULT reporting is internally deglitched (7.5ms typical), so it is not an instantaneous short detector. Retain Hall/ABI validity/time-out checks. Automatic recovery of the switch or a deasserted FAULT must not automatically resume motor drive: require valid feedback and an explicit re-arm. While using the independent onboard magnetic encoder, report/isolate the external accessory fault according to application policy; do not invent an automatic feedback-source swap.

**FW-EXT-04 — scope and commissioning:** FAULT high does not prove that JP601 is bridged, that a sensor is connected or that its supply is healthy; the signal reports switch faults, not every cable/sensor failure. Test shorts at J601.1 toGND at both3.3V/5V selections, including power-up into a short, USB-only operation, maximum intended control load and fault removal. Verify MCU supply stays above its brownout threshold, thermal cycling remains acceptable, and firmware does not auto-rearm. Protection is for the low-voltage accessory power branch, not motor/VM shorts into Hall pins. User CAD/PCB tasks remain deferred.

## 6. Brake chopper, battery profiles and regeneration

**FW-BRAKE-01 — separate the two jobs:** Firmware manages normal bus rise using battery-profile thresholds. The comparator marked **“Capacitor un-exploder”** is an independent last-resort board-bus backup, nominally 45.9/44.2 V. It is **not a BMS**, cell monitor, guaranteed capacitor protector, or appropriate normal cutoff for 6S/8S packs. The board does not measure individual cell voltages or provide a battery-disconnect switch.

**FW-BRAKE-02:** Require an explicitly selected chemistry/cell-count profile; do not infer 6S/8S/10S solely from pack voltage because their operating ranges overlap. Store full-pack voltage, charge acceptance policy/current bound, undervoltage derate/cutoff, software brake thresholds, fault threshold and hysteresis. A **10S bench starting example** is brake on near 43.0 V and off near 42.5 V; these are PROVISIONAL, not battery charge limits. Derive 6S/8S settings separately from their 25.2/33.6 V full-charge levels, sensing error and tested transients. A missing profile prevents arming.

**FW-BRAKE-03:** Choose thresholds so a fresh valid pack does not continuously discharge into the resistor, while the worst-case software regulation/overshoot remains below the earliest hardware trip and the qualified board limit. Use the comparator's tolerance bounds, not just its nominal 45.9 V. Do not raise the backup target to 60 V. The hardware threshold cannot be changed by firmware.

**FW-BRAKE-04:** Schedule VM acquisition and brake control independently of host traffic. Apply bounded duty, hysteresis or a stable control law with anti-windup; avoid rapid chatter and duty jumps. The divider/1 kΩ/10 nF network has an approximate **277 µs** time constant in P3 (560 kΩ ∥ 28 kΩ, plus 1 kΩ, with 10 nF; neglecting mux resistance and ADC loading) before ADC and software delays. Initial VM sampling at least 1 kHz is a scheduling starting point, not proof of sufficient response. Derive and measure the total reaction budget using worst-case net regenerative current and effective bus capacitance: `dV/dt ≈ I_net / C_bus`. Include filtering, conversion, scheduling, gate-drive and resistor response. Increase sampling/control rate or restrict braking energy as required by that budget.

**FW-BRAKE-05:** For the provisional 10 Ω resistor, use `I_on = Vbus/R`, `P_average ≈ duty × Vbus²/R` and `E = integral(P dt)` in duty/energy limits. Full-on examples: 42 V → 4.2 A / 176 W; 46 V → 4.6 A / 212 W. Its “250 W” rating requires specified heatsinking; the documented free-air rating is 100 W at 25°C. Account for tolerance, ambient, cooling, pulse duration and repeated stops. P2 has an **optional brake-resistor NTC input**, but still no brake-current or power-resistor continuity sensor. A connected NTC does not prove that the power resistor is connected. Treat calculated energy as an estimate and require an installation/commissioning record; do not claim software detects an open resistor.

**FW-BRAKE-06:** If predicted regeneration exceeds the battery's allowed acceptance plus the qualified resistor capacity, reduce requested regenerative torque/deceleration before bus voltage becomes critical and notify the higher-level controller that the requested stop cannot be sustained. A larger motor or resistor wattage label does not automatically increase the existing chopper's capability. A BMS may abruptly stop accepting charge; the local bus can then rise. Do not assume a connected battery or laboratory supply will absorb energy. RC LiPo operation requires explicit configuration acknowledging the absence of per-cell protection; bus regulation cannot replace it.

**FW-BRAKE-07:** Inverter disable and brake disable are separate operations. On an inverter fault, stop commanded motor switching immediately, but continue software bus protection when its measurements, supply and execution remain trustworthy. A coasting or externally driven motor can still regenerate through body diodes. Do not implement a blanket “stop every PWM” fault handler that unnecessarily kills a healthy chopper.

**FW-BRAKE-08:** The hardware OV command can hold the chopper on despite PB9 being low or the MCU being reset, provided its supplies remain available. It has no routed MCU status input, so firmware cannot directly know that it fired. Software cannot override it or guarantee resistor thermal shutdown. If VM sensing or software control is invalid, clear the software brake request, latch the inverter off and report loss of normal bus control; the hardware backup is the remaining limited protection, not a guarantee. Resistor overheating and bus overvoltage can conflict: reduce energy generation early and require the system's mechanical/energy-management response rather than promising a firmware-only solution.

## 7. Fault handling, timing and communication

**FW-FAULT-01:** Hardware breaks must latch inverter outputs inactive without depending on an interrupt. Disable automatic restart. ISR/foreground code records the cause; fault clear requires stable healthy conditions, explicit acknowledgement and a separate fresh arm command. A fault cannot erase the history before it is captured. Fault recovery never restores a stored torque command.

| Condition | Minimum required response |
|---|---|
| Hardware overcurrent, VDS trip, nFAULT or loss of driver readiness | Hardware inverter disable where supported; latch fault; retain healthy bus protection |
| ADC overrun, invalid current window, implausible current or FOC deadline miss | Reject bad data; apply validated bounded fallback or latch off; no indefinite stale control |
| Invalid/stale angle, illegal Hall sequence | No uncontrolled commutation; latch inverter off after the validated detection budget |
| Bus OV/UV, VM loss or driver reset while USB remains | Restrict torque / trip as configured; invalidate driver state; repeat startup on return |
| NTC open/short, implausible temperature or overtemperature | Inhibit arming or derate/trip as defined; do not interpret a broken sensor as a cold board |
| Command timeout, CAN bus-off or service disconnect | Apply configured bounded stop if feedback and energy capacity permit; otherwise inverter off; no automatic re-arm |
| Watchdog reset, HardFault, brownout or clock failure | Inactive inverter outputs; reset into unarmed state; log recoverable cause |
| Brake energy budget exhausted / resistor installation unknown | Inhibit or restrict regeneration; latch/report as appropriate; do not assume braking torque is available |

**FW-TEMP-01:** Current NTCs are nominal 10 kΩ at 25°C, B3380, to ground with 4.7 kΩ pull-ups. Use the exact selected part's curve, tolerance and measured ADC scaling. Open tends toward VREF, short toward ground. Set plausibility thresholds outside legitimate cold/hot extremes. Use the hottest valid phase reading and validate thermal lag to MOSFET junctions. Release derate/trip temperatures require measured board/cooling evidence; the NTC is not a direct junction thermometer.

**FW-TEMP-02 — optional brake probe:** J502 pin 1 is the thermistor signal and pin 2 is GND. R511 = 10 kΩ to 3V3, R512 = 4.7 kΩ series into PC2, C505 = 100 nF to ground, D505 = BAT54S rail clamps. Nominal transfer is `Vadc = V3V3 × Rntc / (10000 + Rntc)`; the series resistor is outside the DC divider when input/clamp leakage is negligible. Use actual 3V3-to-VREF scaling, the selected probe's resistance/temperature curve and tolerances; do not reuse the phase sensors' 4.7 kΩ pull-up or assume their B3380 curve. The external probe is not yet selected. Account for diode leakage over board temperature in coarse threshold validation.

**FW-TEMP-03:** Persist `brake_ntc_present`, probe curve/calibration, valid range, derating threshold, overtemperature threshold and hysteresis. Without a probe explicitly configured, report temperature as unavailable and retain conservative resistor energy/duty limits; an open connector is allowed in that mode. If configured present, an open/high, short/low, stale or implausible reading is a sensor fault, never a cold resistor. Validate fault thresholds against legitimate hot/cold extremes. Do not automatically decide the probe is absent after a fault.

**FW-TEMP-04:** Configure PC2 analog mode without pulls; sample channel 8 in the slow ADC schedule without disturbing injected phase-current measurements. Start with 20 Hz monitoring, adequate ADC acquisition time, and at least 10 ms settling after the supply/reference becomes valid (worst nominal external RC time constant 1.47 ms). Validate end-to-end lag including the sensor attachment and software filtering. Use resistor temperature to derate regeneration early and inform the host. The surface probe does not protect against a short energy pulse before its temperature catches up: retain energy integration and pulse limits. Never disable a needed bus clamp merely because the resistor is hot; follow FW-BRAKE-06/07/08 and request system-level energy reduction.

**FW-LED-01:** PC15 now drives D301 through its cathode; low turns it on. Preload high/off, use low-speed open-drain mode, and leave the LSE oscillator/competing backup-domain pin functions disabled. R304 = 2.2 kΩ bounds LED current below approximately 1.65 mA at 3.6 V even for a shorted LED; include PC14's pull-up current in the PC13–PC15 shared 3 mA sink budget. These pins must not source LED current. PC2 must never run the previous status-LED code.

**FW-TIME-01:** Begin with PROVISIONAL 20 kHz center-aligned PWM/FOC and 500 ns programmed deadtime; confirm the actual timer clock, nonlinear deadtime encoding, polarity and measured gate waveforms. At 20 kHz the FOC period is 50 µs. Establish worst-case execution time with margin and detect missed deadlines. SPI angle reads at approximately 5 MHz require about 6.4 µs for two 16-bit frames plus required gaps/overhead; do not budget zero latency. Keep flash operations, printf, packet parsing and blocking sensor retries outside this path.

**FW-TIME-02:** Use an independent watchdog and bounded bus/DMA timeouts. Feed the watchdog only after required control/safety tasks demonstrate progress, not unconditionally in an interrupt. Specify timeout values and worst-case detection-to-gate-off measurements in the release configuration. Debug halt is hazardous: only halt live firmware with motor power safely limited/removed; timer/watchdog freeze settings are not a complete safety strategy.

**FW-COMMS-01:** CAN and UART share validated commands and configuration semantics. Enforce finite values, ranges, units, command ownership, sequence/freshness and an explicit command timeout. Reject malformed/oversized packets without disturbing real-time control. No boot packet, reconnect, stale queue or restored NVM may arm the motor. Keep CAN TX recessive before releasing standby. Report board/firmware ID, active limits, reset/fault reason, VM, currents, temperatures, angle age/errors and estimated brake duty/energy.

**FW-COMMS-02:** CAN termination is manually configured in this revision. R802 (120 Ω) is fitted on every board; JP801 is an open solder jumper, closed only on boards at the two physical bus ends. Firmware cannot change or directly detect its state; record it as installation configuration. All four TMUX1574 channels currently have assigned functions. Any future software-controlled termination requires a separately reviewed circuit and reset/fault policy. The 3.3 V-powered TCAN3413 interoperates with 5 V-powered high-speed CAN transceivers; this is not a selectable bus-supply setting.

## 8. Implementation and acceptance gates

The firmware agent MUST supply a requirements-to-test checklist using these IDs. Passing compilation or simulator tests does not qualify the assembled power stage.

1. **Static configuration:** exact target/clock/AF map; no peripheral clashes; linker-reserved flash; reviewed PWM polarity, reset levels, break routing, external-supply driver registers and fault state machine.
2. **Host/unit tests:** angle wrap/parity/error handling; CRC/journal power-interruption recovery; range/NaN rejection; current units/scaling; NTC endpoints; battery-profile selection; brake saturation/energy accounting; fault/arming transitions and communication timeouts.
3. **Control power only:** SWD provisioning/readback; flash boot with feedback high/low; erased/corrupt configuration; USB-only inhibition; simulated VM disappearance/return; no output pulses during reset or watchdog recovery.
4. **Low-energy hardware tests:** measure rails and ADC calibration; prove each hardware break without an ISR; check comparator thresholds, driver faults, deadtime, bootstrap refresh and low-side sample windows. Inject faults with safe low-energy stimuli rather than high-energy intentional shorts.
5. **Brake tests:** qualified external resistor installed; measured software and hardware thresholds, including MCU held reset; inspect bus and gate peaks, resistor energy and cooling. Simulate a non-absorbing source or controlled disconnect. Demonstrate continued bus control during an inverter fault where possible.
6. **Motor tests:** unloaded 1–2 A initial operation; current/angle sign and electrical zero; bounded calibration; encoder disconnect/stale replies, Hall faults, I²C stuck bus, CAN timeout and thermal sensor faults. Verify that IMU recovery cannot stall FOC.
7. **Release envelope:** record cooling, ambient, motor/load inertia, voltage range, allowable regeneration, current limits, PWM range, response latency and thermal limits. Increase toward 25 A RMS only after measurements support it. Repeat persistence/update tests with interruption at every write/erase/commit stage.

### Parameters that must be resolved before normal arming

- Validated phase peak/RMS and battery charge/discharge limits, comparator/DAC thresholds and VDS settings.
- Battery-specific UV/OV and brake thresholds, tolerance margins and energy-sink configuration.
- Thermal derate/trip limits; resistor continuous/pulse energy and cooling model.
- FOC/angle/VM fault-detection deadlines, watchdog and command timeout, measured brake response budget.
- PWM/deadtime/modulation limits and valid ADC sampling windows.
- Approved option-byte manifest, BOR/PVD settings, flash partition and update/recovery procedure.

A restricted, explicitly entered commissioning build may use documented low-energy provisional limits to measure these values. It must not present itself as a qualified 25 A operating profile.

## 9. Evidence and precedence

- [Current sensor interface revision and exact connectivity checks](../Manual_Rebuild/review/sensor_interface_revision/README.md).
- [Half-bridge and current-amplifier decisions](../Manual_Rebuild/review/bridge_current_parts/README.md).
- [Brake topology, values and resistor limitations](../Manual_Rebuild/review/brake_parts/README.md).
- [External-supply power revision](../Manual_Rebuild/review/cascaded_power/REVIEW.md).
- [MCU review](../Manual_Rebuild/review/MCU_PIN_REVIEW.md): analog/internal resource evidence; shared-SPI/BOOT-button portions are superseded.
- [STSPIN32G4 datasheet](https://www.st.com/resource/en/datasheet/stspin32g4.pdf): external supplies, internal connections, protected driver registers and memory.
- [STM32G4 reference manual RM0440](https://www.st.com/resource/en/reference_manual/rm0440-stm32g4-series-advanced-armbased-32bit-mcus-stmicroelectronics.pdf): firmware agent must verify exact register routing, flash geometry and option-byte procedures for STM32G431. The full manual was not re-audited in creating this document.

Current native schematic and explicit later user-approved changes take precedence over historical design notes. If they disagree with this contract, report and reconcile the discrepancy before enabling torque.
