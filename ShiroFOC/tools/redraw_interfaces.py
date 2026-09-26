"""Connected interface pages for the A0-preserving schematic redraw.

Each route is authored as a circuit, rather than inferred from pin labels.
All physical pin identifiers and component metadata come from redraw_engine.
"""
from redraw_engine import Page, box


def _name(page, net, point):
    page.label(net, point)


def build_can():
    p = Page('08_CAN', 'CAN / CAN-FD interface', 'A4')
    p.heading(12, 17, 'CAN: controller -> transceiver -> protected daisy-chain bus')
    p.ic('U801', 82, 71, {
        '8': (-18,-16,'L'), '1':(-18,-6,'L'), '4':(-18,4,'L'),
        '7':(18,-8,'R'), '6':(18,16,'R'),
        '3':(-4,-24,'T'), '5':(4,-24,'T'), '2':(0,24,'B'),
    }, w=28,h=40)
    for pin,net,y in [('8','CAN_STB',55),('1','FDCAN1_TX',65),('4','FDCAN1_RX',75)]:
        p.wire((20,y),p.p('U801',pin));p.port(net,(20,y))
    p.tp('TP1022',(40,55));p.tp('TP1013',(48,65));p.tp('TP1014',(56,75))
    p.part('R801',44,39,'v');p.wire(p.p('R801','2'),(44,55))
    p.part('R805',56,43,'v');p.wire(p.p('R805','2'),(56,65))
    p.wire(p.p('R801','1'),(44,28),(112,28))
    p.wire(p.p('R805','1'),(56,28))
    p.wire(p.p('U801','3'),(78,28));p.wire(p.p('U801','5'),(86,28))
    p.power('3V3',(68,28));p.wire((56,28),(68,28),(78,28))
    for ref,x in [('C801',100),('C802',112)]:
        p.part(ref,x,36,'v');p.wire(p.p(ref,'1'),(x,28));p.supply(ref,'2','GND',dy=4)
    p.supply('U801','2','GND',dy=5)
    for ref,pin,net,y in [('R803','7','CANH_INT',63),('R804','6','CANL_INT',87)]:
        p.part(ref,120,y);p.wire(p.p('U801',pin),p.p(ref,'1'))
        p.label(net,(102,y));p.wire(p.p(ref,'2'),(184 if y==63 else 190,y))
    p.label('CANH_BUS',(128,63));p.label('CANL_BUS',(128,87))
    # Optional termination visibly spans the two bus wires.
    p.part('R802',172,69,'v');p.part('JP801',172,81,'v')
    p.wire((172,63),p.p('R802','1'));p.wire(p.p('R802','2'),p.p('JP801','1'))
    p.wire(p.p('JP801','2'),(172,87));p.label('CAN_TERM_MID',(172,75))
    p.note(150,49,'End-node option: fit R802\nand close JP801. Both DNP.',1.016)
    # Protection taps; crossings without a dot are not electrical junctions.
    p.ic('D801',149,110,{'1':(-4,-8,'T'),'2':(4,-8,'T'),'3':(0,8,'B')},w=16,h=8)
    p.wire((145,63),p.p('D801','1'));p.wire((153,87),p.p('D801','2'))
    p.supply('D801','3','GND',dy=4)
    for ref,y in [('J801',72),('J802',116)]:
        p.ic(ref,210,y,{'3':(-11,-9,'L'),'2':(-11,-3,'L'),'1':(-11,3,'L'),'4':(-11,9,'L')},w=14,h=24)
    p.wire((184,63),(184,107),p.p('J802','3'))
    p.wire((184,63),p.p('J801','3'))
    p.wire((190,87),(190,69),p.p('J801','2'))
    p.wire((190,87),(190,113),p.p('J802','2'))
    for ref in ['J801','J802']:
        a=p.p(ref,'1');p.wire(a,(194,a[1]),(194,a[1]+4));p.power('GND',(194,a[1]+4),up=False)
    p.wire(p.p('J801','4'),(196,81),(196,125),p.p('J802','4'))
    p.label('CAN_SHIELD',(196,95))
    p.note(12,111,'Reset state: STB high -> standby; TX high -> recessive.\nConfigure FDCAN before taking STB low.\nPlace D801 next to the connectors; route CANH/CANL together.',1.143)
    p.note(12,135,'Both headers: 1 GND | 2 CANL | 3 CANH | 4 shield/drain. Pin 4 carries no supply.',1.143)
    _position_ic_fields(p)
    return p


