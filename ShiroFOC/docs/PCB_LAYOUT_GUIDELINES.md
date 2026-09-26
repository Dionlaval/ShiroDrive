> **P1 update (2026-09-17):** follow [PCB_REVISION_LIST_P1.md](PCB_REVISION_LIST_P1.md) for the reclaimed top-side centre, four M3 corner mounts, parallel bridge/output rows and capacitor proposal.

> **Current placement (2026-09-19):** use [ShiroFOC_KiCad_P1](../ShiroFOC_KiCad_P1/ShiroFOC_KiCad.kicad_pro). [P1 notes](PCB_PLACEMENT_P1.md) supersede older placement coordinates and capacitor-replacement proposals. The original P0 project is retained.

# ShiroFOC PCB layout plan and guidelines

Date: 2026-09-16; revised to user mechanical/DRC constraints  
Basis: A1 connected drawing / A0 electrical design; KiCad 9.  
Status: placement and routing plan, not a routed-board or fabrication approval.

## 1. Design intent and priorities

Use this document alongside the [existing layout handoff](PCB_LAYOUT_HANDOFF.md), [design review](DESIGN_REVIEW_REV_A.md), [pin allocation](MCU_PINOUT_AND_INTERFACE_PLAN.md), and [firmware contract](FIRMWARE_BRINGUP_CONTRACT.md). The schematic/netlist defines connectivity; layout must not silently merge or change nets. Sheet-local aliases are recorded in `ShiroFOC_KiCad/outputs/net_name_aliases.json`.

- Four layers, **2 oz finished outer copper / 0.5 oz inner copper**, double-sided assembly.
- Scope: proceed with the existing part selections and supplied manufacturing limits. **Skip part-availability validation and external fabricator/assembler validation** in this layout workflow. Retain internal electrical, mechanical and DRC checks.
- Outline: compact **rounded square, no larger than 150 × 150 mm**. U601 is centred on the back; U301 and the MOSFETs are on top, with U301 offset from U601 to reserve space beneath U301 for decoupling and ADC parts.
- Default stack: **signal/power – GND – GND – signal/power**. Use broad outer-layer copper for motor power and local rails.
- Put compact analog networks and suitable decoupling on the underside near U301's corresponding pins. Bottom-side shunts are an option subject to the loop, thermal and assembly checks below.
- Prioritise: mechanical encoder alignment and cooling; bridge commutation loops; shunt sensing; gate drive; converter loops; analog references; interfaces; remaining signals.
- The 18–42 V operating range and 25/40 Arms objectives remain design targets. Trace width, copper weight and clean DRC alone do not establish a continuous-current rating.
- Keep the three phase cells geometrically similar, but do not lengthen a critical loop merely to achieve visual symmetry.

## 2. Stackup, ground and fabrication constraints

| Layer | Intended use | Rules |
|---|---|---|
| L1 / F.Cu | Main power stage, components, local power pours, signals | 2 oz finished copper; compact switch nodes; L2 provides signal reference. |
| L2 / In1.Cu | Continuous GND, 0.5 oz | Preserve under logic, analog and top-side interfaces. No general signal routing or power islands. |
| L3 / In2.Cu | Continuous GND, 0.5 oz | Preserve under bottom-side analog and signals. Stitch to L2 and outer GND locally. |
| L4 / B.Cu | ADC networks, decoupling, optional shunts, power reinforcement and signals | 2 oz finished copper; reserve quiet MCU region before allocating power copper. |

### Stackup selection

- Copper weights are fixed: **2 / 0.5 / 0.5 / 2 oz** from top to bottom. The inner planes provide reference/return continuity; do not assume they have the current capacity of the outer copper. No copper-weight or availability validation task is required.
- Prefer thin L1–L2 and L3–L4 dielectrics with the thicker core between the two ground planes. This improves local return coupling on both sides.
- Record the selected stackup identifier, board thickness, finished copper, dielectric thicknesses and impedance calculation in the PCB design notes before routing USB.
- Keep L3 as GND unless a placement/routing review demonstrates a real need for a power plane. Several unrelated voltage islands would fragment the bottom-side reference. If L3 changes, re-evaluate every bottom-side signal return; never route a sensitive signal across a reference-plane boundary.
- Use the self-contained DRC baseline in section 19, transcribed from the supplied screenshots where available. Additional project choices are labelled separately. Do not import 1 oz routing minima or require a fabricator-validation step.

### Ground and return paths

- Keep one electrically continuous GND system. Separate noisy and quiet circuits by placement and short return loops, rather than cutting an analog/digital ground moat.
- Establish a broad power-return corridor between bridge shunts, local capacitors, brake stage and DC input. Keep the MCU/ADC area outside that corridor. Ground-plane current distributes according to impedance; naming a region “quiet” does not keep power current out of it.
- Stitch L2/L3 together near signal layer transitions, IC decouplers, connector protection and local power returns. Put a ground-return via beside a signal transition where practical; never substitute a switch-node via for a ground-return via.
- Avoid rows of antipads forming slots across a signal return corridor. Inspect filled copper on each layer, especially around shunt and MOSFET via arrays.
- Keep continuous reference copper beneath SPI, USB, CAN logic and analog routes. Consider only **small, deliberate local plane clearances** beneath high-dv/dt switch islands where the device guidance or EMI assessment justifies them. No signal may cross those clearances. Do not blanket-remove ground beneath entire power-stage or converter regions.
- VM thermal vias must clear both GND planes. Source-above-shunt vias must also clear GND. A thermal via is electrically part of its pad net.

