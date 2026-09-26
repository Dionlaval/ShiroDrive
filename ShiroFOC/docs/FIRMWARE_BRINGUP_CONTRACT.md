> **Historical A0 document — superseded for Manual_Rebuild.** Use the [current firmware requirements](../requirements/FIRMWARE_REQUIREMENTS.md). In particular, do not implement the shared SPI mode switching, internal 8-to-10 V regulator setup, old current targets or unverified comparator example below on the current board.

# ShiroFOC A0 firmware and bring-up contract

This is a hardware interface contract, not implemented firmware. Follow [MCU pin allocation](MCU_PINOUT_AND_INTERFACE_PLAN.md) and the native schematic. Peripheral capability was checked from the STSPIN32G4 pin table; STM32CubeMX has not been run. Generate and review the actual clock/peripheral configuration during firmware work.

## Initialization before any torque

1. Keep TIM1 MOE cleared and all inverter PWM outputs inactive. PB9 brake PWM starts low. CAN_STB/PB10 stays high. Hardware holds PC14/FEEDBACK_ENABLE_N high, PD2/FEEDBACK_SELECT low, and PB8/BOOT0 low.
2. Configure SWD-only debug so PB3/PB4/PA15 can serve SPI/CS. Start HSE/PLL with a checked 24 MHz clock configuration; retain recovery on SWD.
3. Deassert both sensor chip selects before enabling SPI. Encoder uses SPI mode 1; BMI323 mode 0 or 3. Serialize transactions and change mode only with both CS high.
4. Configure feedback A/B/I or Hall inputs and TIM4; set PD2 source selection, preload PC14 high, then drive it low to enable the TMUX. Wait **at least 2 ms** before accepting VBUS_SENSE. Channel 4 also switches the VM divider, so VM is invalid whenever the feedback mux is disabled.
5. Start/calibrate ADCs and OPAMP1/2/3 in the external feedback configuration. Measure all current offsets with PWM off. Configure comparator thresholds through the internal DAC paths and route **COMP1/2/4 into TIM1 break**. Keep automatic restart disabled; latch a fault until explicitly cleared under safe conditions.
6. Configure the internal STSPIN I2C3 link and gate-driver interlocking/minimum deadtime/VDS protection. Read faults/READY; select **10 V VCC** from its default 8 V after each VM power-up. Require valid VM, VCC/READY and fault-free status before enabling PWM.
7. Initialize FDCAN TX recessive before driving PB10 CAN_STB low. Check temperatures, feedback plausibility and bus limits. Require an explicit arm command; never arm from a stale pre-reset command.
8. Begin at 18 V on a current-limited source, motor unloaded, very low commanded phase current (1–2 A). Start 20 kHz center-aligned PWM and 500 ns programmed deadtime; verify waveforms before reducing deadtime or raising current.

## Analog/peripheral map

| Function | MCU pins | Configuration |
|---|---|---|
| U current | PA1 +, PA3 −, PA2 output | OPAMP1; ADC1 channel 3; COMP1 positive input PA1 |
| V current | PA7 +, PC5 −, PA6 output | OPAMP2; ADC2 channel 3; COMP2 positive input PA7 |
| W current | PB0 +, PB2 −, PB1 output | OPAMP3; ADC1 channel 12; COMP4 positive input PB0 |
| VM | PA0 | ADC1/2 channel 1, divided by 21; only valid with TMUX enabled |
| NTC U/V/W | PC3 / PC0 / PC1 | ADC1/2 channels 9 / 6 / 7 |
| Encoder/Hall | PB6 / PB7 / PB8 | TIM4 CH1/CH2/CH3; index or Hall mode; PB8 shares BOOT0 |
| Brake PWM | PB9 | TIM17_CH1; separate from TIM4 |
| CAN | PA11 RX / PA12 TX; PB10 STB | FDCAN1; STB high is standby |
| UART | PA9 TX / PA10 RX | USART1 to CP2102N through 100 Ω |
| SPI | PB3 SCK / PB4 MISO / PB5 MOSI | SPI3; PA15 encoder CS, PC4 IMU CS |
| IMU interrupts | PA4 / PA5 | EXTI4 / EXTI5 |
| Internal inverter PWM | PE8–PE13 | STSPIN internal TIM1 complementary PWM connections; not exposed package pins |
| Internal driver status | PE14 READY / PE15 NFAULT | Preserve ST's required TIM1 break-capable connections |

