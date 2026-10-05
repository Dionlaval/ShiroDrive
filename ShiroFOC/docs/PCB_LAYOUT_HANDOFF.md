> **Active P3 revision (2026-10-04):** continue `Manual_Layout_P3/ShiroFOC_Manual.kicad_pro`. The [ceramic / six-layer revision](PCB_CERAMIC_SIX_LAYER_2026-10-04.md) supersedes historical P0/P1 capacitor and layer details in this handoff.

# ShiroFOC A1-Drawing / A0 electrical PCB layout handoff

> **Current placement (2026-09-19):** use [ShiroFOC_KiCad_P1](../ShiroFOC_KiCad_P1/ShiroFOC_KiCad.kicad_pro). [P1 notes](PCB_PLACEMENT_P1.md) supersede older placement coordinates and capacitor-replacement proposals. The original P0 project is retained.

**P1 revision notes:** see [PCB_REVISION_LIST_P1.md](PCB_REVISION_LIST_P1.md). H1-H4 are now in the schematic; the P0 PCB still awaits the mounting holes and placement revision. Earlier parity reports and release PDFs/ZIPs predate this change.

**PCB placement update (2026-09-17):** an 80 × 80 mm, four-layer P0 board now contains all 260 footprints. Continue from the existing PCB rather than importing into a new blank board. Read the [P0 placement checkpoint](PCB_PLACEMENT_P0.md) for checks, footprint corrections, remaining warnings and mechanical assumptions. It is not routed.

Read the [detailed PCB layout plan and subsection guidelines](PCB_LAYOUT_GUIDELINES.md) before placement. It defines the six-layer, 2 oz outer-copper approach, double-sided placement, Kelvin routing and routing/review sequence.

Start from `ShiroFOC_KiCad/ShiroFOC_KiCad.kicad_pro` in KiCad 9. Use **Update PCB from Schematic** to import the native hierarchy. There is no routed PCB or fabrication package in this schematic release. Use the checked-in local footprints, not package-name look-alikes. Read [release review](DESIGN_REVIEW_REV_A.md) for operating limits and [firmware contract](FIRMWARE_BRINGUP_CONTRACT.md) for the pin requirements.

The connected redraw preserves the entire A0 electrical circuit. U301A-F are units of one physical STSPIN32G4. Some local net names now include a sheet path; `outputs/net_name_aliases.json` maps them to the original names in this document. The [redraw review](SCHEMATIC_REDRAW_REVIEW.md) lists the new sheet organization.

## Placement order

1. Establish the motor-axis location/magnet clearance for U601, mounting points, heatsink interface, connector access and stack-up. Use the smallest practical rounded square, no larger than 150 × 150 mm. Centre the AS5047P sensing point on the back side. Put the MCU and MOSFETs on top, with the MCU offset from the encoder so its underside remains available for decoupling/ADC components. See the detailed plan for the initial floorplan and DRC settings.
2. Place Q401/Q402/Q403, R416/R426/R436, local ceramics and J401 around a short, broad VM/GND distribution. Place C101–C103 close to that bus and J101. Keep access for an external low-inductance capacitor bank during ripple characterization.
3. Place U301 with short gate/phase-sense/bootstrap connections. Keep its analog side facing the Kelvin shunts and away from phase-node copper.
4. Place U501/Q501/D501/D504/J501 as a tight brake loop; place U502 and its divider in quiet copper away from BRK_SW. The external resistor is a separately cooled assembly.
5. Place buck power loops, mux and LDO; then analog bias/decoupling, feedback, IMU, communications and debug access.

## Nets and routing requirements

