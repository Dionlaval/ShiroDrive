# Routing checkpoint — 2026-09-21

**Incomplete; not released.** Root P1 board remains refined unrouted placement. Original P0 and dated backups remain intact. Work is in candidates.

## Accepted baseline

`finish4_raw.kicad_pcb` with matching project/rules: native `finish4_drc.json` has **91 unconnected items, zero error-severity violations in the violations section**. Warnings include dangling routes and inherited silk/library issues. This is not a completed layout.

Includes completed six Kelvin sense routes and nine op-amp connections, restored front VM spine, snubber relocation, and repaired W-phase VM feed. The W gate pull-down FORCE_W branch was moved around the bottom VM copper instead of cutting through it.

## Current experiment (not accepted)

`driver_fanout.kicad_pcb` opens MCU gate escapes: R301 moved to (45,42.4),90 degrees; R602 to (40.35,45.6),0 degrees; GHS1/GHS3 outward vias; revised OUT1 bootstrap branch; added GLS2/GLS3 fanouts. Coordinates are board-local, native minus 100 mm. Native report: 98 unconnected and two clearance errors, both a USB_UART_TX via against revised OUT1. The offending unlocked via UUID is d5355968-23be-482e-8673-02b56690c0e1.

**Do not use gate4_candidate:** it adds a roughly 154 mm GLS2 detour. Rejected for route quality. Other gate attempts failed at trapped MCU escapes.

## Strategy correction

Ordinary routing was inserted too early and now obstructs critical gate-drive exits. Repeated static A* and short Freerouting passes have stalled. Next: remove ordinary unlocked routes in the MCU region from driver_fanout, preserve locked power/Kelvin/amplifier/local driver routes, complete critical gate connections with bounded route length, then rebuild ordinary routes. Accept candidates only after native DRC, connectivity, route geometry and actual power-fill inspection.

## Tools

`ShiroFOC/tools/route_remaining_p1.py`: native-shape grid router, F/B only, optional SHIRO_FANOUT and SHIRO_STITCH modes. Native DRC mandatory after completion/refill. A successful path is not evidence of acceptable gate geometry. Gate mode currently allows crossing VM fills, so inspect bus continuity explicitly.

`open_driver_escapes_p1.py`, `restore_power_corridor_p1.py`, `repair_vm_w_feed_p1.py`, `prune_candidate_errors.py` document recent changes. `export_routing_dsn.py` removes permissive rule areas only from temporary export; real keepouts and native rules retained. Never repeat the old long Freerouting run.

KiCad Python: /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9
Native CLI: /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
Use RemoveNative; keep .kicad_pro/.kicad_dru beside candidate; refill before DRC; preserve pad/net mapping after fill.

## Remaining deliverables

Finish routing; stitch ground returns; inspect actual power fill and necks; native DRC and schematic/PCB parity; full PCB/cross/thermal/EMC plus manual critical review. Nominal current-amplifier DC simulation and schematic analysis already exist; do not repeat without reason. User excludes external fabricator and availability checks.

Final presentation is not authored. Use actual PCB wireframes with functional regions AND individually coloured components; copies showing actual copper/routes by function and returns; ranked problems, fixes and tradeoffs. `render_layout_review.py` and `render_copper_p1.py` exist. Correct J201 classification to USB. Regenerate figures from final geometry. Both sides currently use top-view coordinates and must be labelled.

## Superseding pause checkpoint — user visual review

User explicitly asked whether a hint is more efficient; answer: **yes**. Routing is paused. Do not run more routing attempts until their hint/resume instruction arrives.

Complete editable review copies: `ShiroFOC/routing_review_2026-09-21/` with README and SHA256 manifest.
- `latest_trial`: phase_references, 152 unconnected, zero other error violations; latest rotated-cap corridor experiment, OUT1/2/3 connected, GHS/GLS pairing still unfinished. 66 warnings remain, including 16 connection-width warnings.
- `best_baseline`: finish4_raw, 91 unconnected, zero other error violations. No later experiment supersedes it as accepted baseline.
- `gate_loop_comparison`: gates_first, 149 unconnected, zero other error violations. Seven of nine gate/reference nets connected but high-side outgoing/return paths separate widely. Not acceptable as final.

New scripts: clear_mcu_routing_p1.py (optional wide driver-region reset); open_gate_corridor_p1.py (C306, R301 moves and ground-stub edits); finish_driver_fanout_p1.py (rejected OUT2 via shorts sensor pad, do not reuse unchanged); open_phase_corridors_p1.py (latest capacitor rotation and 0.2 mm local escape rules, valid result phase_corridors2). route_remaining_p1.py now limits path length/via count, respects explicit net order, supports partner-net corridor constraint and directed fanout rectangle, and uses connected phase polygons as routing endpoints. Pair constraints have not yet produced an accepted paired-gate solution.

Important result: rotating C412/C422/C432 and moving their VM via arrays out of the next phase's Kelvin pads opened the middle phase; OUT2 new link 23.51 mm / one via. Earlier phase_corridors and last_gate_fanout contain shorts and are rejected. phase_corridors2 and phase_references have no native error violations except unconnected items. Inspect actual copper necks and current return before accepting changes.
