import sys, json, collections
import os; HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kigen import *

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'proto-v0.1')
g = Gen('hamref_proto_v0_1', OUT)
g.powernets = {'GND','3V3','3V3_GNSS','3V3_SYN','5V_MAIN','5V_USB','5V_EXT','5V_OCXO','5V_DAC','VSYS','VBUS_MOD'}

CNT = collections.Counter()
def ref(p): CNT[p] += 1; return f'{p}{CNT[p]}'

FP = dict(
 r='Resistor_SMD:R_0402_1005Metric', r6='Resistor_SMD:R_0603_1608Metric',
 c='Capacitor_SMD:C_0402_1005Metric', c6='Capacitor_SMD:C_0603_1608Metric', c8='Capacitor_SMD:C_0805_2012Metric',
 cp='Capacitor_THT:CP_Radial_D6.3mm_P2.50mm', fb='Inductor_SMD:L_0603_1608Metric', l='Inductor_SMD:L_0402_1005Metric',
 fuse='Fuse:Fuse_1812_4532Metric', smb='Diode_SMD:D_SMB', sma='Diode_SMD:D_SMA', tp='TestPoint:TestPoint_Pad_D1.5mm',
 mh='MountingHole:MountingHole_3.2mm_M3', sot5='Package_TO_SOT_SMD:SOT-23-5',
 h2='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical', h3='Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
 h4='Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical', h5='Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical',
 h7='Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical',
 sma_c='Connector_Coaxial:SMA_Amphenol_901-144_Vertical', bnc='Connector_Coaxial:BNC_Amphenol_031-5539_Vertical',
 lea='RF_GPS:ublox_LEA', qfn20='Package_DFN_QFN:QFN-20-1EP_4x4mm_P0.5mm_EP2.6x2.6mm', msop10='Package_SO:MSOP-10_3x3mm_P0.5mm',
 xtal='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',
)

class S:
    """Sheet wrapper with simple grid placement for small parts."""
    def __init__(self, name, fn, gx0=30, gy0=40):
        self.sh = g.sheet(name, fn, 'A2'); self.gx0=gx0; self.gy0=gy0; self.i=0; self.name=name
    def nxt(self):
        col, row = self.i % 12, self.i // 12
        self.i += 1
        return self.gx0 + col*40, self.gy0 + row*28
    def add(self, rf, lib, sym, val, pins, fp, xy=None, **kw):
        x, y = xy or self.nxt()
        return self.sh.add(rf, lib, sym, val, x, y, pins=pins, footprint=fp, **kw)
    def R(self, val, a, b, fp='r', **kw): return self.add(ref('R'),'Device','R',val,{'1':a,'2':b},FP[fp],**kw)
    def C(self, val, a, b, fp='c', **kw): return self.add(ref('C'),'Device','C',val,{'1':a,'2':b},FP[fp],**kw)
    def CP(self, val, a, b, **kw): return self.add(ref('C'),'Device','C_Polarized',val,{'1':a,'2':b},FP['cp'],**kw)
    def FB(self, a, b, val='BLM18PG221SN1D', **kw): return self.add(ref('FB'),'Device','FerriteBead',val,{'1':a,'2':b},FP['fb'],mpn=val,**kw)
    def TP(self, net): return self.add(ref('TP'),'Connector','TestPoint',net,{'1':net},FP['tp'])
    def HDR(self, n, nets, val, fp, rf='J', **kw):
        return self.add(ref(rf),'Connector_Generic',f'Conn_01x0{n}',val,{str(i+1):nm for i,nm in enumerate(nets) if nm},FP[fp],**kw)
    def text(self, t, x, y, size=2.0): self.sh.text(t, x, y, size)

