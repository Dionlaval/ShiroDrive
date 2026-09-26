# Current footprint and CAD checklist

**BVR comparison option:** R7 is a disconnected, DNP BVR-Z-R0005-1.0 with its BVR4026 footprint, excluded from the BOM but available for PCB placement comparison. Keep it off-board and remove before production exports. R1/R3/R5 remain the active LR2512D shunts.

Updated 26 September 2026 after implementing the accepted review changes.

**255 schematic components including one DNP comparison shunt; zero native ERC violations.** U604 (TPS2553DBVR) is newly added; its footprint/3D association is intentionally deferred to the final CAD pass. All previously assigned footprints are retained. [Implementation / selections / limits](../review/schematic_review_2026-09-26/implementation/README.md) · [Current component catalogue](component_footprint_map.csv).

## Model policy — updated 26 September 2026

User accepts generic 3D models; exact vendor STEP downloads are no longer required. Retain suitable existing models and use generic package models where available, with approximate geometry clearly identified. Footprint dimensions, pad numbering and symbol-to-pad mapping still require verification. This policy does not itself assign missing models or complete the final footprint pass. No CAD downloads are currently requested from the user.

**Implemented:** R1/R3/R5 now use Milliohm **LR2512D-3W-0.5mR-1% (C500733)** with `Manual:R_Shunt_LR2512D_0m5_3W_Kelvin`. The two-terminal part has four PCB connection pads: power1/4, sense2/3; net-tie groups1-2 and3-4. Manufacturer main lands plus user-requested horizontal sense stubs; no downward legs. Generic2512 model. [Dimensions, routing rules and native validation](../review/kelvin_shunt/README.md). No BVR download required.

## Optional exact models — reference only, no download required

Put original ZIPs in `downloads/incoming/`. Look for an actual `.step` or `.stp` file. Our functional schematic symbols remain in place.

| Part | References | What to download |
|---|---|---|
| **AMASS XT60PW-M** | J101 | Exact right-angle PCB-mount **PW-M** STEP, not a cable or vertical XT60. Footprint exists. |
| **HRO TYPE-C-31-M-12** | J201 | Exact USB-C receptacle STEP. Footprint exists; shell/board mounting geometry varies between models. |
| **Silicon Labs CP2102N-A02-GQFN20** | U901 | **QFN-20, 3 × 3 mm** STEP; not 24/28-pin versions. Electrical footprint exists. |
| **Kyocera CX3225FB24000C0FZZH1** — optional exact model | Y301 | Search this exact MPN for a KiCad/STEP bundle. **24 MHz, 7 pF, 3.2 × 2.5 × 0.7 mm.** Manufacturer lands already match the assigned standard footprint; a generic STEP exists. Exact STEP availability is unconfirmed, so this does not block placement. [Exact datasheet](https://ele.kyocera.com/assets/products/crystal-device/specification/CX3225FB_7pF.pdf). |

Models are useful for mechanical checking; missing exact purchased-part STEP models do not prevent electrical routing.

Optional: Panasonic **EEVFK1J681M** exact STEP for C101–C103. Existing conservative Ø18 × 17.5 mm model differs from the nominal Ø18 × 16.5 mm body. The Panasonic K16 lands were checked previously. J1/J501 are plated solder-wire features; no purchased connector model is needed for them.

## New item for the final CAD pass

**U604: TPS2553DBVR**, TI DBV SOT-23-6, constant-current version (not TPS2553-1). Associate/verify its footprint and model during the final CAD pass; no download is requested now. C606/C607 retain standard0603 footprints.

## Chosen and assigned — no download required

| Part / refs | Decision |
|---|---|
| CSD88599Q5DC U1–U3 | Imported footprint/STEP retained. Symbol range pins expanded; thermal vias renamed to VIN pad27; NC pads retained. Pad-net fixture passed. |
| Motor terminals J1 | Earlier three large solder-wire holes: `Connector_Wire:SolderWire-6sqmm_1x03_P14mm_D3.5mm_OD7mm`. Actual installed drill **4.4 mm**, copper7mm, pitch14mm. |
| SN74LVC3G17DCUR U603 | `Package_SO:VSSOP-8_2.3x2mm_P0.5mm`; standard STEP exists. |
| Sensor selector JP601 | `Jumper:SolderJumper-3_P1.3mm_Open_Pad1.0x1.5mm`. Bridge1–2=3V3 or2–3=5V; never both. Open=no sensor power. |
| C205/C206/C214/C215 | TDK **C3225X7R1E226M250AB**, 22µF25VX7R,1210. |
| C218/C219 | TDK **C3225X7R1C226M250AC**, 22µF16VX7R,1210. |
| R210/R212 | Yageo **RC0603FR-0722KL**,22k1%,0603; mux coarse OV threshold raised. |

Capacitor selection uses actual manufacturer bias/temperature curves; see the implementation notes for assumptions and the revised 10V output sizing basis. Generic1210 STEP height may differ: selected capacitor bodies are2.5mm nominal, allow2.7mm. No custom capacitor model is needed to start layout.

Already present: STSPIN32G4, LMR36510, TPS2121, TLV755, MPM3620A, Würth47µH inductor, CSD19531, UCC27517A, TLV3012B, AS5047P, TMUX1574, BMI323, TCAN3413, PESD2CANFD24V-T, TPD3E001, USBLC6, JST GH and Samtec SWD. Retain earlier documented family/envelope-model caveats. Ordinary passives, M3 clearance holes and test pads use standard libraries.

MPM NC/test19/20 intentionally have no solder lands; do not restore them from the uncorrected ZIP. JST `MP` pads are mechanical tabs.

## Carry into the next layout / prototype review

- **R6 implemented:** TPS2553 current-limited external sensor supply and PC13 fault input; bench-test supply survival under shorts.
- **R3:** characterize the coarse fast overcurrent trip; normal ADC measurement is unchanged. No precise25A hardware trip claim.
- Check converter startup/load-step behavior and crystal startup/frequency/drive on the prototype.
- Confirm SW301 exact TL3305A actuator height if enclosure clearance is tight.

No stock or fabricator validation. The existing draft PCB has not been synchronized or routed as part of these schematic changes.
