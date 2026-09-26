# Model guide: equations, topology and limits

## Read this as a modelling contract

The models explain consequences and compare choices. They do not include a routed PCB extraction, measured motor, measured capacitor bias curve, MOSFET vendor switching model, regulator control loop or complete FOC controller. They should not be used to declare the board fabrication-ready.

All Python functions use SI units. Browser controls display engineering units and convert to SI. The browser runs without network requests.

## A. Half-bridge winding model

Topology: an ideal synchronous half bridge switches a node between 0 and V. A series R–L–back-EMF load connects that node to the fixed reference. This is a buck-equivalent teaching circuit, not a literal isolated phase of a floating-neutral motor.

For switch state q:

`di/dt = (qV − Ri − E)/L`.

For a constant q over Δt:

`i(t+Δt) = i∞ + (i(t)−i∞)exp(−ΔtR/L)`, with `i∞=(qV−E)/R`.

The implementation solves the fixed point across ON and OFF intervals, so plots start in periodic steady state. It sets `E = DV − RĪ` to obtain the requested mean current. This is not a speed trajectory or current-controller simulation. Source current for the capacitor teaching waveform is set to mean bridge current.

The first static plot and lab default use 36 V, D=0.5, 20 kHz, R=0.1 Ω, L=100 µH and Ī=20 A. Deadtime, diode recovery, nonlinear inductance and semiconductor losses are excluded.

## B. Constant-current PWM charge model

Assumptions: winding current I is constant, source current is DI, switch draws I for DT and zero for (1−D)T.

Capacitor current, positive into capacitor:

- ON: `icap = −(1−D)I`.
- OFF: `icap = DI`.

Therefore:

`ΔVcap,pp = ID(1−D)/(fC)`

`Icap,rms = I sqrt(D(1−D))`

`PESR = Icap,rms² RESR`.

The terminal voltage adds `RESR icap`. A switching change makes an ESR step of magnitude `I RESR`. ESL is deliberately excluded from this ideal discontinuous-current time plot: an instantaneous current step through an inductor would imply an impulse. Use finite edge time and the separate frequency/placement models for high-frequency behaviour.

These formulas are not applied directly as a three-phase capacitor rating.

## C. Frequency-domain supply network

The ideal voltage source is reached through `Zs = Rs + sLs`. Each capacitor branch has:

`Zk = Rk + sLk + 1/(sCk)`.

The board sees:

`Zbus = 1 / (1/Zs + Σ1/Zk)`.

Load-current disturbance transfer: `δVbus/δIload = −Zbus`.

Source-voltage disturbance transfer: `δVbus/δVs = Zparallel_caps/(Zs + Zparallel_caps)`.

These are different transfer functions. The plotted impedance phase is the phase of positive Zbus; the minus sign in the load-disturbance relationship adds inversion.

### Assumed branches in the comparison

| Branch | C | ESR used | Series L used |
|---|---:|---:|---:|
| Three existing bulk cans, lumped | 2,040 µF | 10 mΩ combined | 23 nH combined |
| Existing selected local bypasses, lumped | 7.81 µF nominal × 0.5 | 5 mΩ | 3 nH |
| N study ceramics | N × 4.7 µF × 0.5 | 20 mΩ/N + 1 mΩ common | 1 nH/N + 3 nH common |
| Optional external 1,000 µF | 1,000 µF | 30 mΩ | 30 nH |

Only the existing nominal capacitance values come from the schematic. Parasitics and retention in this table are modelling assumptions, not exact datasheet values. The selected local bypasses are C104–106 plus C412/C422/C432. Auxiliary converter inputs and 10 nF source-above-shunt bypasses are excluded. This model does not capture their additional impedance modes.

The N ceramics are treated as equally connected parallel parts. There is no geometric extraction or unequal-sharing model. Thermal predictions stop at resistive power; no temperature is inferred.

## D. Three-phase periodic switching comparison

For phases k with offsets θk = 0, 2π/3, 4π/3:

`dk(t) = 0.5 + 0.5 m cos(ωe t − θk)`

`ik(t) = sqrt(2) Irms cos(ωe t − θk − φ)`

`qk = 1` when the common triangular carrier is below dk, otherwise 0.

`Iload = Σqk ik`.

Default: 20 kHz centre-aligned sinusoidal PWM, 250 Hz electrical frequency, m=0.8, φ=30° and 40 Arms phase current. One electrical period contains 80 PWM periods. We sample 512 times per PWM period, then repeat with 1,024 for a resolution check. Sampling rates are 10.24 and 20.48 MHz respectively.

A first-order 80 ns time-constant filter smooths ideal bus-current edges using an exact sampled recurrence. This avoids artificial undershoot from a truncated continuous filter spectrum. It is an explicit numerical/physical approximation, not a MOSFET model or a stated 80 ns rise time. A first-order 10–90% rise time is about 2.2τ. The phase currents themselves are prescribed sinusoids without winding PWM ripple or feedback from bus ripple.

The FFT of that current excites the passive network independently at each nonzero frequency:

`Vbus(f) = −Zbus(f) Iload(f)`.

The DC bus voltage is `Vs − Rs mean(Iload)`. Capacitor branch current is `Vbus(f)/Zk(f)`, positive into each capacitor. Source current follows KCL. An inverse FFT reconstructs periodic steady-state waveforms. No startup transient is present in this calculation.

The analytical expected mean bus current is:

`Imean = (3/4)m sqrt(2) Irms cosφ ≈ 29.394 A`.

The numerical result differs by less than 0.01%. At DC, capacitor branch currents are zero. Charge balance and KCL are checked. The two representative p-p voltage results change by about 0.74% and 1.10% when time resolution doubles.

### What this can and cannot conclude