| Nets / components | Requirement |
|---|---|
| VM, OUT1–3, SHUNT_*_FORCE_P, GND power paths | Copper pours/planes and parallel vias sized from the chosen stack-up and thermal model. Do not route motor current using the default 0.2 mm signal width or thermal-relief spokes. |
| C412/C422/C432 | 1 µF local bus capacitors: VM to common GND, spanning the complete bridge/shunt return. |
| C415/C425/C435 | 10 nF / 100 V package bypass: VM directly to the respective MOSFET PGND/source **above** its shunt. Place directly at the package terminals. This is intentionally a different return from the 1 µF capacitors. |
| R416/R426/R436 | Force pads 1 and 4 carry power; sense pads 2 and 3 get separate traces. Do not join a Kelvin sense pad to force copper at the PCB pad. The resistor itself makes the physical four-terminal connection. |
| SHUNT_*_SENSE_P/N | Differential Kelvin pairs; short, close together and over quiet ground. No shared gate-driver or bus-current return. The negative sense trace is not a general ground connection. |
| R417–419 / R427–429 / R437–439; R410/420/430 and R441–443 | Place close to the matching MCU op-amp pins. Match resistor technology/temperature coefficient. Keep the VREF bias distribution quiet and decoupled. DNP feedback capacitors stay beside feedback resistors. |
| GHS*, GLS*, *_GATE | Route short to each package; series resistor nearest gate. Reference GH return to OUTx and GL return to the source/shunt region. Keep gate and return loops tight, with no switching copper under sensor traces. |
| BOOT1–3, C411/C421/C431 | Capacitor directly between corresponding BOOT and OUT pins; short loop to U301. Do not tie bootstrap negative to GND. |
| SCREF, C314, R310–312 | Quiet ground and short track; no phase-node coupling. SCREF protects via VDS, not a calibrated shunt-current threshold. |
| VCC_SW / 5V_SW | Small switch islands; tight input-capacitor, diode/IC, inductor loops. Observe each converter's layout guide. |
| R301/R302, C303–306 | Keep VDDA and VREF decoupling at U301. GND remains continuous; control return placement rather than splitting the reference plane under analog traces. |
| U204 DYD pad 2 | Solid ground thermal copper and via. Validate LDO heating at up to 0.624 W fault allowance; avoid surrounding it with hot power copper. |
| R506–510, U502 | Short quiet sense node and reference. Three series VM resistors distribute voltage stress. Comparator output feedback is intentional hysteresis. |
| Q501/U501/D504 | Kelvin source return from Q501 to U501 GND; gate resistor at Q501; D504 close to J501/Q501/VM loop. Mark external brake resistor specification at connector. |
| PB8 / FEEDBACK_I_H3 | Place U602 and R307 near MCU. No test pad or long stub between switch and MCU; boot-button path R1001 also kept short. |
| J601 / D601 | ESD device at connector, before signal-series resistors. D601 pin 5 is isolated FB_ESD_RAIL with C604; do not replace that net with 3V3. |
| USB_D± | 90 Ω differential target from the actual stack-up, matched pair with continuous ground; connector-adjacent ESD. Join duplicated USB-C A/B D pins without long stubs. |
| CANH/L | Paired routing, short protected branch to U801. R802 and JP801 enable 120 Ω termination only at a bus end. CAN_SHIELD is a separate drain provision. |
| SPI3 | Short SCK/MOSI branches; source resistors at U301. Each MISO resistor belongs near its sensor. Separate CS pull-ups remain fitted. |
| HSE_OSC_IN/OUT | Y301 and C308/C309 close and symmetric. Pads 1/3 are crystal; 2/4 case GND. Initial 10 pF caps assume roughly 2 pF stray for 7 pF load; validate oscillator. |
| TH701/702/703 | Map to U/V/W half-bridges respectively (NTC_PHASE_A/B/C). Thermal contact near representative MOSFET copper, electrically isolated from switching islands. |
| U601, U701 | Encoder magnetic/mechanical alignment first. IMU away from mounting stress, heat and inductors; no vias under its package; mark axes and orientation. |

Use six layers: signal/power–GND–signal–power–GND–signal/power, with 2 oz outer / 0.5 oz inner copper. Apply the detailed plan section 19 DRC baseline; external fabricator and part-availability validation are excluded from this workflow. Do not interpret generic KiCad default trace width/clearance as an approved 40 A routing rule. Use a dedicated current/thermal review for the pours, neck-downs, vias and connector solder joints; account for fine-pitch package clearances locally. No 40 Arms continuous claim follows from copper weight alone.

## Custom package controls

