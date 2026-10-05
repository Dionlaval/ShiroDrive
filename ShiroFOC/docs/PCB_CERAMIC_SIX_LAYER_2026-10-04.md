# P3 ceramic DC link and six-layer revision

Date: 2026-10-04  
Project: [Manual_Layout_P3](../Manual_Layout_P3/ShiroFOC_Manual.kicad_pro)  
Status: schematic and placement revision complete; **PCB remains partially routed**.

The approved change replaces the three electrolytic DC-link capacitors with a ceramic bank, adds optional phase snubbers and measurement access, and establishes six copper layers. The user's correction keeps the existing battery damping pair **R102/C107**, including its original position, connectivity and DNP state. Copper is **2 oz outer / 0.5 oz inner**.

## DC-link capacitor selection

**Samsung CL32Y106KCVZNWE: 10 µF, 100 V, X7S, ±10%, 1210.** The manufacturer's body dimensions are 3.2 × 2.5 × 2.5 mm. The BOM includes manufacturer, MPN, voltage, dielectric, population and LCSC code **C3840810**. Sources: [Samsung product data](https://product.samsungsem.com/mlcc/CL32Y106KCVZNW.do), [manufacturer characteristic sheet](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/3563/CL32Y106KCVZNWE_Tech_Article.pdf), [LCSC listing](https://www.lcsc.com/product-detail/C3840810.html).

| Schematic group | Fitted references | Optional DNP references |
|---|---|---|
| U | C101, C110–C124 | C125, C126 |
| V | C102, C127–C141 | C142, C143 |
| W | C103, C144–C158 | C159, C160 |

- **48 fitted:** 480 µF nominal. Reading the manufacturer's typical DC-bias curve gives approximately **3.3 µF per capacitor at 42 V**, or approximately **160 µF for the bank**, before temperature, tolerance and aging. This is a curve estimate, not a guaranteed minimum.
- **Six spare positions:** another 60 µF nominal, approximately 20 µF typical at 42 V on the same basis.
- All 54 positions connect VM to GND. U/V/W are schematic population groups, not separate electrical rails.
- Physical placement uses **32 front and 22 back positions**, including the DNP positions. Front capacitors occupy the space released by the cans; back capacitors occupy the power-side region. Existing gate/sense routing and the central encoder constrain their distribution.
- Existing local 10 nF, 1 µF and 4.7 µF bypass components remain. C3 and C7 moved within the power region; they had no existing copper touching their pads.

This is a compact prototype choice, not an energy-storage equivalent to the previous 3 × 680 µF bank. The 100 V rating does not eliminate DC-bias loss. Aggregate ripple-current capability, bus ripple, capacitor temperature, cable resonance, hot-plug overshoot and regenerative events remain to be established with the actual assembly. The existing 18–42 V and 25/40 Arms objectives remain targets, not ratings established by this revision.

TP104 (VM) and TP105 (GND) provide 3 mm solder pads for an external bulk-capacitor experiment. Use short paired connections; these pads do not make a remote capacitor equivalent to local commutation decoupling. The existing optional battery RC, TVS and brake circuitry are retained.

## Phase snubbers and measurement access

| Function | Phase U | Phase V | Phase W |
|---|---|---|---|
| Series RC snubber, both DNP | R415 / C413 | R425 / C423 | R435 / C433 |
| Low-side gate probe | TP411 | TP421 | TP431 |
| Low-side source probe | TP412 | TP422 | TP432 |
| Phase probe | TP413 | TP423 | TP433 |
| Current-amplifier output probe restored to PCB | TP1018 | TP1019 | TP1020 |
| Nearby current-probe GND pad | TP414 | TP424 | TP434 |
| Existing optional feedback capacitor restored to PCB | C414 | C424 | C434 |

Each phase RC is **PHASE → resistor → capacitor → low-side source before the shunt**, across the low-side switching device. It does not return through the Kelvin sense trace. The new `LS_SOURCE_U/V/W` labels name existing source nets; all original component-pin connections are unchanged.

