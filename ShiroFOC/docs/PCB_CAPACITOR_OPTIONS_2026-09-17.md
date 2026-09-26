# Historical capacitor options — 2026-09-17

Superseded by the 2026-09-19 decision to retain C101–C103. This records the earlier options discussion, not the active P1 work list.

## DC-link capacitor decision

### Recommended direction

Use **a hybrid DC link**: effective ceramic capacitance physically close to each bridge, with bulk electrolytic capacitance at a convenient board edge. This can free the present row of three large cans without relying on a distant capacitor for the fastest switching currents.

The edge-mounted bulk connection must be a short, broad VM/GND pair. A capacitor with long flying leads is not equivalent to the same capacitor attached directly to the bus. If its body overhangs the board or lies horizontally, reserve its full mechanical envelope and provide support; do not rely on its leads to carry vibration loads.

### Why not replace all bulk capacitance with small ceramics immediately?

- High-capacitance X7R/X7S ceramics lose effective capacitance under DC bias. At the board's 42 V maximum normal bus voltage, use the selected part's capacitance-versus-voltage curve, tolerance and temperature data, not the printed µF value. [Murata DC-bias explanation](https://www.murata.com/en-sg/support/faqs/capacitor/ceramiccapacitor/char/0005)
- Adding parallel ceramics improves high-frequency current handling and reduces impedance, but does not automatically provide enough stored energy for bus transients.
- An all-ceramic input can resonate with battery-lead inductance. Hot-plug overshoot and damping need assessment; very low ESR is not always beneficial by itself. [TI input ringing and damping](https://www.ti.com/document-viewer/lit/html/SSZTDA5/GUID-A708FC6E-38D2-4FCF-BEB3-0E9E75E1FCEC)
- An all-ceramic bank is possible in principle, but its required effective capacitance, ripple heating, voltage margin, board area and mechanical cracking risk need evaluation before removing the electrolytics.

There is no requirement to reproduce every nominal electrolytic µF with ceramic µF: the two technologies may perform different frequency-domain roles. The combined network must still satisfy bus ripple, transient energy and damping requirements.

### One 1000/2000 µF capacitor versus several 680 µF capacitors

The existing bank is **3 × 680 µF = 2040 µF** (680, rather than 670 µF).

| Option | Assessment |
|---|---|
| One 1000 µF bulk capacitor + local ceramics | About half the existing nominal bulk capacitance. May be sufficient after analysis, but is not an established equivalent replacement. |
| One 2000/2200 µF bulk capacitor + local ceramics | Similar nominal bulk storage. A sensible candidate if its ripple-current rating, ESR, temperature rating, lifetime and bus connection are suitable. One large capacitor is not inherently worse than three smaller ones. |
| Two or three smaller bulk capacitors + local ceramics | Can distribute ripple heating and lower effective ESR/inductance, provided current shares reasonably. More capacitance positions may offer useful placement flexibility. There is no special electrical requirement for 680 µF per phase. |
| Ceramics only | Do not approve solely by adding nominal values. Check effective capacitance and the complete bus network first. |

For identical capacitors with equal current sharing, three in parallel approximately triple the capacitance and divide ESR by three. A different large capacitor may equal or exceed that performance; compare actual specifications rather than can count.

The existing [A0 review](DESIGN_REVIEW_REV_A.md) records only **5.07 Arms summed nameplate ripple capability** for the present bulk bank before frequency/temperature correction and unequal sharing. It already identifies capacitor ripple as a possible limit for the 25/40 Arms phase-current targets. Retaining 2040 µF alone does not resolve that limit, and phase RMS current is not the same quantity as DC-link capacitor RMS current.

The capacitance contribution to ripple follows `delta V = delta Q / C`; ESR and connection inductance add their own voltage excursions. Illustrative only: supplying a 20 A current deficit for 25 µs consumes 500 µC, giving 0.50 V droop with 1000 µF or 0.25 V with 2000 µF, before ESR/ESL. This is not a worst-case calculation for this inverter.

### Work required to choose the replacement

1. Use the existing 18-42 V bus, initial 20 kHz PWM, operating-current envelope and modulation scheme; calculate/simulate capacitor current across operating points. Establish allowable bus ripple and source-lead impedance.
2. Size the local ceramic banks by effective capacitance and RMS heating at operating bias. Preserve the separate above-shunt package bypass and full bridge/shunt-loop bypass functions.
3. Compare one approximately 2 mF edge-mounted bulk capacitor with a parallel bank using actual ESR, ripple-current and thermal/lifetime data. A 1000 µF option must independently meet the requirements.
4. Check hot-plug and load-step overshoot, regeneration/brake response and inrush. Bulk capacitors do not replace the brake chopper or a supply capable of accepting returned energy.
5. Choose the physical bulk package and support arrangement, then replace the old footprints and update schematic/BOM values. If the new board requires an external capacitor, mark it as required for operation, not merely an optional DNP convenience.

This revision does not include stock checks or external fabricator validation, as requested. No capacitor replacement has yet been committed.

