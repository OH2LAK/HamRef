# HamREF proto-PCB v0.1 – kaaviosuunnitelma

> Generoitu automaattisesti samasta speksistä kuin KiCad-kaaviot (`hardware/tools/build.py`). Älä muokkaa käsin – muuta speksiä ja generoi uudelleen, tai muokkaa KiCadissa ja päivitä tämä.

Tila: **v0.1 luonnos**, ei vielä layoutia. Kaaviot käyttävät global label -kytkentöjä (netti = nimi), joten ne ovat täsmällisiä mutta visuaalisesti siistittävissä KiCadissa. Hierarkia: `Power`, `GNSS`, `Clock`, `MCU_UI`.

## Tarkistukset tehty

- Nettilista (`kicad-cli sch export netlist`) latautuu: 113 komponenttia, 85 nettiä.
- ERC-lite (oma tarkistus): ei yhden solmun nettejä, ei kytkemättömiä käyttöpinnejä, kaikki jalanjäljet löytyvät KiCad-kirjastoista (paitsi oma RP2350-Plus, joka on projektissa).
- Pinninumerot tarkistettu symbolikirjastoista; LEA-M8S, Si5351C, AD5693R, TPS2065C, LP5907, 74xG-sirut vastaavat datasheet-tietoja.

## Sivu: Power

5V_USB (moduulin VBUS) tai 5V_EXT valitaan jumpperilla JP1 -> 5V_MAIN. TVS (SMBJ5.0A), Schottky moduulin VSYS:lle, TPS2065C OCXO:n virtakytkimenä (EN = GP21, pakko-päälle JP2), LP5907-3.3 puhtaana 3V3_GNSS:nä, ferriittisuodatettu 5V_DAC, 5V-mittaus ADC:lle (GP26), testipisteet ja 4 kiinnitysreikää.

