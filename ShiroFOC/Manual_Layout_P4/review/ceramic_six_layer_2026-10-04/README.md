# Ceramic DC link / six-layer revision evidence

See the [revision notes](../../../docs/PCB_CERAMIC_SIX_LAYER_2026-10-04.md) for the selected parts, circuit changes, stack target and remaining routing work.

- `schematic.pdf` and `schematic_*.png`: final KiCad schematic export; changed pages visually reviewed.
- `placement_front/back.svg/png`: native PCB geometry preview, viewed from the front through the board for coordinate consistency. Separate images show the components on each side and their courtyards. These show placement, not completed routing.
- `change_manifest.json`: capacitor population and added/restored schematic references.
- `placement_manifest.json`: exact positions, sides, orientations and old-net aliases.
- `bom.csv`: native KiCad BOM export, including DNP status and MPNs.
- `validation.json`: 21 passing revision invariants; existing DRC findings and unrouted items remain.
- `validation/`: native before/after ERC and DRC, compressed XML netlists and original copper checks for moved footprints.

`validate_revision.py` is read-only except for its JSON report. It uses the KiCad skill's S-expression parser and the pre-change ZIP under the project's backup directory. Netlist/ERC/DRC inputs are saved snapshots; regenerate them after any later CAD edit before relying on a rerun.

`update_schematic.py` and `update_pcb.py` are one-time migration records. **Do not rerun them on a later revision:** they reconstruct selected files from the temporary pre-change checkpoint and would replace subsequent edits. They are retained to explain how this revision was made. `render_placement.py` is a read-only renderer requiring KiCad's bundled Python/pcbnew.
