# ShiroFOC schematic design presentation plan

## Scope and deliverable

This Markdown skeleton is the specification for a later PowerPoint. It does not create the PowerPoint yet.

**Subject:** ShiroFOC, using the current A1-Drawing schematic with the A0 electrical design, dated 16 September 2026. Older stepper designs, archived schematics and temporary redraws are outside scope.

**Audience assumption:** an engineering design review audience familiar with basic electronics but needing an explanation of this motor drive. Plan for 36 main slides and 5 technical appendix slides, approximately 60–75 minutes with discussion. Slides 12–18 give the inverter and gate drive extra attention.

**Narrative:** requirements, power delivery, controller, switching stage, measurement and protection, feedback, communications, then commissioning.

Each module should explain its purpose, signal/current flow, topology choice, component values, tradeoffs, and validation needs. Present documented choices as documented choices. Label additional reasoning as engineering interpretation, calculations as calculations, and prototype starting values as provisional. Do not invent the original designer's motivation.

## Source hierarchy

1. [Current native KiCad project](../ShiroFOC_KiCad/ShiroFOC_KiCad.kicad_pro) and its schematic sheets define actual connectivity.
2. [Current schematic PDF](../ShiroFOC_KiCad/outputs/ShiroFOC_Rev_A_Schematic.pdf) supplies the presentation images.
3. [Released BOM](../ShiroFOC_KiCad/outputs/ShiroFOC_Rev_A_BOM.csv) defines fitted values, part numbers and DNP status.
4. [Electrical design review](../docs/DESIGN_REVIEW_REV_A.md), [calculation results](../ShiroFOC_KiCad/outputs/electrical_calculations.json), [design constraints](../docs/DESIGN_CONSTRAINTS.md), and [firmware contract](../docs/FIRMWARE_BRINGUP_CONTRACT.md) supply the recorded rationale and limits.
5. [Layout handoff](../docs/PCB_LAYOUT_HANDOFF.md), [layout guidelines](../docs/PCB_LAYOUT_GUIDELINES.md), and [pin allocation](../docs/MCU_PINOUT_AND_INTERFACE_PLAN.md) supply implementation context.
6. Manufacturer datasheets supply component limits and application guidance. Cite the exact revision, section, page and test conditions in the eventual speaker notes.

Current sources take precedence over historical proposals. Component values alone do not prove that a design meets its target ratings.

### Schematic image map

Use native KiCad exports or crops of the released PDF. Keep component references, values, junctions and relevant net names readable. The following page numbers are one-based.

| Image ID | PDF page | Native sheet | Content |
|---|---:|---|---|
| IMG-01 | 1 | ShiroFOC_KiCad.kicad_sch | System overview |
| IMG-02 | 2 | 01_Battery_DC_Link.kicad_sch | Entry, bulk capacitors, damping, VM divider |
| IMG-03 | 3 | 02_Auxiliary_Power.kicad_sch | Battery buck, supply mux, LDO |
| IMG-04 | 4 | 03_Controller.kicad_sch | MCU, supplies, clock, reset, SWD |
| IMG-05 | 5 | 04_Gate_Driver.kicad_sch | Driver, VCC buck, SCREF |
| IMG-06 | 6 | 04_Inverter.kicad_sch | Three half-bridges, bootstrap caps, shunts |
| IMG-07 | 7 | 05_Current_Temperature.kicad_sch | Current amplifiers and NTC networks |
| IMG-08 | 8 | 05_Brake_Chopper.kicad_sch | Brake switch, driver, hardware comparator |
| IMG-09 | 9 | 06_SPI_Sensors.kicad_sch | Encoder and IMU |
| IMG-10 | 10 | 08_Feedback_Selection.kicad_sch | External feedback and VM isolation |
| IMG-11 | 11 | 08_CAN.kicad_sch | CAN transceiver and bus connections |
| IMG-12 | 12 | 09_USB_Service.kicad_sch | USB-C, ESD, UART bridge |

Each slide below specifies its crop. Repeated modules should use one readable representative circuit, with a reference mapping for the other phases. Reusing a circuit crop for a different electrical explanation is intentional. Do not generate or redraw schematic evidence with AI. Full sheets belong in the supporting material, not as unreadable backgrounds.

## Main slide skeleton

### 01. ShiroFOC hardware design

