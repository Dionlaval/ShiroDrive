"""Assemble source tables, worked decision record and a runnable notebook."""
from pathlib import Path
import json, math
R=Path(__file__).resolve().parents[1]
D=R/'docs'
D.mkdir(exist_ok=True)
d=json.loads((R/'data/board_inputs.json').read_text())
comp=d['components']
lines=['# Board inputs and evidence','',
'Snapshot: **19 September 2026**. Nominal circuit values are extracted from the P1 schematic and cross-checked against its exported netlist. P0 placement is unrouted. The user selected adjustable example motor and wiring values.','',
'## Actual circuit values','',
'Confidence is high for nominal values and fitted state, based on project files. This does not establish measured capacitance, electrical tolerances or qualified operating limits.','',
'| Reference | Schematic value | Fitted? | MPN, when assigned |','|---|---|---|---|']
for ref,c in comp.items():lines.append(f"| {ref} | {c['value']} | {'No (DNP)' if c['dnp'] else 'Yes'} | {c.get('mpn') or 'Specification only'} |")
lines += ['', 'C101–103: VM to GND. C412/C422/C432: VM to GND. C415/C425/C435: VM to the respective source-above-shunt net. C414/C424/C434: optional feedback capacitors, **not fitted**.', '',
'## Design targets and firmware intentions','',
'| Quantity | Value | Evidence/status |','|---|---|---|',
'| Bus | 18–42 V | Design target, not demonstrated rating |',
'| Continuous phase current | 25 Arms passive / 40 Arms with cooling | Target; thermal qualification pending |',
'| Short peak phase current | 80 A, up to 2 s subject to limits | Target, not a capacitor sizing waveform |',
'| Initial PWM | 20 kHz centre-aligned | Firmware contract |',
'| Initial deadtime | 500 ns | Conservative bring-up intention, characterise later |',
'| Current-sense gain | 28, 14 mV/A with 0.5 mΩ | Resistor-network calculation |',
'| Gate supply | 8 V startup, firmware selects 10 V | Design/firmware intention |',
'| Brake firmware start | Around 43 V for 10S | Initial control intention |',
'| Brake backup | About 45.92 V rising / 44.21 V falling | Nominal calculation; tolerances and delay apply |',
'| Board | 80 × 80 mm current placement; 2/0.5/0.5/2 oz copper | Existing P0 geometry and stack intent |','',
'## Explicit example assumptions','',
'| Input | Default | Why / how to replace it |','|---|---|---|',
'| Example source | 36 V | Within target range; slider covers 18–42 V |',
'| Winding R and L | 0.1 Ω, 100 µH | Teaching load; use motor phase data, distinguishing phase vs line-to-line measurement |',
'| Source/cable loop R and L | 50 mΩ, 1 µH | Includes positive and return paths; not inferred from a claimed cable length |',
'| Ceramic retention | 50% | Sensitivity only; replace with chosen MPN bias/temperature/tolerance data |',
'| Ceramic part ESR/ESL | 20 mΩ, 1 nH | Lumped examples, not the moteus part specification |',
'| Shared bank connection | 1 mΩ, 3 nH | Geometry assumption; explore 1–50 nH |',
'| Existing bulk ESR | 30 mΩ per can; 10 mΩ combined | Teaching estimate, not datasheet extraction |',
'| Selected local bypass C | 7.81 µF nominal × 0.5 | C104–106 plus C412/C422/C432; auxiliary branches excluded |',
'| Three-phase operating point | 40 Arms, m=0.8, 30° current lag, 250 Hz electrical | Prescribed sinusoidal-current SPWM example; not a closed-loop FOC simulation |',
'| Edge smoothing | First-order τ=80 ns | Finite-edge approximation, not 80 ns rise time or vendor switching model |',
'| Gate example | Qgd=12 nC, plateau=4 V, driver/internal R=3 Ω | Explicit hypothetical numbers; editable in JS source |','',
'## Provenance','',
f"Netlist: `{d['source']}`",'',f"SHA-256: `{d['source_sha256']}`",'',
'Source documents are linked in [SOURCES.md](SOURCES.md). Machine-readable inputs are in [board_inputs.json](../data/board_inputs.json). The automated analyzer includes heuristic findings; this package uses the checked values and does not endorse its unreviewed findings.','']
(D/'BOARD_INPUTS.md').write_text('\n'.join(lines))

