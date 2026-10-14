"""Generate HamREF proto v0.1 PCB (KiCad 7 pcbnew API): placement, zones, manual RF trace.
Usage: build_pcb.py <project_dir>   (expects parts.json + n.net in tools/ or project dir)"""
import sys, os, re, json, math
import numpy as np
import pcbnew
from pcbnew import FromMM as mm, VECTOR2I

PROJ = sys.argv[1]
PARTS = json.load(open(os.path.join(PROJ, 'parts.json')))
NETL = open(os.path.join(PROJ, 'n.net')).read()
HERE = os.path.dirname(os.path.abspath(__file__))
FPDIR = '/usr/share/kicad/footprints'
OX, OY = 50.0, 40.0           # board origin on sheet
BW, BH = 100.0, 100.0         # board size

# ---- netlist: (ref,pin)->net
pin_net = {}
for name, body in re.findall(r'\(net \(code "\d+"\) \(name "([^"]*)"\)((?:\s*\(node [^\n]*)+)', NETL):
    if name.startswith('unconnected'): continue
    for ref, pin in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', body):
        pin_net[(ref, pin)] = name

board = pcbnew.BOARD()
board.SetCopperLayerCount(4)
ds = board.GetDesignSettings()
ds.SetBoardThickness(mm(1.6))
nets = {}
def net(name):
    if name not in nets:
        ni = pcbnew.NETINFO_ITEM(board, name); board.Add(ni); nets[name] = ni
    return nets[name]
for n in sorted(set(pin_net.values())): net(n)

def P(x, y): return VECTOR2I(mm(float(OX + x)), mm(float(OY + y)))
def load_fp(fpid):
    lib, name = fpid.split(':')
    d = os.path.join(PROJ, 'hamref.pretty') if lib == 'HamREF' else f'{FPDIR}/{lib}.pretty'
    return pcbnew.FootprintLoad(d, name)

fps = {}
for p in PARTS:
    fp = load_fp(p['fp'])
    fp.SetReference(p['ref']); fp.SetValue(p['value'])
    for pad in fp.Pads():
        n = pin_net.get((p['ref'], pad.GetNumber()))
        if n: pad.SetNet(net(n))
    fps[p['ref']] = fp
    board.Add(fp)
# hide values to keep silk clean
for fp in fps.values():
    fp.Value().SetVisible(False)

def bbox_mm(fp):
    bb = fp.GetBoundingBox(False, False)
    l, t, r, b = bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()
    try:
        cy = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
        if cy.GetWidth() > 0: l, t, r, b = min(l, cy.GetLeft()), min(t, cy.GetTop()), max(r, cy.GetRight()), max(b, cy.GetBottom())
    except Exception: pass
    return (l/1e6 - OX, t/1e6 - OY, r/1e6 - OX, b/1e6 - OY)
def place(ref, x, y, rot=0):
    fp = fps[ref]; fp.SetOrientationDegrees(rot); fp.SetPosition(P(x, y))
def pad_pos(ref, num):
    for pad in fps[ref].Pads():
        if pad.GetNumber() == str(num):
            v = pad.GetPosition(); return (v.x/1e6 - OX, v.y/1e6 - OY)
def pads_of(ref): return [(p.GetNumber(), (p.GetPosition().x/1e6-OX, p.GetPosition().y/1e6-OY), p.GetNetname()) for p in fps[ref].Pads()]

# ---- fixed anchors -------------------------------------------------------
ref_by_val = {}
for p in PARTS: ref_by_val.setdefault(p['value'], []).append(p['ref'])
def R_(val, i=0): return ref_by_val[val][i]
SMA, MOD = R_('SMA ANT'), R_('RP2350-Plus'); LEA = R_('LEA-M8S-0'); OCXO = R_('OSC5A2B02')
BNC_REF, BNC_PPS, BNC_AUX = R_('BNC REF OUT'), R_('BNC 1PPS OUT'), R_('BNC AUX OUT')
SI = R_('Si5351C-B-GM'); DAC = R_('AD5693R'); TPS = R_('TPS2065C'); LDO = R_('LP5907-3.3')
holes = ref_by_val['MountingHole_M3']
place(holes[0], 4, 4); place(holes[1], 4, 96); place(holes[2], 96, 96); place(holes[3], 96, 60)
place(SMA, 14, 10)
place(BNC_REF, 28, 11); place(BNC_PPS, 45.5, 11); place(BNC_AUX, 63, 11)
place(MOD, 86, 27.5)
# LEA: pick rotation that puts RF_IN (pad 16) closest to the SMA centre pin
best = None
for rot in (0, 90, 180, 270):
    place(LEA, 17, 36, rot)
    a = pad_pos(LEA, 16); b = pad_pos(SMA, 1)
    d = math.hypot(a[0]-b[0], a[1]-b[1])
    if best is None or d < best[0]: best = (d, rot)