- **Purpose:** introduce the single-axis FOC servo module and the scope of the review.
- **Image:** IMG-01 overview, large enough to identify the module groups.
- **Content:** STSPIN32G4 controller, external three-phase bridge, local sensing and protection, CAN coordination.
- **Visible qualification:** schematic prepared for prototype PCB layout. Current, thermal and power ratings remain targets.

### 02. Electrical requirements and operating envelope

- **Image:** IMG-02 power-entry crop beside a compact requirements table.
- **Content:** 6S–10S packs, approximately 18–42 V operation, preferred 8S design point, 20 kHz initial PWM.
- **Targets:** 25 Arms passive cooling, 40 Arms with a defined thermal solution, 80 A peak for at most 2 s subject to qualification.
- **Decision:** 60 V bridge parts require controlled overshoot and regeneration. A 63 V capacitor rating does not increase the permitted bus voltage.
- **Open issue:** the initial +60 A comparator setting limits use of the 80 A peak goal. Explain the distinction between an architectural goal and the initial commissioned limit.

### 03. System architecture and FOC signal flow

- **Image:** IMG-01 with power, control and measurement paths highlighted.
- **Content:** current, velocity and position loops run locally. CAN supplies commands and telemetry. PWM drives the bridge, while shunts and position feedback close the loop.
- **Decision:** integrate MCU, gate drivers and analog resources in U301 to reduce external circuitry, while external MOSFETs allow power-stage selection.
- **Notes:** give a brief FOC explanation without turning this into a motor-control mathematics lecture.

### 04. Power domains and operating modes

- **Images:** IMG-03 supply-chain crop and IMG-05 VCC crop.
- **Content:** VM supplies the inverter, brake and converters. Battery 5 V and USB 5 V feed the mux. 5V_SYS supplies the 3.3 V LDO. VCC supplies gate drive independently.
- **Decision:** USB supports service without energizing the motor power stage. Reverse-current blocking permits both sources to be attached.
- **Table:** battery only, USB only, both present, and VM returning while USB keeps the MCU alive.

### 05. Battery entry and DC-link capacitance

- **Image:** IMG-02, J101 and C101–C106.
- **Values:** three 680 µF / 63 V electrolytics, plus 4.7 µF, 100 nF and 10 nF input bypass capacitors.
- **Calculation:** bulk capacitance is 2040 µF. `E = ½CV² ≈ 1.80 J` at 42 V.
- **Decision:** bulk capacitors buffer bus energy, while lower-inductance ceramics support fast current changes. Explain ESR, ESL, bias derating and physical placement.
- **Validation:** the bulk bank's summed nameplate ripple rating is 5.07 Arms at 100 kHz, not a demonstrated motor-current rating. Determine actual ripple and temperature under PWM before claiming 25/40 Arms operation.

### 06. Inrush, discharge and optional input damping

- **Image:** IMG-02, R101 and the D101/R102/C107 branches.
- **Values:** 470 kΩ / 0.25 W bleeder. TVS and series RC damping positions are DNP and have no qualified fitted values.
- **Calculation:** bleeder power is approximately 3.75 mW at 42 V. Bulk-only `RC ≈ 959 s`, so this is a slow bleed path. Other attached loads change actual discharge time.
- **Decision:** preserve a bidirectional regeneration path. Rev A has no onboard reverse-polarity protection or active precharge.
- **Validation:** cable inductance, hot-plug overshoot and capacitor charging determine external precharge and damping requirements. Separate transient TVS duty from sustained brake energy.

### 07. Bus-voltage divider and ADC isolation

- **Images:** IMG-02 R103–R106/C108 and IMG-10 U602 channel 4, shown together with matching net labels.
- **Values:** 270 kΩ + 270 kΩ upper leg, 27 kΩ lower leg, 1 kΩ series resistor, 10 nF filter after isolation.
- **Calculation:** `VADC = VM/21`, giving 2.00 V at 42 V. `τ ≈ [(540 kΩ || 27 kΩ) + 1 kΩ] × 10 nF = 267 µs`, neglecting small mux resistance.
- **Decision:** split high-side resistance for voltage stress, retain ADC headroom, and isolate live VM sensing from an unpowered MCU.
- **Constraint:** wait at least 2 ms after mux enable. VM sensing becomes invalid when the feedback mux is disabled. The 60 V divider calculation is only a headroom check.

### 08. Battery-to-5 V buck converter

