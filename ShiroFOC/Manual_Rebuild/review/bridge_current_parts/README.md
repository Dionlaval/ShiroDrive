# Half-bridge and current-amplifier component selection

26 September 2026. Implemented in the **manual rebuild** schematic, pages 6 and 7. Target: **10S LiPo, 42 V full charge, provisional 25 A RMS phase current with cooling**. This is a design target, not a measured rating. For sinusoidal phase current, 25 A RMS corresponds to 35.4 A peak. Firmware current conventions must be explicit.

## Selected parts

| References | Selection | Footprint / model |
|---|---|---|
| U1–U3 | Retain TI **CSD88599Q5DC** | Existing downloaded `Manual:DMM0022A` and STEP retained. Known pin-number reconciliation remains; see below. |
| R1, R3, R5 | **BVR-Z-R0005-1.0**, 0.5 mΩ, 1%, four-terminal | Standard `Resistor_SMD:R_Shunt_Isabellenhuette_BVR4026`; **STEP download needed**. |
| R2, R4, R6 | **RC0805FR-074R7L**, 4.7 Ω, 1%, 0.125 W | Standard 0805 resistor footprint and existing generic STEP. |
| C1, C5, C9 | **C1005X7S2A103K050BB**, 10 nF, 100 V, X7S | Standard 0402 capacitor footprint and generic STEP. Replaces generic 100 nF values. |
| C2, C6, C10 | **C3216X7R2A105K160AA**, 1 µF, 100 V, X7R | Standard 1206 capacitor footprint and generic STEP. |
| C3, C7, C11 | **C3225X7S2A475K200AB**, 4.7 µF, 100 V, X7S | Standard 1210 capacitor footprint and generic STEP; exact part maximum height 2.2 mm. |
| C4, C8, C12 | **C1608X7R1H224K080AB**, 220 nF, 50 V, X7R | Standard 0603 capacitor footprint and generic STEP. Replaces `BOOTSTRAP1` value placeholders. |
| R417/R418, R427/R428, R437/R438 | **RT0603BRD071KL**, 1 kΩ, 0.1%, 25 ppm/°C | Standard 0603 resistor footprint and generic STEP. |
| R419, R429, R439 | **RT0603BRD0728KL**, 28 kΩ, 0.1%, 25 ppm/°C | Standard 0603 resistor footprint and generic STEP. |
| R410/R441, R420/R442, R430/R443 | **RT0603BRD0756KL**, 56 kΩ, 0.1%, 25 ppm/°C | Standard 0603 resistor footprint and generic STEP. |
| C414, C424, C434 | **C1608C0G1H470J080AA**, 47 pF, 50 V, C0G, 5% | Standard 0603 capacitor footprint and generic STEP. **Remain DNP.** |
| U4D–F | Existing internal STSPIN32G4 op amps | Share U4's downloaded footprint and model; no separate op-amp packages. |

MPNs, manufacturers, ratings, datasheet URLs and relevant assembly notes are stored as schematic properties. [Per-reference CSV](selected_parts.csv).

## Why these choices

- **Current sensing:** keep gain 28 and 0.5 mΩ, giving 14 mV/A. At 25 A instantaneous, the output is 2.00 V; at ±35.4 A (25 A RMS sinusoid peaks), approximately 1.155–2.145 V. The retained ±100 A nominal measurement capability provides headroom; it does not authorize 100 A operation. Approximately 58 mA per ideal 12-bit ADC count at 3.3 V, before offset/noise errors.
- **Shunt:** datasheet specifies 5 W at the stated hotter-terminal conditions (9 W at 70 °C), not 5 W on any arbitrary copper area. Even a continuously conducting 25 A RMS shunt dissipates only 0.3125 W. Low-side PWM conduction normally reduces average heating, but zero-speed torque and imbalance must also be considered. The standard footprint matches the manufacturer's 10.6 × 7.3 mm land extent, 5.5 mm inner gap, 0.9 mm sense lands and 0.8 mm separation. Pads 1/4 carry current; 2/3 are sense.
- **Gate resistors:** retain TI's recommended 4.7 Ω starting value on GH and direct GL drive. At Qg = 56 nC, Vgate = 10 V, 50 kHz, Qg·Vgate·f = 28 mW bounds the approximate average gate-charge energy per FET; only part is dissipated in the external resistor. Actual ringing and pulse stresses remain bench checks.
- **Bootstrap:** 220 nF gives Qg/C = 0.255 V nominal droop for 56 nC. At an effective 150 nF, gate-charge droop is 0.373 V; 250 µA driver current over 50 µs adds 0.083 V. These estimates exclude refresh-path drop and leakage. Precharge before PWM and preserve refresh intervals. A larger capacitor also charges more slowly through the STSPIN's internal bootstrap diode; do not assume indefinite 100% high-side duty is possible.
- **Local VM capacitors:** 100 V ratings give voltage margin above the 42 V battery. The 10 nF 0402 selection is specifically identified by TI for operation up to 42 V. The 1 µF and 4.7 µF banks and existing main bulk capacitors remain. Nominal µF is not effective µF at 42 V; PWM-loop impedance, DC bias and capacitor ripple heating still need validation with the final layout. No claim that this capacitor bank alone guarantees 25 A operation.
- **Amplifier resistors:** 0.1% thin-film parts retain the balanced differential network; matching reduces conversion of common voltage movement into a false current reading. 47 pF feedback caps remain optional because fitting them changes both settling and high-frequency common-mode rejection.