def build_usb():
    p = Page('09_USB_Service','USB-C service / UART bridge','A3')
    p.heading(12,17,'USB service: connector, protection and bridge in one circuit')
    # Repeated USB connector pins remain individually visible and physically numbered.
    p.ic('J201',45,75,{
        'A4':(17,-26,'R'),'A9':(17,-24,'R'),'B4':(17,-22,'R'),'B9':(17,-20,'R'),
        'A6':(17,-10,'R'),'B6':(17,-8,'R'),'A7':(17,0,'R'),'B7':(17,2,'R'),
        'A5':(17,12,'R'),'B5':(17,22,'R'),
        'A8':(-17,-4,'L'),'B8':(-17,4,'L'),
        'A1':(-9,30,'B'),'A12':(-3,30,'B'),'B1':(3,30,'B'),'B12':(9,30,'B'),
        'S1':(15,30,'B'),
    },w=26,h=52)
    for pin in ['A4','A9','B4','B9']:
        a=p.p('J201',pin);p.wire(a,(70,a[1]))
    p.wire((70,49),(70,55));p.power('5V_USB_RAW',(70,49))
    p.part('R205',94,49);p.wire((70,49),p.p('R205','1'));p.wire(p.p('R205','2'),(145,49),(155,49))
    p.part('C208',160,62,'v');p.wire((155,49),(160,49),p.p('C208','1'));p.supply('C208','2','GND',dy=4)
    p.tp('TP202',(132,49));p.tp('TP1004',(145,49));p.port('5V_USB',(155,49),side='R')
    p.note(80,30,'VBUS to control-power mux\nUSB-only source must allow >=500 mA.',1.143)
    # Merge each reversible connector pair, then route as a differential pair.
    for pin in ['A6','B6']:
        a=p.p('J201',pin);p.wire(a,(68,a[1]))
    p.wire((68,65),(68,67));p.wire((68,66),(109,66));p.label('USB_DP_CONN',(75,66))
    for pin in ['A7','B7']:
        a=p.p('J201',pin);p.wire(a,(72,a[1]))
    p.wire((72,75),(72,77));p.wire((72,76),(109,76));p.label('USB_DM_CONN',(77,76))
    p.ic('U202',122,71,{'3':(-13,-5,'L'),'1':(-13,5,'L'),'4':(13,-5,'R'),'6':(13,5,'R'),'5':(0,-16,'T'),'2':(0,16,'B')},w=18,h=24)
    p.wire((70,55),p.p('U202','5'));p.supply('U202','2','GND',dy=4)
    for ref,pin,y in [('R203','A5',87),('R204','B5',97)]:
        p.part(ref,85,y);p.wire(p.p('J201',pin),p.p(ref,'1'))
        a=p.p(ref,'2');p.wire(a,(97,y));p.power('GND',(97,y),up=False)
        p.label('USB_CC1' if pin=='A5' else 'USB_CC2',(66,y))
    groundpts=[p.p('J201',pin) for pin in ['A1','A12','B1','B12']]
    for a in groundpts:p.wire(a,(a[0],111))
    p.wire((36,111),(54,111));p.power('GND',(45,111),up=False)
    p.part('C207',60,120,'v');p.wire(p.p('J201','S1'),p.p('C207','1'));p.supply('C207','2','GND',dy=4)
    p.label('USB_SHIELD',(60,110));p.note(72,114,'Shield capacitor C207 is DNP.\nPlace USBLC6 at the connector.',1.143)
    # CP2102N uses the common 3V3 rail in its documented regulator-bypass mode.
    cppins={
        '8':(-21,-22,'L'),'4':(-21,-12,'L'),'5':(-21,-4,'L'),'9':(-21,14,'L'),
        '18':(21,-12,'R'),'17':(21,-4,'R'),
        '7':(-5,-34,'T'),'6':(5,-34,'T'),
        '3':(-4,34,'B'),'12':(0,34,'B'),'21':(4,34,'B'),
        '1':(-21,22,'L'),'2':(-21,26,'L'),
    }
    for pin,dy in zip(['10','11','13','14','15','16','19','20'],[6,9,12,15,18,21,24,27]):cppins[pin]=(21,dy,'R')
    p.ic('U901',225,92,cppins,w=34,h=60)
    for ref,x in [('C901',194),('C902',206),('C903',242),('C904',254)]:
        p.part(ref,x,42,'v');p.wire(p.p(ref,'1'),(x,34));p.supply(ref,'2','GND',dy=4)
    p.wire((194,34),(254,34));p.power('3V3',(225,34))
    p.wire(p.p('U901','7'),(220,34));p.wire(p.p('U901','6'),(230,34))
    p.note(192,23,'VREGIN and VDD: both powered from 3V3',1.143)
    p.wire(p.p('U202','4'),(150,66),(150,80),p.p('U901','4'))
    p.wire(p.p('U202','6'),(154,76),(154,88),p.p('U901','5'))
    p.label('USB_DP',(158,80));p.label('USB_DM',(158,88))
    p.part('R904',172,44,'v');p.supply('R904','1','5V_USB_RAW',dy=-6)
    p.part('R905',172,60,'v');p.wire(p.p('R904','2'),p.p('R905','1'));p.supply('R905','2','GND',dy=4)
    p.wire((172,52),(185,52),(185,70),p.p('U901','8'));p.label('CP2102_VBUS_SENSE',(185,70))
    p.part('R901',185,102,'v');p.supply('R901','1','3V3',dy=-4)
    p.wire(p.p('R901','2'),(185,106),p.p('U901','9'));p.label('CP2102_RST_N',(187,106))
    p.part('R902',265,80);p.wire(p.p('U901','18'),p.p('R902','1'));p.wire(p.p('R902','2'),(290,80));p.port('USB_UART_RX',(290,80),side='R');p.tp('TP902',(280,80))
    p.part('R903',265,88,flip=True);p.wire(p.p('U901','17'),p.p('R903','2'));p.wire(p.p('R903','1'),(290,88));p.port('USB_UART_TX',(290,88),side='R');p.tp('TP901',(280,88))
    p.label('UART_BRIDGE_TX',(247,80));p.label('UART_BRIDGE_RX',(247,88))
    for pin in ['3','12','21']:
        a=p.p('U901',pin);p.wire(a,(a[0],132))
    p.wire((221,132),(235,132));p.power('GND',(225,132),up=False);p.tp('TP903',(235,132))
    p.note(190,144,'UART labels are named from the MCU point of view.\nTXD from U901 drives MCU RX. RTS/CTS are unused.\nBOOT0 and reset remain manual controls on the MCU sheet.',1.143)
    p.note(12,155,'LAYOUT: route the USB pair continuously from J201 through U202 to U901; avoid stubs.\nC901/C902 belong at VREGIN; C903/C904 belong at VDD. Both pin groups use the same 3V3 rail.',1.143)
    _position_ic_fields(p)
    return p