- **Image:** IMG-03 U201, L201 and its complete feedback/decoupling network.
- **Values:** LMR36510F, 22 µH / 2.75 A inductor, 100 kΩ / 24.9 kΩ feedback, two 22 µF output capacitors, 100 nF bootstrap capacitor.
- **Calculation:** `VOUT = VFB × (1 + 100/24.9) ≈ 5.016 V` using the applicable feedback reference. Plan an inductor ripple calculation over the intended VM range using the exact switching frequency.
- **Decision:** a wide-input buck reduces loss compared with dropping VM directly through a linear regulator. Explain the forced-PWM variant and its light-load tradeoff.
- **Validation:** saturation and RMS current, effective output capacitance, startup, load steps and feedback layout. Distinguish this converter's bootstrap capacitor from the inverter bootstrap capacitors.

### 09. USB-priority power mux

- **Image:** IMG-03 U203 with R206–R215 and C209–C211.
- **Values:** priority dividers 15 kΩ/5.10 kΩ and 10 kΩ/5.10 kΩ. OV dividers 21 kΩ/5.10 kΩ. ILM resistor 80.6 kΩ. Soft-start capacitor C209 is 100 nF.
- **Calculation:** at 5 V, PR1 is approximately 1.269 V and CP2 approximately 1.689 V. Explain why that selects USB in the configured mode. Recorded OV threshold is approximately 5.43 V and current limit approximately 1.5 A.
- **Decision:** source selection and backfeed prevention without directly connecting two supplies.
- **Validation:** confirm tolerance ranges and soft-start timing from TPS2121 equations. The mux current limit does not grant permission to draw that current from USB.

### 10. 3.3 V LDO and control-power budget

- **Image:** IMG-03 U204 and C212/C213.
- **Values:** TLV75533P, 2.2 µF input and output capacitors, thermally enhanced DYD package.
- **Calculation:** budget 250 mA normally and 320 mA with the stated CAN-fault allowance. `P = (5.25 − 3.3) × I`, giving 0.488 W and 0.624 W.
- **Decision:** discuss simplicity and analog supply quality versus efficiency and thermal loss. External 3.3 V also supports USB-only operation and bypasses the STSPIN internal regulator.
- **Validation:** effective capacitance, dropout, thermal-pad connection and enclosed-board temperature. External feedback has a 25 mA allowance.

### 11. MCU, clock, reset and SWD

- **Image:** IMG-04, cropped into clock/reset/debug and analog-supply views.
- **Values:** U301 STSPIN32G4, 24 MHz / 7 pF crystal, two 10 pF C0G load capacitors, local 100 nF and bulk supply decoupling.
- **Calculation:** `CL ≈ C1C2/(C1+C2) + Cstray`. Two 10 pF capacitors imply approximately 2 pF stray capacitance for a 7 pF load target, to be checked on the board.
- **Decision:** clock accuracy for communications/control, deterministic reset states and separate analog supply routing. Explain pulls, reset filtering, status LED current and decoupling in notes.
- **Constraints:** SWD VTREF is sense-only. PB3 serves SPI rather than SWO. PB8 shares BOOT0, so feedback isolation/default pulls matter and no test stub is provided there.

### 12. Gate-driver supply and 10 V selection

- **Image:** IMG-05, U301 driver unit and L301/D302/C311–C313.
- **Values:** 22 µH inductor, 10 µF / 25 V VCC reservoir, 100 nF local bypass. VCC starts at 8 V and firmware selects 10 V.
- **Decision:** compare MOSFET enhancement, conduction loss, gate-drive loss and voltage stress. The recorded 22 µH choice substitutes for ST's typical 18 µH example and needs validation.
- **Calculation:** using a conservative 56 nC per MOSFET, `6Qg fPWM = 6.72 mA` at 20 kHz. At 10 V, gate-charge power is approximately 67 mW, excluding driver quiescent consumption and other VCC loads.
- **Validation:** regulation, ripple, startup and brake-driver demand. Reapply the VCC setting after VM returns.

### 13. Three-phase inverter topology

- **Image:** IMG-06 showing all three phases, followed by one enlarged representative leg.
- **Parts:** Q401–Q403 CSD88599Q5DC dual MOSFET power blocks, one per phase.
- **Explanation:** high-side and low-side conduction, freewheeling, motor phase outputs and low-side shunt placement. Explain why both devices must never conduct together.
- **Decision:** compact paired MOSFET packages versus six discrete packages or parallel power blocks. Use total loss, transient margin and thermal paths as selection criteria.
- **Notes:** 60 V rating is an absolute limit. Datasheet loss plots have specific driver, capacitor and operating conditions and cannot directly establish this board's current rating.

