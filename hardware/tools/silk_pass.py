"""Place reference designators on F.SilkS after routing so that they avoid pads, vias, silk outlines,
other texts, the logo and the board edge.  Usage: silk_pass.py <in.kicad_pcb> <out.kicad_pcb>"""
import sys, pcbnew
from pcbnew import FromMM as mm, VECTOR2I
OX, OY, BW, BH = 50.0, 40.0, 100.0, 100.0
SIZE, THICK = 0.8, 0.15
b = pcbnew.LoadBoard(sys.argv[1])
F = pcbnew.F_SilkS
def R(bb, m=0.0):
    return (bb.GetLeft()/1e6 - OX - m, bb.GetTop()/1e6 - OY - m, bb.GetRight()/1e6 - OX + m, bb.GetBottom()/1e6 - OY + m)
def hit(a, c): return not (a[2] <= c[0] or c[2] <= a[0] or a[3] <= c[1] or c[3] <= a[1])
def P(x, y): return VECTOR2I(mm(OX + x), mm(OY + y))

obst = [(-1, -1, BW + 1, 0.9), (-1, BH - 0.9, BW + 1, BH + 1), (-1, -1, 0.9, BH + 1), (BW - 0.9, -1, BW + 1, BH + 1)]
fps = list(b.GetFootprints())
for fp in fps:
    for pad in fp.Pads(): obst.append(R(pad.GetBoundingBox(), 0.3))
    for g in fp.GraphicalItems():
        if g.GetLayer() != F or 'TEXT' in g.GetClass().upper(): continue
        bb = R(g.GetBoundingBox(), 0.05)
        if hasattr(g, 'GetShape') and g.GetShape() == pcbnew.SHAPE_T_RECT:
            l, t, r, bt = bb; w = 0.5
            obst += [(l - w, t - w, r + w, t + w), (l - w, bt - w, r + w, bt + w), (l - w, t, l + w, bt), (r - w, t, r + w, bt)]
        else: obst.append(bb)
    if fp.GetReference().startswith('H'): obst.append(R(fp.GetBoundingBox(False, False), 0.2))
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T: obst.append(R(t.GetBoundingBox(), 0.25))
logo = None
for d in b.GetDrawings():
    if d.GetLayer() != F: continue
    if d.GetClass() == 'PCB_SHAPE':
        r = R(d.GetBoundingBox())
        logo = r if logo is None else (min(logo[0], r[0]), min(logo[1], r[1]), max(logo[2], r[2]), max(logo[3], r[3]))
    else: obst.append(R(d.GetBoundingBox(), 0.3))
if logo: obst.append((logo[0] - 0.6, logo[1] - 0.6, logo[2] + 0.6, logo[3] + 0.6))

MANUAL = {'OSC5A2B02': (46.0, 38.4)}
def style(r, size):
    r.SetVisible(True); r.SetLayer(F); r.SetTextSize(VECTOR2I(mm(size), mm(size))); r.SetTextThickness(mm(THICK))
def try_place(fp, cands):
    r = fp.Reference()
    for ang, x, y in cands:
        r.SetTextAngleDegrees(ang); r.SetPosition(P(x, y)); bb = R(r.GetBoundingBox(), 0.12)
        if bb[0] > 1.0 and bb[1] > 1.0 and bb[2] < BW - 1.0 and bb[3] < BH - 1.0 and not any(hit(bb, o) for o in obst):
            obst.append(bb); return True
    return False
def body(fp):
    l, t, r_, bt = 1e9, 1e9, -1e9, -1e9
    for pad in fp.Pads():
        q = R(pad.GetBoundingBox()); l, t, r_, bt = min(l, q[0]), min(t, q[1]), max(r_, q[2]), max(bt, q[3])
    q = R(fp.GetBoundingBox(False, False)); return (min(l, q[0]), min(t, q[1]), max(r_, q[2]), max(bt, q[3]))
def area(fp): q = body(fp); return (q[2]-q[0])*(q[3]-q[1])

failed = []
for fp in sorted(fps, key=lambda f: -area(f)):
    r = fp.Reference(); style(r, SIZE)
    val = fp.GetValue()
    if val in MANUAL:
        x, y = MANUAL[val]; r.SetTextSize(VECTOR2I(mm(1.0), mm(1.0))); r.SetTextAngleDegrees(0); r.SetPosition(P(x, y)); obst.append(R(r.GetBoundingBox(), 0.12)); continue
    l, t, rr, bt = body(fp); cx, cy = (l+rr)/2, (t+bt)/2
    cands = []
    if area(fp) > 150: cands.append((0, cx, cy))
    for gap in (0.35, 0.8, 1.4, 2.2, 3.2, 4.5):
        for ang in (0, 90):
            r.SetTextAngleDegrees(ang); r.SetPosition(P(cx, cy)); bb = R(r.GetBoundingBox()); w, h = bb[2]-bb[0], bb[3]-bb[1]
            for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0), (1, -1), (-1, -1), (1, 1), (-1, 1)):
                cands.append((ang, cx + dx*((rr-l)/2 + w/2 + gap) if dx else cx, cy + dy*((bt-t)/2 + h/2 + gap) if dy else cy))
    if not try_place(fp, cands):
        # dense cluster: keep the designator on the assembly layer instead of cluttering the silkscreen
        failed.append(fp.GetReference())
        r.SetLayer(pcbnew.F_Fab); r.SetTextSize(VECTOR2I(mm(0.6), mm(0.6))); r.SetTextThickness(mm(0.09))
        r.SetTextAngleDegrees(0); r.SetPosition(P(cx, cy))
print('silk pass: designators moved to F.Fab (no free silk space):', failed)
pcbnew.SaveBoard(sys.argv[2], b)
