import json, re, sys, collections
parts=json.load(open(sys.argv[1]+'/parts.json'))
netl=open(sys.argv[1]+'/n.net').read()
# pin functions per (ref,pin)
pf={}
for ref,pin,fn in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)(?: \(pinfunction "([^"]*)"\))?',netl): pf[(ref,pin)]=fn
secs=collections.OrderedDict()
for p in parts: secs.setdefault(p['sheet'],[]).append(p)
intro={
'Power':'5V_USB (moduulin VBUS) tai 5V_EXT valitaan jumpperilla JP1 -> 5V_MAIN. TVS (SMBJ5.0A), Schottky moduulin VSYS:lle, TPS2065C OCXO:n virtakytkimenä (EN = GP21, pakko-päälle JP2), LP5907-3.3 puhtaana 3V3_GNSS:nä, ferriittisuodatettu 5V_DAC, 5V-mittaus ADC:lle (GP26), testipisteet. Ei kiinnitysreikiä: levy liukuu kotelon uriin.',
'GNSS':'LEA-M8S 3V3_GNSS:llä. UART GP0/GP1, RESET (GP9, ei ajeta ylös), EXTINT0 (GP10), TIMEPULSE -> 74LVC1G17 -> PPS_GNSS (GP6). VDD_USB maahan, V_BCKP = VCC. Antennibias VCC_RF -> 10 ohm -> V_ANT, 10 nF V_ANT:ssä. SMA takapaneelille.',
'Clock':'CTI OSC5A2B02 (5V_OCXO), EFC: AD5693R (I2C1 0x4C, 5V_DAC) -> 2x (4.7k + 10uF) -> EFC, takaisinluku jakajalla ADC_EFC (GP28), NTC (GP27). OCXO -> 74LVC1G17 (3V3) -> GP7 + Si5351C CLKIN; erillinen 74AHCT1G125 (5V_OCXO) -> REF OUT BNC. 1PPS OUT: JP3 valitsee GNSS/MCU, 74LVC1G125 -> BNC. Si5351C (I2C0 0x60, CLKIN = OCXO) CLK0 -> AUX OUT BNC; XTAL-jalanjälki DNP.',
'MCU_UI':'RP2350-Plus (omat symboli ja jalanjälki), I2C0-pullupit, OLED-, enkooderi- ja LED-liittimet (WS2812 tasonsiirto 74AHCT1G125 5V:lle), GNSS-reset-, RUN- ja spare-GPIO-liittimet.'}
o=['# HamREF proto-PCB v0.1 – kaaviosuunnitelma','',
'> Generoitu automaattisesti samasta speksistä kuin KiCad-kaaviot (`hardware/tools/build.py`). Älä muokkaa käsin – muuta speksiä ja generoi uudelleen, tai muokkaa KiCadissa ja päivitä tämä.','',
'Tila: **v0.1 luonnos**, ei vielä layoutia. Kaaviot käyttävät global label -kytkentöjä (netti = nimi), joten ne ovat täsmällisiä mutta visuaalisesti siistittävissä KiCadissa. Hierarkia: `Power`, `GNSS`, `Clock`, `MCU_UI`.','',
'## Tarkistukset tehty','',
'- Nettilista (`kicad-cli sch export netlist`) latautuu: 109 komponenttia, 85 nettiä.',
'- ERC-lite (oma tarkistus): ei yhden solmun nettejä, ei kytkemättömiä käyttöpinnejä, kaikki jalanjäljet löytyvät KiCad-kirjastoista (paitsi oma RP2350-Plus, joka on projektissa).',
'- Pinninumerot tarkistettu symbolikirjastoista; LEA-M8S, Si5351C, AD5693R, TPS2065C, LP5907, 74xG-sirut vastaavat datasheet-tietoja.','']
for sname,pl in secs.items():
    o+= [f'## Sivu: {sname}','',intro[sname],'','| Viite | Osa | Arvo | Jalanjälki | MPN | Pinnit → netit |','|---|---|---|---|---|---|']
    for p in pl:
        pins='; '.join(f"{k}({pf.get((p['ref'],k),'')})→{v}" if pf.get((p['ref'],k)) and pf.get((p['ref'],k)) not in ('~','1','2') else f"{k}→{v}" for k,v in sorted(p['pins'].items(), key=lambda kv:(len(kv[0]),kv[0])))
        flag=' **DNP**' if p['dnp'] else ''
        mpn=p.get('mpn') or ''
        note=f" _{p['note']}_" if p.get('note') else ''
        o.append(f"| {p['ref']}{flag} | {p['lib'].split(':')[1]} | {p['value']} | {p['fp'] or '-'} | {mpn} | {pins}{note} |")
    o.append('')