It can show current sharing, resonance and relative behaviour under the stated waveform. It cannot claim a final bank count or controller stability. Large predicted bus movement makes the prescribed-current approximation less credible because the real inverter/current controller would respond. This is especially relevant to the 20-ceramic scenario's large variation. Even a small numerical discretisation error does not mean a small physical modelling error.

Distributed three-phase layout has several bus nodes and coupled loops; collapsing them to one node loses spatial information. Changing modulation, power factor, electrical frequency, source impedance, temperature or capacitor retention can change the ranking.

## E. Load-step and connection model

This model uses one capacitor with ESR but no ESL. States are cable current is and ideal capacitor voltage vc. The load draws il.

`vbus = vc + Rc(is − il)`

`Ls dis/dt = Vs − Rs is − vbus`

`C dvc/dt = is − il`.

State matrix:

```text
A = [ −(Rs+Rc)/Ls    −1/Ls ]
    [     1/C          0   ]

B = [ 1/Ls    Rc/Ls ]   inputs [Vs, il]
    [   0     −1/C  ]
```

The Python reference uses SciPy's continuous linear state-space response. The browser independently evaluates the exact 2×2 matrix exponential, including underdamped, overdamped and critically damped cases. There is no Euler integration instability hidden behind the sliders.

Load-step initial conditions: vc=Vs, is=0, then il=20 A.

Connection initial conditions: vc=0, is=0, il=0, then an ideal Vs is connected.

With capacitor ESR, the source-voltage transfer is:

`H(s) = (1+sRcC)/(1+sC(Rs+Rc)+s²LsC)`.

Natural frequency `f0 = 1/(2πsqrt(LsC))` and damping `ζ = (Rs+Rc)sqrt(C/Ls)/2` describe the denominator. The numerator zero affects the observed voltage response. Source-current and capacitor-voltage peaks need not occur together.

Missing: source current limit, diode clamps, precharge, TVS nonlinearity, brake control, voltage-dependent ceramic capacitance, contact bounce, and converter dynamics. Use it to understand the plant and initial conditions, not to approve a connection method.

## F. Braking-energy calculation

For constant C, `ΔE = ½C(V2²−V1²)`. Solving for required C gives `2E/(V2²−V1²)`; solving for final voltage gives `sqrt(V1²+2E/C)`.

The live energy calculator uses 42 to 46 V as an illustrative window independent of the supply model's voltage slider. It models all selected energy reaching the bus and none going elsewhere. Real motor/copper losses reduce returned energy; other loads and charging acceptance change the result. Gravity or externally driven motion can add more energy.

For nonlinear ceramic capacitance, energy change is `∫ v Cdiff(v) dv`, not generally `½ Csmall-signal(V) V²`. The simple fixed-C examples should not be used for a large-signal MLCC energy claim.

## G. Sensing, filters and delay

The fitted resistor network produces nominal gain 28 with 1.65 V bias. Shunts are 0.5 mΩ. The ideal ADC conversion uses 3.3 V/4096, then divides by 0.014 V/A. Resolution is not accuracy.

For a simple hypothetical RC: `H=1/(1+sRC)`. Delay contributes `e^(−sTd)`, with phase `−ωTd` radians. The lab reports their sum at a chosen evaluation frequency, not a calculated closed-loop phase margin.

Actual bus filter: ratio 1/21, and τ=`((540k || 27k)+1k)10nF`. The plotted gain is normalised to DC, so it does not include the constant divider attenuation. Mux on-resistance, ADC acquisition and leakage are excluded.

### Optional feedback capacitor is not a simple differential RC

For one phase, with Rinput=1 kΩ, Rfeedback=28 kΩ, and two 56 kΩ positive-input bias resistors, the positive input's small-signal coefficient from sense-plus is 28/29. If Cf=47 pF is fitted, `Zf=28k/(1+s28kCf)`.

With sense-minus fixed and VREF AC-grounded:

`Hplus(s) = (28/29)[1 + 28/(1+s28kCf)]`.

It has DC gain 28 and high-frequency gain 28/29. Divide by 28 for the normalised plotted response. The sense-minus path is `−28/(1+s28kCf)`, so the two paths no longer cancel common-mode input identically at high frequency. These capacitors are DNP in the actual schematic. Finite op-amp gain/bandwidth and parasitic capacitance are omitted.

The ringing/sampling illustration is synthetic: a known sinusoidal current plus decaying 2 MHz artifacts at chosen edge times. It teaches timing, and is not represented as a simulated or measured amplifier output.

## H. Gate-drive and local-decoupling estimates

Gate experiment assumptions: 10 V drive, 4 V Miller plateau, 12 nC Miller charge and 3 Ω combined driver/internal resistance. External gate resistance is adjustable. `Igate=(10−4)/(Rext+3)` and `tedge=Qgd/Igate`. None of those assumed switching parameters is a characterised value for our assembled CSD88599 stage.

Overlap loss: `½VI(tr+tf)f`, per hard-switched MOSFET with equal estimated tr and tf. Do not multiply by six and treat it as a complete inverter loss model; device conduction states and additional loss terms differ.

The separate inductance spike estimate uses an independently selected current transition time. Gate-voltage slew and commutating-current slew are not interchangeable, so these controls are deliberately not forced to agree.

## I. Validation scope

See [validation notes](../qa/VALIDATION.md). Models are checked against independent identities, conservation, a finer sampling grid and a separate Python/JavaScript transient implementation. Their physical assumptions remain the dominant limitation.

The installed LTspice batch attempt did not produce successful results. The lesson calculations therefore use the documented numerical models; no successful SPICE verification is claimed. Automated schematic detections were not promoted to electrical findings without manual connectivity checks.