LEA_ROT = best[1]; place(LEA, 17, 36, LEA_ROT)
# OCXO: choose rotation putting pads 1 and 3 toward the upper right (towards buffers / Si5351)
best = None
for rot in (0, 90, 180, 270):
    place(OCXO, 46, 43, rot)
    p1 = pad_pos(OCXO, 1); p3 = pad_pos(OCXO, 3)
    score = -(p1[1] + p3[1]) / 2 + 0.7 * (p1[0] + p3[0]) / 2
    if best is None or score > best[0]: best = (score, rot)
OCXO_ROT = best[1]; place(OCXO, 46, 43, OCXO_ROT)
place(SI, 65, 31); place(LDO, 36, 23)
for ref, xy in {R_('J OLED 0.91in I2C'): (58, 79), R_('J ENCODER'): (66, 79), R_('J LEDS (2x WS2812B)'): (73, 79),
                R_('J RESET GNSS (short=reset)'): (79, 79), R_('J RUN (short=MCU reset)'): (84, 79), R_('J SPARE GPIO'): (92, 74)}.items():
    place(ref, *xy)
place(R_('5V_EXT'), 8, 84); place(R_('JP1 PWR SEL'), 16, 84)

# ---- occupancy grid (0.25 mm) -------------------------------------------
G = 0.25
NX, NY = int(BW/G), int(BH/G)
occ = np.zeros((NY, NX), dtype=bool)
def mark(x0, y0, x1, y1, m=0.0):
    i0 = max(0, int((x0-m)/G)); i1 = min(NX, int(math.ceil((x1+m)/G)))
    j0 = max(0, int((y0-m)/G)); j1 = min(NY, int(math.ceil((y1+m)/G)))
    if i1 > i0 and j1 > j0: occ[j0:j1, i0:i1] = True
# board margin
mark(-1, -1, BW+1, 1.5); mark(-1, BH-1.5, BW+1, BH+1); mark(-1, -1, 1.5, BH+1); mark(BW-1.5, -1, BW+1, BH+1)
placed = set([holes[0], holes[1], holes[2], holes[3], SMA, BNC_REF, BNC_PPS, BNC_AUX, MOD, LEA, OCXO, SI, LDO] +
             [R_(v) for v in ('J OLED 0.91in I2C','J ENCODER','J LEDS (2x WS2812B)','J RESET GNSS (short=reset)','J RUN (short=MCU reset)','J SPARE GPIO','5V_EXT','JP1 PWR SEL')])
for ref in placed:
    x0, y0, x1, y1 = bbox_mm(fps[ref]); mark(x0, y0, x1, y1, 0.9)
# module keep-out for components: whole module footprint
x0, y0, x1, y1 = bbox_mm(fps[MOD]); mark(x0, y0, x1, y1, 0.5)

def integral(a):
    s = np.zeros((a.shape[0]+1, a.shape[1]+1), dtype=np.int32)
    s[1:, 1:] = a.cumsum(0).cumsum(1); return s
def valid_mask(w, h):
    s = integral(occ); wi = int(math.ceil(w/G)); hi = int(math.ceil(h/G))
    m = np.zeros((NY, NX), dtype=bool)
    # window top-left (j,i) covering [j:j+hi, i:i+wi]
    J = NY - hi + 1; I = NX - wi + 1
    tot = s[hi:hi+J, wi:wi+I] - s[0:J, wi:wi+I] - s[hi:hi+J, 0:I] + s[0:J, 0:I]
    m[:J, :I] = (tot == 0)
    return m, wi, hi

yy, xx = np.mgrid[0:NY, 0:NX]
cx_grid = (xx + 0.5) * G; cy_grid = (yy + 0.5) * G