x=json.loads((R/'data/comparison.json').read_text())
table='| Scenario | Effective C, µF | Bus variation, V p-p | Capacitor branch RMS, A | Estimated resistive loss, W |\n|---|---:|---:|---|---:|\n'
for name,a in x.items():
    table+=f"| {name} | {a['effective_C_uF']:.1f} | {a['bus_pp_V']:.2f} | {' / '.join(f'{z:.2f}' for z in a['branch_rms_A'])} | {a['estimated_ESR_loss_W']:.2f} |\n"
record='''# Worked decision record

Status: educational engineering conclusions, 19 September 2026. The schematic and PCB remain unchanged. These are model-supported directions and conditional examples, not released part selections.

## 1. Onboard capacitor architecture

**Direction:** use distributed onboard ceramics as the next architecture to investigate. Large electrolytic cans are not compulsory. Preserve the option for external bulk capacitance without assuming it must be fitted.

**Evidence:** the published moteus-n1 r1.3 schematic uses 40 × 4.7 µF / 100 V ceramics in its main bank. That establishes feasibility of the architecture, not equivalence to our operating conditions. Our own model compares several candidate banks under identical assumptions.

### Worked three-phase case

36 V source, 40 Arms sinusoidal phase current, 20 kHz SPWM, m=0.8, current lag 30°, electrical frequency 250 Hz, source loop 50 mΩ / 1 µH. Ceramic retention is assumed 50%; parasitics are listed in the model guide.

'''+table+'''
Branch currents in multi-branch rows are ordered: bulk then local for the existing case; ceramic then external bulk for the hybrid. Resistive losses include the assumed common connection resistance. They are not temperature predictions or capacitor ripple-current ratings.

### What to learn from these numbers

- The largest nominal capacitance does not guarantee the smallest switching variation because placement inductance and network resonances matter.
- In the 40-ceramic example, 94 µF effective and assumed source impedance produce about 7.72 V p-p—not the single-leg charge-only estimate. The current waveform and supply model differ.
- The hybrid gives lower voltage variation in this example but substantial estimated resistive heating in its assumed external electrolytic branch. Adding bulk is not a free fix.
- The 20-ceramic case produces large voltage movement. Since phase currents are prescribed and do not respond to bus voltage in this model, its numerical result is best treated as a warning about this assumed case, not a precise physical prediction.
- These results do not prove the existing hardware fails. Its actual parasitics and operating envelope are unknown, and the PCB is not routed. They demonstrate which quantities should be measured and why nominal µF alone is insufficient.

![Sensitivity to assumed wiring and capacitance](../figures/10_sensitivity.svg)

### A conditional design choice you can defend

For **this teaching case only**, choose an illustrative objective of at most 4 V p-p bus variation. The 80-part ceramic case gives about 3.20 V p-p and is a candidate under these assumptions. Its nameplate capacitance is 376 µF; effective capacitance is assumed 188 µF. The 4 V budget is an educational choice, not an approved board specification. This does not yet include a validated margin at 42 V or the full current/modulation envelope.

A first pulse-budget calculation is separate: to keep a 20 A, D=0.5, 20 kHz single-leg case below 1 V charge ripple requires 250 µF effective. At 4.7 µF per part, assumed 50% bias retention and a further 10% tolerance allowance, `ceil(250/(4.7×0.5×0.9)) = 119` parts. This deliberately different result shows why a current waveform and an agreed voltage budget must be stated before announcing a capacitor count.

**Final board count remains open.** Choose it after obtaining the actual capacitor bias/ESR data, a defined source/wiring envelope, modulation and current envelope, and the permissible bus variation. Use the learning model to narrow candidates, then validate with hardware measurements. No parts-availability search is needed to understand these tradeoffs.

## 2. Local bypass placement

**Decision:** put useful capacitance close to each half bridge and minimise its complete outgoing/return loop. Use bottom-side parts where a paired via path is genuinely shorter.

**Reason:** 40 A changing in 80 ns gives 1.5 V across 3 nH but 15 V across 30 nH. Increasing C does not remove that shared connection term. These are scale estimates, not complete overshoot predictions.

Preserve the different return nodes of the 1 µF VM–GND capacitors and the 10 nF VM–MOSFET-source bypasses. Place new banks around the three cells rather than collecting them remotely for visual symmetry alone.

## 3. Braking and connection method

**Decision:** retain a defined path for braking energy and treat battery connection as a separate transient design problem.

The 2,040 µF bank has 0.359 J additional storage between 42 and 46 V; the 94 µF example has 0.0165 J. Neither absorbs a typical multi-joule stop by itself. The brake resistor/supply must handle the remaining energy. Smaller C also gives the overvoltage controls less time to react.

Do not interpret the model's unclamped connection peak as an actual allowed stress. Select and model a connection/precharge strategy before final power-stage validation. The current hardware does not claim onboard precharge.

## 4. Sensing and control

**Decision:** retain dedicated Kelvin sensing, start with the actual DNP state, and choose filtering together with sampling/actuation timing.

At 40 A, 0.1 mΩ of unwanted shared copper adds an 8 A equivalent error. A 100 µs first-order filter adds about 51.5° lag at 2 kHz, compared with 7.2° for 10 µs; 25 µs extra delay adds 18° more. These effects materially change measurement and control quality.

The actual bus filter is about 596 Hz, derived from the divider's Thevenin resistance plus R106. It must not be reused as the phase-current-loop filter model. Optional C414/C424/C434 are unfitted, and fitting them changes high-frequency path matching.

## 5. Placement revision still pending

The learning package annotates existing P0 coordinates. It does not implement P1: mounting holes on PCB, reclaiming top-centre space, parallel/closer phase outputs and MOSFETs, or a new ceramic bank. Those remain hardware tasks. Four mounting symbols already exist in the P1 schematic.

## What measurements resolve the assumptions?

| Measurement | Which uncertainty it resolves |
|---|---|
| Effective capacitor C and impedance versus bias/frequency, from selected part data | Whether nameplate count supplies the assumed C/ESR |
| Source loop impedance / measured bus response with intended leads | Where resonance sits and how strongly it is damped |
| Bus voltage close to each half bridge, with an appropriate short-loop probe | Actual local switching stress and spatial differences |
| Capacitor branch current or validated loss estimate, plus temperature | Current sharing and thermal suitability |
| Gate/source and drain/source switching waveforms | Gate resistor tuning and local inductance |
| ADC reading versus an independent current measurement across PWM duty | Offset, gain, switching artifacts and valid sampling windows |
| Brake response to a controlled known energy return | Threshold timing, bus rise and resistor energy margin |

Begin hardware checks at limited energy/current with suitable instruments. This is a learning validation sequence, not a detailed commissioning procedure.
'''
record=record.replace('about 7.72 V',f"about {x['40 ceramics']['bus_pp_V']:.2f} V").replace('about 3.20 V',f"about {x['80 ceramics']['bus_pp_V']:.2f} V")
(D/'DECISION_RECORD.md').write_text(record)

