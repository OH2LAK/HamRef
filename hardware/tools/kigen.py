"""Minimal KiCad 7 schematic generator on top of kiutils (label-based wiring)."""
import copy, uuid as _uuid, os
from kiutils.schematic import Schematic
from kiutils.symbol import SymbolLib, Symbol
from kiutils.items.common import Position, Effects, Font, Property, Justify
from kiutils.items.schitems import (SchematicSymbol, GlobalLabel, LocalLabel, NoConnect, Connection,
    HierarchicalSheet, SymbolProjectInstance, SymbolProjectPath, HierarchicalSheetInstance,
    HierarchicalSheetProjectInstance, HierarchicalSheetProjectPath, Junction)

SYMDIR = os.environ.get('KICAD_SYMBOL_DIR', '/usr/share/kicad/symbols')
_libcache = {}
def uid(): return str(_uuid.uuid4())

def load_lib(name):
    if name not in _libcache:
        _libcache[name] = SymbolLib.from_file(f'{SYMDIR}/{name}.kicad_sym')
    return _libcache[name]

def get_symbol(lib, name):
    """Return a flattened (no 'extends') copy of a library symbol."""
    if lib == "HamREF":
        from customsyms import CUSTOM
        return copy.deepcopy(CUSTOM[name])
    L = load_lib(lib)
    by = {s.entryName: s for s in L.symbols}
    s = by[name]
    if s.extends:
        parent = copy.deepcopy(by[s.extends])
        # child's properties override
        props = {p.key: p for p in parent.properties}
        for p in s.properties: props[p.key] = p
        parent.properties = list(props.values())
        # rename units: parent unit names start with parent name
        parent.entryName = name
        for u in parent.units:
            if u.entryName and u.entryName.startswith(s.extends):
                u.entryName = name + u.entryName[len(s.extends):]
        parent.extends = None
        s = parent
    return copy.deepcopy(s)

def pin_table(sym, unit=None):
    """{number: (x,y,angle,name,etype)} for unit (None=all units incl. unit 0 shared)."""
    t = {}
    for u in sym.units:
        # unit entryName like Name_U_S ; U=unit number (0 = common)
        un = u.unitId if hasattr(u, 'unitId') else None
        for p in u.pins:
            t.setdefault(p.number, []).append((un, p.position.X, p.position.Y, p.position.angle, p.name, p.electricalType))
    return t

class Sheet:
    def __init__(self, gen, name, filename, paper='A3'):
        self.gen=gen; self.name=name; self.filename=filename
        self.sch = Schematic.create_new()
        self.sch.version = '20230121'
        self.sch.generator = 'hamref-gen'
        self.sch.uuid = uid()
        self.sch.paper.paperSize = paper
        self.sch.libSymbols = []
        self.libids = set()
        self.parts = []   # (ref, libid, value, fp, unit, x, y, pinmap)
        self.sheet_uuid = None  # filled by root
        self.sch.sheetInstances = []
        self.sch.symbolInstances = []
    def _embed(self, lib, name):
        libid = f'{lib}:{name}'
        if libid in self.libids: return libid
        s = get_symbol(lib, name)
        s.libId = libid
        s.entryName = name
        self.sch.libSymbols.append(s)
        self.libids.add(libid)
        return libid
    def add(self, ref, lib, name, value, x, y, pins=None, footprint=None, fields=None,
            dnp=False, unit=1, nc=(), mfr=None, mpn=None, note=None, rot=0, near=None):
        """pins: {pin_number(str): netname}. nc: pin numbers to mark no-connect."""
        libid = self._embed(lib, name)
        sym = get_symbol(lib, name)
        # find pins for the requested unit (unit 0 = shared)
        ptab = []
        for u in sym.units:
            uid_ = u.unitId
            if uid_ in (0, unit) or sym.unitCount in (None,0,1):
                ptab += [(p, uid_) for p in u.pins]
        pins = dict(pins or {})
        for _p, _u in ptab:
            if _p.name == 'GND' and _p.number not in pins and _p.number not in nc: pins[_p.number] = 'GND'
        ss = SchematicSymbol()
        ss.libraryNickname = lib; ss.entryName = name
        ss.position = Position(X=x, Y=y, angle=rot)
        ss.unit = unit; ss.inBom = True; ss.onBoard = True; ss.dnp = bool(dnp)
        ss.uuid = uid()
        base = {p.key: p for p in sym.properties}
        def prop(key, val, dy, hide=False):
            p = Property(key=key, value=val, id=len(ss.properties))
            p.position = Position(X=x, Y=y+dy, angle=0)
            p.effects = Effects(font=Font(height=1.27, width=1.27), hide=hide)
            return p
        ss.properties = [prop('Reference', ref, -3.0), prop('Value', value, 3.0),
                         prop('Footprint', footprint or (base['Footprint'].value if 'Footprint' in base else ''), 0, True),
                         prop('Datasheet', base['Datasheet'].value if 'Datasheet' in base else '', 0, True)]
        for k, v in (fields or {}).items():
            ss.properties.append(prop(k, v, 0, True))
        if mfr: ss.properties.append(prop('Manufacturer', mfr, 0, True))
        if mpn: ss.properties.append(prop('MPN', mpn, 0, True))
        if note: ss.properties.append(prop('Note', note, 0, True))
        # pins uuid map
        for p, _u in ptab: ss.pins[p.number] = uid()
        ss.instances = [SymbolProjectInstance(name=self.gen.project,
            paths=[SymbolProjectPath(sheetInstancePath=self.instance_path, reference=ref, unit=unit)])]
        self.sch.schematicSymbols.append(ss)
        self.parts.append(dict(ref=ref, lib=libid, value=value, fp=footprint, dnp=dnp, mpn=mpn, mfr=mfr, note=note, near=near,
                               sheet=self.name, pins=pins or {}))
        # labels
        pins = pins or {}
        for p, _u in ptab:
            num = p.number
            px, py = p.position.X, p.position.Y
            ang = p.position.angle
            # rotation of the symbol (only 0 supported for labelling except rot 90/180/270 simple)
            import math
            r = math.radians(rot)
            rx = px*math.cos(r) - py*math.sin(r)
            ry = px*math.sin(r) + py*math.cos(r)
            sx, sy = round(x + rx, 4), round(y - ry, 4)
            pang = (ang + rot) % 360
            if num in nc:
                self.sch.noConnects.append(NoConnect(position=Position(X=sx, Y=sy), uuid=uid()))
                continue
            net = pins.get(num)
            if net is None: continue
            self._label(net, sx, sy, pang)
        return ss
    def _label(self, net, x, y, pin_angle):
        # label text extends away from the symbol body
        lab_ang = {0: 180, 180: 0, 90: 270, 270: 90}[pin_angle]
        pw = self.gen.is_power(net)
        eff = Effects(font=Font(height=1.27, width=1.27))
        if lab_ang in (180,):
            eff.justify = Justify(horizontally='right')
        gl = GlobalLabel(text=net, shape='bidirectional', position=Position(X=x, Y=y, angle=lab_ang), effects=eff, uuid=uid())
        # KiCad places global label text relative to the anchor; justification is implied by angle
        gl.effects = Effects(font=Font(height=1.27, width=1.27))
        gl.properties = [Property(key='Intersheetrefs', value='${INTERSHEET_REFS}', id=0,
                position=Position(X=x, Y=y, angle=0), effects=Effects(font=Font(height=1.27,width=1.27), hide=True))]
        self.sch.globalLabels.append(gl)
    def text(self, s, x, y, size=1.8):
        from kiutils.items.schitems import Text
        t = Text(text=s, position=Position(X=x, Y=y), effects=Effects(font=Font(height=size, width=size), justify=Justify(horizontally='left')), uuid=uid())
        self.sch.texts.append(t)