# ===================== POWER =====================
P = S('Power','power.kicad_sch', 30, 120)
P.text('POWER: 5V_USB (VBUS) / 5V_EXT -> JP1 -> 5V_MAIN -> TVS, OCXO switch, 3V3_GNSS LDO, ferrite-filtered 5V_DAC', 30, 20, 2.5)
P.text('JP1: 1-2 = USB power, 2-3 = external 5V. Module VSYS fed from 5V_MAIN through Schottky (D2). VBUS pad is direct USB VBUS.', 30, 28, 1.6)
P.HDR(2, ['5V_EXT','GND'], '5V_EXT', 'h2')
P.add(ref('F'),'Device','Polyfuse','1.1A hold',{'1':'VBUS_MOD','2':'5V_USB'},FP['fuse'],mpn='MF-MSMF110/16X-2',mfr='Bourns',note='verify package/footprint')
P.HDR(3, ['5V_USB','5V_MAIN','5V_EXT'], 'JP1 PWR SEL', 'h3', rf='JP')
P.add(ref('D'),'Device','D_TVS','SMBJ5.0A',{'1':'5V_MAIN','2':'GND'},FP['smb'],mpn='SMBJ5.0A',note='unidirectional: cathode (pad 1) to 5V_MAIN')
P.add(ref('D'),'Device','D_Schottky','SS14',{'1':'VSYS','2':'5V_MAIN'},FP['sma'],mpn='SS14',note='cathode to module VSYS')
P.CP('100uF 10V','5V_MAIN','GND'); P.C('10uF 10V','5V_MAIN','GND','c8')
# OCXO power switch
P.add(ref('U'),'Power_Management','TPS2065CDBV','TPS2065C',{'1':'5V_OCXO','3':'OCXO_FLT','4':'OCXO_EN','5':'5V_MAIN'},FP['sot5'],mpn='TPS2065CDBVR',mfr='TI',note='fixed ~1A limit, active-high EN, soft start')
P.R('100k','OCXO_EN','GND'); P.R('100k','OCXO_FLT','3V3')
P.HDR(2, ['OCXO_EN','5V_MAIN'], 'JP2 OCXO FORCE-ON', 'h2', rf='JP')
P.C('10uF 10V','5V_OCXO','GND','c8'); P.C('100nF','5V_OCXO','GND'); P.CP('100uF 10V','5V_OCXO','GND')
# 3V3_GNSS LDO
P.add(ref('U'),'Regulator_Linear','LP5907MFX-3.3','LP5907-3.3',{'1':'5V_MAIN','3':'5V_MAIN','5':'3V3_GNSS'},FP['sot5'],nc=('4',),mpn='LP5907MFX-3.3/NOPB',mfr='TI')
P.C('1uF','5V_MAIN','GND','c6'); P.C('1uF','3V3_GNSS','GND','c6'); P.C('100nF','3V3_GNSS','GND')
# DAC supply
P.FB('5V_MAIN','5V_DAC'); P.C('10uF 10V','5V_DAC','GND','c8'); P.C('100nF','5V_DAC','GND')
# ADC 5V monitor
P.R('100k','5V_MAIN','ADC_5V'); P.R('100k','ADC_5V','GND'); P.C('100nF','ADC_5V','GND')
for n in ['5V_MAIN','5V_OCXO','3V3_GNSS','3V3','5V_DAC','GND']: P.TP(n)
for i in range(4): P.sh.add(ref('H'),'Mechanical','MountingHole','MountingHole_M3',30+i*30,260,pins={},footprint=FP['mh'])

# ===================== GNSS =====================
N = S('GNSS','gnss.kicad_sch', 150, 40)
N.text('GNSS: u-blox LEA-M8S on 3V3_GNSS. UART to MCU, TIMEPULSE -> 74LVC1G17 -> GP6. USB not used (VDD_USB=GND).', 30, 20, 2.5)
N.text('ANT bias: VCC_RF -> 10R -> V_ANT, 10nF at V_ANT (HIM). RF_IN straight to SMA, 50ohm trace.', 30, 28, 1.6)
N.sh.add(ref('U'),'RF_GPS','LEA-M8S','LEA-M8S-0',60,100,
  pins={'3':'GNSS_TXD','4':'GNSS_RXD','6':'3V3_GNSS','10':'GNSS_RESET','11':'3V3_GNSS','16':'GNSS_RF','18':'VCC_RF','19':'V_ANT','24':'GND','27':'GNSS_EXTINT','28':'GNSS_TIMEPULSE'},
  nc=('1','2','5','8','9','12','20','21','22','23','25','26'), footprint=FP['lea'], mpn='LEA-M8S-0-10', mfr='u-blox',
  note='RESET_N: drive low or hi-Z only. SDA/SCL (DDC) unused. USB unused.')