### 14. Bootstrap operation and capacitor value

- **Image:** IMG-06 phase U, tightly framed around C411, Q401 and BOOT1/OUT1, with an IMG-05 driver inset.
- **Values:** C411/C421/C431 are each 100 nF / 25 V. Bootstrap voltage is measured between BOOTx and OUTx.
- **Explanation:** charging while the switch node is low, then supplying the floating high-side driver while the phase rises. The driver includes bootstrap diodes.
- **Calculation:** `Ceff ≥ [Qg + (IHB + Ileak + VGS/RGS)tON + Qother] / ΔVallow`. Start with `56 nC / 100 nF = 0.56 V` gate-charge-only droop. The 100 kΩ gate-source pull-down also draws about 100 µA at 10 V.
- **Decision:** 100 nF is the fitted starting value. Larger capacitance reduces droop but increases charging demand. Use effective capacitance after tolerance, temperature and DC bias, not only the printed value.
- **Validation:** define allowed droop from initial bootstrap voltage, UVLO margin and required MOSFET enhancement. Include diode drop, leakage and high-side dwell time. Do not present 0.56 V alone as proof of adequacy.

### 15. Bootstrap refresh and PWM limits

- **Image:** same bootstrap circuit at a different crop, with an explicitly illustrative timing chart.
- **Explanation:** startup precharge, periodic low-side refresh and why static 100% high-side duty is unsupported.
- **Calculation:** determine recharge time from the integrated diode resistance/current characteristic, capacitor value and required restored voltage. Compare it with available low-side time at 20 kHz and maximum modulation.
- **Decision:** balance bootstrap refresh, current-sampling windows and voltage utilization. Increasing capacitance alone does not solve limited recharge time.
- **Validation:** scope BOOT–OUT and VGS at startup, highest duty and VM interruptions. Establish a measured modulation limit before increasing performance.

### 16. High-side and low-side gate resistor choices

- **Image:** IMG-06 phase U, R411/R412 and R413/R414.
- **Values:** high-side R411/R421/R431 = 4.7 Ω. Low-side R412/R422/R432 = 0 Ω. Gate-source pull-downs = 100 kΩ.
- **Documented basis:** TI's CSD88599Q5DC application guidance recommends 4.7–10 Ω at GH and a direct GL connection to reduce parasitic capacitive turn-on. This supports the fitted starting values, subject to the actual STSPIN driver and PCB.
- **Calculation:** estimate Miller-region gate current using total driver, external and internal gate resistance, then `tMiller ≈ Qgd/Ig`. A 0 Ω external resistor still has driver impedance, internal gate resistance and layout inductance.
- **Tradeoff:** larger GH resistance slows transitions and can reduce ringing, at the cost of switching loss. A strong low-side pull-down helps resist Miller-induced turn-on. The 100 kΩ resistors establish defaults but do not replace active gate sinking.
- **Validation:** sweep resistor values using measured VGS, VDS, switching energy and temperatures. This design has separate resistors for the two MOSFETs, not separate turn-on/turn-off diode paths.

### 17. Deadtime, interlocking and switching losses

- **Images:** IMG-05 driver outputs and IMG-06 representative gate loop.
- **Values:** initial center-aligned PWM at 20 kHz, initial programmed MCU deadtime of 500 ns.
- **Explanation:** distinguish MCU deadtime, driver interlocking and device propagation/switching delays.
- **Calculation:** use `Pcond ≈ Irms² RDS(on,T)` with conduction duty accounted for, and an explicitly approximate `Psw ≈ ½VDS ID(tr+tf)fsw`. Add diode/recovery and output-capacitance losses where relevant.
- **Decision:** avoid overlap while limiting body-diode conduction and current distortion. Present 30 kHz only as a possible later setting with a loss penalty to quantify.
- **Validation:** compare gate waveforms at temperature and load. Treat 500 ns as a commissioning starting point rather than an optimized answer.

### 18. Local bridge capacitors, ringing and snubbers

