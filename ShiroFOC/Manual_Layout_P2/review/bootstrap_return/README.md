# Bootstrap return correction — 27 September 2026

Applied to the user's P2 save at 11:19. `before.zip` preserves all modified electrical/project files before this correction. Older projects remain unchanged.

## Connections

| Phase | Bootstrap cap | BOOT pin | Dedicated return | Driver OUT pin | MOSFET SH pin | Motor-current net |
|---|---|---|---|---|---|---|
| U | C4 | U4.41 | HS_RETURN_U | U4.42 | U1.2 | PHASE_U |
| V | C8 | U4.38 | HS_RETURN_V | U4.39 | U2.2 | PHASE_V |
| W | C12 | U4.35 | HS_RETURN_W | U4.36 | U3.2 | PHASE_W |

Each capacitor pin 2 connects to BOOT; pin 1 connects to its dedicated return. The phase nets retain MOSFET VSW pads 3–11 and the relevant J1 terminal. The dedicated returns and phase power nets join internally in the MOSFET package; keep them separate on the PCB. Route each high-side return alongside its gate trace. Put bootstrap capacitors at the driver pins. No capacitance values or footprints changed.

C4/C8/C12 moved from the bridge schematic sheet to the gate-driver sheet, drawn directly between BOOTx and OUTx. Their PCB symbol paths were migrated to the actual parent sheet instance. Net classes: HS_RETURN_* = Gate; PHASE_* = Power.

All 260 physical placements and layers are unchanged from the latest user save. The user had already moved the MCU and bootstrap capacitors closer together; that work was retained. No routing was added or removed.

## Previous NTC annotation repair

The prior addition used child-file UUIDs where parent sheet-instance UUIDs were required. After the schematic was opened, its five part references reset to '?'. Restored J502, R511, R512, C505 and D505 by their preserved symbol UUIDs and corrected their instance paths. All symbol-instance paths across the hierarchy were checked against their parent sheet instances, not just against ERC.

## Checks

- Native ERC: 0 violations.
- Pad-net cross-check: no mismatches; known U205 pins 19/20 without footprint pads remain.
- PCB DRC: 34 violations, unchanged from the latest user save; zero added findings. Unconnected items remain expected on this unrouted board.
- Schematic parity: reduced from 11 issues to the two existing U205 missing-pad warnings.
- All component positions, angles, sides and existing routing preserved.
- Gate-driver and bridge sheet renders inspected for connectivity and readable placement.

This is a scoped return-path correction, not a fabrication-release review. Current machine reports are in this folder and copied to `../current.xml`, `../erc.json`, and `../drc.json`. Earlier reports/previews describe earlier placements. The one-shot apply script is an audit record, not a reusable rebuild command.
