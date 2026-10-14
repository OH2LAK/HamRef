"""Import a Specctra SES (Freerouting) into a KiCad 7 board via pcbnew API (SES units: 0.1 um, y inverted)."""
import sys, re, pcbnew
from pcbnew import FromMM as mm, VECTOR2I
pcb_in, ses, pcb_out = sys.argv[1:4]
b = pcbnew.LoadBoard(pcb_in)
txt = open(ses).read()
i = txt.find('(network_out'); body = txt[i:]
layers = {'F.Cu': pcbnew.F_Cu, 'In1.Cu': pcbnew.In1_Cu, 'In2.Cu': pcbnew.In2_Cu, 'B.Cu': pcbnew.B_Cu}
nets = {n.GetNetname(): n for n in b.GetNetInfo().NetsByName().values()} if hasattr(b.GetNetInfo(),'NetsByName') else {}
def getnet(name):
    ni = b.FindNet(name); return ni
def pt(x, y): return VECTOR2I(mm(x/10000.0), mm(-y/10000.0))
# split net blocks
def blocks(s, head):
    out = []; k = 0
    while True:
        k = s.find('(' + head, k)
        if k < 0: break
        d = 0; j = k
        while True:
            c = s[j]
            if c == '(': d += 1
            elif c == ')':
                d -= 1
                if d == 0: break
            j += 1
        out.append(s[k:j+1]); k = j + 1
    return out
nt = nw = nv = 0
for nb in blocks(body, 'net '):
    m = re.match(r'\(net\s+"?([^"\s)]+)"?', nb)
    name = m.group(1); ni = getnet(name)
    if ni is None: print('unknown net', name); continue
    for w in blocks(nb, 'wire'):
        pm = re.search(r'\(path\s+(\S+)\s+(\d+)\s+([-\d\s]+)\)', w)
        if not pm: continue
        layer = layers[pm.group(1)]; width = int(pm.group(2)) / 10000.0
        nums = list(map(int, pm.group(3).split()))
        pts = list(zip(nums[0::2], nums[1::2]))
        for a, c in zip(pts, pts[1:]):
            if a == c: continue
            t = pcbnew.PCB_TRACK(b); t.SetStart(pt(*a)); t.SetEnd(pt(*c)); t.SetWidth(mm(width)); t.SetLayer(layer); t.SetNet(ni); b.Add(t); nw += 1
    for v in blocks(nb, 'via'):
        vm = re.match(r'\(via\s+"([^"]+)"\s+(-?\d+)\s+(-?\d+)', v)
        pn = vm.group(1); x, y = int(vm.group(2)), int(vm.group(3))
        dm = re.search(r'_(\d+):(\d+)_um', pn)
        via = pcbnew.PCB_VIA(b); via.SetPosition(pt(x, y)); via.SetNet(ni)
        via.SetWidth(mm(int(dm.group(1))/1000.0)); via.SetDrill(mm(int(dm.group(2))/1000.0))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(via); nv += 1
def gpour(layer):
    for z in b.Zones():
        if z.GetLayer() == layer and not z.GetIsRuleArea(): return
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(b.FindNet('GND'))
    ol = pcbnew.SHAPE_LINE_CHAIN()
    for (x, y) in [(1.9, 0.6), (98.1, 0.6), (99.4, 1.9), (99.4, 78.1), (98.1, 79.4), (1.9, 79.4), (0.6, 78.1), (0.6, 1.9)]: ol.Append(mm(50 + x), mm(40 + y))
    ol.SetClosed(True); z.Outline().AddOutline(ol); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); z.SetMinThickness(mm(0.2)); b.Add(z)
gpour(pcbnew.B_Cu); gpour(pcbnew.F_Cu)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
pcbnew.SaveBoard(pcb_out, b)
c = b.GetConnectivity(); c.RecalculateRatsnest()
print('wires', nw, 'vias', nv, 'unrouted pairs', c.GetUnconnectedCount(False))
