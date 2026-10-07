# CAN and ESD package substitutions — 2026-10-06

Project: Manual_Layout_P3. User-requested substitutions applied to schematic instances, embedded symbols, project symbol library, PCB footprints, and MPN/manufacturer fields.

| Reference | Old part | Replacement | Package |
|---|---|---|---|
| U801 | TCAN3413DR | TCAN3413DRBR | DRB VSON-8, 3 × 3 mm, 1.65 × 2.4 mm exposed pad |
| D601 | TPD3E001DRLR | TPD3E001DRYR | DRY USON-6, 1 × 1.45 mm |

## Pin mapping and layout

Verified against TI datasheets: https://www.ti.com/lit/ds/symlink/tcan3413.pdf and https://www.ti.com/lit/ds/symlink/tpd3e001.pdf.

- U801 pins 1–8 retain their nets. Exposed pad 9 is GND in the schematic and PCB, connected locally to pin 2. The standard footprint without built-in thermal vias was selected because opposite-side components occupy this area. Its final ground-plane via arrangement remains part of the ongoing board routing.
- D601 IO pins 1/2/4 and GND pin 3 retain their nets. VCC changes from pin 5 to pin 6; pin 5 is explicitly NC in the schematic and unconnected on the PCB.
- Both positions, orientations, sides, and footprint UUIDs preserved. All 322 other footprints compare identically to the saved pre-edit board.
- D601 trace endpoints adjusted; IO3 corner rerouted. IO2 uses the existing connector via and one new 0.6 mm / 0.3 mm drill via, avoiding the new NC pad. Existing connections retained.
- D601 uses the KiCad DRY0006A solder-mask-defined land pattern, including negative mask/paste margins, with 0.15 mm local pad clearance to match its minimum copper spacing.
- Copper zones refilled. No zone boundaries or nets intentionally changed.

## Validation

- KiCad 9.0 CLI loads schematic and PCB successfully; updated PCB reopened in KiCad and D601 shown as TPD3E001DRYR / Manual:TPD3E001_DRY6.
- Exported netlist confirms every U801 and D601 pin mapping listed above.
- ERC before: 12 messages. After: 11 messages (1 existing error, 10 warnings); no new package-related errors.
- DRC before refill: 581 violations, 499 unconnected items. After replacement and refill: 177 violations, 499 unconnected items, zero footprint errors. Counts are not a direct quality comparison because original zone fills were stale.
- Final DRC has no new shorts or clearance violations involving the replacements. The existing D601-IO1 connector via still has a 0.25 mm drill below the configured 0.254 mm minimum; it was not changed.
- Refilling exposes several dangling-via warnings elsewhere on the unfinished board. This is a targeted package change, not a full-board routing or fabrication sign-off.

Confidence: high for package identity, pin mappings, and preserved placements (manufacturer datasheets, exported netlist, parsed board comparison); manufacturing availability and full thermal/EMC performance were not evaluated.

Local footprints are copied from the installed KiCad Package_SON library. The pre-edit target files are archived alongside this report. Existing user changes were preserved; no commit was made.