def target_points(ref, anchor, avoid_gnd=True):
    """pads of anchor sharing a net with part (excluding GND), else all anchor pads"""
    mine = {p.GetNetname() for p in fps[ref].Pads() if p.GetNetname()}
    pts = [pos for (num, pos, nn) in pads_of(anchor) if nn in mine and nn != 'GND']
    if not pts: pts = [pos for (num, pos, nn) in pads_of(anchor)]
    return pts

# net-based anchor override: part's non-bus nets touching exactly one non-passive part
def is_passive(ref):
    p = next(q for q in PARTS if q['ref'] == ref)
    return p['lib'].split(':')[1] in ('R', 'C', 'C_Polarized', 'FerriteBead', 'D_Schottky', 'D_TVS', 'Polyfuse', 'Thermistor_NTC', 'TestPoint')
net_members = {}
for (ref, pin), n in pin_net.items(): net_members.setdefault(n, set()).add(ref)
def anchor_for(p):
    cands = {}
    for pad in fps[p['ref']].Pads():
        n = pad.GetNetname()
        if not n or n == 'GND': continue
        mem = [r for r in net_members.get(n, ()) if r != p['ref'] and not is_passive(r) and not r.startswith('H')]
        if 0 < len(mem) <= 2:
            for r in mem: cands[r] = cands.get(r, 0) + 1
    if cands: return max(cands, key=cands.get)
    return p['near']

def place_free(ref, anchor, minfrac=0.0):
    x0, y0, x1, y1 = bbox_mm(fps[ref]); w = x1-x0+1.2; h = y1-y0+1.2
    m, wi, hi = valid_mask(w, h)
    tp = target_points(ref, anchor)
    d = np.full((NY, NX), 1e9)
    # window centre
    cwx = cx_grid + (wi*G)/2 - G/2; cwy = cy_grid + (hi*G)/2 - G/2
    for (tx, ty) in tp:
        d = np.minimum(d, np.hypot(cwx - tx, cwy - ty))
    d[~m] = 1e9
    j, i = np.unravel_index(np.argmin(d), d.shape)
    if d[j, i] >= 1e9: raise SystemExit(f'no space for {ref}')
    # footprint origin such that bbox centre lands at window centre
    ccx = (x0+x1)/2; ccy = (y0+y1)/2     # bbox centre relative origin?  bbox_mm is absolute (placed at current pos)
    cur = fps[ref].GetPosition(); px = cur.x/1e6 - OX; py = cur.y/1e6 - OY
    offx = ccx - px; offy = ccy - py
    nx = i*G + wi*G/2 - offx; ny = j*G + hi*G/2 - offy
    place(ref, nx, ny)
    x0, y0, x1, y1 = bbox_mm(fps[ref]); mark(x0, y0, x1, y1, 0.5)

# special: anchors placed relative to pads
def place_near_pad(ref, tgt_ref, tgt_pad, rot=0):
    anchor_pt = pad_pos(tgt_ref, tgt_pad)
    place(ref, *anchor_pt, rot)
    x0, y0, x1, y1 = bbox_mm(fps[ref]); w = x1-x0+1.2; h = y1-y0+1.2
    m, wi, hi = valid_mask(w, h)
    d = np.hypot(cx_grid + wi*G/2 - G/2 - anchor_pt[0], cy_grid + hi*G/2 - G/2 - anchor_pt[1]); d[~m] = 1e9
    j, i = np.unravel_index(np.argmin(d), d.shape)
    cur = fps[ref].GetPosition(); px = cur.x/1e6 - OX; py = cur.y/1e6 - OY
    offx = (x0+x1)/2 - px; offy = (y0+y1)/2 - py
    place(ref, i*G + wi*G/2 - offx, j*G + hi*G/2 - offy, rot)
    x0, y0, x1, y1 = bbox_mm(fps[ref]); mark(x0, y0, x1, y1, 0.4); placed.add(ref)