- **Image:** IMG-06 phase U, C412/C415 and R415/C413, retaining the shunt and return wiring.
- **Values:** 1 µF / 100 V ceramic returns to GND. 10 nF / 100 V returns to the MOSFET source above the shunt. Phase RC snubbers remain DNP.
- **Decision:** explain high-frequency loop inductance and why these two capacitor return locations differ. Gate-edge control and RC damping address related but different mechanisms.
- **Calculation:** plan ringing-frequency measurements and an added-capacitance test to estimate parasitics, then choose damping resistance and check `Psnub ≈ Csnub V² fsw` as an initial estimate.
- **Source discrepancy to address:** TI's local SLPS597D datasheet calls for switch-node RC snubbers for 42–54 V input operation, while this release leaves them DNP for tuning. Reconcile that guidance with maximum-pack and regenerative excursions before claiming operation in that region.
- **Validation:** characterize overshoot with the final layout. The project commissioning target is measured VDS peaks below 55 V, subject to the full operating envelope.

### 19. Three-shunt current sensing

- **Image:** IMG-06 R416/R426/R436 with force and Kelvin paths highlighted.
- **Values:** three 0.5 mΩ four-terminal shunts.
- **Calculation:** 40 A produces 20 mV and 0.8 W. 80 A produces 40 mV and 3.2 W instantaneous dissipation.
- **Decision:** compare signal amplitude and resolution against loss, temperature rise and pulse capability. Explain why four-terminal sensing avoids including high-current copper drops.
- **Constraint:** three physical shunts do not guarantee three simultaneous valid samples. Low-side conduction windows and ADC scheduling still govern reconstruction.

### 20. Current-amplifier gain, bias and tolerance

- **Image:** IMG-07 phase U, including U301D and the complete resistor feedback/bias network.
- **Values:** R417/R418 = 1 kΩ, R419 = 28 kΩ, R410/R441 = 56 kΩ, all 0.1%. Other phases match.
- **Calculation:** `VOUT = VREF/2 + 28(VSENSE+ − VSENSE−)`. At 3.3 V reference, −80/0/+80 A gives 0.53/1.65/2.77 V.
- **Decision:** midpoint bias measures both current polarities, while gain uses ADC range with headroom. Show how the two 56 kΩ resistors create a 28 kΩ Thevenin source at VREF/2.
- **Validation:** resistor-only zero offset is recorded as 1.6436–1.6564 V. Add amplifier offset, finite bandwidth, ADC errors and drift. The optional 47 pF feedback capacitor is DNP, so do not describe it as a fitted filter.

### 21. Current sampling and hardware overcurrent shutdown

- **Image:** IMG-07 op-amp positive-input node, with the relevant controller pin map.
- **Explanation:** COMP1/2/4 monitor the biased op-amp input nodes, not the amplified ADC outputs. ADC1 sharing also prevents assuming simultaneous sampling of every phase.
- **Calculation:** with the negative Kelvin terminal near analog ground, `VCOMP = (56 × 0.0005I + 3.3)/58`. At +60 A, approximately 85.86 mV or DAC code 107 on a 12-bit 3.3 V scale.
- **Decision:** timer-break shutdown avoids waiting for a CPU interrupt after firmware configures the path. Reset instead keeps PWM inactive.
- **Limitations:** one-sided detection, offset-sensitive threshold, no guaranteed symmetric ±60 A limit, and no automatic entitlement to the 80 A peak target. Include blanking, settling and calibration in the timing budget.

### 22. VDS fault detection and SCREF

- **Image:** IMG-05 R310–R312/C314 and the SCREF pin.
- **Values:** 100 kΩ/10 kΩ divider, 1 kΩ series resistor, 10 nF capacitor.
- **Calculation:** nominal reference `3.3 × 10/(100+10) = 0.30 V`. Include divider impedance when discussing the filter time constant.
- **Decision:** use VDS monitoring as an additional short-circuit mechanism alongside shunt-based protection.
- **Constraint:** RDS(on) changes with temperature and gate voltage. SCREF does not establish a precise phase-current limit. Driver deglitch timing and startup behavior require explicit configuration and testing.

### 23. Phase temperature measurement

- **Image:** IMG-07 one NTC branch, with a small mapping to phases U/V/W.
- **Values:** TH701–TH703 = 10 kΩ NTC, B3380. R701–R703 = 4.7 kΩ pull-ups. Each ADC branch has 1 kΩ and 10 nF.
- **Calculation:** show `R(T) = R25 exp[B(1/T − 1/T25)]` and `VADC = 3.3RNTC/(4.7 kΩ + RNTC)`. Use kelvin in the temperature equation and plot the intended working range.
- **Decision:** three local sensors expose uneven phase heating. Explain the 4.7 kΩ choice through useful sensitivity in the intended temperature range and self-heating checks.
- **Validation:** open reads high, short reads low. Use the hottest valid channel, characterize sensor lag and distinguish measured PCB temperature from MOSFET junction temperature.