| Viite | Osa | Arvo | Jalanjälki | MPN | Pinnit → netit |
|---|---|---|---|---|---|
| J1 | Conn_01x02 | 5V_EXT | Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical |  | 1(Pin_1)→5V_EXT; 2(Pin_2)→GND |
| F1 | Polyfuse | 1.1A hold | Fuse:Fuse_1812_4532Metric | MF-MSMF110/16X-2 | 1→VBUS_MOD; 2→5V_USB _verify package/footprint_ |
| JP1 | Conn_01x03 | JP1 PWR SEL | Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical |  | 1(Pin_1)→5V_USB; 2(Pin_2)→5V_MAIN; 3(Pin_3)→5V_EXT |
| D1 | D_TVS | SMBJ5.0A | Diode_SMD:D_SMB | SMBJ5.0A | 1(A1)→5V_MAIN; 2(A2)→GND _unidirectional: cathode (pad 1) to 5V_MAIN_ |
| D2 | D_Schottky | SS14 | Diode_SMD:D_SMA | SS14 | 1(K)→VSYS; 2(A)→5V_MAIN _cathode to module VSYS_ |
| C1 | C_Polarized | 100uF 10V | Capacitor_THT:CP_Radial_D6.3mm_P2.50mm |  | 1→5V_MAIN; 2→GND |
| C2 | C | 10uF 10V | Capacitor_SMD:C_0805_2012Metric |  | 1→5V_MAIN; 2→GND |
| U1 | TPS2065CDBV | TPS2065C | Package_TO_SOT_SMD:SOT-23-5 | TPS2065CDBVR | 1(OUT)→5V_OCXO; 2(GND)→GND; 3(~{FLT})→OCXO_FLT; 4(EN)→OCXO_EN; 5(IN)→5V_MAIN _fixed ~1A limit, active-high EN, soft start_ |
| R1 | R | 100k | Resistor_SMD:R_0402_1005Metric |  | 1→OCXO_EN; 2→GND |
| R2 | R | 100k | Resistor_SMD:R_0402_1005Metric |  | 1→OCXO_FLT; 2→3V3 |
| JP2 | Conn_01x02 | JP2 OCXO FORCE-ON | Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical |  | 1(Pin_1)→OCXO_EN; 2(Pin_2)→5V_MAIN |
| C3 | C | 10uF 10V | Capacitor_SMD:C_0805_2012Metric |  | 1→5V_OCXO; 2→GND |
| C4 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→5V_OCXO; 2→GND |
| C5 | C_Polarized | 100uF 10V | Capacitor_THT:CP_Radial_D6.3mm_P2.50mm |  | 1→5V_OCXO; 2→GND |
| U2 | LP5907MFX-3.3 | LP5907-3.3 | Package_TO_SOT_SMD:SOT-23-5 | LP5907MFX-3.3/NOPB | 1(IN)→5V_MAIN; 2(GND)→GND; 3(EN)→5V_MAIN; 5(OUT)→3V3_GNSS |
| C6 | C | 1uF | Capacitor_SMD:C_0603_1608Metric |  | 1→5V_MAIN; 2→GND |
| C7 | C | 1uF | Capacitor_SMD:C_0603_1608Metric |  | 1→3V3_GNSS; 2→GND |
| C8 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→3V3_GNSS; 2→GND |
| FB1 | FerriteBead | BLM18PG221SN1D | Inductor_SMD:L_0603_1608Metric | BLM18PG221SN1D | 1→5V_MAIN; 2→5V_DAC |
| C9 | C | 10uF 10V | Capacitor_SMD:C_0805_2012Metric |  | 1→5V_DAC; 2→GND |
| C10 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→5V_DAC; 2→GND |
| R3 | R | 100k | Resistor_SMD:R_0402_1005Metric |  | 1→5V_MAIN; 2→ADC_5V |
| R4 | R | 100k | Resistor_SMD:R_0402_1005Metric |  | 1→ADC_5V; 2→GND |
| C11 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→ADC_5V; 2→GND |
| TP1 | TestPoint | 5V_MAIN | TestPoint:TestPoint_Pad_D1.5mm |  | 1→5V_MAIN |
| TP2 | TestPoint | 5V_OCXO | TestPoint:TestPoint_Pad_D1.5mm |  | 1→5V_OCXO |
| TP3 | TestPoint | 3V3_GNSS | TestPoint:TestPoint_Pad_D1.5mm |  | 1→3V3_GNSS |
| TP4 | TestPoint | 3V3 | TestPoint:TestPoint_Pad_D1.5mm |  | 1→3V3 |
| TP5 | TestPoint | 5V_DAC | TestPoint:TestPoint_Pad_D1.5mm |  | 1→5V_DAC |
| TP6 | TestPoint | GND | TestPoint:TestPoint_Pad_D1.5mm |  | 1→GND |
| H1 | MountingHole | MountingHole_M3 | MountingHole:MountingHole_3.2mm_M3 |  |  |
| H2 | MountingHole | MountingHole_M3 | MountingHole:MountingHole_3.2mm_M3 |  |  |
| H3 | MountingHole | MountingHole_M3 | MountingHole:MountingHole_3.2mm_M3 |  |  |
| H4 | MountingHole | MountingHole_M3 | MountingHole:MountingHole_3.2mm_M3 |  |  |

## Sivu: GNSS

LEA-M8S 3V3_GNSS:llä. UART GP0/GP1, RESET (GP9, ei ajeta ylös), EXTINT0 (GP10), TIMEPULSE -> 74LVC1G17 -> PPS_GNSS (GP6). VDD_USB maahan, V_BCKP = VCC. Antennibias VCC_RF -> 10 ohm -> V_ANT, 10 nF V_ANT:ssä. SMA takapaneelille.

