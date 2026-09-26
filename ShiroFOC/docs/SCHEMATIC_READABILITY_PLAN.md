# ShiroFOC schematic readability review and redraw plan

Status: implemented as A1-Drawing on 2026-09-16. The assessment below records the original A0 problems. See [completed redraw review](SCHEMATIC_REDRAW_REVIEW.md) for the final sheet organization, verification and remaining scope.

## Assessment

The current schematic communicates a netlist rather than circuit operation. The previous readability sign-off was inadequate: absence of overlaps and a clean ERC are not sufficient to make a schematic understandable. Presentation readiness must be reopened; the existing electrical checks remain useful as the baseline for a redraw.

Inspection covered all 11 rendered pages and the native generator. There are **731 global labels**, **719 short wire segments**, and **zero junction objects**. The serializer unconditionally adds a global label to every connected component pin. All ten circuit pages use A2, although many contain only a small amount of circuitry. Scaling component positions apart further increases whitespace without improving topology.

### Critical findings

1. **Actual current and signal paths are invisible.** A reader must match names to discover that two resistors form a divider, a capacitor decouples an IC, or a resistor lies in series with a signal. A divider should visibly look like a divider.
2. **Local and external connections look identical.** An internal regulator feedback node receives the same global-label treatment as a signal crossing the project. Sheet boundaries and circuit boundaries have no useful visual meaning.
3. **Support parts are detached from their ICs.** On the power page, regulator capacitors, inductor, feedback resistors and mux threshold dividers are independent islands. CAN termination is not drawn as a branch across CANH/CANL.
4. **Symbols emphasize package pins rather than function.** STSPIN is one large box ordered largely by pin number; the current amplifiers are invisible inside it. The dual MOSFET box does not show a half-bridge. Repeating the same net label on each power lead obscures the topology.
5. **Subsystems are divided at unhelpful boundaries.** USB connector/protection and USB-UART bridge occupy different pages. The two SPI peripherals are separated, so their shared bus is not visible. Test points occupy an entire page instead of annotating the circuits they measure.
6. **Page size masks poor composition.** Large empty A2 regions coexist with tiny pin text. Reducing everything proportionally would worsen readability. The circuits need to be recomposed at normal symbol/text sizes.
7. **The overview is only an index.** Empty sheet boxes do not explain power distribution, communications, feedback selection or motor control.
8. **Important electrical distinctions require prose to reconstruct.** The two different local DC-link capacitor returns, Kelvin shunt terminals, brake OR circuit and feedback-mux/VM dependency should be evident in the drawing itself.

## Drawing standard

- Use real orthogonal wires for connections within a functional block. Place dots at connected branches; crossings without a dot must remain visibly unambiguous. Avoid four-way intersections.
- Arrange signal flow mainly left to right, positive supply above, ground below. Show vertical shunt capacitors and pull resistors and horizontal series parts when that makes their role apparent.
- Use normal power/ground symbols for common rails. Reserve hierarchical ports for sheet interfaces; use local labels sparingly for genuinely distant connections on a sheet. Annotate a continuous named wire once instead of applying a global label at both ends of every part.
- Use named sections with short purpose/setting notes. Group boundaries should be whitespace and headings; draw a light enclosure only where it explains a real functional or package boundary.
- Aim for A4 landscape for simple modules and A3 for dense power/control pages. Retain normal readable text, typically 1.27–1.5 mm for references/values/net names. Do not shrink text to force a page-count goal.
- Put decoupling at the supply pin or in a clearly connected, adjacent supply group. Put feedback and compensation components beside the IC pins they serve.
- Draw test points as taps on the measured net. Keep only spare GPIOs and genuinely stand-alone service access in a small debug section. Preserve the prohibition on a PB8/BOOT0 test stub.
- Keep DNP parts in their circuit position, with native DNP marks and a short option note. Do not move them into a separate component inventory.
- Keep lengthy ratings and commissioning instructions in the review/handoff document; retain concise circuit-specific notes near their components.

## Proposed sheet organization

Target approximately **10 sheets including the overview**. Page count is secondary to readable complete circuits; retain an additional current-sense page if the three phase blocks will not fit legibly.

