# ShiroFOC Rev A MCU Pinout and Interface Plan

Status: A0 layout-release allocation, checked against the STSPIN32G4 datasheet pin table. The native schematic and this table agree. STM32CubeMX has not been run; generate and verify the complete STM32G431VBx3 firmware configuration before motor commissioning. See [release review](DESIGN_REVIEW_REV_A.md) and [firmware contract](FIRMWARE_BRINGUP_CONTRACT.md).

## Design intent

- Preserve the STSPIN32G4 internal TIM1 gate-driver connections and all three integrated op-amp current-sense paths.
- Support onboard AS5047P ABI feedback, external incremental A/B/Z feedback, or external Hall U/V/W feedback.
- Use TIM4 channels 1, 2, and 3 for the three selected feedback inputs.
- Keep PB8/BOOT0 safe on a blank, assembled board by disabling the feedback mux in hardware during reset.
- Share SPI3 between the BMI323 IMU and AS5047P using independent chip-select signals; do not place a mux in the SPI path.
- Keep FDCAN1, a USB-to-UART service console, and SWD programming/debugging.
- Measure three phase-shunt currents, three MOSFET temperatures, and motor-bus voltage.
- Control a local external brake resistor through a dedicated low-side brake chopper.
- Report thermal state over CAN so system-level cooling can be controlled by the motherboard.

## Rev A external pin map

