"""Hand-wired DC link, auxiliary power and brake drawings.

This is a drawing-only refactor: component data and pin nets come from the A0
circuit definitions through redraw_engine; no parts are added or substituted.
"""
from redraw_engine import Page, poly


def _vertical(page, ref, x, y, top, bottom):
    page.part(ref, x, y, 'v')
    page.wire(page.p(ref, 1), (x, top))
    page.wire(page.p(ref, 2), (x, bottom))


def _fields(page, ref_pos=None, value_pos=None):
    if ref_pos is not None:
        page.placements[-1]['ref_pos'] = ref_pos
    if value_pos is not None:
        page.placements[-1]['value_pos'] = value_pos


def build_dc():
    p = Page('01_Battery_DC_Link', 'Battery input, DC link and bus measurement', 'A4')
    p.heading(14, 18, 'BATTERY / DC LINK')
    p.note(14, 23, '18-42 V operating bus • keyed XT60 • external fuse / precharge required')
    p.ic('J101', 22, 57, {1:(9,4,'R'), 2:(9,-4,'R')}, w=10, h=12)
    p.wire(p.p('J101',2), (36,53), (36,45), (205,45))
    p.wire(p.p('J101',1), (31,69), (205,69))
    p.power('VM', (40,45)); p.power('GND', (40,69), up=False)
    for ref, x in [('C101',50),('C102',74),('C103',98),('C104',124),
                   ('C105',151),('C106',178),('R101',205)]:
        _vertical(p, ref, x, 57, 45, 69)
    p.tp('TP101',(50,45)); p.tp('TP102',(50,69))
    p.wire((40,45),(40,34)); p.tp('TP1001',(40,34))
    p.note(51,29,'3 × 680 µF / 63 V bulk + local high-frequency bypass')

    p.heading(14,80,'OPTIONAL INPUT DAMPING')
    p.part('R102',25,98,'v'); p.part('C107',25,115,'v')
    p.wire(p.p('R102',2),p.p('C107',1))
    p.supply('R102',1,'VM',dy=-5); p.supply('C107',2,'GND',dy=5)
    p.part('D101',78,107,'v')
    p.supply('D101',1,'VM',dy=-7); p.supply('D101',2,'GND',dy=7)
    p.note(14,133,'DNP: choose clamp and damping only after cable / hot-plug tests.',size=1.016)

    p.heading(128,80,'BUS DIVIDER / ISOLATED ADC FILTER')
    p.part('R103',136,94); p.part('R104',164,94); p.part('R106',197,94)
    p.wire(p.p('R103',2),p.p('R104',1))
    p.wire(p.p('R104',2),p.p('R106',1))
    p.wire(p.p('R103',1),(128,94)); p.power('VM',(128,94))
    p.part('R105',179,111,'v')
    p.wire((179,94),p.p('R105',1)); p.supply('R105',2,'GND',dy=5)
    p.out('R106',2,'VBUS_MUX_IN',dx=7)
    p.part('C108',201,117,'v')
    p.wire(p.p('C108',1),(201,106),(209,106))
    p.port('VBUS_SENSE',(209,106),side='R')
    p.tp('TP103',(201,106)); p.supply('C108',2,'GND',dy=4)
    p.note(129,124,'VM / 21 → U602 channel 4 → VBUS_SENSE',size=1.016)
    p.note(129,128,'2.00 V at 42 V; filter is AFTER isolation.',size=1.016)
    return p


