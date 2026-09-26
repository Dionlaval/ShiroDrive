# Schematic review before PCB layout

> **Update:** accepted changes are now implemented. See [implementation and current results](implementation/README.md). The findings below are the preserved pre-change review.

26 September 2026 · Manual rebuild · KiCad 9.0.4 · 12 pages · 253 physical components, 180 nets.

## Verdict

**The architecture is coherent, but this is not yet a clean schematic-to-PCB handoff.** One new electrical tolerance issue was found in the power mux. The existing bridge symbol/pad mismatch and unfinished mechanical assignments also need resolution. The fast hardware current-trip accuracy needs a deliberate acceptance decision; it is not a reason to automatically redesign the current amplifiers.

This pass made **no schematic, PCB or library changes**. It refreshed the [download checklist](../../downloads/FOOTPRINT_CAD_CHECKLIST.md) and [component catalogue](../../downloads/component_footprint_map.csv). Nothing here requires repeating the entire design. Preserve the accepted single-board architecture, external 10 V supply, bulk capacitors and supervised simplifications.

## Actions, in priority order

| ID | Priority | Finding / consequence | Recommended next action | Tradeoff |
|---|---|---|---|---|
| R1 | Must fix before PCB transfer | U1–U3 use literal pin ranges, while their footprint uses individual pad numbers. PCB transfer cannot map these correctly. | Repair symbol-to-pad associations against TI's drawing, retaining the downloaded geometry and 3D model. | Library work; no extra board space or electrical topology change. |
| R2 | Change before freezing power page | U203 can reject a healthy 5 V supply around 5.1 V because the overvoltage comparator and resistor tolerances were not fully allowed for. | Revise the overvoltage acceptance requirement and divider values. See choices below. | Raising threshold costs no area, but does not provide precise 5.5 V protection; precise protection needs extra circuitry. |
| R3 | Resolve before committing protection routing | The proposed internal fast current trip senses a small unamplified signal. Comparator/DAC errors can be large relative to a 25 A target. | Decide earliest/latest permissible fault-trip currents; determine whether calibrated coarse protection plus VDS backup is sufficient. | Keeping it saves area; tighter independent trip accuracy may require changed routing or circuitry. |
| R4 | Finish before placement | J1 motor termination, JP601 selector and U603 buffer lack footprint assignments; Y301 crystal package remains provisional. | Choose J1/JP601 mechanically, assign standard U603 package, obtain exact crystal specification. | Connector versus soldered cable and removable shunt versus solder selector are user-serviceability/profile choices. |
| R5 | Qualify before locking capacitor footprints | New converter caps still use generic values; their effective capacitance at operating voltage is not established. | Select exact C205/C206/C214/C215/C218/C219 parts against the existing capacitance requirements. | Could affect package area/height; no stock check is needed to establish electrical suitability. |
| R6 | Optional robustness | External sensor supply can directly short a shared control rail. | Consider current-limited sensor supply isolation if cable faults must leave control electronics running. | Extra component/area; ordinary intended Hall/ABI use already works without it. |
| R7 | Minor cleanup | TP201 still says `5V_BAT` although connected to ST; some sheet titles/notes refer to the previous regulator/BOOT button arrangement. | Rename testpoint and update stale text during the next authorized schematic edit. | No electrical change. |

**High-confidence findings:** R1/R2/R4/R7 use native netlist/raw-file evidence; R2 additionally uses manufacturer limits. **Engineering decisions:** R3/R5/R6 have concrete reasons but their acceptance depends on the intended operating/fault envelope. Do not present them as observed prototype failures.

## R1 — repair the dual-MOSFET mapping

U1/U2/U3 are CSD88599Q5DC; their existing `Manual:DMM0022A` footprint and STEP are present. The symbol contains literal `[3-11]` and `[12-20]` pin numbers. KiCad does not expand these into footprint pads 3 through 20.

