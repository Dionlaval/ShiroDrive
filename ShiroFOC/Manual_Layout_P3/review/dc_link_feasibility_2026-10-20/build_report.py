"""Reproduce the proposed ten-capacitor DC-link feasibility study. Requires numpy.
No schematic/PCB files are modified. Run from any directory.
"""
from pathlib import Path
import csv
import json
import math
import numpy as np
from pwm_model import sweep
from source_model import response

OUT = Path(__file__).resolve().parent
# Approximate visual readings of Samsung's typical DC-bias graph, article p3.
# These are NOT minimum specified capacitances; rounded deliberately.
CAP_UF = {18: 68, 24: 55, 36: 39, 42: 33}
SAMSUNG = 'https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/3563/CL32Y106KCVZNWE_Tech_Article.pdf'
MOTEUS = 'https://github.com/mjbots/moteus/blob/8f747f4ac448d117c1390b77ca2d80c27e751a56/hw/controller/r4.11/controller.sch'
MSETUP = 'https://mjbots.github.io/moteus/guides/electrical-setup/'
MSPEC = 'https://mjbots.com/products/moteus-r4-11'

theta = np.linspace(0, np.pi/3, 1001)
coefficients = {}
for pf in [1., .9, .8, .7, 0.]:
    best = (0., 0.)
    for m in np.linspace(0, 2/np.sqrt(3), 401):
        k, rms, times, ibus, avg = sweep(m, np.full_like(theta, np.arccos(pf)), theta)
        assert np.all(np.abs(np.sum(ibus*np.diff(times, axis=-1),axis=-1)-avg)<1e-12)
        if k.max() > best[0]: best = (float(k.max()), float(m))
    coefficients[str(pf)] = {'max_k': best[0], 'm_at_max': best[1]}
assert abs(coefficients['1.0']['max_k']-.125)<1e-6
assert abs(coefficients['0.0']['max_k']-.25)<1e-6
rows = []
for v,c in CAP_UF.items():
    for f in [20,30,40]:
        for i in [5,10,15,20,25,30]:
            ripple = .125*math.sqrt(2)*i/(f*1e3*c*1e-6)
            rows.append(dict(bus_V=v, effective_uF_typical=c, pwm_kHz=f, phase_Arms=i,
                unity_pf_Vpp=ripple, unity_pf_percent=100*ripple/v,
                pf_08_Vpp=ripple*coefficients['0.8']['max_k']/.125,
                all_pf_envelope_Vpp=2*ripple, sensitivity_72pct_C_Vpp=ripple/.72))
with open(OUT/'ripple_sweep.csv','w') as stream:
    w=csv.DictWriter(stream,fieldnames=rows[0].keys()); w.writeheader();w.writerows(rows)
source_rows=[]
for l in [.1,.2,.5,1.,2.]:
    source_rows.append(dict(loop_uH=l, resonance_kHz=1/(2*np.pi*np.sqrt(l*1e-6*33e-6))/1e3,
        Vpp=response(l*1e-6,33e-6,.05,20e3,10*np.sqrt(2))))
results={'assumptions':{'capacitors':'10 x Samsung CL32Y106KCVZNWE, no other capacitance credited',
    'current':'balanced sinusoidal phase RMS; peak=sqrt(2)*RMS; frozen within a PWM period',
    'pwm':'center-aligned min/max-injected sinusoidal PWM, linear modulation only',
    'source_for_main_table':'constant switching-cycle-average current, not a universal ripple bound',
    'capacitance_uF_typical':CAP_UF, 'sensitivity_C_factor':.72,
    'source_R_ohm_for_RLC_examples':.05,'source_example_phase_Arms':10,
    'source_example_C_uF':33,'source_example_pwm_kHz':20},
    'coefficients':coefficients,'source_examples':source_rows,
    'regen_energy_42_to_45p8_mJ':.5*33e-6*(45.8**2-42**2)*1000,
    'sources':[SAMSUNG,MOTEUS,MSETUP,MSPEC]}
