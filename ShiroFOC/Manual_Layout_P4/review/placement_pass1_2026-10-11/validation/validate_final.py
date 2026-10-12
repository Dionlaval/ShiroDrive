"""Read-only structural validation of the combined P4 placement candidate.

Run with KiCad's bundled Python. Default inputs are ../before and ../final.
This verifies placement integrity, not completed routing or fabrication readiness.
"""
from pathlib import Path
from collections import Counter, defaultdict
import argparse, hashlib, json, math, re, sys
import xml.etree.ElementTree as ET
import pcbnew as p

HERE=Path(__file__).resolve().parent
RUN=HERE.parent
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--before',type=Path,default=RUN/'before/ShiroFOC_Manual.kicad_pcb')
ap.add_argument('--after',type=Path,default=RUN/'final/ShiroFOC_Manual.kicad_pcb')
ap.add_argument('--netlist',type=Path,default=RUN.parent/'layout_review_2026-10-11/schematic_netlist.xml')
ap.add_argument('--output',type=Path,default=HERE/'final_structural_validation.json')
args=ap.parse_args()
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
start_hash=digest(args.after)
a=p.LoadBoard(str(args.before)); b=p.LoadBoard(str(args.after))
af={f.GetReference():f for f in a.GetFootprints()};bf={f.GetReference():f for f in b.GetFootprints()}
failures=[];warnings=[]
def mm(v):return round(p.ToMM(v),6)
def xy(v):return [mm(v.x),mm(v.y)]
def uid(item):return item.m_Uuid.AsString()
def field(f,name):
    return next((q.GetText() for q in f.GetFields() if q.GetName()==name),'')
def footprint_state(f):
    return dict(uuid=uid(f),reference=f.GetReference(),value=f.GetValue(),
                footprint=f.GetFPID().GetUniStringLibId(),position=xy(f.GetPosition()),
                angle=f.GetOrientationDegrees(),side='B' if f.IsFlipped() else 'F',
                schematic_path=f.GetPath().AsString())
def pad_identity(f):
    return {uid(q):dict(number=q.GetNumber(),net=q.GetNetname()) for q in f.Pads()}
def pad_geometry(f):
    return {uid(q):dict(number=q.GetNumber(),net=q.GetNetname(),position=xy(q.GetPosition()),
                       size=xy(q.GetSize()),drill=xy(q.GetDrillSize()),angle=q.GetOrientationDegrees(),
                       layer_set=q.GetLayerSet().FmtHex(),shape=int(q.GetShape()),attribute=int(q.GetAttribute())) for q in f.Pads()}
def polygon_data(poly):
    out=[]
    for n in range(poly.OutlineCount()):
        ring=poly.COutline(n)
        out.append([xy(ring.CPoint(i)) for i in range(ring.PointCount())])
    return out

outline_a=p.SHAPE_POLY_SET();outline=p.SHAPE_POLY_SET()
outline_a_ok=a.GetBoardPolygonOutlines(outline_a)
outline_ok=b.GetBoardPolygonOutlines(outline)
if not outline_ok:failures.append('Final board outline did not form valid polygon(s).')
outline_equal=outline_a_ok and polygon_data(outline_a)==polygon_data(outline)
if not outline_equal:failures.append('Board outline changed or could not be compared.')
edge_counts={'before':sum(x.GetLayer()==p.Edge_Cuts for x in a.GetDrawings()),'after':sum(x.GetLayer()==p.Edge_Cuts for x in b.GetDrawings())}

def inside_mm(point):return bool(outline.Contains(p.VECTOR2I(p.FromMM(point[0]),p.FromMM(point[1]))))
def footprint_envelope(f):
    f.BuildCourtyardCaches()
    poly=f.GetCourtyard(p.B_CrtYd if f.IsFlipped() else p.F_CrtYd)
    rings=polygon_data(poly)
    if rings:return rings,'courtyard'
    # Retain honest provenance when the custom footprint contains no courtyard.
    box=f.GetBoundingBox(False,False)
    left,top,right,bottom=mm(box.GetLeft()),mm(box.GetTop()),mm(box.GetRight()),mm(box.GetBottom())
    return [[[left,top],[right,top],[right,bottom],[left,bottom]]],'native_body_pad_bounds_fallback'
def entire_envelope_inside(rings):
    # Dense boundary samples cover the actual rounded 45 mm outline, not just
    # footprint origins. The current outline is convex and has no cutouts.
    outside=[]
    for ring in rings:
        for i,v in enumerate(ring):
            w=ring[(i+1)%len(ring)]
            steps=max(1,math.ceil(math.hypot(w[0]-v[0],w[1]-v[1])/.1))
            for n in range(steps+1):
                q=[v[k]+(w[k]-v[k])*n/steps for k in [0,1]]
                if not inside_mm(q):outside.append([round(x,4) for x in q])
    return not outside,outside[:12]