class Gen:
    def __init__(self, project, outdir):
        self.project = project; self.outdir = outdir
        self.sheets = []
        self.root = Schematic.create_new()
        self.root.version = '20230121'; self.root.generator = 'hamref-gen'
        self.root.uuid = uid(); self.root.paper.paperSize = 'A3'
        self.root.libSymbols = []
        self.powernets = set()
    def is_power(self, n): return n in self.powernets
    def sheet(self, name, filename, paper='A3'):
        s = Sheet(self, name, filename, paper)
        sid = uid(); s.sheet_uuid = sid
        s.instance_path = f'/{self.root.uuid}/{sid}'
        self.sheets.append(s)
        return s
    def write(self):
        os.makedirs(self.outdir, exist_ok=True)
        # root with sheet symbols
        x, y = 30, 30
        for i, s in enumerate(self.sheets, start=2):
            hs = HierarchicalSheet()
            hs.position = Position(X=x, Y=y); hs.width = 60; hs.height = 15
            hs.uuid = s.sheet_uuid
            hs.sheetName = Property(key='Sheetname', value=s.name, id=0, position=Position(X=x, Y=y-1.0), effects=Effects(font=Font(height=1.27,width=1.27)))
            hs.fileName = Property(key='Sheetfile', value=s.filename, id=1, position=Position(X=x, Y=y+16.5), effects=Effects(font=Font(height=1.27,width=1.27)))
            hs.instances = [HierarchicalSheetProjectInstance(name=self.project,
                paths=[HierarchicalSheetProjectPath(sheetInstancePath=f'/{self.root.uuid}', page=str(i))])]
            self.root.sheets.append(hs)
            y += 30
        self.root.sheetInstances = [HierarchicalSheetInstance(instancePath='/', page='1')]
        import re
        def fix(path):
            t=open(path).read()
            t=re.sub(r' \(id \d+\)','',t)
            t=t.replace('(stroke (width 0.0))','(stroke (width 0.1524) (type solid))').replace('(fill (color 0 0 0 0))','(fill (color 0 0 0 0.0))')
            t=re.sub(r'(\(property "Sheet(?:name|file)" "[^"]*" \(at [-\d.]+ [-\d.]+)\)',r'\1 0)',t)
            t=re.sub(r'(\(text "[^"]*"\s*\(at [-\d.]+ [-\d.]+)\)',r'\1 0)',t)
            open(path,'w').write(t)
        rp=f'{self.outdir}/{self.project}.kicad_sch'
        self.root.to_file(rp); fix(rp)
        for s in self.sheets:
            s.sch.sheetInstances = []
            p=f'{self.outdir}/{s.filename}'
            s.sch.to_file(p); fix(p)