(OUT/'results.json').write_text(json.dumps(results,indent=2))

# Standalone scientific plot. Straight lines follow the charge-balance model,
# not fitted measurements. Voltage-independent source dynamics are excluded.
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="580" viewBox="0 0 1000 580">',
 '<rect width="1000" height="580" fill="#101b2b"/>',
 '<g font-family="Arial,sans-serif" fill="#edf4fa">',
 '<text x="65" y="35" font-size="23">Ten local ceramics: calculated PWM bus ripple</text>',
 '<text x="65" y="61" font-size="14">Unity power factor, maximum over modulation / electrical angle; typical biased capacitance</text>']
def xy(i,p):return (85+i/30*800,480-p/30*350)
for p in range(0,31,5):
    x,y=xy(0,p);svg += [f'<path d="M85 {y} H885" stroke="#314053"/>',f'<text x="43" y="{y+5}" font-size="14">{p}%</text>']
for i in range(0,31,5):
    x,y=xy(i,0);svg += [f'<text x="{x-8}" y="505" font-size="14">{i}</text>']
for v,f,col,dash in [(24,20,'#65d8e4',''),(42,20,'#ffb96b',''),(24,40,'#65d8e4','7 5'),(42,40,'#ffb96b','7 5')]:
    p=.125*np.sqrt(2)*30/(f*1e3*CAP_UF[v]*1e-6)/v*100
    x,y=xy(30,p);svg += [f'<path d="M85 480 L{x} {y}" fill="none" stroke="{col}" stroke-width="3" stroke-dasharray="{dash}"/>']
for p,label in [(5,'5% design target'),(10,'10% review threshold')]:
    x,y=xy(0,p);svg += [f'<text x="660" y="{y-7}" font-size="13" fill="#c1ccda">{label}</text>']
svg += ['<text x="320" y="539" font-size="16">Phase current (A RMS, not battery current)</text>',
 '<text x="85" y="95" font-size="14" fill="#65d8e4">24 V: 55 µF</text>',
 '<text x="280" y="95" font-size="14" fill="#ffb96b">42 V: 33 µF</text>',
 '<text x="480" y="95" font-size="14">Solid: 20 kHz • Dashed: 40 kHz</text>',
 '<text x="85" y="566" font-size="13">Not a hardware rating. Supply resonance, switching spikes, capacitor heating and thermal limits are additional.</text>', '</g></svg>']
(OUT/'ripple.svg').write_text('\n'.join(svg))
def table(headers, data):
    return '<table><thead><tr>'+''.join('<th>'+str(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in row)+'</tr>' for row in data)+'</tbody></table>'
cap_table=table(['Bus voltage','Ten-cap bank, typical','5% ripple current at 20 kHz','At 40 kHz'],[
    [f'{v} V',f'≈{c} µF',f'{.05*v*20e3*c*1e-6/(.125*np.sqrt(2)):.1f} A RMS',f'{.05*v*40e3*c*1e-6/(.125*np.sqrt(2)):.1f} A RMS'] for v,c in CAP_UF.items()])
ripple_table=table(['Phase current','24 V, 20 kHz','42 V, 20 kHz','42 V, 40 kHz'],[
    [f'{i} A RMS']+[f'{.125*np.sqrt(2)*i/(f*1e3*CAP_UF[v]*1e-6):.2f} Vpp' for v,f in [(24,20),(42,20),(42,40)]] for i in [5,10,15,20,25]])
source_table=table(['Supply-loop inductance (assumed)','LC resonance','Calculated bus ripple'],[
    [f'{r["loop_uH"]} µH',f'{r["resonance_kHz"]:.1f} kHz',f'{r["Vpp"]:.2f} Vpp'] for r in source_rows])