def build_spi():
    p = Page('06_SPI_Sensors','Shared SPI bus / position encoder / IMU','A3')
    p.heading(12,17,'SPI3: one shared bus, separate chip selects, local return damping')
    p.part('R313',36,30);p.wire((30,30),p.p('R313','1'));p.port('SPI3_SCK_MCU',(30,30))
    p.part('R314',36,42);p.wire((30,42),p.p('R314','1'));p.port('SPI3_MOSI_MCU',(30,42))
    p.wire(p.p('R313','2'),(58,30),(58,158));p.tp('TP1010',(48,30));p.label('SPI3_SCK',(48,30))
    p.wire(p.p('R314','2'),(72,42),(72,166));p.tp('TP1012',(48,42));p.label('SPI3_MOSI',(48,42))
    p.wire((30,54),(86,54),(86,174));p.port('SPI3_MISO',(30,54));p.tp('TP1011',(48,54))
    p.ic('U601',138,76,{
        '2':(-21,-10,'L'),'4':(-21,-2,'L'),'3':(-21,6,'L'),
        '1':(21,-16,'R'),'7':(21,-4,'R'),'6':(21,4,'R'),'14':(21,12,'R'),
        '11':(-4,-28,'T'),'12':(4,-28,'T'),
        '5':(-4,28,'B'),'13':(4,28,'B'),
        '8':(8,28,'B'),'9':(12,28,'B'),'10':(16,28,'B'),
    },w=34,h=48)
    p.ic('U701',138,168,{
        '13':(-21,-10,'L'),'14':(-21,-2,'L'),'1':(-21,6,'L'),
        '12':(21,-14,'R'),'4':(21,-2,'R'),'9':(21,6,'R'),
        '5':(-4,-22,'T'),'8':(4,-22,'T'),'6':(-4,22,'B'),'7':(4,22,'B'),
        '2':(6,22,'B'),'3':(9,22,'B'),'10':(12,22,'B'),'11':(15,22,'B'),
    },w=34,h=36)
    for ref,pin,y in [('U601','2',66),('U701','13',158)]:p.wire((58,y),p.p(ref,pin))
    for ref,pin,y in [('U601','4',74),('U701','14',166)]:p.wire((72,y),p.p(ref,pin))
    for r,u,y,raw in [('R611','U601',82,'AS5047_MISO_RAW'),('R714','U701',174,'BMI323_MISO_RAW')]:
        p.part(r,103,y,flip=True);p.wire(p.p(r,'1'),p.p(u,'3' if u=='U601' else '1'))
        p.wire((86,y),p.p(r,'2'));p.label(raw,(107,y))
    # Local bypass groups are attached to the same rail as the corresponding IC pins.
    for u,caps,cy,rail,pins,ground_y in [
        ('U601',['C601','C602'],38,28,['11','12'],110),
        ('U701',['C701','C702'],133,123,['5','8'],196),
    ]:
        for c,x in zip(caps,[122,154]):
            p.part(c,x,cy,'v');p.wire(p.p(c,'1'),(x,rail));p.supply(c,'2','GND',dy=4)
        p.wire((122,rail),(154,rail));p.power('3V3',(138,rail))
        for pin in pins:
            a=p.p(u,pin);p.wire(a,(a[0],rail))
        for pin in (['5','13'] if u=='U601' else ['6','7']):
            a=p.p(u,pin);p.wire(a,(a[0],ground_y))
        p.wire((134,ground_y),(142,ground_y));p.power('GND',(138,ground_y),up=False)
    for u,pin,r,y,ry,net in [('U601','1','R309',60,47,'AS5047P_CS_N'),('U701','12','R308',154,141,'IMU_CS_N')]:
        p.part(r,176,ry,'v');p.supply(r,'1','3V3',dy=-4)
        p.wire(p.p(r,'2'),(176,y));p.wire(p.p(u,pin),(205,y));p.port(net,(205,y),side='R')
    for r,pin,y,src,dst in [('R601','7',72,'ENC_ON_A','MUX_ON_A'),('R602','6',80,'ENC_ON_B','MUX_ON_B'),('R603','14',88,'ENC_ON_I','MUX_ON_I')]:
        p.part(r,176,y);p.wire(p.p('U601',pin),p.p(r,'1'));p.wire(p.p(r,'2'),(205,y));p.port(dst,(205,y),side='R');p.label(src,(160,y))
    for pin,net,y in [('4','IMU_INT1',166),('9','IMU_INT2',174)]:p.wire(p.p('U701',pin),(205,y));p.port(net,(205,y),side='R')
    p.note(228,47,'ONBOARD POSITION\nABI outputs feed the selector sheet.\nTEST is tied low for normal operation.\nAlign the sensor with the shaft magnet.',1.143)
    p.note(228,140,'IMU\nMark X/Y axes on the PCB.\nKeep power-stage heat and switching\nloops away from the sensor.',1.143)
    p.note(12,191,'Place R313/R314 at the MCU. Place R611/R714 at their sensor MISO pins.\nChip-select pull-ups keep both peripherals deselected during reset.\nSPI wire crossings without a junction dot are separate nets.',1.143)
    _position_ic_fields(p)
    return p


def _position_ic_fields(page):
    for c in page.placements:
        if c['ref']=='JP801':c['value_pos']=(170,82,'right')
        if c.get('orient') or c.get('tp'):
            continue
        x,y,w,h=c['x'],c['y'],c['w'],c['h']
        c['ref_pos']=(x-w/2,y-h/2-5,'left')
        c['value_pos']=(x-w/2,y-h/2-3,'left')
        if c['ref']=='U801':
            c['ref_pos']=(64,46,'left')
            c['value_pos']=(64,48,'left')
        if c['ref']=='U202':
            c['ref_pos']=(110,51,'right')
            c['value_pos']=(110,53,'right')
        if c['ref'] in ('U601','U701'):
            c['ref_pos']=(x-w/2-4,y-h/2-5,'right')
            c['value_pos']=(x-w/2-4,y-h/2-3,'right')
        if c['ref']=='U901':
            c['ref_pos']=(246,57,'left')
            c['value_pos']=(246,59,'left')
        if c['ref']=='D801':
            c['ref_pos']=(138,106,'right')
            c['value_pos']=(138,108,'right')
