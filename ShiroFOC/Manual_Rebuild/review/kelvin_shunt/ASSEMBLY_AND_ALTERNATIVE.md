# Assembly profile and BVR comparison option

R7 is a disconnected Device:R_Shunt symbol using the previous BVR-Z-R0005-1.0 / BVR4026 footprint. All four pins are intentionally marked NC. DNP=true, in_bom=false, on_board=true, exclude_from_sim=true. This allows footprint import for placement comparison without ordering the part. **DNP does not remove copper or paste from fabrication output**: keep R7 off-board while comparing and remove the comparison symbol/footprint before production exports. Active R1/R3/R5 remain LR2512D, unchanged.

## LR2512D assembly question

User-supplied datasheet p3 shows a recommended reflow peak230±5°C and30±10s above220°C; p4 lists a solder-heat resistance test at260±5°C for20±1s, with resistance change limit±0.5%. These are different tests, not an interchangeable recipe. The wave-soldering plot is a separate process and does not apply to ordinary reflow assembly of these SMD shunts.

JLC's published [assembly capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities), checked26September2026, list Standard240±5°C and Economic255±5°C (not adjustable), with double-sided placement listed under Standard. The recommended component reflow peak is not an exact match. Heat-resistance testing makes assembly plausible, but is not confirmation of the actual dwell times or two reflow cycles. Preserve the datasheet with the manufacturing handoff and flag this profile mismatch before ordering; no special process has been requested or confirmed. No stock check performed.

The recipe is normal assembly-process information, not a task for the PCB designer to reproduce manually. It does not by itself require returning to the larger BVR part.
