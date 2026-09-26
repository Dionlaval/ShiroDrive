# Footprint and 3D CAD checklist

## Current bridge/amplifier selection — 26 September 2026

- 39 component records selected/updated for a provisional **25 A RMS with cooling** target.
- Standard library footprints assigned; no custom CAD created.
- **Only new download: BVR-Z-R0005-1.0 STEP**, three identical shunts. [Download page](https://componentsearchengine.com/part-view/BVR-Z-R0005-1.0/Isabellenh%C3%BCtte). Place the ZIP/model in `incoming/`.
- [Part list, rationale and remaining limits](../review/bridge_current_parts/README.md).
- The older generic bridge-part rows below are superseded by that selection. J1 motor termination and the existing MOSFET pin mapping still need resolution.


## MPM3620A update — 26 September 2026

- [x] U205 replaced by **MPM3620AGQV-Z**, using the new incoming Ultra Librarian ZIP.
- [x] Imported footprint **Manual:IC18_MPM3620AGQV-Z_MNP**, with manufacturer-required NC/test-area keepout corrections. Pin types corrected in the functional symbol.
- [x] Supplied **MPM3606AGQV.step** linked and aligned; 3 × 5 × 1.6 mm dimensions checked. It is a shared family model (header MPM3610GQV), not exact top marking. No additional STEP download is required for the package envelope.
- [x] R216/R217 updated to 34 kΩ / 6.49 kΩ; C216 removed; R219 added to bound EN voltage.
- [x] Updated catalogue: **251 components**, zero new ERC findings.

See [current power/CAD review](../review/cascaded_power/REVIEW.md). The sections below record the earlier 25 September bulk import; its historical counts do not replace the current catalogue.


## Earlier 26 September power revision — superseded where noted

- **Historical U205: TPS82150SILR (superseded by MPM3620A above; no STEP download needed)** added with `Manual:TPS82150_SIL0008D`, derived from standard KiCad geometry and checked against TI. **Exact STEP still needed**; download the eight-pin SIL0008D package. No model substitute is attached.
- **L201: 74437349470, 47 µH** now uses `Manual:WE_LHMI_7050_74437349470`; same 7050 family STEP and land dimensions.
- **L301 and D302 removed** from the current schematic. Their downloaded files are retained for reference. Older rows below describe the prior import.
- C205/C206/C214/C215 now require 25 V X7R; C218/C219 require 16 V X7R. Effective-capacitance requirements are recorded on the schematic properties; exact MPNs remain to be qualified.
- See [power change review](../review/cascaded_power/REVIEW.md). PCB synchronization remains pending.


Updated **25 September 2026**. Reviewed all **17 incoming ZIPs**, changed **16 component associations**, and linked **12 downloaded STEP models**. Original ZIPs remain in `incoming/`. Active footprints are in `../libs/Manual.pretty/`; downloaded models are in `../libs/3dmodels/`. Functional schematic symbols were retained.

The project remains a **schematic review baseline**, not a fabrication release. No stock or fabricator validation was performed. The manual MOSFET bridge, its imported CAD, STSPIN CAD and the PCB were preserved. The PCB has not been synchronized.

## The five unavailable CAD downloads

“Unavailable” here means CAD was not found, not that the component cannot be purchased.

| Part / references | Footprint decision | 3D model / further action |
|---|---|---|
| **TCAN3413DR — U801** | Keep standard `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`. TI DR ordering code specifies 8-pin SOIC/D. | Installed standard SOIC STEP is suitable for package visualization. No custom footprint needed. |
| **TLV3012BIDBVR — U502** | Keep standard `Package_TO_SOT_SMD:SOT-23-6`. TI DBV is the six-lead package here. | Installed standard STEP. No custom footprint needed. |
| **PESD2CANFD24V-T — D801** | Keep standard `Package_TO_SOT_SMD:SOT-23`. Nexperia specifies SOT23; pins 1/2 are the protected lines, pin 3 is common. | Installed standard STEP. No custom footprint needed. |
| **EEVFK1J681M — C101–C103** | **Corrected now:** `Manual:Panasonic_EEVFK_K16_18x16.5`. Panasonic K16 standard land pattern: two 7.9 × 2.5 mm pads, 6.0 mm gap, centres ±6.95 mm. Positive pad remains 1. The previous Vishay-based 18 × 17.5 footprint had 8.8 × 9.6 mm pads. | Exact Panasonic STEP still absent. Uses the installed 18 × 17.5 mm model as an explicitly **approximate, conservative envelope**. Actual nominal Panasonic body length is 16.5 mm, tolerance ±0.5 mm. Do not use the generic base/terminal shape for tight mechanical fit. |
| **0132M4-24.000F07DTNLL — Y301** | Existing `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` retained **provisionally**. | Standard STEP exists, but an authoritative drawing for this exact ordering code was not obtained. Confirm terminal numbering, recommended lands and maximum height before accepting it. A custom footprint may be unnecessary; this is still unresolved. |

Sources: [TI TCAN3413 ordering/package information](https://www.ti.com/product/TCAN3413/part-details/TCAN3413DR), [TI TLV3012 datasheet](https://www.ti.com/lit/ds/symlink/tlv3012.pdf), [Nexperia PESD2CANFD24V-T datasheet](https://assets.nexperia.com/documents/data-sheet/PESD2CANFD24V-T.pdf), [Panasonic FK drawing, pages 1–2 and part table](https://api.pim.na.industrial.panasonic.com/file_stream/main/fileversion/3128), [Panasonic exact part dimensions](https://industrial.panasonic.com/kr/products/pt/aluminum-cap-smd/models/EEVFK1J681M).

## Incoming ZIP audit and applied associations

The part number on the ZIP generally matches the intended component. That does **not** make every exported footprint correct. Where a KiCad land pattern was a better match to the drawing, its geometry was retained in a project-local copy and the downloaded STEP attached. No bundled symbols were substituted into the circuit.

| ZIP part / references | Result and chosen footprint | Model status |
|---|---|---|
| `74437349220` — L201, L301 | Correct inductor family. Retain `Manual:WE_LHMI_7050_74437349220`: its 2.95 × 3.5 mm lands and 2.5 mm central copper keepout match Würth. Downloaded nominal lands are smaller; do not replace the existing exact geometry. | Downloaded Würth STEP linked; top/angled fit inspected. |
| `AS5047P-ATSM` — U601 | TSSOP-14 and pin sequence match. `Manual:AS5047P_TSSOP14` retains KiCad TSSOP-14 land geometry. | Downloaded STEP linked and visually aligned. |
| `BMI323` — U701 | Correct 14-pin LGA and pin sequence. Downloaded nominal lands are approximately 0.381 × 0.203 mm, smaller than Bosch's 0.475 × 0.25 recommendation. `Manual:BMI323_LGA14` retains KiCad geometry with outward toe extensions and the same inner pad edges. | Downloaded STEP linked and visually aligned. |
| `TPS2121RUXR` — U203 | Correct RUX 12-pad package, no extra central EP. `Manual:TPS2121_RUX` retains KiCad RUX land geometry and thermal vias. | Downloaded RUX STEP replaces missing library model; fit inspected. |
| `LMR36510FADDAR` — U201 | Correct DDA family. Raw `DDA0008J` numbers thermal vias 10–17; these do not match the symbol. Its `_NV` variant avoids that issue. We retained KiCad's properly numbered geometry as `Manual:LMR36510_DDA`. | Downloaded `DDA0008E.stp` fits the package envelope. This is a package visualization; land geometry remains the DDA0008J pattern. Do not treat the E-named model as exact J revision metrology. |
| `TLV75533PDYDR` — U204 | **Imported with a mapping correction** as `Manual:TLV75533_DYD_GND`: raw centre pad 6 and vias 7–9 all renamed **2/GND**. Five external pins plus grounded thermal pad; source copper/mask/paste geometry retained. Added missing assembly courtyard. | Downloaded DYD STEP linked and visually aligned. |
| `TMUX1574PWR` — U602 | **Raw footprint rejected:** bundled PWP footprint and symbol add EPAD, but requested PW is ordinary 16-pin TSSOP. R is the reel suffix. `Manual:TMUX1574_PW16` retains the correct standard PW lands. | The bundled `PW0016A.stp` is suitable and aligned despite the footprint mismatch. |
| `UCC27517ADBVR` — U501 | DBV five-lead package and pins 1–5 match. `Manual:UCC27517A_DBV5` retains standard SOT-23-5 geometry. | Downloaded STEP linked and aligned. |
| `USBLC6-2SC6` — U202 | Six-lead SOT-23 package and pin sequence match. `Manual:USBLC6_SOT23_6` retains standard geometry. | Downloaded STEP linked and aligned. |
| `TPD3E001DRLR` — D601 | Correct tiny DRL-5 package, not SOT-23-5. `Manual:TPD3E001_DRL5` retains the TI-specific KiCad lands. | Downloaded DRL STEP replaces missing library model; fit inspected. |
| `CSD19531Q5A` — Q501 | Correct part, but raw `DQJ8` draws its central drain land as **un-numbered F.Cu graphics**, unsuitable for reliable net-aware pad handling. It also differs from the current TI recommended land dimensions. Retain `Manual:CSD19531Q5A_Q5A_DQJ0008A`, with the central drain numbered 5. Pins 1–3 source, 4 gate, 5–8 drain. | Downloaded STEP linked with **180° Z rotation** to match the retained footprint orientation; fit inspected. No circuit change. |
| `CP2102N-A02-GQFN20` — U901 | Correct 20-pin version. Downloaded nominal EP is about 1.702 mm square; Silicon Labs recommends 1.8 mm and specific corner lands. Retain the exact KiCad SiliconLabs QFN-20 footprint. | **ZIP contains no STEP.** Installed footprint's STEP file is also missing. Download exact QFN20 model later, or create a clearly labelled package model. |
| `BM04B-GHS-TBT` — J801, J802 | Correct four-way vertical JST GH. Raw mounting tabs are numbered 5/6, beyond the four-contact symbol. Keep the installed exact JST footprint with mechanical tabs. | Exact-name KiCad STEP already installed; no extra download needed. ZIP has no STEP. |
| `BM06B-GHS-TBT-LF-SN-N-` — J601 | Correct six-way vertical GH base package. Raw mounting tabs are numbered 7/8. Keep the installed exact six-way JST footprint; no need to introduce extra symbol pins for the tabs. | Exact-name KiCad STEP already installed; ZIP has no STEP. |
| `FTSH-105-01-L-DV-K` — J1001 | Imported nominal `Manual:FTSH_105_01_L_DV_K`: ten lands, 1.27 mm pitch; same pin sequence. No -A alignment holes. K is a housing keying option, not permission to omit an arbitrary electrical contact. | Downloaded STEP linked and aligned. Manufacturer drawing used to distinguish the K and A options. |
| `XT60PW-M` — J101 | **Raw footprint rejected as a drop-in:** signal holes are numbered 3/4, while its symbol uses 1/2; raw 1/2 are the narrow mounting features. Keep the exact installed AMASS footprint, whose contacts are 1/2. | **ZIP contains no STEP**, and installed model is missing. Exact XT60PW-M STEP still needed for mechanical checks. |
| `TYPE-C-31-M-12` — J201 | Correct connector name, but raw footprint combines pad names (`A1-B12`, etc.) and numbers shield tabs 13–16. These do not match the current A/B/S1 symbol pins. Keep the exact installed HRO footprint with compatible pad naming. | **ZIP contains no STEP**, and installed model is missing. Exact HRO STEP still needed. |

“Visually aligned” means KiCad top and angled renders showed the model at the footprint's position, sensible scale, orientation and board height. It is not a dimensional inspection of a manufactured part or every STEP face. Models without independently verified exact revisions are identified above. Standard-library land patterns were kept where they avoided unnecessary vendor-export errors.

Relevant package evidence: local `../../DataSheets/{TLV755P,LMR36510,CSD19531Q5A,WE_74437349220,TPS2121RUXR,TMUX1574,CP2102N}.pdf`; [Bosch BMI323 drawing, landing pattern p213](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi323-ds000.PDF); [TI TPD3E001 DRL drawing](https://www.ti.com/lit/ds/symlink/tpd3e001.pdf); [TI UCC27517A DBV drawing](https://www.ti.com/lit/ds/symlink/ucc27517a.pdf); [Samtec FTSH drawing](https://suddendocs.samtec.com/prints/ftsh-1xx-xx-xxx-dv-xxx-mkt.pdf). The machine report records source ZIPs, source footprint paths and final associations.

### Important correction to the earlier wording

**TLV75533PDYDR does have an exposed thermal pad.** TI calls it a five-pin package because it has five external leads; the underside thermal pad is internally connected to ground. It must be soldered to grounded copper. The previous assigned custom footprint already included a centre pad numbered 2; the old checklist's “five-pad” wording was misleading. The new imported footprint explicitly maps the thermal land and all its vias to pin 2. See TI TLV755P pin-functions table on page 3 and DYD drawing.

## Remaining CAD checklist

- [x] Inspect all 17 ZIPs and retain originals.
- [x] Apply checked local associations and project-relative model links.
- [x] Correct TLV755 thermal land/via numbering.
- [x] Replace bulk capacitor lands with Panasonic K16 dimensions.
- [x] Keep standard SOIC / SOT-23 alternatives for the three unavailable small IC/protection packages.
- [x] Render the 12 downloaded models against their assigned footprints.
- [ ] Obtain **XT60PW-M STEP**.
- [ ] Obtain **TYPE-C-31-M-12 STEP**.
- [ ] Obtain **CP2102N QFN20 STEP**, or create an explicit mechanical approximation.
- [ ] Obtain exact **EEVFK1J681M STEP** if a precise enclosure/terminal fit is required. Approximate model is already present.
- [ ] Obtain the exact **0132M4-24.000F07DTNLL drawing** and confirm the provisional crystal assignment.
- [ ] Reconcile the existing **CSD88599Q5DC grouped symbol pins** with individually numbered footprint pads before updating the PCB. This is a separate, pre-existing blocker, preserved for your supervised bridge review.

J501 is a solder-wire feature; its missing optional wire model is not a missing purchased connector. No download is necessary unless a visual wire envelope is useful.

## Existing imported STSPIN and bridge CAD

| References | Part | Status |
|---|---|---|
| U4, units A–F | STSPIN32G4 | Imported `Manual:QFN_IN32G4_STM` and STEP retained; no new download. |
| U1–U3 | CSD88599Q5DC | Imported `Manual:DMM0022A` and STEP retained. Literal symbol pin ranges `[3-11]` / `[12-20]` do not match individual footprint pads; additional pads including `V` require reconciliation. |

## 5. Choose these parts before downloading CAD

These are still generic or unassigned in the retained manual bridge / copied source. There is no unique package to download yet.

| References | What is undecided | Reference-design starting point, not an automatic selection |
|---|---|---|
| R1, R3, R5 | Shunt resistance, exact part and footprint | P1 used `BVR-Z-R0005-1.0`, a 0.5 mΩ four-terminal shunt. The sensing scale assumes that resistance. Your `R_Shunt` placeholders are retained. |
| J1 | Motor connector or direct solder-wire pads | P1 used three 6 mm² solder-wire pads, not a purchased connector. Choose the mechanical termination you want. |
| C4, C8, C12 | Bootstrap capacitance, rating and footprint | Currently named `BOOTSTRAP1`, not given a capacitance. P1 used 100 nF / 25 V; retain as a review choice. |
| C1–C3, C5–C7, C9–C11 | Bridge ceramic voltage rating and package | Values are retained; no footprints assigned. Choose parts/packages with suitable voltage and effective capacitance before matching CAD. |
| R2, R4, R6 | Gate resistor package | 4.7 Ω retained; footprint still blank. Standard resistor footprint once size is chosen. |
| SW301, SW1001, SW1002 | Exact pushbutton | Existing assignment is `SW_SPST_TL3305A`; exact ordering suffix/actuator height is not selected. Download after choosing, or remove during your review. |
| D301 | Exact red LED | Standard 0603 footprint already assigned. Exact LED only needed for part selection / appearance. |
| D101 | Optional input TVS | DNP/tuning placeholder. SMC footprint exists; choose exact TVS only if retaining it. |
| R102, C107 | Optional input damping values/parts | DNP/tuning placeholders. No exact part selected. |

## No separate download needed

- Ordinary resistors/capacitors: the assigned KiCad metric footprints cover 0603, 0805, 1206, 1210, 2220 and 2512 as used. Do not download a different model for each resistance or capacitance.
- H1–H4: standard 3.2 mm M3 non-plated clearance-hole footprints. Screws/standoffs are separate mechanical choices.
- Test pads, JP801 solder jumper, and J501 direct solder-wire brake connection: PCB features, not purchased connector bodies.
- The optional standard-package parts in section 4 already have KiCad footprints. Exact vendor downloads are useful if you want them, but are lower priority than sections 1–3.


## Verification and review files

- **252 components; circuit and pin-to-net mapping unchanged.** Component values, MPNs, assembly fields and functional symbols unchanged.
- All **16 changed associations** have matching symbol/footprint electrical pad-number sets and resolving model links.
- **ERC remains at the same 16 pre-existing findings**, with no new findings and no exclusions added.
- Protected manual bridge, PCB, project settings and imported STSPIN/dual-MOS footprints have identical hashes to the pre-import snapshot.
- [Machine validation and provenance](../review/cad_import_validation.json)
- [Per-component association catalogue](component_footprint_map.csv)
- [Top model inspection](../review/cad_audit/models_top.png) / [angled model inspection](../review/cad_audit/models_angled.png)

The model images are a separate inspection arrangement, **not the PCB layout**. No circuit simplification was performed; your page-by-page review remains the next step.
