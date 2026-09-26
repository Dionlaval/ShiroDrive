# ShiroFOC workspace

## Start here

- **[Manual rebuild](Manual_Rebuild/ShiroFOC_Manual.kicad_pro)** — complete reference schematic with your manual MOSFET bridge retained, ready for page-by-page review; [library instructions](Manual_Rebuild/README.md).
- [P1 reference project](ShiroFOC_KiCad_P1/ShiroFOC_KiCad.kicad_pro) — existing schematic and revised component placement.
- [Saved routing review](routing_review_2026-09-21/README.md) — independent snapshots of the incomplete routing, paused for review.
- [Learning lab](../learning/README.md) — interactive models, exercises and explanations.

The original design files remain in their project folders. Routing is incomplete; the saved boards are not fabrication releases. The notes below document different design stages.

## Design notes

### Schematic and firmware

- **[Current firmware requirements](requirements/FIRMWARE_REQUIREMENTS.md)** — manual rebuild: safe startup, persistent BOOT0, calibration storage, sensors, current protection and brake control.

- [Design constraints](docs/DESIGN_CONSTRAINTS.md)
- [Rev A schematic plan](docs/SCHEMATIC_REV_A_PLAN.md)
- [Rev A design review](docs/DESIGN_REVIEW_REV_A.md)
- [Schematic readability plan](docs/SCHEMATIC_READABILITY_PLAN.md)
- [Schematic redraw review](docs/SCHEMATIC_REDRAW_REVIEW.md)
- [MCU pinout and interfaces](docs/MCU_PINOUT_AND_INTERFACE_PLAN.md)
- [Historical A0 firmware bring-up contract](docs/FIRMWARE_BRINGUP_CONTRACT.md)

### PCB

- [Layout guidelines and DRC settings](docs/PCB_LAYOUT_GUIDELINES.md)
- [Layout handoff](docs/PCB_LAYOUT_HANDOFF.md)
- [Original placement notes](docs/PCB_PLACEMENT_P0.md)
- [Revised placement notes](docs/PCB_PLACEMENT_P1.md)
- [P1 revision list](docs/PCB_REVISION_LIST_P1.md)
- [Capacitor options study](docs/PCB_CAPACITOR_OPTIONS_2026-09-17.md)

## Folder guide

| Folder | Contents |
|---|---|
| `Manual_Rebuild/` | Your schematic review copy, imported CAD and download checklist |
| `requirements/` | Current implementation requirements for the manual rebuild |
| `docs/` | Design plans, decisions and review notes |
| `ShiroFOC_KiCad/` | Original reference project and its outputs |
| `ShiroFOC_KiCad_P1/` | Revised placement project and routing experiments |
| `routing_review_2026-09-21/` | Saved routing checkpoints for inspection |
| `tools/` | Existing generation, checking and routing scripts |
| `backups/` | Preserved files, including the notes before this cleanup |

The documentation cleanup moved notes and repaired links; it did not change the existing circuitry or routing.
