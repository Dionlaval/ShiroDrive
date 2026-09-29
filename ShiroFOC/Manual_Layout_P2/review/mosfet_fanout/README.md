# MOSFET pad-to-routing clearance correction

U1, U2 and U3 now use 0.15 mm clearance for any copper clearance comparison involving a member of the footprint. This includes pad-to-track and pad-to-zone checks; the old rules only covered pairs of pads. Other routing-to-routing and netclass clearances remain unchanged. No global clearance checking was disabled.

The imported DMM0022A footprints have no courtyard, so these rules deliberately use memberOfFootprint rather than intersectsCourtyard. No footprint geometry was changed.

Verification: KiCad DRC on a disposable board with 18 temporary outward 0.25 mm tracks on pads 3, 6, 11, 12, 16 and 20 across U1–U3 reported no violations involving those tracks apart from their deliberately dangling ends. A 0.40 mm track at the corner pins was too close to the corner NC lands (about 0.126 mm); use a smaller local escape there or start from the middle of the power pad bank.

These test traces demonstrate routing access, not motor-current capacity. Final phase/source connections need broad copper collecting the full power-pad bank; do not leave a single thin escape as the main phase-current connection. Existing layout violations are outside this focused settings change.

The board was reopened with the new rules. Current routing and component placement were preserved.
