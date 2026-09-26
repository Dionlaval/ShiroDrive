EESchema Schematic File Version 4
LIBS:ShiroFOC_KiCad-cache
EELAYER 29 0
EELAYER END
$Descr A3 16535 11693
encoding utf-8
Sheet 1 11
Title "ShiroFOC Rev A"
Date "2026-09-14"
Rev "A"
Comp "ShiroFOC"
Comment1 "Hierarchical first-build FOC motor controller"
Comment2 "6S-10S LiPo / 24-42 V; 60 V inverter devices"
Comment3 "USB-powered control domain; CAN production interface"
Comment4 "See DESIGN_REVIEW_REV_A.md before PCB layout"
$EndDescr
Text Notes 600 450 0    100   ~ 0
ShiroFOC Rev A - SYSTEM OVERVIEW
Text Notes 600 850 0    60   ~ 0
VM -> DC link + inverter + STSPIN VCC buck + 5V_BAT buck
Text Notes 600 1150 0    60   ~ 0
USB VBUS + 5V_BAT -> TPS2121 (USB priority) -> 5V_SYS -> 3V3
Text Notes 600 1450 0    60   ~ 0
STSPIN32G4 -> three CSD88599Q5DC power blocks -> motor U/V/W
Text Notes 600 1750 0    60   ~ 0
CAN is the normal production interface. USB-UART and SWD are local service interfaces.
$Sheet
S 900 2450 6500 1050
U 20000000
F0 "01 - Battery Input and DC Link" 55
F1 "01_Battery_DC_Link.sch" 55
$EndSheet
$Sheet
S 8500 2450 6500 1050
U 20000001
F0 "02 - Auxiliary Power, USB and Source Mux" 55
F1 "02_Aux_Power_USB.sch" 55
$EndSheet
$Sheet
S 900 4000 6500 1050
U 20000002
F0 "03 - STSPIN32G4 Core and Gate-Driver Supply" 55
F1 "03_STSPIN_Core.sch" 55
$EndSheet
$Sheet
S 8500 4000 6500 1050
U 20000003
F0 "04 - Three-Phase Inverter and Current Sensing" 55
F1 "04_Inverter_CurrentSense.sch" 55
$EndSheet
$Sheet
S 900 5550 6500 1050
U 20000004
F0 "05 - Brake Chopper" 55
F1 "05_Brake_Chopper.sch" 55
$EndSheet
$Sheet
S 8500 5550 6500 1050
U 20000005
F0 "06 - Onboard and External Position Feedback" 55
F1 "06_Position_Feedback.sch" 55
$EndSheet
$Sheet
S 900 7100 6500 1050
U 20000006
F0 "07 - IMU and Half-Bridge Temperature" 55
F1 "07_IMU_Temperature.sch" 55
$EndSheet
$Sheet
S 8500 7100 6500 1050
U 20000007
F0 "08 - CAN / CAN-FD Interface" 55
F1 "08_CAN.sch" 55
$EndSheet
$Sheet
S 900 8650 6500 1050
U 20000008
F0 "09 - USB-UART Service Interface" 55
F1 "09_USB_UART.sch" 55
$EndSheet
$Sheet
S 8500 8650 6500 1050
U 20000009
F0 "10 - SWD, Boot and Test Access" 55
F1 "10_SWD_Test.sch" 55
$EndSheet
Text Notes 600 10600 0    55   ~ 0
RELEASE CONDITIONS: ERC clean; exact footprints/pad maps verified; startup defaults off; all DNP states documented; review log signed before layout.
$EndSCHEMATC