| STSPIN pin | MCU pin | Net | Peripheral / role | Required details |
|---:|---|---|---|---|
| 3 | PC13 | `SPARE_GPIO_3` | GPIO/EXTI input | Reserve for future expansion; expose as a test pad if practical. |
| 4 | PC14 | `FEEDBACK_ENABLE_N` | GPIO output | Active-low TMUX1574 enable. Add 10 kOhm pull-up to 3.3 V so the mux is disabled throughout reset. |
| 5 | PC15 | `SPARE_GPIO_1` | GPIO | Reserve; also OSC32_OUT if an LSE crystal is later required. |
| 6 | PF0 | `HSE_OSC_IN` | OSC_IN | Dedicated to the 24 MHz HSE crystal in Rev A. Do not use as GPIO/ADC while HSE is fitted. |
| 7 | PF1 | `HSE_OSC_OUT` | OSC_OUT | Dedicated to the 24 MHz HSE crystal in Rev A. Do not use as GPIO/ADC while HSE is fitted. |
| 8 | PG10 | `NRST` | Reset | Route to SWD connector and a reset test point/button. |
| 9 | PC0 | `NTC_PHASE_B` | ADC12_IN6 | Half-bridge B temperature divider. |
| 10 | PC1 | `NTC_PHASE_C` | ADC12_IN7 | Half-bridge C temperature divider. |
| 11 | PC2 | `STATUS_LED_RED` | GPIO output | Drive through a resistor; active-low is preferred. |
| 12 | PC3 | `NTC_PHASE_A` | ADC12_IN9 | Half-bridge A temperature divider. |
| 13 | PA0 | `VBUS_SENSE` | ADC12_IN1 | Protected, filtered motor-bus divider; size for maximum bus and transient voltage. |
| 14 | PA1 | `OPP_U1` | OPAMP1_VINP | Phase-U shunt amplifier positive input. |
| 15 | PA2 | `OPO_U1` | OPAMP1_VOUT / ADC1_IN3 | Phase-U shunt amplifier output. |
| 16 | PA3 | `OPN_U1` | OPAMP1_VINM | Phase-U shunt amplifier negative/input network. |
| 17 | PA4 | `IMU_INT1` | GPIO/EXTI4 input | BMI323 data-ready or FIFO-watermark interrupt. |
| 18 | PA5 | `IMU_INT2` | GPIO/EXTI5 input | BMI323 secondary event/error interrupt. |
| 19 | PA6 | `OPO_V1` | OPAMP2_VOUT / ADC2_IN3 | Phase-V shunt amplifier output. |
| 20 | PA7 | `OPP_V1` | OPAMP2_VINP | Phase-V shunt amplifier positive input. |
| 21 | PC4 | `IMU_CS_N` | GPIO output | BMI323 active-low chip select; add 10 kOhm pull-up to 3.3 V. |
| 22 | PC5 | `OPN_V1` | OPAMP2_VINM | Phase-V shunt amplifier negative/input network. |
| 23 | PB0 | `OPP_W1` | OPAMP3_VINP | Phase-W shunt amplifier positive input. |
| 24 | PB1 | `OPO_W1` | OPAMP3_VOUT / ADC1_IN12 | Phase-W shunt amplifier output. |
| 25 | PB2 | `OPN_W1` | OPAMP3_VINM | Phase-W shunt amplifier negative/input network. |
| 28 | PB10 | `CAN_STB` | GPIO output | 10 kOhm pull-up holds CAN standby through reset; configure TX recessive before driving low. |
| 44 | PA8 | `SPARE_TIM_GPIO` | TIM4_ETR / GPIO | Reserve; expose as a test pad if practical. |
| 45 | PA9 | `USB_UART_TX` | USART1_TX | MCU TX to USB-UART bridge RX; ROM-bootloader-compatible UART pin. |
| 46 | PA10 | `USB_UART_RX` | USART1_RX | MCU RX from USB-UART bridge TX; ROM-bootloader-compatible UART pin. |
| 47 | PA11 | `FDCAN1_RX` | FDCAN1_RX | Connect to CAN transceiver RXD. |
| 48 | PA12 | `FDCAN1_TX` | FDCAN1_TX | Connect to CAN transceiver TXD. |
| 49 | PA13 | `SWDIO` | SWD | Route to 10-pin Arm Cortex debug connector. |
| 50 | PA14 | `SWCLK` | SWD | Route to 10-pin Arm Cortex debug connector. |
| 51 | PA15 | `AS5047P_CS_N` | GPIO output / SPI3_NSS | Active-low encoder chip select; add 10 kOhm pull-up to 3.3 V. |
| 53 | PD2 | `FEEDBACK_SELECT` | GPIO output | TMUX1574 source selection; add 10 kOhm pull-down and wire `0` to select the onboard encoder. |
| 54 | PB3 | `SPI3_SCK` | SPI3_SCK | Shared BMI323/AS5047P clock. Full JTAG/SWO is sacrificed; SWD remains. |
| 55 | PB4 | `SPI3_MISO` | SPI3_MISO | Shared BMI323/AS5047P controller input. |
| 56 | PB5 | `SPI3_MOSI` | SPI3_MOSI | Shared BMI323/AS5047P controller output. |
| 57 | PB6 | `FEEDBACK_A_H1` | TIM4_CH1 / EXTI6 | Muxed encoder A or Hall U/H1. |
| 58 | PB7 | `FEEDBACK_B_H2` | TIM4_CH2 / EXTI7 | Muxed encoder B or Hall V/H2. |
| 59 | PB8 | `FEEDBACK_I_H3` | TIM4_CH3 / EXTI8 / BOOT0 | Muxed encoder index I/Z or Hall W/H3. Add 10 kOhm pull-down. The mux must remain disabled during reset. |
| 60 | PB9 | `BRAKE_PWM` | TIM17_CH1 output | Drive the brake-chopper gate driver input. Add a hardware pull-down so the software-command path remains off throughout reset. The independent U502 overvoltage circuit may command braking while the MCU is reset. |

## Internal motor-control resources

The following MCU resources are connected internally inside the STSPIN32G4 and are not exposed as package GPIOs:

- TIM1 complementary PWM channels drive the three half-bridge gate-driver inputs.
- Gate-driver READY and NFAULT connect to internal break-capable MCU inputs.
- Internal I2C3 connects the MCU to the gate-driver configuration/status interface.

Do not attempt to reassign the associated internal MCU pins. Follow the GPIO configurations required by the STSPIN32G4 datasheet.

## Feedback selection and reset safety

Use a TI TMUX1574 four-channel 2:1 switch. Three channels select feedback signals. The fourth isolates the VM divider from an unpowered MCU; both switch inputs carry VBUS_MUX_IN.

| TMUX1574 | Onboard input | External input | MCU/common output |
|---|---|---|---|
| Channel 1 | AS5047P A | External A or Hall U | PB6 / TIM4_CH1 |
| Channel 2 | AS5047P B | External B or Hall V | PB7 / TIM4_CH2 |
| Channel 3 | AS5047P I | External Z or Hall W | PB8 / TIM4_CH3 |
| Channel 4 | VBUS_MUX_IN | VBUS_MUX_IN | PA0 / VBUS_SENSE |
| `SEL` | Low selects onboard | High selects external | PD2 `FEEDBACK_SELECT` |
| `EN_N` | High disconnects all paths | Low enables selected paths | PC14 `FEEDBACK_ENABLE_N` |

