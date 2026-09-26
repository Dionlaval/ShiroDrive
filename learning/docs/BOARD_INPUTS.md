# Board inputs and evidence

Snapshot: **19 September 2026**. Nominal circuit values are extracted from the P1 schematic and cross-checked against its exported netlist. P0 placement is unrouted. The user selected adjustable example motor and wiring values.

## Actual circuit values

Confidence is high for nominal values and fitted state, based on project files. This does not establish measured capacitance, electrical tolerances or qualified operating limits.

| Reference | Schematic value | Fitted? | MPN, when assigned |
|---|---|---|---|
| C101 | 680uF 63V | Yes | EEVFK1J681M |
| C102 | 680uF 63V | Yes | EEVFK1J681M |
| C103 | 680uF 63V | Yes | EEVFK1J681M |
| C104 | 4.7uF 100V X7R | Yes | Specification only |
| C105 | 100nF 100V X7R | Yes | Specification only |
| C106 | 10nF 100V C0G | Yes | Specification only |
| R103 | 270k 0.1% 100V | Yes | Specification only |
| R104 | 270k 0.1% 100V | Yes | Specification only |
| R106 | 1k | Yes | Specification only |
| R105 | 27k 0.1% | Yes | Specification only |
| C108 | 10nF | Yes | Specification only |
| U301 | STSPIN32G4 | Yes | STSPIN32G4 |
| C301 | 100nF | Yes | Specification only |
| C302 | 10uF 10V | Yes | Specification only |
| C307 | 100nF | Yes | Specification only |
| C303 | 100nF | Yes | Specification only |
| C304 | 1uF | Yes | Specification only |
| C305 | 100nF | Yes | Specification only |
| C306 | 1uF | Yes | Specification only |
| C312 | 10uF 25V X7R | Yes | Specification only |
| C313 | 100nF 25V | Yes | Specification only |
| C412 | 1uF 100V X7R | Yes | Specification only |
| C415 | 10nF 100V X7S | Yes | Specification only |
| R411 | 4.7R | Yes | Specification only |
| R412 | 0R | Yes | Specification only |
| C411 | 100nF 25V | Yes | Specification only |
| R416 | BVR-Z-R0005 0.5mR | Yes | BVR-Z-R0005-1.0 |
| R417 | 1k 0.1% | Yes | Specification only |
| R418 | 1k 0.1% | Yes | Specification only |
| R410 | 56k 0.1% | Yes | Specification only |
| R441 | 56k 0.1% | Yes | Specification only |
| R419 | 28k 0.1% | Yes | Specification only |
| C414 | 47pF C0G | No (DNP) | Specification only |

C101–103: VM to GND. C412/C422/C432: VM to GND. C415/C425/C435: VM to the respective source-above-shunt net. C414/C424/C434: optional feedback capacitors, **not fitted**.

## Design targets and firmware intentions

| Quantity | Value | Evidence/status |
|---|---|---|
| Bus | 18–42 V | Design target, not demonstrated rating |
| Continuous phase current | 25 Arms passive / 40 Arms with cooling | Target; thermal qualification pending |
| Short peak phase current | 80 A, up to 2 s subject to limits | Target, not a capacitor sizing waveform |
| Initial PWM | 20 kHz centre-aligned | Firmware contract |
| Initial deadtime | 500 ns | Conservative bring-up intention, characterise later |
| Current-sense gain | 28, 14 mV/A with 0.5 mΩ | Resistor-network calculation |
| Gate supply | 8 V startup, firmware selects 10 V | Design/firmware intention |
| Brake firmware start | Around 43 V for 10S | Initial control intention |
| Brake backup | About 45.92 V rising / 44.21 V falling | Nominal calculation; tolerances and delay apply |
| Board | 80 × 80 mm current placement; 2/0.5/0.5/2 oz copper | Existing P0 geometry and stack intent |

## Explicit example assumptions

| Input | Default | Why / how to replace it |
|---|---|---|
| Example source | 36 V | Within target range; slider covers 18–42 V |
| Winding R and L | 0.1 Ω, 100 µH | Teaching load; use motor phase data, distinguishing phase vs line-to-line measurement |
| Source/cable loop R and L | 50 mΩ, 1 µH | Includes positive and return paths; not inferred from a claimed cable length |
| Ceramic retention | 50% | Sensitivity only; replace with chosen MPN bias/temperature/tolerance data |
| Ceramic part ESR/ESL | 20 mΩ, 1 nH | Lumped examples, not the moteus part specification |
| Shared bank connection | 1 mΩ, 3 nH | Geometry assumption; explore 1–50 nH |
| Existing bulk ESR | 30 mΩ per can; 10 mΩ combined | Teaching estimate, not datasheet extraction |
| Selected local bypass C | 7.81 µF nominal × 0.5 | C104–106 plus C412/C422/C432; auxiliary branches excluded |
| Three-phase operating point | 40 Arms, m=0.8, 30° current lag, 250 Hz electrical | Prescribed sinusoidal-current SPWM example; not a closed-loop FOC simulation |
| Edge smoothing | First-order τ=80 ns | Finite-edge approximation, not 80 ns rise time or vendor switching model |
| Gate example | Qgd=12 nC, plateau=4 V, driver/internal R=3 Ω | Explicit hypothetical numbers; editable in JS source |

## Provenance

Netlist: `ShiroFOC/ShiroFOC_KiCad/outputs/revision_P1/netlist.xml`

SHA-256: `bdeca8dd80db46110dc3622fcaaff7522bf1f98c753e98461f893002781ab3d9`

Source documents are linked in [SOURCES.md](SOURCES.md). Machine-readable inputs are in [board_inputs.json](../data/board_inputs.json). The automated analyzer includes heuristic findings; this package uses the checked values and does not endorse its unreviewed findings.
