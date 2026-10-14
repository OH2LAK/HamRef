"""Place reference designators on F.SilkS after routing so that they avoid pads, vias, silk outlines,
other texts, the logo and the board edge.  Usage: silk_pass.py <in.kicad_pcb> <out.kicad_pcb>"""
import sys, pcbnew
from pcbnew import FromMM as mm, VECTOR2I
OX, OY, BW, BH = 50.0, 40.0, 100.0, 80.0
SIZE, THICK = 0.8, 0.15
b = pcbnew.LoadBoard(sys.argv[1])
F = pcbnew.F_SilkS
def R(bb, m=0.0):
    return (bb.GetLeft()/1e6 - OX - m, bb.GetTop()/1e6 - OY - m, bb.GetRight()/1e6 - OX + m, bb.GetBottom()/1e6 - OY + m)
def hit(a, c): return not (a[2] <= c[0] or c[2] <= a[0] or a[3] <= c[1] or c[3] <= a[1])
def P(x, y): return VECTOR2I(mm(OX + x), mm(OY + y))

_removed = []
for d in [x for x in b.GetDrawings() if x.GetClass() == 'PCB_TEXT' and x.GetText().startswith('REAR:')]:
    b.Remove(d); _removed.append(d)   # old combined rear-panel note (replaced by per-connector labels); keep a reference to avoid SWIG GC
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
import numpy as np
_pts = []
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == pcbnew.F_Cu:
        x0, y0, x1, y1 = t.GetStart().x/1e6 - OX, t.GetStart().y/1e6 - OY, t.GetEnd().x/1e6 - OX, t.GetEnd().y/1e6 - OY
        n = max(2, int(((x1-x0)**2 + (y1-y0)**2) ** 0.5 / 0.25))
        for k in range(n + 1): _pts.append((x0 + (x1-x0)*k/n, y0 + (y1-y0)*k/n, t.GetWidth()/2e6))
TR = np.array(_pts) if _pts else np.zeros((0, 3))
def on_track(bb):
    if not len(TR): return False
    m = (TR[:, 0] + TR[:, 2] > bb[0]) & (TR[:, 0] - TR[:, 2] < bb[2]) & (TR[:, 1] + TR[:, 2] > bb[1]) & (TR[:, 1] - TR[:, 2] < bb[3])
    return bool(m.any())
logo = None
for d in b.GetDrawings():
    if d.GetLayer() != F: continue
    if d.GetClass() == 'PCB_SHAPE':
        r = R(d.GetBoundingBox())
        logo = r if logo is None else (min(logo[0], r[0]), min(logo[1], r[1]), max(logo[2], r[2]), max(logo[3], r[3]))
    else: obst.append(R(d.GetBoundingBox(), 0.3))
if logo: obst.append((logo[0] - 0.6, logo[1] - 0.6, logo[2] + 0.6, logo[3] + 0.6))

MANUAL = {'OSC5A2B02': (46.0, 35.4)}
def style(r, size):
    r.SetVisible(True); r.SetLayer(F); r.SetTextSize(VECTOR2I(mm(size), mm(size))); r.SetTextThickness(mm(THICK))
def try_place(fp, cands):
    r = fp.Reference()
    for avoid_tracks, (ang, x, y) in [(True, c) for c in cands[:49]] + [(False, c) for c in cands]:   # first choice: close and off the tracks
        r.SetTextAngleDegrees(ang); r.SetPosition(P(x, y)); bb = R(r.GetBoundingBox(), 0.12)
        if avoid_tracks and on_track(bb): continue
        if bb[0] > 1.0 and bb[1] > 1.0 and bb[2] < BW - 1.0 and bb[3] < BH - 1.0 and not any(hit(bb, o) for o in obst):
            obst.append(bb); return True
    return False
def body(fp):
    l, t, r_, bt = 1e9, 1e9, -1e9, -1e9
    for pad in fp.Pads():
        q = R(pad.GetBoundingBox()); l, t, r_, bt = min(l, q[0]), min(t, q[1]), max(r_, q[2]), max(bt, q[3])
    q = R(fp.GetBoundingBox(False, False)); return (min(l, q[0]), min(t, q[1]), max(r_, q[2]), max(bt, q[3]))
def area(fp): q = body(fp); return (q[2]-q[0])*(q[3]-q[1])


# ---- function labels for connectors, jumpers and test points ------------------------------
LBL = 0.8
def new_text(s, ang):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(F)
    t.SetTextSize(VECTOR2I(mm(LBL), mm(LBL))); t.SetTextThickness(mm(THICK)); t.SetTextAngleDegrees(ang); return t
def put_text(s, cands, ang=0):
    t = new_text(s, ang)
    for avoid_tracks in (True, False):          # prefer a spot that is not on top of a track
        for x, y in cands:
            t.SetPosition(P(x, y)); bb = R(t.GetBoundingBox(), 0.12)
            if bb[0] > 1.0 and bb[1] > 1.0 and bb[2] < BW - 1.0 and bb[3] < BH - 1.0 and not any(hit(bb, o) for o in obst) \
                    and not (avoid_tracks and on_track(bb)):
                b.Add(t); obst.append(bb); return True
    if cands:
        t.SetPosition(P(*cands[0])); bb = R(t.GetBoundingBox(), 0.12)
        print('  blocked:', s, [round(v, 1) for v in bb], '<-', [[round(v, 1) for v in o] for o in obst if hit(bb, o)][:3])
    return False
