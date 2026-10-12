"""Independent native KiCad geometry and copper connectivity comparison."""
from pathlib import Path
from collections import Counter
import pcbnew as p
import json,hashlib,math,xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'placement_manifest.json').read_text())
before=p.LoadBoard(str(HERE/'baseline.kicad_pcb'))
after=p.LoadBoard(str(HERE/'final.kicad_pcb'))
def uid(o):return o.m_Uuid.AsString()
def pt(v):return [v.x,v.y]
def fpd(f):
    return {'position':pt(f.GetPosition()),'rotation':f.GetOrientationDegrees(),'layer':f.GetLayer(),'id':str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()),'value':f.GetValue(),'dnp':f.IsDNP(),'path':f.GetPath().AsString(),
            'pads':sorted([(uid(q),q.GetNumber(),q.GetNetname(),pt(q.GetPosition()),pt(q.GetSize()),pt(q.GetDrillSize()),q.GetOrientationDegrees(),q.GetLayerSet().FmtHex()) for q in f.Pads()])}
def copper(t):
    d={'type':type(t).__name__,'start':pt(t.GetStart()),'end':pt(t.GetEnd()),'net':t.GetNetname(),'layer':t.GetLayer()}
    if isinstance(t,p.PCB_VIA):d.update(diameter=t.GetWidth(p.F_Cu),drill=t.GetDrillValue(),layers=t.GetLayerSet().FmtHex())
    else:d['width']=t.GetWidth()
    return d
fa={f.GetReference():f for f in before.GetFootprints()};fb={f.GetReference():f for f in after.GetFootprints()}
assert fa.keys()==fb.keys() and len(fa)==219
assert not any(r.startswith('TP') for r in fb)
for r in manifest['protected_references']:assert fpd(fa[r])==fpd(fb[r]),r
for r in fa:
    a,z=fpd(fa[r]),fpd(fb[r])
    assert all(a[k]==z[k] for k in ['id','value','dnp','path']),r
    assert [(q[0],q[1],q[2],q[4],q[5]) for q in a['pads']]==[(q[0],q[1],q[2],q[4],q[5]) for q in z['pads']],r
    q=fb[r].GetPosition();assert 73.660311<=p.ToMM(q.x)<=153.660313 and 63.93633<=p.ToMM(q.y)<=143.936333,r
assert fb['U601'].IsFlipped() and pt(fb['U601'].GetPosition())==[113660312,103936331]
ca={uid(t):t for t in before.GetTracks()};cb={uid(t):t for t in after.GetTracks()}
assert ca.keys()==cb.keys() and len(ca)==325
for u in manifest['fixed_copper_uuids']:assert copper(ca[u])==copper(cb[u]),u
for u,move in manifest['moved_copper'].items():
    a,z=copper(ca[u]),copper(cb[u]);assert all(a[k]==z[k] for k in a if k not in ['start','end']),u
    if 'translation_nm' in move:
        delta=move['translation_nm']
        assert z['start']==[a['start'][i]+delta[i] for i in range(2)],u
        assert z['end']==[a['end'][i]+delta[i] for i in range(2)],u
    else:
        # The only reflected object is the via at U201's PG pad during its side change.
        old,new=fa['U201'].GetPosition(),fb['U201'].GetPosition()
        assert z['start']==[new.x+a['start'][0]-old.x,new.y-(a['start'][1]-old.y)],u

def connectivity(board):
    board.BuildConnectivity();con=board.GetConnectivity()
    items=list(board.GetTracks())+[q for f in board.GetFootprints() for q in f.Pads() if q.GetNetname()]
    roots={uid(i):uid(i) for i in items}
    def root(u):
        while roots[u]!=u:roots[u]=roots[roots[u]];u=roots[u]
        return u
    def union(a,z):
        if a in roots and z in roots:
            aa,zz=root(a),root(z)
            if aa!=zz:roots[max(aa,zz)]=min(aa,zz)
    for item in items:
        for q in con.GetConnectedPads(item):union(uid(item),uid(q))
        for t in con.GetConnectedTracks(item):union(uid(item),uid(t))
    groups={}
    for u in roots:groups.setdefault(root(u),[]).append(u)
    return sorted(tuple(sorted(v)) for v in groups.values())
first,last=connectivity(before),connectivity(after)
assert first==last, 'Physical copper connectivity changed'

# Compare schematic inventory without importing omitted parts or test points.
tree=ET.parse(HERE/'source_netlist.xml').getroot();sch={v.attrib['ref']:v for v in tree.find('components')}
schematic_only=sorted(sch.keys()-fb.keys())
expected={}
for net in tree.find('nets'):
    name=net.attrib['name']
    if name.startswith(('Net-(','unconnected-(')):name=name.replace('/','{slash}')
    for node in net:expected[node.attrib['ref'],node.attrib['pin']]=name
pad_net_mismatches=[]
for ref,f in fb.items():
    for q in f.Pads():
        if q.GetNumber() and (ref,q.GetNumber()) in expected and q.GetNetname()!=expected[ref,q.GetNumber()]:pad_net_mismatches.append([ref,q.GetNumber(),q.GetNetname(),expected[ref,q.GetNumber()]])

result={'status':'PASS','footprints':len(fb),'protected_footprints_identical':len(manifest['protected_references']),
 'moved_footprints':len(manifest['moved_references']),'test_points':0,'tracks':sum(not isinstance(t,p.PCB_VIA) for t in after.GetTracks()),'vias':sum(isinstance(t,p.PCB_VIA) for t in after.GetTracks()),
 'protected_copper_objects_identical':len(manifest['fixed_copper_uuids']),'relocated_copper_objects':len(manifest['moved_copper']),
 'all_copper_connected_components_identical':True,'physical_connected_components':len(first),'encoder_center_mm':[113.660312,103.936331],
 'schematic_only_references_retained_absent':schematic_only,'schematic_only_test_points':sum(r.startswith('TP') for r in schematic_only),
 'present_pad_net_mismatches':pad_net_mismatches,'final_sha256':hashlib.sha256((HERE/'final.kicad_pcb').read_bytes()).hexdigest()}
(HERE/'geometry_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