The footprint also contains pad 21, pads 23–26, central VIN pad 27 and eleven plated holes numbered `V`. The eleven holes lie inside central pad 27 copper. They must be reconciled to the proper VIN/VM electrical function, not treated as ground thermal vias. The remaining auxiliary pads require reconciliation against the package drawing, not an assumption that every extra pad should be grounded.

This requires symbol/pad-number work, **not another download of the same package**. Preserve the user's bridge circuit and downloaded land geometry. Then export a PCB update fixture and check every physical power, gate and sense pad before synchronizing the actual board. Correct the unsuitable symbol pin types and library mismatches at the same time; use explicit bootstrap power declarations only after checking the internal charging paths.

Evidence: [full pad inventory](cad_inventory.json), [fresh netlist](netlist.xml), [TI CSD88599Q5DC datasheet and DMM drawing](https://www.ti.com/lit/ds/symlink/csd88599q5dc.pdf). The electrical pad-number mismatch is deterministic; the entire footprint geometry was not requalified here.

## R2 — power-mux overvoltage setting

Both inputs use 21.0 kΩ / 5.10 kΩ, 1%: R210/R211 and R212/R213. The typical result is 5.425 V, but typical is not a guaranteed cutoff.

TI specifies a rising reference of 1.01–1.10 V and input leakage up to ±0.1 µA. Including resistor tolerances:

| Setting | Minimum rising cutoff | Typical | Maximum rising cutoff |
|---|---:|---:|---:|
| Existing 21.0 kΩ / 5.10 kΩ | 5.084 V | 5.425 V | 5.723 V |
| Candidate 22.0 kΩ / 5.10 kΩ | 5.278 V | 5.633 V | 5.943 V |

A healthy upper-range 5 V source can therefore be rejected by the existing circuit. The previously calculated 5V_BAT upper static bound of 5.089 V also marginally overlaps the minimum trip.

**Suggested decision:** for the first board, a divider-only change is a reasonable compact option if these are trusted regulated 5 V sources and this mux function is treated as coarse rejection of bad supplies. It must not be described as guaranteed protection of the downstream LDO from every overvoltage. If accepting 5.25 V while always disconnecting below the LDO's 5.5 V recommended maximum is required, a more accurate detector/protector is necessary. The TPS2121 reference spread alone is wider than that window, even with perfect resistors. Its current existing setting also fails to guarantee a 5.5 V ceiling.

Do not simply install 22 kΩ and claim the overvoltage problem is universally solved: its upper threshold approaches the LDO's 6.0 V absolute maximum, which is a stress limit, not an operating target. No values were changed in this review.

Sources: [TPS2121, electrical characteristics and overvoltage section, pp. 8/18](https://www.ti.com/lit/ds/symlink/tps2121.pdf); [TLV755P ratings, p. 4](https://www.ti.com/lit/ds/symlink/tlv755p.pdf). Reproducible values: [calculate.py](calculate.py), [calculations.json](calculations.json).

## R3 — distinguish current measurement from fast fault protection

The current measurement circuit remains sensible:

- 0.5 mΩ shunt and gain 28 give **14 mV/A**, centered at 1.65 V.
- 25 A RMS sinusoidal phase current means ±35.4 A peak; outputs are approximately **1.155–2.145 V**.
- Nominal positive amplifier-input voltages stay around **39.8–74.0 mV** over that range. The circuit does not require negative amplifier inputs in normal intended operation.
- All three amplifiers can operate concurrently, but two ADCs require scheduled sampling in valid low-side conduction windows. This is already in the firmware requirements.

The proposed internal comparator paths see `OPP_U1/V1/W1`, approximately:

`V_OPP = 56.90 mV + 0.48276 mV/A × phase current`

Consequently comparator offset of 9 mV magnitude corresponds to **18.6 A**. An illustrative 60 A setting is 85.86 mV. Adding conservative comparator and DAC error magnitudes can put an illustrative threshold envelope around **33–87 A**, before other errors and switching disturbances. This is not an exact signed statistical distribution or a measured trip range. The lowest nonzero comparator hysteresis setting also has meaningful spread compared with this signal.

**Keep the amplifier/ADC circuit.** Decide whether a coarse, characterized emergency trip is acceptable; do not promise a precise 25 A hardware cutoff. STSPIN VDS/SCREF protection is an independent short-circuit backup, also not a precise current limiter. Current firmware requirements already leave the fast-trip validation open.

If tighter trip accuracy is desired, investigate a properly scaled comparator path before layout. The current pin assignments do not provide a simple symmetric internal comparator route from all three amplified outputs. Calibration is a possible mitigation, not proof that all transient faults are covered.

Sources: [STM32G431, tables 12/71/73](https://www.st.com/resource/en/datasheet/stm32g431cb.pdf), [ST comparator input definitions](https://raw.githubusercontent.com/STMicroelectronics/stm32g4xx-hal-driver/master/Inc/stm32g4xx_hal_comp.h), [existing firmware contract](../../../requirements/FIRMWARE_REQUIREMENTS.md). Full RM0440 retrieval was unsuccessful in this pass; complete comparator-to-break implementation remains a firmware/protection verification item.

## Page-by-page outcome

| Page / section | Outcome and remaining limits |
|---|---|
| 1 — overview/mechanics | Four M3 NPTH holes are present. Keep current rounded compact single-board plan and central back-side encoder. Actual outline/clearances belong to new PCB layout. |
| 2 — DC link | Three 680 µF / 63 V capacitors remain; ceramic bypass and 21:1 VM divider are coherent. At 42 V the ADC sees 2.00 V. Main bulk stores about 1.80 J. External fuse/precharge and DNP TVS/damping are deliberate choices, not omissions discovered here. |
| 3 — supplies | VM → approximately 10.009 V LMR36510 → approximately 4.979 V MPM3620A → mux → 3.3 V LDO. PG/EN divider and MPM internal VCC/BST/AGND usage match documentation. **Revise mux OV setting; qualify capacitor effective values.** |
| 4 — MCU/clock/SWD | Current dedicated SPI3/I2C2/timer map remains consistent. Retain SWD recovery, persistent BOOT0 option-byte provisioning, UCPD dead-battery disable and documented analog configuration. Exact crystal qualification remains open. |
| 5 — gate driver | External VCC, SW tied to VM and external 3V3 bypass agree with ST guidance. SCREF nominal 0.30 V. Firmware must configure driver supplies/faults and bootstrap refresh after startup and VM return. |
| 6 — bridge | Selected FET/shunt/gate/bootstrap/local cap scheme remains a plausible first 25 A RMS cooled prototype. **Fix library mapping.** Current rating and ringing remain layout/bench dependent. No automatic restoration of omitted GL resistors/gate pulldowns/snubber parts. |
| 7 — current/temperature | Gain/bias checks pass using the actual network. At 25°C, nominal 10 kΩ NTC divider gives 2.245 V. The complete loaded NTC filter corner is about 3.79 kHz, not the isolated 1 kΩ/10 nF value of 15.9 kHz. Review fast-trip precision separately above. |
| 8 — brake | Comparator polarity, positive feedback, diode OR, driver and MOSFET connections are coherent. Nominal 45.9 V on / 44.2 V off includes comparator hysteresis. TLV3012**B** fail-safe input matters during power sequencing. External 10 Ω resistor dissipates about 212 W at 46 V full-on; cooling/energy budget remains required, not arbitrary regeneration absorption. |
| 9 — encoder/IMU | AS5047P dedicated SPI3, 3.3 V strap, test pin grounding and CS pull-up are coherent. BMI323 uses I2C2, CSB high, SA0 low and paired 2.2 kΩ pull-ups; no SPI mode switching required. |
| 10 — Hall/ABI | 3.3 V SN74LVC3G17 accepts the intended 3–5 V inputs; pull-up/DNP and reset-isolation choices are coherent. TPD3E001 floating supply rail with capacitor is supported by TI. Assign U603/JP601; consider optional external-supply fault isolation. |
| 11 — CAN | 3.3 V TCAN3413 supports the intended CAN physical bus with 5 V transceiver nodes. R802 120 Ω is fitted; JP801 enables termination manually at the two bus ends. TX/standby pull-ups and ESD pin mapping are coherent. |
| 12 — USB | CP2102N remains on shared 3V3, VBUS sense divider and USB-C CC resistors are coherent. USB powers control electronics, not VM/motor. Previous 60–80 mA running budget and roughly 100 mA controlled-start estimate remain estimates, not measured peak or USB compliance proof. |

### Useful optional simplifications/robustness choices

- **JP601:** a solder selector reduces height versus a removable header, at the expense of convenient voltage changes. Choose before placement.
- **External sensor supply:** a cable short currently can collapse a control rail through JP601/R604. A protected supply switch contains that fault but costs area. No change is needed for the basic intended sensor connection.
- **Shields:** USB shell is floating with C207 DNP; CAN shield passes through the connectors without a chassis connection. Define the intended cable/enclosure shield connection during layout. This is an EMI design choice, not a demonstrated failure.
- Retain the existing bulk caps and accepted direct GL drive for now. No new argument here requires changing those decisions. Runtime ringing/thermal measurements remain necessary.

## Verification and evidence

### Native/ERC and analyzer agreement

- Fresh KiCad netlist and schematic analyzer both contain **253 components, 180 nets**. Component reference sets match exactly.
- **16 native ERC findings remain:** 7 errors for power-drive declarations; 9 warnings consisting of 4 symbol/library mismatches and 5 pin-type conflicts. They are the same baseline categories, concentrated around the retained bridge and bootstrap symbols. The bridge mapping problem is real and can survive ERC; remaining declaration/type warnings must be resolved explicitly rather than globally suppressed.
- U4 remains one physical 65-pad device with six functional symbol units.
- The two newer autosaves (MCU and gate-driver sheets) have **identical native pin-to-net connectivity** to the saved hierarchy. This review did not overwrite them or save the editor.
- Saved source hashes and snapshot: [source_identity.json](source_identity.json), [saved_source/](saved_source/). Native [ERC](erc.json), [netlist](netlist.xml), [schematic analyzer](schematic.json), [cross analysis](cross_analysis.json).

### Datasheet and CAD coverage

Critical IC/circuit checks used native netlists plus manufacturer documents, not just agreement between symbols and footprints. Existing local PDFs in `ShiroFOC/DataSheets` and the earlier per-section reviews were cross-referenced. No newly populated structured datasheet extraction cache is claimed. The automated analyzer has **mixed trust** (80 deterministic / 44 heuristic findings, no datasheet-backed automated findings); manual datasheet checks supply the stronger evidence where stated.

The fresh association audit covers every component's assigned footprint-file existence, electrical pin/pad-number sets and linked model-file existence. It does **not** mean all downloaded pad dimensions, paste patterns or STEP faces were remeasured. Prior import qualifications are retained, with documented family-model and provisional-crystal caveats. J1, JP601, Y301 and unfinished capacitor specifications are explicit gaps.

### Calculations and simulation

The SPICE skill ran **36 isolated passive/divider calculations, all numerically passing**. Several reconstructed subcircuits use incomplete topology or guessed rails; those passes are **not** evidence that 36 actual board circuits are correct.

A separate [actual-network testbench](actual_networks.cir) was therefore run with KiCad's bundled ngspice 44.2. [Its log](actual_networks.log) confirms:

- Current amplifier zero 1.650 V and ±35.4 A endpoints 1.155/2.145 V, ideal amplifier.
- VM divider: 2.000 V at 42 V.
- NTC divider: 2.245 V at nominal 25°C resistance.
- 10 V and 5 V divider feedback: 1.000 V and 0.798 V respectively at their calculated outputs.
- Brake divider: 1.245 V rising and 1.239 V falling at the existing nominal bus thresholds and fixed command levels, consistent with the documented typical hysteresis treatment.

These checks cover DC/passive arithmetic, not switching regulator loop stability, op-amp transient fidelity, short-circuit interruption, thermal behavior or brake energy capacity. [Calculation helper](calculate.py) also includes mux tolerance extremes, sense scaling and loaded filter calculations.

### False positives and reviewer overrides

- Bootstrap supplies reported without DC sources are charged by internal driver/regulator paths. Correct declaration/modeling is needed; the warning does not imply absent physical charging hardware.
- USB D+/D− are not 5 V logic simply because the ESD device references USB 5 V. No level shifter should be added on that basis.
- U205 PG is deliberately unused/NC; it does not need a pull-up. AS5047 MISO does not need a mandatory pull-up to function.
- `10V_FB`, `10V_GOOD`, ST and VM sense labels are signals, not independently generated power rails.
- JP601 is a deliberately selectable supply; unselected external power is not a missing internal board supply.
- U205 NC/test 19/20 intentionally have no solder lands. JST `MP` pads are mechanical. These pad-set differences are not blockers.
- Automatic regulator checks assumed inappropriate reference voltages/rails; manual checks use 1.000 V for LMR36510 and 0.798 V for MPM3620A.
- Several automatic divider detections split loaded multi-resistor networks into misleading pairs. DNP feedback capacitors were included by isolated simulations. Neither result overrides actual topology and population.
- Routine passive MPN gaps are not interpreted as a request to restart sourcing. Exact converter capacitor requirements are singled out because package suitability can change.

## Previous-review delta

| Previous issue/change | Current status |
|---|---|
| Shared encoder/IMU SPI concern | Resolved by dedicated SPI3 / separate I2C2. |
| External Hall/ABI voltage compatibility | Buffered 3–5 V interface in place. |
| Generic bridge shunt/passive selections and many blank bridge footprints | Selected and assigned; older checklist text was stale. |
| MPM3620A integration and external STSPIN supply | Present and consistent with the checked manufacturer connections. |
| CAN termination assembly | 120 Ω fitted; manual jumper retained. |
| Dual-MOSFET symbol/pad mapping | Still open; must repair before PCB transfer. |
| J1 / crystal / missing STEP models | Still open; updated current download list. |
| Hardware current-trip requirement | Still open; error scale now quantified. |
| TPS2121 OV tolerance | Newly identified issue. |

## Not performed / limits

- PCB routing, return-path, EMC, thermal and schematic-to-PCB analysis were not run: the manual PCB is a stale pre-merge draft and is not the layout of this schematic. Reviewing it as current would be misleading. Run these after a valid new PCB synchronization/placement.
- Gerber/DFM/fabricator checks and component availability/lifecycle checks were not performed, as requested. No current fabrication outputs exist for this schematic revision.
- No full manufacturer switching/macromodel simulation, full transistor transient simulation, hardware test, current rating certification or USB compliance claim.
- Crystal exact-part electrical/package qualification, capacitor DC-bias qualification and complete short-circuit protection timing remain open.
- Existing imported CAD was inventoried and pin-set checked; final physical pin orientation/land-pattern signoff belongs to the association/PCB-update step, especially U1–U3.

## Next handoff

1. Resolve R1 mapping and R2 mux choice; decide the R3 fast-trip acceptance envelope.
2. Select J1/JP601 and finish Y301/converter-cap specifications. Assign U603 from installed libraries.
3. Associate the four requested STEP models when supplied; retain existing imported models elsewhere.
4. Clear remaining ERC issues explicitly and confirm all physical pads have intended nets in a PCB update fixture.
5. Begin fresh placement using the existing layout guidelines. Keep the current PCB draft as historical backup.