### 24. Brake-chopper topology and gate drive

- **Image:** IMG-08 U501, Q501, J501 and D501/D504.
- **Values:** CSD19531Q5A 100 V MOSFET, UCC27517A driver, 4.7 Ω gate resistor, 10 kΩ gate pull-down, 12 V gate clamp, 1 µF + 100 nF local driver bypass.
- **Explanation:** VM feeds the external resistor, which returns through the low-side switch. A dedicated VCC-powered driver drives the gate.
- **Decision:** provide local energy dumping when the supply cannot absorb regeneration. Give the brake MOSFET more voltage margin than the phase bridge.
- **Validation:** pulse SOA, switching loss and gate-clamp behavior. The 100 V / 5 A D504 handles brake-lead inductance, not sustained motor energy.

### 25. Brake resistor power and energy sizing

- **Image:** IMG-08 J501 power path beside a worked example table.
- **Example:** 10 Ω external resistor, 48 V calculation point, inertia 0.01 kg·m² and initial speed 2000 rpm.
- **Calculation:** `I = V/R = 4.8 A`, `P = V²/R = 230.4 W`, and `E = ½Jω² ≈ 219 J` for stopping to rest.
- **Decision:** the recorded example calls for at least 250 W on its specified heatsink and independently qualified 500 J over 5 s pulse capability. Continuous wattage alone cannot establish pulse suitability.
- **Limits:** account for repetition rate, gravity, driven loads and cooldown. An absent/open resistor removes braking, and the circuit does not automatically detect that condition. This example does not authorize sustained 48 V operation.

### 26. Independent overvoltage brake command

- **Image:** IMG-08 U502, R506–R510, C504 and D502/D503.
- **Values:** TLV3012B, three 150 kΩ upper resistors, 12.7 kΩ lower resistor, 1 MΩ positive feedback and 1 nF filtering.
- **Calculation:** derive the comparator-node equation including output feedback. Recorded nominal thresholds are 45.92 V rising and 44.21 V falling. Show the corner ranges of 44.19–47.51 V rising and 42.58–45.96 V falling.
- **Decision:** positive feedback creates hysteresis. Diode OR permits firmware or hardware to command the driver. Normal firmware braking starts earlier, with 43 V as the initial 10S setting.
- **Constraint:** hardware braking needs both 3V3 and VCC. Threshold tolerance calculations omit dynamic overshoot and are not a transient qualification.

### 27. Onboard magnetic encoder

- **Image:** IMG-09 U601, local capacitors, SPI connections and ABI outputs.
- **Values:** AS5047P, 100 nF and 1 µF local capacitors, 33 Ω ABI series resistors and 33 Ω sensor MISO resistor.
- **Decision:** combine absolute SPI position with timer-compatible incremental outputs. Explain pin use and mechanical alignment with the shaft magnet.
- **Value rationale:** decoupling supports local supply transients, while series resistors provide a signal-integrity starting point. Confirm timing against actual trace loading rather than assigning an arbitrary cutoff frequency.
- **Validation:** magnet alignment, angle offset, error handling, velocity range and reset chip-select state.

### 28. IMU and shared SPI bus

- **Image:** IMG-09 U701 and shared SPI wiring, with both chip selects visible.
- **Values:** BMI323, local 100 nF supply bypassing, 33 Ω MISO resistor. MCU-side SCK/MOSI series resistors are 22 Ω.
- **Decision:** a shared bus saves pins while separate chip selects isolate transactions. IMU telemetry supports system motion sensing and does not replace shaft position feedback.
- **Firmware constraint:** encoder uses SPI mode 1, BMI323 mode 0 or 3. Switch modes only with both devices deselected.
- **Validation:** axis orientation, interrupt use, mechanical vibration, temperature exposure, bus timing and inactive-device MISO behavior.

### 29. External feedback selection and protection