- **CSD88599Q5DC DMM0022A:** pad 1 upper-left, pad 22 upper-right in the footprint's default top view. Pad 27, including the thermal-via array, is **VM**. The exposed thermal surfaces can be electrically live; insulate a common heatsink/chassis. Pads 21 and 23–26 are NC.
- **CSD19531Q5A Q5A/DQJ:** pins 1–3 source, 4 gate, 5–8 drain; large copper land also drain/pad 5. Do not substitute a generic TDSON footprint with another functional pad arrangement.
- **TLV755 DYD0005A:** five leads plus an internally grounded thermal land, repeated pad 2. It is not the plain DBV SOT-23-5 footprint.
- **Wurth 74437349220:** 2.95 × 3.5 mm pads centered at ±2.725 mm. Observe the central 2.5 mm top-copper keepout. The footprint includes a rule area; do not remove it when importing.
- Custom models provide fabrication geometry, not verified STEP bodies. Use manufacturer dimensional drawings for height, pin-one and heatsink checks. Print land patterns 1:1 and compare to actual samples before ordering boards.
- Via-in-pad openings require the fabricator's filled/capped process or a reviewed alternative stencil/thermal implementation. Included paste segmentation is a starting manufacturer pattern, not approval of an arbitrary stencil thickness. Check soldermask dams, annular rings and assembly yield.

## Connector contract

| Reference | Pin assignment / restriction |
|---|---|
| J101 XT60PW-M | 1 GND, 2 VM. Mark polarity prominently; no reverse protection. External fuse/precharge required for initial tests. |
| J401 | 1 U/OUT1, 2 V/OUT2, 3 W/OUT3; solder-wire pads, not a logic connector. |
| J501 | 1 VM, 2 BRK_SW; external 10 Ω example, ≥250 W with specified heatsink and ≥500 J/5 s pulse capability. Both wires are bus-voltage conductors. |
| J601 | 1 3V3 output (≤25 mA), 2 GND, 3 A/H1, 4 B/H2, 5 I/H3, 6 NC. Inputs 0–3.3 V only. Do not inject power into pin 1. |
| J801/J802 | 1 GND, 2 CANL, 3 CANH, 4 shield/drain; no bus power. |
| J1001 Cortex SWD | 1 VTREF, 2 SWDIO, 3 GND, 4 SWCLK, 5 GND, 6 NC, 7 key/NC, 8 NC, 9 GND, 10 NRST. Remove/key pin 7 if required by the chosen cable. VTREF must not power the board. |
| J201 USB-C | Service only, 5 V; source must permit ≥500 mA for USB-only operation. No PD negotiation or automatic suspend load shedding. |

## Population and procurement

The historical A0 population list below is supplemented by six optional MLCC positions in P3. Use the active P3 schematic DNP flags for assembly:

- D101, R102/C107: measured VM clamp/cable damping options.
- R415/C413, R425/C423, R435/C433: phase RC snubbers.
- C414/C424/C434: op-amp feedback tuning capacitors.
- R608/R609/R610: fit only for compatible open-collector Hall inputs.
- R802/JP801: fit resistor and bridge jumper only at a CAN bus end.
- C207: optional USB shield coupling, pending enclosure EMC strategy.

The BOM records exact MPNs for package-specific active/power parts and sensors. Ordinary passives use explicit value/package/rating specifications in `Procurement`; blank MPN is a purchasing selection, not a missing footprint. Select reputable parts within these footprints before assembly:

- Current-sense/bias resistors: 0.1%, matched technology, ≤25 ppm/°C recommended; no casual E24 substitution of 28 kΩ/56 kΩ ratios.
- VM-connected resistors: ≥100 V working voltage and the stated power/package (R101 0.25 W); snubber resistor pulse capability selected after measurement.
- VM capacitors: stated 100 V rating; the P3 bank is 48 fitted 10 uF / 100 V X7S ceramics plus six DNP positions. Review **effective capacitance at DC bias**, temperature and ripple rather than nominal capacitance alone.
- Converter/LDO output capacitors: comply with each datasheet's effective capacitance and ESR range at operating voltage. Increase nominal capacitance within the same footprint if needed; recheck regulator stability when substituting.
- Crystal load and optional feedback caps: C0G/NP0. Do not substitute X7R for the oscillator load capacitors.
- Select switch variants that fit the specified TL3305A land pattern. Solder-wire pads and solder jumpers are PCB features; verify wire and mating-connector mechanics.

## Before fabrication release

Finish outline and mechanical fit, copper/thermal sizing, custom footprint inspection, and routing. Run PCB DRC including unconnected-net, clearance, courtyard and differential-pair checks; inspect ground returns and high-current loops manually. Check capacitor bias/ripple assumptions and internal via-in-pad/stencil geometry, then export fabrication and assembly outputs. Skip part-availability and external fabricator validation as requested. This schematic release does not include those later-stage approvals.
