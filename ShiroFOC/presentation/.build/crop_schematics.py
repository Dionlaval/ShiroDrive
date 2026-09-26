from pathlib import Path
import subprocess,json,concurrent.futures
root=Path(__file__).resolve().parent
pdf=root.parents[1]/'ShiroFOC_KiCad/outputs/ShiroFOC_Rev_A_Schematic.pdf'
# Coordinates in the redraw source grid (1.27 mm per unit). Keep actual wires and labels.
crops={
'overview':(1,10,25,330,215),
'dc':(2,9,25,219,73),'damping':(2,9,79,120,132),'divider':(2,123,80,226,133),
'buck':(3,17,28,183,104),'mux':(3,17,117,295,209),'ldo':(3,205,27,314,99),
'controller':(4,13,14,305,147),'clock':(4,126,19,321,91),'corepower':(4,13,149,280,216),'debug':(4,131,88,305,147),
'gate':(5,94,31,307,179),'vcc':(5,97,32,307,98),'scref':(5,12,114,123,177),
'inverter':(6,10,29,321,162),'phase':(6,10,30,113,161),'gates':(6,9,57,88,140),'bootstrap':(6,10,67,91,106),'localcaps':(6,13,34,114,162),'shunt':(6,34,126,114,163),
'current':(7,10,34,105,126),'ntc':(7,10,144,106,199),
'brake':(8,146,34,325,145),'brakecontrol':(8,13,32,150,92),'brakeov':(8,16,84,127,182),
'sensors':(9,12,28,319,205),'encoder':(9,12,23,217,117),'imu':(9,48,119,217,199),
'vmmux':(10,12,158,104,210),'feedback':(10,10,27,321,210),'can':(11,10,24,257,157),'usb':(12,10,27,321,190)
}
def crop(item):
 name,(pg,x1,y1,x2,y2)=item; d=240; scale=d/25.4*1.27
 subprocess.run(['pdftoppm','-f',str(pg),'-l',str(pg),'-singlefile','-r',str(d),'-x',str(round(x1*scale)),'-y',str(round(y1*scale)),'-W',str(round((x2-x1)*scale)),'-H',str(round((y2-y1)*scale)),'-png',str(pdf),str(root/'assets'/name)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 return name
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: print(list(pool.map(crop,crops.items())))
(root/'crops.json').write_text(json.dumps(crops,indent=2))
