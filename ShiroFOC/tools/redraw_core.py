"""Controller, its local support circuits, and STSPIN gate power."""
from redraw_engine import *

def build_core():
 s=Page('03_Controller','Controller, clock, reset and debug','A3')
 s.heading(12,12,'CONTROLLER / CLOCK / DEBUG')
 # Digital functions grouped by interface; analog amplifiers are units 4..6.
 left={48:-34,47:-32,28:-30,45:-24,46:-22,54:-16,56:-14,55:-12,51:-10,21:-8,57:0,58:2,59:4,53:6,4:8,17:14,18:16,60:22,3:28,5:36,44:44}
 right={6:-34,7:-30,9:-20,10:-18,12:-16,13:-14,8:0,11:10,49:24,50:28}
 pins={str(p):(-19,y,'L') for p,y in left.items()}|{str(p):(19,y,'R') for p,y in right.items()}
 s.ic('U301',110,68,pins,w=30,h=96,unit=1)
 s.placements[-1]['ref_pos']=(110,17);s.placements[-1]['value_pos']=(110,119)
 # Ports at functional boundaries, not labels on every support part.
 for pn,y in left.items():
  net=NETS[('U301',str(pn))];a=s.p('U301',pn);end=(68,a[1]);s.wire(a,end)
  if pn in (3,5,44):
   ref={3:'TP1023',5:'TP1021',44:'TP1024'}[pn];s.tp(ref,end);s.label(net,(70,a[1]))
  else:s.port(net,end,side='L')
 for pn in (9,10,12,13):s.out('U301',pn,NETS[('U301',str(pn))],dx=12)
 for x,y,t in [(18,31,'CAN'),(18,43,'UART'),(18,51,'SPI3'),(18,67,'FEEDBACK'),(18,81,'IMU IRQ'),(18,89,'BRAKE')]:s.note(x,y,t)
 # Local crystal with its two case grounds and actual load branches.
 yp={'1':(-7,0,'L',True,'~'), '3':(7,0,'R',True,'~'),'2':(-2,8,'B',True,'~'),'4':(2,8,'B',True,'~')}
 body=poly([(-3,-3),(-3,3),(3,3),(3,-3),(-3,-3)])+poly([(-5,-4),(-5,4)])+poly([(5,-4),(5,4)])+poly([(-7,0),(-5,0)])+poly([(5,0),(7,0)])
 s.ic('Y301',222,34,yp,w=10,h=8,body=body)
 s.placements[-1]['value_pos']=(238,31,'left')
 s.wire(s.p('U301',6),s.p('Y301',1))
 s.wire(s.p('U301',7),(207,38),(207,22),(229,22),s.p('Y301',3))
 s.part('C308',193,48,orient='v');s.wire(s.p('Y301',1),(193,34),s.p('C308',1));s.supply('C308',2,'GND',dy=4)
 s.part('C309',252,48,orient='v');s.wire(s.p('Y301',3),(252,34),s.p('C309',1));s.supply('C309',2,'GND',dy=4)
 for pn in (2,4):s.supply('Y301',pn,'GND',dy=3)
 s.note(270,29,'24 MHz / 7 pF load\n10 pF C0G starting caps\nCase pads 2 and 4 = GND')
 # Reset: local pull-up, bypass and switches. The debug header uses a local NRST label.
 a=s.p('U301',8);s.wire(a,(283,68));s.label('NRST',(136,68))
 s.part('R303',283,57,orient='v');s.wire(s.p('R303',2),(283,68));s.supply('R303',1,'3V3')
 s.part('C310',283,82,orient='v');s.wire((283,68),s.p('C310',1));s.supply('C310',2,'GND',dy=4)
 for ref,x in [('SW301',181),('SW1002',214)]:
  s.part(ref,x,78);s.wire((153,68),(x-4,68),s.p(ref,1));s.supply(ref,2,'GND',dy=8)
 s.tp('TP303',(144,68));s.tp('TP1007',(204,68))
 # LED current path: 3V3 through R304 and LED to MCU sink.
 s.part('D301',230,99);s.part('R304',250,99,flip=True)
 s.wire(s.p('U301',11),(134,78),(134,99),s.p('D301',1));s.wire(s.p('D301',2),s.p('R304',2));s.supply('R304',1,'3V3')
 # SWD is grouped locally. Ports are pulled from GPIO wires; no testpoint list.
 cp={str(i):(-9,(i-1)*2-9,'L') for i in range(1,11)}
 s.ic('J1001',187,118,cp,w=10,h=24)
 s.wire(s.p('U301',49),(163,92),(163,111),s.p('J1001',2));s.tp('TP1008',(151,92))
 s.wire(s.p('U301',50),(157,96),(157,115),s.p('J1001',4));s.wire((157,108),(139,108));s.tp('TP1009',(139,108))
 for pn in (3,5,9):
  a=s.p('J1001',pn);s.wire(a,(174,a[1]),(174,137))
 s.power('GND',(174,137),False)
 s.wire(s.p('J1001',1),(174,109),(174,103));s.power('3V3',(174,103))
 a=s.p('J1001',10);s.wire(a,(162,a[1]));s.label('NRST',(162,a[1]))
 s.note(200,115,'SWD VTREF is sense-only.\nNo SWO: PB3 is SPI3 SCK.\nPins 6/7/8 are intentionally NC.')
 # Boot button is adjacent to service interface and uses an explicit boundary label.
 s.part('R1001',237,135);s.part('SW1001',266,135)
 s.wire(s.p('R1001',1),(210,135));s.port('FEEDBACK_I_H3',(210,135))
 s.wire(s.p('R1001',2),s.p('SW1001',1));s.supply('SW1001',2,'3V3')
 s.note(210,143,'BOOT0 shares PB8; feedback mux is off in reset.\nKeep R1001/button branch short. No PB8 test pad.')
 # Core supply unit and decoupling. Power pins explicit, no hidden common pins.
 s.heading(12,148,'MCU / ANALOG SUPPLIES')
 ps={'1':(-16,-6,'L'),'2':(-16,0,'L'),'64':(-16,6,'L'),'27':(16,-5,'R'),'26':(16,5,'R'),'65':(0,15,'B')}
 s.ic('U301',94,180,ps,w=24,h=22,unit=2)
 s.placements[-1]['ref_pos']=(94,166);s.placements[-1]['value_pos']=(94,207)
 for pn in (1,2,64):a=s.p('U301',pn,2);s.wire(a,(73,a[1]),(73,164))
 s.power('3V3',(73,164));s.supply('U301',65,'GND',dy=6,unit=2)
 for ref,x in [('C301',21),('C302',38),('C307',55)]:
  s.part(ref,x,179,orient='v');s.wire((73,164),(x,164),s.p(ref,1));s.supply(ref,2,'GND',dy=6)
 s.part('R301',134,166);s.wire(s.p('R301',1),(120,166));s.power('3V3',(120,166))
 s.wire(s.p('R301',2),(170,166));s.power('VDDA',(145,166));s.wire(s.p('U301',27,2),(145,175),(145,166))
 for ref,x in [('C303',154),('C304',174)]:
  s.part(ref,x,181,orient='v');s.wire((145,166),(x,166),s.p(ref,1));s.supply(ref,2,'GND',dy=7)
 s.part('R302',208,166);s.wire((174,166),s.p('R302',1));s.wire(s.p('R302',2),(258,166));s.power('VREF+',(232,166))
 s.wire(s.p('U301',26,2),(120,185),(120,205),(222,205),(222,166))
 for ref,x in [('C305',237),('C306',260)]:
  s.part(ref,x,181,orient='v');s.wire((222,166),(x,166),s.p(ref,1));s.supply(ref,2,'GND',dy=7)
 s.note(12,215,'U301 units: A digital, B supplies, C gate driver, D/E/F current amplifiers. Same STSPIN32G4 package.')
 return s

