# Routing review checkpoint — 21 September 2026

**Paused for the user's visual review. Nothing here is a finished PCB.** Original P0, P1 placement and all routing candidates are preserved. No more routing changes should be made until the user provides their hint or asks to resume.

## Which board to open

| Project folder | Purpose | Unconnected items | Other error-severity DRC violations |
|---|---|---:|---:|
| `latest_trial` | Latest placement/corridor experiment; open this first | 152 | 0 |
| `best_baseline` | Most complete checked connectivity before the corridor reset | 91 | 0 |
| `gate_loop_comparison` | Seven gate/reference connections, but some outgoing/return routes form large loops; comparison only | 149 | 0 |

Open `ShiroFOC_KiCad.kicad_pro` or `.kicad_pcb` in each folder. Each includes the schematic hierarchy, local libraries, board rules and native DRC checkpoint. Counts refer to KiCad's unconnected **items**, not distinct nets. Zero other errors does not mean clean DRC: all boards remain incomplete and have warnings.

## Most useful area to examine

The corridor from U301's upper/right gate-driver pins to Q401/Q402/Q403 and their gate resistors. In native KiCad coordinates this is approximately **X 137–170 mm, Y 128–164 mm** (board-local X 37–70, Y 28–64).

- Highlight **GHS1 + OUT1**, **GHS2 + OUT2**, and **GHS3 + OUT3** in turn. Each high-side gate signal needs its matching phase-reference return close by.
- Check the remaining **GLS1/2/3** routes alongside their source/ground return environment.
- The six **SHUNT_*_SENSE_P/N** traces and underside ratio networks are already connected; preserve their Kelvin pickoff and avoid routing gate signals alongside them for long distances.
- Examine C412/C422/C432 and the adjacent source/shunt via banks on both faces. A passage that appears open on top may be blocked underneath.
- Preserve the wide **VM** feed and the **FORCE_P** / shunt / GND current paths. A route that cuts their only useful copper bridge is not an acceptable improvement.

A useful hint would be a preferred routing corridor, a different ordering of these paths, or a suggested relocation of the MCU-side parts / phase-cell passives. No need to solve all remaining ordinary signals.

## What the latest trial contains

- Ordinary unlocked routes around the driver corridor were removed deliberately. This explains the higher unconnected count than the baseline.
- R301 and C306 moved to open an underside corridor; R602 retained at the earlier clean location. GHS1/GHS3 outward fanouts and additional driver fanouts remain.
- C412/C422/C432 were rotated horizontally; their VM/GND via arrangements changed. Six gate resistors moved 0.2 mm sideways to maintain component courtyards.
- Local 0.20 mm clearance regions were added around those populated capacitor/gate-resistor areas. Existing global and MCU/package rules remain.
- The middle-phase reference route was previously trapped. It now has a roughly 23.5 mm new connecting path. All three OUT reference connections are present in this latest trial, but their matching gate routes still need to be established as close pairs.
- Remaining warnings include narrow copper connections around the revised via arrays, dangling items and inherited silk/library warnings. These have **not** been accepted as final.

## Why routing is paused

Repeated shortest-path routing was reducing connectivity counts without preserving gate-return geometry. Some routes were rejected for 90–154 mm detours; others connected successfully but created large loops or isolated power copper. The experiments found specific placement bottlenecks, but a visual hint is now more efficient than another automatic iteration.

## Still outstanding after the hint

Finish paired gate routing and ordinary signals; restore/check bus copper continuity and ground stitching; recheck native DRC and schematic/PCB parity; perform the critical return-path/EMI/thermal review; implement low-tradeoff high-priority fixes; produce the requested actual-PCB wireframe and colour-coded routing presentation. External fabricator and component-availability checks remain excluded as requested.
