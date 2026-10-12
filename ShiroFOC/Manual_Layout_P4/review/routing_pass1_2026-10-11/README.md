# P4 support and MCU routing — first pass

Saved 11 October 2026. The working board is `../../ShiroFOC_Manual.kicad_pcb`. The pre-routing user board and project are backed up in `before/`; the checked saved result is duplicated in `final/`.

## Routing added

359 new trace segments: 283 at 6 mil (0.1524 mm), 76 at 10 mil (0.254 mm). 73 new through vias, all 0.5 mm copper diameter with 0.3 mm drill. New tracks use F.Cu, B.Cu and Signals L3; the two internal GND layers remain planes.

The pass connects local VDDA/VREF and SCREF circuitry, the VBUS divider and mux input, brake NTC and portions of the phase NTC networks, MCU SPI/I²C/interrupt/UART paths, feedback-mux controls, and auxiliary/brake control components. It also adds short local 3.3 V links, capacitor ground returns, and 18 additional GND return vias beside signal transitions. Existing crystal and local op-amp routes were already connected and were retained. The encoder MISO connection was shortened from an initial 15.24 mm candidate to 7.64 mm. Its resistor orientation and existing copper constrain the straight path.

All 272 footprints, values, pad nets, positions, and every pre-existing track/via remain unchanged. The accepted NTC/connector/VBUS placement is preserved. DNP footprints remain unplaced. Project settings, custom rules and schematics were not changed.

## Verification

Fresh zone fill and native KiCad 9 DRC with the project rules:

| Check | Before | Saved |
| --- | ---: | ---: |
| Unconnected items | 433 | 337 |
| DRC errors | 33 | 33 |
| DRC warnings | 395 | 388 |

No new DRC error pairs. All new copper is inside the board outline; no new via overlaps a footprint pad, including same-net pads. Native structural checks passed. See `final/validation.json`, `saved_result.json`, and `final/drc.json`.

Independent return-plane inspection found one filled region on each GND layer and adjacent GND reference under every new segment. Sampling at 0.05 mm found no local reference gap of 0.75 mm or longer; the largest sampled gap was 0.60 mm. This is a geometric routing check, not full EMC or signal-integrity sign-off.

[Front/back routing preview](preview/final/overview.png). New copper is coloured, previous copper is grey. L3 is available as `preview/final/inner.svg`; plane fills are omitted from these previews.

## Still to finish

This is a routing pass, not a finished board. Several crowded MCU escapes cannot be completed cleanly without revisiting existing connected copper. Outstanding selected paths include CAN TX/RX and termination control, encoder CS, reset, VBUS ADC, phase-B NTC ADC, mux feedback/enable, the remaining UART receive link, brake PWM, two power-mux sense branches, and phase-B/C raw NTC runs. Local 3.3 V links do not complete the power distribution. `final/net_status.json` lists physical on-board pad clusters for each targeted net.

Next routing work should address those escapes, the 34.25 mm EXT_FEEDBACK_SELECT detour, and remaining ground-return proximity at crowded transitions. The largest checked digital transition-to-ground distance is 4.003 mm at I2C2_SCL; others above 2 mm are listed in `validation/signal_via_ground_proximity_final.json`. High-current/gate routing, USB differential-pair review, the 33 inherited DRC errors, and silkscreen/final cleanup remain.