N.add(ref('J'),'Connector','Conn_Coaxial','SMA ANT',{'1':'GNSS_RF','2':'GND'},FP['sma_c'],xy=(120,60),mpn='901-144',mfr='Amphenol',note='rear panel; verify edge-mount vs vertical')
N.R('10','VCC_RF','V_ANT'); N.C('10nF','V_ANT','GND'); N.C('100nF','VCC_RF','GND')
N.C('4.7uF','3V3_GNSS','GND','c6'); N.C('100nF','3V3_GNSS','GND'); N.C('100nF','3V3_GNSS','GND')
N.add(ref('U'),'74xGxx','74LVC1G17','74LVC1G17',{'2':'GNSS_TIMEPULSE','4':'PPS_GNSS','5':'3V3'},FP['sot5'],nc=('1',),mpn='SN74LVC1G17DBVR',mfr='TI')
N.C('100nF','3V3','GND')
N.TP('GNSS_TXD'); N.TP('GNSS_RXD'); N.TP('PPS_GNSS')
N.R('100k','GNSS_EXTINT','GND', note='keeps EXTINT0 low at boot (MCU GP10 drives it)')

# ===================== CLOCK =====================
K = S('Clock','clock.kicad_sch', 30, 160)
K.text('CLOCK: OCXO + EFC DAC, 10MHz buffers, 1PPS OUT mux, Si5351C AUX synth (CLKIN = OCXO). I2C1: DAC 0x4C. I2C0: Si5351 0x60 + OLED 0x3C.', 30, 14, 2.2)
K.text('OCXO pin geometry unverified: placeholder 1x5 header, pad N = OCXO pin N (datasheet bottom view). Verify before layout.', 30, 22, 1.6)
K.sh.add(ref('X'),'HamREF','OCXO_OSC5A2B02','OSC5A2B02',40,60,pins={'1':'OCXO_OUT_RAW','5':'5V_OCXO','2':'GND','3':'EFC'},nc=('4',),footprint=FP['h5'],mfr='CTI',mpn='OSC5A2B02',note='used units often salvaged: test before fitting')
# DAC
K.sh.add(ref('U'),'Analog_DAC','AD5693RxRM','AD5693R',110,60,pins={'1':'5V_DAC','2':'3V3','3':'3V3','4':'GND','5':'GND','6':'GND','7':'I2C1_SCL','8':'I2C1_SDA','9':'DAC_VREF','10':'DAC_OUT'},footprint=FP['msop10'],mfr='ADI',mpn='AD5693RBRMZ',note='A0=GND -> 0x4C. Set gain x2 (0-5V), clamp code to ~4.0V in firmware.')
K.C('10nF','DAC_VREF','GND'); K.C('100nF','3V3','GND'); K.C('100nF','5V_DAC','GND'); K.C('10uF 10V','5V_DAC','GND','c8')
K.R('4.7k','I2C1_SDA','3V3'); K.R('4.7k','I2C1_SCL','3V3')
K.R('4.7k','DAC_OUT','EFC_F1'); K.C('10uF 10V','EFC_F1','GND','c8')
K.R('4.7k','EFC_F1','EFC'); K.C('10uF 10V','EFC','GND','c8')
K.R('470k','EFC','ADC_EFC'); K.R('470k','ADC_EFC','GND'); K.C('100nF','ADC_EFC','GND')
K.TP('EFC'); K.TP('OCXO_OUT_RAW')
# NTC
K.add(ref('RT'),'Device','Thermistor_NTC','NTC 10k',{'1':'ADC_NTC','2':'GND'},FP['r6'],mpn='NCP18XH103F03RB',mfr='Murata',note='place next to OCXO')
K.R('10k','3V3','ADC_NTC'); K.C('100nF','ADC_NTC','GND')
# 3V3 input buffer
K.add(ref('U'),'74xGxx','74LVC1G17','74LVC1G17',{'2':'OCXO_OUT_RAW','4':'OCXO_10M_BUF','5':'3V3'},FP['sot5'],nc=('1',),mpn='SN74LVC1G17DBVR',mfr='TI',note='5V-tolerant input; feeds MCU GP7 + Si5351 CLKIN')
K.R('33','OCXO_10M_BUF','OCXO_10M_3V3'); K.C('100nF','3V3','GND')
# REF OUT buffer (5V_OCXO domain)
K.add(ref('U'),'74xGxx','74AHCT1G125','74AHCT1G125',{'1':'GND','2':'OCXO_OUT_RAW','4':'REF_BUF','5':'5V_OCXO'},FP['sot5'],mpn='SN74AHCT1G125DBVR',mfr='TI',note='clean REF OUT path; /OE tied low')
K.R('47','REF_BUF','REF_OUT'); K.C('100nF','5V_OCXO','GND')
K.add(ref('J'),'Connector','Conn_Coaxial','BNC REF OUT',{'1':'REF_OUT','2':'GND'},FP['bnc'],mfr='Amphenol',mpn='031-5539',note='rear panel')
# 1PPS OUT
K.HDR(3, ['PPS_GNSS','PPS_SEL','PPS_MCU'], 'JP3 1PPS SRC (1-2 GNSS, 2-3 MCU)', 'h3', rf='JP')
K.add(ref('U'),'74xGxx','74LVC1G125','74LVC1G125',{'1':'GND','2':'PPS_SEL','4':'PPS_BUF','5':'3V3'},FP['sot5'],mpn='SN74LVC1G125DBVR',mfr='TI')
K.R('47','PPS_BUF','PPS_OUT'); K.C('100nF','3V3','GND')
K.add(ref('J'),'Connector','Conn_Coaxial','BNC 1PPS OUT',{'1':'PPS_OUT','2':'GND'},FP['bnc'],mfr='Amphenol',mpn='031-5539',note='rear panel')
# Si5351C
K.sh.add(ref('U'),'Oscillator','Si5351C-B-GM','Si5351C-B-GM',170,60,
  pins={'1':'XA_DNP','2':'XB_DNP','3':'SYN_INTR','4':'I2C0_SCL','5':'I2C0_SDA','6':'OCXO_10M_3V3','7':'AUX_OEB','10':'3V3_SYN','11':'3V3_SYN','13':'AUX_CLK0','14':'3V3_SYN','18':'3V3_SYN','20':'3V3_SYN','21':'GND'},
  nc=('8','9','12','15','16','17','19'),footprint=FP['qfn20'],mfr='Skyworks',mpn='SI5351C-B-GM',note='I2C 0x60. XA/XB wired to DNP crystal Y1 only; with CLKIN used they stay open. Verify EP size.')
