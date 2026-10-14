"""GND finishing after routing: F.Cu/B.Cu/In1 GND pours with thermal reliefs, a ground-via fence along
the board edge and a stitching-via grid, then refill.  Idempotent.
Usage: gnd_finish.py <in.kicad_pcb> <out.kicad_pcb>"""
import sys, math, pcbnew
from pcbnew import FromMM as mm, VECTOR2I
OX, OY, BW, BH = 50.0, 40.0, 100.0, 80.0
CORNER_R, SIDE = 1.5, 1.0
FENCE_INSET, FENCE_PITCH, STITCH_PITCH = 1.0, 3.0, 6.0
VIA_D, VIA_DRILL = 0.6, 0.3
b = pcbnew.LoadBoard(sys.argv[1])
gnd = b.FindNet('GND')
def P(x, y): return VECTOR2I(mm(OX + x), mm(OY + y))

# 0. side strips ---------------------------------------------------------------
# The side keep-out bands only served the autorouter; the unmasked GND strips replace them.
_gone = []
for z in list(b.Zones()):
    if z.GetIsRuleArea():
        bb = z.GetBoundingBox()
        if bb.GetWidth() < mm(3) and bb.GetHeight() > mm(50): b.Remove(z); _gone.append(z)
    elif z.GetZoneName() == 'SIDE_STRIP': b.Remove(z); _gone.append(z)
for d in list(b.GetDrawings()):
    if d.GetLayer() in (pcbnew.F_Mask, pcbnew.B_Mask): b.Remove(d); _gone.append(d)
for (xa, xb) in ((0.0, SIDE), (BW - SIDE, BW)):
    for L in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b); z.SetLayer(L); z.SetNet(b.FindNet('GND')); z.SetZoneName('SIDE_STRIP')
        ol = pcbnew.SHAPE_LINE_CHAIN()
        for (x, y) in [(xa, CORNER_R + 0.1), (xb, CORNER_R + 0.1), (xb, BH - CORNER_R - 0.1), (xa, BH - CORNER_R - 0.1)]: ol.Append(mm(OX + x), mm(OY + y))
        ol.SetClosed(True); z.Outline().AddOutline(ol)
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); z.SetMinThickness(mm(0.2)); b.Add(z)
    for L in (pcbnew.F_Mask, pcbnew.B_Mask):       # bare copper (HASL/ENIG) where the case grooves touch the board
        r = pcbnew.PCB_SHAPE(b); r.SetShape(pcbnew.SHAPE_T_RECT); r.SetFilled(True); r.SetWidth(0); r.SetLayer(L)
        r.SetStart(P(xa - (0.5 if xa == 0.0 else 0.0), CORNER_R + 0.1)); r.SetEnd(P(xb + (0.5 if xb == BW else 0.0), BH - CORNER_R - 0.1)); b.Add(r)

# 1. pours -------------------------------------------------------------------
def pour(layer):
    for z in b.Zones():
        if z.GetLayer() == layer and not z.GetIsRuleArea() and z.GetNetname() == 'GND': return z
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(gnd)
    ol = pcbnew.SHAPE_LINE_CHAIN()
    for (x, y) in [(1.9, 0.6), (BW-1.9, 0.6), (BW-0.6, 1.9), (BW-0.6, BH-1.9), (BW-1.9, BH-0.6), (1.9, BH-0.6), (0.6, BH-1.9), (0.6, 1.9)]: ol.Append(mm(OX + x), mm(OY + y))
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
SV = SIDE * 0.7                       # side vias sit in the groove strip
n = int((BW - 5.0) / FENCE_PITCH)
for i in range(n + 1):                # top/bottom edges
    t = 2.5 + i * (BW - 5.0) / n
    pts += [(t, FENCE_INSET, 'h'), (t, BH - FENCE_INSET, 'h')]
m = int((BH - 6.0) / FENCE_PITCH)
for i in range(m + 1):                # side strips
    t = 3.0 + i * (BH - 6.0) / m
    pts += [(SV, t, 'v'), (BW - SV, t, 'v')]
for x, y, kind in pts:
    for sh in (0, 0.8, -0.8, 1.6, -1.6):
        xx, yy = (x + sh, y) if kind == 'h' else (x, y + sh)
        if ok(xx, yy, False):
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
# starved thermals (single spoke): connect those THT pads solid instead
import re, tempfile, os
pcbnew.SaveBoard(sys.argv[2], b)
_rep = os.path.join(tempfile.gettempdir(), 'gf_drc.rpt'); pcbnew.WriteDRCReport(b, _rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
for m in re.finditer(r'\[starved_thermal\][^\n]*\n[^\n]*\n[^\n]*\n\s*@\(([\d.]+) mm, ([\d.]+) mm\): (?:PTH|Pad)', open(_rep).read()):
    px, py = mm(float(m.group(1))), mm(float(m.group(2)))
    for fp_ in b.GetFootprints():
        for p_ in fp_.Pads():
            if abs(p_.GetPosition().x - px) < 1000 and abs(p_.GetPosition().y - py) < 1000: p_.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)
print('gnd_finish: fence vias', nfence, '(skipped', nskip, '), stitching vias', nst)
