> **Interface update, 2026-09-26:** The shared SPI and feedback selection portions below are historical. See the [implemented sensor interface revision](sensor_interface_revision/README.md) for the current dedicated SPI3, IMU I2C2, external-input and MCU pin assignments.

# MCU pin and resource review — manual rebuild

Date: 2026-09-25

## Verdict and scope

No incompatible MCU pin assignment or duplicate physical U4 pin allocation found in the saved schematic. This conclusion requires the firmware configuration below. All 65 package-pad entries occur once in the exported netlist, including the two deliberate NC pins and exposed pad. U4A/B/C/D/E/F represent one physical component.

This is a bounded MCU pin/function and resource review, not PCB release approval. Native KiCad ERC has 16 findings on the root, gate-driver and bridge sheets; none is reported on the MCU sheet. Those findings have not been cleared by this review. ADC timing, crystal startup, analog accuracy, firmware execution, PCB routing and assembly geometry are not validated here. No circuit changes were made.

Evidence: fresh native KiCad XML netlist after saving current editor changes; raw schematic/library review; local STSPIN32G4 DS13630 Rev 2 tables 6/7 (pages 11–14), cross-check of current Rev 3 tables; STM32G431 DS12589 Rev 6 pin descriptions and alternate-function table. Confidence: high for supported pin functions and observed connectivity; conditional for runtime behavior until firmware and bench verification.

## Required firmware choices

1. **Keep TIM1 for the motor bridge.** Its internal PE8–PE13 connections drive the three complementary gate pairs. PE7 controls WAKE; PE14/PE15 receive READY/NFAULT. PC8/PC9 are the internal I2C3 driver connection. Reserve all these resources. Configure fault/break response and dead time deliberately.
2. **Use TIM4 for feedback and TIM17_CH1 for PB9 brake PWM.** PB9 also offers TIM4_CH4, but TIM4's counter is already needed for encoder/Hall processing. In quadrature mode use PB6/PB7 as A/B; handle PB8 index explicitly, for example using EXTI8. In Hall mode configure the three TIM4 inputs accordingly. Select one feedback source at a time.
3. **Disable unused USB-C dead-battery pull-downs early:** set PWR_CR3.UCPD1_DBDIS = 1. Otherwise UART levels on PA9/PA10 can enable 5.1 kΩ internal loads on PB6/PB4, which this board uses for feedback A and SPI MISO. This is extra loading, not proof those signals necessarily fail.
4. **Use SWD only.** PA13/PA14 remain debug pins; explicitly configure PB3/PB4 for SPI3 and PA15 for chip select. Full JTAG/SWO would compete with these signals.
5. **PB8 is also BOOT0.** R305 keeps the feedback mux disabled in reset; R307 holds PB8 low. The BOOT button raises PB8 through R1001. Verify boot option bytes allow the intended button behavior. Use this button for reset/boot, not during active feedback operation. Keep PG10 configured as NRST.
6. **Use GPIO chip selects / software NSS for SPI3.** PA15 selects AS5047P; PC4 selects the IMU. Only one selected at a time; configure transfers for each sensor's required protocol. PA4/PA5 remain IMU interrupts (EXTI4/5).
7. **Configure the op-amps for the actual external feedback networks.** Select the VINP/VINM pins listed below; do not silently substitute internal PGA gain. Keep analog pins in analog mode. PA2, PA6 and PB1 expose the outputs to ADC-capable pins. There are two ADCs, not three independent simultaneous converters: the FOC acquisition schedule must account for this and for valid low-side shunt sampling windows. Slow NTC/bus readings must not disrupt current acquisition.
8. **VREF+ is externally supplied here.** Keep the internal VREFBUF output disabled/high impedance. R301/R302 are 0 Ω links, not defined RC filter resistances. VDDA and VREF+ have their own local capacitors.
9. **PC14 is a slow enable output.** Prefer open-drain, low-speed drive with its existing 10 kΩ pull-up. PC13/PC15 spares have restricted drive capability. Do not enable the LSE crystal function while PC14 is used for feedback enable.
10. **Treat PA8 as spare GPIO, not a promised independent PWM output.** Its current label SPARE_TIM_GPIO is too broad; TIM1 is already committed to the motor bridge.
11. **VBUS_SENSE requires the feedback mux to be enabled.** U602 also switches the bus divider. Allow the RC node to settle before using the ADC result.

