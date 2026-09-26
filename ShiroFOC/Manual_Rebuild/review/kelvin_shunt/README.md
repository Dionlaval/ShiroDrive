# LR2512D shunt and Kelvin footprint

## Implemented

R1/R3/R5 use **Milliohm LR2512D-3W-0.5mR-1%**, two physical terminals,0.5mΩ,1%,3W. Custom local symbol **Manual:LR2512D_Kelvin** exposes four passive PCB connections; the body is still one two-terminal purchased component. Amplifier gain28 and14mV/A are unchanged. Existing wires/positions were preserved. Current-sense sheet annotation and component catalogue updated.

## Source and geometry

User-supplied [manufacturer PDF](../../../DataSheets/LR2512D_C500733.pdf), HoLR2512D Ho-A1 dated2020-07-15, pad revision2020-12-23. Pages2–3 were visually inspected. Use the **2W/3W,0.25–0.5mΩ** row, not the overlapping resistance row for3.5W.

- Main pads: **2.57 ×4.00mm**, centers x=±2.340mm, inner gap **2.11mm**, total span7.25mm. Manufacturer dimensions a=4.00,b=2.57,L=2.11.
- Body6.4±0.25 ×3.2±0.25mm, thickness0.8±0.25mm. Generic KiCad2512 STEP is approximate; use these dimensions for mechanical clearance.
- Horizontal sense stubs extend **0.600mm inward** from each power pad, **0.250mm wide**. These are engineering choices; the datasheet illustrates but does not dimension the stubs. No vertical/downward legs.
- Sense-pad routing anchors x=±0.580mm,y=0;0.25mm squares, copper-only. Stub tips x=±0.455mm; copper gap0.91mm.
- Main pads include copper,mask,paste and solid zone connection. Sense stubs are masked copper without paste openings and have no zone connection. Solder mask over the stubs stops the paste opening from growing toward the resistor body.
- Courtyard±3.90 ×±2.25mm includes pad allowance and maximum specified body dimensions.

| PCB pad | Function | Intended copper join |
|---|---|---|
|1|Power+ / MOSFET low-side return|Pad2|
|2|Kelvin sense+|Pad1 at the short stub|
|3|Kelvin sense−|Pad4 at the short stub|
|4|Power− / ground return|Pad3|

The footprint declares **two independent net-tie groups:1,2 and3,4**. This permits those physical copper joins while keeping power and sensing nets separate for routing. There is no copper join across the resistance element. All four symbol pins are passive, not logic inputs.

## Routing requirements

Route sensing from pads2/3, upwards or downwards as placement requires. Keep the two traces close together and clear of switching copper; avoid adding length simply to equalize resistance. Keep all high-current entry/exit on the large pads and make the three phases' entry geometry consistent. Do not let a power pour engulf a sense stub or add another power-to-sense join elsewhere. Inspect zone fills manually: a clean DRC alone does not guarantee Kelvin accuracy. Sense stubs under the resistor remain masked; no vias in solder lands by default.

At25A continuously through a shunt,P=0.3125W. Actual low-side RMS current depends on PWM operation. The3W rating derates above70°C toward zero at170°C in the supplied curve; PCB thermal conditions still require prototype validation. Calibrate assembled phase-current gain;1% component tolerance is not a guarantee of1% total measurement accuracy.

## Verification

- Native schematic ERC: **0 violations**,254 components.
- Before/after netlists have identical sets of connected pins. Three automatically generated power-net names change with the newly named symbol pins; no wiring changes.
- Native KiCad footprint load/save/read succeeds with four assigned pads.
- Isolated front-side and flipped back-side fixtures: **0 DRC violations,0 unconnected items**.
- Removing only the net-tie declarations in a negative-control fixture produces12 violations, confirming the copper connections were checked rather than silently ignored.
- Native copper renders and both schematic sheets visually inspected.
- Actual draft PCB and all unrelated schematic sheets remain unchanged. This is not a full board DRC or thermal validation.

`before.zip` preserves the prior schematic/library/docs. `footprint_fixture.kicad_pcb` is a test fixture only; `negative_control.kicad_pcb` is intentionally invalid. Native reports and `validation.json` sit beside this note.