place_near_pad(TPS, OCXO, 5)
place_near_pad(DAC, OCXO, 3)
buf33 = R_('74LVC1G17', 1); buf_gnss = R_('74LVC1G17', 0); buf5 = R_('74AHCT1G125', 0); pps_buf = R_('74LVC1G125'); led_buf = R_('74AHCT1G125', 1)
place_near_pad(buf33, OCXO, 1); place_near_pad(buf5, OCXO, 1)
place_near_pad(pps_buf, BNC_PPS, 1); place_near_pad(R_('JP3 1PPS SRC (1-2 GNSS, 2-3 MCU)'), pps_buf, 2)
place_near_pad(buf_gnss, LEA, 28)
place_near_pad(led_buf, R_('J LEDS (2x WS2812B)'), 2)
# remaining non-passive anchors: JP2 near TPS
place_near_pad(R_('JP2 OCXO FORCE-ON'), TPS, 4)

# ---- passives / TPs -----------------------------------------------------
rest = [p for p in PARTS if p['ref'] not in placed and p['ref'] not in (TPS, DAC, buf33, buf5, pps_buf, buf_gnss, led_buf)]
tps = [p for p in rest if p['lib'].endswith('TestPoint')]
rest = [p for p in rest if p not in tps]
# place bigger first
def area(p):
    x0, y0, x1, y1 = bbox_mm(fps[p['ref']]); return (x1-x0)*(y1-y0)
rest.sort(key=lambda p: -area(p))
for p in rest:
    a = anchor_for(p)
    if a is None or a not in fps: a = LEA
    place_free(p['ref'], a)
# test points: row along the bottom edge
for i, p in enumerate(tps):
    place(p['ref'], 9 + i*5.4, 97.2)

# ---- outline ------------------------------------------------------------
edge = pcbnew.PCB_SHAPE(board); edge.SetShape(pcbnew.SHAPE_T_RECT)
edge.SetStart(P(0, 0)); edge.SetEnd(P(BW, BH)); edge.SetLayer(pcbnew.Edge_Cuts); edge.SetWidth(mm(0.1)); board.Add(edge)

# ---- zones --------------------------------------------------------------
def add_zone(layer, netname, inset=0.6):
    z = pcbnew.ZONE(board); z.SetLayer(layer); z.SetNet(net(netname))
    o = pcbnew.SHAPE_LINE_CHAIN()
    for (x, y) in [(inset, inset), (BW-inset, inset), (BW-inset, BH-inset), (inset, BH-inset)]: o.Append(mm(OX+x), mm(OY+y))
    o.SetClosed(True); z.Outline().AddOutline(o)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); z.SetMinThickness(mm(0.2))
    board.Add(z); return z
add_zone(pcbnew.In1_Cu, 'GND')
if os.environ.get('IN2_3V3'): add_zone(pcbnew.In2_Cu, '3V3')
if os.environ.get('BCU_POUR'): add_zone(pcbnew.B_Cu, 'GND')
# keep-out under the module body (no tracks/vias on top between the pad rows)
ko = pcbnew.ZONE(board); ko.SetIsRuleArea(True)
ko.SetLayerSet(pcbnew.LSET(pcbnew.F_Cu)); ko.SetDoNotAllowTracks(True); ko.SetDoNotAllowVias(True); ko.SetDoNotAllowPads(False)
ko.SetDoNotAllowCopperPour(False); ko.SetDoNotAllowFootprints(False)
mx, my = pad_pos(MOD, 1)[0] + 3.0, pad_pos(MOD, 1)[1] - 1.0
o = pcbnew.SHAPE_LINE_CHAIN()
x_l = pad_pos(MOD, 1)[0] + 1.75; x_r = pad_pos(MOD, 40)[0] - 1.75
for (x, y) in [(x_l, 1.0), (x_r, 1.0), (x_r, 54), (x_l, 54)]: o.Append(mm(OX+x), mm(OY+y))
o.SetClosed(True); ko.Outline().AddOutline(o); board.Add(ko)

# edge keep-out bands (no tracks/vias within 0.5 mm of the outline)
for (x0_, y0_, x1_, y1_) in [(-1, -1, BW+1, 0.5), (-1, BH-0.5, BW+1, BH+1), (-1, -1, 0.5, BH+1), (BW-0.5, -1, BW+1, BH+1)]:
    z = pcbnew.ZONE(board); z.SetIsRuleArea(True)
    ls_ = pcbnew.LSET()
    for L_ in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu): ls_.AddLayer(L_)
    z.SetLayerSet(ls_); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False)
    z.SetDoNotAllowCopperPour(False); z.SetDoNotAllowFootprints(False)
    ol = pcbnew.SHAPE_LINE_CHAIN()
    for (x, y) in [(x0_, y0_), (x1_, y0_), (x1_, y1_), (x0_, y1_)]: ol.Append(mm(OX+x), mm(OY+y))
    ol.SetClosed(True); z.Outline().AddOutline(ol); board.Add(z)