html=f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>P3 DC-link feasibility — ten ceramic capacitors</title>
<style>body{{font:17px/1.55 system-ui,sans-serif;color:#203047;background:#f3f6fa;margin:0}}main{{max-width:1050px;margin:auto;padding:40px;background:white}}h1,h2{{line-height:1.2}}h1{{font-size:34px}}h2{{margin-top:38px}}a{{color:#075ab8}}table{{border-collapse:collapse;width:100%;font-size:15px;margin:18px 0}}td,th{{padding:10px;border-bottom:1px solid #d9e2ee;text-align:left}}th{{background:#eaf0f7}}.verdict{{background:#e9f4ee;padding:20px;border-left:5px solid #369569}}.scope{{background:#fff2de;padding:16px}}img{{width:100%}}code{{background:#edf1f5;padding:2px 5px}}li{{margin:8px 0}}small{{color:#536478}}@media print{{main{{padding:0}}body{{background:white}}h2,table,img{{break-inside:avoid}}}}</style>
<main><small>ShiroFOC P3 • Focused feasibility study • 20 October 2026 • Discussion only</small>
<h1>Can ten 10 µF ceramics support the motor controller?</h1>
<div class="verdict"><b>Yes, a useful operating envelope is plausible without an external capacitor.</b> The proposed bank does not yet justify a blanket 25 A RMS / 42 V rating. Short supply wiring, PWM frequency, motor operating point and regeneration handling matter as much as nominal capacitance.</div>
<p class="scope"><b>Scope:</b> evaluates your proposed ten-cap bank using the capacitor MPN in P3. The saved schematic still contains the earlier 48 fitted 10 µF capacitors plus six DNP positions. This study intentionally overrides that count with ten and credits no other caps. No PCB or schematic was edited. This is an analytical feasibility study, not a completed board validation or thermal rating.</p>
<h2>1. The capacitance available at operating voltage</h2>
<p>The selected Samsung <b>CL32Y106KCVZNWE</b> is a 10 µF, 100 V, X7S, ±10%, 1210 ceramic. Its voltage rating does not guarantee 10 µF at high bias. Approximate readings from Samsung’s typical DC-bias graph give:</p>{cap_table}
<p>The current columns use the unity-power-factor PWM envelope below and a chosen 5% peak-to-peak target. They are not safe operating limits. The capacitance readings are typical, approximately rounded and have not been temperature/aging qualified. A sensitivity case with only 72% of those values increases ripple by 39%; this is an illustrative allowance (0.9 × 0.8), <b>not a guaranteed combined minimum</b>.</p>
<p>The schematic also includes local 1 µF and 4.7 µF VM capacitors. If retained, their effective capacitance improves these results. For example, an extra effective 10 µF reduces the 42 V result by 33/43 ≈ 23%. Their present placement and effective values are not credited here. Source: <a href="{SAMSUNG}">Samsung article, page 3 DC-bias curve</a>.</p>
<h2>2. Normal switching ripple</h2>
<p>A numerical switching model uses balanced three-phase currents, center-aligned space-vector-equivalent PWM, all electrical angles and the linear modulation range. The supply provides average current during each PWM cycle; the capacitor handles the difference. Charge is integrated exactly between switching events.</p>
<p><code>ΔVpp = k × Iphase,peak / (fPWM × Ceffective)</code>, with <code>Iphase,peak = √2 × Iphase,RMS</code>.</p>
<ul><li>Unity voltage/current power factor: maximum <b>k = 0.125</b>.</li><li>Power factor 0.8: maximum <b>k ≈ 0.165</b>, approximately 32% more ripple.</li><li>Full idealized angle/modulation/power-factor envelope: <b>k = 0.25</b>, twice the unity-power-factor table. This is not a bound on real wiring resonance or switching spikes.</li></ul>
{ripple_table}<img src="ripple.svg" alt="Calculated ripple versus phase current at 24 and 42 volts, 20 and 40 kilohertz">
<p><b>5% is a design target, not a point at which FOC stops working.</b> Around 10% needs closer review of voltage headroom, sampled bus-voltage accuracy, current regulation and protection behavior. At 25 A RMS / 42 V / 20 kHz, the table predicts 6.7 Vpp (16%); poor power factor can increase that, so this is a demanding operating point. At 40 kHz it becomes 3.35 Vpp (8%), before those additional effects.</p>
<h2>3. Why slow robotic joints can be easier</h2>
<p>High phase current at low speed often needs little average winding voltage. Most current then recirculates within the bridge rather than coming in large sustained bursts from the bus. This does not remove winding, MOSFET or shunt heating.</p>
<p>For example, with modulation <code>m = 0.1</code> (phase-voltage fundamental peak = 5% of VM) and unity power factor, k ≈ 0.0347. At 25 A RMS / 42 V / 20 kHz the estimated ripple is <b>1.86 Vpp</b>, versus the 6.7 Vpp maximum over modulation. At m = 0.2 it is about 3.41 Vpp. These examples require a motor whose resistance/back-EMF permits those operating points; they are not blanket stall-current ratings. At standstill, “phase RMS” here means the equivalent sinusoidal current-vector magnitude, not a time average of a rotating waveform.</p>
<ul><li><b>Low-speed positioning, holding, modest torque:</b> plausible use cases; often thermally limited first.</li><li><b>5–10 A RMS while moving:</b> a credible development target with short paired supply wires and controlled regeneration. 20 kHz may be workable; 30–40 kHz gives useful capacitive-ripple margin.</li><li><b>15–25 A RMS while moving:</b> conditional on effective capacitance, motor power factor, PWM and supply wiring. Do not label the entire range supported yet.</li><li><b>High-speed/high-current operation or aggressive reversals:</b> the most demanding cases for this proposed bank. An external capacitor is not the only possible remedy, but ten of these parts cannot establish the rating on paper.</li></ul>
<h2>4. Supply wiring can help—or amplify the ripple</h2>
<p>A close, low-impedance source can supply part of the PWM ripple. However, lead inductance and the ceramic bank also form an LC resonance. “The battery is stiff” alone is insufficient.</p>
<p>The following is an illustrative linear R–L source model: 33 µF, 50 mΩ total series resistance, 20 kHz PWM, 10 A RMS, m = 2/3, unity power factor at the worst unity-PF electrical angle. The input-current waveform is two equal pulses per PWM period, making 40 kHz important. Inductances are assumptions, not measurements or asserted cable-length conversions. Capacitor ESR/ESL, distributed wiring and controller response are omitted.</p>
{source_table}<p>The capacitor-only result for this case is 2.68 Vpp. The assumed 0.5 µH case resonates near 40 kHz and reaches 5.64 Vpp. Thus the main table is neither a guaranteed pessimistic nor optimistic prediction. Measure the actual harness; an RC damping network may address resonance without a large external bulk capacitor. The existing DNP damping provision needs tuning, not blind population.</p>
<h2>5. Regeneration and capacitor heating are separate limits</h2>
<p>Using constant 33 µF, the energy from 42 V to the project’s nominal 45.8 V hardware brake threshold is only <b>{results['regen_energy_42_to_45p8_mJ']:.2f} mJ</b>. At 100 W of net regenerative power that buys about <b>55 µs</b>. Real capacitance decreases further with rising voltage. This threshold is a brake-command threshold from the project document, not a safe absolute voltage rating.</p>
<p>The battery must be able to accept braking energy, or the chopper must have a suitable external resistor, or firmware must limit/dissipate regenerative energy through a validated strategy. A fitted chopper MOSFET with no resistor cannot absorb useful braking energy. This applies even when ordinary PWM ripple is acceptable. A full battery or BMS disconnect also changes the situation. A source-only bench PSU is not equivalent to a receptive battery.</p>
<p>The ideal model reaches capacitor-bank RMS current of about <b>0.5 × phase peak = 0.707 × phase RMS</b>. At 25 A RMS that is up to 17.7 A RMS for the bank, or 1.77 A per capacitor with perfect sharing. Actual sharing, ESR versus frequency, bias and temperature must be checked. No Samsung ripple-temperature curve or board thermal model was validated in this study. Higher PWM frequency reduces capacitive voltage ripple but does not proportionally remove capacitor RMS current; it also raises switching losses.</p>
<h2>6. What the moteus comparison actually shows</h2>
<p>The public <a href="{MOTEUS}">r4.11 schematic at the pinned commit</a> has <b>C22–C37: sixteen 10 µF, 50 V TDK C3216X7R1H106K160AE capacitors</b> on V+ to V−, plus smaller decouplers. C40–C54 are DNP. That is 160 µF nominal versus your proposed 100 µF. Both parts lose capacitance with DC bias; a numerical effective-capacitance ratio between the two has not been established here.</p>
<p>The <a href="{MSPEC}">product page</a> gives 10–44 V operation, 100 A peak phase current, 12/32 A continuous without/with thermal management and 15–60 kHz PWM. Do not equate its advertised current values to this report’s sinusoidal RMS values without confirming the current convention. Its <a href="{MSETUP}">electrical guide</a> explicitly discusses hot-plugging, wiring and regeneration, and recommends lower voltage for sharp regenerative loads without a continuously receptive battery.</p>
<p><b>Your architecture is credible.</b> Similar footprint and headline current are not enough to transfer moteus’s tested operating envelope to P3, especially with a different capacitor bank and firmware.</p>
<h2>7. Decision and minimum validation</h2>
<p><b>Keep the no-external-cap objective.</b> Treat roughly 5–10 A RMS with short power wiring as an initial development envelope, then expand it using measurements. For 20–25 A RMS motion, investigate 30–40 kHz and/or greater effective capacitance within the available footprint before committing to a rating. At 42 V the limited headroom to the brake thresholds makes transient behavior particularly important. Lower voltage helps headroom, although the percentage PWM-ripple calculations are surprisingly similar across 18–42 V because capacitance increases as voltage falls.</p>
<ol><li>Measure VM-to-power-GND at the bridge with a suitable differential probe, including startup, current steps, steady PWM, deceleration and reversals. Use both a bandwidth-limited ripple view and full-bandwidth spike view. Do not connect an earth-referenced probe ground to a switching node.</li><li>Use the actual shortest and longest intended paired supply harnesses, at minimum and maximum bus voltage. Log brake activation and current-loop errors, not only bus averages.</li><li>Test low/mid/high modulation at 5, 10, 15, 20 and 25 A RMS only as thermal/current/protection measurements permit; compare 20 and 40 kHz. Check maximum instantaneous bus voltage and minimum voltage headroom, not only Vpp.</li><li>Measure capacitor and bridge temperatures and confirm current-sampling windows/deadtime/firmware execution at the chosen PWM frequency. Validate loss of regenerative sink.</li></ol>
<p><b>Limits of this study:</b> no full PCB DRC, parasitic extraction, motor R/L identification, temperature simulation, component-lifecycle review or hardware test. No SPICE executable was available; the accompanying NumPy models perform ideal switching charge integration and exact linear state-transition calculations. Source-model examples assume ideal constant capacitance and do not capture closed-loop motor/source interactions. Motor phase-current ripple within each PWM cycle is omitted; a very low-inductance motor can add substantial ripple beyond this model. Other local capacitors were excluded deliberately. A reproducible numerical model is evidence for feasibility, not proof of a safe board rating.</p>
<p>Artifacts: <a href="ripple_sweep.csv">numerical sweep CSV</a> • <a href="results.json">assumptions and coefficients</a> • <a href="pwm_model.py">PWM model</a> • <a href="source_model.py">source model</a> • <a href="build_report.py">report generator</a>.</p></main></html>'''
(OUT/'report.html').write_text(html)
print(json.dumps({'coefficients':coefficients,'source_examples':source_rows,'report':str(OUT/'report.html')},indent=2))