Required hardware defaults:

```text
3V3 --- 10 kOhm --- PC14 / TMUX EN_N
GND --- 10 kOhm --- PD2  / TMUX SEL
GND --- 10 kOhm --- PB8  / BOOT0
```

These resistors, rather than firmware, establish the safe state of a blank MCU:

1. PC14 is high-impedance during reset, so its pull-up holds `EN_N` high.
2. The disabled TMUX isolates PB8 from the onboard and external feedback sources.
3. PB8 is held low and the MCU samples the normal application boot state.
4. Firmware configures the feedback pins and selection before enabling the TMUX.

Do not rely solely on STM32 option bytes to make PB8 safe. Rev A must be programable after assembly without pre-programming the MCU.

### TMUX1574PWR schematic capture

Use the TSSOP-16 `TMUX1574PWR` for Rev A. Its exact pin connections are:

| Pin | TMUX signal | ShiroFOC connection |
|---:|---|---|
| 1 | SEL | PD2 `FEEDBACK_SELECT`, with 10 kOhm pull-down |
| 2 | S1A | Onboard AS5047P A through optional 33 ohm series resistor |
| 3 | S1B | Protected external A / Hall U input |
| 4 | D1 | PB6 `FEEDBACK_A_H1` |
| 5 | S2A | Onboard AS5047P B through optional 33 ohm series resistor |
| 6 | S2B | Protected external B / Hall V input |
| 7 | D2 | PB7 `FEEDBACK_B_H2` |
| 8 | GND | Digital ground |
| 9 | D3 | PB8 `FEEDBACK_I_H3`, with 10 kOhm pull-down at the MCU |
| 10 | S3B | Protected external Z / Hall W input |
| 11 | S3A | Onboard AS5047P I through optional 33 ohm series resistor |
| 12 | D4 | VBUS_SENSE to PA0 and C108 |
| 13 | S4B | VBUS_MUX_IN from R106 |
| 14 | S4A | VBUS_MUX_IN from R106 |
| 15 | EN | PC14 `FEEDBACK_ENABLE_N`, with 10 kOhm pull-up to 3.3 V |
| 16 | VDD | 3.3 V, with 100 nF C0G/X7R decoupling directly to pin 8 |

`SEL=0` connects the A-side/onboard inputs to the MCU. `SEL=1` connects the B-side/external inputs. `EN=1` disconnects all channels; `EN=0` enables the selected source. The net name must retain the `_N` suffix because enable is active-low.

Place the TMUX close to PB6/PB7/PB8. Keep its common-output traces short, particularly PB8/BOOT0. Do not place a test point or long stub on PB8 between the mux and MCU.

### External feedback input front end

For each external A/B/Z or Hall U/V/W input, use the following Rev A starting network:

```text
connector signal --- ESD protection --- 100 ohm series --- TMUX SxB
                                             |
                                      optional 10 kOhm
                                      pull-up to 3.3 V
```

- Place the ESD device at the connector before the trace enters the board.
- Populate the 100 ohm resistors initially; revise only after edge-rate testing.
- Provide individual 10 kOhm pull-up footprints. Populate them for open-collector Hall sensors and leave them DNP for push-pull encoders unless required.
- Define connector pinout and supported voltage explicitly. Prefer 3.3 V signals. Although the TMUX signal path can pass voltages above its 3.3 V supply, do not treat it as a voltage-level translator.
- Ensure any chosen ESD clamp has sufficiently low capacitance for the maximum encoder edge rate and does not clamp ordinary 3.3 V logic.
- Put the onboard AS5047P source resistors close to the encoder. They reduce ringing and isolate its push-pull outputs from switch/trace capacitance.

## Feedback operating modes

### Onboard or external incremental encoder

- Configure PB6/PB7 as TIM4_CH1/CH2 in hardware encoder mode.
- PB8 may be used as TIM4_CH3 or as an EXTI input for the index pulse, depending on firmware design.
- A/B counting occurs in hardware. Index is used for homing, counter validation, or mechanical-zero establishment.
- Use the AS5047P SPI interface for absolute startup angle, configuration, and magnetic/diagnostic status.

### External Hall U/V/W