# ---- net classes ---------------------------------------------------------
ns = ds.m_NetSettings
ns.m_DefaultNetClass.SetTrackWidth(mm(0.2)); ns.m_DefaultNetClass.SetClearance(mm(0.2))
ns.m_DefaultNetClass.SetViaDiameter(mm(0.6)); ns.m_DefaultNetClass.SetViaDrill(mm(0.3))
pw = pcbnew.NETCLASS('Power'); pw.SetTrackWidth(mm(0.5)); pw.SetClearance(mm(0.2)); pw.SetViaDiameter(mm(0.8)); pw.SetViaDrill(mm(0.4))
ns.m_NetClasses['Power'] = pw
for n in ('5V_MAIN', '5V_OCXO', '5V_USB', '5V_EXT', 'VSYS', 'VBUS_MOD', '3V3', '3V3_GNSS'):
    if n in nets: nets[n].SetNetClass(pw)
ds.m_MinClearance = mm(0.15)
try: ds.m_CopperEdgeClearance = mm(0.3)
except Exception: pass

# ---- RF trace (50 ohm microstrip on F.Cu over In1 GND, ~0.37 mm for 0.21 mm prepreg) -----
a = pad_pos(SMA, 1); b = pad_pos(LEA, 16)
def seg(p, q, w, layer, netname):
    t = pcbnew.PCB_TRACK(board); t.SetStart(P(*p)); t.SetEnd(P(*q)); t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(net(netname)); t.SetLocked(True); board.Add(t)
# two-segment route with a 45 deg-ish dogleg
mid = (a[0], b[1]) if abs(a[0]-b[0]) < abs(a[1]-b[1]) else (b[0], a[1])
seg(a, mid, 0.37, pcbnew.F_Cu, 'GNSS_RF'); seg(mid, b, 0.37, pcbnew.F_Cu, 'GNSS_RF')


# ---- GND fan-out vias (stitch SMD GND pads to the In1 plane before autorouting) --------
def rect_dist(px, py, r):
    dx = max(r[0]-px, 0, px-r[2]); dy = max(r[1]-py, 0, py-r[3]); return math.hypot(dx, dy)
pad_rects = []
for ref, fp in fps.items():
    for pad in fp.Pads():
        bb = pad.GetBoundingBox()
        pad_rects.append((bb.GetLeft()/1e6-OX, bb.GetTop()/1e6-OY, bb.GetRight()/1e6-OX, bb.GetBottom()/1e6-OY, pad.GetNetname(), pad.GetAttribute()))
vias_xy = []
VIA_D, VIA_DR = 0.6, 0.3
def add_via(x, y):
    v = pcbnew.PCB_VIA(board); v.SetPosition(P(x, y)); v.SetNet(net('GND')); v.SetWidth(mm(VIA_D)); v.SetDrill(mm(VIA_DR))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetLocked(True); board.Add(v); vias_xy.append((x, y))
def via_ok(x, y, own):
    if x < 1.2 or y < 1.2 or x > BW-1.2 or y > BH-1.2: return False
    for r in pad_rects:
        if r[4] == 'GND' and r is own: continue
        d = rect_dist(x, y, r)
        need = 0.3 + (0.2 if r[4] != 'GND' else 0.0) + 0.05
        if r[4] != 'GND' and d < need: return False
        if r[4] == 'GND' and d < 0.0 and r is not own: pass
    for (vx, vy) in vias_xy:
        if math.hypot(x-vx, y-vy) < 0.9: return False
    # keep out of module body region
    if x_l - 0.5 < x < x_r + 0.5 and 0.5 < y < 54.5: return False
    return True
def via_ok_pt(x, y, own):
    for r in pad_rects:
        if r[4] == 'GND': continue
        if rect_dist(x, y, r) < 0.125 + 0.2 + 0.05: return False
    return True
