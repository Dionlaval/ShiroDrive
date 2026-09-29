# MCU fanout correction

The imported U4 has 0.500126 mm pin pitch and 0.254 mm pad width: adjacent-pad gap is 0.246126 mm. BOOTSTRAP nets were mistakenly assigned to Power (2 mm default tracks, 0.50 mm clearance). The previous U4 rule covered two footprint pads but not an escaping track, so the interactive router refused to start even with a 0.15 mm track selected.

- BOOTSTRAP* now belongs to Gate (0.40 mm normal width / 0.20 mm normal clearance).
- Two copper items intersecting U4's courtyard use 0.15 mm clearance.
- Tracks intersecting U4's courtyard have 0.20 mm preferred width, with 0.15 mm minimum.
- Other netclass values, footprint geometry, schematic connectivity and placement are unchanged.

Exit pads straight outward; widen gate/supply tracks once clear of the pin row. Keep the narrow portions short. KiCad courtyard predicates apply to whole intersecting objects: make a short separate escape segment before wider routing, rather than one long segment crossing the courtyard. This exception does not provide a creepage/isolation rating.

## Verification

KiCad CLI DRC accepted the rules. A disposable board copy with 13 outward 0.20 mm tracks on U4 pins 35–43 and 61–64 produced no clearance or width errors involving those tracks; only expected dangling-end warnings. The user board has no added test tracks. Existing unfinished-layout violations are outside this focused correction.
