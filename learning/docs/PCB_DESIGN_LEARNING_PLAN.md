# Understanding ShiroFOC PCB Design Decisions

## Purpose

Move from following PCB rules to understanding the system well enough to predict what changes when a component value or its placement changes.

This plan is tailored to a mechanical engineer specialising in robotics, control theory and mechatronics. It connects familiar concepts—energy storage, impedance, disturbances, resonance, damping and transfer functions—to the actual board.

## Goal for the weekend

Build an interactive model of our board, supported by a short learning notebook. By the end, be able to explain:

- What capacitors do during motor switching.
- What changes when capacitance increases or decreases.
- Why placement can matter as much as capacitance.
- What heats capacitors, MOSFETs and shunts.
- Which decisions can be justified analytically, and which need measurements.

Use understandable approximations and make every assumption visible. Models support design decisions; their precision should not be overstated.

## 1. Establish the actual system

Extract the relevant values from the schematic and intended operating conditions:

- Battery voltage and supply cable length.
- Motor resistance and inductance, or a clearly labelled range if unknown.
- Phase current and PWM frequency.
- MOSFET switching characteristics.
- Capacitor values and approximate resistance and inductance.
- Brake circuit thresholds.

**Deliverable:** one annotated power-path diagram and a table of model inputs. Mark every number as a design value, datasheet value or assumption.

## 2. Start with one switching half bridge

Before modelling all three phases, make one understandable.

Show current paths during each switching state, including when motor current continues flowing while a MOSFET is off.

Plot together:

- PWM command.
- Motor voltage and current.
- Current drawn from the supply.
- Current entering or leaving the local capacitor.

Answer the key question: **why can motor current be fairly smooth while the supply sees pulses?**

**Deliverable:** an interactive switching example with adjustable duty cycle, frequency and motor inductance.

## 3. Model the supply and capacitor bank

Build the model in stages so each added detail has an obvious purpose.

| Model | What it teaches |
|---|---|
| Ideal capacitor supplying a current pulse | How capacitance limits voltage change |
| Add capacitor resistance | Instantaneous voltage drop and capacitor heating |
| Add cable inductance and resistance | Supply-voltage oscillation and damping |
| Add capacitor and connection inductance | Why large capacitance alone cannot stop fast spikes |
| Separate nearby and distant capacitors | Why local and bulk describe different jobs |

Start with the familiar relationships:

- `i = C × dv/dt`
- `v = L × di/dt`

Derive the relevant impedance and transfer functions. Explain what their poles and frequency responses mean physically.

**Deliverable:** time-domain plots alongside impedance/Bode plots of the same system.

## 4. Compare concrete capacitor choices

Use our board's operating range to compare:

- The existing three-electrolytic arrangement.
- Several sizes of ceramic-only bank.
- A ceramic bank with an optional external electrolytic.
- The same capacitance placed close to versus far from the MOSFETs.

For each option, plot:

- Bus voltage variation during PWM.
- Capacitor current and estimated heating.
- Response to a sudden load change.
- Connection/startup transient.
- Effective ceramic capacitance as operating voltage increases.

Separate switching pulses from braking energy: they occur on different timescales and may need different solutions.

**Deliverable:** a comparison dashboard where changing a value visibly changes the outcome. Do not assume moteus's capacitor count is automatically correct for our board.

## 5. Connect the electrical model to PCB placement

Translate the plots into actual layout decisions:

- Which current loops must be small.
- Where each capacitor bank belongs.
- Why a narrow connection can undermine a large copper area.
- How gate resistance changes switching speed, losses and ringing.
- Why current-sense connections must avoid shared power-current paths.
- Why MCU decoupling needs short connections to both supply and ground.

**Deliverable:** annotated views of our PCB, with each placement rule linked to a model or waveform.

## 6. Extend the approach to sensing and control

Once the power path makes sense, examine:

- Shunt resistance: signal size, heat and measurement range.
- Amplifier gain: sensitivity versus clipping.
- ADC filtering: noise reduction versus delay.
- PWM-synchronised sampling: avoiding switching disturbances.
- How measurement delay affects the current-control loop.

**Deliverable:** filter response and sampling plots using our actual component values.

## Suggested weekend structure

| Session | Focus |
|---|---|
| Saturday morning | Current paths and one half bridge |
| Saturday afternoon | Capacitor and supply models; interactive comparisons |
| Sunday morning | PCB placement, switching and sensing |
| Sunday afternoon | Choose design values and document the reasoning |

## Teaching format

Use a guided notebook and interactive plots rather than a large presentation. Each section follows:

1. A concrete question about our board.
2. The learner's predicted outcome.
3. A simple model and plot.
4. The physical explanation.
5. The resulting design decision.

Define electrical terminology in plain language when it first appears. Connect equations to physical current paths and observable waveforms, rather than presenting unexplained rules of thumb.

## Final outcome

Produce a short decision record for each important choice:

> We chose this value and placement because this model predicts this behaviour, under these assumptions.

The result should be something the learner can understand, challenge and reuse on future designs.