K.FB('3V3','3V3_SYN','BLM18PG221SN1D'); K.C('10uF 10V','3V3_SYN','GND','c8')
for _ in range(5): K.C('100nF','3V3_SYN','GND')
K.R('10k','AUX_OEB','3V3', note='outputs disabled at boot')
K.R('10k','SYN_INTR','3V3')
K.add(ref('Y'),'Device','Crystal_GND24','25MHz',{'1':'XA_DNP','2':'GND','3':'XB_DNP','4':'GND'},FP['xtal'],dnp=True,note='DNP; footprint for optional 25 MHz crystal (XA/XB would need connecting)')
K.R('47','AUX_CLK0','AUX_OUT')
K.add(ref('J'),'Connector','Conn_Coaxial','BNC AUX OUT',{'1':'AUX_OUT','2':'GND'},FP['bnc'],mfr='Amphenol',mpn='031-5539',note='rear panel; 3.3V CMOS, filter for LNB/Pluto TBD')
K.TP('AUX_OUT'); K.TP('PPS_OUT')

# ===================== MCU & UI =====================
M = S('MCU_UI','mcu_ui.kicad_sch', 200, 40)
M.text('MCU + UI: Waveshare RP2350-Plus module soldered via castellated pads. GPIO map = docs v0.9 (GP16 = OCXO_FLT).', 30, 14, 2.5)
M.sh.add(ref('A'),'HamREF','RP2350-Plus','RP2350-Plus',80,110,
  pins={'1':'GNSS_RXD','2':'GNSS_TXD','4':'I2C1_SDA','5':'I2C1_SCL','6':'I2C0_SDA','7':'I2C0_SCL','9':'PPS_GNSS','10':'OCXO_10M_3V3','11':'PPS_MCU','12':'GNSS_RESET',
        '14':'GNSS_EXTINT','15':'ENC_A','16':'ENC_B','17':'ENC_SW','19':'LED_DATA_3V3','20':'AUX_OEB','21':'GP16_OCXO_FLT','27':'OCXO_EN','29':'SYN_INTR','30':'RUN_MOD',
        '31':'ADC_5V','32':'ADC_NTC','34':'ADC_EFC','36':'3V3','39':'VSYS','40':'VBUS_MOD','22':'GP17','24':'GP18','25':'GP19','26':'GP20'},
  nc=('35','37'),footprint='HamREF:RP2350-Plus_Castellated',mfr='Waveshare',mpn='RP2350-Plus',note='footprint to be drawn from STEP/drawing; see docs')
