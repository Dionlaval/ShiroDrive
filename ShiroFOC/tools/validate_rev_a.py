#!/usr/bin/env python3
"""Release gates: real KiCad nets vs intended pins, pad audit, BOM, and calculations."""
import argparse, csv, hashlib, itertools, json, math, sys, xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'ShiroFOC_KiCad'; O=P/'outputs'
BASELINE=ROOT/'review_baselines'/'A0_before_redraw'
def check(condition,message):
 if not condition: raise AssertionError(message)

def read_baseline(path):
 """The redraw must preserve the released circuit, not just its regenerated intent."""
 manifest=json.loads((path/'manifest.json').read_text())
 for filename,key in [('source_connectivity.json','ShiroFOC_KiCad/outputs/source_connectivity.json'),
                      ('original_BOM.csv','ShiroFOC_KiCad/outputs/ShiroFOC_Rev_A_BOM.csv')]:
  check(hashlib.sha256((path/filename).read_bytes()).hexdigest()==manifest['files'][key],
        f'Frozen baseline hash mismatch: {filename}')
 source=json.loads((path/'source_connectivity.json').read_text())
 with (path/'original_BOM.csv').open(newline='') as f:rows=list(csv.DictReader(f))
 bom={r['Reference']:r for r in rows}
 check(len(rows)==len(bom) and set(bom)==set(source),'Frozen BOM reference set differs from connectivity baseline')
 return source,bom

def audit_netlist(xml,source,baseline_bom,metadata=True):
 """Compare complete sets of connected physical pins, independent of net names.

 Native local labels acquire hierarchy prefixes. Exact equality of each pin set
 proves that labels may change without accepting a split, short or swapped pin.
 Names are canonicalized only in the returned in-memory map for the explicit
 datasheet pin contracts below; the KiCad netlist is never rewritten.
 """
 comps={c.attrib['ref']:c for c in xml.findall('./components/comp')}
 check(len(comps)==len(xml.findall('./components/comp')),'Duplicate netlist component reference')
 check(set(comps)==set(source),'Netlist reference set differs from source')
 nodes={}; raw_nets={}; nc=0
 for net in xml.findall('./nets/net'):
  name=net.attrib['name'];pins=net.findall('node')
  check(name not in raw_nets,f'Duplicate net name: {name}')
  raw_nets[name]={(n.attrib['ref'],n.attrib['pin']) for n in pins}
  check(pins,f'Empty physical net: {name}')
  for n in pins:
   key=(n.attrib['ref'],n.attrib['pin']);check(key not in nodes,f'Duplicate pin in nets: {key}')
   nodes[key]=(name,n.attrib.get('pintype',''))
 expected_pins={(r,p) for r,c in source.items() for p in c['pins']}
 check(set(nodes)==expected_pins,
       f'Physical pin set changed; missing={sorted(expected_pins-set(nodes))}, extra={sorted(set(nodes)-expected_pins)}')
 expected=defaultdict(set)
 for ref,c in source.items():
  for pin,want in c['pins'].items():
   key=want if want is not None else ('NC',ref,pin)
   expected[key].add((ref,pin))
 expected_groups={frozenset(pins):name for name,pins in expected.items()}
 check(len(expected_groups)==len(expected),'Invalid duplicate baseline net partition')
 canonical={};aliases={}
 for actual,pins in raw_nets.items():
  group=frozenset(pins)
  if group not in expected_groups:
   wants={source[r]['pins'][p] for r,p in pins}
   missing={str(want):sorted(expected[want]-pins) for want in wants if want is not None}
   raise AssertionError(f'Physical net partition changed: {actual}; actual pins={sorted(pins)}; '
                        f'baseline nets={sorted(str(w) for w in wants)}; missing pins={missing}')
  name=expected_groups[group]
  canonical[actual]=actual if isinstance(name,tuple) else name
  if not isinstance(name,tuple) and actual!=name:aliases[actual]=name
 check(len(raw_nets)==len(expected),'Physical net partition count changed')
 for ref,c in source.items():
  check(comps[ref].findtext('footprint')==c['footprint'],f'{ref} footprint changed')
  check(comps[ref].findtext('value')==c['value'],f'{ref} value changed')
  if metadata:
   fields={f.attrib['name']:f.text or '' for f in comps[ref].findall('./fields/field')}
   check(fields.get('Assembly')==c['assembly'],f'{ref} Assembly changed')
   check(fields.get('MPN','')==baseline_bom[ref]['MPN'],f'{ref} MPN changed: {baseline_bom[ref]["MPN"]!r} -> {fields.get("MPN","")!r}')
   check((comps[ref].find('./property[@name="dnp"]') is not None)==(c['assembly']=='DNP'),f'{ref} native DNP flag changed')
  for pin,want in c['pins'].items():
   actual,kind=nodes[(ref,pin)]
   if want is None:
    check('no_connect' in kind and len(raw_nets[actual])==1,f'{ref}.{pin} NC is connected');nc+=1
   else:check('no_connect' not in kind,f'{ref}.{pin} functional pin marked NC')
 nets={canonical[actual]:pins for actual,pins in raw_nets.items()}
 check(len(nets)==len(raw_nets),'Canonical net names collide')
 return comps,nodes,nets,nc,aliases

