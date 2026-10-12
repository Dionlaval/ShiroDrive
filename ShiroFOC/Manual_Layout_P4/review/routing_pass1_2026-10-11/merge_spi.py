from pathlib import Path
import pcbnew as p,json,shutil
R=Path(__file__).resolve().parent;delta=json.loads((R/'engine/optimized/final/delta.json').read_text());src=R/'grounded/ShiroFOC_Manual.kicad_pcb';d=R/'optimized';d.mkdir(exist_ok=True)
b=p.LoadBoard(str(src));c=p.LoadBoard(delta['candidate']);remove=set(delta['delete_ids']);add=set(delta['new_ids']);items=[t for t in b.GetTracks()if t.m_Uuid.AsString()in remove];assert len(items)==len(remove)
for t in items:b.Remove(t)
netobjs={n.GetNetname():n for n in b.GetNetInfo().NetsByNetcode().values()};ids=[];hold=[]
for old in c.GetTracks():
 if old.m_Uuid.AsString()not in add:continue
 if isinstance(old,p.PCB_VIA):
  t=p.PCB_VIA(b);t.SetPosition(old.GetPosition());t.SetWidth(old.GetWidth(p.F_Cu));t.SetDrill(old.GetDrill());t.SetViaType(old.GetViaType());t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED)
 else:
  t=p.PCB_TRACK(b);t.SetStart(old.GetStart());t.SetEnd(old.GetEnd());t.SetWidth(old.GetWidth());t.SetLayer(old.GetLayer())
 t.SetNet(netobjs[old.GetNetname()]);b.Add(t);hold.append(t);ids.append(t.m_Uuid.AsString())
assert len(ids)==len(add)
for fn in ['ShiroFOC_Manual.kicad_pro','ShiroFOC_Manual.kicad_dru','fp-lib-table','sym-lib-table']:shutil.copy2(src.parent/fn,d/fn)
if not(d/'libs').exists():(d/'libs').symlink_to((src.parent/'libs').resolve(),target_is_directory=True)
p.SaveBoard(str(d/src.name),b);(d/'replacement_manifest.json').write_text(json.dumps({'net':delta['net'],'removed_items':list(remove),'new_items':ids,'old_length_mm':delta['old_length_mm'],'new_length_mm':delta['new_length_mm']},indent=2))
print('Replaced MISO',len(remove),'items with',len(ids),'items')
