# P1 layout revision list

Updated 2026-09-19. **Implemented as a separate component-placement project.** See [P1 placement and validation](PCB_PLACEMENT_P1.md).

| ID | Request | Result |
|---|---|---|
| P1-01 | Reclaim top-side centre | Removed the obsolete 15 mm blanket magnet envelope; U601 remains centred on the back. |
| P1-02 | Four M3 clearance mounting holes | H1–H4 present in schematic and PCB, 3.2 mm NPTH. |
| P1-03 | Space for screw heads/washers | 8 mm envelopes on both faces, centres 6 mm from adjacent straight edges; placement checks pass. |
| P1-04 | Parallel bridge and phase-output rows | Two vertical columns at the same 14 mm pitch, each output directly opposite its half bridge. |
| P1-05 | Repeated phase cells | Matching MOSFET/gate/bypass geometry; bottom shunts and DNP snubber resistors. Kelvin and force connections remain separate nets for routing. |
| P1-06 | Bulk capacitor decision | **Retain the existing three 680 µF electrolytics.** Shifted their row to clear the corner screws. The earlier replacement/hybrid proposal is superseded. |
| P1-07 | Repack affected circuits | Brake block occupies the released upper-middle area; controller and local underside circuitry shifted together. |
| P1-08 | Recheck revision | Zero native schematic-parity or placement-clearance errors; 499 unrouted items and the 9 existing warnings remain. |
| P1-09 | Preserve previous layout | Original project untouched; separate P1 project plus a tested P0 backup ZIP. |

## Files

- [New P1 project](../ShiroFOC_KiCad_P1/ShiroFOC_KiCad.kicad_pro)
- [Original project](../ShiroFOC_KiCad/ShiroFOC_KiCad.kicad_pro)
- [P0 backup ZIP](../backups/ShiroFOC_P0_before_parallel_bridges_2026-09-19.zip)
- [Detailed placement record](PCB_PLACEMENT_P1.md)
- [Historical capacitor alternatives](PCB_CAPACITOR_OPTIONS_2026-09-17.md)

The capacitor choice is retained for the prototype; it does not erase the operating-current and thermal checks documented in the design review. No component sourcing or external fabricator validation was performed.
