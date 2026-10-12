"""Read-only P4 placement evidence from native KiCad 9 geometry."""
from pathlib import Path
from html import escape
import hashlib, json, math
import pcbnew as p
HERE=Path(__file__).resolve().parent
SRC=HERE.parents[1]/'ShiroFOC_Manual.kicad_pcb'
b=p.LoadBoard(str(SRC))
mm=p.ToMM

def xy(q): return mm(q.x),mm(q.y)
def poly_path(poly):
    parts=[]
    for i in range(poly.OutlineCount()):
        for j in [-1]+list(range(poly.HoleCount(i))):
            ln=poly.COutline(i) if j==-1 else poly.CHole(i,j)
            pts=[xy(ln.CPoint(k)) for k in range(ln.PointCount())]
            if pts: parts.append('M'+' L'.join(f'{x:.4f},{y:.4f}' for x,y in pts)+' Z')
    return ' '.join(parts)
def geom(item,layer):
    poly=p.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(poly,layer,0,p.FromMM(.008),p.ERROR_INSIDE)
    return poly_path(poly)
def inside(x,y):
    dx=max(abs(x)-19.5,0);dy=max(abs(y)-19.5,0)
    return abs(x)<=22.5 and abs(y)<=22.5 and dx*dx+dy*dy<=9

fps=list(b.GetFootprints())
rows=[]
for f in fps:
    x,y=xy(f.GetPosition());f.BuildCourtyardCaches()
    rows.append(dict(ref=f.GetReference(),value=f.GetValue(),side='B' if f.IsFlipped() else 'F',x_mm=x,y_mm=y,angle=f.GetOrientationDegrees(),origin_inside_outline=inside(x,y),locked=f.IsLocked(),footprint=f.GetFPID().GetUniStringLibId(),visible_reference=f.Reference().IsVisible()))
(HERE/'placement_inventory.json').write_text(json.dumps({'source':str(SRC),'sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'board_outline_mm':{'width':45,'height':45,'corner_radius':3},'origin_inside':sum(r['origin_inside_outline'] for r in rows),'origin_outside':sum(not r['origin_inside_outline'] for r in rows),'parts':rows},indent=2))

for side,layer,cy,fb in [('front',p.F_Cu,p.F_CrtYd,p.F_Fab),('back',p.B_Cu,p.B_CrtYd,p.B_Fab)]:
    for variant,box in [('board',(-24,-26,48,51)),('all',(-96,-49,204,114))]:
        x0,y0,w,h=box
        a=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{1700 if variant=="board" else 2600}" height="{int((1700 if variant=="board" else 2600)*h/w)}" viewBox="{x0} {y0} {w} {h}">',f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="#f4f6f9"/>','<rect x="-22.5" y="-22.5" width="45" height="45" rx="3" fill="#fff" stroke="#283f53" stroke-width=".14"/>',f'<text x="{x0+.8}" y="{y0+1.6}" font-family="Arial" font-size="{1.0 if variant=="board" else 1.8}" fill="#283f53">P4 {side}: native geometry, top-view coordinates; '+('45 × 45 mm outline' if variant=='board' else 'staged components outside the board are still present')+'</text>']
        for t in b.GetTracks():
            if isinstance(t,p.PCB_VIA):
                x,y=xy(t.GetPosition());a.append(f'<circle cx="{x}" cy="{y}" r="{mm(t.GetWidth(layer))/2}" fill="#a2b9c6" stroke="#628191" stroke-width=".02"/>')
            elif t.GetLayer()==layer:
                x1,y1=xy(t.GetStart());x2,y2=xy(t.GetEnd());a.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#a1bac6" stroke-width="{mm(t.GetWidth())}" stroke-linecap="round"/>')
        for f in fps:
            same=f.IsFlipped()==(side=='back');ref=f.GetReference();x,y=xy(f.GetPosition())
            bad=side=='back' and ref in ['U601','R309','R313','R314']
            c='#c43f46' if bad else ('#aa7847' if not inside(x,y) else '#416278')
            if same:
                poly=f.GetCourtyard(cy)
                if poly.OutlineCount():a.append(f'<path d="{poly_path(poly)}" fill="{c}" fill-opacity=".04" stroke="{c}" stroke-width=".035" stroke-dasharray=".16 .12"/>')
                for g in f.GraphicalItems():
                    if isinstance(g,p.PCB_SHAPE) and g.GetLayer()==fb:a.append(f'<path d="{geom(g,fb)}" fill="{c}"/>')
            for pad in f.Pads():
                if pad.IsOnLayer(layer):
                    a.append(f'<path d="{geom(pad,layer)}" fill="#dce5eb" stroke="{c}" stroke-width=".035"/>')
                    if pad.GetDrillSize().x:
                        px,py=xy(pad.GetPosition());a.append(f'<circle cx="{px}" cy="{py}" r="{mm(pad.GetDrillSize().x)/2}" fill="#fff" stroke="{c}" stroke-width=".03"/>')
            if same:
                size=.51 if ref[0] in 'UQJLH' else .38
                if variant=='all':size=.67
                a.append(f'<text x="{x}" y="{y-.1}" text-anchor="middle" font-family="Arial" font-weight="bold" font-size="{size}" fill="{c}" stroke="white" stroke-width=".10" paint-order="stroke">{escape(ref)}</text>')
        a.append('</svg>')
        (HERE/f'placement_{side}_{variant}.svg').write_text('\n'.join(a))

print(json.dumps({'footprints':len(rows),'inside_origin':sum(r['origin_inside_outline'] for r in rows),'outside_origin':sum(not r['origin_inside_outline'] for r in rows),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest()}))