u_results=[]
for r in sorted(x for x in bf if re.fullmatch(r'U\d+',x)):
    f=bf[r];rings,source=footprint_envelope(f);ok,outside=entire_envelope_inside(rings)
    u_results.append(dict(reference=r,value=f.GetValue(),source=source,full_envelope_inside=ok,
                          position=xy(f.GetPosition()),side='B' if f.IsFlipped() else 'F',outside_samples=outside))
    if not ok:failures.append(r+' full courtyard/body envelope is outside the board.')
if len(u_results)!=18:failures.append('Expected 18 U references; found '+str(len(u_results)))
fallbacks=[x['reference'] for x in u_results if x['source']!='courtyard']
if fallbacks:warnings.append('No courtyard polygons on '+', '.join(fallbacks)+'; native body/pad envelopes checked instead.')

removed_refs=sorted(set(af)-set(bf));added_refs=sorted(set(bf)-set(af))
if removed_refs:failures.append('Existing footprints removed: '+', '.join(removed_refs))
if added_refs!=['R618']:failures.append('Expected R618 as sole new footprint; found '+str(added_refs))
identity_changes=[];path_changes=[];pad_changes=[];allowed_wire_cleanup=[];moved=[]
for r in sorted(set(af)&set(bf)):
    old,new=af[r],bf[r]
    if uid(old)!=uid(new):identity_changes.append(r)
    if old.GetPath().AsString()!=new.GetPath().AsString():path_changes.append(r)
    if [xy(old.GetPosition()),old.GetOrientationDegrees(),old.IsFlipped()] != [xy(new.GetPosition()),new.GetOrientationDegrees(),new.IsFlipped()]:moved.append(r)
    oldp,newp=pad_identity(old),pad_identity(new)
    for pid in sorted(set(oldp)|set(newp)):
        if oldp.get(pid)==newp.get(pid):continue
        if r in ['J1','J101'] and pid in oldp and pid not in newp and not oldp[pid]['number'] and not oldp[pid]['net']:
            allowed_wire_cleanup.append(dict(reference=r,pad_uuid=pid,old=oldp[pid]))
        else:pad_changes.append(dict(reference=r,pad_uuid=pid,before=oldp.get(pid),after=newp.get(pid)))
if identity_changes:failures.append('Existing footprint UUID changes: '+str(identity_changes))
if path_changes:failures.append('Existing schematic path changes: '+str(path_changes))
if pad_changes:failures.append('Unexpected existing pad identity/net changes: '+str(len(pad_changes)))

fixed={}
for r in ['U4','U601']:
    ok=r in af and r in bf and footprint_state(af[r])==footprint_state(bf[r]) and pad_geometry(af[r])==pad_geometry(bf[r])
    fixed[r]=dict(unchanged=ok,before=footprint_state(af[r]),after=footprint_state(bf[r]))
    if not ok:failures.append(r+' fixed footprint state/pad geometry changed.')

mounting={}
for r in sorted(set(x for x in af if re.fullmatch(r'H\d+',x))|set(x for x in bf if re.fullmatch(r'H\d+',x))):
    ok=r in af and r in bf and footprint_state(af[r])==footprint_state(bf[r]) and pad_geometry(af[r])==pad_geometry(bf[r])
    mounting[r]=dict(unchanged=ok,pad_count=len(list(bf[r].Pads())) if r in bf else 0)
    if not ok:failures.append(r+' mounting footprint changed.')

def keepouts(board):
    result={}
    for zone in board.Zones():
        if zone.GetIsRuleArea():
            result[uid(zone)]=dict(polygons=polygon_data(zone.Outline()),layer_set=zone.GetLayerSet().FmtHex(),
                                  tracks=zone.GetDoNotAllowTracks(),vias=zone.GetDoNotAllowVias(),
                                  pads=zone.GetDoNotAllowPads(),copperpour=zone.GetDoNotAllowCopperPour(),
                                  footprints=zone.GetDoNotAllowFootprints())
    return result
ka,kb=keepouts(a),keepouts(b)
if ka!=kb:failures.append('Rule-area keepouts changed.')

via_violations=[];via_counts=Counter()
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA):
        dia,drill=mm(t.GetWidth(p.F_Cu)),mm(t.GetDrillValue())
        via_counts[str(dia)+'/'+str(drill)]+=1
        if abs(dia-.5)>1e-6 or abs(drill-.3)>1e-6:
            via_violations.append(dict(uuid=uid(t),position=xy(t.GetPosition()),diameter_mm=dia,drill_mm=drill,net=t.GetNetname()))
if via_violations:failures.append(str(len(via_violations))+' standalone vias differ from 0.5/0.3 mm.')

# Verify the added current-limit resistor against the exported schematic netlist.
netroot=ET.parse(args.netlist).getroot()
comp=next(c for c in netroot.findall('./components/comp') if c.attrib['ref']=='R618')
expected_nets={}
for n in netroot.findall('./nets/net'):
    for node in n.findall('node'):
        if node.attrib['ref']=='R618':expected_nets[node.attrib['pin']]=n.attrib['name']