def main(argv=None):
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--project',type=Path,default=P,help='KiCad project directory (default: released project)')
 ap.add_argument('--baseline',type=Path,default=BASELINE,help='Frozen A0 baseline directory')
 ap.add_argument('--netlist',type=Path,help='XML netlist to check instead of outputs/ShiroFOC_Rev_A.net')
 ap.add_argument('--netlist-only',action='store_true',help='Run partition, physical metadata and critical pin checks without other release artifacts')
 args=ap.parse_args(argv)
 project=args.project.resolve();output=project/'outputs'
 source,baseline_bom=read_baseline(args.baseline.resolve())
 check(json.loads((output/'source_connectivity.json').read_text())==source,'Current source intent differs from frozen A0 baseline')
 netlist=args.netlist.resolve() if args.netlist else output/'ShiroFOC_Rev_A.net'
 xml=ET.parse(netlist).getroot()
 comps,nodes,nets,nc,aliases=audit_netlist(xml,source,baseline_bom)
 sheet_sources={s.findtext('./title_block/source') for s in xml.findall('./design/sheet')}
 sheet_count=len(xml.findall('./design/sheet'))
 check(sheet_count==len(sheet_sources) and None not in sheet_sources,'Duplicate or unspecified hierarchy sheet source')
 check(sheet_sources=={f.name for f in project.glob('*.kicad_sch')},'Netlist did not cover every native schematic sheet')
 def on(net,*pins):
  check(set(pins)<=nets.get(net,set()),f'Critical mapping failed: {net} {pins}')
 # Explicit independent physical-pad contracts (datasheet-based, not serializer output).
 on('VM',('J101','2'),('U201','2'),('U301','61'),('Q401','27'),('Q402','27'),('Q403','27'),('D504','1'))
 on('GND',('J101','1'),('U301','32'),('U301','65'),('Q501','1'),('Q501','2'),('Q501','3'),('U901','12'))
 on('3V3',('U301','1'),('U301','2'),('U301','64'),('U901','6'),('U901','7'),('U502','6'),('R801','1'),('R805','1'))
 on('5V_SYS',('U203','1'),('U203','8'),('U204','1'))
 on('VCC',('L301','2'),('U301','63'),('U501','1'))
 on('VCC_SW',('D302','1'),('U301','62'),('L301','1'))
 on('GND',('D302','2'),('D501','2'),('Y301','2'),('Y301','4'))
 on('BRAKE_GATE',('Q501','4'),('D501','1'),('R503','2'))
 on('BRK_SW',('Q501','5'),('Q501','6'),('Q501','7'),('Q501','8'),('J501','2'),('D504','2'))
 on('BRAKE_PWM_DRV',('D502','1'),('D503','1'),('U501','3'),('R505','1'))
 on('BRAKE_OV_REF',('U502','4'),('U502','5'))
 on('BRAKE_OV_SENSE',('U502','3'),('R508','2'),('R509','1'),('R510','2'))
 on('VBUS_SENSE',('U301','13'),('U602','12'),('C108','1'))
 on('VBUS_MUX_IN',('R106','2'),('U602','13'),('U602','14'))
 on('FB_ESD_RAIL',('D601','5'),('C604','1'))
 on('FEEDBACK_ENABLE_N',('U301','4'),('U602','15'),('R305','2'))
 on('FEEDBACK_I_H3',('U301','59'),('U602','9'),('R307','1'),('R1001','1'))
 check(not any(r.startswith('TP') for r,p in nets['FEEDBACK_I_H3']),'PB8 must not have a test stub')
 on('CAN_STB',('U301','28'),('U801','8'),('R801','2'))
 on('STATUS_LED_RED',('U301','11'),('D301','1'))
 on('STATUS_LED_A',('D301','2'),('R304','2'))
 for i,phase in enumerate('UVW',1):
  q=f'Q40{i}'; r=f'R4{i}6'
  on(f'OUT{i}',*[(q,str(p)) for p in range(2,12)])
  on(f'SHUNT_{phase}_FORCE_P',*[(q,str(p)) for p in range(12,21)],(r,'1'),(f'C4{i}5','2'))
  on(f'SHUNT_{phase}_SENSE_P',(r,'2'),(f'R4{i}7','1'))
  on(f'SHUNT_{phase}_SENSE_N',(r,'3'),(f'R4{i}8','1'))
  on('GND',(r,'4'),(f'C4{i}2','2'),(f'R44{i}','2'))
  on(f'OPP_{phase}1',(f'R4{i}7','2'),(f'R4{i}0','2'),(f'R44{i}','1'))
  on('VREF+',(f'R4{i}0','1'))
  check(source[f'R4{i}9']['value']=='28k 0.1%' and source[f'R4{i}0']['value']=='56k 0.1%' and source[f'R44{i}']['value']=='56k 0.1%','Current-sense ratio changed')
 if args.netlist_only:
  print(json.dumps({'status':'PASS','scope':'Physical net partitions, metadata, NC singletons and critical pin contracts',
                    'sheets':sheet_count,'components':len(source),'verified_symbol_pins':len(nodes),
                    'NC_pins':nc,'nets_including_NC':len(nets),'renamed_local_nets':len(aliases)},indent=2))
  return
 erc=json.loads((output/'erc_rev_a.json').read_text())
 check(len(erc['sheets'])==sheet_count,f'ERC did not cover {sheet_count} sheets')
 violations=[v for s in erc['sheets'] for v in s['violations']]
 check(not violations,f'ERC has {len(violations)} violations')
 settings=json.loads((project/'ShiroFOC_KiCad.kicad_pro').read_text())
 check(not settings['erc']['erc_exclusions'],'ERC exclusions are not permitted')
 with (output/'ShiroFOC_Rev_A_BOM.csv').open(newline='') as f:bom=list(csv.DictReader(f))
 check({r['Reference'] for r in bom}==set(source) and len(bom)==len(source),'BOM differs from netlist')
 dnp=[]
 for row in bom:
  ref=row['Reference']; c=source[ref]
  check(row['Footprint']==c['footprint'] and row['Value']==c['value'],f'BOM mismatch {ref}')
  check(row['Assembly']==c['assembly'],f'Assembly mismatch {ref}')
  check(row['MPN']==baseline_bom[ref]['MPN'],f'BOM MPN changed {ref}')
  check(bool(row['DNP'])==(c['assembly']=='DNP'),f'Native DNP mismatch {ref}')
  check(row['MPN'] or row['Procurement'],f'{ref} lacks purchasing specification')
  if c['assembly']=='DNP':dnp.append(ref)
 audit=json.loads((output/'footprint_audit.json').read_text())
 check(not audit['problems'] and audit['components']==len(source),'Footprint loading/pad check failed')
 # Independent circuit equations and corner calculations. These do not simulate switching.
 vref=3.3; rsh=.0005; gain=28
 sense={str(i):vref/2+gain*rsh*i for i in (-80,-60,0,60,80)}
 check(min(sense.values())>.2 and max(sense.values())<3.1,'Current amplifier lacks ADC headroom')
 bias=[]
 for a,b,c,d,e in itertools.product((.999,1.001),repeat=5):
  rp,rn,rf,rt,rb=1000*a,1000*b,28000*c,56000*d,56000*e
  vp=(vref/rt)/(1/rp+1/rt+1/rb)
  bias.append(vp*(1+rf/rn))
 # TLV3012B: 1.223..1.260 V REF, +/-9mV offset, 2..8mV internal hysteresis.
 # Corner bound adds full 100ppm/C *100C reference drift conservatively.
 rises=[];falls=[]
 for rt,rb,rh,ref,off,hyst,vol,voh in itertools.product((449550,450450),(12687.3,12712.7),(999000,1001000),(1.223*.99,1.260*1.01),(-.009,.009),(.002,.008),(0,.2),(3.034,3.366)):
  rises.append((ref+off+hyst/2)*(1+rt/rb+rt/rh)-vol*rt/rh)
  falls.append((ref+off-hyst/2)*(1+rt/rb+rt/rh)-voh*rt/rh)
 check(max(rises)<48,'Brake comparator worst-case exceeds prototype ceiling')
 omega=2000*2*math.pi/60
 calculations={
  'current':{'gain':gain,'shunt_ohm':rsh,'V_per_A':gain*rsh,'output_V_by_A':sense,'zero_offset_V_resistor_tolerance_only':[min(bias),max(bias)],'shunt_W_at_40Arms':40**2*rsh,'shunt_instantaneous_W_at_80A':80**2*rsh,'COMP_input_V_at_60A':(56*.0005*60+3.3)/58,'COMP_DAC_12bit_code_nominal_60A':round(4095*((56*.0005*60+3.3)/58)/3.3),'note':'Calibrate amplifier and comparator offsets, DAC error and shunt temperature. One-sided comparator threshold is not a guaranteed bidirectional 60A limit.'},
  'bus':{'divider_ratio':1/21,'ADC_V_at_42V':2.0,'ADC_V_at_60V':60/21,'RC_tau_s':(540e3*27e3/(567e3)+1000)*10e-9,'settle_wait_s':.002,'bulk_capacitance_uF':2040,'energy_J_at_42V':.5*.00204*42**2,'bulk_ripple_sum_A_at_100kHz_rating':3*1.690},
  'brake':{'nominal_rise_V':(1.242+.003)*(1+450/12.7+450/1000),'nominal_fall_V':(1.242-.003)*(1+450/12.7+450/1000)-3.3*.45,'rise_corner_V':[min(rises),max(rises)],'fall_corner_V':[min(falls),max(falls)],'resistor_ohm_example':10,'current_A_at_48V':4.8,'power_W_at_48V':230.4,'mechanical_example_inertia_kg_m2':.01,'mechanical_example_rpm':2000,'mechanical_example_energy_J':.5*.01*omega**2,'resistor_minimum_continuous_W_with_specified_heatsink':250,'resistor_required_pulse_J_over_5s_example':500,'note':'Corner estimate, not transient simulation. External energy and bus spikes must be tested. No gate drive if VCC is absent.'},
  'logic_budget_mA':{'MCU_driver_logic_allowance':100,'encoder_allowance':25,'IMU_allowance':10,'CAN_dominant_max':61,'CP2102N_allowance':20,'external_feedback_max':25,'LED_mux_bias_misc':9,'total_allowance':250,'CAN_fault_total_allowance':320,'LDO_dissipation_W_5_25V_250mA':.4875,'LDO_dissipation_W_5_25V_320mA':.624,'note':'Planning allowances; measure rail current and LDO junction rise. USB-only requires a source permitting >=500mA; pre-enumeration/suspend compliance is not implemented.'}}
 (output/'electrical_calculations.json').write_text(json.dumps(calculations,indent=2)+'\n')
 report={'status':'PASS','sheets':sheet_count,'components':len(source),'connected_nets':len(nets)-nc,'nets_including_NC':len(nets),'verified_symbol_pins':len(nodes),'NC_pins':nc,'ERC_violations':0,'unique_footprints':audit['unique_footprints'],'DNP_references':sorted(dnp),'frozen_baseline':str(args.baseline.resolve()),'physical_net_partitions_unchanged':True,'renamed_local_nets':len(aliases),'scope':'Schematic and package release checks; no PCB routing, hardware test or switching simulation.'}
 (output/'validation_report.json').write_text(json.dumps(report,indent=2)+'\n')
 (output/'net_name_aliases.json').write_text(json.dumps(aliases,indent=2,sort_keys=True)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':
 try:main()
 except Exception as e: print(f'FAIL: {e}',file=sys.stderr);raise