def tsize(s, ang):
    t = new_text(s, ang); t.SetPosition(P(50, 50)); q = R(t.GetBoundingBox()); return q[2]-q[0], q[3]-q[1]
def fp_body(fp):
    l, t, r_, bt = 1e9, 1e9, -1e9, -1e9
    for pad in fp.Pads():
        q = R(pad.GetBoundingBox()); l, t, r_, bt = min(l, q[0]), min(t, q[1]), max(r_, q[2]), max(bt, q[3])
    return l, t, r_, bt
def near(fp, s, sides, gaps=(0.3, 0.7, 1.2, 1.9, 2.8), shifts=(0, -1, 1, -2, 2, -3, 3, -4, 4, -6, 6), ang=0):
    w, h = tsize(s, ang); l, t, rr, bt = fp_body(fp); cx, cy = (l+rr)/2, (t+bt)/2; c = []
    for g in gaps:
        for side in sides:
            for sh in shifts:
                if side == 'above': c.append((cx + sh, t - g - h/2))
                if side == 'below': c.append((cx + sh, bt + g + h/2))
                if side == 'right': c.append((rr + g + w/2, cy + sh))
                if side == 'left': c.append((l - g - w/2, cy + sh))
    return put_text(s, c, ang)
def pin_labels(fp, names):
    ok = True
    pads = sorted([p for p in fp.Pads()], key=lambda p: int(p.GetNumber()))
    for pad, nm in zip(pads, names):
        if not nm: continue
        q = R(pad.GetBoundingBox()); w, h = tsize(nm, 0); cy = (q[1]+q[3])/2
        c = [(q[2] + g + w/2, cy) for g in (0.9, 1.2, 1.6)] + [(q[0] - g - w/2, cy) for g in (0.9, 1.2, 1.6)]
        ok &= put_text(nm, c)
    return ok
byref = {f.GetReference(): f for f in fps}
miss = []
def lab(ok, what):
    if not ok: miss.append(what)
# rear-panel connector names (above each connector, on the board edge side)
for ref, s_, x in (('J2', 'GNSS ANT', 11.0), ('J3', 'REF 10M', 30.0), ('J4', '1PPS', 47.0), ('J5', 'AUX', 64.0)):
    lab(put_text(s_, [(x + dx, y) for y in (16.2, 16.8, 15.6) for dx in (0, -1.5, 1.5, -3, 3)]), ref)
HDR = {'J1': ('EXT 5V', ['+5V', 'GND']), 'J6': ('OLED', ['GND', '3V3', 'SCL', 'SDA']),
       'J7': ('ENCODER', ['A', 'B', 'SW', 'GND']), 'J8': ('LEDS', ['5V', 'DIN', 'GND']),
       'J9': ('GNSS RST', []), 'J10': ('MCU RST', ['RUN', 'GND']),
       'J11': ('SPARE', ['GP17', 'GP18', 'GP19', 'GP20', '3V3', 'GND', '5V']),
       'JP2': ('OCXO ON', ['EN', '5V'])}
for ref, (title, pins) in HDR.items():
    lab(pin_labels(byref[ref], pins), ref + ' pins')
    lab(near(byref[ref], title, ('above', 'right', 'below', 'left')), ref + ' title')
# jumpers that sit in tight spots: one descriptive line each
lab(near(byref['JP1'], 'SEL 1-2 USB 2-3 EXT', ('below',), shifts=tuple(x*0.5 for x in range(-24, 25)), ang=0), 'JP1')
lab(put_text('1PPS 1-2 GNSS 2-3 MCU', [(46.0, 44.6), (46.0, 46.0), (46.0, 47.4)]) or near(byref['JP3'], '1PPS SRC', ('above', 'below', 'right', 'left')), 'JP3')
lab(near(byref['JP2'], 'EN=short: OCXO always on', ('right', 'below', 'above')), 'JP2 note')
# test point net names, vertical above each pad
TPN = {'TP1': '5V', 'TP2': '5V_OX', 'TP3': '3V3_GN', 'TP4': '3V3', 'TP5': '5V_DAC', 'TP6': 'GND', 'TP7': 'GTXD',
       'TP8': 'GRXD', 'TP9': 'PPS_G', 'TP10': 'EFC', 'TP11': 'OCXO', 'TP12': 'AUX', 'TP13': 'PPS', 'TP14': 'FLT'}
for i, (ref, nm) in enumerate(TPN.items()):
    if ref in ('TP2', 'TP5', 'TP9'):
        lab(near(byref[ref], nm, ('right', 'left', 'above', 'below')), ref); continue
    l_, t_, r_, bt_ = fp_body(byref[ref]); x = (l_ + r_) / 2
    rows = [74.8, 72.9] if i % 2 == 0 else [72.9, 74.8]     # two staggered rows above the test points
    lab(put_text(nm, [(x, rows[0]), (x, rows[1]), (x, 71.0)]), ref)
print('labels not placed:', miss)

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
