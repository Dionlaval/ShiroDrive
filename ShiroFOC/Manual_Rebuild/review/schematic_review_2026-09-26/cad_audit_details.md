# Fresh footprint/CAD audit, 26 September 2026

Read-only source: native KiCad 9.0.4 XML export `/tmp/review_cad.xml` from saved root schematic. 253 components; 250 assigned footprints, 46 distinct assigned footprint IDs, all files present. Exactly three unassigned: J1, JP601, U603. Per-component paths, pin/pad sets and resolved model paths: `/tmp/review_cad_inventory.json`. 18 incoming ZIP archives inspected by member listing; 15 local STEP/STP model files present. All current project-relative model links resolve.

## Required work before PCB transfer/layout

| Reference | MPN / package | Existing footprint and model | Action |
|---|---|---|---|
| U1–U3 | CSD88599Q5DC / DMM0022A | Manual:DMM0022A + DMM0022A.stp present | **Repair pin-to-pad mapping. No download needed.** Netlist has literal pin names [3-11], [12-20]; footprint has individual 3…20. Also resolve 21,23…26 and thermal vias named V against package drawing. |
| U603 | SN74LVC3G17DCUR / DCU VSSOP-8, 2.3×2mm, 0.5mm pitch | Currently blank; installed Package_SO:VSSOP-8_2.3x2mm_P0.5mm and its STEP both exist | Assign/review standard footprint. No vendor CAD download needed. Local TI datasheet identifies exact DCU variant; installed footprint tags Texas_DCU0008A. |
| JP601 | SENSOR SUPPLY / three-contact removable-shunt selector | Currently blank, MPN blank; standard Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical and STEP available | Choose pitch/height/header and compatible shunt; standard footprint likely sufficient. Pins 1/2/3 = 3V3/output/5V_SYS. One shunt only. |
| J1 | Motor termination / no MPN selected | No footprint, generic protected three-contact receptacle symbol | Choose actual connector or solder-wire termination and cable sizing. Then select matching existing footprint or obtain exact manufacturer CAD if absent. Cannot specify unique download yet. |
| Y301 | 0132M4-24.000F07DTNLL / nominal 3225 four-pad crystal | Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm + standard STEP present | Obtain authoritative exact-part package/pin drawing and qualify existing footprint. Current package assignment remains provisional. STEP alone does not settle pad mapping. |

## Missing 3D models (footprints already present)

| Reference | MPN / package | Footprint status | Download/action |
|---|---|---|---|
| J101 | AMASS XT60PW-M, right-angle PCB connector | Exact KiCad AMASS footprint exists, pins 1/2 match | XT60PW-M STEP useful for enclosure/connector mating clearance. Incoming ZIP contains footprint only; model link missing. |
| J201 | HRO TYPE-C-31-M-12 | Exact KiCad HRO footprint exists, all electrical/shield pad names match | Exact connector STEP useful for enclosure opening/fit. Incoming ZIP contains no STEP; model link missing. |
| R1, R3, R5 | BVR-Z-R0005-1.0 / four-terminal BVR4026 | Resistor_SMD:R_Shunt_Isabellenhuette_BVR4026 exists, pins 1…4 match | One BVR STEP shared by three shunts. Installed link missing; no incoming BVR archive. Optional 3D representation, not missing electrical land pattern. |
| U901 | CP2102N-A02-GQFN20 / QFN-20+EP, 3×3mm | SiliconLabs-specific QFN footprint exists, pins 1…21 match | Exact QFN20 STEP optional for appearance/height checks. Existing ZIP has only three footprint variants, no STEP; installed STEP link missing. |
| C101–C103 | EEVFK1J681M / Panasonic K16, Ø18×16.5mm | Manual:Panasonic_EEVFK_K16_18x16.5 exists | Exact Panasonic STEP only needed for precise terminal/enclosure fit. Current generic 18×17.5 STEP exists and is explicitly labelled approximate. |
| J501 | Solder-wire pads to off-board RH25010R00FE01 resistor | Standard two-wire footprint exists | No connector download required. Missing optional wire STEP can be ignored; actual off-board resistor/heatsink envelope is a separate mechanical assembly choice. |

Thus four missing purchased-part model types worth downloading are XT60PW-M, TYPE-C-31-M-12, BVR-Z-R0005-1.0 and CP2102N QFN20. Exact Panasonic is conditional. These model gaps are separate from footprint/electrical blockers.

## Already have footprint + resolving model; no new download