M.R('4.7k','I2C0_SDA','3V3'); M.R('4.7k','I2C0_SCL','3V3')
M.C('10uF 10V','3V3','GND','c8'); M.C('100nF','3V3','GND')
M.HDR(4, ['GND','3V3','I2C0_SCL','I2C0_SDA'], 'J OLED 0.91in I2C', 'h4')
M.HDR(4, ['ENC_A','ENC_B','ENC_SW','GND'], 'J ENCODER', 'h4')
for n in ('ENC_A','ENC_B','ENC_SW'): M.C('100nF',n,'GND')
M.add(ref('U'),'74xGxx','74AHCT1G125','74AHCT1G125',{'1':'GND','2':'LED_DATA_3V3','4':'LED_DATA_BUF','5':'5V_MAIN'},FP['sot5'],mpn='SN74AHCT1G125DBVR',mfr='TI',note='3V3 -> 5V level shift for WS2812')
M.R('330','LED_DATA_BUF','LED_DATA'); M.C('100nF','5V_MAIN','GND')
M.HDR(3, ['5V_MAIN','LED_DATA','GND'], 'J LEDS (2x WS2812B)', 'h3')
M.HDR(2, ['GNSS_RESET','GND'], 'J RESET GNSS (short=reset)', 'h2')
M.HDR(2, ['RUN_MOD','GND'], 'J RUN (short=MCU reset)', 'h2')
M.HDR(7, ['GP17','GP18','GP19','GP20','3V3','GND','5V_MAIN'], 'J SPARE GPIO', 'h7')
M.TP('GP16_OCXO_FLT')

g.write()
import shutil
shutil.copytree(os.path.join(HERE,'fplib','hamref.pretty'), OUT+'/hamref.pretty', dirs_exist_ok=True)
open(OUT+'/fp-lib-table','w').write('(fp_lib_table\n  (version 7)\n  (lib (name "HamREF")(type "KiCad")(uri "${KIPRJMOD}/hamref.pretty")(options "")(descr "HamREF project footprints"))\n)\n')
open(OUT+'/hamref_proto_v0_1.kicad_pro','w').write(json.dumps({'meta':{'filename':'hamref_proto_v0_1.kicad_pro','version':1},'sheets':[],'text_variables':{}},indent=2))
json.dump([dict(p) for s in g.sheets for p in s.parts], open(OUT+'/parts.json','w'), indent=1)
print('parts:', sum(len(s.parts) for s in g.sheets))
