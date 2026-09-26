"""Hand-routed power phases, Kelvin amplifiers and position-selection circuits."""
from redraw_engine import Page, PARTS, NETS, poly, rect


def _halfbridge(page, ref, x, y):
    pins = {'1': (-18, -16, 'L', True, 'GH'),
            '22': (-18, 16, 'L', True, 'GL'),
            '27': (0, -36, 'T', True, 'VIN'),
            '2': (20, 0, 'R', False, 'SH'),
            '21': (-16, 38, 'B', True, 'NC')}
    for number in range(3, 12):
        pins[str(number)] = (20, 0, 'R', number == 3, 'SW')
    for number in range(12, 21):
        pins[str(number)] = (0, 36, 'B', number == 12, 'SOURCE')
    for number,dx in zip((23, 24, 25, 26),(-13,-10,-7,-4)):
        pins[str(number)] = (dx, 38, 'B', False, 'NC')
    body = ''
    for cy in (-16, 16):
        body += poly([(-16, cy), (-6, cy)])
        body += poly([(-6, cy-7), (-6, cy+7)])
        for a, b in ((-8, -3), (-2, 2), (3, 8)):
            body += poly([(-2, cy+a), (-2, cy+b)])
        body += poly([(0, cy-16), (0, cy-8), (-2, cy-8)])
        body += poly([(-2, cy+8), (0, cy+8), (0, cy+16)])
        # Intrinsic diode: anode at source, cathode at drain.
        body += poly([(0, cy-8), (7, cy-8), (7, cy-2)])
        body += poly([(0, cy+8), (7, cy+8), (7, cy+2)])
        body += poly([(5, cy-2), (9, cy-2)])
        body += poly([(7, cy-1), (5, cy+2), (9, cy+2), (7, cy-1)])
    body += poly([(0,-34),(0,-32)]) + poly([(0,32),(0,34)])
    body += poly([(0,0),(18,0)])
    page.ic(ref,x,y,pins,w=32,h=68,kind='halfbridge',body=body)
    page.placements[-1]['ref_pos']=(x+9,y-37,'left')
    page.placements[-1]['value_pos']=(x+9,y-34,'left')


def _shunt(page, ref, x, y):
    body = poly([(0,-4),(0,-2)]) + poly([(-2,-2),(2,-2),(2,2),(-2,2),(-2,-2)])
    body += poly([(0,2),(0,4)])
    body += poly([(0,-2),(4,-2),(4,-3),(6,-3)])
    body += poly([(0,2),(4,2),(4,3),(6,3)])
    page.ic(ref,x,y,{'1':(0,-6,'T',True,'~'),
                    '4':(0,6,'B',True,'~'),
                    '2':(8,-3,'R',True,'SENSE+'),
                    '3':(8,3,'R',True,'SENSE-')},w=8,h=8,kind='passive',body=body)
    page.placements[-1]['ref_pos']=(x-5,y-3,'right')
    page.placements[-1]['value_pos']=(x-5,y+6,'right')