- **Image:** IMG-10 J601, D601, U602 and default pulls.
- **Values:** TMUX1574, 100 Ω external signal series resistors, optional 10 kΩ Hall pull-ups, isolated ESD rail with 100 nF, 0 Ω supply link with a 25 mA load allowance.
- **Decision:** select onboard ABI or external encoder/Hall signals onto shared timer inputs. Preserve reset isolation for PB8/BOOT0 and powered-off isolation.
- **Constraints:** inputs are 0–3.3 V, including while the board is off. The mux is not a level translator. The 0 Ω link is not a current limiter, and sensor power is not switched by the signal mux.
- **Validation:** change source at zero torque, handle open-drain versus push-pull outputs, then settle and revalidate VM because channel 4 shares enable control.

### 30. CAN physical interface

- **Image:** IMG-11 U801, D801, termination and J801/J802.
- **Values:** TCAN3413, 100 nF + 1 µF bypass, 10 kΩ TX/STB pulls, optional 120 Ω end termination with JP801, fitted 0 Ω bus links.
- **Decision:** differential daisy-chain communication for distributed motor modules. Pulls keep the transceiver in standby and TX recessive through reset.
- **Explanation:** terminate only the physical bus ends. Connector pin 4 carries shield/drain, not supply power. Explain the unisolated grounding arrangement.
- **Validation:** cable topology, bitrate/timing budget, ESD placement, power-off behavior and fault current. Hardware capability alone does not establish a validated bus rate.

### 31. USB-C service and UART bridge

- **Image:** IMG-12, connector/protection and CP2102N power/UART groups.
- **Values:** 5.1 kΩ CC resistors, USBLC6 protection, CP2102N, 100 Ω UART series resistors, 22.1 kΩ/47.5 kΩ VBUS sense divider, local 4.7 µF + 100 nF supply bypass pairs.
- **Decision:** provide service UART while CAN remains the primary interface. VDD and VREGIN both use external 3V3 in regulator-bypass mode.
- **Explanation:** distinguish VBUS detection from bridge power, and label UART directions from the MCU perspective. Explain fitted shield link and DNP shield capacitor.
- **Constraint:** USB-only source must permit at least 500 mA. No USB-PD negotiation or pre-enumeration/suspend load shedding is implemented. Reset and BOOT0 remain manual controls.

### 32. Reset states and fault response

- **Images:** selected pulls/default-state crops from IMG-04, IMG-08, IMG-10 and IMG-11.
- **Content:** fault-response table covering erased MCU, reset, USB-only service, VM loss/return, overcurrent, feedback loss, overtemperature and nonsinking supplies.
- **Distinction:** comparator/TIM1 shutdown needs prior configuration. Hardware brake backup can act during MCU reset if its supplies exist. DNP TVS/snubber positions provide no fitted protection.
- **Decision:** deliberate arming, latched faults and reinitialization prevent stale commands from restarting torque after power disturbances.

### 33. Layout requirements behind the schematic

- **Images:** IMG-06 gate/power/Kelvin loops and IMG-03 regulator thermal-pad crop.
- **Content:** compact commutation loops, correct capacitor returns, short bootstrap paths, separated Kelvin sense pairs and quiet analog routing.
- **Decision:** explain how parasitic inductance and thermal resistance can invalidate otherwise reasonable component values.
- **Package details:** CSD88599 live VIN thermal pad, correct Q501 package pad map, LDO ground thermal pad, inductor keepouts, sensor placement and brake connector separation.
- **Status:** use schematic evidence and layout requirements. Do not imply that a routed or thermally validated PCB already exists.

### 34. Startup and low-energy commissioning

- **Images:** crops showing existing supply, SCREF, current-output and brake test points.
- **Sequence:** inspect continuity, apply permitted control power, confirm supply selection and backfeed behavior, program via SWD, apply current-limited VM, calibrate sensing, configure and demonstrate protection, then begin unloaded low-current switching.
- **Initial conditions:** 18 V, 1–2 A command, 20 kHz and 500 ns deadtime from the firmware contract.
- **Evidence required:** measured waveforms and fault actions. Explain the safe progression to higher bus voltage and current rather than showing unmeasured efficiency or thermal results.

### 35. Component choices requiring prototype measurements

- **Image:** annotated IMG-06 crop identifying gate resistors, bootstrap caps and DNP snubbers.
- **Table columns:** choice, present value, governing tradeoff, required measurement, reason to change it.
- **Rows:** 100 nF bootstrap, 4.7 Ω/0 Ω gates, phase snubbers, input damping/TVS, 22 µH VCC inductor, current comparator threshold, capacitor bank and brake resistor.
- **Purpose:** make clear which values follow documented calculations and which remain initial selections. Tie each measurement to a decision rather than promising the current BOM will meet every target.

