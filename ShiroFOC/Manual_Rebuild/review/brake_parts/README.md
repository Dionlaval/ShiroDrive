# Brake chopper: parts and purpose

Updated 2026-09-26. Scope: manual-rebuild schematic page 8 only.

## Decision

Keep the present topology and nominal **45.9 V turn-on / 44.2 V turn-off** thresholds for the independent board-bus backup. Its functional heading is now **Capacitor un-exploder**, with an explicit **NOT a BMS or battery protector** subtitle. U502 retains its actual TLV3012BIDBVR part identity.

The name is a reminder of purpose, not a guarantee against capacitor failure. It also aims to protect the other bus-connected electronics. Firmware must use pack-appropriate braking thresholds for 6S, 8S or 10S. This fixed backup does not detect a full or overcharged individual cell.

## Selected on-board values

| References | Selection | Reason |
|---|---|---|
| R506–R508 | Three 150 kΩ, 0.1%, RT1206BRD07150KL | 450 kΩ upper divider; each selected resistor is rated 200 V / 0.25 W. Actual dissipation is only about 1.5 mW each at 46 V. |
| R509 | 12.7 kΩ, 0.1%, RT0603BRD0712K7L | Sets the comparator input scaling. |
| R510 | 1 MΩ, 0.1%, RT0603BRD071ML | Positive feedback creates a gap between switch-on and switch-off voltages, avoiding rapid toggling around one voltage. |
| C504 | 1 nF C0G, 50 V, C1608C0G1H102J080AA | Stable filter capacitor; nominal divider time constant 12.2 µs. |
| R501/R504/R505 | 10 kΩ, 1%, RC0603FR-0710KL | Existing command/gate pulldowns retained. |
| R502 / R503 | 33 Ω / 4.7 Ω, 1%, RC0603FR-0733RL / RC0603FR-074R7L | Existing command series resistor and gate damping retained. |
| C501 | 1 µF, 25 V X7R, C1608X7R1E105K080AB | Driver reservoir on the 10 V rail; nominal capacitance decreases under DC voltage. |
| C502/C503 | 100 nF, 50 V X7R, C1608X7R1H104K080AA | Driver/comparator bypass; increased selected voltage rating, same capacitance. |
| D501 | BZT52C12-7-F | Exact ordering code for the existing 12 V gate Zener. |

Q501, U501, U502 and D502–D504 retain their existing parts. J501 is a pair of solder-wire pads, not a purchased terminal block. The external resistor is recorded separately as an accessory and in J501's hidden properties.

All associations and wiring are preserved. The complete part list is in [selected_parts.csv](selected_parts.csv).

## Threshold calculation and its limits

For Rtop = 450 kΩ, Rbottom = 12.7 kΩ, Rfeedback = 1 MΩ:

`Vbus_trip = Vin_trip × (1 + Rtop/Rbottom + Rtop/Rfeedback) − Vout × Rtop/Rfeedback`

Using the TLV3012B typical 1.242 V reference, typical 6 mV internal hysteresis, and ideal output levels 0 / 3.3 V gives 45.919 V rising and 44.213 V falling. Reference accuracy, input offset, output swing, supply tolerance, resistor tolerance and temperature move the actual thresholds. These are nominal values, not guaranteed limits.

The filter sees 450 kΩ || 12.7 kΩ || 1 MΩ = 12.20 kΩ, giving 12.20 µs with 1 nF. Filtering and comparator/switch delay allow overshoot. The dump resistor also has finite absorption power: the bus can keep rising if regeneration exceeds it. Bench testing must measure actual trip voltages and peak bus voltage under representative braking and battery-disconnect conditions.

## Provisional external resistor

**Vishay Dale RH25010R00FE01: 10 Ω, 1%, 250 W chassis resistor.** This is a first-prototype bench choice, not a final rating for every future robot. It is off-board and does not consume PCB area.

| Bus voltage | Full-on current | Full-on resistor power |
|---|---:|---:|
| 25.2 V (6S full) | 2.52 A | 63.5 W |
| 33.6 V (8S full) | 3.36 A | 112.9 W |
| 42.0 V (10S full) | 4.20 A | 176.4 W |
| 46.0 V (near hardware trip) | 4.60 A | 211.6 W |

Calculated using I = V/R and P = V²/R, ignoring small switch/wiring drops. At 48 V and −1% resistance, the instantaneous figures rise to 4.85 A and 232.7 W. These are calculation points, not a claimed board operating range.

**250 W requires the manufacturer's heatsink conditions and temperature derating.** The RH250 free-air rating is only 100 W at 25 °C. The datasheet reference mounting is a 12 × 12 × 0.125 inch aluminium panel; a smaller heatsink needs its own thermal assessment. The existing circuit has no external-resistor temperature shutdown. A sustained hardware brake command can overheat an inadequately cooled resistor.

For PWM operation, average resistor power is approximately duty × V²/R. Repeated stopping also needs an energy budget: E = ½Jω² for a rotating load, plus any gravitational energy and other moving masses. Check both each stop and average heat between stops. Do not equate the motor's 25 A phase-current target to brake-resistor current. With this resistor, 46 V full-on braking absorbs about 212 W, not arbitrary motor power.

Use short twisted leads. D504 provides the existing path for resistor/lead inductive current at switch-off. Verify diode temperature and switch overshoot on the prototype, particularly with a wirewound resistor. No resistor pulse-energy qualification or complete braking transient simulation has been claimed.

## Verification

- Before-edit schematic snapshot retained in `before/`.
- Netlist connectivity is unchanged.
- ERC has the same 16 pre-existing findings; no new findings introduced. This is not a claim that the whole project is ERC-clean.
- Footprint assignments, wires and labels are unchanged.
- Divider DC calculation cross-checked with ngspice (`divider_check.cir`, `divider_check.log`); this checks the passive network with each output state held fixed, not the comparator's full transient response.
- Rendered brake sheet inspected; see [brake_chopper.svg](brake_chopper.svg).
- No stock, fabrication, whole-board layout or CAD audit was performed in this change.

## Manufacturer sources

- [TI TLV3012 / TLV3012B](https://www.ti.com/lit/ds/symlink/tlv3012.pdf): reference and comparator behavior.
- [Yageo precision RT resistors](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RT_1-TO-0-01_ROHS_L): ordering codes and ratings.
- [Yageo RC resistors](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L).
- [TDK 1 µF capacitor](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1608X7R1E105K080AB), [100 nF capacitor](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1608X7R1H104K080AA), [1 nF C0G capacitor](https://product.tdk.com/info/en/documents/chara_sheet/C1608C0G1H102J080AA.pdf).
- [Diodes BZT52 series](https://www.diodes.com/_files/datasheets/ds18004.pdf).
- [Vishay RH/NH power resistors](https://www.vishay.com/docs/30201/rhnh.pdf): ratings, cooling conditions and ordering format.