| Viite | Osa | Arvo | Jalanjälki | MPN | Pinnit → netit |
|---|---|---|---|---|---|
| U3 | LEA-M8S | LEA-M8S-0 | RF_GPS:ublox_LEA | LEA-M8S-0-10 | 3(TXD)→GNSS_TXD; 4(RXD)→GNSS_RXD; 6(VCC)→3V3_GNSS; 7(GND)→GND; 10(~{RESET})→GNSS_RESET; 11(V_BCKP)→3V3_GNSS; 13(GND)→GND; 14(GND)→GND; 15(GND)→GND; 16(RF_IN)→GNSS_RF; 17(GND)→GND; 18(VCC_RF)→VCC_RF; 19(V_ANT)→V_ANT; 24(VDD_USB)→GND; 27(EXTINT0)→GNSS_EXTINT; 28(TIMEPULSE)→GNSS_TIMEPULSE _RESET_N: drive low or hi-Z only. SDA/SCL (DDC) unused. USB unused._ |
| J2 | Conn_Coaxial | SMA ANT | Connector_Coaxial:SMA_Amphenol_901-144_Vertical | 901-144 | 1(In)→GNSS_RF; 2(Ext)→GND _rear panel; verify edge-mount vs vertical_ |
| R5 | R | 10 | Resistor_SMD:R_0402_1005Metric |  | 1→VCC_RF; 2→V_ANT |
| C12 | C | 10nF | Capacitor_SMD:C_0402_1005Metric |  | 1→V_ANT; 2→GND |
| C13 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→VCC_RF; 2→GND |
| C14 | C | 4.7uF | Capacitor_SMD:C_0603_1608Metric |  | 1→3V3_GNSS; 2→GND |
| C15 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→3V3_GNSS; 2→GND |
| C16 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→3V3_GNSS; 2→GND |
| U4 | 74LVC1G17 | 74LVC1G17 | Package_TO_SOT_SMD:SOT-23-5 | SN74LVC1G17DBVR | 2→GNSS_TIMEPULSE; 3(GND)→GND; 4→PPS_GNSS; 5(VCC)→3V3 |
| C17 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→3V3; 2→GND |
| TP7 | TestPoint | GNSS_TXD | TestPoint:TestPoint_Pad_D1.5mm |  | 1→GNSS_TXD |
| TP8 | TestPoint | GNSS_RXD | TestPoint:TestPoint_Pad_D1.5mm |  | 1→GNSS_RXD |
| TP9 | TestPoint | PPS_GNSS | TestPoint:TestPoint_Pad_D1.5mm |  | 1→PPS_GNSS |
| R6 | R | 100k | Resistor_SMD:R_0402_1005Metric |  | 1→GNSS_EXTINT; 2→GND _keeps EXTINT0 low at boot (MCU GP10 drives it)_ |

## Sivu: Clock

CTI OSC5A2B02 (5V_OCXO), EFC: AD5693R (I2C1 0x4C, 5V_DAC) -> 2x (4.7k + 10uF) -> EFC, takaisinluku jakajalla ADC_EFC (GP28), NTC (GP27). OCXO -> 74LVC1G17 (3V3) -> GP7 + Si5351C CLKIN; erillinen 74AHCT1G125 (5V_OCXO) -> REF OUT BNC. 1PPS OUT: JP3 valitsee GNSS/MCU, 74LVC1G125 -> BNC. Si5351C (I2C0 0x60, CLKIN = OCXO) CLK0 -> AUX OUT BNC; XTAL-jalanjälki DNP.

