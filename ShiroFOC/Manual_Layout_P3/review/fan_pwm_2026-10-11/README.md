> Supply update: the sensor selector was subsequently removed. J601 now has fixed protected 5 V. See [the current supply revision](../fixed_5v_feedback_2026-10-11/README.md). The fan circuit below is unchanged.

# P3 — fan PWM and selectable external sensor supply

Implemented 2026-10-11 in `Manual_Layout_P3`. Schematic changes only; the PCB is not synchronized or routed for these changes.

## Fan connector

J502 replaces the brake thermistor input with a protected, fixed 5 V, two-wire fan output. The original JST GH connector footprint is retained.

| Connection | Function |
|---|---|
| J502 pin 1 | `FAN_5V`, supplied from `5V_SYS` through U503 |
| J502 pin 2 | `FAN_RETURN`, switched to ground by Q502; do not connect it externally to ground |
| J502 MP | Grounded mounting tabs |
| STSPIN32G4 PC1 / physical pin 10 | `FAN_PWM`, hardware PWM using LPTIM1_OUT |

U503 is TPS2553DBVR, reusing the sensor limiter part. IN and EN are tied to `5V_SYS`. R513 = 49.9 kΩ, 1%, sets the current limit to about 520 mA nominal; the datasheet's 49.9 kΩ test gives 475–565 mA over temperature before resistor tolerance. This is a protection threshold, not a continuous fan-current promise. Start with a fan rated at no more than 250 mA running current and check its startup/stall current.

Q502 is CSD17483F4, reusing the small MOSFET already on the board. Gate pin 1 is driven through R511 = 100 Ω; source pin 2 is ground; drain pin 3 is `FAN_RETURN`. R512 = 100 kΩ pulls its gate to ground during reset. The datasheet specifies maximum RDS(on) of 310 mΩ at VGS = 2.5 V and 25°C, suitable for the provisional small-fan current budget with 3.3 V drive. Thermal behavior still needs board validation.

D506 = PMEG2010EA,115 (20 V, 1 A, SOD-323) clamps inductive turn-off transients: pin 1 cathode to `FAN_5V`, pin 2 anode to `FAN_RETURN`. C505 = 100 nF input bypass and C506 = 4.7 µF protected-output bypass return to unswitched ground. D505 and the original brake thermistor pull-up, series filter and ADC connection have been removed or repurposed.

### Firmware behavior

- Configure PC1 for LPTIM1_OUT and active-high duty: 0% = off; 100% = continuously on. Initialize to off before enabling the alternate function. Motor PWM remains on its existing timer.
- Remove PC1 from brake-NTC ADC sampling and remove brake-thermistor open/short fault handling. Other temperature inputs remain available.
- Select a two-wire 5 V fan documented to tolerate supply PWM. PWM frequency, minimum running duty and a full-duty startup interval depend on the fan. Do not assume the 25 kHz control convention of a four-wire fan applies. There is no tachometer connection.
- Keep the fan off under USB-only power unless the available USB current and total load are verified. Independent branch current limits do not prevent an upstream supply brownout. The earlier illustrative total of roughly 555 mA on 5 V exceeds a 500 mA USB allowance.

## External sensor connector

J601 retains continuous sensor power. JP601 is restored as a three-pad manual solder selector ahead of U604. Pads 1–2 are bridged by default for 3.3 V. To select 5 V, turn power off, remove the 1–2 bridge and solder 2–3. Never bridge both supply positions.

U604 IN, EN and ILIM follow the selected voltage. ILIM tied to IN restores the 75 mA nominal sensor current limit (50–100 mA specified range). Keep the initial normal sensor-plus-pull-up budget at or below 25 mA. The former fan-capable sensor-limit resistor R618 is removed. J601 is independent of fan PWM.

## Fault reporting and brake operation

U503 and U604 have open-drain fault outputs, joined to the existing pull-up and MCU PC13 input. This net and TP1023 are renamed `EXT_POWER_FAULT_N`. A low level reports a current-limit/thermal fault from either limiter; it does not identify which branch. Firmware should maintain external-feedback-loss protection and may disable the fan when this fault is asserted.

The brake power stage, UCC27517A driver, firmware `BRAKE_PWM`, diode command OR and hardware `BRAKE_OV_CMD` overvoltage clamp retain their previous components and connectivity. Only the brake thermistor function was removed.

## Layout handoff

Keep fan power-switch current local to J502, Q502, U503 and the bypass capacitors. C506 goes to actual ground, not to the switched fan return. Put D506 near the fan connector/switch and R513 close to U503. The schematic now differs from the PCB; update and route the PCB in a later layout task.

## Validation

**Verified:** native KiCad netlist assertions cover every new fan pin, selector positions, limiter connections, diode polarity, grounded mounting tabs, MCU output and fault aggregation. All unrelated pin assignments and the brake control circuits match the saved baseline. Footprint pad numbers match all affected/new symbols. Pages 4, 8 and 10 were exported and visually checked.

ERC has **no new findings**: before and after both contain 1 error and 16 warnings. The existing error is the #FLG11/#FLG12 power-output connection; existing warnings include library mismatches, off-grid endpoints and the USB supply net-name conflict. This change is not a full-board sign-off. Fan behavior and PWM frequency have not been tested on hardware.

The PCB SHA-256 is unchanged. `validation.json` contains the scoped checks and hashes. `before-target-files.zip` preserves the exact pre-change versions, including the user's existing edits. `schematic_changes.pdf` contains the three changed functional sheets.

## Manufacturer sources

- [STSPIN32G4 datasheet](https://www.st.com/resource/en/datasheet/stspin32g4.pdf): PC1 physical pin 10 and LPTIM1_OUT alternate function.
- [TPS2553 datasheet](https://www.ti.com/lit/ds/symlink/tps2553.pdf): DBV pinout, ILIM settings and open-drain FAULT.
- [CSD17483F4 datasheet](https://www.ti.com/lit/gpn/csd17483f4): 1=gate, 2=source, 3=drain; low-voltage gate-drive resistance ratings.
- [PMEG2010EA datasheet](https://assets.nexperia.com/documents/data-sheet/PMEG2010EA.pdf): ratings and SOD-323 cathode/anode pinout.
- [Analog Devices fan-control guidance](https://www.analog.com/en/resources/analog-dialogue/articles/how-to-control-fan-speed.html): distinctions between fan supply PWM and a separate four-wire PWM control input.