- The preferred high-integration option is TIM4's Hall-sensor interface using CH1/CH2/CH3.
- A software alternative is to configure PB6/PB7/PB8 as EXTI inputs, read the three-bit Hall state at every edge, and timestamp transitions with a free-running timer.
- Firmware must reject illegal Hall states `000` and `111`, validate the transition sequence, and enter a safe state on feedback loss.

Never switch `FEEDBACK_SELECT` while producing motor torque. Disable PWM, wait for a safe state, disable the TMUX, change the selection, reconfigure the feedback peripheral, clear pending flags/counters, and then re-enable feedback.

## Shared SPI3 sensor bus

SPI3 connects electrically to both local sensors without a bus mux:

| Signal | MCU | AS5047P | BMI323 |
|---|---|---|---|
| Clock | PB3 | CLK | SCK |
| Controller input | PB4 | MISO | SDO |
| Controller output | PB5 | MOSI | SDI |
| Encoder select | PA15 | CSn | - |
| IMU select | PC4 | - | CSB |

Both chip selects need external pull-ups so neither device is selected during reset.

The devices use different SPI modes:

- AS5047P: mode 1, CPOL=0 and CPHA=1.
- BMI323: mode 0 or mode 3.

Firmware must serialize access, deassert both chip selects, wait for the bus to be idle, and change CPOL/CPHA before selecting the other device. Protect this sequence with one bus lock. Encoder A/B counting continues in TIM4 independently of SPI transfers, and IMU traffic must never block the hard real-time current-control loop.

### SPI3 schematic and routing details

- Put optional 22 to 33 ohm series resistors in SCK and MOSI close to PB3/PB5. Populate 22 ohm for Rev A as a starting point.
- Put an optional 22 to 33 ohm resistor in each peripheral's MISO branch close to that peripheral. This limits contention current during reset/firmware mistakes and helps damp the two return branches.
- A chip-select series resistor footprint may be provided but is normally populated as 0 ohm. The mandatory component on each chip select is its 10 kOhm pull-up to 3.3 V.
- Route SCK as the most sensitive SPI signal: short, referenced continuously to ground, with no large loop or routing alongside gate-drive, phase-node, buck-switch, or other high-current traces.
- Keep the branch from the SCK trunk to each sensor short. Avoid long T-shaped stubs. If placement forces a long branch, route from the MCU past one sensor to the other and validate the resulting topology.
- Do not place the TMUX1574 in the SPI path. Its first three channels select ABI/Hall feedback; channel 4 isolates bus-voltage sensing.
- Keep both CS lines high whenever changing SPI CPOL/CPHA. Do not change the clock mode while either peripheral is selected.
- Add local 100 nF supply decoupling at each sensor plus the bulk/local capacitors required by its datasheet.

## Debug and programming

- Use SWDIO, SWCLK, NRST, 3.3 V reference, and GND on the 10-pin Arm Cortex debug connector. Full JTAG is unnecessary.
- PB3, PB4, and PA15 have JTAG/debug functions after reset. Configure debugging as **Serial Wire only** so they become available for SPI3 and encoder chip select while retaining PA13/PA14 SWD.
- Keep the SWD connector available even though USART1 may support ROM-UART programming. SWD is the primary programming and recovery path.
- The USB-C UART bridge is for console, configuration, logging, and optional bootloader workflows; it is not required for normal CAN operation.

## Power and analog notes