def build_inverter():
    p=Page('04_Inverter','Three-phase inverter / gate loops / Kelvin shunts')
    p.heading(12,18,'THREE IDENTICAL PHASE POWER LOOPS')
    p.note(12,23,'Gate resistors at MOSFET pins. The 10 nF capacitor returns above the shunt; the 1 uF capacitor returns to GND.')
    for idx,(phase,b) in enumerate((('U',14),('V',116),('W',218)),1):
        q=f'Q40{idx}'; sr=f'R4{idx}6'; x=b+46; y=85
        p.heading(b+4,30,f'PHASE {phase}')
        if idx>1:p.line((b-5,29),(b-5,196),width=.127)
        _halfbridge(p,q,x,y)
        # One VM supply rail feeds the bridge and both local bypass paths.
        p.wire((b+9,42),(b+74,42));p.power('VM',(x,42))
        p.wire((x,42),p.p(q,27))
        p.part(f'C4{idx}2',b+9,50,'v')
        p.wire((b+9,42),p.p(f'C4{idx}2',1))
        p.supply(f'C4{idx}2',2,'GND',dy=4)
        p.part(f'C4{idx}5',b+74,104,'v')
        p.wire((b+74,42),p.p(f'C4{idx}5',1))
        p.wire(p.p(f'C4{idx}5',2),(b+74,136),(x,136))
        for rr,dy,gate in ((1,-16,'1'),(2,16,'22')):
            r=f'R4{idx}{rr}';p.part(r,b+15,y+dy)
            if rr==2:
                p.placements[-1]['ref_pos']=(b+15,y+20)
                p.placements[-1]['value_pos']=(b+15,y+23)
            p.wire(p.p(r,2),p.p(q,gate));p.out(r,1,f'{"GHS" if rr==1 else "GLS"}{idx}',dx=-7)
        # Gate-to-source defaults are visibly connected to their respective source.
        p.part(f'R4{idx}3',b+24,77,'v')
        p.wire((b+24,69),p.p(f'R4{idx}3',1))
        p.wire(p.p(f'R4{idx}3',2),(b+24,85),p.p(q,3))
        p.part(f'R4{idx}4',b+24,113,'v')
        p.wire((b+24,101),p.p(f'R4{idx}4',1))
        p.wire(p.p(f'R4{idx}4',2),(b+24,136),(x,136))
        # Bootstrap reservoir returns to the phase switching node.
        p.part(f'C4{idx}1',b+9,94,'v')
        p.placements[-1]['value_pos']=(b+7,94,'right')
        p.out(f'C4{idx}1',1,f'BOOT{idx}',dx=0,dy=-5)
        p.wire(p.p(f'C4{idx}1',2),(b+19,98),(b+19,85),(b+24,85))
        p.wire(p.p(q,3),(b+66,85),(b+66,106))
        p.port(f'OUT{idx}',(b+66,85),side='R')
        # Optional series RC snubber is drawn as the actual shunt branch.
        p.part(f'R4{idx}5',b+66,110,'v')
        p.part(f'C4{idx}3',b+66,127,'v')
        p.wire(p.p(f'R4{idx}5',2),p.p(f'C4{idx}3',1))
        p.supply(f'C4{idx}3',2,'GND',dy=7)
        _shunt(p,sr,x,147)
        p.wire(p.p(q,12),(x,136),p.p(sr,1));p.supply(sr,4,'GND',dy=5)
        for pin,suffix in ((2,'P'),(3,'N')):
            p.out(sr,pin,f'SHUNT_{phase}_SENSE_{suffix}',dx=8)
        p.label(f'SHUNT_{phase}_FORCE_P',(x,136))
        p.note(b+3,169,'Package pins: VIN 27; GH 1; GL 22.\nSW/SH: 2, 3-11; source: 12-20.\nNC: 21, 23-26. Stacked pins are retained.',1.016)
        p.note(b+3,185,'Kelvin pads 2/3 go only to the amplifier.\nForce-current copper uses pads 1/4.\nSnubber R/C are DNP tuning positions.',1.016)
    # The motor connector belongs next to the three output interfaces.
    p.ic('J401',175,207,{'1':(-15,-3,'L'),'2':(-15,0,'L'),'3':(-15,3,'L')},w=22,h=10)
    for i in range(1,4):p.out('J401',i,f'OUT{i}',dx=-8)
    p.note(14,202,'Layout order: VM ceramic -> high-side FET -> low-side FET -> local source return.\nKeep the bootstrap and gate loops short; do not route motor current in Kelvin sense traces.',1.016)
    return p