## Interface map

| Board function | GPIOs | Peripheral/configuration |
|---|---|---|
| CAN TX / RX | PA12 / PA11 | FDCAN1, AF9 |
| CAN standby | PB10 | GPIO output |
| USB bridge TX / RX | PA9 / PA10 | USART1, AF7; bridge RX/TX respectively |
| SPI clock / MISO / MOSI | PB3 / PB4 / PB5 | SPI3, AF6 |
| Encoder / IMU chip select | PA15 / PC4 | Independent GPIO outputs |
| IMU interrupts | PA4 / PA5 | GPIO inputs, EXTI4 / EXTI5 |
| Feedback A / B / I or Hall 1 / 2 / 3 | PB6 / PB7 / PB8 | TIM4 CH1 / CH2 / CH3, AF2; index handling depends on mode |
| Feedback mux enable / select | PC14 / PD2 | GPIO outputs |
| Brake PWM | PB9 | TIM17_CH1, AF1 |
| Bus voltage | PA0 | ADC1 or ADC2 channel 1 |
| Temperature A / B / C | PC3 / PC0 / PC1 | ADC1 or ADC2 channels 9 / 6 / 7 |
| SWD data / clock | PA13 / PA14 | SWD |
| Status LED | PC2 | GPIO, low turns LED on |
| Main crystal | PF0 / PF1 | HSE oscillator |

## Current amplifier pin map

| Phase | Amplifier | + input | − input | Output / external ADC input |
|---|---|---|---|---|
| U | OPAMP1 | PA1, pad 14 | PA3, pad 16 | PA2, pad 15 / ADC1_IN3 |
| V | OPAMP2 | PA7, pad 20 | PC5, pad 22 | PA6, pad 19 / ADC2_IN3 |
| W | OPAMP3 | PB0, pad 23 | PB2, pad 25 | PB1, pad 24 / ADC1_IN12 |

The separate amplifier symbols do not need another wire back to U4A: they already describe analog resources inside the same MCU. Output-to-ADC capability is present on these pins. Two listed outputs share ADC1; simultaneous acquisition of all three is not implied.

## Page walkthrough notes

- C301/C302 provide 100 nF plus 10 µF on 3V3; C307 decouples VBAT. VBAT is the MCU backup-domain supply, connected to 3V3, not the motor battery.
- R301 feeds VDDA with C303/C304 (100 nF / 1 µF). R302 feeds VREF+ with C305/C306 (100 nF / 1 µF). These are direct DC connections with local capacitors, not independent precision supplies.
- Y301 is 24 MHz. C308/C309 are 10 pF each; their series-equivalent load is 5 pF plus board/pin stray capacitance. This is a plausible starting point for the specified 7 pF crystal, not a measured oscillator qualification.
- R303 pulls NRST high; C310 provides local noise filtering; reset buttons pull it low. SW301 and SW1002 are electrically duplicate reset buttons and are optional simplification candidates.
- J1001 carries SWD, target-voltage reference, ground and reset. Its VTREF tells the debugger the target logic voltage; do not assume it powers the board. SWO is intentionally absent.
- R304 limits status LED current; PC2 sinks that current when low.

## Complete observed package allocation

The symbol uses pad 65 for the physical exposed pad. GPIO names on the op-amp units have been expanded below from the manufacturer pin table.