### 36. Design conclusions and remaining decisions

- **Image:** IMG-01 or a readable selection of the discussed module crops.
- **Content:** summarize the architecture's principal choices and the relationship between electrical design, firmware, layout and physical validation.
- **Open decisions:** operating-current envelope, switching margin at maximum pack voltage and regeneration, snubber population, thermal solution, brake-energy envelope and final firmware protection settings.
- **Closing evidence:** a schematic and ERC result support connectivity review. Waveform, thermal and fault testing establish the usable hardware envelope.

## Technical appendix skeleton

### A1. Bootstrap and gate-drive worksheet

- Include Qg/Qgd source conditions, driver source/sink behavior, high-side supply current, leakage, pull-down current, UVLO limits, capacitor effective value, maximum on-time and recharge window.
- Show nominal and worst-case droop, startup charge time, and measured resistor-sweep results when available.
- Keep unavailable inputs visibly marked as pending. Link to slides 12 and 14–17.

### A2. Power and analog calculation tables

- Consolidate buck ripple, mux thresholds, LDO power, VM divider/filter, shunt loss, amplifier transfer/error, comparator threshold and NTC conversion.
- For every result include units, assumptions, tolerance treatment, component references and source revision.
- Include common supporting passives omitted from main-slide detail: pull resistors, LED current limiting, reset RC, regulator bypass and status pins.

### A3. Brake threshold and energy worksheet

- Derive rising/falling thresholds from the actual feedback network, including output levels and reference/offset tolerances.
- Separate resistor peak watts, pulse joules, average duty, cooldown and lead-inductance clamp behavior.
- Explain the missing-supply and missing-resistor cases. Link to slides 24–26.

### A4. Component and schematic cross-reference

- Map each main slide to PDF page/crop, component references, fitted/DNP state and BOM entry.
- Include the U/V/W reference mappings and the 18 DNP positions with their purpose.
- Link the complete 12-page schematic PDF for readers who need whole-sheet context.

### A5. References and unresolved evidence

- List local design records and exact manufacturer datasheet revisions/pages used in the final presentation.
- Record that the electrical review cites STSPIN32G4 DS13630 Rev 2, while the currently served [ST datasheet](https://www.st.com/resource/en/datasheet/stspin32g4.pdf) is Rev 3, May 2026. Reconcile relevant changes before final calculations.
- Use the local [CSD88599Q5DC datasheet](../DataSheets/CSD88599Q5DC.pdf), SLPS597D, particularly its charge data and application sections, for the gate-resistor and ringing discussion. The [manufacturer datasheet URL](https://www.ti.com/lit/ds/symlink/csd88599q5dc.pdf) should accompany the local revision citation.
- Record outstanding measurements explicitly. Do not replace missing evidence with invented scope traces or simulated results presented as measurements.

## Instructions for the later PowerPoint build

1. Freeze the source revision and check that schematic PDF, native sheets and BOM agree before extracting images.
2. Export sharp schematic crops, preferably vector when supported. Keep annotation overlays separate from original circuit evidence.
3. Use a 16:9 technical presentation with one main circuit crop and a short explanation per slide. Keep detailed derivations, error budgets and source citations in speaker notes or appendices.
4. Retain the distinction between fitted values, nominal calculations, manufacturer guidance and measured results. Mark timing illustrations as illustrative.
5. Resolve datasheet revision differences and the snubber guidance discrepancy. Check bootstrap recharge and comparator assumptions before making adequacy claims.
6. Populate supporting worksheets and cite exact datasheet sections. Every component group should have a purpose and value-selection explanation, without repeating identical phase circuits three times.
7. Render and inspect every slide for schematic legibility, clipping and consistent units. Split overly dense content if needed while retaining this coverage.

## Coverage check

- [x] All 11 functional KiCad sheets and the system overview have assigned slides.
- [x] Bootstrap capacitance, recharge timing and gate resistors have dedicated explanations.
- [x] Power conversion, measurement, thermal sensing, braking, sensors and service interfaces include value-selection topics.
- [x] Each slide identifies its schematic image or crop.
- [x] Prototype assumptions, DNP parts, design targets and unresolved evidence remain visible.
- [x] PowerPoint creation remains the next stage, after this skeleton.