| Viite | Osa | Arvo | Jalanjälki | MPN | Pinnit → netit |
|---|---|---|---|---|---|
| X1 | OCXO_OSC5A2B02 | OSC5A2B02 | HamREF:OCXO_OSC5A2B02_EST | OSC5A2B02 | 1(OUT)→OCXO_OUT_RAW; 2(GND)→GND; 3(EFC)→EFC; 5(VCC)→5V_OCXO _used units often salvaged: test before fitting_ |
| U5 | AD5693RxRM | AD5693R | Package_SO:MSOP-10_3x3mm_P0.5mm | AD5693RBRMZ | 1(VDD)→5V_DAC; 2(VLOGIC)→3V3; 3(~{RESET})→3V3; 4(~{LDAC})→GND; 5(GND)→GND; 6(A0)→GND; 7(SCL)→I2C1_SCL; 8(SDA)→I2C1_SDA; 9(VREF)→DAC_VREF; 10(VOUT)→DAC_OUT _A0=GND -> 0x4C. Set gain x2 (0-5V), clamp code to ~4.0V in firmware._ |
| C18 | C | 10nF | Capacitor_SMD:C_0402_1005Metric |  | 1→DAC_VREF; 2→GND |
| C19 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→3V3; 2→GND |
| C20 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→5V_DAC; 2→GND |
| C21 | C | 10uF 10V | Capacitor_SMD:C_0805_2012Metric |  | 1→5V_DAC; 2→GND |
| R7 | R | 4.7k | Resistor_SMD:R_0402_1005Metric |  | 1→I2C1_SDA; 2→3V3 |
| R8 | R | 4.7k | Resistor_SMD:R_0402_1005Metric |  | 1→I2C1_SCL; 2→3V3 |
| R9 | R | 4.7k | Resistor_SMD:R_0402_1005Metric |  | 1→DAC_OUT; 2→EFC_F1 |
| C22 | C | 10uF 10V | Capacitor_SMD:C_0805_2012Metric |  | 1→EFC_F1; 2→GND |
| R10 | R | 4.7k | Resistor_SMD:R_0402_1005Metric |  | 1→EFC_F1; 2→EFC |
| C23 | C | 10uF 10V | Capacitor_SMD:C_0805_2012Metric |  | 1→EFC; 2→GND |
| R11 | R | 470k | Resistor_SMD:R_0402_1005Metric |  | 1→EFC; 2→ADC_EFC |
| R12 | R | 470k | Resistor_SMD:R_0402_1005Metric |  | 1→ADC_EFC; 2→GND |
| C24 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→ADC_EFC; 2→GND |
| TP10 | TestPoint | EFC | TestPoint:TestPoint_Pad_D1.5mm |  | 1→EFC |
| TP11 | TestPoint | OCXO_OUT_RAW | TestPoint:TestPoint_Pad_D1.5mm |  | 1→OCXO_OUT_RAW |
| RT1 | Thermistor_NTC | NTC 10k | Resistor_SMD:R_0603_1608Metric | NCP18XH103F03RB | 1→ADC_NTC; 2→GND _place next to OCXO_ |
| R13 | R | 10k | Resistor_SMD:R_0402_1005Metric |  | 1→3V3; 2→ADC_NTC |
| C25 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→ADC_NTC; 2→GND |
| U6 | 74LVC1G17 | 74LVC1G17 | Package_TO_SOT_SMD:SOT-23-5 | SN74LVC1G17DBVR | 2→OCXO_OUT_RAW; 3(GND)→GND; 4→OCXO_10M_BUF; 5(VCC)→3V3 _5V-tolerant input; feeds MCU GP7 + Si5351 CLKIN_ |
| R14 | R | 33 | Resistor_SMD:R_0402_1005Metric |  | 1→OCXO_10M_BUF; 2→OCXO_10M_3V3 |
| C26 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→3V3; 2→GND |
| U7 | 74AHCT1G125 | 74AHCT1G125 | Package_TO_SOT_SMD:SOT-23-5 | SN74AHCT1G125DBVR | 1→GND; 2→OCXO_OUT_RAW; 3(GND)→GND; 4→REF_BUF; 5(VCC)→5V_OCXO _clean REF OUT path; /OE tied low_ |
| R15 | R | 47 | Resistor_SMD:R_0402_1005Metric |  | 1→REF_BUF; 2→REF_OUT |
| C27 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→5V_OCXO; 2→GND |
| J3 | Conn_Coaxial | BNC REF OUT | Connector_Coaxial:BNC_Amphenol_031-5539_Vertical | 031-5539 | 1(In)→REF_OUT; 2(Ext)→GND _rear panel_ |
| JP3 | Conn_01x03 | JP3 1PPS SRC (1-2 GNSS, 2-3 MCU) | Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical |  | 1(Pin_1)→PPS_GNSS; 2(Pin_2)→PPS_SEL; 3(Pin_3)→PPS_MCU |
| U8 | 74LVC1G125 | 74LVC1G125 | Package_TO_SOT_SMD:SOT-23-5 | SN74LVC1G125DBVR | 1→GND; 2→PPS_SEL; 3(GND)→GND; 4→PPS_BUF; 5(VCC)→3V3 |
| R16 | R | 47 | Resistor_SMD:R_0402_1005Metric |  | 1→PPS_BUF; 2→PPS_OUT |
| C28 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→3V3; 2→GND |
| J4 | Conn_Coaxial | BNC 1PPS OUT | Connector_Coaxial:BNC_Amphenol_031-5539_Vertical | 031-5539 | 1(In)→PPS_OUT; 2(Ext)→GND _rear panel_ |
| U9 | Si5351C-B-GM | Si5351C-B-GM | Package_DFN_QFN:QFN-20-1EP_4x4mm_P0.5mm_EP2.6x2.6mm | SI5351C-B-GM | 1(XA)→XA_DNP; 2(XB)→XB_DNP; 3(INTR)→SYN_INTR; 4(SCL)→I2C0_SCL; 5(SDA)→I2C0_SDA; 6(CLKIN)→OCXO_10M_3V3; 7(OEB)→AUX_OEB; 10(VDDOB)→3V3_SYN; 11(VDDOA)→3V3_SYN; 13(CLK0)→AUX_CLK0; 14(VDDOD)→3V3_SYN; 18(VDDOC)→3V3_SYN; 20(VDD)→3V3_SYN; 21(GND)→GND _I2C 0x60. XA/XB wired to DNP crystal Y1 only; with CLKIN used they stay open. Verify EP size._ |
| FB2 | FerriteBead | BLM18PG221SN1D | Inductor_SMD:L_0603_1608Metric | BLM18PG221SN1D | 1→3V3; 2→3V3_SYN |
| C29 | C | 10uF 10V | Capacitor_SMD:C_0805_2012Metric |  | 1→3V3_SYN; 2→GND |
| C30 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→3V3_SYN; 2→GND |
| C31 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→3V3_SYN; 2→GND |
| C32 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→3V3_SYN; 2→GND |
| C33 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→3V3_SYN; 2→GND |
| C34 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→3V3_SYN; 2→GND |
| R17 | R | 10k | Resistor_SMD:R_0402_1005Metric |  | 1→AUX_OEB; 2→3V3 _outputs disabled at boot_ |
| R18 | R | 10k | Resistor_SMD:R_0402_1005Metric |  | 1→SYN_INTR; 2→3V3 |
| Y1 **DNP** | Crystal_GND24 | 25MHz | Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm |  | 1→XA_DNP; 2→GND; 3(3)→XB_DNP; 4(4)→GND _DNP; footprint for optional 25 MHz crystal (XA/XB would need connecting)_ |
| R19 | R | 47 | Resistor_SMD:R_0402_1005Metric |  | 1→AUX_CLK0; 2→AUX_OUT |
| J5 | Conn_Coaxial | BNC AUX OUT | Connector_Coaxial:BNC_Amphenol_031-5539_Vertical | 031-5539 | 1(In)→AUX_OUT; 2(Ext)→GND _rear panel; 3.3V CMOS, filter for LNB/Pluto TBD_ |
| TP12 | TestPoint | AUX_OUT | TestPoint:TestPoint_Pad_D1.5mm |  | 1→AUX_OUT |
| TP13 | TestPoint | PPS_OUT | TestPoint:TestPoint_Pad_D1.5mm |  | 1→PPS_OUT |