| U4 pad | Pin / function | Saved schematic net |
|---|---|---|
| 1 | REG3V3/VDD | `3V3` |
| 2 | VBAT | `3V3` |
| 3 | PC13 | `/MCU / clock / SWD/SPARE_GPIO_3` |
| 4 | PC14 | `FEEDBACK_ENABLE_N` |
| 5 | PC15 | `/MCU / clock / SWD/SPARE_GPIO_1` |
| 6 | PF0 | `Net-(U4A-PF0)` |
| 7 | PF1 | `Net-(U4A-PF1)` |
| 8 | PG10/NRST | `/MCU / clock / SWD/NRST` |
| 9 | PC0 | `NTC_PHASE_B` |
| 10 | PC1 | `NTC_PHASE_C` |
| 11 | PC2 | `Net-(D301-K)` |
| 12 | PC3 | `NTC_PHASE_A` |
| 13 | PA0 | `VBUS_SENSE` |
| 14 | PA1 / OPAMP1 VINP | `/Current / temperature/OPP_U1` |
| 15 | PA2 / OPAMP1 VOUT | `OPO_U1` |
| 16 | PA3 / OPAMP1 VINM | `/Current / temperature/OPN_U1` |
| 17 | PA4 | `IMU_INT1` |
| 18 | PA5 | `IMU_INT2` |
| 19 | PA6 / OPAMP2 VOUT | `OPO_V1` |
| 20 | PA7 / OPAMP2 VINP | `/Current / temperature/OPP_V1` |
| 21 | PC4 | `IMU_CS_N` |
| 22 | PC5 / OPAMP2 VINM | `/Current / temperature/OPN_V1` |
| 23 | PB0 / OPAMP3 VINP | `/Current / temperature/OPP_W1` |
| 24 | PB1 / OPAMP3 VOUT | `OPO_W1` |
| 25 | PB2 / OPAMP3 VINM | `/Current / temperature/OPN_W1` |
| 26 | VREF+ | `VREF+` |
| 27 | VDDA | `VDDA` |
| 28 | PB10 | `CAN_STB` |
| 29 | GLS1 | `GLS1` |
| 30 | GLS2 | `GLS2` |
| 31 | GLS3 | `GLS3` |
| 32 | PGND | `GND` |
| 33 | NC | `unconnected-(U4C-NC-Pad33)` |
| 34 | NC | `unconnected-(U4C-NC-Pad34)` |
| 35 | BOOTSTRAP3 | `BOOTSTRAP3` |
| 36 | OUT3 | `OUT3` |
| 37 | GHS3 | `GHS3` |
| 38 | BOOTSTRAP2 | `BOOTSTRAP2` |
| 39 | OUT2 | `OUT2` |
| 40 | GHS2 | `GHS2` |
| 41 | BOOTSTRAP1 | `BOOTSTRAP1` |
| 42 | OUT1 | `OUT1` |
| 43 | GHS1 | `GHS1` |
| 44 | PA8 | `/MCU / clock / SWD/SPARE_TIM_GPIO` |
| 45 | PA9 | `USB_UART_TX` |
| 46 | PA10 | `USB_UART_RX` |
| 47 | PA11 | `FDCAN1_RX` |
| 48 | PA12 | `FDCAN1_TX` |
| 49 | PA13/SWDIO | `Net-(U4A-PA13/SWDIO)` |
| 50 | PA14/SWCLK | `Net-(U4A-PA14/SWCLK)` |
| 51 | PA15 | `AS5047P_CS_N` |
| 52 | SCREF | `Net-(U4C-SCREF)` |
| 53 | PD2 | `FEEDBACK_SELECT` |
| 54 | PB3 | `SPI3_SCK_MCU` |
| 55 | PB4 | `SPI3_MISO` |
| 56 | PB5 | `SPI3_MOSI_MCU` |
| 57 | PB6 | `FEEDBACK_A_H1` |
| 58 | PB7 | `FEEDBACK_B_H2` |
| 59 | PB8/BOOT0 | `FEEDBACK_I_H3` |
| 60 | PB9 | `BRAKE_PWM` |
| 61 | VM | `VM` |
| 62 | SW | `Net-(D302-K)` |
| 63 | VCC | `VCC` |
| 64 | REGIN | `3V3` |
| 65 | VSS/EP | `GND` |

## Sources

- [STSPIN32G4 datasheet, DS13630](https://www.st.com/resource/en/datasheet/stspin32g4.pdf), pin list and internal connections. Local copy reviewed: Rev 2; online Rev 3 internal connections cross-checked.
- [STM32G431 datasheet, DS12589 Rev 6](https://www.st.com/resource/en/datasheet/stm32g431cb.pdf), pages 60–66: pin restrictions and AF mapping.

## Snapshot identity

- `MCUclockSWD.kicad_sch` SHA-256: `81fb9d19de067e64c5f2be3e2fce05cd1c92d79f6af38bb857b19683aa1666c0`
- `ShiroFOC_Manual.kicad_sch` SHA-256: `4a075394fe38cbdc4052f12055932860261d23970263e0152ad39fc6f3a98fed`
