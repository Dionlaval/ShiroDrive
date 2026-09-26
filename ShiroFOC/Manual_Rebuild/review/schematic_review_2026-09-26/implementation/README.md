# Accepted review changes — 26 September 2026

## Result

R1, R2, R4, R5 and R7 implemented. R3 clarified below without added circuitry. R6 deferred at the user's request. **Native KiCad ERC: zero violations.** All 251 components have resolving footprint assignments (49 unique footprints). This completes these schematic revisions; it is not a routed-board or fabrication signoff.

The original files, local libraries and newer MCU/gate-driver autosaves are preserved in `before_changes.zip`. The autosave drawing adjustments were incorporated before editing. The existing draft PCB is untouched.

| Item | Implemented result |
|---|---|
| R1 — bridge | Expanded literal VSW/PGND ranges into individual stacked pins. Pads 3–11=VSW, 12–20=PGND, 27=VIN; 21 and 23–26 remain NC. Eleven thermal vias previously named V now share pad 27/VM. Downloaded copper/mask/paste geometry and existing 3D files are unchanged. Corrected inappropriate electrical pin types. |
| R2 — mux | R210/R212 now 22.0 kΩ, 1%; R211/R213 remain 5.10 kΩ. Nominal rising OV cutoff 5.633 V, calculated tolerance envelope 5.278–5.943 V. This is coarse rejection of abnormal trusted 5 V sources, not precise downstream overvoltage protection. |
| R4 — motor | J1 uses the earlier three large plated wire terminals: `Connector_Wire:SolderWire-6sqmm_1x03_P14mm_D3.5mm_OD7mm`. Installed geometry has 7 mm copper, 4.4 mm plated drills and 14 mm pitch; do not infer drill size from its legacy name. Pins 1/2/3=U/V/W. Local schematic connector symbol is passive; no new footprint geometry. |
| R4 — external sensor | U603 uses standard TI DCU VSSOP-8. JP601 uses an open three-pad solder selector: bridge 1–2 for 3.3 V or 2–3 for 5 V. Open means no supplied sensor power. Never bridge both. No removable header/shunt is required. |
| R4 — crystal | Y301 is Kyocera CX3225FB24000C0FZZH1. Standard 3225 footprint matches the manufacturer drawing; generic STEP remains. |
| R5 — capacitors | Exact TDK parts below recorded in symbol MPN, Manufacturer, Datasheet and comments. Existing 1210 footprint size retained. |
| R7 — test points | Values now identify actual signals, including TP201=PWR_SOURCE_STATUS, TP302=SCREF, TP1008/1009=SWDIO/SWCLK. Removed TP1003 (duplicate VCC; TP301 retained) and TP903 (duplicate GND; TP102 retained). No duplicate test-point nets remain. |

Bootstrap power flags declare the STSPIN's internal bootstrap charging paths to ERC; they are not extra physical parts. No global ERC exclusions were added. Omitted low-side gate resistors, pull-downs and snubbers were not reinstated.

## R3 in plain language

There are two different jobs:

1. **Normal motor current measurement:** shunts → amplifiers → ADC. This remains unchanged and is suitable for the planned control measurements.
2. **Emergency overcurrent shutdown:** internal comparators can stop PWM quickly, but the proposed inputs are tiny unamplified voltages. Their errors become a sizeable uncertainty in the actual trip current.

This is unrelated to the brake chopper. It does not mean the current-measurement circuit is broken. Keep the current hardware and characterize the coarse emergency trip during firmware/bench work. Do not advertise a precise 25 A hardware cutoff. The existing `FW-OCP-01` firmware requirement remains open until the trip range and shutdown timing are measured/validated. A tighter hardware trip would be a separate design decision; no extra comparator circuitry was added.

## R6 — deferred, raise at the next layout review

**Ask the user again before final placement is frozen:** should a short in the external Hall/encoder cable be allowed to collapse the shared control supply, or should its supply be current-limited separately? The present direct selector/R604 connection is retained. This is an explicit deferred robustness choice, not a required change in this revision.

## Selected capacitors and evidence

| References | Manufacturer / exact MPN | Selection |
|---|---|---|
| C205/C206/C214/C215 | TDK **C3225X7R1E226M250AB** | 22 µF, 25 V, X7R, ±20%, 1210; nominal 2.5 mm body height |
| C218/C219 | TDK **C3225X7R1C226M250AC** | 22 µF, 16 V, X7R, ±20%, 1210; nominal 2.5 mm body height |

