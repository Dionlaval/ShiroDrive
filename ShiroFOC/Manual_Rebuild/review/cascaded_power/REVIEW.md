# Cascaded power — MPM3620A revision, 26 September 2026

## Current implementation

```text
VM → U201 LMR36510 + L201 → VCC (10.01 V) → STSPIN and brake gate drivers
                                       └→ U205 MPM3620A → 5V_BAT ┐
USB → existing protection → 5V_USB ──────────────────────────────┤ U203 mux
                                                               └→ 5V_SYS → U204 → 3V3
```

U205 is now **MPM3620AGQV-Z**, replacing TPS82150. The 10 V buck, external STSPIN supply/bypass, source mux, LDO, user's bridge and PCB are unchanged by this replacement. The updated auxiliary sheet is revision **PWR3**. The earlier TPS82150 circuit and review artifacts are preserved in `../../../backups/manual_before_MPM3620A_2026-09-26.zip`.

## Circuit changes

- **R216/R217 = 34.0 kΩ / 6.49 kΩ, 0.1%.** These are MPS Table 1's values for 10 V → 5 V with two 22 µF output capacitors; no feed-forward capacitor is specified. Using the typical 0.798 V reference gives **4.979 V**. Conservative static reference/resistor/input-bias limits give about **4.869–5.089 V**. These bounds exclude transients.
- **C214/C215:** retain two 22 µF / 25 V X7R input capacitors, with at least 10 µF effective total at 10 V.
- **C218/C219:** retain two 22 µF / 16 V X7R output capacitors, with at least 22 µF effective total at 5 V. Exact capacitor MPNs and DC-bias/tolerance/temperature behaviour still need qualification; generic values are not a completed procurement specification.
- **C216 removed.** MPM3620A has internal soft start: typically 1.6 ms from 10% to 90%, specified 0.6–2.6 ms across temperature.
- **R218/R219 = 100 kΩ / 100 kΩ.** R218 pulls U201 PG high from VCC; new R219 pulls the same node toward ground. This retains PG-controlled startup while limiting the direct EN voltage below 6 V. The worst static high bound is about 5.224 V; a conservative loaded nominal calculation gives 4.60 V, comfortably above the 1.65 V maximum rising threshold. PG pulls it low when the 10 V supply is not ready. This does not rely on operating the internal EN clamp.
- **U205 pin 16 = input VCC/10 V.** Its pin **2**, confusingly also called VCC, is the module's **internal 4.9 V output** and is left open. Its capacitor is internal. BST pin 11 also has its capacitor inside and is left open.
- **OUT pins 7/8/9** connect to 5V_BAT. **PGND pins 12/13/14** connect to GND. **SW pins 4/5/6** share the local U205_SW net for the footprint copper; they do not connect to the external output.
- **AGND pin 3** receives only the feedback-divider return on U205_AGND. MPS specifies that AGND joins PGND internally; no external connection is necessary. Route this small return directly to pin 3 and keep power current out of it.
- PG pin 18 is unused. NC pins 10/15/19/20 remain unconnected. Stacked equivalent pins are hidden in the compact functional symbol; all 20 individual pin numbers remain present in the netlist.

The upstream LMR36510 remains a **1 A, 10 V source** shared with gate-drive loads. U205's 2 A rating does not make 2 A available to the complete 5 V rail. The earlier illustrative 320 mA logic load plus 50 mA gate allowance remains about 238 mA at 10 V with assumed 85% conversion efficiency. Existing mux/LDO limits also remain unchanged.

## Imported CAD and necessary corrections

Original supplied ZIP retained: `../../downloads/incoming/ul_MPM3620AGQV-Z.zip`.

- Symbol: `Manual:MPM3620AGQV-Z`, consolidated in `libs/Manual.kicad_sym`. Imported pin numbering checked against MPS page 12. Incorrect imported electrical types were corrected, including ground pins labelled power outputs and VCC labelled power input. Symbol graphics were rearranged to preserve the readable power-flow drawing.
- Footprint: **`Manual:IC18_MPM3620AGQV-Z_MNP`**, from the supplied ZIP. Peripheral pad locations and land shapes were retained.
- Pads **19/20** in the downloaded footprint were inside MPS's underside no-contact region. Their copper, mask and paste were removed; a conservative F.Cu keepout now prohibits tracks, vias, pads and zones in that area. These two NC/test locations deliberately have no PCB solder lands, matching the page 24 recommended land pattern.
- SW and OUT copper bars were converted from unnumbered copper graphics to numbered pads so KiCad can associate them with their nets. The original land outlines, paste and mask are retained within export rounding. The oversized off-courtyard pin marker was replaced with a compact front-silkscreen marker.
- Model: **`libs/3dmodels/MPM3606AGQV.step`**, byte-for-byte from the ZIP. The STEP header names MPM3610GQV; this is a supplier-provided **family package model**, not an exact MPM3620A top marking. Its vertex bounds give **3 × 5 × 1.6 mm**. Offset (−1.5, −2.5, +0.1) mm, unit scale and zero rotation align it with the footprint. Top and angled renders were inspected.
- The superseded local TPS82150 symbol and footprint were removed from the active library; the backup retains them.

## Placement requirements

Place input capacitors directly beside IN/PGND, output capacitors beside OUT/PGND, and the divider beside FB/AGND. Keep FB away from U205_SW. Follow the footprint keepout, connect every PGND pad to substantial ground copper, and provide ground vias nearby. Use only as much SW copper as needed for thermal performance; keep sensitive traces away. Route the gate-drive branch and regulator-input branch separately from the 10 V source, each with its own local bypass. The integrated inductor still produces a switching magnetic field.

## Verification

**PASS, scoped change:**

- Native KiCad netlist export and all 20 U205 pin-to-net checks.
- Every pre-existing pin-to-net association preserved except replacement U205, removed C216 and R217's intentional AGND return.
- **251 components:** C216 removed, R219 added.
- Native ERC: **same 16 pre-existing findings; zero new findings**, no exclusions added.
- PCB and all other schematic sheets have unchanged hashes.
- Isolated footprint test board: **zero geometry/clearance/keepout DRC violations**. Its two unrouted PGND links are expected because this is a footprint fixture, not a routed design.
- ngspice DC divider/enable checks; rendered auxiliary schematic and supplied STEP alignment inspected. SPICE did not model switching-loop dynamics.

This is not a full-board fabrication review. The existing bridge symbol/pad mapping issues and capacitor qualification remain open. No fabrication or availability validation was added. Transients, temperature and EMI still require placed/routed hardware validation.

## Evidence and artifacts

- [MPS datasheet](https://www.monolithicpower.com/en/documentview/productdocument/index/version/2/document_type/Datasheet/lang/en/sku/MPM3620AGQV-Z/document_id/2100/): pages 4–5, 12, 15, 17–20 and 24. Local copy: `../../../DataSheets/MPM3620A.pdf`.
- [Updated overview, power and gate-driver sheets](Power_Revision.pdf)
- [Circuit detail](MPM3620A_circuit.png)
- [Model top](MPM3620A_model_top.png) / [angled](MPM3620A_model_angled.png)
- [Machine verification](validation.json), `netlist_before.xml`, `netlist_after.xml`, `erc_before.json`, `erc_after.json`, `dividers.cir`, `dividers.log`.