## Sivu: MCU_UI

RP2350-Plus (omat symboli ja jalanjälki), I2C0-pullupit, OLED-, enkooderi- ja LED-liittimet (WS2812 tasonsiirto 74AHCT1G125 5V:lle), GNSS-reset-, RUN- ja spare-GPIO-liittimet.

| Viite | Osa | Arvo | Jalanjälki | MPN | Pinnit → netit |
|---|---|---|---|---|---|
| A1 | RP2350-Plus | RP2350-Plus | HamREF:RP2350-Plus_Castellated | RP2350-Plus | 1(GP0)→GNSS_RXD; 2(GP1)→GNSS_TXD; 3(GND)→GND; 4(GP2)→I2C1_SDA; 5(GP3)→I2C1_SCL; 6(GP4)→I2C0_SDA; 7(GP5)→I2C0_SCL; 8(GND)→GND; 9(GP6)→PPS_GNSS; 10(GP7)→OCXO_10M_3V3; 11(GP8)→PPS_MCU; 12(GP9)→GNSS_RESET; 13(GND)→GND; 14(GP10)→GNSS_EXTINT; 15(GP11)→ENC_A; 16(GP12)→ENC_B; 17(GP13)→ENC_SW; 18(GND)→GND; 19(GP14)→LED_DATA_3V3; 20(GP15)→AUX_OEB; 21(GP16)→GP16_OCXO_FLT; 22(GP17)→GP17; 23(GND)→GND; 24(GP18)→GP18; 25(GP19)→GP19; 26(GP20)→GP20; 27(GP21)→OCXO_EN; 28(GND)→GND; 29(GP22)→SYN_INTR; 30(RUN)→RUN_MOD; 31(GP26)→ADC_5V; 32(GP27)→ADC_NTC; 33(GND)→GND; 34(GP28)→ADC_EFC; 36(3V3(OUT))→3V3; 38(GND)→GND; 39(VSYS)→VSYS; 40(VBUS)→VBUS_MOD _footprint to be drawn from STEP/drawing; see docs_ |
| R20 | R | 4.7k | Resistor_SMD:R_0402_1005Metric |  | 1→I2C0_SDA; 2→3V3 |
| R21 | R | 4.7k | Resistor_SMD:R_0402_1005Metric |  | 1→I2C0_SCL; 2→3V3 |
| C35 | C | 10uF 10V | Capacitor_SMD:C_0805_2012Metric |  | 1→3V3; 2→GND |
| C36 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→3V3; 2→GND |
| J6 | Conn_01x04 | J OLED 0.91in I2C | Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical |  | 1(Pin_1)→GND; 2(Pin_2)→3V3; 3(Pin_3)→I2C0_SCL; 4(Pin_4)→I2C0_SDA |
| J7 | Conn_01x04 | J ENCODER | Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical |  | 1(Pin_1)→ENC_A; 2(Pin_2)→ENC_B; 3(Pin_3)→ENC_SW; 4(Pin_4)→GND |
| C37 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→ENC_A; 2→GND |
| C38 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→ENC_B; 2→GND |
| C39 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→ENC_SW; 2→GND |
| U10 | 74AHCT1G125 | 74AHCT1G125 | Package_TO_SOT_SMD:SOT-23-5 | SN74AHCT1G125DBVR | 1→GND; 2→LED_DATA_3V3; 3(GND)→GND; 4→LED_DATA_BUF; 5(VCC)→5V_MAIN _3V3 -> 5V level shift for WS2812_ |
| R22 | R | 330 | Resistor_SMD:R_0402_1005Metric |  | 1→LED_DATA_BUF; 2→LED_DATA |
| C40 | C | 100nF | Capacitor_SMD:C_0402_1005Metric |  | 1→5V_MAIN; 2→GND |
| J8 | Conn_01x03 | J LEDS (2x WS2812B) | Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical |  | 1(Pin_1)→5V_MAIN; 2(Pin_2)→LED_DATA; 3(Pin_3)→GND |
| J9 | Conn_01x02 | J RESET GNSS (short=reset) | Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical |  | 1(Pin_1)→GNSS_RESET; 2(Pin_2)→GND |
| J10 | Conn_01x02 | J RUN (short=MCU reset) | Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical |  | 1(Pin_1)→RUN_MOD; 2(Pin_2)→GND |
| J11 | Conn_01x07 | J SPARE GPIO | Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical |  | 1(Pin_1)→GP17; 2(Pin_2)→GP18; 3(Pin_3)→GP19; 4(Pin_4)→GP20; 5(Pin_5)→3V3; 6(Pin_6)→GND; 7(Pin_7)→5V_MAIN |
| TP14 | TestPoint | GP16_OCXO_FLT | TestPoint:TestPoint_Pad_D1.5mm |  | 1→GP16_OCXO_FLT |

