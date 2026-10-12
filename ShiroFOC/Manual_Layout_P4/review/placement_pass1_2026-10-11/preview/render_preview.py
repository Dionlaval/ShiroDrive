"""Read-only placement preview from native KiCad geometry (run with KiCad Python).

Usage: render_preview.py INPUT.kicad_pcb OUTPUT_DIRECTORY
Produces front.svg, back.svg, overview.svg and geometry_manifest.json.
The back is shown in front/top coordinates for cross-side alignment.
"""
from pathlib import Path
from html import escape
import sys, json, hashlib
import pcbnew as p

src=Path(sys.argv[1]).resolve()
out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True)
b=p.LoadBoard(str(src));mm=p.ToMM
xy=lambda q:(mm(q.x),mm(q.y))
poly=p.SHAPE_POLY_SET()
assert b.GetBoardPolygonOutlines(poly), 'Cannot extract valid board outline'
bb=poly.BBox();left,top,right,bottom=map(mm,[bb.GetLeft(),bb.GetTop(),bb.GetRight(),bb.GetBottom()])
width,height=right-left,bottom-top
fps=list(b.GetFootprints())
wire_only={'J1','J101'}

def path(poly):
    a=[]
    for i in range(poly.OutlineCount()):
        for j in [-1]+list(range(poly.HoleCount(i))):
            ln=poly.COutline(i) if j==-1 else poly.CHole(i,j)
            pts=[xy(ln.CPoint(k)) for k in range(ln.PointCount())]
            if pts:a.append('M'+' L'.join(f'{x:.4f},{y:.4f}' for x,y in pts)+' Z')
    return ' '.join(a)

def shape(item,layer):
    ps=p.SHAPE_POLY_SET();item.TransformShapeToPolygon(ps,layer,0,p.FromMM(.008),p.ERROR_INSIDE)
    return path(ps)

def onboard(f):return poly.Contains(f.GetPosition())
for f in fps:f.BuildCourtyardCaches()
onboard_fps=[f for f in fps if onboard(f)]
ics=[dict(ref=f.GetReference(),value=f.GetValue(),side='back' if f.IsFlipped() else 'front',xy_mm=xy(f.GetPosition())) for f in onboard_fps if f.GetReference().startswith('U')]