nfan = 0; nfail = []
for ref, fp in fps.items():
    if ref in holes: continue
    for pad in fp.Pads():
        if pad.GetNetname() != 'GND' or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD: continue
        bb = pad.GetBoundingBox(); w = bb.GetWidth()/1e6; h = bb.GetHeight()/1e6
        cx = bb.GetCenter().x/1e6 - OX; cy = bb.GetCenter().y/1e6 - OY
        own = next(r for r in pad_rects if abs((r[0]+r[2])/2-cx) < 1e-3 and abs((r[1]+r[3])/2-cy) < 1e-3 and r[4] == 'GND')
        if min(w, h) >= 2.0:
            for ox_, oy_ in ((-0.7, -0.7), (0.7, -0.7), (-0.7, 0.7), (0.7, 0.7)):
                add_via(cx + ox_, cy + oy_); nfan += 1
            continue
        if min(w, h) >= 1.6 and via_ok(cx, cy, own):
            add_via(cx, cy); nfan += 1; continue
        done = False
        for d in [max(w, h)/2 + 0.45 + 0.25*k for k in range(0, 14)]:
            for ang in range(0, 360, 20):
                x = cx + d*math.cos(math.radians(ang)); y = cy + d*math.sin(math.radians(ang))
                if via_ok(x, y, own) and all(via_ok_pt(cx+(x-cx)*t, cy+(y-cy)*t, own) for t in (0.25, 0.5, 0.75)):
                    seg((cx, cy), (x, y), 0.25, pcbnew.F_Cu, 'GND'); add_via(x, y); nfan += 1; done = True; break
            if done: break
        if not done: nfail.append((ref, pad.GetNumber()))
print('GND fanout vias', nfan, 'failed', nfail)

def escape_via(ref, padnum, netname, dist=1.0):
    pc = pad_pos(ref, padnum); ic = fps[ref].GetPosition(); icx = ic.x/1e6 - OX; icy = ic.y/1e6 - OY
    dx, dy = pc[0]-icx, pc[1]-icy; L = math.hypot(dx, dy) or 1.0
    # snap to dominant axis
    if abs(dx) > abs(dy): dx, dy = math.copysign(1, dx), 0
    else: dx, dy = 0, math.copysign(1, dy)
    q = (pc[0] + dx*dist, pc[1] + dy*dist)
    seg(pc, q, 0.2, pcbnew.F_Cu, netname)
    v = pcbnew.PCB_VIA(board); v.SetPosition(P(*q)); v.SetNet(net(netname)); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetLocked(True); board.Add(v)
escape_via(DAC, 1, '5V_DAC', 1.1)
# same-net neighbouring pads that cannot be routed between: tie directly (DAC VLOGIC/RESET)
a = pad_pos(DAC, 2); c = pad_pos(DAC, 3)
seg(a, c, 0.25, pcbnew.F_Cu, '3V3')
# ---- 3D models -----------------------------------------------------------
# Stock KiCad footprints reference ${KICAD6_3DMODEL_DIR}; point them at the variable that the
# installed KiCad actually defines (override with MODEL_VAR=KICAD9_3DMODEL_DIR etc.).
MODEL_VAR = os.environ.get('MODEL_VAR', 'KICAD10_3DMODEL_DIR')
MODEL_EXT = os.environ.get('MODEL_EXT', 'step')   # official libs ship .step (master) and .wrl; use MODEL_EXT=wrl if models are missing
def wrl_box(path, boxes):
    """boxes: list of (cx, cy, z0, w, h, d, (r,g,b)) in mm. VRML units are 0.1 inch; VRML +y = footprint -y (board up)."""
    u = 1 / 2.54
    out = ['#VRML V2.0 utf8']
    for cx, cy, z0, w, h, d, col in boxes:
        out.append('Transform { translation %.5f %.5f %.5f children Shape { appearance Appearance { material Material '
                   '{ diffuseColor %.2f %.2f %.2f specularColor 0.4 0.4 0.4 shininess 0.3 } } geometry Box { size %.5f %.5f %.5f } } }'
                   % (cx*u, cy*u, (z0 + d/2)*u, col[0], col[1], col[2], w*u, h*u, d*u))
    open(path, 'w').write('\n'.join(out) + '\n')
