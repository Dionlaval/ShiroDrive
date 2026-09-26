import xml.etree.ElementTree as E,json,hashlib
from pathlib import Path
work=Path(__file__).resolve().parent
def load(f):
 d=E.parse(work/f);nets={n.get('name'):frozenset((a.get('ref'),a.get('pin')) for a in n.findall('node')) for n in d.findall('.//nets/net')};pins={v:k for k,vs in nets.items() for v in vs};comps={c.get('ref'):c for c in d.findall('.//components/comp')};return nets,pins,comps
bn,bp,bc=load('before.xml');an,ap,ac=load('after.xml');checks=[]
def ck(name,test):
 assert test,name
 checks.append(name)
def nodes(*xs):return frozenset(tuple(x.split('.')) for x in xs)
def exact(name,*xs):ck(name,an[name]==nodes(*xs))
def same(*xs):ps=nodes(*xs);ck('Connected: '+', '.join(xs),len({ap[x] for x in ps})==1)
exact('I2C2_SCL','R308.2','U4.21','U701.13')
exact('I2C2_SDA','R715.2','TP1024.1','U4.44','U701.14')
exact('INPUT_MUX_ENABLE_N','R305.2','U4.4','U602.15')
exact('EXT_FEEDBACK_SELECT','R306.1','U4.53','U602.1')
for pin in ['5','8','12']:ck('BMI323 pin '+pin+' to 3V3',ap['U701',pin]=='3V3')
for pin in ['1','6','7']:ck('BMI323 pin '+pin+' to GND',ap['U701',pin]=='GND')
for r in ['R308','R715']:ck(r+' to 3V3',ap[r,'1']=='3V3')
for pin in ['6','7','8','9','10','14']:ck('AS5047 unused '+pin,len(an[ap['U601',pin]])==1)
for p1,p2 in [('1','1'),('3','3')]:pass
ck('No BMI323 on any encoder SPI net',all(not any(a=='U701' for a,b in ns) for n,ns in an.items() if 'SPI3' in n))
same('U601.2','R313.2','TP1010.1');same('U601.4','R314.2','TP1012.1');same('U601.3','R611.1');same('R611.2','U4.55','TP1011.1');same('U601.1','U4.51','R309.2')
for p,j,r,pull,pd,bi,bo,mp,mo,mc in [('1','3','R605','R608','R615','1','7','3','4','57'),('2','4','R606','R609','R616','3','5','6','7','58'),('4','5','R607','R610','R617','6','2','10','9','59')]:
 same('D601.'+p,'J601.'+j,r+'.1');same(r+'.2',pull+'.2',pd+'.1','U603.'+bi);same('U603.'+bo,'U602.'+mp);same('U602.'+mo,'U4.'+mc);ck(pd+' GND',ap[pd,'2']=='GND')
for p in ['2','5','11','8']:ck('Mux grounded '+p,ap['U602',p]=='GND')
for p,n in [('1','3V3'),('3','5V_SYS')]:ck('Jumper '+p,ap['JP601',p]==n)
same('JP601.2','R604.1');same('J601.1','R604.2','R608.1','R609.1','R610.1')
ck('Sensor supply not grounded',ap['J601','1']!='GND');same('J601.2','U603.4','R307.2');same('U603.8','C605.1','U701.8')
ck('Isolated ESD rail exactly cap + protection',an[ap['D601','5']]==nodes('D601.5','C604.1'))
exact('VBUS_MUX_IN','R106.2','U602.13','U602.14');exact('VBUS_SENSE','C108.1','TP103.1','U4.13','U602.12')
# Remaining circuitry: compare connected pin groups independent of renamed sheet paths.
new=set(ac)-set(bc);removed=set(bc)-set(ac)
changed_refs=new|removed|{'U601','U701','U602','J601','D601','R604','R605','R606','R607','R608','R609','R610','R308','TP1024'}
changed_pins={('U4','21'),('U4','44')}
allowed={x for x in bp if x[0] not in changed_refs and x not in changed_pins}
def groups(n):return {frozenset(xs&allowed) for xs in n.values() if xs&allowed}
ck('All unaffected pin groups preserved',groups(bn)==groups(an))
ck('Existing footprint assignments preserved',all(bc[r].findtext('footprint','')==ac[r].findtext('footprint','') for r in set(bc)&set(ac)))
ck('Only intended removals',removed=={'R601','R602','R603','R714'})
ck('New components',new=={'U603','JP601','R715','R615','R616','R617','C605'})
ck('U603/JP601 CAD deferred',all(not ac[r].findtext('footprint','') for r in ['U603','JP601']))
def findings(f):
 return {(s['path'],v['type'],v['description'],tuple(sorted(x['description'] for x in v['items']))) for s in json.load(open(work/f))['sheets'] for v in s['violations']}
ck('ERC findings unchanged',findings('before_erc.json')==findings('after_erc.json'))
result={'checks_passed':len(checks),'checks':checks,'erc_before':len(findings('before_erc.json')),'erc_after':len(findings('after_erc.json')),'new_components':sorted(new),'removed_components':sorted(removed),'scope':'Schematic interface revision only; no board, CAD or fabrication qualification'}
(work/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