- Fit a 24 MHz HSE crystal between PF0/OSC_IN and PF1/OSC_OUT. The selected Rev A part is HCI `0132M4-24.000F07DTNLL` (JLCPCB/LCSC `C19674287`): passive fundamental-mode crystal, 7 pF load capacitance, 40 ohm maximum ESR, +/-10 ppm tolerance, +/-20 ppm stability, -40 to +85 degrees C, SMD3225-4P.
- Start with two 10 pF C0G/NP0 load capacitors, one from each crystal terminal to ground. With equal capacitors this targets a 7 pF crystal load when board/pin stray capacitance is roughly 2 pF. Confirm the final value from the actual layout and oscillator validation; do not substitute X7R parts here.
- Place the crystal and capacitors immediately beside PF0/PF1 with short, symmetric traces and short ground returns. Keep the network away from MOSFET gates, phase/switch nodes, bootstrap loops, and the buck inductor. Connect the case/ground pads exactly as specified by the crystal datasheet.
- Connect VBAT according to the STM32 backup-domain requirements. If no backup battery is used, normally tie it to the appropriate 3.3 V supply as recommended by ST rather than leaving it floating.
- Supply the STSPIN MCU/logic from the external `3V3` rail using the datasheet-defined regulator-bypass configuration. Decouple VDD, VDDA, and VREF+ exactly as required by the STSPIN32G4 and STM32G431 documentation. Keep analog decoupling and current-sense routing away from gate-drive switching loops.
- Budget the IMU, onboard AS5047P, the maximum permitted external encoder/Hall load, CAN transceiver, USB-UART bridge, LEDs, and other logic against the external 5 V regulator, power mux, and 3.3 V LDO ratings. The feedback mux switches signals, not sensor power, so the electrical budget must allow both feedback devices to be powered at once. The STSPIN internal buck is reserved for the VCC gate-driver rail.
- Place each NTC divider close to its measured half-bridge region, add ADC filtering, and include open/short plausibility checks in firmware.
- Design the VBUS divider and protection for the maximum battery voltage plus switching transients, not only the nominal battery voltage.
- SCREF is a dedicated analog protection input, not a GPIO. Its network must preserve short-circuit protection across tolerances and noise.

## External-interface protection

- Protect external A/B/Z or Hall U/V/W at the connector with suitable ESD components and modest filtering/series resistance.
- Define the supported external signal voltage. Prefer 3.3 V logic; add explicit translation if 5 V encoders must be supported.
- Add CAN termination as a selectable option rather than permanently terminating every module.

## Firmware initialization order

1. Hardware keeps the TMUX disabled and PB8/BOOT0 low during reset.
2. Configure clocking, safety state, gate-driver fault handling, and SWD-only debug mode.
3. Deassert both sensor chip selects and initialize SPI3 only when required.
4. Configure PB6/PB7/PB8 for the selected encoder or Hall mode.
5. Set PD2 to the required onboard/external source.
6. Write the PC14 output data latch high before changing PC14 to output mode, avoiding an accidental enable pulse.
7. Drive PC14 low to enable the TMUX only after the feedback inputs and timers are ready.
8. Wait at least 2 ms for channel 4 VM sensing to settle; validate VM and feedback before enabling motor PWM.

If USB keeps the control domain alive while VM disappears and later returns, treat the return as a complete power-stage restart: hold inverter and brake PWM off, re-establish VCC, clear and read gate-driver faults, reapply the 10 V VCC setting, validate ADC/feedback state, and only then permit motor PWM.

On a detected feedback fault, disable motor PWM first and then disable the TMUX if isolation is useful for diagnosis.

## Pre-layout verification checklist

- Reproduce this allocation in STM32CubeMX using STM32G431VBx3, accounting for the smaller set of pins actually exposed by STSPIN32G4.
- Confirm TIM1 internal motor-control configuration required by ST.
- Confirm TIM4 encoder and Hall configurations can be selected by firmware while PB9 is committed to TIM17_CH1 `BRAKE_PWM`.
- Confirm ADC instance/channel allocation and sampling schedule for three current channels, three NTCs, and VBUS.
- Confirm OPAMP1/2/3 input and output routing.
- Confirm FDCAN1 on PA11/PA12, USART1 on PA9/PA10, and SPI3 on PB3/PB4/PB5.
- Confirm SWD-only mode releases PB3/PB4/PA15.
- Test first power-up with an erased MCU and verify PB8 remains below the BOOT0-low threshold for the complete sampling interval.
- Test reset while both onboard and external feedback sources are powered and actively high.
- External digital feedback in Rev A is ABI/index or Hall U/V/W only. External SPI/SSI feedback is explicitly deferred to a later revision.
- A0 pins were reviewed against the datasheet and KiCad ERC. Firmware clock, ADC timing and break routing still require exact-device configuration verification before commissioning.

## A0 electrical details

External inputs are 0–3.3 V only, including when board power is off; J601 supply output is limited to 25 mA. D601 pin 5 connects to an isolated ESD rail with C604, not system 3V3. Disable inverter PWM before disabling the TMUX because VM sensing then becomes invalid. CP2102N VREGIN and VDD both use 3V3 in bypass mode. Current-sense gain is 28 with 0.5 mOhm shunts and midscale bias (14 mV/A); COMP1/2/4 must be configured with internal DAC thresholds and TIM1 break.