| Proposed sheet | Connected functional groups | Format target |
|---|---|---|
| System overview | Wired sheet interfaces showing VM distribution, control-power tree, MCU/peripheral buses and feedback/motor connections | A3 |
| Battery / DC link | XT60 to VM rail; capacitor bank in parallel to GND; bleed and optional damping/clamp branches; visible VM divider | A4/A3 |
| Auxiliary supplies | Complete LMR36510 buck; USB/battery source mux; 3V3 LDO; connected threshold and feedback dividers | A3 |
| MCU core / debug | STSPIN digital/power units, clock, reset, boot, SWD and local decoupling; grouped GPIO ports | A3 |
| Three-phase inverter / current / temperature | Three matching phase rows containing half-bridge, local bypass, shunt, amplifier and associated NTC block; gate-driver unit alongside | A3, split if needed |
| Brake chopper | Visible VM-to-resistor-to-MOSFET-to-GND power path; driver/gate network; OV comparator and diode-OR command circuit | A4/A3 |
| SPI sensors | AS5047P and BMI323 on a visibly shared SCK/MOSI/MISO bus, separate chip selects, MISO resistors and decoupling | A3 |
| External feedback / selection | Connector, ESD, input resistors/pull-ups, three selector channels to MCU; fourth channel visibly dedicated to VM isolation | A4/A3 |
| CAN | TX/RX/STB interface, transceiver, supply decoupling, series links, ESD, end termination and both connectors | A4 |
| USB service | USB-C connector/CC, ESD, CP2102N, VBUS divider, reset/bypass capacitors and UART interface | A4/A3 |

Move the existing SWD/boot circuitry into the MCU page and distribute test points to their owners. Move the USB connector/ESD/CC parts onto the bridge page; pass raw USB VBUS to the auxiliary-power page through an explicit interface. Move BMI323 onto the SPI-sensor page. Move the three NTC circuits beside their phase channels or onto a dedicated analog page if needed. Preserve reference designators when moving parts.

## Circuit-specific redraw details

### CAN — first implementation example

Place MCU-side TX/RX/STB ports on the left, U801 in the center, and J801/J802 on the right. Draw CANH/CANL continuously through their respective 0 Ω links to the connectors. Branch D801 to the pair and ground. Draw R802 and JP801 as a series branch directly across CANH/CANL. Attach R801/R805 pull-ups to their actual signal wires and C801/C802 to U801's supply. Mark termination as an end-node option. The complete bus path should be understandable without looking up any net names.

### 5 V buck and source mux — second implementation example

Draw VM entering the input capacitors and U201 VIN. Draw SW to L201 to 5V_BAT, with output capacitors dropping to ground. Place the bootstrap capacitor physically between BOOT and SW on the drawing. Draw R201/R202 as a divider from output to ground, with its midpoint returning visibly to FB. Connect the enable and VCC bypass circuits locally.

Place the TPS2121 next in the power flow. Show 5V_BAT and USB as two distinct incoming supplies, then 5V_SYS leaving for the LDO. Each PR1/CP2/OV divider must be a visible vertical divider connected to its associated pin. Connect SS and ILM parts directly to their pins. Put the LDO, its input/output capacitors and enable tie in one compact group.

### SPI sensors and feedback

Draw three named bus wires with short branches to both sensors. Put controller SCK/MOSI series resistors at the bus entry and each MISO resistor at its peripheral branch. Keep chip selects distinct and show their pull-ups. Route the encoder ABI outputs toward the feedback-sheet interface. Draw both sensors' supplies and decoupling locally.

On the selector page, align A/B/I channels in three rows: onboard input and protected external input into the mux, selected output toward the MCU. Show enable/select pulls visibly. Put the fourth switch channel in a separate small group titled “VM sense isolation — follows feedback enable,” with both inputs visibly joined to the divided VM signal. Keep its electrical connection to the same U602 package explicit.

### Inverter and current sensing

Use a functional half-bridge symbol for each CSD88599 package, preserving every pad number and the VIN exposed pad. Either use a verified multi-unit symbol or grouped pins with an explicit package boundary; do not hide physical pad mappings to simplify the picture.

Draw VM at the top, high-side and low-side switches vertically, phase output from the midpoint, and the shunt below. Draw the 1 µF capacitor to GND and the 10 nF capacitor to the package source above the shunt so the different returns are visible. Attach gate series and pull-down resistors to the appropriate gate/source nodes; show bootstrap connections.