def build_aux():
    p = Page('02_Auxiliary_Power', 'Auxiliary supplies / USB priority', 'A3')
    p.heading(14,18,'AUXILIARY POWER - USB HAS PRIORITY')
    p.heading(20,27,'BATTERY → 5 V BUCK')
    p.ic('U201',75,58,{
        2:(-19,-10,'L'),3:(-19,-4,'L'),8:(19,-10,'R'),
        7:(6,-21,'T'),6:(-8,21,'B'),5:(19,11,'R'),4:(19,3,'R'),
        1:(0,21,'B'),9:(0,21,'B',False)},w=30,h=34)
    _fields(p,(66,38),(75,60))
    p.wire((22,48),p.p('U201',2)); p.power('VM',(25,48))
    p.wire(p.p('U201',3),(52,54),(52,48))
    for ref,x in [('C201',22),('C202',40)]:
        _vertical(p,ref,x,65,48,81)
    p.wire((22,81),(40,81)); p.power('GND',(31,81),up=False)
    p.part('L201',119,48)
    p.wire(p.p('U201',8),p.p('L201',1))
    p.wire(p.p('L201',2),(177,48)); p.power('5V_BAT',(177,48))
    p.part('C203',100,35)
    p.wire(p.p('U201',7),(81,35),p.p('C203',1))
    p.wire(p.p('C203',2),(106,35),(106,48))
    p.part('C204',67,90,'v')
    p.wire(p.p('U201',6),p.p('C204',1))
    p.wire(p.p('C204',2),(67,98),(75,98),p.p('U201',1))
    p.power('GND',(75,98),up=False)
    for ref,x in [('C205',142),('C206',165)]:
        _vertical(p,ref,x,63,48,81)
    p.wire((142,81),(165,81)); p.power('GND',(157,81),up=False)
    p.part('R201',124,69,'v'); p.part('R202',124,88,'v')
    p.wire((124,48),p.p('R201',1))
    p.wire(p.p('R201',2),p.p('R202',1))
    p.wire(p.p('U201',5),(107,69),(107,79),(124,79))
    p.supply('R202',2,'GND',dy=6)
    p.label('5V_FB',(107,79)); p.tp('TP201',(142,48))
    p.wire((155,48),(155,40)); p.tp('TP1003',(155,40))
    p.note(95,104,'FB loop: 100 kΩ / 24.9 kΩ → approximately 5.02 V',size=1.016)

    p.heading(214,27,'5 V SYSTEM → 3.3 V')
    p.ic('U204',251,59,{1:(-17,-5,'L'),3:(-17,3,'L'),
         5:(17,-5,'R'),4:(17,5,'R'),2:(0,15,'B')},w=26,h=22)
    _fields(p,(251,45),(251,59))
    p.wire((217,54),p.p('U204',1)); p.power('5V_SYS',(217,54))
    p.wire(p.p('U204',3),(230,62),(230,54))
    p.wire(p.p('U204',5),(293,54)); p.power('3V3',(293,54))
    _vertical(p,'C212',220,67,54,81); _vertical(p,'C213',283,67,54,81)
    p.wire((220,81),(283,81)); p.wire(p.p('U204',2),(251,81))
    p.power('GND',(251,81),up=False)
    p.tp('TP203',(227,54)); p.tp('TP204',(274,54))
    p.wire((217,54),(207,54),(207,45)); p.tp('TP1005',(207,45))
    p.wire((293,54),(305,54),(305,45)); p.tp('TP1006',(305,45))
    p.note(214,92,'Debugger VTREF is sense-only: never inject 3V3.',size=1.016)
    p.note(214,97,'U204 thermal pad / pin 2 returns to GND.',size=1.016)

    p.heading(20,112,'USB-PRIORITY POWER MUX')
    p.note(20,117,'5V_USB arrives from the USB service sheet.',size=1.016)
    p.ic('U203',155,154,{
        7:(-21,-25,'L'),2:(-21,-18,'L'),6:(-21,-7,'L'),5:(-21,17,'L'),
        3:(21,-7,'R'),4:(21,17,'R'),9:(21,28,'R'),
        1:(0,-36,'T'),8:(0,-36,'T',False),
        11:(-8,36,'B'),10:(8,36,'B'),12:(0,36,'B')},w=34,h=60)
    _fields(p,(145,127),(155,156))
    for pin,net in [(7,'5V_BAT'),(2,'5V_USB')]:
        a=p.p('U203',pin); p.wire(a,(125,a[1])); p.power(net,(125,a[1]))
    p.wire(p.p('U203',1),(155,109),(214,109)); p.power('5V_SYS',(155,109))
    for ref,x in [('C210',185),('C211',214)]:
        _vertical(p,ref,x,120,109,132)
    p.wire((185,132),(214,132)); p.power('GND',(214,132),up=False)
    # Each threshold is a complete local divider; no midpoint relies on labels.
    for top,bottom,x,cy,net,pin in [
        ('R206','R207',110,139,'5V_BAT',6),
        ('R210','R211',80,163,'5V_BAT',5),
        ('R208','R209',200,139,'5V_USB',3),
        ('R212','R213',230,163,'5V_USB',4)]:
        p.part(top,x,cy,'v'); p.part(bottom,x,cy+16,'v')
        p.wire(p.p(top,2),p.p(bottom,1))
        p.supply(top,1,net,dy=-5); p.supply(bottom,2,'GND',dy=5)
        p.wire((x,cy+8),p.p('U203',pin))
    p.part('C209',147,199,'v'); p.part('R214',163,199,'v')
    p.wire(p.p('U203',11),p.p('C209',1)); p.wire(p.p('U203',10),p.p('R214',1))
    p.wire(p.p('C209',2),(147,207),(163,207),p.p('R214',2))
    p.wire(p.p('U203',12),(155,207)); p.power('GND',(155,207),up=False)
    p.part('R215',265,169,'v'); p.supply('R215',1,'3V3',dy=-5)
    p.wire(p.p('R215',2),(265,195))
    p.wire(p.p('U203',9),(190,182),(190,195),(288,195))
    p.port('PWR_SOURCE_STATUS',(288,195),side='R')
    p.note(20,194,'At 5 V: PR1 = 1.269 V; CP2 = 1.689 V.',size=1.016)
    p.note(20,199,'USB wins the priority comparison. OV ≈ 5.43 V.',size=1.016)
    p.note(20,204,'80.6 kΩ sets approximately 1.5 A current limit.',size=1.016)
    return p