def panel(side):
    layer,cy,fab=(p.F_Cu,p.F_CrtYd,p.F_Fab) if side=='front' else (p.B_Cu,p.B_CrtYd,p.B_Fab)
    count=sum(f.IsFlipped()==(side=='back') for f in onboard_fps)
    a=[f'<path d="{path(poly)}" fill="#fff" stroke="#213d4c" stroke-width=".11"/>']
    # Light neutral copper provides context without implying completed routing.
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA):
            x,y=xy(t.GetPosition())
            if not(left-.5<x<right+.5 and top-.5<y<bottom+.5):continue
            a.append(f'<circle cx="{x}" cy="{y}" r="{mm(t.GetWidth(layer))/2}" fill="#d1dce0" stroke="#879aa5" stroke-width=".025"/>')
        elif t.GetLayer()==layer:
            x1,y1=xy(t.GetStart());x2,y2=xy(t.GetEnd())
            if not(left-1<x1<right+1 and top-1<y1<bottom+1):continue
            a.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#c3d1d7" stroke-width="{mm(t.GetWidth())}" stroke-linecap="round"/>')
    for f in onboard_fps:
        same=f.IsFlipped()==(side=='back');ref=f.GetReference()
        ic=ref.startswith('U');mount=ref.startswith('H');conn=ref.startswith('J')
        ink='#157c78' if ic else ('#6e8592' if mount else '#355b70')
        if same and ref not in wire_only:
            courtyard=f.GetCourtyard(cy)
            if courtyard.OutlineCount():a.append(f'<path d="{path(courtyard)}" fill="{ink}" fill-opacity="{.075 if ic else .025}" stroke="{ink}" stroke-opacity=".65" stroke-width=".035" stroke-dasharray=".16 .13"/>')
            for g in f.GraphicalItems():
                if isinstance(g,p.PCB_SHAPE) and g.GetLayer()==fab:a.append(f'<path d="{shape(g,fab)}" fill="{ink}"/>')
        for pad in f.Pads():
            if not pad.IsOnLayer(layer):continue
            # The original connector footprints retain outboard plastic mounting
            # posts. They are not part of the chosen bare-wire attachment.
            if ref in wire_only and not poly.Contains(pad.GetPosition()):continue
            fill='#e9d7aa' if conn else ('#dce7e7' if ic else '#dbe4ea')
            a.append(f'<path d="{shape(pad,layer)}" fill="{fill}" stroke="{ink}" stroke-width=".035"/>')
            if pad.GetDrillSize().x:
                x,y=xy(pad.GetPosition())
                a.append(f'<circle cx="{x}" cy="{y}" r="{mm(pad.GetDrillSize().x)/2}" fill="#fff" stroke="{ink}" stroke-width=".025"/>')
        if same:
            x,y=xy(f.GetPosition());size=.54 if ic or conn else (.46 if mount else .34)
            a.append(f'<text x="{x}" y="{y-.08}" text-anchor="middle" font-family="Arial,sans-serif" font-weight="bold" font-size="{size}" fill="{ink}" stroke="#fff" stroke-width=".10" paint-order="stroke">{escape(ref)}</text>')
    a.extend([
        f'<text x="{left}" y="{top-2.5}" font-family="Arial,sans-serif" font-size="1.28" font-weight="bold" fill="#213d4c">P4 · {side.capitalize()} placement</text>',
        f'<text x="{left}" y="{top-1.15}" font-family="Arial,sans-serif" font-size=".61" fill="#59707e">{width:g} × {height:g} mm · {count} footprints on this side · top-view coordinates</text>',
        f'<text x="{left}" y="{bottom+1.45}" font-family="Arial,sans-serif" font-size=".54" fill="#59707e">ICs in teal · native footprint geometry · copper fills omitted</text>',
        f'<text x="{left}" y="{bottom+2.45}" font-family="Arial,sans-serif" font-size=".54" fill="#59707e">J1 / J101 shown as wire pads; connector plastic is intentionally omitted.</text>',
    ])
    return '\n'.join(a)

vw,vh=width+3,height+8
parts={}
for side in ['front','back']:
    content=panel(side);parts[side]=content
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1700" height="{int(1700*vh/vw)}" viewBox="{left-1.5} {top-4.5} {vw} {vh}"><rect x="{left-1.5}" y="{top-4.5}" width="{vw}" height="{vh}" fill="#f7f9fa"/>{content}</svg>'
    (out/f'{side}.svg').write_text(svg)

gap=3;ow=vw*2+gap
svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="3000" height="{int(3000*vh/ow)}" viewBox="0 0 {ow} {vh}"><rect width="{ow}" height="{vh}" fill="#f7f9fa"/>'
for n,side in enumerate(['front','back']):svg+=f'<g transform="translate({-left+1.5+n*(vw+gap)} {-top+4.5})">{parts[side]}</g>'
svg+='</svg>'; (out/'overview.svg').write_text(svg)
(out/'geometry_manifest.json').write_text(json.dumps(dict(source=str(src),sha256=hashlib.sha256(src.read_bytes()).hexdigest(),outline_mm=[width,height],footprints=len(fps),footprint_origins_on_board=len(onboard_fps),footprint_origins_staged=len(fps)-len(onboard_fps),onboard_ics=ics,wire_pad_display=list(sorted(wire_only)),limitations=['Top-view coordinates on both sides, not mirrored underside photography.','Footprint labels reconstructed at component origins for review.','This placement view omits copper zone fills and does not assert final routing or DRC clearance.']),indent=2))
print(json.dumps(dict(source=str(src),output=str(out),onboard_IC_count=len(ics),onboard_footprints=len(onboard_fps))))