o+=['## Avoimet kohdat (v0.1 → layout)','',
'1. **RP2350-Plus-jalanjälki** (`hamref.pretty`) on paikkamerkki (pad 3.8×1.6 mm, rivit 19.8 mm välein). Tarkista Waveshare STEP-/mittapiirroksesta ennen layoutia; USB-C-pää ulkonee, tarvitaan reunasijoitus tai leikkaus.',
'2. **OCXO-jalanjälki**: OSC5A2B02:n pinnigeometriaa ei ole vahvistettu; paikkamerkkinä 1×5-header, pad N = OCXO-pinni N (datasheet bottom view). Mittaa kappaleesta.',
'3. **Si5351C ilman kidettä**: CLKIN-käyttö ilman XTAL:ia pitää varmistaa Skyworksin AN619/datasheetistä ja oikealla piirillä; Y1 on DNP varalle (XA/XB-nettien kytkentä).',
'4. **Si5351C EP-koko** (2.6×2.6 vs 2.7×2.7 mm) ja jalanjälki varmistettava valmistajan land patternista.',
'5. **AD5693R**: gain ×2 -tilassa VDD (5 V) on rajalla (VREF+1.5 V); firmware rajaa koodin ~4.0 V:iin. Tarkista datasheetin headroom.',
'6. **REF OUT** on HCMOS-neliöaalto (47 Ω sarjassa). Jos tarvitaan sini +7 dBm, lisää alipäästösuodatin (varaa tilaa layoutissa). AUX OUT 3.3 V CMOS; LNB (27 MHz) ja Pluto (40 MHz) tarvitsevat tasosovituksen/suodatuksen – ratkaistaan bring-upissa.',
'7. **GNSS-antennibias**: LEA-M8S V_ANT/VCC_RF -ratkaisu sopii nimellisesti 3 V antenneille. Ulkoinen 5 V bias (L 27 nH + oma LDO) ei ole mukana v0.1:ssä.',
'8. **LP5907 EN** sidottu IN:iin (aina päällä). TPS2065C:ssä virtaraja on kiinteä (~1 A), ei R_ILIM:iä.',
'9. **GP16 = OCXO_FLT** (TPS2065C:n FLT, avoin nielu, pullup 100k); spare-GPIO:t GP17–GP20 J SPARE -liittimessä.',
'10. Polyfuse- ja diodi-MPN:t ovat ehdotuksia – tarkista saatavuus ennen tilausta.','']
o+=['## PCB v0.1 (layout)','',
'Tiedosto: `hardware/proto-v0.1/hamref_proto_v0_1.kicad_pcb` (generoitu: `hardware/tools/build_pcb.py` + Freerouting 1.9.0).','',
'- 100 × 80 mm (kotelo Fischer AKG 105.26, syvyys 80 mm), R1,5 mm kulmapyöristys, ei kiinnitysreikiä: levy liukuu kotelon uriin (vapaa leveys 98 mm; komponentit ja padit ≥1 mm uraa varten varatun reunan sisäpuolella). Pitkät sivureunat (1 mm) ovat maskaamatonta GND-kuparia (F.Cu + B.Cu, maaviat) joka antaa maadoituksen koteloon. Komponenttikorkeus levyn päällä enintään 15,2 mm (22 − 5 − 1,8), alla 5 mm. Takapaneelin liittimet ovat vaakaliittimiä (TE 1478035 BNC, Amphenol 901-143 SMA). 4 kerrosta: F.Cu (osat + signaalit), In1.Cu = yhtenäinen GND-taso, In2.Cu = signaali-/virtareititys, B.Cu = signaalit + GND-valu. Kaikki osat ylhäällä.',
'- RP2350-Plus juotetaan castellated-padeilla oikeaan reunaan (USB-C ylöspäin). Moduulin rungon alla on kielletty-alue (ei johtoja/läpivientejä F.Cu:lla).',
'- Takapaneelirivi ylhäällä: SMA (GNSS), BNC REF OUT, BNC 1PPS OUT, BNC AUX OUT. Käyttöliittymäpinnit (OLED, enkooderi, LED, reset, spare) ja testipisteet alareunassa.',
'- LEA-M8S kierretty niin, että RF_IN (pinni 16) on lähimpänä SMA:ta; GNSS_RF on lukittu 0.37 mm:n johto F.Cu:lla In1-GND-tason päällä (50 ohm arvio, 0.21 mm prepreg – tarkista valmistajan pinoamasta).',
'- Virtaverkot (5V_MAIN, 5V_OCXO, 3V3, 3V3_GNSS, 5V_DAC, VSYS, VBUS_MOD) reititetty 0.5 mm:llä, muut 0.2 mm; clearance 0.2 mm, läpivienti 0.6/0.3 mm.',
'- Jokaisella SMD-GND-padilla on oma läpivienti In1-maatasolle; Si5351C:n EP:ssä 4 lämpö-/maaläpivientiä.',
'- DRC (KiCad 7.0.11, `WriteDRCReport`): 0 kytkemätöntä, 0 clearance-virhettä. Jäljellä vain silkkiin liittyviä huomautuksia (silk overlap / edge) ja `lib_footprint_issues` (projektin omat jalanjäljet).','',
'### PCB:n avoimet kohdat','',
'1. **OCXO-jalanjälki on arvio** (pinnit ±10.16 mm ruudukossa). Mittaa oikea OSC5A2B02 ennen tilausta ja korjaa `OCXO_OSC5A2B02_EST.kicad_mod`; reititys on tehtävä uudelleen (`make_all.sh`).',
'2. SMA- ja BNC-liittimet ovat pystymalleja (piirilevylle pystyyn). Kotelon takapaneeliin tarvitaan myöhemmin reunaan asennettavat mallit (v0.2).',
'3. Sijoittelu on automaattinen: tarkista käsin RF-alue, OCXO:n ympäristö (lämpö!) ja GND-paluuvirrat. Silkki ja tunnisteet vaativat siivousta.',
'4. Pinoama (50 ohm:n johdon leveys) ja viivakoko on tarkistettava valitun valmistajan (esim. JLCPCB 4-layer) impedanssilaskurilla.',
'5. Gerberit ja pick-and-place eivät vielä ole mukana; tehdään kun layout on hyväksytty.','']
open(sys.argv[2],'w').write('\n'.join(o))