expected_path=comp.find('sheetpath').attrib['tstamps']+comp.findtext('tstamps')
r618=bf.get('R618')
expected_r618=dict(value=comp.findtext('value'),footprint=comp.findtext('footprint'),path=expected_path,pad_nets=expected_nets)
actual_r618=None
if r618:
    actual_r618=dict(value=r618.GetValue(),footprint=r618.GetFPID().GetUniStringLibId(),path=r618.GetPath().AsString(),pad_nets={q.GetNumber():q.GetNetname() for q in r618.Pads()})
    r618_ok=actual_r618==expected_r618 and not r618.IsDNP() and field(r618,'Assembly')=='FIT'
else:r618_ok=False
if not r618_ok:failures.append('R618 does not match schematic value/footprint/path/net identities/FIT status.')

def fit_status(f):
    assembly=field(f,'Assembly').upper()
    if f.IsDNP() or assembly=='DNP':return 'DNP'
    if 'DO NOT FIT' in assembly or 'PCB FEATURE' in assembly:return 'PCB feature'
    return 'fitted/default'
def category(f):
    ref=f.GetReference();v=f.GetValue().upper()
    if field(f,'Bank'):return 'DC-link ceramic bank'
    if ref in ['R415','C413','R425','C423','R435','C433']:return 'phase RC snubbers'
    if ref in ['C104','C105','C106']:return 'VM input ceramic support'
    if ref in ['R102','C107','D101']:return 'optional bus damping/TVS'
    if ref=='R101':return 'VM bleeder'
    if ref=='SW301':return 'reset switch'
    if ref=='J1001':return 'SWD programming footprint'
    if ref=='J502':return 'brake NTC connector'
    if ref.startswith('TP'):return 'test point'
    return f.GetSheetname() or re.sub(r'\d+','',ref)

inventory=[];counts=Counter();staged_groups=defaultdict(list)
for r,f in sorted(bf.items()):
    on=bool(outline.Contains(f.GetPosition()));fit=fit_status(f)
    row=dict(reference=r,value=f.GetValue(),position=xy(f.GetPosition()),side='B' if f.IsFlipped() else 'F',
             origin_on_board=on,fit_status=fit,category=category(f),sheet=f.GetSheetname())
    inventory.append(row);counts[('on_board' if on else 'staged')+' | '+fit]+=1
    if not on:staged_groups[row['category']].append(row)
before_on=sum(bool(outline_a.Contains(f.GetPosition())) for f in af.values())

if start_hash!=digest(args.after):failures.append('Final PCB changed during validation; rerun for stable evidence.')
output=dict(status='PASS' if not failures else 'FAIL',scope='Structural placement validation only; not routing/fabrication readiness',
            inputs=dict(before=str(args.before),after=str(args.after),before_sha256=digest(args.before),after_sha256=start_hash,netlist=str(args.netlist)),
            failures=failures,warnings=warnings,
            footprints=dict(before=len(af),after=len(bf),added=added_refs,removed=removed_refs,moved_count=len(moved),moved=moved,
                            existing_uuid_changes=identity_changes,schematic_path_changes=path_changes,pad_identity_net_changes=pad_changes,
                            allowed_unnumbered_wire_mechanical_pad_removals=allowed_wire_cleanup),
            fixed_footprints=fixed,integrated_circuit_envelopes=u_results,
            board_outline=dict(unchanged=outline_equal,edge_object_counts=edge_counts,polygon_count=outline.OutlineCount()),
            mounting_holes=mounting,rule_area_keepouts=dict(before_count=len(ka),after_count=len(kb),unchanged=ka==kb),
            standalone_vias=dict(count=sum(via_counts.values()),diameter_drill_counts=dict(via_counts),nonstandard=via_violations),
            R618=dict(matches_schematic=r618_ok,expected=expected_r618,actual=actual_r618),
            placement_inventory=dict(before_origins_on_board=before_on,after_origins_on_board=sum(x['origin_on_board'] for x in inventory),
                                     counts_by_location_fit_status=dict(counts),staged_categories={k:dict(count=len(v),references=[x['reference'] for x in v],fit_counts=dict(Counter(x['fit_status'] for x in v))) for k,v in staged_groups.items()},parts=inventory))
args.output.write_text(json.dumps(output,indent=2)+'\n')
text=[output['status']+' — structural placement validation',
      'Final PCB SHA256: '+start_hash,
      'Footprints: %d -> %d; moved existing: %d; added: %s' % (len(af),len(bf),len(moved),', '.join(added_refs)),
      'On-board origins: %d -> %d' % (before_on,output['placement_inventory']['after_origins_on_board']),
      'U references: %d; true courtyards: %d; native body/pad fallback: %s' % (len(u_results),sum(x['source']=='courtyard' for x in u_results),', '.join(fallbacks) or 'none'),
      'Origins by placement / assembly status: '+json.dumps(dict(counts)),
      'Still staged:']
for cat,rows in staged_groups.items():
    text.append('  %s: %d (%s); %s' % (cat,len(rows),dict(Counter(x['fit_status'] for x in rows)),', '.join(x['reference'] for x in rows)))
text+=['Warnings: '+str(warnings),'Failures: '+str(failures)]
args.output.with_suffix('.txt').write_text('\n'.join(text)+'\n')
print('\n'.join(text))
sys.exit(1 if failures else 0)