def build_sensing():
    p=Page('05_Current_Temperature','Three Kelvin current amplifiers / phase temperature')
    p.heading(12,18,'MATCHED CURRENT CHANNELS AND LOCAL MOSFET TEMPERATURE')
    p.note(12,24,'VOUT = VREF/2 + 28 x (SENSE+ - SENSE-). At 0.5 mOhm: 14 mV/A. Bias resistors establish the bipolar zero-current point.')
    for idx,(phase,ntc,b,unit,plus,minus,out) in enumerate([
        ('U','A',12,4,14,16,15),('V','B',115,5,20,22,19),('W','C',218,6,23,25,24)],1):
        if idx>1:p.line((b-6,31),(b-6,206),width=.127)
        p.heading(b+2,33,f'PHASE {phase} / OPAMP{idx}')
        x=b+60;y=82
        p.ic('U301',x,y,{str(plus):(-14,5,'L',True,'+'),str(minus):(-14,-5,'L',True,'-'),str(out):(14,0,'R',True,'OUT')},w=24,h=24,kind='opamp',unit=unit)
        p.placements[-1]['value_pos']=(x,y+18)
        p.part(f'R4{idx}7',b+25,y+5);p.part(f'R4{idx}8',b+25,y-5)
        p.out(f'R4{idx}7',1,f'SHUNT_{phase}_SENSE_P',dx=-6)
        p.out(f'R4{idx}8',1,f'SHUNT_{phase}_SENSE_N',dx=-6)
        p.wire(p.p(f'R4{idx}7',2),p.p('U301',plus,unit))
        p.wire(p.p(f'R4{idx}8',2),p.p('U301',minus,unit))
        # The two 56 k resistors make the equivalent 28 k / VREF/2 bias source.
        p.part(f'R4{idx}0',b+19,105)
        p.wire(p.p(f'R4{idx}0',1),(b+10,105));p.power('VREF+',(b+10,105))
        p.wire(p.p(f'R4{idx}0',2),(b+37,105),(b+37,y+5))
        p.part(f'R44{idx}',b+37,114,'v')
        p.wire((b+37,105),p.p(f'R44{idx}',1));p.supply(f'R44{idx}',2,'GND',dy=3)
        # Negative feedback and its optional compensation capacitor are explicit loops.
        p.part(f'R4{idx}9',b+61,52,flip=True);p.part(f'C4{idx}4',b+61,42,flip=True)
        p.wire((b+43,y-5),(b+43,42),p.p(f'C4{idx}4',2))
        p.wire((b+43,52),p.p(f'R4{idx}9',2))
        p.wire(p.p('U301',out,unit),(b+82,y),(b+82,42),p.p(f'C4{idx}4',1))
        p.wire((b+82,52),p.p(f'R4{idx}9',1))
        p.tp(f'TP{1017+idx}',(b+87,y))
        p.port(f'OPO_{phase}1',(b+88,y),side='R');p.wire((b+82,y),(b+88,y))
        # Preserve useful names on the actual wired amplifier nodes.
        p.label(f'OPP_{phase}1',(b+31,y+5));p.label(f'OPN_{phase}1',(b+33,y-5))
        p.note(b+2,122,f'COMP{(1,2,4)[idx-1]} monitors the + input.\nConfigure DAC3 threshold and TIM1 break\nbefore any gate PWM is enabled.',1.016)
        p.heading(b+2,140,f'NTC {ntc} - place beside phase {phase}')
        p.part(f'R70{idx}',b+24,158,'v');p.supply(f'R70{idx}',1,'3V3',dy=-5)
        p.part(f'TH70{idx}',b+24,186,'v')
        p.wire(p.p(f'R70{idx}',2),p.p(f'TH70{idx}',1));p.supply(f'TH70{idx}',2,'GND',dy=4)
        p.part(f'R71{idx}',b+49,173)
        p.wire((b+24,173),p.p(f'R71{idx}',1))
        p.part(f'C71{idx}',b+68,186,'v')
        p.wire(p.p(f'R71{idx}',2),(b+68,173),p.p(f'C71{idx}',1));p.supply(f'C71{idx}',2,'GND',dy=4)
        p.tp(f'TP70{idx}',(b+68,173));p.wire((b+68,173),(b+85,173));p.port(f'NTC_PHASE_{ntc}',(b+85,173),side='R')
        p.label(f'NTC_{ntc}_RAW',(b+24,173))
    p.note(12,211,'NTC faults: open -> ADC near 3V3; short -> ADC near GND. Use the hottest valid channel and calibrate protection against measured temperature.',1.016)
    return p


