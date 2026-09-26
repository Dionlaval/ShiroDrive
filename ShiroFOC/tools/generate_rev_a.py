#!/usr/bin/env python3
"""Generate the ShiroFOC Rev A KiCad schematic hierarchy.

Circuit definitions and datasheet-derived footprints. native_rev_a.py writes
the editable KiCad 9 hierarchy directly. Legacy rendering helpers are retained
for reference only and are not part of the release build.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import shutil
import re


ROOT = Path(__file__).resolve().parents[1] / "ShiroFOC_KiCad"
LIBDIR = ROOT / "libs"
FPDIR = LIBDIR / "ShiroFOC.pretty"


@dataclass
class Pin:
    name: str
    number: str
    x: int
    y: int
    length: int = 300
    orient: str = "R"
    etype: str = "P"
    visible: bool = True


@dataclass
class Symbol:
    name: str
    ref: str
    width: int
    height: int
    pins: list[Pin]
    description: str = ""

    def legacy(self) -> str:
        lines = [
            f"#\n# {self.name}\n#",
            f"DEF {self.name} {self.ref} 0 40 Y Y 1 F N",
            f'F0 "{self.ref}" 0 {self.height // 2 + 180} 50 H V C CNN',
            f'F1 "{self.name}" 0 {-self.height // 2 - 180} 50 H V C CNN',
            "DRAW",
            f"S {-self.width//2} {self.height//2} {self.width//2} {-self.height//2} 0 1 12 f",
        ]
        for p in self.pins:
            vis = "" if p.visible else " N"
            lines.append(
                f"X {p.name} {p.number} {p.x} {p.y} {p.length} {p.orient} "
                f"40 35 1 1 {p.etype}{vis}"
            )
        lines += ["ENDDRAW", "ENDDEF"]
        return "\n".join(lines)

    def endpoint(self, pin_number: str, x: int, y: int) -> tuple[int, int]:
        p = next(p for p in self.pins if p.number == str(pin_number))
        return x + p.x, y - p.y


def lr_symbol(name: str, ref: str, left: list[tuple[str, str]], right: list[tuple[str, str]],
              width: int = 1600, pitch: int = 150, pin_len: int = 300) -> Symbol:
    n = max(len(left), len(right), 2)
    height = max(700, (n + 1) * pitch)
    y0_l = (len(left) - 1) * pitch // 2
    y0_r = (len(right) - 1) * pitch // 2
    pins = []
    for i, (num, pname) in enumerate(left):
        pins.append(Pin(pname, str(num), -width // 2 - pin_len, y0_l - i * pitch, pin_len, "R"))
    for i, (num, pname) in enumerate(right):
        pins.append(Pin(pname, str(num), width // 2 + pin_len, y0_r - i * pitch, pin_len, "L"))
    return Symbol(name, ref, width, height, pins)


def two_pin(name: str, ref: str) -> Symbol:
    return Symbol(name, ref, 300, 200, [
        Pin("1", "1", -350, 0, 200, "R"),
        Pin("2", "2", 350, 0, 200, "L"),
    ])


SYMS: dict[str, Symbol] = {}


def add(sym: Symbol) -> Symbol:
    SYMS[sym.name] = sym
    return sym


RES = add(two_pin("RESISTOR", "R"))
CAP = add(two_pin("CAPACITOR", "C"))
IND = add(two_pin("INDUCTOR", "L"))
DIODE = add(two_pin("DIODE", "D"))
LED = add(two_pin("LED", "D"))
XTAL4 = add(lr_symbol("CRYSTAL_4PAD", "Y",
    [("1","XIN"),("2","CASE/GND")], [("3","XOUT"),("4","CASE/GND")],
    width=900, pitch=200, pin_len=250))
SW = add(two_pin("SWITCH", "SW"))
TP = add(Symbol("TESTPOINT", "TP", 200, 200, [Pin("TP", "1", -300, 0, 200, "R")]))


def conn(n: int) -> Symbol:
    pins = []
    y0 = (n - 1) * 200 // 2
    for i in range(n):
        pins.append(Pin(str(i + 1), str(i + 1), -600, y0 - i * 200, 300, "R"))
    return add(Symbol(f"CONN_{n}", "J", 600, max(600, n * 200 + 200), pins))


for _n in (2, 3, 4, 6, 10):
    conn(_n)


# STSPIN32G4 exact package pin names.
st_names = {
    1:"REG3V3/VDD",2:"VBAT",3:"PC13",4:"PC14",5:"PC15",6:"PF0",7:"PF1",8:"PG10/NRST",
    9:"PC0",10:"PC1",11:"PC2",12:"PC3",13:"PA0",14:"PA1",15:"PA2",16:"PA3",
    17:"PA4",18:"PA5",19:"PA6",20:"PA7",21:"PC4",22:"PC5",23:"PB0",24:"PB1",
    25:"PB2",26:"VREF+",27:"VDDA",28:"PB10",29:"GLS1",30:"GLS2",31:"GLS3",32:"PGND",
    33:"NC",34:"NC",35:"BOOT3",36:"OUT3",37:"GHS3",38:"BOOT2",39:"OUT2",40:"GHS2",
    41:"BOOT1",42:"OUT1",43:"GHS1",44:"PA8",45:"PA9",46:"PA10",47:"PA11",48:"PA12",
    49:"PA13/SWDIO",50:"PA14/SWCLK",51:"PA15",52:"SCREF",53:"PD2",54:"PB3",55:"PB4",56:"PB5",
    57:"PB6",58:"PB7",59:"PB8/BOOT0",60:"PB9",61:"VM",62:"SW",63:"VCC",64:"REGIN",65:"VSS/EP",
}
st_left = [(str(i), st_names[i]) for i in range(1, 33)]
st_right = [(str(i), st_names[i]) for i in range(65, 32, -1)]
STSPIN = add(lr_symbol("STSPIN32G4", "U", st_left, st_right, width=2600, pitch=100, pin_len=350))

LMR = add(lr_symbol("LMR36510FADDA", "U",
    [(2,"VIN"),(3,"EN"),(1,"PGND"),(9,"EP")],
    [(8,"SW"),(7,"BOOT"),(6,"VCC"),(5,"FB"),(4,"PG")], width=1500, pitch=200))

TPS = add(lr_symbol("TPS2121RUXR", "U",
    [(7,"IN1"),(2,"IN2"),(6,"PR1"),(3,"CP2"),(5,"OV1"),(4,"OV2")],
    [(1,"OUT"),(8,"OUT"),(11,"SS"),(10,"ILM"),(9,"ST"),(12,"GND")], width=1700, pitch=200))

TLV = add(lr_symbol("TLV75533PDYDR", "U",
    [(1,"IN"),(3,"EN"),(2,"GND")], [(5,"OUT"),(4,"NC")], width=1300, pitch=200))

UCC = add(lr_symbol("UCC27517ADBVR", "U",
    [(3,"IN+"),(4,"IN-"),(2,"GND")], [(5,"OUT"),(1,"VDD")], width=1300, pitch=200))

OVCOMP = add(lr_symbol("TLV3012BIDBVR", "U",
    [(3,"IN+"),(4,"IN-"),(2,"GND")], [(1,"OUT"),(5,"REF"),(6,"VDD")], width=1400, pitch=200))

AS5047 = add(lr_symbol("AS5047P", "U",
    [(1,"CSn"),(2,"CLK"),(3,"MISO"),(4,"MOSI"),(5,"TEST"),(13,"GND")],
    [(7,"A"),(6,"B"),(14,"I/PWM"),(8,"W/PWM"),(9,"V"),(10,"U"),(11,"VDD"),(12,"VDD3V3")],
    width=1700, pitch=200))

BMI = add(lr_symbol("BMI323", "U",
    [(1,"SDO"),(4,"INT1"),(5,"VDDIO"),(6,"GNDIO"),(7,"GND")],
    [(14,"SDI"),(13,"SCK"),(12,"CSB"),(9,"INT2"),(8,"VDD"),(2,"NC"),(3,"NC"),(10,"NC"),(11,"NC")],
    width=1600, pitch=200))

TMUX = add(lr_symbol("TMUX1574PW", "U",
    [(2,"S1A"),(3,"S1B"),(5,"S2A"),(6,"S2B"),(11,"S3A"),(10,"S3B"),(14,"S4A"),(13,"S4B"),(1,"SEL"),(15,"EN_N")],
    [(4,"D1"),(7,"D2"),(9,"D3"),(12,"D4"),(16,"VDD"),(8,"GND")],
    width=1800, pitch=200))

TCAN = add(lr_symbol("TCAN3413DR", "U",
    [(1,"TXD"),(4,"RXD"),(8,"STB")], [(7,"CANH"),(6,"CANL"),(3,"VCC"),(5,"VIO"),(2,"GND")], width=1400, pitch=200))

CP2102 = add(lr_symbol("CP2102N-A02-GQFN20", "U",
    [(1,"GPIO.1"),(2,"GPIO.0"),(8,"VBUS"),(5,"D-"),(4,"D+"),(7,"VREGIN"),(6,"VDD"),(9,"RST")],
    [(10,"NC"),(13,"WAKEUP"),(19,"GPIO.3"),(20,"GPIO.2"),(18,"TXD"),(17,"RXD"),(16,"RTS"),(15,"CTS"),(14,"SUSPEND"),(11,"SUSPEND_N"),(3,"GND"),(12,"GND"),(21,"EP")],
    width=1800, pitch=200))

USB_ESD = add(lr_symbol("USBLC6-2SC6", "U",
    [(1,"IO1"),(3,"IO2"),(2,"GND")], [(6,"IO1"),(4,"IO2"),(5,"VBUS")], width=1200, pitch=200))

CAN_ESD = add(lr_symbol("PESD2CANFD24V", "D",
    [(1,"CANH_IN"),(2,"CANL_IN")], [(3,"GND")], width=1100, pitch=200))

TPD3E001 = add(lr_symbol("TPD3E001DRLR", "D",
    [(1,"IO1"),(2,"IO2"),(4,"IO3")], [(5,"VCC"),(3,"GND")], width=1200, pitch=200))

MOS_BRAKE = add(lr_symbol("CSD19531Q5A", "Q",
    [(4,"G")], [(5,"D"),(6,"D"),(7,"D"),(8,"D"),(1,"S"),(2,"S"),(3,"S")], width=1200, pitch=200))

SHUNT = add(Symbol("BVR_Z_R0005", "R", 700, 500, [
    Pin("FORCE+", "1", -650, 150, 300, "R"), Pin("SENSE+", "2", -650, -150, 300, "R"),
    Pin("SENSE-", "3", 650, -150, 300, "L"), Pin("FORCE-", "4", 650, 150, 300, "L"),
]))

# CSD88599Q5DC pin mapping: DMM0022A dual-cool 5 x 6 mm power block.
csd_pins = [
    Pin("GH","1",-1250,900,350,"R"), Pin("SH","2",-1250,650,350,"R"), Pin("GL","22",-1250,400,350,"R"),
]
for i, num in enumerate(range(3,12)):
    csd_pins.append(Pin("VSW",str(num),1250,900-i*100,350,"L"))
for i, num in enumerate(range(12,21)):
    csd_pins.append(Pin("PGND",str(num),1250,-250-i*100,350,"L"))
csd_pins += [Pin("VIN","27",-1250,-100,350,"R")]
for i, num in enumerate((21,23,24,25,26)):
    csd_pins.append(Pin("NC",str(num),-500+i*250,-1550,250,"U",etype="N"))
CSD88599 = add(Symbol("CSD88599Q5DC", "Q", 1800, 2600, csd_pins))

USB_C = add(lr_symbol("USB_C_16P", "J",
    [("A1","GND"),("A4","VBUS"),("A5","CC1"),("A6","D+"),("A7","D-"),("A8","SBU1"),("A9","VBUS"),("A12","GND")],
    [("B12","GND"),("B9","VBUS"),("B8","SBU2"),("B7","D-"),("B6","D+"),("B5","CC2"),("B4","VBUS"),("B1","GND"),("S1","SHIELD")],
    width=1600, pitch=200))


@dataclass
class Component:
    sym: Symbol
    ref: str
    value: str
    x: int
    y: int
    footprint: str
    datasheet: str = ""
    fields: dict[str, str] = field(default_factory=dict)


class Sheet:
    def __init__(self, filename: str, title: str, rev: str = "A"):
        self.filename = filename
        self.title = title
        self.rev = rev
        self.items: list[str] = []
        self.components: list[Component] = []
        self.uid = 0x10000000
        self.connections = {}
        self.no_connects = set()

    def comp(self, sym: Symbol, ref: str, value: str, x: int, y: int, footprint: str,
             datasheet: str = "", **fields: str) -> Component:
        c = Component(sym, ref, value, x, y, footprint, datasheet, fields)
        self.components.append(c)
        return c

    def label(self, x: int, y: int, net: str, orient: int = 0, shape: str = "BiDi"):
        self.items.append(f"Text GLabel {x} {y} {orient}    45   {shape} ~ 0\n{net}")

    def pin_label(self, c: Component, pin: str, net: str, shape: str = "BiDi"):
        self.connections[(c.ref, str(pin))] = net
        x, y = c.sym.endpoint(pin, c.x, c.y)
        p = next(p for p in c.sym.pins if p.number == str(pin))
        orient = 0 if p.orient in ("R", "U", "D") else 2
        self.label(x, y, net, orient, shape)

    def nc(self, c: Component, pin: str):
        self.no_connects.add((c.ref, str(pin)))
        x, y = c.sym.endpoint(pin, c.x, c.y)
        self.items.append(f"NoConn ~ {x} {y}")

    def wire(self, x1: int, y1: int, x2: int, y2: int):
        self.items.append(f"Wire Wire Line\n\t{x1} {y1} {x2} {y2}")

    def note(self, x: int, y: int, text: str, size: int = 60, bold: bool = False):
        b = " ~ 12" if bold else " ~ 0"
        self.items.append(f"Text Notes {x} {y} 0    {size}   {b}\n{text}")

    def render(self) -> str:
        lines = [
            "EESchema Schematic File Version 4",
            "LIBS:ShiroFOC_KiCad-cache",
            "EELAYER 29 0", "EELAYER END", "$Descr A3 16535 11693",
            "encoding utf-8", "Sheet 1 1",
            f'Title "{self.title}"', f'Date "2026-09-15"', f'Rev "{self.rev}"',
            'Comp "ShiroFOC"', 'Comment1 "Rev A first-build schematic"',
            'Comment2 "6S-10S LiPo / 18-42 V operating target"',
            'Comment3 "Prototype: validate switching, transient, and thermal behavior"',
            'Comment4 "GND and PGND are one electrical net; route returns deliberately"',
            "$EndDescr",
        ]
        for c in self.components:
            self.uid += 1
            lines += [
                "$Comp", f"L ShiroFOC_KiCad:{c.sym.name} {c.ref}", f"U 1 1 {self.uid:08X}",
                f"P {c.x} {c.y}",
                f'F 0 "{c.ref}" H {c.x} {c.y - c.sym.height//2 - 180} 50  0000 C CNN',
                f'F 1 "{c.value}" H {c.x} {c.y + c.sym.height//2 + 180} 50  0000 C CNN',
                f'F 2 "{c.footprint}" H {c.x} {c.y} 50  0001 C CNN',
                f'F 3 "{c.datasheet}" H {c.x} {c.y} 50  0001 C CNN',
            ]
            fi = 4
            for name, value in c.fields.items():
                lines.append(f'F {fi} "{value}" H {c.x} {c.y} 50  0001 C CNN "{name}"')
                fi += 1
            lines += [f"\t1    {c.x} {c.y}", "\t1 0 0 -1", "$EndComp"]
        lines += self.items
        lines.append("$EndSCHEMATC")
        return "\n".join(lines) + "\n"


def passive(sheet: Sheet, sym: Symbol, ref: str, value: str, x: int, y: int, fp: str,
            left: str, right: str, dnp: bool = False, mpn: str = "") -> Component:
    c = sheet.comp(sym, ref, value, x, y, fp, MPN=mpn, Assembly="DNP" if dnp else "FIT")
    sheet.pin_label(c, "1", left)
    sheet.pin_label(c, "2", right)
    return c


R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1210 = "Capacitor_SMD:C_1210_3225Metric"


def make_01() -> Sheet:
    s = Sheet("01_Battery_DC_Link.sch", "01 - Battery Input and DC Link")
    s.note(700, 500, "BATTERY INPUT / DC LINK", 90, True)
    s.note(700, 850, "Rev A: keyed XT60, no onboard reverse-polarity or precharge stage.")
    j = s.comp(SYMS["CONN_2"], "J101", "AMASS XT60PW-M", 1800, 2200,
               "Connector_AMASS:AMASS_XT60PW-M_1x02_P7.20mm_Horizontal", MPN="XT60PW-M")
    s.pin_label(j,"1","GND"); s.pin_label(j,"2","VM")
    for i, x in enumerate((3500, 4800, 6100), 1):
        passive(s,CAP,f"C10{i}","680uF 63V",x,2200,"Capacitor_SMD:CP_Elec_18x17.5","VM","GND",mpn="EEVFK1J681M")
    passive(s,CAP,"C104","4.7uF 100V X7R",7500,2200,C1210,"VM","GND")
    passive(s,CAP,"C105","100nF 100V X7R",8700,2200,C0805,"VM","GND")
    passive(s,CAP,"C106","10nF 100V C0G",9900,2200,C0603,"VM","GND")
    passive(s,RES,"R101","470k 0.25W",11100,2200,"Resistor_SMD:R_1206_3216Metric","VM","GND")
    passive(s,DIODE,"D101","VM TVS - SELECT AFTER TEST",12900,2200,"Diode_SMD:D_SMC","VM","GND",dnp=True)
    passive(s,RES,"R102","RC DAMP R - TUNE",4300,4000,"Resistor_SMD:R_2512_6332Metric","VM","VM_DAMP",dnp=True)
    passive(s,CAP,"C107","RC DAMP C - TUNE",6100,4000,"Capacitor_SMD:C_2220_5750Metric","VM_DAMP","GND",dnp=True)
    passive(s,RES,"R103","270k 0.1% 100V",7000,4000,"Resistor_SMD:R_1206_3216Metric","VM","VBUS_DIV_A")
    passive(s,RES,"R104","270k 0.1% 100V",10000,4000,"Resistor_SMD:R_1206_3216Metric","VBUS_DIV_A","VBUS_DIV")
    passive(s,RES,"R105","27k 0.1%",13200,4000,R0603,"VBUS_DIV","GND")
    passive(s,RES,"R106","1k",8200,5200,R0603,"VBUS_DIV","VBUS_MUX_IN")
    passive(s,CAP,"C108","10nF",12100,5200,C0603,"VBUS_SENSE","GND")
    for ref,net,x in (("TP101","VM",3500),("TP102","GND",5000),("TP103","VBUS_SENSE",12500)):
        t=s.comp(TP,ref,net,x,6500,"TestPoint:TestPoint_Pad_D1.5mm"); s.pin_label(t,"1",net)
    s.note(700,7600,"PLACEMENT: keep all three 680 uF capacitors close to the bridge bus. Fit local 1 uF + 10 nF / 100 V ceramics at each power block.")
    s.note(700,7950,"R102/C107 and D101 are DNP tuning positions. Select only after cable/hot-plug measurements; they are not functional requirements for first power-up.")
    s.note(700,8300,"VBUS_SENSE = VM x 27k/(540k+27k): 2.00 V at 42 V, 2.86 V at 60 V. Set the firmware overvoltage trip below the hardware transient ceiling.")
    return s


def make_02() -> Sheet:
    s=Sheet("02_Aux_Power_USB.sch","02 - Auxiliary Power, USB and Source Mux")
    s.note(600,450,"VM -> 5V_BAT; USB VBUS -> 5V_USB; USB has priority; 5V_SYS -> 3V3",80,True)
    u=s.comp(LMR,"U201","LMR36510FADDAR",3000,2600,"Package_SO:Texas_HTSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.95x4.9mm_Mask2.4x3.1mm_ThermalVias","https://www.ti.com/lit/ds/symlink/lmr36510.pdf",MPN="LMR36510FADDAR")
    for p,n in (("2","VM"),("3","VM"),("1","GND"),("9","GND"),("8","5V_SW"),("7","5V_BOOT"),("6","LMR_VCC"),("5","5V_FB")):
        s.pin_label(u,p,n)
    s.nc(u,"4")
    passive(s,CAP,"C201","2.2uF 100V X7R",1000,1750,C1210,"VM","GND")
    passive(s,CAP,"C202","220nF 100V X7R",1000,2700,C0805,"VM","GND")
    passive(s,CAP,"C203","100nF",5350,1550,C0603,"5V_BOOT","5V_SW")
    passive(s,CAP,"C204","1uF",5350,2450,C0603,"LMR_VCC","GND")
    passive(s,IND,"L201","22uH / 2.75A",5350,3350,"ShiroFOC_Footprints:WE_LHMI_7050_74437349220","5V_SW","5V_BAT",mpn="74437349220")
    passive(s,RES,"R201","100k 1%",5350,4250,R0603,"5V_BAT","5V_FB")
    passive(s,RES,"R202","24.9k 1%",5350,5050,R0603,"5V_FB","GND")
    passive(s,CAP,"C205","22uF 10V X7R",7350,3400,C1210,"5V_BAT","GND")
    passive(s,CAP,"C206","22uF 10V X7R",7350,4350,C1210,"5V_BAT","GND")

    j=s.comp(USB_C,"J201","USB-C service",3600,7450,"Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",MPN="TYPE-C-31-M-12")
    usbmap={"A1":"GND","A4":"5V_USB_RAW","A5":"USB_CC1","A6":"USB_DP_CONN","A7":"USB_DM_CONN","A9":"5V_USB_RAW","A12":"GND",
            "B12":"GND","B9":"5V_USB_RAW","B7":"USB_DM_CONN","B6":"USB_DP_CONN","B5":"USB_CC2","B4":"5V_USB_RAW","B1":"GND","S1":"USB_SHIELD"}
    for p,n in usbmap.items(): s.pin_label(j,p,n)
    s.nc(j,"A8"); s.nc(j,"B8")
    passive(s,RES,"R203","5.1k",1300,6550,R0603,"USB_CC1","GND")
    passive(s,RES,"R204","5.1k",1300,7450,R0603,"USB_CC2","GND")
    passive(s,CAP,"C207","4.7nF 2kV",1300,8350,"Capacitor_SMD:C_1206_3216Metric","USB_SHIELD","GND",dnp=True)
    esd=s.comp(USB_ESD,"U202","USBLC6-2SC6",7000,7450,"Package_TO_SOT_SMD:SOT-23-6","https://www.st.com/resource/en/datasheet/usblc6-2.pdf",MPN="USBLC6-2SC6")
    for p,n in (("1","USB_DM_CONN"),("3","USB_DP_CONN"),("2","GND"),("6","USB_DM"),("4","USB_DP"),("5","5V_USB_RAW")): s.pin_label(esd,p,n)
    passive(s,RES,"R205","0R",9000,6800,R0603,"5V_USB_RAW","5V_USB")
    passive(s,CAP,"C208","1uF 10V",9000,7700,C0603,"5V_USB","GND")

    mux=s.comp(TPS,"U203","TPS2121RUXR",10600,3550,"Package_DFN_QFN:Texas_VQFN-HR-12_2x2.5mm_P0.5mm_ThermalVias","https://www.ti.com/lit/ds/symlink/tps2121.pdf",MPN="TPS2121RUXR")
    for p,n in (("7","5V_BAT"),("2","5V_USB"),("6","MUX_PR1"),("3","MUX_CP2"),("5","MUX_OV1"),("4","MUX_OV2"),("1","5V_SYS"),("8","5V_SYS"),("11","MUX_SS"),("10","MUX_ILM"),("9","PWR_SOURCE_STATUS"),("12","GND")): s.pin_label(mux,p,n)
    passive(s,RES,"R206","15.0k 1%",7600,1200,R0603,"5V_BAT","MUX_PR1")
    passive(s,RES,"R207","5.10k 1%",7600,2250,R0603,"MUX_PR1","GND")
    passive(s,RES,"R208","10.0k 1%",9500,1200,R0603,"5V_USB","MUX_CP2")
    passive(s,RES,"R209","5.10k 1%",9500,2250,R0603,"MUX_CP2","GND")
    passive(s,RES,"R210","21.0k 1%",11400,1200,R0603,"5V_BAT","MUX_OV1")
    passive(s,RES,"R211","5.10k 1%",11400,2250,R0603,"MUX_OV1","GND")
    passive(s,RES,"R212","21.0k 1%",13300,1200,R0603,"5V_USB","MUX_OV2")
    passive(s,RES,"R213","5.10k 1%",13300,2250,R0603,"MUX_OV2","GND")
    passive(s,RES,"R214","80.6k 1%",7600,5050,R0603,"MUX_ILM","GND")
    passive(s,CAP,"C209","100nF",9500,5050,C0603,"MUX_SS","GND")
    passive(s,RES,"R215","10k",11400,5050,R0603,"3V3","PWR_SOURCE_STATUS")
    passive(s,CAP,"C210","22uF 10V X7R",13500,4050,C1210,"5V_SYS","GND")
    passive(s,CAP,"C211","100nF",13500,5050,C0603,"5V_SYS","GND")
    ldo=s.comp(TLV,"U204","TLV75533PDYDR",11600,7550,"ShiroFOC_Footprints:Texas_DYD0005A_SOT23-5","https://www.ti.com/lit/ds/symlink/tlv755p.pdf",MPN="TLV75533PDYDR")
    for p,n in (("1","5V_SYS"),("3","5V_SYS"),("2","GND"),("5","3V3")): s.pin_label(ldo,p,n)
    s.nc(ldo,"4")
    passive(s,CAP,"C212","2.2uF 10V X7R",9800,8500,C0603,"5V_SYS","GND")
    passive(s,CAP,"C213","2.2uF 10V X7R",14200,7550,C0603,"3V3","GND")
    for ref,net,x,y in (("TP201","5V_BAT",7400,5800),("TP202","5V_USB",9000,5800),("TP203","5V_SYS",13200,5800),("TP204","3V3",14200,8600)):
        t=s.comp(TP,ref,net,x,y,"TestPoint:TestPoint_Pad_D1.5mm"); s.pin_label(t,"1",net)
    s.note(700,9800,"USB priority: PR1=1.269 V and CP2=1.689 V at 5 V. ILM=80.6k sets approx. 1.5 A. OV dividers trip near 5.43 V typical.")
    s.note(700,10200,"The TLV755 has no reverse-current blocking: SWD VTREF is sense-only; never inject 3V3 from the debugger.")
    return s


def make_03() -> Sheet:
    s=Sheet("03_STSPIN_Core.sch","03 - STSPIN32G4 Core and Gate-Driver Supply")
    s.note(500,400,"STSPIN32G4 CORE - EXTERNAL 3V3 MODE",90,True)
    u=s.comp(STSPIN,"U301","STSPIN32G4",7600,5200,"Package_DFN_QFN:QFN-64-1EP_9x9mm_P0.5mm_EP4.1x4.1mm_ThermalVias","../DataSheets/STSPIN32G4.pdf",MPN="STSPIN32G4")
    pin_nets={
        1:"3V3",2:"3V3",3:"SPARE_GPIO_3",4:"FEEDBACK_ENABLE_N",5:"SPARE_GPIO_1",6:"HSE_OSC_IN",7:"HSE_OSC_OUT",8:"NRST",
        9:"NTC_PHASE_B",10:"NTC_PHASE_C",11:"STATUS_LED_RED",12:"NTC_PHASE_A",13:"VBUS_SENSE",14:"OPP_U1",15:"OPO_U1",16:"OPN_U1",
        17:"IMU_INT1",18:"IMU_INT2",19:"OPO_V1",20:"OPP_V1",21:"IMU_CS_N",22:"OPN_V1",23:"OPP_W1",24:"OPO_W1",25:"OPN_W1",
        26:"VREF+",27:"VDDA",28:"CAN_STB",29:"GLS1",30:"GLS2",31:"GLS3",32:"GND",
        35:"BOOT3",36:"OUT3",37:"GHS3",38:"BOOT2",39:"OUT2",40:"GHS2",41:"BOOT1",42:"OUT1",43:"GHS1",44:"SPARE_TIM_GPIO",
        45:"USB_UART_TX",46:"USB_UART_RX",47:"FDCAN1_RX",48:"FDCAN1_TX",49:"SWDIO",50:"SWCLK",51:"AS5047P_CS_N",52:"SCREF",
        53:"FEEDBACK_SELECT",54:"SPI3_SCK_MCU",55:"SPI3_MISO",56:"SPI3_MOSI_MCU",57:"FEEDBACK_A_H1",58:"FEEDBACK_B_H2",59:"FEEDBACK_I_H3",
        60:"BRAKE_PWM",61:"VM",62:"VCC_SW",63:"VCC",64:"3V3",65:"GND",
    }
    for p,n in pin_nets.items(): s.pin_label(u,str(p),n)
    s.nc(u,"33"); s.nc(u,"34")
    passive(s,CAP,"C301","100nF",1200,1300,C0603,"3V3","GND")
    passive(s,CAP,"C302","10uF 10V",1200,1950,C0805,"3V3","GND")
    passive(s,CAP,"C303","100nF",2600,1300,C0603,"VDDA","GND")
    passive(s,CAP,"C304","1uF",2600,1950,C0603,"VDDA","GND")
    passive(s,RES,"R301","0R",4000,1300,R0603,"3V3","VDDA")
    passive(s,CAP,"C305","100nF",5200,1300,C0603,"VREF+","GND")
    passive(s,CAP,"C306","1uF",5200,1950,C0603,"VREF+","GND")
    passive(s,RES,"R302","0R",6500,1300,R0603,"VDDA","VREF+")
    passive(s,CAP,"C307","100nF",1200,3000,C0603,"3V3","GND")
    y=s.comp(XTAL4,"Y301","24MHz 7pF",2500,3300,"Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",MPN="0132M4-24.000F07DTNLL")
    s.pin_label(y,"1","HSE_OSC_IN"); s.pin_label(y,"3","HSE_OSC_OUT")
    s.pin_label(y,"2","GND"); s.pin_label(y,"4","GND")
    passive(s,CAP,"C308","10pF C0G",1700,4000,C0603,"HSE_OSC_IN","GND")
    passive(s,CAP,"C309","10pF C0G",4700,4000,C0603,"HSE_OSC_OUT","GND")
    passive(s,RES,"R303","100k",1200,5100,R0603,"3V3","NRST")
    passive(s,CAP,"C310","100nF",2400,5100,C0603,"NRST","GND")
    passive(s,SW,"SW301","RESET",3600,5100,"Button_Switch_SMD:SW_SPST_TL3305A","NRST","GND")
    passive(s,RES,"R304","1k",1200,6000,R0603,"3V3","STATUS_LED_A")
    # Device/LED convention is pin 1 = cathode, pin 2 = anode.  The MCU sinks current.
    passive(s,LED,"D301","RED",2400,6000,"LED_SMD:LED_0603_1608Metric","STATUS_LED_RED","STATUS_LED_A")
    passive(s,RES,"R305","10k",1600,7000,R0603,"3V3","FEEDBACK_ENABLE_N")
    passive(s,RES,"R306","10k",4800,7000,R0603,"FEEDBACK_SELECT","GND")
    passive(s,RES,"R307","10k",7600,8500,R0603,"FEEDBACK_I_H3","GND")
    passive(s,RES,"R308","10k",10600,8500,R0603,"3V3","IMU_CS_N")
    passive(s,RES,"R309","10k",13800,8500,R0603,"3V3","AS5047P_CS_N")
    # Buck catch diode: pin 1/K to SW, pin 2/A to GND.
    passive(s,DIODE,"D302","STPS1H100A",11100,1800,"Diode_SMD:D_SMA","VCC_SW","GND",mpn="STPS1H100A")
    passive(s,IND,"L301","22uH / 2.75A",12500,1800,"ShiroFOC_Footprints:WE_LHMI_7050_74437349220","VCC_SW","VCC",mpn="74437349220")
    passive(s,CAP,"C311","220nF 100V",9800,1800,C0805,"VM","GND")
    passive(s,CAP,"C312","10uF 25V X7R",13900,1800,C1210,"VCC","GND")
    passive(s,CAP,"C313","100nF 25V",13900,2450,C0603,"VCC","GND")
    passive(s,RES,"R310","100k",11100,3300,R0603,"3V3","SCREF_DIV")
    passive(s,RES,"R311","10k",12500,3300,R0603,"SCREF_DIV","GND")
    passive(s,RES,"R312","1k",11100,3950,R0603,"SCREF_DIV","SCREF")
    passive(s,CAP,"C314","10nF",12500,3950,C0603,"SCREF","GND")
    passive(s,RES,"R313","22R",11000,7500,R0603,"SPI3_SCK_MCU","SPI3_SCK")
    passive(s,RES,"R314","22R",14000,7500,R0603,"SPI3_MOSI_MCU","SPI3_MOSI")
    for ref,net,x,y in (("TP301","VCC",10800,6100),("TP302","SCREF",12600,6100),("TP303","NRST",14400,6100)):
        t=s.comp(TP,ref,net,x,y,"TestPoint:TestPoint_Pad_D1.5mm"); s.pin_label(t,"1",net)
    s.note(650,9400,"VCC BUCK: starts at 8 V. Firmware must set 10 V through the internal power-management interface after every VM return.")
    s.note(650,9750,"Pin 64 REGIN and pin 1 REG3V3/VDD are both tied to external 3V3. The internal 3V3 regulator stays disabled.")
    s.note(650,10100,"SCREF approx. 0.30 V controls VDS fault detection; it is not a precision current limit. Configure COMP1/2/4 + DAC + TIM1 break before enabling PWM.")
    s.note(650,10450,"PB8/BOOT0 has a 10k pulldown. FEEDBACK_ENABLE_N is pulled high, so the mux cannot drive PB8 while reset is active.")
    return s


def add_power_block(s: Sheet, phase: str, idx: int, x: int, y: int):
    q=s.comp(CSD88599,f"Q40{idx}","CSD88599Q5DC",x,y,"ShiroFOC_Footprints:CSD88599Q5DC_DMM0022A","../DataSheets/CSD88599Q5DC.pdf",MPN="CSD88599Q5DC")
    s.pin_label(q,"1",f"GHS{idx}_GATE"); s.pin_label(q,"2",f"OUT{idx}"); s.pin_label(q,"22",f"GLS{idx}_GATE"); s.pin_label(q,"27","VM")
    for p in range(3,12): s.pin_label(q,str(p),f"OUT{idx}")
    for p in range(12,21): s.pin_label(q,str(p),f"SHUNT_{phase}_FORCE_P")
    for p in (21,23,24,25,26): s.nc(q,str(p))
    passive(s,RES,f"R4{idx}1","4.7R",x-3500,y-650,R0603,f"GHS{idx}",f"GHS{idx}_GATE")
    passive(s,RES,f"R4{idx}3","100k",x-1800,y-900,R0603,f"GHS{idx}_GATE",f"OUT{idx}")
    passive(s,RES,f"R4{idx}2","0R",x-3500,y+650,R0603,f"GLS{idx}",f"GLS{idx}_GATE")
    passive(s,RES,f"R4{idx}4","100k",x-1800,y+650,R0603,f"GLS{idx}_GATE",f"SHUNT_{phase}_FORCE_P")
    passive(s,CAP,f"C4{idx}1","100nF 25V",x+2600,y-700,C0603,f"BOOT{idx}",f"OUT{idx}")
    # The 1 uF cap spans the complete bridge/shunt loop.  TI's mandatory 10 nF
    # edge-current bypass instead connects directly from VIN to the package
    # PGND/source pins to minimize package-loop inductance.
    passive(s,CAP,f"C4{idx}2","1uF 100V X7R",x+2600,y,C1210,"VM","GND")
    passive(s,CAP,f"C4{idx}5","10nF 100V X7S",x+2600,y+700,"Capacitor_SMD:C_0402_1005Metric","VM",f"SHUNT_{phase}_FORCE_P")
    passive(s,RES,f"R4{idx}5","SNUBBER R TUNE",x+4100,y+1450,"Resistor_SMD:R_2512_6332Metric",f"OUT{idx}",f"SNUB_{phase}",dnp=True)
    passive(s,CAP,f"C4{idx}3","SNUBBER C TUNE",x+6000,y+1450,C1210,f"SNUB_{phase}","GND",dnp=True)
    sh=s.comp(SHUNT,f"R4{idx}6","BVR-Z-R0005 0.5mR",x+5500,y-100,"Resistor_SMD:R_Shunt_Isabellenhuette_BVR4026","https://www.isabellenhuette.com/fileadmin/Daten/Praezisions_Power_Widerstaende/Datenblaetter/BVR-Z-R0005.pdf",MPN="BVR-Z-R0005-1.0")
    for p,n in (("1",f"SHUNT_{phase}_FORCE_P"),("2",f"SHUNT_{phase}_SENSE_P"),("3",f"SHUNT_{phase}_SENSE_N"),("4","GND")): s.pin_label(sh,p,n)
    passive(s,RES,f"R4{idx}7","1k 0.1%",x+8400,y-700,R0603,f"SHUNT_{phase}_SENSE_P",f"OPP_{phase}1")
    passive(s,RES,f"R4{idx}8","1k 0.1%",x+8400,y,R0603,f"SHUNT_{phase}_SENSE_N",f"OPN_{phase}1")
    passive(s,RES,f"R4{idx}9","28k 0.1%",x+8400,y+700,R0603,f"OPO_{phase}1",f"OPN_{phase}1")
    passive(s,RES,f"R4{idx}0","56k 0.1%",x+5700,y-900,R0603,"VREF+",f"OPP_{phase}1")
    passive(s,RES,f"R44{idx}","56k 0.1%",x+5700,y+700,R0603,f"OPP_{phase}1","GND")
    passive(s,CAP,f"C4{idx}4","47pF C0G",x+8400,y+1400,C0603,f"OPO_{phase}1",f"OPN_{phase}1",dnp=True)


def make_04() -> Sheet:
    s=Sheet("04_Inverter_CurrentSense.sch","04 - Three-Phase Inverter and Current Sensing")
    s.note(500,400,"THREE-PHASE POWER STAGE - 3 x CSD88599Q5DC / 3 x 0.5 mR KELVIN SHUNTS",80,True)
    add_power_block(s,"U",1,5200,2000)
    add_power_block(s,"V",2,5200,5100)
    add_power_block(s,"W",3,5200,8200)
    j=s.comp(SYMS["CONN_3"],"J401","MOTOR U/V/W",15000,10500,"Connector_Wire:SolderWire-6sqmm_1x03_P14mm_D3.5mm_OD7mm")
    s.pin_label(j,"1","OUT1"); s.pin_label(j,"2","OUT2"); s.pin_label(j,"3","OUT3")
    s.note(500,10200,"LAYOUT: each gate resistor sits at its MOSFET gate. Kelvin sense traces leave pads 2/3 of each BVR shunt independently and never share force copper.")
    s.note(500,10550,"Current transfer: VOUT = VREF/2 + 28 x (SENSE_P-SENSE_N); 14 mV/A. Configure COMP1/2/4 on PA1/PA7/PB0 for hardware TIM1 break.")
    s.note(500,10900,"Fit GH=4.7R and GL=0R initially per TI guidance. Snubbers and 47 pF feedback capacitors are DNP tuning positions; bootstrap diodes are internal.")
    return s


def make_05() -> Sheet:
    s=Sheet("05_Brake_Chopper.sch","05 - Brake Chopper")
    s.note(650,500,"LOW-SIDE BRAKE CHOPPER - EXTERNAL RESISTOR",90,True)
    u=s.comp(UCC,"U501","UCC27517ADBVR",4600,3500,"Package_TO_SOT_SMD:SOT-23-5","https://www.ti.com/lit/ds/symlink/ucc27517a.pdf",MPN="UCC27517ADBVR")
    for p,n in (("1","VCC"),("2","GND"),("3","BRAKE_PWM_DRV"),("4","GND"),("5","BRAKE_GATE_DRV")): s.pin_label(u,p,n)
    passive(s,RES,"R501","10k",2200,2700,R0603,"BRAKE_PWM","GND")
    passive(s,RES,"R502","33R",3300,2700,R0603,"BRAKE_PWM","BRAKE_PWM_SER")
    passive(s,DIODE,"D502","BAT54H",4600,1800,"Diode_SMD:D_SOD-123F","BRAKE_PWM_DRV","BRAKE_PWM_SER",mpn="BAT54H,115")
    passive(s,DIODE,"D503","BAT54H",6500,1800,"Diode_SMD:D_SOD-123F","BRAKE_PWM_DRV","BRAKE_OV_CMD",mpn="BAT54H,115")
    passive(s,RES,"R505","10k",8200,1800,R0603,"BRAKE_PWM_DRV","GND")
    ov=s.comp(OVCOMP,"U502","TLV3012BIDBVR",3800,6650,"Package_TO_SOT_SMD:SOT-23-6","https://www.ti.com/lit/ds/symlink/tlv3012.pdf",MPN="TLV3012BIDBVR")
    for p,n in (("1","BRAKE_OV_CMD"),("2","GND"),("3","BRAKE_OV_SENSE"),("4","BRAKE_OV_REF"),("5","BRAKE_OV_REF"),("6","3V3")): s.pin_label(ov,p,n)
    passive(s,RES,"R506","150k 0.1% 100V",1400,4700,"Resistor_SMD:R_1206_3216Metric","VM","BRK_DIV1")
    passive(s,RES,"R507","150k 0.1% 100V",1400,5500,"Resistor_SMD:R_1206_3216Metric","BRK_DIV1","BRK_DIV2")
    passive(s,RES,"R508","150k 0.1% 100V",1400,6300,"Resistor_SMD:R_1206_3216Metric","BRK_DIV2","BRAKE_OV_SENSE")
    passive(s,RES,"R509","12.7k 0.1%",1400,7100,R0603,"BRAKE_OV_SENSE","GND")
    passive(s,RES,"R510","1M 0.1%",5900,6250,R0603,"BRAKE_OV_CMD","BRAKE_OV_SENSE")
    passive(s,CAP,"C503","100nF",5900,7150,C0603,"3V3","GND")
    passive(s,CAP,"C504","1nF C0G",3800,7850,C0603,"BRAKE_OV_SENSE","GND")
    passive(s,CAP,"C501","1uF 25V",6700,2700,C0603,"VCC","GND")
    passive(s,CAP,"C502","100nF 25V",6700,3350,C0603,"VCC","GND")
    passive(s,RES,"R503","4.7R",6700,4300,R0603,"BRAKE_GATE_DRV","BRAKE_GATE")
    q=s.comp(MOS_BRAKE,"Q501","CSD19531Q5A 100V",9400,4300,"ShiroFOC_Footprints:CSD19531Q5A_Q5A_DQJ0008A","../DataSheets/CSD19531Q5A.pdf",MPN="CSD19531Q5A")
    s.pin_label(q,"4","BRAKE_GATE")
    for p in ("5","6","7","8"): s.pin_label(q,p,"BRK_SW")
    for p in ("1","2","3"): s.pin_label(q,p,"GND")
    passive(s,RES,"R504","10k",8000,5400,R0603,"BRAKE_GATE","GND")
    # Gate clamp: pin 1/K to gate, pin 2/A to source/GND.
    passive(s,DIODE,"D501","BZT52C12 12V",9500,5800,"Diode_SMD:D_SOD-123","BRAKE_GATE","GND",mpn="BZT52C12")
    j=s.comp(SYMS["CONN_2"],"J501","BRAKE RESISTOR",12800,4300,"Connector_Wire:SolderWire-2sqmm_1x02_P7.8mm_D2mm_OD3.9mm")
    s.pin_label(j,"1","VM"); s.pin_label(j,"2","BRK_SW")
    passive(s,DIODE,"D504","B5100C 100V 5A",12500,5800,"Diode_SMD:D_SMC","VM","BRK_SW",mpn="B5100C-13-F")
    for ref,net,x in (("TP501","BRAKE_GATE",7000),("TP502","BRK_SW",11500)):
        t=s.comp(TP,ref,net,x,7000,"TestPoint:TestPoint_Pad_D1.5mm"); s.pin_label(t,"1",net)
    s.note(650,8400,"CSD19531Q5A: 100 V, 5.3 mR typ. / 6.4 mR max. at 10 V, 37 nC typ. Qg. The external resistor value and pulse-energy rating are application-specific.")
    s.note(650,8800,"R501/R504/R505 hold the chopper off. U502 can command it independently at approx. 45.9 V rising / 44.2 V falling; fit the external resistor before regeneration.")
    s.note(650,9200,"Connector pin 1 is raw VM. Both brake-resistor wires carry hazardous bus voltage. Place driver decoupling at U501 and use a short Kelvin source return.")
    return s


def make_06() -> Sheet:
    s=Sheet("06_Position_Feedback.sch","06 - Onboard and External Position Feedback")
    s.note(500,400,"AS5047P + EXTERNAL ABI/HALL -> TMUX1574 -> TIM4 CH1/2/3",85,True)
    e=s.comp(AS5047,"U601","AS5047P-ATSM",3000,3200,"Package_SO:TSSOP-14_4.4x5mm_P0.65mm","https://ams-osram.com/products/sensors/position-sensors/ams-as5047p-high-resolution-position-sensor",MPN="AS5047P-ATSM")
    emap={"1":"AS5047P_CS_N","2":"SPI3_SCK","3":"AS5047_MISO_RAW","4":"SPI3_MOSI","5":"GND","13":"GND","7":"ENC_ON_A","6":"ENC_ON_B","14":"ENC_ON_I","11":"3V3","12":"3V3"}
    for p,n in emap.items(): s.pin_label(e,p,n)
    for p in ("8","9","10"): s.nc(e,p)
    passive(s,CAP,"C601","100nF",900,2100,C0603,"3V3","GND")
    passive(s,CAP,"C602","1uF",900,2750,C0603,"3V3","GND")
    passive(s,RES,"R601","33R",5100,2250,R0603,"ENC_ON_A","MUX_ON_A")
    passive(s,RES,"R602","33R",5100,2900,R0603,"ENC_ON_B","MUX_ON_B")
    passive(s,RES,"R603","33R",5100,3550,R0603,"ENC_ON_I","MUX_ON_I")
    passive(s,RES,"R611","33R",5100,4200,R0603,"AS5047_MISO_RAW","SPI3_MISO")
    j=s.comp(SYMS["CONN_6"],"J601","EXT ENCODER / HALL",2600,7300,"Connector_JST:JST_GH_BM06B-GHS-TBT_1x06-1MP_P1.25mm_Vertical",MPN="BM06B-GHS-TBT")
    for p,n in (("1","3V3_EXT_FB"),("2","GND"),("3","EXT_A_U_CONN"),("4","EXT_B_V_CONN"),("5","EXT_I_W_CONN")): s.pin_label(j,p,n)
    s.nc(j,"6")
    passive(s,RES,"R604","0R; external load <=25mA",900,6500,R0603,"3V3","3V3_EXT_FB")
    esd=s.comp(TPD3E001,"D601","TPD3E001DRLR 3-line ESD",5100,7300,"Package_TO_SOT_SMD:Texas_R-PDSO-N5_DRL-5","https://www.ti.com/lit/ds/symlink/tpd3e001.pdf",MPN="TPD3E001DRLR")
    for p,n in (("1","EXT_A_U_CONN"),("2","EXT_B_V_CONN"),("4","EXT_I_W_CONN"),("3","GND"),("5","FB_ESD_RAIL")): s.pin_label(esd,p,n)
    passive(s,RES,"R605","100R",7300,6500,R0603,"EXT_A_U_CONN","MUX_EXT_A")
    passive(s,RES,"R606","100R",7300,7150,R0603,"EXT_B_V_CONN","MUX_EXT_B")
    passive(s,RES,"R607","100R",7300,7800,R0603,"EXT_I_W_CONN","MUX_EXT_I")
    passive(s,RES,"R608","10k DNP Hall pull-up",9400,6500,R0603,"3V3","MUX_EXT_A",dnp=True)
    passive(s,RES,"R609","10k DNP Hall pull-up",9400,7150,R0603,"3V3","MUX_EXT_B",dnp=True)
    passive(s,RES,"R610","10k DNP Hall pull-up",9400,7800,R0603,"3V3","MUX_EXT_I",dnp=True)
    m=s.comp(TMUX,"U602","TMUX1574PW",11500,5000,"Package_SO:TSSOP-16_4.4x5mm_P0.65mm","https://www.ti.com/lit/ds/symlink/tmux1574.pdf",MPN="TMUX1574PW")
    mmap={"4":"FEEDBACK_A_H1","7":"FEEDBACK_B_H2","9":"FEEDBACK_I_H3","1":"FEEDBACK_SELECT","15":"FEEDBACK_ENABLE_N",
          "2":"MUX_ON_A","3":"MUX_EXT_A","5":"MUX_ON_B","6":"MUX_EXT_B","11":"MUX_ON_I","10":"MUX_EXT_I",
          "12":"VBUS_SENSE","13":"VBUS_MUX_IN","14":"VBUS_MUX_IN","16":"3V3","8":"GND"}
    for p,n in mmap.items(): s.pin_label(m,p,n)
    passive(s,CAP,"C603","100nF",14000,4700,C0603,"3V3","GND")
    passive(s,CAP,"C604","100nF 50V",5100,8450,C0603,"FB_ESD_RAIL","GND")
    s.note(500,9300,"Default: FEEDBACK_ENABLE_N high disables all outputs; FEEDBACK_SELECT low selects onboard encoder after firmware explicitly enables the mux.")
    s.note(500,9650,"MUX channel 4 isolates VBUS_SENSE when unpowered. Enable mux and wait 2 ms before reading VM; disable PWM before disabling mux. J601 pin 6 NC.")
    s.note(500,10000,"D601 pin 5 uses an isolated 100 nF ESD rail; no DC tie to 3V3. External signals: 0-3.3 V only, including when board power is off.")
    return s


def make_07() -> Sheet:
    s=Sheet("07_IMU_Temperature.sch","07 - IMU and Half-Bridge Temperature")
    s.note(500,400,"BMI323 4-WIRE SPI + THREE IDENTICAL NTC CHANNELS",85,True)
    u=s.comp(BMI,"U701","BMI323",3500,3100,"Package_LGA:Bosch_LGA-14_3x2.5mm_P0.5mm","https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi323-ds000.PDF",MPN="BMI323")
    bmap={"1":"BMI323_MISO_RAW","4":"IMU_INT1","5":"3V3","6":"GND","7":"GND","14":"SPI3_MOSI","13":"SPI3_SCK","12":"IMU_CS_N","9":"IMU_INT2","8":"3V3"}
    for p,n in bmap.items(): s.pin_label(u,p,n)
    for p in ("2","3","10","11"): s.nc(u,p)
    passive(s,CAP,"C701","100nF",1000,2400,C0603,"3V3","GND")
    passive(s,CAP,"C702","100nF",1000,3050,C0603,"3V3","GND")
    passive(s,RES,"R714","33R",5500,4700,R0603,"BMI323_MISO_RAW","SPI3_MISO")
    s.note(700,5400,"Pin 1 SDO=MISO, pin 14 SDI=MOSI, pin 13 SCK, pin 12 CSB. Mark package X/Y axes on silkscreen; avoid vias under package.")
    for idx,(phase,x) in enumerate((("A",7600),("B",10300),("C",13000)),1):
        passive(s,RES,f"R70{idx}","4.7k 1%",x,2500,R0603,"3V3",f"NTC_{phase}_RAW")
        passive(s,RES,f"TH70{idx}","10k NTC B3380",x,3300,R0603,f"NTC_{phase}_RAW","GND",mpn="NCP18XH103F03RB")
        passive(s,RES,f"R71{idx}","1k",x,4100,R0603,f"NTC_{phase}_RAW",f"NTC_PHASE_{phase}")
        passive(s,CAP,f"C71{idx}","10nF",x,4900,C0603,f"NTC_PHASE_{phase}","GND")
        t=s.comp(TP,f"TP70{idx}",f"NTC_{phase}",x,5800,"TestPoint:TestPoint_Pad_D1.0mm"); s.pin_label(t,"1",f"NTC_PHASE_{phase}")
    s.note(500,7200,"NTC divider behavior: open thermistor -> ADC near 3.3 V; short -> ADC near 0 V. Firmware treats both as faults and uses the hottest valid reading.")
    s.note(500,7600,"Initial fixed resistor 4.7k improves resolution over roughly 40-120 C. Calibrate thresholds against measured MOSFET case/junction temperature.")
    return s


def make_08() -> Sheet:
    s=Sheet("08_CAN.sch","08 - CAN / CAN-FD Interface")
    s.note(600,450,"3.3 V CAN-FD TRANSCEIVER WITH DAISY-CHAIN CONNECTORS",85,True)
    u=s.comp(TCAN,"U801","TCAN3413DR",5200,3500,"Package_SO:SOIC-8_3.9x4.9mm_P1.27mm","https://www.ti.com/lit/ds/symlink/tcan3413.pdf",MPN="TCAN3413DR")
    for p,n in (("1","FDCAN1_TX"),("4","FDCAN1_RX"),("8","CAN_STB"),("7","CANH_INT"),("6","CANL_INT"),("3","3V3"),("5","3V3"),("2","GND")): s.pin_label(u,p,n)
    passive(s,RES,"R801","10k",2300,2600,R0603,"3V3","CAN_STB")
    passive(s,RES,"R805","10k",2300,4800,R0603,"3V3","FDCAN1_TX")
    passive(s,CAP,"C801","100nF",2300,3300,C0603,"3V3","GND")
    passive(s,CAP,"C802","1uF",2300,4000,C0603,"3V3","GND")
    passive(s,RES,"R803","0R CANH link",7900,3150,R0603,"CANH_INT","CANH_BUS")
    passive(s,RES,"R804","0R CANL link",7900,3850,R0603,"CANL_INT","CANL_BUS")
    d=s.comp(CAN_ESD,"D801","PESD2CANFD24V-T",9900,3500,"Package_TO_SOT_SMD:SOT-23","https://assets.nexperia.com/documents/data-sheet/PESD2CANFD24V-T.pdf",MPN="PESD2CANFD24V-T")
    s.pin_label(d,"1","CANH_BUS"); s.pin_label(d,"2","CANL_BUS"); s.pin_label(d,"3","GND")
    passive(s,RES,"R802","120R 1%",11500,2750,R0603,"CANH_BUS","CAN_TERM_MID",dnp=True)
    passive(s,SW,"JP801","TERM ENABLE",11500,4800,"Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm","CAN_TERM_MID","CANL_BUS",dnp=True)
    for k,x in ((1,12800),(2,14500)):
        j=s.comp(SYMS["CONN_4"],f"J80{k}",f"CAN {k}",x,3500,"Connector_JST:JST_GH_BM04B-GHS-TBT_1x04-1MP_P1.25mm_Vertical",MPN="BM04B-GHS-TBT")
        for p,n in (("1","GND"),("2","CANL_BUS"),("3","CANH_BUS"),("4","CAN_SHIELD")): s.pin_label(j,p,n)
    s.note(600,6300,"CAN_STB (PB10) has a pull-up: standby through reset. Configure FDCAN TX recessive before driving STB low. Fit termination only at bus ends.")
    s.note(600,6700,"CAN connector pinout is identical on both JST-GH headers. Twist CANH/CANL. Pin 4 is shield/drain provision and is not a power conductor.")
    return s


def make_09() -> Sheet:
    s=Sheet("09_USB_UART.sch","09 - USB-UART Service Interface")
    s.note(600,450,"CP2102N USB-UART - SERVICE, LOGS AND ROM-UART PROGRAMMING",85,True)
    u=s.comp(CP2102,"U901","CP2102N-A02-GQFN20",6000,3900,"Package_DFN_QFN:SiliconLabs_QFN-20-1EP_3x3mm_P0.5mm_EP1.8x1.8mm_ThermalVias","https://www.silabs.com/documents/public/data-sheets/cp2102n-datasheet.pdf",MPN="CP2102N-A02-GQFN20")
    for p,n in (("8","CP2102_VBUS_SENSE"),("5","USB_DM"),("4","USB_DP"),("7","3V3"),("6","3V3"),("9","CP2102_RST_N"),("18","UART_BRIDGE_TX"),("17","UART_BRIDGE_RX"),("3","GND"),("12","GND"),("21","GND")): s.pin_label(u,p,n)
    for p in ("1","2","10","11","13","14","15","16","19","20"): s.nc(u,p)
    passive(s,CAP,"C901","4.7uF 10V",2800,2300,C0603,"3V3","GND")
    passive(s,CAP,"C902","100nF",2800,2850,C0603,"3V3","GND")
    passive(s,CAP,"C903","4.7uF 10V",2800,3400,C0603,"3V3","GND")
    passive(s,CAP,"C904","100nF",2800,3950,C0603,"3V3","GND")
    passive(s,RES,"R901","1k",2800,4550,R0603,"3V3","CP2102_RST_N")
    passive(s,RES,"R902","100R",9100,3300,R0603,"UART_BRIDGE_TX","USB_UART_RX")
    passive(s,RES,"R903","100R",9100,3950,R0603,"USB_UART_TX","UART_BRIDGE_RX")
    passive(s,RES,"R904","22.1k 1%",9100,4700,R0603,"5V_USB_RAW","CP2102_VBUS_SENSE")
    passive(s,RES,"R905","47.5k 1%",9100,5250,R0603,"CP2102_VBUS_SENSE","GND")
    for ref,net,x in (("TP901","USB_UART_TX",10800),("TP902","USB_UART_RX",12200),("TP903","GND",13600)):
        t=s.comp(TP,ref,net,x,5600,"TestPoint:TestPoint_Pad_D1.0mm"); s.pin_label(t,"1",net)
    s.note(600,7200,"CP2102N regulator bypass: VREGIN and VDD both use 3V3 (datasheet Fig. 2.3). MCU and UART therefore have the same startup rail.")
    s.note(600,7600,"Manual BOOT0 and NRST remain on the SWD/test sheet. CP2102 RTS is intentionally not wired to reset in Rev A.")
    return s


def make_10() -> Sheet:
    s=Sheet("10_SWD_Test.sch","10 - SWD, Boot and Test Access")
    s.note(600,450,"10-PIN ARM CORTEX SWD + BOOT/POWER TEST ACCESS",85,True)
    j=s.comp(SYMS["CONN_10"],"J1001","ARM Cortex SWD 10-pin",3600,3300,"Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD",MPN="FTSH-105-01-L-DV-K")
    # Standard Cortex pinout: 1 VTref, 2 SWDIO, 3 GND, 4 SWCLK, 5 GND, 6 SWO/NC, 7 KEY, 8 NC, 9 GNDDetect, 10 NRST.
    for p,n in (("1","3V3"),("2","SWDIO"),("3","GND"),("4","SWCLK"),("5","GND"),("9","GND"),("10","NRST")): s.pin_label(j,p,n)
    for p in ("6","7","8"): s.nc(j,p)
    passive(s,RES,"R1001","1k",6900,2500,R0603,"FEEDBACK_I_H3","BOOT0_PAD")
    passive(s,SW,"SW1001","BOOT0",8800,2500,"Button_Switch_SMD:SW_SPST_TL3305A","BOOT0_PAD","3V3")
    passive(s,SW,"SW1002","RESET",8800,3300,"Button_Switch_SMD:SW_SPST_TL3305A","NRST","GND")
    nets=["VM","VCC","5V_BAT","5V_USB","5V_SYS","3V3","NRST","SWDIO","SWCLK","SPI3_SCK","SPI3_MISO","SPI3_MOSI","FDCAN1_TX","FDCAN1_RX","FEEDBACK_A_H1","FEEDBACK_B_H2","FEEDBACK_I_H3","OPO_U1","OPO_V1","OPO_W1","SPARE_GPIO_1","CAN_STB","SPARE_GPIO_3","SPARE_TIM_GPIO"]
    for i,net in enumerate(nets):
        if net == "FEEDBACK_I_H3": continue  # No PB8/BOOT0 test stub.
        x=650+(i%10)*1450; y=5600+(i//10)*1300
        t=s.comp(TP,f"TP{1001+i}",net,x,y,"TestPoint:TestPoint_Pad_D1.0mm"); s.pin_label(t,"1",net)
    s.note(600,9000,"The debugger must sense target 3V3 on VTREF; it must not source 3V3 into the board. PB3 is SPI3_SCK, therefore SWO is NC in Rev A.")
    s.note(600,9400,"BOOT0 shares PB8 with feedback I/H3. The mux is disabled during reset; the 1k button path permits deliberate ROM-boot entry without hard-shorting an active encoder output.")
    return s


def root_sheet(children: list[Sheet]) -> str:
    lines=["EESchema Schematic File Version 4","LIBS:ShiroFOC_KiCad-cache","EELAYER 29 0","EELAYER END","$Descr A3 16535 11693","encoding utf-8","Sheet 1 11",
           'Title "ShiroFOC Rev A"','Date "2026-09-15"','Rev "A"','Comp "ShiroFOC"','Comment1 "Hierarchical first-build FOC motor controller"','Comment2 "6S-10S LiPo / 18-42 V; 60 V inverter devices"','Comment3 "USB-powered control domain; CAN production interface"','Comment4 "See ../docs/DESIGN_REVIEW_REV_A.md before PCB layout"',"$EndDescr"]
    notes=[
        (600,450,"ShiroFOC Rev A - SYSTEM OVERVIEW",100),
        (600,850,"VM -> DC link + inverter + STSPIN VCC buck + 5V_BAT buck",60),
        (600,1150,"USB VBUS + 5V_BAT -> TPS2121 (USB priority) -> 5V_SYS -> 3V3",60),
        (600,1450,"STSPIN32G4 -> three CSD88599Q5DC power blocks -> motor U/V/W",60),
        (600,1750,"CAN is the normal production interface. USB-UART and SWD are local service interfaces.",60),
    ]
    for x,y,t,z in notes: lines.append(f"Text Notes {x} {y} 0    {z}   ~ 0\n{t}")
    for i,ch in enumerate(children):
        col=i%2; row=i//2
        x=900+col*7600; y=2450+row*1550; uid=0x20000000+i
        lines += ["$Sheet",f"S {x} {y} 6500 1050",f"U {uid:08X}",f'F0 "{ch.title}" 55',f'F1 "{ch.filename}" 55',"$EndSheet"]
    lines += [
        "Text Notes 600 10600 0    55   ~ 0\nRELEASE CONDITIONS: ERC clean; exact footprints/pad maps verified; startup defaults off; all DNP states documented; review log signed before layout.",
        "$EndSCHEMATC",
    ]
    return "\n".join(lines)+"\n"


def custom_footprints():
    # TLV755 DYD0005A: TI land pattern 4228946/A.  The exposed pad is
    # internally GND, so it intentionally reuses electrical pad number 2.
    # P0: use a 0.975 x 1.7 mm NSMD thermal land at +0.0625 mm.
    # Retains TI exposed solderable area; omits the wider covered heat-spreader
    # to meet the project 0.15 mm outer-copper clearance. Via remains GND.
    dyd='''(footprint "Texas_DYD0005A_SOT23-5" (version 20240108) (generator pcbnew)
  (layer "F.Cu")
  (descr "Texas DYD0005A thermally enhanced SOT-23-5; TI drawing 4228946/A")
  (attr smd)
  (fp_rect (start -0.8 -1.45) (end 0.8 1.45) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))
  (fp_circle (center -1.75 -1.45) (end -1.60 -1.45) (stroke (width 0.1) (type default)) (fill none) (layer "F.SilkS"))
  (fp_rect (start -2.1 -1.9) (end 2.1 1.9) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))
  (pad "1" smd roundrect (at -1.30 -0.95) (size 1.1 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2))
  (pad "2" smd roundrect (at -1.30 0) (size 1.1 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2))
  (pad "3" smd roundrect (at -1.30 0.95) (size 1.1 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2))
  (pad "4" smd roundrect (at 1.30 0.95) (size 1.1 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2))
  (pad "5" smd roundrect (at 1.30 -0.95) (size 1.1 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2))
  (pad "2" smd roundrect (at 0.0625 0) (size 0.975 1.7) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.06))
  (pad "" smd roundrect (at 0.0625 0) (size 0.975 1.7) (layers "F.Paste") (roundrect_rratio 0.06))
  (pad "2" thru_hole circle (at 0.0625 0) (size 0.45 0.45) (drill 0.20) (layers "*.Cu" "*.Mask"))
)
'''
    # DMM0022A land pattern from TI drawing 4222731/B.
    pads=[]
    for num in range(1,12):
        # Pin 1 is at the marked upper-left corner; KiCad Y grows downward.
        y=-2.5+(num-1)*0.5
        pads.append(f'  (pad "{num}" smd roundrect (at -2.35 {y:.2f}) (size 0.70 0.25) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2))')
    for num in range(12,23):
        y=2.5-(num-12)*0.5
        pads.append(f'  (pad "{num}" smd roundrect (at 2.35 {y:.2f}) (size 0.70 0.25) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2))')
    # Continuous metal beneath each common power-lead bank, per TI drawing.
    # The individual lead pads retain their mask/paste openings.
    for number,x in ((3,-2.35),(12,2.35)):
        pads.append(f'  (pad "{number}" smd rect (at {x} 0.5) (size 0.80 4.35) (layers "F.Cu"))')
    edge={23:(-2.115,-3.013),24:(-2.115,3.013),25:(2.115,3.013),26:(2.115,-3.013)}
    for num,(x,y) in edge.items(): pads.append(f'  (pad "{num}" smd roundrect (at {x} {y}) (size 0.43 0.375) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2))')
    pads.append('  (pad "27" smd rect (at 0 0) (size 3.3 5.4) (layers "F.Cu" "F.Mask"))')
    for x in (-0.8,0.8):
        for y in (-1.98,-0.66,0.66,1.98):
            pads.append(f'  (pad "" smd roundrect (at {x} {y}) (size 1.41 1.12) (layers "F.Paste") (roundrect_rratio 0.08))')
    # Optional TI thermal-via array inside the VIN exposed pad.  Pad 27 is VIN,
    # not GND; retaining the pad number preserves that electrical connection.
    for x in (-1.4,0,1.4):
        for y in (-1.32,0,1.32):
            pads.append(f'  (pad "27" thru_hole circle (at {x} {y}) (size 0.45 0.45) (drill 0.20) (layers "*.Cu" "*.Mask"))')
    csd='''(footprint "CSD88599Q5DC_DMM0022A" (version 20240108) (generator pcbnew)
  (layer "F.Cu")
  (descr "TI DMM0022A 5x6 mm dual-cool power block; land pattern from CSD88599Q5DC datasheet")
  (attr smd)
  (fp_rect (start -2.55 -3.05) (end 2.55 3.05) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))
  (fp_line (start -2.75 -3.2) (end -2.75 -2.7) (stroke (width 0.12) (type default)) (layer "F.SilkS"))
  (fp_line (start -2.75 -3.2) (end -2.25 -3.2) (stroke (width 0.12) (type default)) (layer "F.SilkS"))
  (fp_rect (start -2.85 -3.35) (end 2.85 3.35) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))
'''+"\n".join(pads)+"\n)\n"
    # CSD19531Q5A Q5A/DQJ0008A.  Copper geometry follows TI's recommended
    # PCB pattern (SLPS406B, section 7.2); paste apertures follow section 7.3.
    # TI's official pinout is 1-3 source, 4 gate and 5-8 drain.  The exposed
    # central drain land therefore reuses electrical pad number 5.
    q5a_pads=[]
    for num,y in ((5,-1.905),(6,-0.635),(7,0.635),(8,1.905)):
        q5a_pads.append(f'  (pad "{num}" smd rect (at -2.800 {y:.3f}) (size 0.655 0.675) (layers "F.Cu" "F.Mask"))')
        q5a_pads.append(f'  (pad "" smd rect (at -2.800 {y:.3f}) (size 0.500 0.500) (layers "F.Paste"))')
    for num,y in ((4,-1.905),(3,-0.635),(2,0.635),(1,1.905)):
        q5a_pads.append(f'  (pad "{num}" smd rect (at 2.7525 {y:.3f}) (size 0.750 0.675) (layers "F.Cu" "F.Mask"))')
        q5a_pads.append(f'  (pad "" smd rect (at 2.7525 {y:.3f}) (size 0.500 0.500) (layers "F.Paste"))')
    q5a_pads.append('  (pad "5" smd rect (at -0.325 0) (size 4.295 4.510) (layers "F.Cu" "F.Mask"))')
    for x,w in ((-1.0425,1.585),(0.8675,1.235)):
        for y in (-0.9775,0.9775):
            q5a_pads.append(f'  (pad "" smd rect (at {x:.4f} {y:.4f}) (size {w:.3f} 1.570) (layers "F.Paste"))')
    q5a='''(footprint "CSD19531Q5A_Q5A_DQJ0008A" (version 20240108) (generator pcbnew)
  (layer "F.Cu")
  (descr "TI CSD19531Q5A Q5A/DQJ0008A SON 5x6 mm; TI recommended copper and stencil patterns")
  (attr smd)
  (fp_rect (start -3.00 -2.50) (end 3.00 2.50) (stroke (width 0.10) (type default)) (fill none) (layer "F.Fab"))
  (fp_line (start 3.15 2.65) (end 2.65 2.65) (stroke (width 0.12) (type default)) (layer "F.SilkS"))
  (fp_line (start 3.15 2.65) (end 3.15 2.15) (stroke (width 0.12) (type default)) (layer "F.SilkS"))
  (fp_rect (start -3.35 -2.75) (end 3.35 2.75) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))
'''+"\n".join(q5a_pads)+"\n)\n"
    we = """(footprint "WE_LHMI_7050_74437349220" (version 20240108) (generator pcbnew)
 (layer "F.Cu") (attr smd)
 (descr "Wurth 74437349220; official 2024-12-27 land pattern; no vias or traces in central 2.5mm strip")
 (fp_rect (start -3.8 -3.45)(end 3.8 3.45)(stroke(width .1)(type default))(fill none)(layer "F.Fab"))
 (fp_rect (start -4.45 -3.7)(end 4.45 3.7)(stroke(width .05)(type default))(fill none)(layer "F.CrtYd"))
 (fp_line(start -3.3 -3.6)(end 3.3 -3.6)(stroke(width .12)(type default))(layer "F.SilkS"))
 (fp_line(start -3.3 3.6)(end 3.3 3.6)(stroke(width .12)(type default))(layer "F.SilkS"))
 (pad "1" smd rect(at -2.725 0)(size 2.95 3.5)(layers "F.Cu" "F.Paste" "F.Mask"))
 (pad "2" smd rect(at 2.725 0)(size 2.95 3.5)(layers "F.Cu" "F.Paste" "F.Mask"))
 (zone (net 0) (net_name "") (layers "F.Cu") (name "No copper below inductor")
 (hatch edge 0.5)(connect_pads(clearance 0))(min_thickness 0.25)(filled_areas_thickness no)
 (keepout(tracks not_allowed)(vias not_allowed)(pads allowed)(copperpour not_allowed)(footprints allowed))
 (placement(enabled no)(sheetname ""))(fill(thermal_gap 0.5)(thermal_bridge_width 0.5))
 (polygon(pts(xy -1.25 -3.5)(xy 1.25 -3.5)(xy 1.25 3.5)(xy -1.25 3.5)))))
"""
    (FPDIR/"WE_LHMI_7050_74437349220.kicad_mod").write_text(we)
    (FPDIR/"Texas_DYD0005A_SOT23-5.kicad_mod").write_text(dyd)
    (FPDIR/"CSD88599Q5DC_DMM0022A.kicad_mod").write_text(csd)
    (FPDIR/"CSD19531Q5A_Q5A_DQJ0008A.kicad_mod").write_text(q5a)


def main():
    # One authoritative native serializer; preserve manual project settings/docs.
    from native_rev_a import main as native_main
    native_main()


if __name__ == "__main__":
    main()
