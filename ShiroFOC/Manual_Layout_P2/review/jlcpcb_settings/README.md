# PCB editor routing defaults — 2026-09-27

Current project: Manual_Layout_P2. Previous settings and board preserved in before.zip.
Source: https://jlcpcb.com/capabilities/pcb-capabilities (checked 2026-09-27).

## Via and routing rules

- Project minimum drill: 0.20 mm; minimum via diameter: 0.45 mm; minimum radial annular width: 0.10 mm.
- Default, Analog and USB netclasses: 0.50 mm diameter / 0.25 mm drill.
- Gate, LogicPower and Power retain 0.60 / 0.30 mm defaults.
- Selectable presets: 0.50/0.25, 0.45/0.20 and 0.60/0.30 mm (diameter/drill).
- Via hole-to-hole edge spacing: 0.20 mm. Existing component-pad drill spacing rule: 0.45 mm; existing U901 thermal-hole rule retained.
- Minimum track width and copper clearance: 0.15 mm, matching the stated multilayer 2 oz limits. Existing netclass clearances remain larger.

JLCPCB publishes an absolute via/drill minimum of 0.25/0.15 mm, but this project intentionally uses stricter practical minima. Its table charges extra for 0.15 mm holes and for 0.20/0.25 mm holes with via pads below 0.45 mm. The chosen sizes avoid those categories. A via preset does not establish a high-current rating: power transitions still need appropriately sized parallel arrays.

## Placement

Applied and saved editor grid: 0.10 mm. Option+1 selects 0.10 mm; Option+2 selects 0.05 mm for fine placement. These are editing increments, not component-clearance rules.

This is a focused routing-default update, not fabrication sign-off. Existing footprint and unfinished-layout DRC issues remain to be resolved.

## Verification

KiCad loaded and saved the settings. Readback confirmed all three presets and netclass defaults, plus grid indices 18/19 for 0.10/0.05 mm. The PCB file is byte-identical to its pre-change backup; no geometry, placement or routing changed.
