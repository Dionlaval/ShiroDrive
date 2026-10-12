# P3 joint-feedback supply: fixed 5 V

2026-10-11 follow-up to the fan PWM change. The board is dedicated to joint control. J601 remains the Hall/ABI motor-feedback interface, J502 is the dedicated fan output, and unrelated external sensors belong on the main motherboard.

JP601 and its 3.3 V feed are removed. U604 IN, EN and ILIM, plus C606 input bypass, now connect directly to 5V_SYS. J601 pin 1 therefore supplies protected 5 V only. The existing 75 mA nominal sensor current limit and 25 mA provisional normal-load budget remain unchanged. The separate fan supply/PWM circuitry is unchanged. Sensor signal-voltage support is not altered by this supply change.

This keeps the external feedback power load off the MCU 3.3 V rail. It does not create galvanic isolation or eliminate the shared upstream 5 V power budget.

Validation: native netlists confirm that only JP601 was removed and the former selected-input net merged into 5V_SYS. All retained component values, footprints and unrelated pin connections are unchanged. The exported sheet was visually checked. Native ERC is unchanged at 1 error and 16 warnings; no new findings. These are scoped schematic checks, not a full-board review. The PCB is unchanged and still needs schematic synchronization in a later layout task.

See fixed_5v_feedback.pdf for the current sheet, validation.json for checks/hashes, and before-target-files.zip for the exact prior sheet. This update supersedes the selectable sensor supply described in the earlier fan PWM review.

[TI TPS2553 datasheet](https://www.ti.com/lit/ds/symlink/tps2553.pdf): 2.5–6.5 V input operating range; ILIM tied to IN selects the 75 mA typical setting.