## Download list — no custom CAD required

**Required for complete 3D visualization:**

1. **BVR-Z-R0005-1.0**, quantity 3: download its **STEP model** from [Component Search Engine](https://componentsearchengine.com/part-view/BVR-Z-R0005-1.0/Isabellenh%C3%BCtte). A complete KiCad ZIP is fine; place it in `downloads/incoming/`. Its footprint is already assigned from the installed KiCad library. We only need the model and a placement/orientation check; no new symbol or footprint needs to be drawn.

No other new download is necessary for the selected bridge/amplifier passives. Installed standard models are **generic visualizations**, not exact vendor body-height certifications. Use the manufacturer dimensions for tight mechanical clearances, particularly the 1 µF and 4.7 µF capacitors.

## Preserved / outstanding

- **Existing MOSFET CAD blocker:** the downloaded symbol has literal pin ranges `[3-11]` and `[12-20]`; its footprint has individual pad numbers and additional pads including `V`. This must be reconciled before a PCB update. Downloading the same ZIP again will not fix the mismatch. No symbol, footprint or STEP geometry was created or changed in this task.
- **J1 motor termination:** still the user's generic three-pole symbol, with no selected physical connector. Decide a connector or direct solder-wire arrangement before PCB placement. A 25 A RMS phase rating needs an appropriately rated termination; do not substitute a small signal header.
- Temperature-divider parts on the lower half of page 7 are unchanged; this pass selected the current-amplifier network.
- No part-stock or fabricator validation was performed. PCB, other sheets and all library CAD files are unchanged. Cooling hardware and current limits remain part of layout/firmware validation.

## Checks

- 39 component records updated across two sheets.
- Native KiCad netlist: **identical electrical connectivity** before/after.
- Native ERC: **same 16 pre-existing findings**, no new findings and no exclusions added.
- Every selected footprint resolves. The only missing model in this selection is the shared BVR shunt model.
- DNP settings preserved; both rendered sheets inspected. Existing gain/bias was already checked with an ideal SPICE model; it is unchanged.
- Original two sheets saved in [before/](before/); [machine validation](validation.json).

## Manufacturer evidence

- [TI CSD88599Q5DC](https://www.ti.com/lit/ds/symlink/csd88599q5dc.pdf), gate charge, recommended bypass, gate-resistor guidance.
- [ST STSPIN32G4](https://www.st.com/resource/en/datasheet/stspin32g4.pdf), bootstrap current/diode and supply limits.
- [Isabellenhütte BVR](https://www.isabellenhuette.com/hubfs/143808517/files/Data%20sheets/BVR.pdf), pp. 1–2, exact ordering code, thermal conditions and lands.
- [TDK 10 nF](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1005X7S2A103K050BB), [1 µF](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C3216X7R2A105K160AA), [4.7 µF](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C3225X7S2A475K200AB), [220 nF](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1608X7R1H224K080AB), [47 pF](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1608C0G1H470J080AA).
- Exact YAGEO specification PDFs saved in `../../DataSheets/` (from the manual project root: `../DataSheets/`). BVR PDF also saved there. TDK website specifications were checked; direct PDF downloads were blocked, so their links are retained in the schematic.
