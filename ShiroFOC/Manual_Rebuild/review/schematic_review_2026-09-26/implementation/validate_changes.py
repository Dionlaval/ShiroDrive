import sys,zipfile,json,xml.etree.ElementTree as E,collections,hashlib
sys.path.insert(0,str(__import__('pathlib').Path(__file__).parent));from sexp_edit import *
R=P/'review/schematic_review_2026-09-26/implementation'
b=E.parse(P/'review/schematic_review_2026-09-26/netlist.xml');a=E.parse(R/'netlist.xml')
def groups(r,expand=False):
 out=set()
 for n in r.findall('.//nets/net'):
  nodes=set()
  for x in n.findall('node'):
   refn,pin=x.get('ref'),x.get('pin')
   if refn in ['TP903','TP1003']:continue
   if refn in ['U1','U2','U3']:
    if pin in ['21','23','24','25','26']:continue
    if expand and pin in ['[3-11]','[12-20]']:
     for v in (range(3,12) if pin=='[3-11]' else range(12,21)):nodes.add((refn,str(v)))
     continue
   nodes.add((refn,pin))
  if nodes:out.add(frozenset(nodes))
 return out
assert groups(b,True)==groups(a),'Unexpected topology changes'
with zipfile.ZipFile(R/'before_changes.zip') as z:
 old=parse(z.read('libs/Manual.pretty/DMM0022A.kicad_mod').decode())
 new=read(P/'libs/Manual.pretty/DMM0022A.kicad_mod')
 for p in children(old,'pad'):
  if p[1]=='V':p[1]=Q('27')
 assert old==new,'Footprint geometry changed'
 beforemodels={n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.endswith(('.step','.stp','.wrl'))}
 assert all(hashlib.sha256((P/n).read_bytes()).hexdigest()==h for n,h in beforemodels.items())
K=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport');libparts={(x.get('lib'),x.get('part')):x for x in a.findall('.//libparts/libpart')};rows=[]
for c in a.findall('.//components/comp'):
 r=c.get('ref');fp=c.findtext('footprint','');assert fp,r
 ns,fn=fp.split(':');f=(P/'libs/Manual.pretty' if ns=='Manual' else K/'footprints'/(ns+'.pretty'))/(fn+'.kicad_mod');assert f.exists(),fp
 d=read(f);pads={str(x[1]) for x in children(d,'pad') if x[1]};ls=c.find('libsource');pins={x.get('num') for x in libparts[ls.get('lib'),ls.get('part')].findall('./pins/pin')};missing=pins-pads;extra=pads-pins
 assert not missing or r=='U205' and missing=={'19','20'},(r,missing)
 assert not extra or extra=={'MP'},(r,extra)
 models=[]
 for m in children(d,'model'):
  path=str(m[1]).replace('${KIPRJMOD}',str(P)).replace('${KICAD9_3DMODEL_DIR}',str(K/'3dmodels'));models.append({'link':m[1],'exists':Path(path).exists()})
 props={x.get('name'):x.text or '' for x in c.findall('./fields/field')}
 rows.append({'ref':r,'value':c.findtext('value'),'mpn':props.get('MPN',''),'footprint':fp,'path':str(f),'pads':sorted(pads),'missing_pads':sorted(missing),'extra_pads':sorted(extra),'models':models})
dups={n.get('name'):[x.get('ref') for x in n.findall('node') if x.get('ref','').startswith('TP')] for n in a.findall('.//nets/net')};dups={n:v for n,v in dups.items() if len(v)>1};assert not dups,dups
result={'topology_preserved_except_intended_pin_expansion_and_removed_testpoints':True,'downloaded_fet_geometry_preserved':True,'all_existing_3d_files_unchanged':True,'all_footprints_resolve':True,'components':len(rows),'unique_footprints':len({x['footprint'] for x in rows}),'no_duplicate_testpoint_nets':True,'documented_pad_exceptions':{x['ref']:{'missing':x['missing_pads'],'extra':x['extra_pads']} for x in rows if x['missing_pads'] or x['extra_pads']}}
(R/'validation.json').write_text(json.dumps(result,indent=2));(R/'cad_inventory.json').write_text(json.dumps(rows,indent=2));print(json.dumps(result,indent=2))
