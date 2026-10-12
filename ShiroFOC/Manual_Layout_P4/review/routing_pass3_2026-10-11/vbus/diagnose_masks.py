from pathlib import Path
import sys
r=Path(__file__).resolve().parent.parent
sys.argv=['probe',str(r/'vbus/prepared2/ShiroFOC_Manual.kicad_pcb'),str(r/'before/drc.json'),str(r/'vbus/mask_diagnostic/ShiroFOC_Manual.kicad_pcb'),'VBUS_SENSE','--layers','F,B,L3,L4','--step','.025']
source=(r/'engine/route_signals.py').read_text().split('report=json.loads(args.drc.read_text())')[0].replace("Path(__file__).with_name('grid_route_native.dylib')","Path(__file__).resolve().parent.parent/'engine/grid_route_native.dylib'")
exec(compile(source,'router_helpers','exec'))
lib.flood.argtypes=[byte,byte,byte,byte,ct.c_int]
block,via=masks('VBUS_SENSE',.1524)
seed=next(q for q in pads if q.GetParentFootprint().GetReference()=='U4' and q.GetNumber()=='9')
st,_=terminals(component(seed))
obstacles=[];holes=[]
for q in pads+list(b.GetTracks()):
    own=q.GetNetname()=='VBUS_SENSE'
    if isinstance(q,p.PCB_VIA):
        holes.append((q.GetPosition().x,q.GetPosition().y,mm(.15+.45)+q.GetDrillValue()/2))
    if own and not isinstance(q,p.PAD):continue
    cl=0 if own else mm(.5 if q.GetNetClassName()=='Power' else .2)
    bb=q.GetBoundingBox();bb.Inflate(cl+mm(.25))
    qq=[q.GetEffectiveShape(l) for l in alllayers if q.IsOnLayer(l)]
    obstacles.append((bb.GetLeft(),bb.GetRight(),bb.GetTop(),bb.GetBottom(),cl,qq))
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="2200" viewBox="0 0 20 22"><rect width="20" height="22" fill="white"/>']
for li,layer in enumerate(layers):
    twin=np.ones((2,n,n),np.uint8);twin[0]=block[li];starts=np.zeros_like(twin);starts[0]=st[li];visited=np.zeros_like(twin);lib.flood(twin,np.ones((n,n),np.uint8),starts,visited,n)
    yy,xx=np.where(visited[0]);print(layer,'bounds',(origin+xx.min()*step,origin+xx.max()*step,origin+yy.min()*step,origin+yy.max()*step),flush=True)
    legal=[]
    for yy0,xx0 in zip(yy,xx):
        if xx0%2 or yy0%2:continue
        vx,vy=mm(float(origin+xx0*step)),mm(float(origin+yy0*step))
        if any((vx-hx)**2+(vy-hy)**2<rad*rad for hx,hy,rad in holes):continue
        shape0=p.SHAPE_CIRCLE(p.VECTOR2I(vx,vy),mm(.25))
        if any(left<=vx<=right and top<=vy<=bottom and any(q.Collide(shape0,cl) for q in qq) for left,right,top,bottom,cl,qq in obstacles):continue
        legal.append([p.ToMM(vx),p.ToMM(vy)])
    print('NATIVE LEGAL',layer,len(legal),legal[:100],flush=True)
    (r/f'vbus/native_via_sites_{layer}.json').write_text(json.dumps(legal))
    img=block[li].copy();img[visited[0].astype(bool)]=2;img[st[li].astype(bool)]=3
    x0=int((-13-origin)/step);x1=int((-7-origin)/step);y0=int((5-origin)/step);y1=int((15-origin)/step)
    ox=(li%2)*10;oy=(li//2)*11
    for y in range(y0,y1):
        xs=x0
        while xs<x1:
            val=img[y,xs];end=xs+1
            while end<x1 and img[y,end]==val:end+=1
            if val:svg.append(f'<rect x="{ox+(xs-x0)*step}" y="{oy+(y-y0)*step}" width="{(end-xs)*step}" height="{step}" fill="{["white","#999","#66bcee","#f40"][val]}"/>')
            xs=end
    svg.append(f'<text x="{ox+6.2}" y="{oy+1}" font-size=".3">Layer {layer}</text>')
svg.append('</svg>');(r/'vbus/masks.svg').write_text(''.join(svg))