Represent each STSPIN op-amp as an actual amplifier unit adjacent to its shunt. Wire the Kelvin pair, 1 kΩ inputs, 28 kΩ feedback, and 56 kΩ bias pair into a complete loop. Place the 14 mV/A equation beside this circuit. Use identical U/V/W geometry so a wiring difference is conspicuous. Add the corresponding NTC circuit nearby if space permits.

### STSPIN symbol structure

Create a multi-unit U301: digital interface/clock/reset, core power/analog supplies, gate-driver/power-management section, and three amplifier units. Keep the single physical reference U301 and footprint. Assign each physical pin exactly once except where KiCad explicitly supports an intentional common-pin representation; avoid hidden power-pin shortcuts. Keep comparator sharing visible through pin names/notes without inventing exposed package pins. Validate all units and physical pads after the split.

### Brake and input power

Show the brake resistor as an explicit external component illustration tied to J501 (graphical annotation, excluded from PCB/BOM unless separately specified). Draw the power switch and flyback path conventionally. Below it, wire the OV divider into the comparator, the hysteresis feedback to its input, and both Schottky commands into a visible OR node feeding U501. Draw the driver output, gate resistor, clamp and pull-down as one local chain.

For the DC link, draw a VM bus across the capacitor tops and a GND return across their bottoms. Arrange the divider as a series chain, with a visible tap and output filter/interface. Put each optional branch where it actually connects.

## Implementation sequence

1. **Freeze the electrical baseline.** Save the current netlist, physical `(reference, pin)` connectivity, BOM, DNP state, footprints and UUIDs. The work is a presentation/hierarchy refactor. Record any newly discovered electrical issue separately before changing its circuit.
2. **Replace the drawing engine's label-per-pin rule.** Add rotation/mirroring, explicit wires, junctions, power symbols, local labels, hierarchical ports, multi-unit symbols and block-relative placement. Keep circuit connectivity separate from drawing geometry. Hand-author routes within small functional blocks; do not rely on a generic automatic schematic router.
3. **Complete CAN and the 5 V buck first.** These exercise signal pairs, connector branches, pull-ups, decoupling, feedback and power loops. Render them at the intended page sizes and apply the acceptance tests below before propagating the style.
4. **Redraw auxiliary power, USB, SPI and feedback.** Establish connected modules and move parts to their functional owner sheets. Use explicit hierarchy interfaces.
5. **Redraw STSPIN, inverter/current sense and brake.** Introduce and verify multi-unit symbols; preserve all package and Kelvin distinctions. Repeat a reviewed phase-block drawing rather than independently positioning three variants.
6. **Compose final pages and overview.** Distribute test points, merge debug, place concise notes and choose the smallest legible page size for each circuit. Wire the system overview after its interfaces are settled.
7. **Verify electrical equivalence.** Compare connected sets of physical `(reference, pin)` pairs, allowing sheet-path/net-name changes without overlooking merged or split nets. Preserve values, MPNs, footprints and DNP states. Repeat native ERC and actual footprint/pad checks. Update validators to support multi-unit symbols and the final sheet count, not weaken their connectivity checks.
8. **Perform a circuit-reading review, then publish.** Trace the paths below directly from the rendered drawings. Re-export BOM/netlist/PDF, refresh review evidence and package the new revision only after both electrical and presentation gates pass.

## Acceptance criteria

- A reader can trace CAN TX-to-connector, buck VIN-to-output and FB loop, SPI fanout, shunt-to-amplifier, and brake OV-to-gate directly through visible wires.
- Every divider, pull-up, decoupling group, filter and local feedback loop looks like its electrical function. No local two-component connection requires searching for a matching label elsewhere.
- Global labels are limited to justified shared connections; sheet interfaces use hierarchy ports. Label count should fall substantially, but there is no arbitrary quota that encourages missing information.
- No detached grid of test points, regulator support parts, or gate resistors remains.
- Standard text remains readable at the intended printed A4/A3 size. Full-page viewing communicates the functional groups immediately; zooming is for pin detail, not discovering where a block starts.
- No ambiguous wire crossings, unintended junctions, overlapping labels, hidden pin-number errors, clipped notes or falsely implied connections.
- The root page communicates the system relationships, not merely filenames.
- Physical pin connectivity and BOM/footprints/DNP remain equivalent to the frozen baseline; ERC has no unexplained violations.
- Any remaining electrical qualification limits from A0 remain documented; improved presentation must not imply new hardware qualification.