## 3. Mechanical floorplan and double-sided assembly

- Fix the AS5047P magnetic centre, magnet axis, air gap and rotating-part clearance first. Establish mounting holes, connector mating envelopes, heatsink, insulation and enclosure height on both sides.
- Use a rounded-square Edge.Cuts outline, width = height, **at most 150 mm per side**. Begin with an **80 × 80 mm trial floorplan and 5 mm corner radius** (project starting choices, not committed dimensions). Shrink or grow after establishing the revised edge-bulk/local-ceramic arrangement, four corner mounts and complete phase cells; choose the smallest practical square that preserves electrical, thermal and mechanical space. Never exceed 150 × 150 mm.
- Put the **magnetic sensing centre of U601 on B.Cu at the board geometric centre**; account for any package-to-sensing-centre offset and bottom-side orientation. Fix this location before placing the other circuits. The magnet is outward from the underside sensor, not through the PCB. Reserve only the actual underside component/rotating-part height clearance; do not exclude the top-side centre from placement.
- Put **U301 and Q401–Q403 on F.Cu**. Offset U301 laterally from the centre so its underside decoupling/ADC region does not physically overlap U601 or its underside assembly clearance. Determine the offset from both footprint courtyards and component clearances, not from an arbitrary fixed distance.
- Keep power switching, inductors and high-current paths away from the central encoder on both sides. Arrange the power cells toward an edge and the MCU toward their quiet side; use perimeter connectors. Do not route a motor-current shortcut through the encoder region. Keep optional bottom shunts beneath their phase cells and outside the central sensor envelope.
- Place the three half bridges near the phase-wire exit and DC-link bank. Place U301 with its gate-drive side facing the bridges and analog side facing the sense routes. Keep logic connectors toward the quiet region.
- Reserve underside areas under U301 for pin-local decoupling and ADC networks; reserve separate underside areas under bridge cells for optional shunts. Do not overlap these functions.
- Keep underside components out of mounting hardware, heatsink, insulation-pad compression and test-fixture contact areas. Maintain rework access and realistic component height clearances.
- Avoid placing an ADC resistor network directly beneath a hot inductor, MOSFET or shunt even if its XY coordinates look convenient.
- Account internally for bottom-side shunt retention during second reflow and the heavy top-side parts/process sequence. Check stencil aperture balance and solder wicking at power pads; no external assembler-validation gate is included.
- Use filled/capped via-in-pad only where the selected process supports it. Ordinary open vias in solder lands can drain solder; tenting alone is not equivalent to filled/capped via-in-pad.
- Add fiducials, tooling/panel clearances and visible polarity/axis markings on the required assembly sides. Keep test points accessible after the heatsink and connectors are installed.

## 4. DC input, bulk capacitors and bus measurement

P1 proposal: replace the large three-can row with local ceramic banks and edge-mounted bulk, after electrical sizing. See [P1 revision list](PCB_REVISION_LIST_P1.md); do not remove C101-C103 solely on nominal capacitance or appearance.

**J101, C101–C106, D101, R102/C107, VM divider and C108.**

- Route J101 to a broad VM/GND distribution with the bulk bank adjacent to the inverter. Keep outgoing and returning high-current paths close to reduce loop area; avoid long separated rails.
- Connect C101–C103 with comparable, low-resistance paths so one capacitor does not take most of the ripple. Keep their bodies away from MOSFET/shunt heat and provide pressure-vent clearance.
- Place small bus ceramics where current commutates, not merely beside the input connector. Bulk capacitors do not replace package-local ceramics.
- Keep DNP clamp and damping positions electrically short enough to be useful. A long branch to an optional TVS or RC network adds inductance. Preserve access for an external low-inductance capacitor bank.
- Connect voltage-divider pickup to the intended DC bus, away from phase and brake switching islands. Put the high-voltage resistor chain toward the bus and keep the divided, high-impedance node short and shielded by quiet ground.
- Preserve resistor-to-resistor voltage spacing and distance to nearby low-voltage copper; account for working voltage, transient envelope and contamination when setting clearance rules.
- Place the final ADC capacitor C108 near PA0/U301; route through the existing TMUX channel as drawn. Do not bypass the power-off isolation provided by the mux.
- Input polarity marking must be unambiguous: J101 pin 1 GND, pin 2 VM. Reserve strain relief and soldering access. Existing external fuse/precharge requirements remain in the design review.
- Verify bulk ripple and temperature in hardware: the present bank's nameplate total ripple rating is a possible operating-current limit, independent of PCB copper capacity.

## 5. Three half bridges and high-current copper

**Q401/Q402/Q403; phase U/V/W cells.**