## Avoimet kohdat (v0.1 → layout)

1. **RP2350-Plus-jalanjälki** (`hamref.pretty`) on paikkamerkki (pad 3.8×1.6 mm, rivit 19.8 mm välein). Tarkista Waveshare STEP-/mittapiirroksesta ennen layoutia; USB-C-pää ulkonee, tarvitaan reunasijoitus tai leikkaus.
2. **OCXO-jalanjälki**: OSC5A2B02:n pinnigeometriaa ei ole vahvistettu; paikkamerkkinä 1×5-header, pad N = OCXO-pinni N (datasheet bottom view). Mittaa kappaleesta.
3. **Si5351C ilman kidettä**: CLKIN-käyttö ilman XTAL:ia pitää varmistaa Skyworksin AN619/datasheetistä ja oikealla piirillä; Y1 on DNP varalle (XA/XB-nettien kytkentä).
4. **Si5351C EP-koko** (2.6×2.6 vs 2.7×2.7 mm) ja jalanjälki varmistettava valmistajan land patternista.
5. **AD5693R**: gain ×2 -tilassa VDD (5 V) on rajalla (VREF+1.5 V); firmware rajaa koodin ~4.0 V:iin. Tarkista datasheetin headroom.
6. **REF OUT** on HCMOS-neliöaalto (47 Ω sarjassa). Jos tarvitaan sini +7 dBm, lisää alipäästösuodatin (varaa tilaa layoutissa). AUX OUT 3.3 V CMOS; LNB (27 MHz) ja Pluto (40 MHz) tarvitsevat tasosovituksen/suodatuksen – ratkaistaan bring-upissa.
7. **GNSS-antennibias**: LEA-M8S V_ANT/VCC_RF -ratkaisu sopii nimellisesti 3 V antenneille. Ulkoinen 5 V bias (L 27 nH + oma LDO) ei ole mukana v0.1:ssä.
8. **LP5907 EN** sidottu IN:iin (aina päällä). TPS2065C:ssä virtaraja on kiinteä (~1 A), ei R_ILIM:iä.
9. **GP16 = OCXO_FLT** (TPS2065C:n FLT, avoin nielu, pullup 100k); spare-GPIO:t GP17–GP20 J SPARE -liittimessä.
10. Polyfuse- ja diodi-MPN:t ovat ehdotuksia – tarkista saatavuus ennen tilausta.