| References | Part / package | Existing local CAD |
|---|---|---|
| U4 | STSPIN32G4 / QFN | Manual:QFN_IN32G4_STM + QFN_IN32G4_STM.step |
| U201 | LMR36510FADDAR / DDA | Manual:LMR36510_DDA + DDA0008E.stp (family/revision envelope caveat) |
| U203 | TPS2121RUXR / RUX 12 | Manual:TPS2121_RUX + RUX0012A.stp |
| U204 | TLV75533PDYDR / DYD | Manual:TLV75533_DYD_GND + DYD0005A.stp |
| U205 | MPM3620AGQV-Z / 3×5×1.6mm module | Manual:IC18_MPM3620AGQV-Z_MNP + MPM3606AGQV.step (shared family model) |
| L201 | 74437349470 / WE-LHMI 7050 | Manual:WE_LHMI_7050_74437349470 + downloaded WE-LHMI 7050 family STEP |
| Q501 | CSD19531Q5A / DQJ/Q5A | Manual:CSD19531Q5A_Q5A_DQJ0008A + DQJ0008A.stp |
| U501 | UCC27517ADBVR / DBV5 | Manual:UCC27517A_DBV5 + DBV0005A.stp |
| U502 | TLV3012BIDBVR / DBV6 | Standard SOT-23-6 + STEP |
| U601 | AS5047P-ATSM / TSSOP14 | Manual:AS5047P_TSSOP14 + TSSOP14_OSM.step |
| U602 | TMUX1574PW / PW16 | Manual:TMUX1574_PW16 + PW0016A.stp |
| U701 | BMI323 / LGA14 | Manual:BMI323_LGA14 + BMI323_BOS.step |
| D601 | TPD3E001DRLR / DRL5 | Manual:TPD3E001_DRL5 + DRL0005A.stp |
| U801 | TCAN3413DR / SOIC8 | Standard SOIC-8_3.9x4.9mm_P1.27mm + STEP |
| D801 | PESD2CANFD24V-T / SOT23 | Standard SOT-23 + STEP |
| U202 | USBLC6-2SC6 / SOT23-6 | Manual:USBLC6_SOT23_6 + SOT23-6L_STM.step |
| J601, J801/J802 | JST BM06B/BM04B-GHS-TBT | Exact KiCad JST GH footprints + matching installed STEP |
| J1001 | FTSH-105-01-L-DV-K | Manual:FTSH_105_01_L_DV_K + downloaded Samtec STEP |
| SW301 | TL3305A family, exact ordering suffix absent | Assigned standard SW_SPST_TL3305A + STEP; qualify height/actuator selection |

Ordinary bridge passives are now assigned, contrary to historical checklist sections: C1/C5/C9 0402; C2/C6/C10 1206; C3/C7/C11 1210; C4/C8/C12 0603; R2/R4/R6 0805. Standard footprints/models exist. No value-specific CAD downloads. Test pads, mounting holes and JP801 are intentional PCB features with no body-model requirement. SW1001/SW1002 are absent from the fresh netlist, despite old checklist text.

## Evidence / triage

- High-confidence file/netlist consistency blocker: Three-phase bridge.kicad_sch lines 791 and 827 encode literal [12-20]/[3-11]; native XML exports U1 [3-11] on OUT1 and [12-20] on Net-(U1-PGND). DMM0022A.kicad_mod line 523 onward contains additional pad 21, 23…27 and line 565 onward pads V. Imported presence does not make these electrically mapped.
- U603 source is 09_Feedback_Selection.kicad_sch:5012 (MPN), with blank footprint. Local DataSheets/SN74LVC3G17.pdf pages 1,24–26 identifies DCU0008A and MO-187-CA; installed VSSOP footprint line 6 has matching Texas_DCU0008A tag. Assignment remains intentionally deferred; no edits performed.
- JP601 source blank footprint at 09_Feedback_Selection.kicad_sch:7697; J1 blank at Three-phase bridge.kicad_sch:5363.
- U205 symbol pins 19/20 have no footprint pads: **intentional exception**, not extra download or blocker. Netlist marks them no_connect; prior review/cascaded_power/REVIEW.md:34 explains removal within manufacturer underside no-contact zone; local MPM3620A.pdf p24 forbids metal/trace/via mechanical or electrical contact in this area. Do not re-import raw archive to restore these pads.
- JST extra MP pads are mechanical tabs, not missing electrical symbol pins.
- Panasonic footprint description line 5 explicitly states model is approximate 18×17.5mm envelope.
- This audit checks saved footprint association, pad-number-set consistency and model file presence. It does not claim all imported geometry or 3D alignment has been remeasured, nor assess unsaved UI changes.
- DMM0022A raw geometry detail: central pad 27 (symbol VIN, net VM) is at (0,0), 3.3×5.4mm. Eleven plated through-hole pads named V sit within that copper at x=−1.4/0/+1.4mm, y up to ±2.45mm. They must be reconciled with VIN/VM; do not assume these thermal vias are ground. Pad 21 is at (+2.35,−2.0)mm; corner pads 23–26 are at x=±2.115,y=±3.013mm. Their intended electrical function still needs exact drawing reconciliation, independent of their CAD presence.