- Place each MOSFET package, its local ceramics and shunt as one tightly coupled cell. Trace the physical loop: local VM capacitor → high-side device → low-side device → shunt → capacitor GND. Minimise enclosed area and inductance, not just individual trace lengths.
- C412/C422/C432 (1 µF) return to common **GND below the shunts**. C415/C425/C435 (10 nF) connect VM directly to each package's **source/PGND above its shunt**. Preserve this intentional distinction.
- Put the 10 nF package bypass directly at the relevant package terminals, ideally on the same side. Place the 1 µF capacitor to minimise the complete bridge/shunt loop; evaluate a bottom-side location only with its transitions included.
- Use short, broad pours for VM, phase and force paths. Avoid thin necks at pad exits, corner connections, via arrays and connector pads. Connect all designated power pads; do not rely on a single lead into a large pour.
- Use the second outer layer for parallel current paths where helpful, with distributed via arrays at both ends. A large lower pour connected through one tiny neck or a few remote vias contributes little.
- Size conductors using actual RMS/peak current, duty cycle, copper thickness, length, allowable drop and temperature rise. Calculate I²R loss and check terminal temperatures. Do not use a universal “amps per via” rule.
- Keep phase-node copper only as large as needed for current and heat. Avoid unnecessary overlap with sensors, analog networks, crystal and interface traces on other layers.
- Keep optional snubber R415/C413, R425/C423 and R435/C433 immediately beside their corresponding switching devices and return points. Preserve short pads for probing and later tuning.
- High-current SMD pads should use solid copper connections or specifically engineered thermal connections, rather than default narrow thermal spokes. Check solderability in the layout; treat through-hole connector heat balance separately.
- CSD88599 pad 27 and its thermal vias are **VM**, not GND. Its exposed metal requires an electrically verified heatsink interface; use suitable insulation for a shared heatsink/chassis. Follow the actual package drawing for NC and power pads. [TI CSD88599Q5DC](https://www.ti.com/product/CSD88599Q5DC).

## 6. Bottom-side shunts and Kelvin routing

**R416/R426/R436, 0.5 mΩ four-terminal shunts.**

Bottom-side placement is acceptable if it improves the total cell geometry and passes these checks; “plenty of vias” alone is insufficient.

- Place each shunt immediately below/adjacent to its own bridge return. Use a broad **source-side force via bank** into force pad 1 and a separate broad **GND-side force connection/via bank** from force pad 4. Follow the actual netlist if the footprint is rotated or flipped.
- Keep these two force conductors separate on **every layer**. Source-side copper must never touch a GND plane or common return before crossing the resistor. That would bypass the measurement.
- Distribute vias across the force-pad connection width for current spreading. Check copper between holes, barrel plating, finished hole size, solder wicking, array temperature and both top/bottom neck-downs. Include the added through-board inductance in the commutation-loop review.
- Pads 2 and 3 are the dedicated sense connections. Start a separate trace at each sense pad. Do not merge either into adjacent force copper or share its power vias. Preserve any intentional net separation in the footprint/netlist.
- Route SENSE_P and SENSE_N together along the same quiet corridor, with similar exposure and as few transitions as practical. If a transition is needed, use one dedicated via per sense trace, adjacent to each other and away from force-via current crowding.
- The negative Kelvin trace is **not a spare GND connection**, even when near ground potential. Route it all the way to its matching amplifier network.
- Keep pairs away from gate loops, phase copper, buck inductors and brake switching. Avoid long parallel runs with these nets. A 90° crossing is only a fallback and does not remove capacitive coupling.
- Prioritise a small pickup loop and balanced routing over exact length matching; do not add serpentine tuning to low-frequency analog sense pairs.
- Allow cooling copper on the force terminals per the shunt manufacturer's guidance, while preserving the sense geometry. Do not pour copper across the resistive element or sense isolation.
- At 40 Arms, 0.5 mΩ dissipates 0.8 W; pulse and terminal-temperature limits still apply. Keep shunt heat away from the IMU and gain resistors, and consider bottom airflow/enclosure clearance.
- Review the complete top-to-bottom loop before accepting this placement. If it produces excessive inductance, temperature or assembly difficulty, move the shunt beside its bridge on top.

## 7. Gate drive, bootstrap and hardware protection

**U301 driver section, gate resistors/pulls, C411/C421/C431 and SCREF network.**

- Place each series gate resistor at the MOSFET gate terminal so the resistor-to-gate segment is very short. Keep gate pull-downs local to their gate/source connection.
- Route gates short with a nearby appropriate return. High-side gate return is the corresponding OUT/phase node. Keep the OUT connection to U301 short and take it from the device region, not the far end of the motor connector trace.
- U301 has shared ground references in this circuit: place its driver ground/decoupling toward the local bridge-return region, minimising common-source inductance. Do not invent a separate low-side source pin or connect U301 GND to a source-above-shunt net to imitate a dedicated Kelvin driver.
- Keep gate routing away from Kelvin pairs and amplifier inputs. Avoid vias if practical; where necessary, minimise the entire gate/return loop rather than routing one conductor on a long detour.
- Use adequate gate width for pulse current and low inductance; gate nets do not need motor-current-sized pours. Avoid unnecessarily large copper that couples switching noise.
- Bootstrap capacitors connect **BOOT to the matching OUT**, never to GND. Place at the driver pins with short connections, away from analog inputs. Treat their pads/traces as moving with the phase potential.
- Keep VCC decoupling directly at driver supply/ground pins. Do not feed a chain of decouplers through one long thin trace or shared ground via.
- Put SCREF R310–R312/C314 close to U301 with quiet local ground; keep switch-node and gate copper away. Preserve the distinction between VDS protection and shunt-based current measurement.
- Provide accessible gate/source and phase/bus probe locations with short return access. Use differential probing for floating high-side nodes; keep large test-pad stubs off critical loops.
- Validate gate-source overshoot/undershoot, drain overshoot, ringing and dead time at increasing current. Final gate/snubber values are measurement-dependent.

## 8. U301 MCU supplies, ADC networks and crystal

### Decoupling and underside placement

- Place each local capacitor next to the power pin it serves. Judge the full pin → capacitor → ground return loop, including vias, rather than the component's distance to the centre of U301.
- Bottom-side placement directly under the relevant peripheral pin is preferred where it gives a short loop. Use nearby supply and ground vias, with the ground via immediately beside the capacitor ground pad. Avoid a remote shared via serving many capacitors.
- Do not crowd the exposed-pad thermal-via array with bottom parts or via escapes. Respect solder-process clearances. Keep gate/switch routing out of the underside analog area.
- If a same-side capacitor has a materially shorter high-frequency loop, keep it on top. Compactness is secondary to decoupling effectiveness.
- Place bulk local capacitance nearby after the pin-local ceramics. Give VDDA/VREF filtering and C303–C306 their own short quiet branches; keep R301/R302 near the loads they filter.
- Preserve the external 3V3 bypass wiring to REGIN and the existing STSPIN supply connections. Do not treat REGIN as a buck feedback input. [STSPIN32G4 datasheet](https://www.st.com/resource/en/datasheet/stspin32g4.pdf).

### Current amplifiers and other ADC channels

- Put R417–R419 / R427–R429 / R437–R439, R410/R420/R430 and R441–R443 next to their actual op-amp pins, preferably underneath the corresponding analog edge of U301.
- Keep feedback resistors and DNP feedback capacitors immediately around their amplifier pins. Make the feedback loop short; route amplifier output away from the sensitive input until it reaches the intended connection.
- Keep each channel compact with comparable thermal surroundings. Match resistor specification and technology; avoid placing one ratio resistor over hot copper and its partner over cool ground.
- Route VREF bias quietly, with local decoupling as drawn. Do not use its path for digital load currents. Keep input pairs separate from amplifier outputs and reference distribution.
- Put final RC filtering at the receiving ADC pin. Temperature sensors themselves stay at the heat sources; their filter capacitors/pull networks can occupy the MCU underside.
- Preserve component values and RC topology. Additional filtering changes acquisition settling and fault response and requires schematic/firmware review.

### Crystal, reset and boot

- Keep Y301 and C308/C309 close to PF0/PF1, preferably on the same side as U301. Keep oscillator traces short, compact and separated from gates, inductors, USB and clocks.
- Pads 1/3 carry the crystal signal; pads 2/4 are grounded case pads. Give load-cap grounds short local returns; keep unrelated routing out of the oscillator area on adjacent layers.
- Do not add oscillator test pads or long stubs. Preserve load-capacitance assumptions and verify startup over supply/temperature after assembly.
- Place PB8 pull-down R307 near U301 and U602 nearby. Keep the PB8/common-mux route short with no test stub. Keep reset pull/filter and boot controls short and away from power switching.

## 9. STSPIN VCC buck and auxiliary 5 V converter

### VCC converter around U301, L301 and D302

- Place the input bypass, switching pins, diode and inductor as a compact block on the driver/power side of U301. Keep the switching loop out of the ADC/crystal region.
- Put local input and output capacitor returns near the relevant driver ground connection, with short vias into the ground planes. Keep VCC_SW small and away from sense/SCREF/reference routing.
- Follow the ST layout example for the diode, inductor, exposed-pad ground connection and thermal spreading; retain the selected inductor's footprint keepout. The existing 22 µH choice still needs hardware startup/ripple verification. [ST AN5953](https://www.st.com/resource/en/application_note/an5953-stspin32g4--buck-converter-design-guidelines--stmicroelectronics.pdf).

### LMR36510 5 V supply, U201

- Place the high-frequency input ceramic directly across VIN/PGND with a tiny switching-current loop. Keep IC, bootstrap capacitor, inductor and output capacitor grouped on the same side where possible.
- Keep the switch node compact. Sense output voltage after the inductor at the output-capacitor region; route FB back through quiet copper and place the divider near FB.
- Keep feedback and enable/high-impedance nodes away from the inductor and SW. Return the divider to the local quiet IC ground region, without sharing an input switching-current neck.
- Connect the exposed pad and GND correctly for both heat and electrical return. Preserve continuous reference copper except any narrowly justified switch-node keepout.
- Keep converter heat away from the IMU and analog gain networks. Check inductor clearance, saturation margin and the Wurth footprint's central top-copper keepout. [TI LMR36510 datasheet](https://www.ti.com/lit/ds/symlink/lmr36510.pdf).

## 10. USB/buck power mux and 3V3 LDO

**U203 TPS2121, U204 TLV75533PDYDR.**

- Arrange USB 5 V and buck 5 V into separate short input paths, then a short 5V_SYS path to the LDO. Keep all nets distinct; copper must not bypass mux reverse blocking.
- Put each mux input capacitor at its respective input and the output capacitor near OUT. Route current-carrying pins broadly; place threshold, current-limit and timing components near their pins and away from switch-node copper.
- Preserve USB priority and power-off behaviour from the schematic. Provide test access to each input, 5V_SYS and 3V3. [TI TPS2121 layout guidance](https://www.ti.com/lit/ds/symlink/tps2121.pdf).
- Place LDO input/output capacitors close to U204 with short ground loops. Use the **DYD** footprint and repeated pad 2/GND thermal land; do not replace it with a plain five-pin SOT23 footprint.
- Provide ground copper and thermal vias for the LDO while keeping it outside the hot bridge area. Review the documented approximately 0.49 W nominal allowance and 0.624 W fault allowance against actual enclosure temperature.
- Distribute 3V3 with short adequate-width branches; feed analog filtering from a quiet branch. Do not route sensor supply through a narrow CAN/transceiver supply neck.

## 11. Brake chopper and independent overvoltage circuit

**Q501, U501, D501–D504, U502, J501 and R506–R510.**

- Put Q501 and J501 near the power bus. Keep the VM → external resistor connection → Q501 → GND current path compact on the board, with a broad return to the DC-link region.
- Place D504 close to the connector/switch/VM loop so lead-inductance recirculation does not traverse a long board trace. Keep BRK_SW copper small and away from analog, feedback and communications.
- Place U501 near Q501, its decouplers directly across its supply/GND, and the gate resistor/GS clamp near Q501. Route a dedicated low-current source return from Q501 source region to the driver ground, without sharing a long high-current source neck.
- Q501 pads 1–3 are source, 4 gate, 5–8 and the large drain land are drain. Thermal copper/vias on the drain are BRK_SW, not GND; limit unnecessary capacitive coupling.
- Put U502 and its reference/filter/hysteresis network in quiet copper, outside the switching loop. Route VM pickup from the bus and keep the three series high-voltage resistors' clearances and the comparator input node compact.
- Preserve diode-OR wiring and hardware brake operation during MCU reset. Keep control pull-downs local and provide comparator/control test access without long sensitive-node stubs.
- Mark J501 as VM and BRK_SW; both wires are bus-voltage conductors. Provide strain relief and twisted-lead routing space. Resistor cooling belongs off-board; do not put its heat into the logic region.

## 12. Position feedback: AS5047P, external Hall/ABI and TMUX1574

- Fix U601 on the **back side with its sensing centre at the rounded-square board centre**, using mechanical magnet geometry, package sensor-centre offset and bottom-side orientation. Verify air gap, magnet dimensions, runout and tolerances against the encoder guidance before fixing the outline.
- Keep inductors, high-current conductors and magnetic/ferromagnetic hardware away from the sensor. Ground copper is not a shield against low-frequency magnetic fields; reduce loop area and increase physical separation.
- Put encoder supply capacitors close to the correct supply pins. Respect the existing supply mode and do not connect internally regulated pins differently for routing convenience.
- Route ABI signals from U601 through the selected series components to U602, then short paths to TIM4 pins. Avoid switch-node coupling that could create false counts. Preserve source termination positions and hardware default pulls.
- Place U602 near the MCU; keep its fourth-channel VBUS analog path away from the clock/ABI branches where practical. Keep PB8 particularly short as described above.
- Put D601 at J601, ahead of downstream signal resistors, with a short ground discharge path. Its pin 5/C604 net is **FB_ESD_RAIL**, not 3V3; keep that isolated rail compact.
- Keep optional Hall pull-ups accessible for population changes. Mark J601's 0–3.3 V input and 3V3-output contract. Route cable-related ESD currents near the connector rather than through the MCU region.

## 13. Shared SPI and BMI323 IMU

- Place SCK/MOSI series resistors at U301; route a compact shared bus with short branches to the two slaves. Avoid an unnecessarily large star or long dangling branches.
- Put each MISO series resistor near the sensor that drives it. Keep chip-select pulls at their receiving devices and ensure neither branch is left floating during reset.
- Route SPI over uninterrupted ground and away from power loops. Exact length matching is less important than short branches, continuous returns and signal integrity at the selected clock rate; avoid ornamental meanders.
- Place U701 in a quiet, mechanically stable region, away from board edges that flex, screws, connectors, breakaway tabs, inductors and hot parts. Align and mark its axes relative to the board/mechanical assembly.
- Place IMU supply decoupling beside its pins, with short ground connections. Keep INT1/INT2 away from noisy copper and route them over ground.
- Do not put through vias in the BMI323 package footprint area. Maintain Bosch's land, soldermask and paste requirements; avoid solder beneath unintended package areas. Check panel separation and screw loading for strain. [Bosch BMI2xy/BMI3xy handling and mounting guidance](https://www.bosch-sensortec.com/media/boschsensortec/downloads/handling_soldering_mounting_instructions/bst-mis-hs001-2.pdf).
- ABI provides timer-based control feedback; shared SPI remains available for sensor/configuration traffic. Layout still needs clean digital edges, and firmware retains the documented per-device SPI mode and scheduling requirements.

## 14. Phase temperature sensing

**TH701/TH702/TH703 and their ADC filters.**

- Associate the sensors with U/V/W explicitly in PCB text and assembly documentation. Place each near representative MOSFET thermal copper, with similar thermal coupling across phases.
- Keep thermistor terminals electrically isolated from VM/phase copper. Thermal proximity does not authorise a copper connection to a hot electrical node.
- Prefer short, quiet sensing paths; place ADC-side capacitors near U301. Route away from gate/phase edges and do not share the sense ground return with a high-current neck.
- Check that bottom shunts or a nearby converter do not dominate one temperature reading. Allow for lag between package junction, copper and thermistor when setting protection thresholds.

## 15. CAN interface

**U801, D801, J801/J802, termination R802/JP801.**

- Place protection at the cable entry and U801 nearby. Keep CANH/CANL paired, with similar geometry and a short branch from the bus path to the transceiver.
- For two pass-through connectors, maintain a short continuous bus path and minimise the transceiver/termination stub. Put selectable termination near that path and retain access to JP801.
- Provide short, broad ESD return connections. Keep CAN_SHIELD/drain separate as drawn; do not accidentally merge it into GND by a mounting hole or copper pour.
- Place transceiver decoupling at the supply pins. Keep standby pull-up near U801; route TX/RX/STB over ground and away from the inverter.
- Review trace impedance/geometry for the selected CAN-FD rate and cable arrangement; avoid long stubs. A 120 Ω termination value is not a reason to serpentine a short on-board pair.

## 16. USB-C service connector and CP2102N

**J201, U202, U901 and local supply/VBUS components.**

- Put ESD protection adjacent to USB-C so the pair encounters protection before entering the board. Keep the discharge return short and out of the crystal/ADC region.
- Join duplicated USB-C D+/D− contacts with minimal stubs, then route a **90 Ω differential target** using the actual 2 oz stackup and fabrication calculator.
- Keep pair geometry consistent and routes reasonably matched, over continuous ground. Avoid layer changes; if necessary, transition both together with nearby ground-return vias. Do not cross plane voids or route next to phase copper.
- Place U901 near the connector/protection, with its decoupling and VBUS detection divider local. Keep UART source paths short and separate from high-current power input routing.
- Keep CC resistors local to the connector and preserve the service-only USB power configuration. USB shield/C207 remains the separate optional coupling network in the schematic.
- Check connector shell pads, edge overhang, insertion force, cable clearance and solder inspection access on both sides. Do not let a screw or enclosure silently bypass the intended shield connection.

## 17. SWD, buttons, LEDs and test access

- Put J1001 where a keyed cable can be attached with the heatsink installed. Mark pin 1; VTREF is sense-only. Keep SWCLK/SWDIO short, referenced to ground and away from gate/phase routing.
- Place reset/boot buttons where they can be operated safely during bench work. Keep their pin-local pulls near U301 and avoid long antenna-like traces on reset/boot nets.
- Keep LEDs visible and their switching currents out of VREF/ADC ground branches.
- Provide accessible test points for VM/GND, both 5 V sources, 5V_SYS, 3V3, VCC, current-amplifier outputs, VBUS_SENSE, brake command and reset. Place a nearby ground pad for low-voltage probing.
- Give high-voltage and switching test points suitable spacing and clear labels. Avoid exposed probes near the rotating magnet or heatsink. Do not add long stubs to PB8, crystal, gate or Kelvin input nets merely for test convenience.

## 18. Routing workflow and acceptance checks

### A. Before placement is frozen

- [ ] Fix outline, mounting, magnet position, heatsink/insulation and both-side height envelopes.
- [ ] Record the fixed 2/0.5/0.5/2 oz stack, dielectric geometry, assembly assumptions and via treatment; use section 19 without an external validation gate.
- [ ] Confirm square outline ≤150 × 150 mm, centred bottom encoder, top MCU/MOSFETs and nonoverlapping underside MCU/sensor regions.
- [ ] Establish net classes: motor force/power, switch nodes, gates/bootstrap, Kelvin analog, low-voltage analog, logic and USB differential. Set manufacturing minima separately from current/voltage design rules.
- [ ] Define operational/transient clearance requirements; size power copper/via arrays from current and thermal calculations, not generic track defaults.
- [ ] Place one complete phase cell and review its top/bottom current loop before replicating it.
- [ ] Reserve the underside MCU analog region and converter keepouts; inspect pad-net mappings for live thermal lands.

### B. Routing order

1. Bridge ceramics, shunt force connections and gate/bootstrap loops.
2. Kelvin pairs and pin-local analog/decoupling networks; adjust placement if these cannot be short and quiet.
3. VM/phase/GND distribution, brake loop and thermal copper, preserving the reserved quiet corridors.
4. Both buck converters, mux/LDO, reference distribution and voltage/temperature filters.
5. Encoder ABI/mux, SPI, USB, CAN, SWD and remaining control signals.
6. Ground stitching, test access and silkscreen; refill all zones and inspect every layer.

### C. Before fabrication outputs

- [ ] ERC and PCB DRC pass; no unconnected pads, accidental shunt bypasses, orphan copper or unexplained exclusions.
- [ ] Manually trace each commutation loop, gate return, Kelvin pair and converter feedback path; DRC cannot prove these are good.
- [ ] Check both ground planes for slots created by via arrays, keepouts and power antipads; verify reference continuity for both outer layers.
- [ ] Verify force-path losses, via/connector temperature, shunt heating, LDO thermal budget and heatsink insulation with documented assumptions.
- [ ] Verify footprints and actual orderable packages, all pad/thermal-net assignments, bottom-side mirroring, soldermask, paste and assembly clearances.
- [ ] Inspect 3D/mechanical fit including underside parts, magnet, mating cables, screws and heatsink; mark unverified generic model dimensions.
- [ ] Review BOM/CPL rotations and double-sided assembly process, fiducials and test-fixture access; keep DNP options identifiable.
- [ ] Export and independently inspect Gerbers, drill files and assembly drawings. Check exported dimensions, layer assignments and impedance calculations against the intended rules; external manufacturer validation and stock checks are excluded.

### D. Hardware evidence needed after assembly

Measure low-voltage supplies and power switchover first, then current-sense offset/noise, gate waveforms, bus overshoot and protection/braking at controlled energy. Raise current progressively while checking MOSFETs, vias, shunts, connectors and bulk-capacitor temperatures/ripple. Record any required gate/snubber/filter changes in the schematic as well as the PCB.

## 19. DRC setup and saved layout rules

This is the rule sheet to use when setting up KiCad Board Setup. **All dimensions below are mm.** The supplied screenshots are the source of the manufacturing values; no new fabricator validation or part-availability check is required. Values labelled **project choice** are design margins, not quoted capabilities. These settings are documented here; this Markdown edit does not apply them to a PCB file or claim a DRC pass.

### 19.1 Screenshot limits retained for reference

| Item | Supplied value | Interpretation for this board |
|---|---|---|
| 2 oz multilayer track width / spacing | 0.15 / 0.15 | Use the screenshot's **multilayer** row. Its 0.16 / 0.16 row is for two-layer boards. |
| Multilayer minimum drilled hole | 0.15 | Available limit, not the routine drill choice. Screenshot notes added cost at 0.15. |
| Minimum via drill / copper diameter | 0.15 / 0.25 | 0.05 radial annulus; avoid this absolute minimum in normal layout. |
| Preferred minimum via drill | 0.20 | Screenshot also prefers diameter at least 0.15 larger than drill. |
| Via cost note | 0.20/0.25 drill with diameter below 0.45 costs more | Use 0.45 diameter or larger for ordinary small vias. |
| Via hole-to-hole spacing | 0.20 | Treat as drilled-hole edge-to-edge spacing, not centre pitch. |
| Through-hole pad hole-to-hole spacing | 0.45 | Keep separate from the via-to-via limit. |
| Through-hole size tolerance | +0.13 / −0.08 | Account for fit of connector leads; this is not a track-clearance setting. |
| Press-fit hole tolerance | ±0.05 with stated process restrictions | No press-fit fit specification is assumed for this board. |
| Drilling upper size | 6.3 | Screenshot states holes at/above 6.3 are routed. Prefer simple round mounting holes below this boundary. |

Evidence: user screenshots dated 2026-09-16 at 23:53:32 (drilling), 23:54:15 (vias), 23:54:32 (hole spacing), and 23:54:58 (tracks). Those images do not specify dielectric thickness, soldermask web, soldermask registration or copper-to-edge clearance; the choices below must not be attributed to them.

### 19.2 Board Setup → Design Rules → Constraints

| Setting | Saved project baseline | Basis / use |
|---|---|---|
| Minimum copper clearance | **0.15** | Screenshot 2 oz multilayer floor; use larger class clearances below. |
| Minimum track width | **0.15** | Fine-pitch escapes only; default signal width 0.25. Apply same conservative floor to inner copper features even though inner layers are 0.5 oz planes. |
| Minimum connection width | **0.15** | Project choice to catch narrow zone slivers; does not size power necks. |
| Minimum through-via diameter | **0.45** | Project choice above absolute capability limit. |
| Minimum through-hole/via drill | **0.20** | Preferred drill from screenshot; ordinary via 0.30 drill. |
| Minimum via annular width | **0.10 radial** | Project choice. Check `(diameter − drill)/2`; both presets below comply. |
| Minimum hole-to-hole clearance | **0.20** | Via-to-via base floor. Add 0.45 for pairs involving through-hole component pads, as below. |
| Copper-to-hole clearance (non-connected copper) | **0.25** | Project choice; plated-pad copper intentionally attached to its own hole is exempt. |
| Copper-to-board-edge clearance | **0.50** | Project choice for routed rounded-square edges; no V-score assumption. |
| Silkscreen minimum text height / stroke | **1.0 / 0.15** | Project readability choice. |
| Silkscreen clearance to exposed pads | **0.20** | Project choice; keep polarity/reference markings legible. |
| Blind/buried vias and microvias | **Do not use** | Through-via-only baseline. |

- Set a pair-specific hole-clearance rule of **0.45** whenever either drilled item is a through-hole component pad; retain **0.20** for via–via pairs. This conservatively covers mixed pad–via pairs too. If pair-specific rules are not implemented, use a global 0.45 rule until they are; do not silently accept 0.20 between component holes.
- For equal 0.30 drills, a 0.20 edge spacing needs at least **0.50 centre pitch**. Copper clearance between different-net via pads can require a larger pitch: 0.60 pads at 0.20 copper clearance need **0.80 centre pitch**. Apply the stricter rule.
- Standard through-via preset: **0.60 diameter / 0.30 drill**. Compact fanout preset: **0.45 / 0.20**. Power arrays use calculated numbers of suitably sized vias; neither preset has an assumed current rating.
- Existing footprint-embedded thermal vias must be checked against these rules. A smaller legacy via is a discrepancy to resolve, not a reason to lower the whole-board baseline. Any footprint-specific exception must identify the pad, geometry and reason explicitly.
- Retain footprint-specific paste segmentation and pad geometry. Start ordinary soldermask expansion at **0.05 per side** and minimum mask web at **0.10** as project choices; inspect fine-pitch/QFN packages individually and record any intentional merged opening or local override. Do not resize electrical lands just to satisfy a generic mask preference.

### 19.3 Net classes and routing presets

Global minima are manufacturing floors; net classes below express intended routing. Pad escapes may need local rules, but long routes should return to their class width immediately after escape.

| Class | Track-width preset | Different-net clearance | Additional requirement |
|---|---|---|---|
| Default logic / SWD / SPI / UART | **0.25** | **0.20** | Short pin escape may use 0.15 width/clearance locally. |
| Kelvin sense / ADC / reference | **0.20** | **0.20** | Paired quiet routing; target ≥1.0 separation from switching copper where space allows. |
| Gate drive | **0.40** | **0.20** | Short resistor-to-gate route; larger clearance to unrelated switching/power nets below. |
| Low-voltage 3V3 / 5V / VCC | **0.50** initial preset | **0.20** | Widen for actual branch load and drop; pin-local decoupling loop takes priority. |
| VM / OUT1–3 / BRK_SW / BOOT1–3 | **Pours or purpose-sized tracks** | **0.50 target to unrelated nets** | Project noise/spacing target; narrow package-local gaps need documented local rules ≥0.15. BOOT floats with OUT; use actual voltage difference when judging insulation. |
| Shunt force / bridge GND return | **Calculated pours, no default current width** | **0.20 floor; 0.50 to unrelated control copper preferred** | Do not reclassify all GND as a special current route; use local geometry/rule areas and manual loop review. |
| CANH/CANL | **0.25 initial routing preset** | **0.20** | Paired short routing; preserve bus topology and termination. |
| USB D+/D− | **Impedance-derived width and gap** | **0.20 to other nets; 0.15 absolute interpair-gap floor** | 90 Ω differential target; use actual dielectric geometry and 2 oz copper. |

- The 0.50 power-net target is a project layout margin, **not an isolation certification or a claim that every package has that pin spacing**. Keep wider spacing outside package escapes and around probe/connector areas.
- USB width/gap cannot be honestly fixed from copper weight alone. Save calculated values once the dielectric stack is entered; retain ≥0.15 track width/gap. If 90 Ω cannot be achieved within those limits, adjust dielectric geometry/routing geometry rather than assuming 0.15/0.15 produces 90 Ω.
- Use **≤0.50 USB intra-pair length mismatch** as a conservative project routing target, with matched via count and no deliberate stubs. This is a project choice, not a quoted protocol maximum. Avoid unnecessary meanders on an already short pair.
- Make local higher-clearance rule areas around the encoder, ADC networks, crystal and switching islands where useful. DRC copper clearance alone cannot detect magnetic interference or a poor return path.

### 19.4 Mechanical and connectivity checks

- Four enabled copper layers with **2 / 0.5 / 0.5 / 2 oz**; both inner layers assigned GND.
- Edge.Cuts forms one closed, non-self-intersecting rounded square with equal width/height and maximum **150 × 150** bounding dimensions. Corner radius is chosen with the final mechanics; 5 is the starting preference.
- U601 is on B.Cu with its sensing centre at the outline centre; U301 and Q401–Q403 are on F.Cu. Treat these as explicit placement checks, not capabilities of generic electrical DRC.
- MCU underside component courtyards must not overlap the encoder/magnet envelope. Courtyard checks work per side; separately check through-board height, magnet and heatsink envelopes in the mechanical view.
- Enable shorts, clearance, minimum width, annular ring, drill spacing, edge clearance, courtyard overlap, unconnected items and schematic/PCB parity checks. Review rather than globally suppress footprint-library differences for deliberate local custom footprints.
- Refill zones before every final DRC run. Resolve every error and triage warnings individually; save a report with any narrowly justified exceptions.
- Inspect source-side force vias on all four layers: **no GND connection before the shunt**. Check that sense pads use their dedicated traces and never join force pours. These are mandatory manual checks even if the netlist/DRC is clean.
- This stage does not run sourcing checks or request fabrication/assembly sign-off. It still checks the design's own dimensions, connectivity, current paths and exported artwork.

## 20. Source and interpretation notes

The reference designators, values and net distinctions above come from the current local schematic, BOM and linked release documents. Placement choices such as two inner ground planes and underside analog grouping are this board's engineering plan; they are not claims that a manufacturer has approved this board. Linked manufacturer guidance supplies package/converter/interface constraints. Where a manufacturer document conflicts with a generic placement preference, resolve the specific device requirement before routing that block.
