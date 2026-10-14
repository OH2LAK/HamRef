"""Try to finish one leftover connection by hand: manual_route.py in.kicad_pcb out.kicad_pcb NET x1 y1 x2 y2 (board mm)
Tries straight/L-shaped F.Cu, B.Cu and In2.Cu (with vias) paths and keeps the first that adds no DRC errors."""
import sys, re, itertools, collections, pcbnew
from pcbnew import FromMM as mm, VECTOR2I
OX, OY = 50.0, 40.0
inp, outp, net = sys.argv[1], sys.argv[2], sys.argv[3]
x1, y1, x2, y2 = map(float, sys.argv[4:8])
def P(x, y): return VECTOR2I(mm(OX + x), mm(OY + y))
def drc(b):
    pcbnew.WriteDRCReport(b, '/tmp/mr.rpt', pcbnew.EDA_UNITS_MILLIMETRES, True)
    t = open('/tmp/mr.rpt').read()
    return collections.Counter(re.findall(r'^\[(\w+)\]', t, re.M)), t
base = None
def attempt(path, layer, vias):
    b = pcbnew.LoadBoard(inp); n = b.FindNet(net); items = []
    for (a, c) in zip(path, path[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(mm(0.25)); t.SetLayer(layer); t.SetNet(n); b.Add(t)
    for v_ in vias:
        v = pcbnew.PCB_VIA(b); v.SetPosition(P(*v_)); v.SetNet(n); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(v)
    return b
b0 = pcbnew.LoadBoard(inp); c0, _ = drc(b0)
bad = {k: c0.get(k, 0) for k in ('clearance', 'shorting_items', 'tracks_crossing', 'hole_clearance', 'via_dangling', 'track_dangling')}
cands = []
for layer in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu):
    for mid in ((x1, y2), (x2, y1)):
        cands.append((layer, [(x1, y1), mid, (x2, y2)]))
    for off in (-3, -2, -1, 1, 2, 3):
        cands.append((layer, [(x1, y1), (x1, y1 + off), (x2, y1 + off), (x2, y2)]))
        cands.append((layer, [(x1, y1), (x1 + off, y1), (x1 + off, y2), (x2, y2)]))
for layer, path in cands:
    vias = [] if layer == pcbnew.F_Cu else [path[0], path[-1]]
    b = attempt(path, layer, vias); c, _ = drc(b)
    ok = all(c.get(k, 0) <= bad[k] for k in ('clearance', 'shorting_items', 'tracks_crossing', 'hole_clearance')) and c.get('unconnected_items', 0) < c0.get('unconnected_items', 0)
    print(b.GetLayerName(layer), [tuple(round(v, 1) for v in p) for p in path], 'OK' if ok else dict((k, c.get(k, 0)) for k in ('clearance', 'unconnected_items')))
    if ok:
        pcbnew.SaveBoard(outp, b); print('saved', outp); sys.exit(0)
print('no path found'); sys.exit(1)