def build_brake():
    p = Page('05_Brake_Chopper','Brake chopper / overvoltage protection','A3')
    p.heading(14,18,'BRAKE CHOPPER - TWO COMMAND SOURCES, ONE GATE DRIVE')
    p.heading(20,28,'FIRMWARE / HARDWARE DIODE OR')
    p.part('R502',52,40); p.part('D502',70,40,flip=True)
    p.wire((20,40),p.p('R502',1)); p.port('BRAKE_PWM',(20,40),side='L')
    p.wire(p.p('R502',2),p.p('D502',2))
    p.part('R501',35,55,'v'); p.wire((35,40),p.p('R501',1)); p.supply('R501',2,'GND',dy=6)
    p.wire(p.p('D502',1),(140,40),(140,98),(158,98))
    p.part('D503',121,63,'v')
    p.wire((121,40),p.p('D503',1))
    p.part('R505',136,73,'v'); p.wire((136,40),p.p('R505',1)); p.supply('R505',2,'GND',dy=6)
    p.label('BRAKE_PWM_DRV',(96,40))

    p.heading(154,28,'LOCAL GATE DRIVE / POWER SWITCH')
    p.ic('U501',174,100,{1:(-16,-10,'L'),3:(-16,-2,'L'),
         4:(-16,5,'L'),2:(-16,10,'L'),5:(16,0,'R')},w=24,h=28)
    _fields(p,(174,88.5),None)
    p.wire(p.p('U501',1),(151,90),(151,62),(192,62)); p.power('VCC',(151,62))
    for ref,x in [('C501',166),('C502',192)]:
        _vertical(p,ref,x,73,62,84)
    p.wire((166,84),(192,84)); p.power('GND',(192,84),up=False)
    p.wire(p.p('U501',4),(146,105),(146,118)); p.wire(p.p('U501',2),(146,110))
    p.power('GND',(146,118),up=False)
    p.part('R503',211,100)
    p.wire(p.p('U501',5),p.p('R503',1))
    # Standard low-side NMOS geometry; all package drain/source leads remain
    # explicit numbered pins, stacked at the corresponding electrical node.
    mosbody=(poly([(-10,0),(-4,0)]) + poly([(-4,-6),(-4,6)]) +
        poly([(-2,-6),(-2,-2)]) + poly([(-2,-1),(-2,1)]) +
        poly([(-2,2),(-2,6)]) + poly([(0,-12),(0,-5),(-2,-5)]) +
        poly([(-2,5),(0,5),(0,12)]) + poly([(0,-8),(6,-8),(6,8),(0,8)]) +
        poly([(4,-2),(8,-2)]) + poly([(6,-2),(4,2),(8,2),(6,-2)]))
    pins={4:(-12,0,'L',True,'G')}
    pins.update({i:(0,-14,'T',i==5,'D') for i in (5,6,7,8)})
    pins.update({i:(0,14,'B',i==1,'S') for i in (1,2,3)})
    p.ic('Q501',240,100,pins,w=16,h=24,kind='nmos',body=mosbody)
    _fields(p,(254,95),(265,101))
    p.wire(p.p('R503',2),p.p('Q501',4))
    p.part('D501',213,126,'v')
    _fields(p,(210,125,'right'),(210,127,'right'))
    p.part('R504',227,126,'v')
    p.wire((221,100),(221,116),(213,116),p.p('D501',1))
    p.wire((221,116),(227,116),p.p('R504',1))
    p.wire(p.p('D501',2),(213,140),(240,140),p.p('Q501',1))
    p.wire(p.p('R504',2),(227,140)); p.power('GND',(240,140),up=False)
    p.tp('TP501',(221,100))
    p.ic('J501',239,50,{1:(-9,-12,'L'),2:(-9,12,'L')},w=10,h=30)
    _fields(p,(239,32),(263,70))
    p.wire(p.p('J501',1),(212,38)); p.power('VM',(212,38))
    p.wire(p.p('J501',2),(240,62),p.p('Q501',5))
    p.part('D504',212,50,'v')
    p.wire(p.p('D504',1),(212,38)); p.wire(p.p('D504',2),(212,62),(230,62))
    p.wire((240,76),(250,76)); p.tp('TP502',(250,76))
    # External resistor is a drawing annotation, excluded from PCB and BOM.
    p.line((244,38),(287,38),(287,46))
    p.line((284,46),(290,46),(290,54),(284,54),(284,46))
    p.line((287,54),(287,62),(244,62))
    p.note(294,46,'EXTERNAL\nDUMP R',size=1.016)
    p.note(260,81,'Short / twisted resistor leads.',size=1.016)
    p.note(260,86,'D504 catches lead inductance.',size=1.016)
    p.note(256,115,'Q501: D = pads 5-8; S = pads 1-3; G = pad 4.',size=1.016)

    p.heading(20,83,'INDEPENDENT OVERVOLTAGE COMMAND')
    for ref,y in [('R506',100),('R507',115),('R508',130)]:
        p.part(ref,30,y,'v')
    p.supply('R506',1,'VM',dy=-5)
    p.wire(p.p('R506',2),p.p('R507',1)); p.wire(p.p('R507',2),p.p('R508',1))
    p.part('R509',30,156,'v'); p.part('C504',44,156,'v')
    p.wire(p.p('R508',2),p.p('R509',1))
    p.wire((30,142),(58,142)); p.wire((44,142),p.p('C504',1))
    p.wire(p.p('R509',2),(30,169),(44,169),p.p('C504',2)); p.power('GND',(30,169),up=False)
    compbody=(poly([(-14,-12),(-14,12),(14,0),(-14,-12)],fill='background') +
              poly([(0,-14),(0,-6)]) + poly([(0,6),(0,14)]) +
              poly([(16,8),(5,8),(5,4)]))
    p.ic('U502',76,147,{3:(-18,-5,'L'),4:(-18,5,'L'),1:(18,0,'R'),
          5:(18,8,'R'),6:(0,-16,'T'),2:(0,16,'B')},w=28,h=24,kind='opamp',body=compbody)
    _fields(p,(68,132),(79,180))
    p.wire(p.p('U502',5),(102,155),(102,172),(56,172),(56,152),p.p('U502',4))
    p.supply('U502',2,'GND',dy=3)
    p.part('C503',96,121,'v')
    p.wire(p.p('U502',6),(76,112),(96,112),p.p('C503',1)); p.power('3V3',(76,112))
    p.supply('C503',2,'GND',dy=5)
    p.part('R510',76,104,flip=True)
    p.wire(p.p('U502',1),(110,147),(110,80),(121,80),p.p('D503',2))
    p.wire((110,104),p.p('R510',1))
    p.wire(p.p('R510',2),(58,104),(58,142))
    p.label('BRAKE_OV_CMD',(110,92))
    p.note(128,156,'The positive-feedback resistor is wired back to IN+.',size=1.016)
    p.note(128,162,'Internal 1.242 V reference returns directly to IN−.',size=1.016)
    p.note(20,192,'U502 commands braking at approximately 45.9 V rising / 44.2 V falling; MCU PWM can also command the diode OR.')
    p.note(20,198,'Fit and rate the external resistor before regeneration. Both resistor wires carry bus voltage; pulse energy is application-specific.')
    p.note(20,204,'Place U501 decoupling / R503 / D501 at Q501. Return the driver ground to Q501 source with a short Kelvin connection.')
    return p
