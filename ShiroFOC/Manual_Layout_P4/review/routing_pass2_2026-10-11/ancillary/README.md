# Ancillary routing candidate

Best candidate: `io2/ShiroFOC_Manual.kicad_pcb`, based on pass2 `power_fed`.
`delta.json` contains exact UUID additions/removals in three indivisible groups.
`validation_delta.json` is a native geometry/DRC PASS: 39 new items, eight
intentional removals, no modified existing objects, no footprint changes, and
all new tracks/vias meet 6 mil / 0.5 mm pad / 0.3 mm drill requirements.

Changes:

- U203 OV1: joined front R210 to the back-side divider/pin. Replaced four
  CP2/PR1 back-side fanout segments to open the corridor, then reconnected both
  neighboring nets. The OV1 cross-side route is 10.22 mm with two vias.
- UART bridge RX: removed two clearance-violating dangling tail tracks and
  their unused via near R902. Joined R903 to U901 using the existing R903
  through-via, approved L4 routing, and one new transition via; 28.57 mm.
- External feedback IO2: removed the via violating clearance to R607 and
  reconnected the D601/R606 network through a legal new transition. Also joined
  D601's same-net pass-through pads. Added 3.14 mm total and one via.

Native DRC: 30 errors / 385 warnings / 321 unconnected versus the power_fed
baseline's 33 / 387 / 322, with zero new error pairs. The three resolved errors
are the two UART tail clearances and the external feedback IO2 via clearance.

Integration condition: the UART L4 clearance cut creates two additional 3V3
airwires after zone refill, around the supply groups at (-10.03, 1.28),
(-7.85, -1.17), and (-14, 1.85). Reconnect those supply groups in the combined
board, or omit the entire UART group. Three signal airwires close, explaining
the net reduction of one in the raw candidate.

Remaining scoped nets:

- OV2: the back-side divider/pin remains inside a pad/track pocket with no
  legal 0.5/0.3 transition site. The attempted CP2/PR1 reroute did not free it.
- BRAKE_PWM: U4.60 can reach a small front pocket but no legal via site; VM
  decoupling, SPI-series resistor pads, and existing fanout/stitching occupy the
  exit. No unsafe route or footprint change was applied.

All candidate and debug files are separate from the working project.