def build_gate():
 s=Page('04_Gate_Driver','STSPIN gate drive and 10 V converter','A3')
 s.heading(12,12,'GATE DRIVER / VCC CONVERTER')
 # Driver outputs arranged in matching phase rows; power converter is wired above.
 ps={'61':(-18,-30,'L'),'62':(18,-30,'R'),'63':(0,-38,'T'),'52':(-18,28,'L'),'32':(0,38,'B'),'33':(-10,38,'B'),'34':(10,38,'B')}
 for i,base in enumerate([-14,0,14],1):
  for pn,dy in [( {1:41,2:38,3:35}[i],-3),({1:42,2:39,3:36}[i],3)]:ps[str(pn)]=(-18,base+dy,'L')
  for pn,dy in [({1:43,2:40,3:37}[i],-3),({1:29,2:30,3:31}[i],3)]:ps[str(pn)]=(18,base+dy,'R')
 s.ic('U301',166,121,ps,w=28,h=68,unit=3)
 s.placements[-1]['ref_pos']=(183,86,'left');s.placements[-1]['value_pos']=(185,160,'left')
 s.wire(s.p('U301',61,3),(130,91),(130,40));s.power('VM',(130,40))
 s.part('C311',106,60,orient='v');s.wire((130,40),(106,40),s.p('C311',1));s.supply('C311',2,'GND',dy=6)
 # SW out goes through L301 to output VCC; catch diode cathode on SW.
 s.part('L301',230,64);s.wire(s.p('U301',62,3),(194,91),(194,64),s.p('L301',1))
 s.part('D302',205,78,orient='v');s.wire((205,64),s.p('D302',1));s.supply('D302',2,'GND',dy=5)
 s.wire(s.p('L301',2),(285,64));s.power('VCC',(267,64));s.wire(s.p('U301',63,3),(166,46),(267,46),(267,64))
 for ref,x in [('C312',267),('C313',292)]:
  s.part(ref,x,79,orient='v');s.wire((267,64),(x,64),s.p(ref,1));s.supply(ref,2,'GND',dy=5)
 s.tp('TP301',(280,64));s.tp('TP1002',(267,46))
 for pn in [41,42,38,39,35,36]:s.out('U301',pn,NETS[('U301',str(pn))],dx=-23,unit=3)
 for pn in [43,29,40,30,37,31]:s.out('U301',pn,NETS[('U301',str(pn))],dx=30,unit=3)
 s.supply('U301',32,'GND',dy=12,unit=3)
 # SCREF is shown as the actual divider plus series/filter network.
 s.heading(12,110,'VDS FAULT REFERENCE')
 s.part('R310',42,131,orient='v');s.supply('R310',1,'3V3',dy=-8)
 s.part('R311',42,154,orient='v');s.wire(s.p('R310',2),s.p('R311',1));s.supply('R311',2,'GND',dy=6)
 s.part('R312',76,143);s.wire((42,143),s.p('R312',1));s.wire(s.p('R312',2),(102,143),(102,149),s.p('U301',52,3))
 s.part('C314',102,163,orient='v');s.wire((102,149),s.p('C314',1));s.supply('C314',2,'GND',dy=5);s.tp('TP302',(111,149))
 s.note(12,183,'SCREF is a VDS fault threshold (~0.30 V), not a precision phase-current limit.\nConfigure COMP1/2/4 and TIM1 break before enabling PWM.')
 s.note(12,198,'VCC starts at 8 V. Reapply the 10 V setting after each VM return.\nREGIN and REG3V3/VDD use external 3V3 (unit B). Gate supply stays off with USB alone.')
 return s
