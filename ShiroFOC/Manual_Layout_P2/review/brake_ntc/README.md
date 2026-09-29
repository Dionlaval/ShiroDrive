# Optional external brake-resistor NTC input

Updated P2 schematic and placement, 27 September 2026. The older Manual_Rebuild/P1 projects remain unchanged; `before.zip` preserves the pre-change P2 files and firmware requirements.

## Circuit and pin allocation

- J502: JST GH SM02B-GHS-TB, standard KiCad footprint and generic library model. Pin 1 = probe, pin 2 = quiet GND. Optional passive external 10 kΩ-at-25°C NTC; no external probe part is included in the board BOM.
- R511: 10 kΩ, 1%, 0603, pull-up to 3V3.
- R512: 4.7 kΩ, 1%, 0603, series input current limiting/filter resistance.
- C505: 100 nF, 16 V, X7R, 0603, to GND at the ADC end.
- D505: BAT54S, SOT-23 rail clamps. Pin 1 = GND, pin 2 = 3V3, pin 3 = ADC. This is basic transient input conditioning, not isolation or protection against connecting the probe to VM/brake power terminals; ESD performance is not qualified.
- PC2 / STSPIN pad 11: ADC12_IN8; `NTC_BRAKE`.
- Status LED moved from PC2 to PC15 / STSPIN pad 5. Active-low sink, open-drain/low-speed; R304 changed from 1 kΩ to 2.2 kΩ. TP1021 relabelled `STATUS_LED_N`. PC15 is no longer spare.

The probe must be thermally attached and electrically insulated from resistor power terminals. Its insulation, adhesive and sensor temperature range must suit the actual resistor body. 5 cm leads are suitable; use a twisted pair away from switched-current wiring. The external probe's actual curve and temperature rating remain an installation choice, not an assumed B3380/B3950 interchangeability.

## Nominal calculations

`Vadc = V3V3 * Rntc / (10000 + Rntc)` neglecting input and diode leakage. At 25°C with a 10 kΩ probe: 1.65 V for 3.3 V supply. A short tends to 0 V; open tends to 3.3 V. Scale against the actual ADC reference. Clamp leakage, especially at high PCB temperature, introduces error and must be included in threshold validation.

`tau = (4700 + (10000 || Rntc)) * 100 nF`: 0.97 ms at 25°C (164 Hz pole), 1.47 ms at open circuit (108 Hz pole). These are electrical filter values, not sensor response times. Maximum nominal probe self-heating is about 0.272 mW at Rntc = 10 kΩ and 3.3 V. Firmware starts with >=10 ms electrical settling and 20 Hz acquisition without disturbing FOC sampling. Use measured thermal lag and the selected probe curve to choose final filtering/thresholds.

PC15 sinks below 1.65 mA even with a shorted LED at 3.6 V and 2.2 kΩ. Include PC14's input-mux pull-up current in the PC13–PC15 shared 3 mA budget; do not use PC15 as an LED current source. Keep LSE disabled.

## Firmware behavior

Updated [firmware requirements](../../../requirements/FIRMWARE_REQUIREMENTS.md): FW-TEMP-02/03/04, FW-LED-01 and resource map. Probe presence is explicitly configured. An unplugged optional probe reports unavailable; loss of a configured probe faults. Temperature supplements the brake energy budget and requests early regeneration derating. It must not disable the independent bus-overvoltage clamp. A connected temperature probe does not prove power-resistor continuity.

## Verification and limitations

- Native ERC: zero violations.
- Native PCB DRC: same 27 pre-existing violations and two U205 missing-pad parity warnings; no added DRC findings after placement cleanup.
- All new pad nets and the PC2/PC15 remap cross-checked against native schematic export.
- Existing footprint positions, angles and sides preserved; five new parts are on the back. No traces, vias or planes added.
- Rendered MCU and brake sheets inspected; bottom layout preview inspected separately.
- This is a scoped schematic/placement addition, not a complete power-stage, EMC, thermal, sourcing or fabrication review. Existing issues in `../OPEN_ITEMS.md` remain.

Sources: STSPIN32G4 local datasheet pin table (PC2, pad 11, ADC12_IN8); [STM32G431 datasheet](https://www.st.com/resource/en/datasheet/stm32g431cb.pdf) pin table and PC13–PC15 drive note; [BAT54S datasheet](https://assets.nexperia.com/documents/data-sheet/BAT54S.pdf) pinning. Standard KiCad connector, SOT-23 and 0603 footprints used.

Migration scripts are one-shot audit records and depend on the local KiCad runtime/helper; do not rerun them over manual edits. Subsequent schematic-only drawing cleanups and final new-part placement shifts are included in the native files and final reports.
