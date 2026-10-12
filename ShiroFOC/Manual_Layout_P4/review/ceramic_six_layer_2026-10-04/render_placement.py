"""Read-only, true-geometry placement drawings for both board sides."""
import sys
from pathlib import Path
from html import escape
import pcbnew as p

src=Path(sys.argv[1]); out=Path(sys.argv[2]); out.mkdir(exist_ok=True)
b=p.LoadBoard(str(src)); ox,oy=-40,-40
def xy(v):return p.ToMM(v.x)-ox,p.ToMM(v.y)-oy
def poly_path(poly):
    parts=[]
    for i in range(poly.OutlineCount()):
        for j in [-1]+list(range(poly.HoleCount(i))):
            line=poly.COutline(i) if j==-1 else poly.CHole(i,j)
            points=[xy(line.CPoint(k)) for k in range(line.PointCount())]
            if points:parts.append('M'+' L'.join(f'{x:.4f},{y:.4f}' for x,y in points)+' Z')
    return ' '.join(parts)
def shape(item,layer):
    poly=p.SHAPE_POLY_SET();item.TransformShapeToPolygon(poly,layer,0,p.FromMM(.01),p.ERROR_INSIDE)
    return poly_path(poly)
for side,layer,cy,fb in [('front',p.F_Cu,p.F_CrtYd,p.F_Fab),('back',p.B_Cu,p.B_CrtYd,p.B_Fab)]:
    a=['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1680" viewBox="-2 -4 84 88">',
       '<rect x="-2" y="-4" width="84" height="88" fill="#f8fafc"/>',
       '<rect x="0" y="0" width="80" height="80" rx="5" fill="#fff" stroke="#25394b" stroke-width=".18"/>',
       f'<text x="0" y="-1.7" font-family="Arial" font-size="1.2" fill="#24364b">P3 {side} placement — top-view coordinates</text>']
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA):
            x,y=xy(t.GetPosition());a.append(f'<circle cx="{x}" cy="{y}" r="{p.ToMM(t.GetWidth(layer))/2}" fill="#c1c8d4" stroke="#59677a" stroke-width=".035"/>')
        elif t.GetLayer()==layer:
            x1,y1=xy(t.GetStart());x2,y2=xy(t.GetEnd())
            a.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#a2a9b7" stroke-width="{p.ToMM(t.GetWidth())}" stroke-linecap="round"/>')
    for f in b.GetFootprints():
        same=f.IsFlipped()==(side=='back')
        if same:
            f.BuildCourtyardCaches();poly=f.GetCourtyard(cy)
            if poly.OutlineCount():a.append(f'<path d="{poly_path(poly)}" fill="#7aa1ba" fill-opacity=".045" stroke="#92a8b8" stroke-width=".045" stroke-dasharray=".2 .15"/>')
            for g in f.GraphicalItems():
                if isinstance(g,p.PCB_SHAPE) and g.GetLayer()==fb:a.append(f'<path d="{shape(g,fb)}" fill="#4f6271"/>')
        for pad in f.Pads():
            if pad.IsOnLayer(layer):
                a.append(f'<path d="{shape(pad,layer)}" fill="#d6e0e8" stroke="#44657c" stroke-width=".045"/>')
                if pad.GetDrillSize().x:
                    x,y=xy(pad.GetPosition());a.append(f'<circle cx="{x}" cy="{y}" r="{p.ToMM(pad.GetDrillSize().x)/2}" fill="white" stroke="#688497" stroke-width=".04"/>')
        if same:
            x,y=xy(f.GetPosition());ref=f.GetReference();size=.68 if ref[0] in 'UQJL' else .53
            a.append(f'<text x="{x}" y="{y-.15}" text-anchor="middle" font-family="Arial" font-weight="bold" font-size="{size}" fill="#142b44" stroke="white" stroke-width=".15" paint-order="stroke">{escape(ref)}</text>')
        if f.GetReference().startswith('H'):
            x,y=xy(f.GetPosition());a.append(f'<circle cx="{x}" cy="{y}" r="4" fill="none" stroke="#9f7380" stroke-width=".08" stroke-dasharray=".35 .3"/>')
    a.append('</svg>');(out/f'placement_{side}.svg').write_text('\n'.join(a))
    a.pop()
    guide_layer=p.User_1 if side=='front' else p.User_2
    for d in b.GetDrawings():
        if d.GetLayer()!=guide_layer:continue
        if isinstance(d,p.PCB_SHAPE):
            x1,y1=xy(d.GetStart());x2,y2=xy(d.GetEnd())
            a.append(f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="#328078" stroke-width=".10" stroke-dasharray=".6 .35"/>')
        elif isinstance(d,p.PCB_TEXT):
            x,y=xy(d.GetPosition());size=p.ToMM(d.GetTextSize().x)
            a.append(f'<text x="{x}" y="{y}" dominant-baseline="middle" text-anchor="middle" font-family="Arial" font-weight="bold" font-size="{size}" fill="#145d57" stroke="white" stroke-width=".22" paint-order="stroke">{escape(d.GetText())}</text>')
    a.append('</svg>');(out/f'sections_{side}.svg').write_text('\n'.join(a))
print(out)
