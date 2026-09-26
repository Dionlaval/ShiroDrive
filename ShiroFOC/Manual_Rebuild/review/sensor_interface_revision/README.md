# Dedicated angle SPI, IMU I²C and external Hall/ABI inputs

Updated 2026-09-26 in **Manual_Rebuild**. This supersedes the shared-SPI architecture in the earlier sensor walkthrough and the affected assignments in MCU_PIN_REVIEW.md.

## What changed

- **Page 9:** AS5047P has SPI3 to itself. Its A/B/I outputs are deliberately unconnected; R601–R603 are removed. R313/R314 and R611 retain clock, MOSI and MISO damping.
- **Page 9:** BMI323 now uses I²C2 for both configuration and samples. CSB is hard-wired to 3V3; SDO/SA0 is grounded for address **0x68**. R308 is repurposed as a 2.2 kΩ SCL pull-up; R715 supplies the matching SDA pull-up. R714 is removed. Both interrupt lines and supply bypass capacitors remain.
- **Page 10:** U603, **SN74LVC3G17DCUR**, conditions three external Hall or ABI inputs into 3.3 V logic. It accepts input levels through 5.5 V and supports partial power-down. C605 is its 100 nF bypass. Existing ESD protection and 100 Ω series resistors remain. R615–R617, 100 kΩ, keep unplugged inputs from floating.
- **Page 10:** JP601 selects the external sensor supply. The existing TMUX1574 remains useful: it isolates PB8/BOOT0 at reset and retains the bus-voltage sensing channel. Its former onboard-encoder inputs are grounded.
- **Page 4 and overview:** updated bus names and connections. Existing footprint assignments and the user's bridge are preserved. New U603 and JP601 footprint/model work is deferred as requested.

## Firmware pin map

| Function | MCU pin / package pad | Configuration |
|---|---|---|
| Angle SPI clock | PB3 / 54 | SPI3 SCK |
| Angle SPI MISO | PB4 / 55 | SPI3 MISO |
| Angle SPI MOSI | PB5 / 56 | SPI3 MOSI |
| Angle chip select | PA15 / 51 | GPIO; active low |
| IMU I²C clock | PC4 / 21 | I2C2 SCL, open-drain |
| IMU I²C data | PA8 / 44 | I2C2 SDA, open-drain; TP1024 retained |
| IMU interrupts | PA4 / 17; PA5 / 18 | EXTI4 / EXTI5 |
| External A/H1, B/H2, I/H3 | PB6 / 57; PB7 / 58; PB8 / 59 | TIM4 / index handling as appropriate |
| External connect selection | PD2 / 53 | EXT_FEEDBACK_SELECT: 0 grounds timer inputs; 1 connects buffered external signals |
| Input mux enable | PC14 / 4 | INPUT_MUX_ENABLE_N: 0 enables all four channels |

SPI3 stays in **mode 1**; start around 5 MHz. Each response contains an absolute angle, but firmware must still handle the pipelined protocol, parity, error flags, stale data and measurement latency. This removes accumulated ABI count errors for the onboard sensor; it does not make communications infallible.

Use I²C at 400 kHz. A six-axis burst including two dummy bytes and addressing consumes approximately 0.4 ms of bus time, before software overhead. A 1 ms update period is reasonable; configure sensor output rate and data-ready handling accordingly. No SPI transaction to the IMU is required at startup. I2C3 remains reserved for the internal gate driver.

During reset, R305 disables the mux and R307 holds PB8 low. On startup configure boot option bytes consistently with the intended flash boot policy, keep EXT_FEEDBACK_SELECT low, enable the mux and allow at least 2 ms for VM sensing to settle. Select external feedback only when using it; configure Hall versus ABI processing in firmware. Do not disable this mux while depending on its VM reading. Continue to disable UCPD1 dead-battery pulls and use SWD rather than competing JTAG functions as documented in the MCU review.

## External connector and configuration

J601: **1 = sensor supply; 2 = ground; 3 = A/H1; 4 = B/H2; 5 = index/H3; 6 = unused.** These are single-ended inputs, not differential RS422. The selected supply must match the sensor; signal tolerance does not establish the sensor's own power requirements.

JP601 takes **one shunt only**: pins 1–2 select 3.3 V; pins 2–3 select 5 V. Remove the shunt for a self-powered sensor and leave connector pin 1 unconnected unless deliberately supplying it. The retained external load budget is 25 mA, including fitted pull-ups. R604 is a 0 Ω link, not overload protection. Do not change the supply jumper under power.

- **Default assembly: push-pull signals at 3–5 V.** R608–R610 remain DNP (not fitted). This avoids a pull-up path back into board supply rails when an external source drives high with the board off.
- **Open-drain/open-collector Hall sensors:** fit R608–R610, now 4.7 kΩ. They pull up to the selected sensor supply. Confirm the sensor output can tolerate that voltage and sink roughly 1 mA at 5 V. A sensor with suitable internal pull-ups may not need these parts. This is an assembly configuration, not automatic detection.
- D601 retains its isolated VCC rail with C604 to ground, as supported by its datasheet; it is not tied to the MCU supply. A shared signal ground is required.

## Verification and limits

**59 explicit native-netlist checks pass.** These cover I²C and SPI separation, IC straps, connector pin order, the three buffer channels, reset pulls, supply jumper, isolated ESD rail, preservation of unrelated pin groups and all existing footprint assignments. KiCad ERC remains at **16 pre-existing findings** on the root/bridge/gate-driver portions; the changed interface and MCU pages have no ERC findings. None was suppressed for this revision.

The BMI323 library now contains a separate `COMP_U701_I2C` symbol variant, preserving its imported footprint association. It labels the shared pins for I²C and treats SA0 as an input because CSB is permanently high. The original SPI-capable library symbol is retained. This avoids incorrectly treating an address strap as a driven SPI output.

The SPICE check gives a **280 ns** 30–70% rise time for 2.2 kΩ and an assumed **150 pF total bus capacitance**, under the 300 ns Fast-mode limit. At +5% resistance this is about 294 ns. Keep the local bus at or below that capacitance; this is a layout constraint, not a measured capacitance. The 4.7 kΩ/100 kΩ Hall bias example reaches 4.776 V from a 5 V source (3.152 V from 3.3 V). Cable capacitance still limits open-drain edge speed; no universal maximum encoder speed is claimed.

Native SVGs were visually inspected. The schematic analyzer was also run as supplementary evidence; the exact net checks and datasheets are the verification basis. No firmware, PCB routing, EMC/thermal, manufacturing, sourcing or new CAD qualification is implied by this schematic change.

Evidence and machine checks are in `checks/`; rendered sheets are in `rendered/`. The changed schematic files and original library were backed up in `before/` before editing.

## Primary references

- [STSPIN32G4 datasheet](https://www.st.com/resource/en/datasheet/stspin32g4.pdf): PC4 I2C2_SCL, PA8 I2C2_SDA, shared MCU functions.
- [BMI323 datasheet](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi323-ds000.pdf): I²C straps, address and read protocol.
- [SN74LVC3G17 datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc3g17.pdf): pin mapping, Schmitt input, 5.5 V input tolerance and Ioff.
- [TPD3E001 datasheet](https://www.ti.com/lit/ds/symlink/tpd3e001.pdf): isolated VCC rail application with 100 nF capacitor.
- [AS5047P datasheet](https://www.infineon.com/assets/row/public/documents/24/49/infineon-as5047p-datasheet-en.pdf): absolute-angle SPI and timing.