## PCB v0.1 (layout)

Tiedosto: `hardware/proto-v0.1/hamref_proto_v0_1.kicad_pcb` (generoitu: `hardware/tools/build_pcb.py` + Freerouting 1.9.0).

- 100 × 100 mm, 4 kerrosta: F.Cu (osat + signaalit), In1.Cu = yhtenäinen GND-taso, In2.Cu = signaali-/virtareititys, B.Cu = signaalit + GND-valu. Kaikki osat ylhäällä.
- RP2350-Plus juotetaan castellated-padeilla oikeaan reunaan (USB-C ylöspäin). Moduulin rungon alla on kielletty-alue (ei johtoja/läpivientejä F.Cu:lla).
- Takapaneelirivi ylhäällä: SMA (GNSS), BNC REF OUT, BNC 1PPS OUT, BNC AUX OUT. Käyttöliittymäpinnit (OLED, enkooderi, LED, reset, spare) ja testipisteet alareunassa.
- LEA-M8S kierretty niin, että RF_IN (pinni 16) on lähimpänä SMA:ta; GNSS_RF on lukittu 0.37 mm:n johto F.Cu:lla In1-GND-tason päällä (50 ohm arvio, 0.21 mm prepreg – tarkista valmistajan pinoamasta).
- Virtaverkot (5V_MAIN, 5V_OCXO, 3V3, 3V3_GNSS, 5V_DAC, VSYS, VBUS_MOD) reititetty 0.5 mm:llä, muut 0.2 mm; clearance 0.2 mm, läpivienti 0.6/0.3 mm.
- Jokaisella SMD-GND-padilla on oma läpivienti In1-maatasolle; Si5351C:n EP:ssä 4 lämpö-/maaläpivientiä.
- DRC (KiCad 7.0.11, `WriteDRCReport`): 0 kytkemätöntä, 0 clearance-virhettä, ei silkkipäällekkäisyyksiä. Jäljellä vain yksi `silk_over_copper` (RP2350-Plus-jalanjäljen ääriviiva castellated-padien kohdalla) ja `lib_footprint_issues` (projektin omat jalanjäljet).
- Silkki: logo "HamREF by OH2LAK" + satelliitti on vektoroitu kotelon mockup-kuvasta (`hardware/tools/make_logo.py` → `logo/hamref_logo.json`) ja sijoitettu levyn vasempaan alakulmaan. Tunnisteet (`silk_pass.py`) asetetaan reitityksen jälkeen vapaaseen kohtaan (0,8 mm); tiheimmän alueen tunnisteet (C30, C35, R4, R9, R10, R14, R17, R18, R19, FB2 ym.) ovat F.Fab-kerroksella. OCXO:n "estimated"-varoitus on yhtenä tekstinä OCXO:n ääriviivan sisällä.
- 3D-mallit: KiCadin vakiojalanjäljet viittaavat 3D-malleihin, ja polut kirjoitetaan muotoon `${KICAD10_3DMODEL_DIR}/...step` (muuttujat `MODEL_VAR`, `MODEL_EXT` ympäristömuuttujina `make_all.sh`:lle). OCXO:lle ja RP2350-Plus-moduulille on yksinkertaiset laatikkomallit `hamref.3dshapes/` (mitat arvioita).

### PCB:n avoimet kohdat

1. **OCXO-jalanjälki on arvio** (pinnit ±10.16 mm ruudukossa). Mittaa oikea OSC5A2B02 ennen tilausta ja korjaa `OCXO_OSC5A2B02_EST.kicad_mod`; reititys on tehtävä uudelleen (`make_all.sh`).
2. SMA- ja BNC-liittimet ovat pystymalleja (piirilevylle pystyyn). Kotelon takapaneeliin tarvitaan myöhemmin reunaan asennettavat mallit (v0.2).
3. Sijoittelu on automaattinen: tarkista käsin RF-alue, OCXO:n ympäristö (lämpö!) ja GND-paluuvirrat.
4. Pinoama (50 ohm:n johdon leveys) ja viivakoko on tarkistettava valitun valmistajan (esim. JLCPCB 4-layer) impedanssilaskurilla.
5. Gerberit ja pick-and-place eivät vielä ole mukana; tehdään kun layout on hyväksytty.