ADC1 is shared by U and W: do not assume simultaneous sampling of all three currents. Use valid low-side conduction windows, synchronized injected conversions, and reconstruct the third phase when appropriate. Account for switching blanking, op-amp settling and minimum sampling time. OPAMP3 also has internal ADC routing options; any use must be confirmed in the exact device configuration. Set a maximum modulation limit until sampling and bootstrap refresh are demonstrated.

The comparator positive inputs are the biased **op-amp inputs**, not the amplified ADC outputs. With SENSE_N near ground, `VCOMP = (56 × 0.0005 × I + 3.3)/58`. Internal DAC choice is DAC3 channel 1 for COMP1 and DAC3 channel 2 for COMP2/COMP4, according to ST's G4 LL interface. Confirm the exact register configuration and internal DAC mode in the firmware project. A nominal +60 A setting is about 85.86 mV / code 107, but offset/DAC errors can shift this substantially. Calibrate and demonstrate shutdown at reduced test current before enabling a higher threshold. Apply software limits to both current polarities; this one-sided comparator setup does not give a precise negative-current trip.

## Runtime rules

- Invalidate VM readings before disabling the feedback mux. Disable inverter PWM first; change source only at zero torque, then re-enable, settle and validate feedback/VM.
- Monitor VM independently of command traffic. Starting 10S software brake threshold: 43 V; use hysteresis/duty limiting and the installed resistor's energy/temperature model. Hardware OV backup is approximately 45.9/44.2 V. It may command the brake even while the MCU is reset.
- Do not arm without a suitable energy sink. An open/absent external resistor is not detected by this circuit; installation configuration and commissioning must establish its presence. Do not rely on the battery or PSU to absorb energy without verification.
- On VM loss while USB remains, clear torque commands and driver state. On VM return, repeat driver/VCC/protection setup; do not resume motion automatically.
- On comparator break, VDS fault, encoder loss, illegal Hall state, overtemperature or implausible NTC/ADC reading, latch inverter off. NTC short reads near zero and open near VREF. Use the hottest valid reading and characterize thermal lag.
- Before enabling CAN, hold TX recessive and configure the controller; stay in standby through reset. Apply end termination only where physically appropriate.
- USB-only operation is service mode; VM/VCC absent means no power-stage commands. Configure the CP2102N power descriptors for the actual service-power arrangement. Suspend/current-compliance load control is not provided by this hardware.

## Hardware commissioning sequence

1. Visual/continuity inspection, then USB/control power only from an allowed source. Measure 3V3, regulator temperature, standby current and absence of VM/VCC backfeed; flash via SWD.
2. Apply VM with current limiting and external precharge. Test battery-only, USB-only and both sources in both orders, including brownout, erased MCU and reset with active feedback inputs.
3. Verify 5V_BAT, mux source priority, 3V3, VCC default/programmed voltage and restart behavior. Scope switching/overshoot using probes appropriate to the bus voltage.
4. Calibrate current, VM and NTC channels. Inject controlled low-energy shunt/COMP stimuli and prove TIM1 turns off without executing a software ISR. Verify NFAULT/READY breaks and latch behavior.
5. Fit the qualified external resistor; test hardware OV thresholds with a current-limited source and verify brake current, gate drive and lead-voltage clamp. Test with MCU held reset. Do not test an intentional resistor short at high energy.
6. Spin unloaded at low current, inspect gate deadtime, bootstrap refresh, phase-node overshoot, current waveform and feedback timing. Keep sustained VM below 48 V during characterization and target measured MOSFET VDS peaks below 55 V; never approach the 60 V absolute maximum.
7. Increase voltage/current only after protection works. Measure capacitor RMS ripple, MOSFET/shunt/connector/LDO temperatures, external resistor energy and cooling. The 25/40 Arms and 80 A peak goals remain gated by these results.