def build_feedback():
    p=Page('08_Feedback_Selection','External ABI / Hall protection and position-source selection')
    p.heading(12,18,'ONBOARD OR EXTERNAL POSITION FEEDBACK -> TIM4')
    p.note(12,24,'External signals must stay within 0-3.3 V, including when board power is off. DNP pull-ups are for open-drain Hall outputs.')
    # The external connector is grouped with its rail feed and ESD network.
    p.ic('J601',38,100,{'1':(0,-21,'T'),'2':(0,21,'B'),'3':(14,-10,'R'),'4':(14,0,'R'),'5':(14,10,'R'),'6':(-14,12,'L')},w=18,h=34)
    p.placements[-1]['ref_pos']=(25,80,'left')
    p.placements[-1]['value_pos']=(15,123,'left')
    p.part('R604',38,56,'v');p.supply('R604',1,'3V3',dy=-7);p.wire(p.p('R604',2),p.p('J601',1));p.label('3V3_EXT_FB',(38,69));p.supply('J601',2,'GND',dy=9)
    p.ic('D601',110,47,{'1':(-10,15,'B',True,'IO1'),'2':(0,15,'B',True,'IO2'),'4':(10,15,'B',True,'IO3'),'3':(-16,0,'L',True,'GND'),'5':(16,0,'R',True,'VCC')},w=24,h=22)
    p.placements[-1]['value_pos']=(110,42.5)
    p.wire(p.p('D601',3),(90,47),(90,55));p.power('GND',(90,55),up=False)
    p.part('C604',148,55,'v');p.wire(p.p('D601',5),(148,47),p.p('C604',1));p.supply('C604',2,'GND',dy=4);p.label('FB_ESD_RAIL',(129,47))
    p.note(88,31,'ESD rail is isolated from 3V3',1.016)
    mpins={};body=rect(-16,-40,16,40)
    for channel,(on,ext,out,dy) in enumerate(((2,3,4,-27),(5,6,7,3),(11,10,9,33))):
        mpins[str(on)]=(-20,dy-3,'L',True,f'S{channel+1}A')
        mpins[str(ext)]=(-20,dy+3,'L',True,f'S{channel+1}B')
        mpins[str(out)]=(20,dy,'R',True,f'D{channel+1}')
        body+=poly([(-16,dy-3),(-9,dy-3)])+poly([(-16,dy+3),(-9,dy+3)])+poly([(-8,dy-3),(3,dy),(16,dy)])
    p.ic('U602',225,100,mpins,w=32,h=80,body=body)
    for idx,(channel,cp,esdp,y,tap) in enumerate((('A',3,1,76,67),('B',4,2,106,75),('I',5,4,136,83))):
        p.wire(p.p('J601',cp),(tap,p.p('J601',cp)[1]),(tap,y),(161,y))
        p.wire(p.p('D601',esdp),(p.p('D601',esdp)[0],y))
        r=f'R{605+idx}';p.part(r,165,y);p.wire(p.p(r,2),(205,y))
        pull=f'R{608+idx}';p.part(pull,184,y-15,'v');p.supply(pull,1,'3V3',dy=-5);p.wire(p.p(pull,2),(184,y))
        p.port(f'MUX_ON_{channel}',(193,y-6),side='L');p.wire((193,y-6),(205,y-6))
        outpin=(4,7,9)[idx];outnet=('FEEDBACK_A_H1','FEEDBACK_B_H2','FEEDBACK_I_H3')[idx]
        p.wire(p.p('U602',outpin),(278,y-3));p.port(outnet,(278,y-3),side='R')
        p.label(f'MUX_EXT_{channel}',(174,y))
        if idx<2:p.tp(f'TP{1015+idx}',(260,y-3))
    p.part('R307',260,150,'v');p.wire((260,133),p.p('R307',1));p.supply('R307',2,'GND',dy=5)
    p.note(274,146,'PB8 / BOOT0:\n10k default low.\nNo test stub.',1.016)
    # Fourth switch channel isolates the live bus divider from unpowered MCU pins.
    p.heading(15,161,'CHANNEL 4 - BUS ADC ISOLATION')
    c4body=rect(-10,-8,10,8)+poly([(-10,-4),(-5,-4)])+poly([(-10,4),(-5,4)])+poly([(-4,-4),(0,0),(10,0)])
    p.ic('U602',61,186,{'13':(-14,-4,'L',True,'S4A'),'14':(-14,4,'L',True,'S4B'),'12':(14,0,'R',True,'D4')},w=20,h=16,unit=2,body=c4body)
    p.wire(p.p('U602',13,2),(34,182),(34,190),p.p('U602',14,2));p.wire((25,186),(34,186));p.port('VBUS_MUX_IN',(25,186),side='L')
    p.out('U602',12,'VBUS_SENSE',dx=11,unit=2)
    p.note(15,204,'Both select positions pass VM.\nEnable mux; wait 2 ms before reading VM.',1.016)
    # Shared power and controls remain explicitly part of the same physical U602.
    p.ic('U602',235,170,{'1':(-20,-7,'L',True,'SEL'),'15':(-20,7,'L',True,'EN_N'),'16':(0,-20,'T',True,'VDD'),'8':(0,20,'B',True,'GND')},w=32,h=32,unit=3)
    p.placements[-1]['ref_pos']=(251,151,'left')
    p.placements[-1]['value_pos']=(251,191,'left')
    p.supply('U602',16,'3V3',dy=-5,unit=3);p.supply('U602',8,'GND',dy=5,unit=3)
    p.part('C603',267,173,'v');p.supply('C603',1,'3V3',dy=-5);p.supply('C603',2,'GND',dy=5)
    p.wire((160,163),p.p('U602',1,3));p.port('FEEDBACK_SELECT',(160,163),side='L')
    p.part('R306',172,175,'v');p.wire((172,163),p.p('R306',1));p.supply('R306',2,'GND',dy=5)
    p.part('R305',190,151,'v');p.supply('R305',1,'3V3',dy=-5);p.wire(p.p('R305',2),(190,177),p.p('U602',15,3))
    p.port('FEEDBACK_ENABLE_N',(163,193),side='L');p.wire((163,193),(203,193),(203,177))
    p.note(145,205,'Reset: disabled; onboard selected.\nDisable PWM before disabling this mux.',1.016)
    return p
