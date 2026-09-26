# Predict, change, explain

Write a prediction before moving a slider. Try to explain the result using a current path or an equation, not only “the plot went up.” Answers are below each exercise so this can be used independently.

## 1. What is the capacitor doing?

In the default half-bridge example, approximately 20 A flows through the winding at 50% duty. Assume source current is constant over a PWM cycle. Predict source current and capacitor current during ON and OFF.

**Answer:** mean source current ≈10 A. During ON the capacitor supplies the missing ≈10 A; during OFF the source recharges it at ≈10 A. Capacitor average current is zero in steady state. Its RMS current is about 10 A, so it can heat despite zero mean.

## 2. Frequency or motor inductance?

Record winding ripple at 20 kHz / 100 µH. Double frequency, restore it, then double inductance.

**Answer:** both approximately halve ripple around this operating point. The default ripple is about 4.50 A p-p. Doubling frequency approximately doubles switching events per second, so it may increase switching-related losses; doubling inductance is not a free motor change either.

## 3. Battery current versus phase current

In the single-leg model, can winding current exceed average battery current? In the supplied three-phase example, what is the predicted mean input current at 40 Arms, m=0.8 and 30° displacement?

**Answer:** yes. A switching converter trades voltage and current; compare power, not just current. For the three-phase ideal waveform, `(3/4)×0.8×sqrt(2)×40×cos(30°) ≈29.394 A`. This is not a universal 40 Arms-to-battery-current conversion.

## 4. Choose a capacitor from a pulse

A capacitor must supply 20 A for 5 µs, and charge-related voltage drop must stay below 0.5 V. Find effective C.

**Answer:** `C ≥ IΔt/ΔV = 200 µF`. This applies to the specified missing-current pulse, not necessarily to our entire PWM cycle. ESR and ESL add other effects.

## 5. What does doubling C fail to halve?

In the capacitor lab, double the number of identical capacitors while holding I, D and f fixed. Predict charge-related ripple, total RMS bank current, per-part current and resistive loss.

**Answer:** charge-related ripple halves. Total required bank RMS current stays approximately unchanged in this model. Equal-share per-part current halves. Internal-part loss drops, but the fixed common connection resistance still dissipates the same `I²R` loss. The cable-network model may change the actual bank current because current sharing also changes.

## 6. Nameplate arithmetic

Forty 4.7 µF parts retain 50% at the operating bias. How much effective C is available? At 20 A, D=0.5 and 20 kHz, what is the simple charge ripple?

**Answer:** 94 µF. Ripple is `20×0.25/(20000×94e−6) ≈2.66 V p-p`. The 50% is an assumed sensitivity point, not a manufacturer claim. The full three-phase/cable model uses different assumptions and need not give this result.

## 7. A mechanical-looking resonance

For L=1 µH and C=100 µF, calculate f0. With total damping resistance 52 mΩ, estimate ζ. Double C and predict f0.

**Answer:** f0≈15.9 kHz, ζ≈0.26. Doubling C lowers f0 to about 11.3 kHz and increases ζ to about 0.368 if R and L remain unchanged. More C changes the dynamics, not just a vertical scale on a plot.

## 8. Could a capacitor absorb a stop?

How much extra energy fits in 2,040 µF between 42 and 46 V? How much capacitance is needed for 10 J over that window?

**Answer:** 0.359 J; about 56,818 µF. The existing bank's total 1.799 J at 42 V is not its remaining overvoltage headroom. A 94 µF example bank has about 0.0165 J headroom in the same window.

## 9. The cost of a shared copper segment

At 40 A, a 0.5 mΩ shunt gives 20 mV. Suppose a poorly placed sense return includes another 0.1 mΩ of force-current copper. What error results?

**Answer:** 4 mV additional input, equivalent to 8 A. The indicated current becomes 48 A if the added drop has the same polarity. Kelvin routing removes that shared contribution; calibration at one operating condition does not reliably remove all current/temperature-dependent errors.

## 10. Is the bus filter just 1 kΩ × 10 nF?

Find the time constant of R103=270 kΩ, R104=270 kΩ, R105=27 kΩ, R106=1 kΩ and C108=10 nF.

**Answer:** `(540k || 27k + 1k) ×10nF =267.14 µs`, meaning the parallel combination is calculated before adding 1 kΩ. Cutoff is 595.77 Hz. The divider's output resistance is essential. Mux and ADC effects are omitted from this first model.

## 11. Spend the phase budget

At 2 kHz, compare τ=10 µs and τ=100 µs. Add 25 µs sample-to-actuation delay.

**Answer:** filter lag is about 7.16° or 51.49°. Delay adds 18°, giving about 25.16° or 69.49° additional lag. These are not the complete loop margins. More smoothing is not automatically better control.

## 12. A placement estimate

A 40 A change takes 80 ns. Compare 3 nH and 30 nH connections. Does changing 100 µF to 1,000 µF directly remove this inductive term?

**Answer:** `LΔI/Δt` gives 1.5 V and 15 V. More capacitance does not directly remove the shared inductance; changing geometry can. These estimates are voltage across that inductance, not a complete device stress calculation.

## Final exercise: write a decision

Choose an illustrative bus-ripple objective, a current/PWM envelope and a capacitor-retention assumption. Use the simple pulse equation for a starting value, then inspect the network impedance and three-phase examples. Explain why the answers differ.

Fill in:

1. My assumed operating case is ...
2. My allowable variation is ... and I chose that limit because ...
3. My first effective-C estimate is ...
4. My nameplate-C estimate is ... given the assumed bias/tolerance reduction.
5. My resonance and branch-current concerns are ...
6. I would place the capacitors ... because ...
7. The first measurements I need are ...
8. My decision would change if ...

There is no single correct final capacitor count without an agreed operating envelope and part curves. A good answer makes its assumptions testable rather than disguising them as a universal design rule.