cells=[]
def md(s):cells.append({'cell_type':'markdown','metadata':{},'source':s.splitlines(True)})
def code(s):cells.append({'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':s.splitlines(True)})
md('# ShiroFOC computational companion\nUse the offline HTML lab for sliders and docs/NOTEBOOK.md for the guided explanation. This notebook exposes the reproducible Python model. Example motor and parasitic values are assumptions, not measurements. Run from this learning directory or the repository root.')
code("from pathlib import Path\nimport sys, json\nroot = Path.cwd() if Path('models/build_models.py').exists() else Path.cwd()/'learning'\nsys.path.insert(0, str(root/'models'))\nimport build_models as model\nimport numpy as np\nimport matplotlib.pyplot as plt\nfrom IPython.display import display, SVG\nprint('Learning directory:', root)")
md('## 1. Inputs\nPredict which inputs are measured, design intent or assumptions before opening the file.')
code("inputs = json.loads((root/'data/board_inputs.json').read_text())\ninputs['assumptions']")
md('## 2. One half bridge\nChange the winding L and PWM frequency. E is adjusted to hold the selected mean current; this is not a speed transient.')
code("t, voltage, winding, bridge, emf = model.half_bridge(v=36, d=0.5, fsw=20000, l=100e-6, r=0.1, mean_i=20)\nplt.figure(figsize=(9,4))\nplt.plot(t*1e6, winding, label='Winding')\nplt.plot(t*1e6, bridge, label='Bridge bus draw')\nplt.xlabel('Time (us)'); plt.ylabel('Current (A)'); plt.legend(); plt.show()")
md('## 3. Impedance and current sharing\nChange number of ceramics, retention and connection inductance. Are the dominant frequencies still away from the switching excitation?')
code("branches = [model.ceramic(40, retention=0.5, connection_nh=3)]\nf = np.logspace(1,8,1500)\nz, zs, zc = model.network(f, branches, rs=0.05, ls=1e-6)\nplt.figure(figsize=(9,4)); plt.loglog(f, abs(z))\nplt.xlabel('Frequency (Hz)'); plt.ylabel('Bus impedance (ohm)'); plt.show()")
md('## 4. Three-phase periodic response\nThe phase currents are prescribed sinusoids. Bus voltage does not feed back into them; high-ripple cases exceed the model’s useful precision.')
code("t, v, load, source, caps, metrics = model.periodic_result(branches)\nprint(json.dumps(metrics, indent=2))\nplt.figure(figsize=(9,4)); plt.plot(t*1e3, v)\nplt.xlabel('Time (ms)'); plt.ylabel('Bus voltage (V)'); plt.show()")
md('## 5. Load step and uncharged connection\nCompare initial conditions. No clamps, precharge or current limits are included.')
code("for startup in [False, True]:\n    t, out = model.rlc_response(c=94e-6, rc=0.0015, rs=0.05, ls=1e-6, startup=startup)\n    plt.plot(t*1e3, out[:,0], label='Connection' if startup else 'Load step')\nplt.xlabel('Time (ms)'); plt.ylabel('Bus voltage (V)'); plt.legend(); plt.show()")
md('## 6. Energy and delay\nReplace these values with your own example, then explain why energy buffering and measurement filtering are different design problems.')
code("C = 94e-6\nprint('Extra energy from 42 to 46 V:', 0.5*C*(46**2-42**2), 'J')\nf_eval, tau, delay = 2000, 10e-6, 25e-6\nprint('Filter lag:', -np.degrees(np.arctan(2*np.pi*f_eval*tau)), 'deg')\nprint('Delay lag:', -360*f_eval*delay, 'deg')")
md('## 7. Rebuild and inspect validation\nThis writes learning figures/data only. See qa/VALIDATION.md for physical limitations and the unsuccessful SPICE attempt.')
code("model.build()\njson.loads((root/'qa/numerical_checks.json').read_text())")
md('## 8. Your decision\nRecord an operating envelope, voltage budget, capacitor assumptions, placement rationale and the two measurements most likely to change your answer. Use docs/DECISION_RECORD.md as a worked example.')
notebook={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'}},'nbformat':4,'nbformat_minor':5}
for j,c in enumerate(cells):c['id']=f'lesson-{j:02d}'
(R/'ShiroFOC_learning.ipynb').write_text(json.dumps(notebook,indent=2)+'\n')
print('Wrote inputs, decision record and computational notebook.')
