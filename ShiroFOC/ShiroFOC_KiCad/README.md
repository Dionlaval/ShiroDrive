# ShiroFOC A1-Drawing - schematic ready for prototype PCB layout

**P1 revision notes:** see [../PCB_REVISION_LIST_P1.md](../docs/PCB_REVISION_LIST_P1.md). H1-H4 are now in the schematic; the P0 PCB still awaits the mounting holes and placement revision. Earlier parity reports and release PDFs/ZIPs predate this change.

**PCB P0 placement is now available:** all 260 footprints on an 80 × 80 mm rounded-square, four-layer board. See [placement notes and previews](../docs/PCB_PLACEMENT_P0.md). Open the existing `.kicad_pcb`; it remains unrouted. The prior schematic release archives and manifests describe the earlier release, not this placement checkpoint.

Open `ShiroFOC_KiCad.kicad_pro` in **KiCad 9**. The project contains 12 native schematic sheets with connected functional blocks and project-local symbols/critical footprints. Standard footprints resolve through KiCad 9's installed libraries. A1-Drawing preserves all A0 electrical connections, components, values, MPNs, footprints and DNP choices.

Start with [design review](../docs/DESIGN_REVIEW_REV_A.md), [PCB layout handoff](../docs/PCB_LAYOUT_HANDOFF.md), and [firmware contract](../docs/FIRMWARE_BRINGUP_CONTRACT.md). No PCB has been routed. Current/voltage goals still require hardware qualification; the review identifies ripple, thermal, USB-power and braking limits.

## Release contents

- `libs/ShiroFOC_Redraw.kicad_sym`: functional symbols, including multi-unit STSPIN and analog switches, with complete physical pin mapping.
- `libs/ShiroFOC.pretty`: four datasheet-derived footprint types.
- `outputs/ShiroFOC_Rev_A_Schematic.pdf`: reviewed, searchable 12-page schematic (ten A3 and two A4 pages).
- `outputs/ShiroFOC_Rev_A_BOM.csv`: one row per reference, including DNP and procurement specifications.
- `outputs/ShiroFOC_Rev_A.net`: KiCad XML netlist.
- `outputs/erc_rev_a.json`, `validation_report.json`, `footprint_audit.json`, `footprint_pad_audit.csv`: release verification evidence.
- `outputs/electrical_calculations.json`: current-sense, brake-threshold, bus and rail calculations.
- `outputs/visual_review.json`, `release_manifest.json`: reviewed PDF/pages and SHA-256 release hashes.
- `outputs/net_name_aliases.json`: maps KiCad's local/hierarchical net names to the A0 names used by the handoff. Complete physical pin groups are verified independently of naming.
- `../review_baselines/A0_before_redraw/`: frozen connectivity and BOM used by the validator.

## Rebuild

Requires Python 3.12+ and KiCad 9 CLI, plus a Python interpreter containing `pcbnew`. From the ShiroFOC directory:

```sh
python3 tools/release_rev_a.py
```

On macOS the script discovers the standard `/Applications/KiCad/` installation. Other installations can set `KICAD_CLI`, `KICAD_PYTHON`, and `KICAD9_FOOTPRINT_DIR`. `KICAD_PYTHON` must import pcbnew. Set `FONTCONFIG_FILE` to a valid local fontconfig configuration if that installation needs one for headless PDF export.

`generate_rev_a.py` retains the electrical definitions. `native_rev_a.py` now delegates to `redraw_rev_a.py`; `redraw_core.py`, `redraw_power.py`, `redraw_analog.py` and `redraw_interfaces.py` define the connected drawings using `redraw_engine.py`. No legacy GUI conversion is needed. UUIDs are stable between redraw builds. **Rebuild overwrites generated native sheets and the redraw symbol library.** If editing in KiCad, also reconcile those changes into the layout modules before rebuilding. The checked-in custom footprints, project settings and handoff documents are preserved.

The overview contains navigable child sheets and graphic system connections. Circuit boundaries use named global ports; local circuits use wires and junctions. STSPIN units A/B/C/D/E/F remain one physical U301. See [redraw review](../docs/SCHEMATIC_REDRAW_REVIEW.md) for the sheet map and validation scope.

Rebuild regenerates machine checks but does not perform visual approval. Render and inspect the new PDF; refresh `visual_review.json` with its exact hash only after review, then run `python3 tools/release_rev_a.py --manifest-only`. That final command checks the visual hash and writes the release manifest. Keep review status separate from a successful CLI export.

## Start PCB layout

Continue from the existing P0 PCB. Use Update PCB from Schematic when synchronizing subsequent schematic changes. Keep all DNP footprints on-board; fitted state is controlled by the native DNP property and Assembly field. Follow the handoff for Kelvin routing, DC-link return points, live VIN thermal pads, optional termination and external connector restrictions. Preserve U901's documented thermal-drill adjustment when updating footprints. Resolve mechanical fit, copper/current sizing, DRC and fabrication details during PCB work.
