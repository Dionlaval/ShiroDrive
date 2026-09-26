# Manual schematic review

**BVR comparison option:** R7 is a disconnected, DNP BVR-Z-R0005-1.0 with its BVR4026 footprint, excluded from the BOM but available for PCB placement comparison. Keep it off-board and remove before production exports. R1/R3/R5 remain the active LR2512D shunts.

**Shunt update:** [LR2512D two-terminal shunts with four PCB Kelvin connections](review/kelvin_shunt/README.md), applied to R1/R3/R5. This supersedes the historical BVR selection below. Generic 3D models accepted; no exact STEP downloads required.

**Current pre-layout status:** [Protected external sensor supply added](review/sensor_supply_protection/README.md): zero ERC violations,254 components; U604 footprint/3D deferred to final CAD pass. R3 coarse motor-current-trip validation remains for firmware/bench work. Complete other circuit decisions, then CAD association, then PCB layout.

## Cascaded power revision — 26 September 2026

The manual schematic now uses VM → 10 V (LMR36510) → 5 V (MPM3620A integrated-inductor module) → existing USB mux / 3.3 V LDO. STSPIN uses external VCC with SW tied to VM. See [change review](review/cascaded_power/REVIEW.md) and [updated supply drawings](review/cascaded_power/Power_Revision.pdf). The bridge and PCB are unchanged. U205 now uses the downloaded footprint with corrected keepout and the aligned supplier family STEP. Exact capacitor DC-bias qualification remains open. ERC remains at the same 16 pre-existing findings.


Open [ShiroFOC_Manual.kicad_pro](ShiroFOC_Manual.kicad_pro). This project now contains the complete P1 reference schematic **with your manually rebuilt MOSFET bridge retained**. Review and simplify this copy page by page.

## Start here

- **[Firmware requirements](../requirements/FIRMWARE_REQUIREMENTS.md):** current startup, BOOT0 option bytes, persistent calibration, sensing, faults and brake-chopper contract.

- [Footprint / STEP download checklist](downloads/FOOTPRINT_CAD_CHECKLIST.md): exact part numbers, component references, package distinctions and priorities.
- Put downloaded bundles in **[downloads/incoming/](downloads/incoming/)**.
- [Component-to-footprint catalogue](downloads/component_footprint_map.csv): all 253 components and current associations.
- [Import validation](review/import_validation.json): checks, remaining library issues and preserved-file evidence summary.

## Pages

| Page | Section |
|---|---|
| 1 | Functional overview and four M3 clearance holes |
| 2 | Battery / DC link |
| 3 | Auxiliary 5 V / 3.3 V power and source selection |
| 4 | STSPIN MCU, MCU supplies, clock, reset and SWD |
| 5 | STSPIN gate driver and VCC converter |
| 6 | **Your retained three-phase bridge** |
| 7 | Three current-sensing amplifiers and phase thermistors |
| 8 | Brake chopper |
| 9 | Dedicated encoder SPI3 and IMU I2C2 |
| 10 | Buffered external Hall / ABI and reset isolation |
| 11 | CAN |
| 12 | USB service |

## STSPIN and library organisation

U4 is one physical STSPIN32G4 using `Manual:STSPIN32G4_Functional`. Its copied reference symbol uses these units: A = MCU; B = MCU supplies; C = gate driver / VCC; D/E/F = current-sensing op-amps. All six retain your imported **`Manual:QFN_IN32G4_STM`** footprint and its existing STEP association. The downloaded original symbol remains in the library for reference.

Your MOSFETs U1/U2/U3 retain **`Manual:DMM0022A`**. Imported footprint files and STEP files were not changed. Custom schematic symbols are consolidated in the single `libs/Manual.kicad_sym` library. Footprints belong in `libs/Manual.pretty/`; models belong in `libs/3dmodels/`.

The **25 September CAD pass** checked 17 incoming ZIPs, updated 16 component associations, and linked 12 downloaded STEP models. TLV755 thermal-pad numbering and Panasonic bulk-capacitor lands were corrected. Standard geometry was retained where downloaded exports were incompatible. See the existing download checklist for the exact decisions, three missing purchased-part STEP models, approximate capacitor model and provisional crystal assignment.

## What was copied and preserved

Source: `../ShiroFOC_KiCad_P1/`. Ten functional sheets and the overview were copied, including optional/DNP circuitry and mounting holes. Source U301 becomes U4. Copied BOOT1/2/3 net names become BOOTSTRAP1/2/3 to match your retained bridge. The bridge's circuit, references, values and file content are unchanged.

The existing manual PCB was left untouched and **has not been synchronized** with the copied schematic. The original reference project was not modified. No extra component removals were made; you will choose those during your page-by-page review.

## Checks and remaining work

- Exported netlist matches the copied source circuitry, values, MPNs and assembly properties, excluding the intentionally substituted bridge.
- Retained bridge connectivity and file hash match the pre-copy state. Bootstrap and Kelvin interfaces connect to the copied driver/sensing sheets.
- U4 exports as one component; all 65 pins are represented and match the imported footprint pad-number set.
- Twelve pages export and render; modified overview, driver and sensing sheets were inspected at full size.
- ERC reports **16 findings**: 4 existing symbol/library mismatches, 5 existing bridge pin-type conflicts, and 7 power-drive declarations around the retained bridge/bootstrap interface. No ERC exclusions or suppressions were added. This is a review baseline, not a fabrication release.
- The retained MOSFET symbol uses literal pin ranges `[3-11]` / `[12-20]` that do not match individually numbered footprint pads. Additional footprint pads also need mapping. Resolve this before PCB synchronization; no repeat download is needed.
- R1/R3/R5 are now BVR-Z-R0005-1.0, 0.5 mΩ shunts; bridge passive values and footprints have been assigned. Only J1, U603 and JP601 currently have blank footprints. See the fresh checklist for exact actions.
- Purchased-part STEP files still missing: J101 (XT60PW-M), J201 (HRO USB-C), R1/R3/R5 (BVR shunt), U901 (CP2102N QFN20). J501 is a wire feature with an optional missing model. The capacitor STEP is approximate and the exact crystal package drawing still needs verification; see `downloads/FOOTPRINT_CAD_CHECKLIST.md`.

## Backups

Before the copy: `../backups/manual_before_reference_merge_2026-09-24_220041.zip`.

Before CAD association: `../backups/manual_before_cad_association_2026-09-25_100127.zip`. Validation: `review/cad_import_validation.json`.

Earlier manual stages remain in the existing `../backups/` archives. Existing generation scripts for the reference project do not target this manual folder.

## Downloaded CAD organization

Keep original bundles in `downloads/incoming/`. After checking pad numbers and package geometry, copy footprints into `libs/Manual.pretty/`, models into `libs/3dmodels/`, and assign `Manual:<footprint>` to the relevant symbol(s). Use `${KIPRJMOD}/libs/3dmodels/<model>.step` for model paths. Keep the functional schematic symbol; its appearance is independent of the footprint. Check model alignment in the 3D preview.