os.makedirs(os.path.join(PROJ, 'hamref.3dshapes'), exist_ok=True)
SH = os.path.join(PROJ, 'hamref.3dshapes')
wrl_box(os.path.join(SH, 'OCXO_OSC5A2B02_EST.wrl'), [(0, 0, 0.5, 25.4, 25.4, 10.2, (0.75, 0.75, 0.78))])
wrl_box(os.path.join(SH, 'RP2350-Plus.wrl'), [(0, 0, 0.5, 21.0, 51.0, 1.0, (0.05, 0.35, 0.15)),
                                              (0, 23.5, 1.5, 9.0, 7.4, 3.2, (0.8, 0.8, 0.82)),
                                              (0, -6.0, 1.5, 12.0, 12.0, 1.0, (0.1, 0.1, 0.1))])
def add_model(ref, name):
    m = pcbnew.FP_3DMODEL(); m.m_Filename = '${KIPRJMOD}/hamref.3dshapes/' + name
    m.m_Scale = pcbnew.VECTOR3D(1, 1, 1); m.m_Rotation = pcbnew.VECTOR3D(0, 0, 0); m.m_Offset = pcbnew.VECTOR3D(0, 0, 0)
    fps[ref].Models().push_back(m)
add_model(OCXO, 'OCXO_OSC5A2B02_EST.wrl'); add_model(MOD, 'RP2350-Plus.wrl')

# ---- silk ----------------------------------------------------------------
F_SILK = pcbnew.F_SilkS
def txt(s, x, y, size=1.2, layer=F_SILK, thick=None):
    t = pcbnew.PCB_TEXT(board); t.SetText(s); t.SetPosition(P(x, y)); t.SetLayer(layer)
    t.SetTextSize(VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(thick or size*0.15)); board.Add(t); return t
# footprint-level warning texts: move from silk to fab layer (the board gets one tidy note instead)
for fp in fps.values():
    for g in fp.GraphicalItems():
        if isinstance(g, pcbnew.PCB_TEXT) or g.GetClass() == 'FP_TEXT':
            try:
                if 'ESTIMATED' in g.GetText(): g.SetLayer(pcbnew.F_Fab)
            except Exception: pass


txt('HamREF proto v0.1', 64, 92.2, 1.2)
txt('REAR: SMA ANT / BNC REF / 1PPS / AUX', 40, 2.2, 0.9)
txt('OCXO OSC5A2B02', 46, 41.4, 0.8); txt('FOOTPRINT ESTIMATED', 46, 43.2, 0.8); txt('- VERIFY BEFORE ORDER -', 46, 45.0, 0.8)

# logo (HamREF by OH2LAK + satellite), vectorised from the enclosure mockup by make_logo.py
LOGO_X, LOGO_Y, LOGO_W = 6.0, 58.0, 32.0
lg = json.load(open(os.path.join(HERE, 'logo', 'hamref_logo.json')))
k = LOGO_W / lg['w']
def lpt(p): return pcbnew.VECTOR2I(mm(OX + LOGO_X + p[0]*k), mm(OY + LOGO_Y + p[1]*k))
byid = {c['id']: c for c in lg['contours']}
for c in lg['contours']:
    if c['hole']: continue
    ps = pcbnew.SHAPE_POLY_SET(); ps.NewOutline()
    for p in c['pts']: v = lpt(p); ps.Append(v.x, v.y, 0)
    for h in lg['contours']:
        if h['hole'] and h['parent'] == c['id']:
            hi = ps.NewHole(0)
            for p in h['pts']: v = lpt(p); ps.Append(v.x, v.y, 0, hi)
    sh = pcbnew.PCB_SHAPE(board); sh.SetShape(pcbnew.SHAPE_T_POLY); sh.SetFilled(True)
    sh.SetLayer(F_SILK); sh.SetWidth(0); sh.SetPolyShape(ps); board.Add(sh)

# reference designators are placed by silk_pass.py after routing (needs final vias/tracks)

out = os.path.join(PROJ, 'hamref_proto_v0_1.kicad_pcb')
pcbnew.SaveBoard(out, board)
# (pcbnew returns model entries by value, so rewrite the paths in the saved file)
txt_ = open(out).read()
txt_ = re.sub(r'\$\{KICAD\d+_3DMODEL_DIR\}([^"]*?)\.wrl', lambda m: '${%s}%s.%s' % (MODEL_VAR, m.group(1), MODEL_EXT), txt_)
open(out, 'w').write(txt_)
print('saved', out, 'LEA rot', LEA_ROT, 'OCXO rot', OCXO_ROT)
