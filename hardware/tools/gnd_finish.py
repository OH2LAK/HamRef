"""GND finishing after routing: F.Cu/B.Cu/In1 GND pours with thermal reliefs, a ground-via fence along
the board edge and a stitching-via grid, then refill.  Idempotent.
Usage: gnd_finish.py <in.kicad_pcb> <out.kicad_pcb>"""
import sys, math, pcbnew
from pcbnew import FromMM as mm, VECTOR2I
OX, OY, BW, BH = 50.0, 40.0, 100.0, 100.0
FENCE_INSET, FENCE_PITCH, STITCH_PITCH = 1.0, 3.0, 6.0
VIA_D, VIA_DRILL = 0.6, 0.3
b = pcbnew.LoadBoard(sys.argv[1])
gnd = b.FindNet('GND')
def P(x, y): return VECTOR2I(mm(OX + x), mm(OY + y))

# 1. pours -------------------------------------------------------------------
def pour(layer):
    for z in b.Zones():
        if z.GetLayer() == layer and not z.GetIsRuleArea() and z.GetNetname() == 'GND': return z
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(gnd)
    ol = pcbnew.SHAPE_LINE_CHAIN()
    for (x, y) in [(0.6, 0.6), (BW-0.6, 0.6), (BW-0.6, BH-0.6), (0.6, BH-0.6)]: ol.Append(mm(OX + x), mm(OY + y))
    ol.SetClosed(True); z.Outline().AddOutline(ol); b.Add(z); return z
for L in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu): pour(L)
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetNetname() != 'GND': continue
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)      # thermal reliefs: THT/SMD GND pads stay hand-solderable
    z.SetThermalReliefGap(mm(0.3)); z.SetThermalReliefSpokeWidth(mm(0.4)); z.SetMinThickness(mm(0.2))
    z.SetLocalClearance(mm(0.25)); z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
# keep the pour away from the 50 ohm GNSS_RF microstrip (a coplanar ground would change its impedance)
_old = [z for z in b.Zones() if z.GetZoneName() == 'RF_NO_POUR']
for z in _old: b.Remove(z)
_keep = _old   # keep references (SWIG)
rf = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() == 'GNSS_RF']
have = {id(z) for z in b.Zones()}
for t in rf:
    x0, y0, x1, y1 = t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1: continue
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L; w = t.GetWidth() / 2 + mm(0.7)
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetLayerSet(pcbnew.LSET(pcbnew.F_Cu))
    z.SetDoNotAllowCopperPour(True); z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ol = pcbnew.SHAPE_LINE_CHAIN()
    for (x, y) in [(x0 + nx*w, y0 + ny*w), (x1 + nx*w, y1 + ny*w), (x1 - nx*w, y1 - ny*w), (x0 - nx*w, y0 - ny*w)]: ol.Append(int(x), int(y))
    ol.SetClosed(True); z.Outline().AddOutline(ol); z.SetZoneName('RF_NO_POUR'); b.Add(z)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())

# 2. vias ---------------------------------------------------------------------
vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
pads = [(p, fp) for fp in b.GetFootprints() for p in fp.Pads()]
tracks = [t for t in b.GetTracks()]
noviaz = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
gnd_pours = {L: [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.GetLayer() == L] for L in (pcbnew.F_Cu, pcbnew.B_Cu)}
def _bb(bb): return (bb.GetLeft()/1e6 - OX, bb.GetTop()/1e6 - OY, bb.GetRight()/1e6 - OX, bb.GetBottom()/1e6 - OY)
silk_boxes = []
for fp in b.GetFootprints():
    r = fp.Reference()
    if r.IsVisible() and r.GetLayer() == pcbnew.F_SilkS: silk_boxes.append(_bb(r.GetBoundingBox()))
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.F_SilkS: silk_boxes.append(_bb(d.GetBoundingBox()))
def ok(x, y, need_pour):
    pos = P(x, y); r = VIA_D / 2
    for z in noviaz:
        for dx, dy in ((0, 0), (0.35, 0), (-0.35, 0), (0, 0.35), (0, -0.35)):
            if z.Outline().Contains(VECTOR2I(pos.x + mm(dx), pos.y + mm(dy))): return False
    for (l, t, r_, bt) in silk_boxes:
        if l - 0.35 < x < r_ + 0.35 and t - 0.35 < y < bt + 0.35: return False
    for v in vias:
        d = math.hypot(v.GetPosition().x - pos.x, v.GetPosition().y - pos.y) / 1e6
        if d < 0.95: return False
    for t in tracks:
        if t.Type() == pcbnew.PCB_VIA_T: continue
        if t.GetNetname() == 'GND': continue
        if t.HitTest(pos, mm(r + 0.25)): return False
    for p, fp in pads:
        m = r + (0.25 if p.GetNetname() != 'GND' else 0.4)
        if p.HitTest(pos, mm(m)): return False
        if p.GetAttribute() in (pcbnew.PAD_ATTRIB_NPTH, ) and p.HitTest(pos, mm(r + 0.6)): return False
    if need_pour:
        for L, zs in gnd_pours.items():
            if not any(z.HitTestFilledArea(L, pos, 0) for z in zs): return False
    return True
def add(x, y):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetNet(gnd); v.SetWidth(mm(VIA_D)); v.SetDrill(mm(VIA_DRILL))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(v); vias.append(v); tracks.append(v)
nfence = nskip = 0
pts = []
n = int((BW - 2*FENCE_INSET) / FENCE_PITCH)
for i in range(n + 1):
    t = FENCE_INSET + i * (BW - 2*FENCE_INSET) / n
    pts += [(t, FENCE_INSET), (t, BH - FENCE_INSET)]
    if 0 < i < n: pts += [(FENCE_INSET, t), (BW - FENCE_INSET, t)]
for x, y in pts:
    horiz = abs(y - FENCE_INSET) < 1e-6 or abs(y - (BH - FENCE_INSET)) < 1e-6      # point on top/bottom edge -> slide along x
    for sh in (0, 0.8, -0.8, 1.6, -1.6):
        xx, yy = (x + sh, y) if horiz else (x, y + sh)
        if FENCE_INSET <= xx <= BW - FENCE_INSET and FENCE_INSET <= yy <= BH - FENCE_INSET and ok(xx, yy, False):
            add(xx, yy); nfence += 1; break
    else: nskip += 1
nst = 0
y = 4.0
row = 0
while y < BH - 3:
    x = 4.0 + (STITCH_PITCH / 2 if row % 2 else 0)
    while x < BW - 3:
        if ok(x, y, True): add(x, y); nst += 1
        x += STITCH_PITCH
    y += STITCH_PITCH; row += 1
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)
print('gnd_finish: fence vias', nfence, '(skipped', nskip, '), stitching vias', nst)