[25 V manufacturer curves](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C3225X7R1E226M250AB), [16 V manufacturer curves](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C3225X7R1C226M250AC). Original CSV exports are retained in `manufacturer_data/`.

- 25 V part: typical 15.9193 µF each at 10 V. A pair with 20% tolerance and a separate 15% temperature allowance gives about 21.65 µF. The combined temperature/bias curve at a higher 12.5 V gives a conservative cross-check of about 17.70 µF per pair after tolerance. This exceeds the MPM input design target of 10 µF.
- 16 V part: typical 20.4003 µF each at 5 V. The same estimate gives about 27.74 µF per pair; the combined higher-bias 8 V curve gives about 24.05 µF after tolerance, above the MPM output target of 22 µF.
- These are **reference-data estimates**, not guaranteed minima over production spread and aging. The higher-bias cross-check assumes capacitance is no worse at the lower operating bias. Do not present the independent 15% temperature factor as a proven combined worst case.

### 10 V converter output sizing

The earlier universal ≥22 µF *effective* output requirement is replaced with an application-specific sizing basis. The [LMR36510 datasheet, Table 8-1](https://www.ti.com/lit/ds/symlink/lmr36510.pdf) gives 20 µF minimum **rated** / 30 µF nominal rated for its nearby 12 V, 47 µH application. Our selected pair is 44 µF rated; our output is about 10.01 V with 47 µH ±20%.

Using TI Equation 6 with an illustrative 0.25 A load step, 0.2 V allowed excursion, 340 kHz minimum frequency and 56.4 µH maximum inductance gives about 9.33–10.40 µF for 24–65 V input. The 17.7 µF reference-data cross-check exceeds that example requirement. This supports the compact 1210 choice for the expected control/gate loads; it does not prove full-load transient performance or loop stability. Verify startup, load steps and switching response on the prototype. The example is not a guarantee of 0.2 V excursion or an extension of the board's battery rating to 65 V.

**Mechanical note:** the standard generic 1210 STEP may be shorter than these specific 2.5 mm-high parts. Allow at least the manufacturer's maximum body height (2.7 mm) when planning underside/enclosure clearance. No custom capacitor CAD was made.

## Crystal / download request

**Search/download: Kyocera CX3225FB24000C0FZZH1** — 24 MHz, 7 pF, 3.2 × 2.5 × 0.7 mm. Download KiCad/STEP bundle if offered; place it in `downloads/incoming/`. Exact STEP availability has not been established. Another symbol is unnecessary.

[Exact manufacturer specification](https://ele.kyocera.com/assets/products/crystal-device/specification/CX3225FB_7pF.pdf), also retained locally. Pads 1/3 are crystal, 2/4 ground. Recommended lands are 1.4 × 1.2 mm at x=±1.1, y=±0.85 mm, matching the assigned KiCad footprint. ESR ≤40 Ω, drive ≤100 µW. Existing 10 pF C0G loads are the starting values for a 7 pF crystal with approximately 2 pF effective stray capacitance. Verify frequency, startup margin and drive on the finished PCB.

## Validation

- `erc.json`: zero violations, KiCad 9.0.4.
- `netlist.xml` and `validation.json`: circuit connection groups match the pre-edit design after intentional pin expansion and the two TP removals. Automatically generated net names changed for the MOSFET PGND/shunt nodes; their connections did not.
- `cad_inventory.json`: all assigned footprints resolve; MOSFET symbol pins cover physical pads 1–27. Documented exceptions remain U205 NC/test 19/20 without lands and JST mechanical MP tabs.
- `pad_mapping_fixture.kicad_pcb` / `pad_fixture_validation.json`: all 251 footprint files loaded through KiCad's PCB API; 860 physical pads serialized and reloaded with their expected nets. This is a programmatically net-assigned **validation fixture**, not a placed/routed PCB and not a claim of GUI F8 synchronization.
- Downloaded MOSFET geometry checked identical after normalizing only the eleven pad-name corrections; existing 3D files unchanged.
- Revised sheets rendered and visually checked for text/wire overlap; stale OV/BOOT/selector notes corrected.

No component-stock or fabricator checks. PCB return paths, placement, temperature/current capability and hardware fault timing remain future layout/prototype checks.
