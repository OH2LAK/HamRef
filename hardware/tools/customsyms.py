
from kiutils.symbol import Symbol, SymbolPin
from kiutils.items.syitems import SyRect
from kiutils.items.common import Position, Effects, Font, Property, Stroke, Fill

PITCH = 2.54
def _eff(h=1.27, hide=False): return Effects(font=Font(height=h, width=h), hide=hide)

def make_symbol(name, left, right, ref='U', w=25.4, datasheet='', desc=''):
    """left/right: lists of (number, pinname, electrical_type) top->bottom; None = gap."""
    n = max(len(left), len(right))
    h = (n + 1) * PITCH
    top = h / 2
    s = Symbol(entryName=name, pinNames=True, inBom=True, onBoard=True)
    s.pinNamesOffset = 1.016
    def prop(k, v, y, hide=False):
        return Property(key=k, value=v, id=0, position=Position(X=0, Y=y, angle=0), effects=_eff(hide=hide))
    s.properties = [prop('Reference', ref, top + 1.5), prop('Value', name, -top - 1.5),
                    prop('Footprint', '', 0, True), prop('Datasheet', datasheet, 0, True),
                    prop('Description', desc, 0, True)]
    u = Symbol(entryName=f'{name}_1_1', unitId=1, styleId=1)
    u.graphicItems = [SyRect(start=Position(X=-w/2, Y=top), end=Position(X=w/2, Y=-top),
                             stroke=Stroke(width=0.254, type='default'), fill=Fill(type='background'))]
    def mk(num, pname, et, x, y, ang):
        return SymbolPin(electricalType=et, graphicalStyle='line', position=Position(X=x, Y=y, angle=ang), length=2.54,
                         name=pname, nameEffects=_eff(), number=num, numberEffects=_eff())
    for i, p in enumerate(left):
        if p: u.pins.append(mk(p[0], p[1], p[2], -w/2 - 2.54, top - (i + 1) * PITCH, 0))
    for i, p in enumerate(right):
        if p: u.pins.append(mk(p[0], p[1], p[2], w/2 + 2.54, top - (i + 1) * PITCH, 180))
    s.units = [u]
    return s

P = 'passive'; I = 'input'; O = 'output'; B = 'bidirectional'; PW = 'power_in'; PO = 'power_out'
# Waveshare RP2350-Plus, 40 castellated pads in Pico order. Left = pads 1..20, right = pads 40..21
LEFT = [('1','GP0',B),('2','GP1',B),('3','GND',PW),('4','GP2',B),('5','GP3',B),('6','GP4',B),('7','GP5',B),('8','GND',PW),
        ('9','GP6',B),('10','GP7',B),('11','GP8',B),('12','GP9',B),('13','GND',PW),('14','GP10',B),('15','GP11',B),
        ('16','GP12',B),('17','GP13',B),('18','GND',PW),('19','GP14',B),('20','GP15',B)]
RIGHT = [('40','VBUS',PW),('39','VSYS',PW),('38','GND',PW),('37','3V3_EN',I),('36','3V3(OUT)',PO),('35','ADC_VREF',P),
         ('34','GP28',B),('33','GND',PW),('32','GP27',B),('31','GP26',B),('30','RUN',I),('29','GP22',B),('28','GND',PW),
         ('27','GP21',B),('26','GP20',B),('25','GP19',B),('24','GP18',B),('23','GND',PW),('22','GP17',B),('21','GP16',B)]

CUSTOM = {
 'RP2350-Plus': make_symbol('RP2350-Plus', LEFT, RIGHT, ref='A', w=22.86,
    datasheet='https://www.waveshare.com/wiki/RP2350-Plus', desc='Waveshare RP2350-Plus module, 40 castellated pads, Pico pin order'),
 'OCXO_OSC5A2B02': make_symbol('OCXO_OSC5A2B02',
    [('5','VCC',PW),('2','GND',PW),('3','EFC',I)], [('1','OUT',O),('4','NC',P)], ref='X', w=12.7,
    desc='CTI OSC5A2B02 5V 10MHz OCXO, pin numbers per datasheet bottom view'),
}
