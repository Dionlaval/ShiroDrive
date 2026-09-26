# ShiroFOC P2 — manual layout starting point

Open **ShiroFOC_Manual.kicad_pro** in this folder, then its PCB. This is the new working revision. The prior P1 project and Manual_Rebuild files are preserved.

## What is carried forward

- P1's 80 × 80 mm rounded outline, four M3 mounting holes, bulk-capacitor row and parallel bridge/phase-output arrangement.
- Latest manual schematic and imported component libraries. U604 now uses standard SOT-23-6 with its generic model (TI DBV six-pin package, 0.95 mm pitch; standard KiCad lands are an IPC-style alternative to TI's example).
- Current footprint and net assignments, including the LR2512D Kelvin shunts. Source-reference changes such as U301 → U4 and Q401/Q402/Q403 → U1/U2/U3 are explicitly mapped.
- Four copper layers: 70 / 17.5 / 17.5 / 70 µm. The copied dielectric dimensions are provisional; they are not a confirmed fabrication stack or an impedance calculation.

This is **rough placement, intentionally unrouted**. Component shifts clear gross overlaps, not optimize every pin-local loop. Final placement, copper planes, routing, silkscreen and fabrication checks are the user's next steps. A guide box is not a copper zone or enforced keepout.

## Guide layers

| Layer | Content |
|---|---|
| Dwgs.User | Mechanical screw envelopes and routing reminders |
| User.1 | Bulk capacitors, three power cells and brake-stage regions |
| User.2 | Auxiliary supply, USB and external-interface regions |
| User.3 | MCU/analog area, centred underside encoder and sense-route direction hints |
| F.Fab / B.Fab | Component references and body outlines |

Hide the guide layers when they obstruct routing. Nothing on them is electrical copper.

## Placement and routing checklist

1. **Mechanics first:** retain the encoder centre on the back at (140,140) mm. The magnet is outside that face; no top-side central magnet void is required. The MCU is offset at (142,149) mm. Check connector mating clearance and corner screw/washer envelopes; the circles show an 8 mm hardware envelope.
2. **Three repeated phase cells:** U1/U2/U3 line up with J1's U/V/W holes. Keep each VM ceramic → MOSFET pair → low-side shunt → ceramic ground loop short and broad. Respect the actual schematic: the three sets of local VM bypass capacitors return to GND. Do not copy older notes that put a capacitor above the shunt.
3. **Shunts:** active phase U/V/W shunts are R3/R1/R5 respectively, on the back near the power cells. Pads1/4 carry current; pads2/3 are the Kelvin pickup stubs. Route from the stubs as a close pair, away from phase/gate/brake switching nodes. Keep power pours from swallowing the stubs. Short direct force paths and multiple correctly sized vias are needed for backside shunts; there is no fixed amps-per-via guarantee.
4. **Gate drive:** finish placement around the actual U4 gate-driver pins before routing. Put R2/R4/R6 near the relevant GH gate pads. Pair the high-side drive with its source/phase return and low-side drive with its driver return. Bootstrap capacitors C4/C8/C12 need short connections to the appropriate driver bootstrap/output references; rough placement can be moved.
5. **Quiet measurement:** R417/R418/R419 and corresponding V/W networks, bias resistors and optional feedback capacitors belong close to their U4 amplifier pins. Use the underside of the MCU where useful, keeping clear of the encoder and hot power copper. Place VREF/VDDA filters and bypass capacitors close to their pins. Do not run main DC or brake return current through this area.
6. **Ground:** create substantially continuous GND planes on In1.Cu and In2.Cu. They provide signal return paths, not the sole motor-current conductor. Use broad outer-layer VM/GND paths for power. Stitch local decoupling grounds and signal layer transitions to the planes. Check both inner layers for accidental slots caused by via fields. A VM thermal via must not touch GND; likewise the source above each shunt is not GND.
7. **Brake:** keep the external resistor connector and chopper loop at the edge, away from the encoder. Finish Q501/U501 placement and gate loop before signal routing. Keep BRK_SW copper compact and sense the bus from a quieter pickup.
8. **Supplies:** current topology is VM → LMR36510/U201 + L201 → 10V → MPM3620A/U205 → 5V mux → 3V3 LDO. U4 uses external VCC; there is no L301 internal-switcher inductor. Finish capacitor placement at U201 and U205 first, then keep feedback resistors away from switching copper. U205's embedded footprint keepout remains present.
9. **Interfaces:** AS5047 uses dedicated SPI; BMI323 uses I2C. Keep both over continuous ground. Place external Hall protection/buffer and U604 sensor-power protector near J601; place their decouplers at their pins. CAN protection belongs at the connectors, with JP801 termination access. USB D+/D− should be short and paired; determine 90Ω geometry from a real stack before treating the saved width/gap as final.
10. **Comparison part:** R7 is the disconnected BVR4026 parked outside the outline. Compare it to the small shunts and then remove it before production exports. DNP/excluded-from-BOM does not remove its copper/paste from Gerbers.

## Saved routing presets

- Global copper clearance / minimum track width: 0.15 mm.
- Default logic: 0.25 mm track, 0.20 mm clearance.
- Analog: 0.20 mm track/clearance. Gate: 0.40 mm initial width. Logic power: 0.50 mm initial width.
- Power class: 0.50 mm clearance target; its 2 mm track width is a router convenience, **not a 25 A current-rating calculation**. Use purpose-sized copper.
- Through vias: 0.60 / 0.30 mm default; 0.45 / 0.20 mm compact. No blind/buried or microvia plan.
- Copper-to-edge: 0.50 mm. Drill spacing: 0.20 mm base; 0.45 mm for pairs involving component pads, with a retained explicit U901 thermal-via exception.
- Silkscreen: 1.0 mm minimum text / 0.15 mm stroke / 0.20 mm clearance. Imported library reference styling is not final production silkscreen.

See `review/` for the native ERC, unrouted-board DRC, footprint/pad-net validation and migration manifest. Those checks establish a usable starting project, not a finished-board release. Remaining fast-overcurrent-trip, thermal and shunt reflow-profile questions carry forward from the manual schematic review and firmware requirements.

## Known starting-state flags

See [open items](review/OPEN_ITEMS.md): U204's imported land pattern has 0.10 mm copper gaps, U901 has 0.15 mm thermal-via hole webs, and U205 has two NC/test symbol pins without footprint pads. These are recorded rather than hidden by relaxed rules. The board is ready for manual placement/routing work, not fabrication.