The phase RC footprints are 1206 and remain **DNP / TUNE**. Select C0G/NP0 capacitors rated at least 100 V and pulse-capable resistors after measuring ringing, then verify resistor pulse energy and average loss. No guessed resistor/capacitor values are fitted. [TI's motor-driver RC snubber guidance](https://e2e.ti.com/support/motor-drivers-group/motor-drivers/f/motor-drivers-forum/991693/faq-proper-rc-snubber-design-for-motor-drivers) describes the measurement and tuning approach.

C414/C424/C434 retain their existing **47 pF C0G, DNP** selection. Their inclusion on the PCB preserves the option to tune current-amplifier bandwidth after settling and control-loop checks. TP101/TP102 were also restored to the PCB as a small bus/ground probe pair. Added bare test pads have no paste aperture and are excluded from assembly BOM/position output.

## Six-layer allocation

| Physical layer | KiCad layer | Intended use | Nominal copper |
|---|---|---|---|
| L1 | F.Cu | Power stage, local power copper, components and signals | 2 oz / 70 µm |
| L2 | In1.Cu — GND L2 | Continuous ground reference | 0.5 oz / 17.5 µm |
| L3 | In2.Cu — Signals L3 | Signals referenced primarily to L2 | 0.5 oz / 17.5 µm |
| L4 | In3.Cu — Power L4 | Power distribution, supplemented by outer copper | 0.5 oz / 17.5 µm |
| L5 | In4.Cu — GND L5 | Continuous ground reference | 0.5 oz / 17.5 µm |
| L6 | B.Cu | Encoder, analog, ceramics, local power copper and signals | 2 oz / 70 µm |

Filled GND zones are present on L2 and L5. Three existing signal segments formerly on In1.Cu moved to In2.Cu: two I2C2_SCL segments and one SHUNT_V_SENSE_N segment. **L4 is allocated but has no new power pour yet.** Additional stitching and the high-current supply/return routing are part of completing the PCB.

The saved **nominal 1.60 mm geometry target** uses dielectric thicknesses, top to bottom, of **0.10 / 0.13 / 0.91 / 0.13 / 0.10 mm**, plus the copper above and 0.01 mm solder mask on each side. It places L1/L3 near L2 and L4/L6 near L5, with the thick dielectric at the centre.

These dimensions are not an approved board-house stack identifier. Match the eventual fabricator's available 2 oz / 0.5 oz build and update the KiCad physical stack and USB impedance calculation before fabrication. The generic FR4 permittivity and loss values in the file are placeholders for that calculation. [JLCPCB's stackup and impedance tool](https://jlcpcb.com/impedance) is one reference for selecting a production build.

The thin inner copper provides reference and distribution; it does not establish motor-current capacity. Main current paths still require broad outer copper, appropriate via arrays and thermal verification.

## Preserved layout and recorded movements

- U601 remains locked on B.Cu at **(0, 0)**. The **80 × 80 mm outline with 5 mm corner radius**, four mounting holes, and centred 50/60/70/80 mm comparison rectangles are preserved.
- U4's complete footprint, including the manually chamfered F.Paste pattern, is preserved.
- R102/C107 and all other original footprints are preserved apart from the three replaced can footprints and these three small moves:

| Reference | Old position, mm | New position, mm | Reason |
|---|---|---|---|
| C3 | (25.889688, 5.563669), F.Cu | (17.3, 5.56), F.Cu | Space for phase RC |
| C7 | (25.889688, 19.563669), F.Cu | (17.3, 19.56), F.Cu | Space for phase RC |
| JP601 | (17.5, 25.599999), B.Cu | (24, 36.4), B.Cu | Space for ceramic bank |

All three were unrouted at their pads. Two GND segments that only joined the old electrolytic pads were removed after they became dangling. Remaining original tracks and vias are preserved, aside from the three layer moves above. The [placement manifest](../Manual_Layout_P3/review/ceramic_six_layer_2026-10-04/placement_manifest.json) records all new positions and orientations.

## Verification and remaining work

KiCad 9.0.4 native exports and an independent comparison against the pre-change backup give:

| Check | Before | After |
|---|---:|---:|
| ERC errors | 0 | 0 |
| ERC warnings | 9 | 9, same findings |
| PCB DRC violations, excluding unconnected items | 127 | 117, no new findings |
| Existing clearance violations | 11 | 11 |
| Unconnected items | 412 | 499 |
| PCB footprints | 219 | 298 |

The unconnected count increases because this revision adds footprints to an already partly routed PCB. **New capacitor, snubber and probe connections still require PCB routing.** Clean comparison results mean the revision did not introduce additional clearance/other DRC violations; they do not mean the complete board passes DRC.

All 21 revision checks passed: original schematic connectivity, new PCB-to-schematic pad assignments, population, snubber return nodes, preserved geometry/copper and layer configuration. The DC-link, bridge and current-sense schematic pages and both placement views were rendered and visually inspected. This was not a complete EMC, thermal, transient or manufacturing review.

Artifacts: [validation report](../Manual_Layout_P3/review/ceramic_six_layer_2026-10-04/validation.json), [BOM](../Manual_Layout_P3/review/ceramic_six_layer_2026-10-04/bom.csv), [schematic PDF](../Manual_Layout_P3/review/ceramic_six_layer_2026-10-04/schematic.pdf), [front placement](../Manual_Layout_P3/review/ceramic_six_layer_2026-10-04/placement_front.png), [back placement](../Manual_Layout_P3/review/ceramic_six_layer_2026-10-04/placement_back.png). A complete pre-change archive is in `Manual_Layout_P3/ShiroFOC_Manual-backups/ShiroFOC_Manual-before-ceramic-six-layer-2026-10-04.zip`.
