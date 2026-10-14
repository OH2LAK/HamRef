# HamREF – arkkitehtuuri ja projektisuunnitelma (v0.10)

## Tavoite
Pieni tuote radioamatöörin asemalle, joka tarjoaa:
1. Jatkuvan, GNSS-referoidun **10 MHz** taajuusreferenssin laitteiden lukitusta varten (esim. transceiverit, synteesit, mittalaitteet).
2. Tarkan **kellonajan tietokoneelle** (NTP/PTP-tyylinen palvelu), jotta FT8 ja muut digimoodit pysyvät ajassa.
3. Statuksen näyttämiseen pienellä OLED-näytöllä ja kahdella monivärisellä tilaledillä (GPSDO, NTP); parametrien hallinta etupaneelin enkooderilla ja/tai USB:n kautta.

Erik: OH2LAK / OH2CH, Finskas Networks Oy. Varastossa **82 kpl LEA-M8S-0-10** -moduleita — suunnittelu lukitaan näihin, ei LEA-M8T:hen.

## Keskeinen tekninen huomio: miksi ei suoraan 10 MHz GNSS-piiristä
LEA-M8S:ssä (Data sheet UBX-16010205 R05, HIM UBX-15030060 R07) on vain yksi konfiguroitava TIMEPULSE-pinni (pin 28), taajuusalue 0.25 Hz…10 MHz, PPS-tarkkuus RMS 30 ns / 99% 60 ns. TIMEPULSE on **digitaalisesti syntetisoitu pulssijuna** (TCXO + fraktionaalinen N-synteesi), ei analoginen puhdas oskillaattori — 10 MHz-tilassa se kärsii merkittävästä vaihekohinasta/jitteristä (30 ns-luokan pulssikohtainen hyppely on paljon 10 MHz:n jaksonaikaan, 100 ns, nähden), mahdollisista vaihehypyistä sekuntirajalla, eikä tarjoa holdoveria jos GNSS-lukko katoaa.

→ Ratkaisu: klassinen GPSDO-arkkitehtuuri. LEA-M8S:n TIMEPULSE käytetään **1PPS**-tilassa (RMS 30 ns), ja tämä yksi PPS-signaali ohjaa MCU:n kautta kahta asiaa samanaikaisesti:
- **Erillisen OCXO/TCXO:n kurittamista (disciplining)** — OCXO pyörii vapaana, MCU vertaa sen taajuutta PPS:ään pitkällä aikavakiolla (100–1000 s) ja säätää EFC-jännitettä DAC:lla. Lopputulos: OCXO:n matala vaihekohina + GNSS:n pitkän aikavälin absoluuttinen tarkkuus + holdover-kyky.
- **NTP/aikapalvelun aikapohjaa** samasta PPS+NMEA/UBX-datasta.

## Päätökset tähän mennessä
- GNSS-moduuli: **LEA-M8S** (82 kpl varastossa). Footprint ja pinnijärjestys ovat samat kuin LEA-M8T:llä (HIM kuva 5 / taulukko 2: 22,4 × 17,0 mm); erot vain M8T:n SPI/D_SEL-toiminnoissa (pinnit 1–2, 5), joita HamREF ei tarvitse.
- Antenni: **aktiivinen ulkoantenni** (HIM 2.4.2–2.4.4: käytä antennisupervisoria, R_BIAS-vastus pakollinen sarjaan V_ANT:iin oikosulkusuojaksi, koska ulkoantennin kaapeli on aina riski; VCC_RF→V_ANT 10 Ω:n kautta jos antennin jännite sopii moduulin syöttöön, muuten erillinen suodatettu syöttö per HIM kuva 12).
- Vaihe: **prototyyppi omaan käyttöön ensin**.
- Kotelo: **Fischer Elektronik AKG 105.26 (tuote AKG1052680ME)** — ekstrudoitu alumiininen minikotelo, 105 × 100,3 × 26 mm, luonnonanodisoitu, integroidut jäähdytysripa-urat, 100 mm:n eurokortille. Ks. "Kotelo ja käyttöliittymä" alla.
- Näyttö: **~~pieni väri-TFT, SPI, 240x240~~ → 0.91" 128x32 mono-OLED, I2C, SSD1306-luokkaa** — lukittu valinta, ks. "Näyttövalinta" alla.
- MCU: **~~ESP32-S3~~ → RP2350A, toteutuksena valmis Pico-muotoinen RP2350A-kortti (ensisijaisesti Waveshare RP2350-Plus, USB-C)** — MCU lukittu 2026-10-14, kortin valinta päivitetty 2026-10-14 (ks. "USB-C-kortin valinta"). Koska HamREF:stä halutaan **rakennussarjamainen** (helppo koota itse), käytetään valmista Pico 2 -korttia eikä omaa RP2350-piiriä/flashia/kidettä omalla PCB:llä. Perusteet: PIO-lohkot antavat deterministisen 10 MHz -laskennan ja 1PPS-aikaleimauksen ilman WiFi-häiriötä, natiivi USB (TinyUSB), UF2-päivitys. WiFi ei ole v1:ssä tarpeen, koska USB hoitaa kellopalvelun. Ks. "MCU-valinta" alla.
- **Käyttöteho ja kellopalvelu: USB** (ks. alla) — sekä virta että data yhdestä USB-liitännästä.

## Kotelo ja käyttöliittymä (päivitetty valitun kotelon mukaan)

Kotelo on lukittu: **Fischer Elektronik AKG 105.26** (AKG1052680ME) — kaksi puolikuorta jotka liukuvat toisiinsa, 100 mm:n eurokortille. Mitat datalehden mukaan: leveys 105 mm, korkeus 26 mm, syvyys (D) 100,3 mm. Etu-/takapaneelit ovat erilliset 2 mm:n kansilevyt.

26 mm sisäkorkeus muuttaa aiempaa käyttöliittymäsuunnitelmaa:
- **Väri-TFT (240x240) ei mahdu** — sekä itse moduuli että sen liitin/piirilevyn paksuus vievät tyypillisesti enemmän kuin 26 mm jää käytettäväksi kortin molemmin puolin. → vaihdettu **0.91" 128x32 mono-OLEDiin** (I2C, SSD1306-luokkaa, ~36×12,5 mm PCB). Tarkka koko-/piirilevyvertailu ks. "Näyttövalinta" alla.
- **Enkooderi mahtuu kuitenkin** — tarkistettu EC11-luokan enkooderin mitat: runko n. 11,7 × 12–13 mm, korkeus vain 4,5–8,5 mm mallista riippuen, paneelin läpivientiholkki ø7 mm ([Farnell EC11 datasheet](https://www.farnell.com/datasheets/1837001.pdf)). Tämä mahtuu reilusti 22 mm:n sisäkorkeuteen, joten alkuperäinen "ei mahdu" -päätös oli liian varovainen. → **Etupaneeliin tulee EC11-tyyppinen enkooderi** (usein sisäänrakennetulla painikkeella) OLED-valikon selailuun ja parametrien säätöön.
- **Tilan ilmaisu: kaksi monivärista (RGB/bi-color) tilaledia**: **GPSDO**-ledi (väri+vilkku/kiinteä kertoo OCXO:n kuritustilan, esim. vihreä kiinteä = disciplined, keltainen vilkkuva = acquiring/hakee lukkoa, punainen = vika) ja **NTP**-ledi (vastaavasti ajanjakelun tilan, esim. vihreä kiinteä = tarjoaa validia aikaa, keltainen vilkkuva = odottaa GNSS-fixiä, punainen = ei USB-host-yhteyttä/vika).
- **Parametrien hallinta: etupaneelin enkooderi + OLED-valikko, ja/tai USB:n kautta.**
- **Takapaneelin liittimet**: SMA (GNSS-antenni), BNC × 2 (1PPS OUT, REF OUT), USB-C (host computer + virta, 5V). 1PPS saa oman fyysisen BNC-lähtönsä ulkoisia laitteita (taajuuslaskuri, oskilloskooppi ym.) varten USB-kellopalvelun rinnalle.
- 26 mm sisäkorkeus rajaa yhä **kortin komponenttikorkeuden molemmin puolin** — OCXO-valinnassa pitää tarkistaa fyysinen korkeus tämän kotelon suhteen, ei vain sähköiset ominaisuudet. Tämä on avoin riski, ks. alla.

## Näyttövalinta: 0.91" 128x32 OLED (lukittu)

Tarkennettu sisäkorkeus on **22 mm** (26 mm kotelo miinus seinämät/marginaalit). Vertailtiin kahta yleisintä pientä I2C-OLED-kokoa niiden todellisen piirilevyn mittojen perusteella (ei pelkän näyttödiagonaalin):

| Moduuli | Piirilevyn koko | Mahtuuko 22 mm:ään? |
|---|---|---|
| 0.91" 128x32 (esim. Waveshare-tyyppinen 4-pin I2C) | ~36 × 12,5 mm | **Kyllä**, reilusti — n. 9,5 mm marginaalia kiinnitykseen |
| 0.91" 128x32 (Adafruit STEMMA QT, isommat kiinnitysreiät) | 20 × 35 mm | Kyllä (20 mm < 22 mm), niukemmin |
| 0.96" 128x64 (esim. Adafruit STEMMA QT / useimmat geneeriset SSD1306-moduulit) | ~26,7–29,2 × 29,2 mm (lähes neliö) | **Ei** — lyhyempikin sivu (~26,7 mm) ylittää 22 mm:n rajan |

→ **Valinta: 0.91" 128x32 I2C OLED, SSD1306-ajuri**, esim. geneerinen 4-pin moduuli (~36 × 12,5 mm PCB, VCC/GND/SDA/SCL). Mahtuu landscape-asennossa etupaneeliin reilulla marginaalilla. Tekstiasettelut: ks. OLED Layout Variants -mockup (oletuksena 3 riviä).

Konseptikuvat (mittasuhteet oikein datalehden mukaan):
- Etu-/takapaneeli-mockup kotelon mitoilla: `https://claude.ai/artifact/WYU3QZwbzuxi1QUfCSpZFV`
- OLED-tekstivariantit: `https://claude.ai/artifact/8gpZwQhh3ehsbZSFcEQK6K`
- Aiempi, jo vanhentunut yleismockup (värinäyttö+enkooderi, ei sidottu tiettyyn koteloon): `https://claude.ai/artifact/QKyhnXYtYmfK1mJ8LYiwAB`

### Prototyypin OLED-moduuli (tilattu 2026-10-14)
Prototyyppeihin tilattu 5 kpl 0.91" 128×32 I2C OLED -moduuleja (Yeluft, valkoinen, nastat esijuotettu). Tiedot myyntisivun kuvista (`docs/datasheets/OLED_0.91_I2C_proto/`; kuvat ovat myyjän, ei virallinen datalehti — varmista mitat kaliipereilla kun moduulit saapuvat):
- **Mitat:** piirilevy **38,00 × 12,00 mm** (levyn korkeus 11,50 mm); lasi 30,00 mm pitkä ja päättyy 3,00 mm:n päähän levyn oikeasta reunasta; **aktiivinen alue 22,38 × 5,58 mm**, alkaa n. 7,1 mm levyn vasemmasta reunasta (8,52 mm oikeasta reunasta) ja n. 2,43 mm levyn yläreunasta. FPC-taittoalue oikeassa päässä.
- **Ei kiinnitysreikiä** — kiinnitys etupaneeliin liimaamalla/kehyksellä/pidikkeellä, ei ruuveilla.
- **Liitäntä:** 4 reikää/juotospadia 2,54 mm:n välein vasemmassa päässä, järjestys **GND (neliöpadi), VCC, SCL, SDA**. Nastalista on esijuotettu; poistettavissa tai korvattavissa johdoilla.
- **Elektroniikka:** SSD1306-luokan ohjain (ruudulla "091OLED"), moduulilla XC6206 3,3 V:n LDO → **VCC 3,3–5 V**, I2C-pull-upit 4,7 kΩ moduulin 3,3 V:iin (SCL, SDA), reset-RC + diodi. Käytä Pico 2:n 3V3(OUT):a.
- **I2C-osoite:** ei näy kuvissa (todennäköisesti 0x3C) — varmista I2C-skannauksella.
- Etupaneelin ikkuna: mitoitetaan aktiivisen alueen mukaan (22,38 × 5,58 mm) + toleranssi/reunus; tarkka aukko ja kiinnitys piirretään kun moduulit on mitattu.

### Tuotantonäyttö (avoin)
Yllä oleva Yeluft-moduuli on **vain prototyyppikappale**. Tuotantoversioon (rakennussarja) etsitään paremmin dokumentoitu ja halvempi näyttö. Vaatimukset, joilla vaihto ei vaadi muutoksia firmwareen tai paneelin perusratkaisuun:
- **Ohjain ja liitäntä:** SSD1306 (tai yhteensopiva), 128×32, I2C, 3,3 V — ohjelmisto pysyy samana.
- **Dokumentointi:** tunnetun valmistajan paneeli (esim. Winstar, Midas, Newhaven, Densitron), jolla on oikea datalehti ja osanumero (mitat, toleranssit, I2C-osoite, alustusarvot). Myyjän oma kuva ei riitä.
- **Mitat:** piirilevy enintään n. 38 × 12 mm (22 mm:n sisäkorkeus); kiinnitysreiät mieluiten mukana (prototyypissä ei ole).
- **Saatavuus ja hinta:** sama osanumero saatavilla myös myöhemmin; hinta vertailtava rakennussarjan määrällä.
- **Vaihtoehto:** paljas 0.91" OLED-paneeli (14-nastainen FPC) ilman moduulin PCB:tä, liitettynä suoraan omalle kortille. Prototyyppimoduulin kaavio on käytännössä paneeli + muutama kondensaattori (C1/C2 105, C4 2,2 µF, C5 4,7 µF, R4 560 kΩ), joten oma kytkentä on mahdollinen — vaatii enemmän layout-työtä, mutta on halvin ja tarkimmin dokumentoitu reitti, jos oma kortti on joka tapauksessa tulossa.
- **Mekaniikka:** etupaneelin ikkunan ja kiinnityksen suunnittelu pidetään riittävän yleisenä, jotta aktiivisen alueen ja ulkomittojen pienet erot eri näytöillä eivät vaadi uutta paneelikaiverrusta (esim. ikkunan reunus + sisäpuolinen painokehys).

## OCXO/TCXO-suositus

Ehdotus: **5 V:n analogisella EFC-tulolla varustettu OCXO**, koska se sopii suoraan USB-virransyöttöön (ei tarvita 12V-hakkuria) ja koska tämä on juuri se komponenttiluokka jota ham-yhteisön GPSDO-rakentajat ovat käyttäneet vuosia — hyvin dokumentoitu, halpa ja helposti saatavilla surplus-markkinoilta (eBay), esim. paulvdiyblogs-GPSDO-projektin testaamat ja monen muun DIY-GPSDO:n käyttämät:
- **Trimble 65256** (5V, sini-ulostulo)
- **IsoTemp 143-141** (5V, neliöaalto-ulostulo)
- **CTI OC5SVC25** (5V, neliöaalto)
- **Bliley NV47M1008** (5V, neliöaalto)

Nämä ovat kaikki 5V analogisella EFC-piikillä varustettuja, eli MCU→I2C-DAC (esim. MCP4725)→RC-suodatin→EFC toimii suoraan, ilman erillistä jännitesäädintä OCXO:lle.

Vaihtoehto (jos halutaan välttää analoginen DAC+silmukkasuodatin kokonaan): **SiTime-sarjan digitaalisesti viritettävät MEMS-OCXO:t** (esim. SiT5711-tyyppinen, 3.3V, I2C-ohjaus) tarjoavat erittäin hyvän ±5–8 ppb -stabiiliuden ja pienen koon (9×7mm) ilman analogista EFC-silmukkaa — MCU kirjoittaa taajuuskorjauksen suoraan I2C:n yli. Huom: SiT5711 on merkitty "Not recommended for new designs" (SiTime ohjaa SiT5801:een), ja SiTime-osat yleensä hankitaan jakelijan kautta (Mouser/Digikey/SiTimeDirect) eivätkä ole yhtä helposti/halvasti saatavilla pienissä erissä kuin surplus-OCXO:t eBaysta. Prototyyppivaiheeseen suosittelen aloittamaan halvemmalla ja paremmin dokumentoidulla analogisella 5V OCXO:lla; SiTime-reitti kannattaa harkita vasta jos päädytään pieneen sarjaan asti.

**Huomio virransyötöstä (liittyy USB-kysymykseen alla):** pienetkin OCXO:t vetävät lämmitysvaiheessa (ensimmäiset ~3–5 min kylmästä käynnistyksestä) merkittävästi enemmän virtaa (tyypillisesti 300–700 mA) kuin stabiloituneena (~100–200 mA). Tämä pitää ottaa huomioon USB-virtabudjetissa ja mahdollisesti puskuroida isolla elektrolyyttikondensaattorilla, ettei isäntäkoneen USB-portin virtarajoitus laukea käynnistyksessä.

## OCXO-ehdokkaat (selvitys 2026-10-14)

Kriteerit: 10 MHz, 5 V syöttö, analoginen EFC, korkeus selvästi alle 22 mm, hyvä saatavuus. Hinnat ja varastot ovat 2026-10-14 hakutuloksista ja jälleenmyyjien sivuilta; vahvista ennen tilausta. Virrat on laskettu datalehtien tehoarvoista (P/5 V), eli ne ovat arvioita.

| # | Osa | Koko (mm) | EFC | Teho / virta (5 V, arvio) | Stabiilisuus | Hinta ja saatavuus |
|---|---|---|---|---|---|---|
| 1 | **Abracon AOCJY1A-10.000MHZ** (DIP-14, CMOS; "-SW" = siniaalto) | 20,8 × 13,2 × 8,2 | 0…Vdd, ±5 ppm, 10 kΩ | käynnistys 2,0 W (~0,4 A), vakio 1,0 W (~0,2 A) | ±50 ppb (0…50 °C); vanheneminen ±500 ppb/v | Future Electronics 89–95 $/kpl (MOQ 5 pakkaus, varasto 0, tehtaan toimitusaika 27 vk); Farnell IE 87,38 € ex VAT (26 vk); eräs jälleenmyyjä ilmoittaa 1 586 kpl varastossa (89 $) |
| 2 | **Abracon AOCJY-…A (5 V -versio)** | 25,4 × 22,1 × 12,7 | 0…Vdd, ±0,7 ppm, 10 kΩ | käynnistys 3,6 W (~0,72 A), vakio 1,4 W (~0,28 A) | ±5 ppb (0…50 °C), parempi vaihekohina | Hintaa ja varastoa ei löytynyt (Abracon: ei verkkokaupan varastossa, myynti Digi-Keyn kautta); 5 V:n tilauskoodi vahvistettava |
| 3 | **CTS 1188** (SMD/muu, 5 V = koodi D) | 25,8 × 25,8 × 12,7 | 0…Vcc, ±0,7 ppm min | 1,2 W vakio (taulukon tulkinta epävarma) | ±10…100 ppb valinnan mukaan | Hintaa ei löytynyt; tilauskoodi 1188-xxGEDHV-10M000-tyyppinen |
| 4 | Surplus: Bliley NV47M1008 (10 MHz, 5 V, neliö, EFC) | ei vahvistettu | EFC | surplus-OCXO-luokka | ei vahvistettu | eBay 11–24 $ + noin 20 $ postit (useita listauksia, osa loppunut) |
| 5 | Surplus: Trimble 65256 | ei vahvistettu | EFC (VL-pinni) | surplus-OCXO-luokka | ei vahvistettu | eBay noin 24 $ perillä (vanha foorumitieto) |

**Havaintoja:**
- Uudet osat 1–3 mahtuvat 22 mm:n sisäkorkeuteen helposti (8,2–12,7 mm). Surplus-osien (4–5) korkeus on vielä mittaamatta.
- **Virta:** AOCJY1A:n käynnistysvirta on noin 0,4 A (osa 2:lla noin 0,72 A), mikä yhdessä muun elektroniikan (noin 0,1–0,15 A) kanssa on joko hieman yli tai selvästi yli USB 2.0:n 500 mA:n. OCXO:n load switch virrarajalla ja pehmeäkäynnistyksellä on siis tarpeen, ja ulkoinen 5 V -syöttö kannattaa varata protoon.
- **EFC:** ±5 ppm:n pull-alue (AOCJY1A) vaatii hienojakoisen DAC:n: 12 bitillä askel olisi noin 2,4 ppb, 16 bitillä noin 0,15 ppb. Tämä tukee 16-bittistä DAC-paikkaa proto-PCB:llä. ±0,7 ppm:n osilla (2, 3) 12 bitin askel olisi noin 0,34 ppb.
- Vaihekohina (10 MHz, osa 1): −90 dBc/Hz @ 10 Hz, −120 @ 100 Hz, −145 @ 1 kHz, −150 @ 10 kHz.
- **Hinta:** uusien osien hinta (noin 90 €) on suuri rakennussarjaan; surplus on selvästi halvempaa, mutta saatavuus ja mitat vaihtelevat.

**Suositus:** protoon AOCJY1A (pieni, hyvin dokumentoitu, uusi, DIP-14-pistokesovitin helppo) ja rinnalle yksi surplus-OCXO halvempana vertailuna. Lopullinen valinta tehdään kun toimitusaika (26–27 vk) ja sarjan hinta on selvillä; osan 2 (5 V -versio) hinta ja saatavuus tarkistettava Digi-Keyltä.

## USB: virta + kellopalvelu samasta liitännästä — kyllä, toimiva ratkaisu

Tähän on hyviä, tunnettuja esikuvia ham-/DIY-piireistä:

- **[ddrown/usb-gps](https://github.com/ddrown/usb-gps)** — STM32F4 + GPS-moduuli, PPS kytketty suoraan MCU:n GPIO:hon, MCU näkyy isäntäkoneelle USB-CDC-ACM-sarjaporttina (`/dev/ttyACM0`). PC-puolen pieni apuohjelma ("ntp-shm") lukee sarjaportin datavirtaa ja kirjoittaa NTP:n shared-memory-rajapintaan, josta chrony/ntpd lukee ajan. Laite on virrallistettu suoraan USB:stä.
- **[quantum5.ca: DIY Stratum 1 NTP Server with a Serial Port](https://quantum5.ca/2023/01/24/diy-stratum-1-ntp-server-with-serial-port/)** — samantyyppinen lähestymistapa, dokumentoi tarkkuuden ja chrony-konfiguraation.
- Vaihtoehtoinen, "puhtaampi" reitti: MCU (RP2350:n natiivi USB + TinyUSB) esiintyy isäntäkoneelle **USB-CDC:n SERIAL_STATE-ilmoituksella toteutettuna virtuaalisena DCD-linjana**, joka nousee/laskee PPS-reunan tahdissa — Linuxin oma PPS-API/`pps-ldisc` sekä gpsd tukevat tätä natiivisti ilman erillistä host-puolen apuohjelmaa. Vaatii enemmän firmware-työtä TinyUSB:n kanssa.
- Kolmas vaihtoehto: MCU esiintyy **USB-Ethernet-laitteena (CDC-NCM/RNDIS)**, jolloin isäntäkone saa laitteelle virtuaalisen IP-osoitteen ja tavallinen chrony/ntpd-asiakas osoitetaan siihen — laite ajaa omaa pientä NTP-palvelinta tuolle virtuaaliverkolle.

**Suositus v1-prototyyppiin:** aloita yksinkertaisimmalla tavalla (USB-CDC-ACM sarjaportti + pieni PC-puolen apuohjelma chrony SHM/PPS-refclockille, kuten ddrown/usb-gps ja quantum5.ca) — nopein saada toimimaan, ms-luokan tarkkuus riittää FT8:aan reilusti. DCD-linja- tai USB-Ethernet-reittiin voi siirtyä myöhemmin.

Käytännössä: **yksi USB-kaapeli isäntäkoneeseen riittää sekä virtaan että kellopalveluun**, kunhan USB-portti/hubi pystyy antamaan OCXO:n lämmitysvaiheen huippuvirran — suositellaan itsevoimaista USB-hubia tai USB-C PD -syöttöä, ainakin kunnes lämmitysvirtapiikki on mitattu ja puskuroitu.

## MCU-valinta: RP2350 (Raspberry Pi Pico 2) — lukittu 2026-10-14

Vertailtiin ESP32-S3:a, klassista Arduinoa (ATmega328), RP2350:tä ja STM32:ta. Klassinen Arduino putosi pois (ei natiivia USB:tä, laskuri ei jaksa 10 MHz:ää, vähän muistia). Valinta: **RP2350 / Pico 2**.

**Perusteet:**
- **PIO-lohkot** (ja PWM-laskuri edge-count-tilassa) laskevat OCXO:n 10 MHz:n ja aikaleimaavat 1PPS-reunan laitteistotasolla deterministisesti — ei WiFi/RTOS-keskeytysjitteriä kuten ESP32:lla.
- **Natiivi USB (TinyUSB)**: CDC-ACM, myöhemmin virtuaalinen DCD tai CDC-NCM. Riittää virtaan + kellopalveluun + konfigurointiin.
- **UF2-bootloader (BOOTSEL)**: firmwarepäivitys vetämällä tiedosto asemalle.
- **Toolchain**: Pico SDK (C/C++) aikakriittisiin osiin, tai Arduino-Pico-core (Arduino IDE / PlatformIO) nopeaan prototypointiin.
- **Mekaniikka ja kokoonpano**: Pico 2 -kortti on n. 51 × 21 mm, 40 nastaa (26 käytettävää GPIO:ta; GP23–25 ja GP29 on varattu kortin sisäiseen käyttöön). Kortti kiinnitetään HamREF-pääkortille joko pistokelistoilla (helpoin rakennussarjassa, vaihdettavissa) tai juottamalla reunapadeilla (matalampi). Pico 2:n korkeus + pistoke on laskettava mukaan 22 mm:n sisäkorkeuteen. Oma RP2350-piiri (Minimal KiCad -referenssi, `docs/datasheets/RPi_Pico_2/`) **ei ole suunnitelmissa** — jätetty mahdolliseksi myöhemmäksi jatkokehitykseksi.

**Mitä menetetään ESP32-S3:een verrattuna:**
- Ei WiFiä (Pico 2 W:ssä olisi, jos tarvitaan myöhemmin). Ei WiFi-NTP:tä eikä web-UI:ta v1:ssä — korvataan USB-yhteydellä ja enkooderi+OLED-valikolla.
- Ei OTA-päivityksiä — UF2 USB:n yli riittää laitteelle, joka on tietokoneen vieressä.

**Yhteiset ratkaisut (ei muutu):** DAC on edelleen ulkoinen I2C-DAC (MCP4725 tms.) EFC-ohjaukseen; OLED I2C:llä; u-blox UART:lla; 10 MHz kannattaa puskuroida/jakaa ennen MCU:ta signaalitasojen ja laskentataajuuden hallitsemiseksi. Vaihtoehtona myöhemmin STM32 (hyvä timer-capture), ei tarpeen v1:ssä.

**Avoin:** PIO-pohjaisen taajuuslaskennan ja 1PPS-aikaleimauksen toteutus (laskurin laajennus 32 bittiin, PPS-latchi) validoidaan proof-of-conceptissa.

### Datalehtitarkistus (RP2350 datasheet RP-008373, Hardware design RP-008280) — 2026-10-14
Vahvistettu:
- USB 1.1 -kontrolleri ja PHY (Full Speed -laite), sisäiset pull-upit, ulkoisena vain 27 Ω sarjavastus D+/D−. Riittää CDC-ACM:lle ja myöhemmin CDC-NCM:lle.
- PIO:n tulossa 2 flipflopin synkronoija (+2 jaksoa viivettä, ohitettavissa nastakohtaisesti). 150 MHz:n clk_sys:llä aikaleimaus/laskenta n. 6,7 ns resoluutiolla; 10 MHz tulee samplatuksi n. 15-kertaisella nopeudella.
- PWM-laskuri tukee B-nastan reunalaskentaa (taajuusmittaus), mutta laskuri on 16-bittinen (ylivuoto 10 MHz:llä n. 6,5 ms) → **PIO (32-bit) on suositeltu tapa**.
- GPIO:t ovat **5 V-sietoisia** (kun siru on käynnissä) → 5 V:n OCXO:n neliöaalto voi mennä tuloon suoraan; puskuri on silti suositeltava reunojen siistimiseen.
- RP2350A: QFN-60, 30 GPIO:ta; Pico 2 käyttää A-versiota.

Huomioitavaa (virhelista, appendix D):
- **RP2350-E9 (A2-silikoni):** Bank 0 GPIO:n tulolla vuotovirta (~120 µA) jännitealueella VIL…VIH; sisäinen pull-down ei voita sitä (vaatii ≤8,2 kΩ ulkoisen vedon). → **Älä käytä sisäisiä pull-downeja tuloissa**; pull-up toimii. Tarkista Pico 2:n silikoniversio.
- **RP2350-E12 (A2–A4, lievennetty A3:ssa):** USB-tilasignaalien synkronointi puutteellinen, jos clk_sys ≤ clk_usb (48 MHz) → pidä clk_sys selvästi yli 48 MHz (esim. 150 MHz).
- **RP2350-E16:** USB_OTP_VDD:n häiriö voi korruptoida OTP-luvun → pidä syöttö siistinä (koskee omaa piirilevyä, ei valmista Pico 2 -korttia).

Myöhempi optimointi (ei v1:een): OCXO:n 10 MHz voidaan syöttää XIN:iin (XOSC pass-through, max 50 MHz), jolloin PLL tuottaa clk_sys:n (esim. 150 MHz = 15 × 10 MHz) lukittuna OCXO:hon ja 10 MHz:n laskenta muuttuu triviaaliksi (clk_sys-jaksot 1PPS-reunojen välillä). Haitat: bootrom/USB-boot olettaa oletuksena 12 MHz:n kiteen (muu taajuus vaatii peruuttamattoman OTP-asetuksen), eikä MCU:lla ole kelloa ennen OCXO:n käynnistymistä; vaatisi myös oman RP2350-piirin. Siksi v1:ssä pidetään kortin 12 MHz:n kide ja lasketaan 10 MHz PIO:lla.

## USB-C-kortin valinta: Waveshare RP2350-Plus (ensisijainen) — 2026-10-14

Virallinen Pico 2 käyttää micro-USB:tä, mutta takapaneeliin halutaan USB-C. Vertailtiin kolmea USB-C-korttia (lähteet: Waveshare-wikit, schematic ja STEP-malli kansiossa `docs/datasheets/Waveshare_RP2350-Plus/`):

| Kortti | GPIO padeilla | Tulos |
|---|---|---|
| DFRobot Beetle RP2350 | 11 | Hylätty: ei riitä (tarve 14–19). |
| Waveshare RP2350-Zero Mini | 20 reunalla + 9 juotospisteissä | Varavaihtoehto: komponentteja molemmilla puolilla, joten ei juotettavissa suoraan emolevyyn ilman nastalistaa. |
| **Waveshare RP2350-Plus** | 26 (GP0–GP22, GP26–GP28) | **Ensisijainen**: Pico 2 -yhteensopiva pinout, USB-C, castellated-reunat, alapuoli tyhjä. |

**RP2350-Plus (schematic RP2350_Plus.pdf, STEP RP2350_Plus_STEP.zip):**
- RP2350A, 12 MHz kide, flash 4 MB (W25Q32JVSSIQ) tai 16 MB (W25Q128JVSIQ); 4 MB riittää. Mallit: RP2350-Plus (ei nastalistoja) ja RP2350-Plus-M (valmiiksi juotetut nastalistat). Hinta noin 6–7 $.
- **Mitat (STEP):** PCB 21,0 × 51,0 mm (Pico-koko). USB-C-liitin työntyy PCB:n reunan yli noin 1,3 mm (kokonaispituus 52,3 mm); liittimen korkeus +3,25 mm ylä- ja 0,91 mm alapuolella. Muut komponentit vain yläpuolella, korkeintaan 2,5 mm (BOOT/RESET-painikkeet). Alapuolella ei ole muuta kuin USB-C-liitin, joten kortin voi juottaa castellated-reunoista suoraan emolevyyn.
- **Padit (Pico-nastajärjestys, 40 pinniä):** GPIO0–GPIO22 ja GPIO26–GPIO28 padeilla; pad 30 RUN, pad 35 ADC_VREF, pad 36 3V3, pad 37 3V3_EN (PWR_EN), pad 39 VSYS, pad 40 VBUS. GPIO23–25 ja GPIO29 eivät ole padeilla: GPIO25 = käyttäjä-LED (tavallinen LED, ei WS2812), GPIO24 = VBUS-tunnistus (jakaja 51k/100k), GPIO29 = VSYS-mittaus (ADC-jakaja), GPIO23 = regulaattorin MODE/SYNC.
- **Virtapolku:** VBUS-pad on suoraan USB-C:n VBUS (ei sulaketta kortilla). Diodi D1 (MBR230LSFT1G) on VBUS:n ja VSYS:n välissä; MP28164 buck-boost (max 2 A) saa tulonsa VSYS:stä ja tuottaa 3V3:n. Akkulaturi ETA6096 (tulo VBUS, akkuliitin PH1.25-2P, D2 VBAT→VSYS) on kortilla mutta käyttämätön. OCXO:n 5 V voidaan siten ottaa VBUS-padista ilman kortin diodin pudotusta, mutta sulake/suoja pitää tehdä emolevylle.
- **Huomioita:** USB-datalinjoissa 27 Ω sarjavastukset (R16/R17) kuten Pico 2:ssa. Käyttämätön laturi ja akkuliitin eivät saa olla kytkettynä; laturin lepovirta mitataan ensimmäisellä kortilla.

**Päätös:** suunnitellaan emolevy RP2350-Plus-korttia varten (juotettuna castellated-reunoista tai pistokelistoilla). Pico 2 (micro-USB) ja Zero Mini jäävät varavaihtoehdoiksi.

## GPIO-jako RP2350-Plus-padeille (ehdotus, 2026-10-14)

Periaatteet: UART/I2C-toiminnot on valittu RP2350:n kiinteisiin periferiapinneihin; PIO-tulot (1PPS, 10 MHz) voivat olla mitkä tahansa GPIO:t, joten ne sijoitetaan lähelle toisiaan reitityksen helpottamiseksi. Tulopinneille ei käytetä sisäisiä pull-down-vastuksia (errata E9; pull-up toimii). Pad-numerot ovat Pico-tyylisiä (40 pinniä).

| GPIO | Pad | Toiminto | Huomio |
|---|---|---|---|
| GP0 | 1 | UART0 TX → LEA-M8S RXD (pin 4) | NMEA/UBX, 9600 oletus, nostetaan tarvittaessa |
| GP1 | 2 | UART0 RX ← LEA-M8S TXD (pin 3) | |
| GP2 | 4 | I2C1 SDA → DAC | DAC omalla väylällä, jotta OLED-liikenne ei kytkeydy EFC-jännitteeseen |
| GP3 | 5 | I2C1 SCL → DAC | |
| GP4 | 6 | I2C0 SDA → OLED | 4,7 kΩ pull-upit moduulilla, älä kaksinkertaista |
| GP5 | 7 | I2C0 SCL → OLED | |
| GP6 | 9 | **1PPS IN** (LEA-M8S TIMEPULSE, pin 28, puskuroituna) | PIO-aikaleima |
| GP7 | 10 | **10 MHz IN** (OCXO, puskuroituna/neliöitynä) | PIO-laskuri; GP7 on PWM-slice 3 B-pinni, joten PWM-edge-count on varakeino |
| GP8 | 11 | 1PPS OUT (MCU:n generoima, valinnainen) | v1:ssä BNC-lähtö tulee suoraan TIMEPULSE-puskurista |
| GP9 | 12 | LEA-M8S RESET_N (pin 10) | avokollektori/open-drain-tyyliin: ajetaan vain matalaksi |
| GP10 | 14 | LEA-M8S EXTINT0 (pin 27) | aikamerkki/aiding; varaus |
| GP11 | 15 | Enkooderi A | RC-suodatus + firmware-debounce |
| GP12 | 16 | Enkooderi B | |
| GP13 | 17 | Enkooderin painike | |
| GP14 | 19 | WS2812-ketju (2 RGB-LEDiä) | 3,3 V:n data → 5 V:n LED: käytä 5 V-tasonsiirtoa (esim. 74AHCT1G125) |
| GP15–GP20 | 20, 21, 22, 24, 25, 26 | Varalla: erilliset RGB-LEDit (2×3) | käytetään vain jos WS2812 hylätään |
| GP21 | 27 | OCXO-virran enable (load switch) | OCXO:n lämmitysvirran hallinta |
| GP22 | 29 | Vapaa (esim. PPS-tulon toinen kopio / varalla) | |
| GP26 | 31 | ADC0: 5 V -syötön / OCXO-virran mittaus | |
| GP27 | 32 | ADC1: lämpötila (NTC OCXO:n vieressä) | |
| GP28 | 34 | ADC2: EFC-jännitteen takaisinluku | |

Käyttö: perustoiminnot vaativat 15 GPIO:ta (GP0–GP14), OCXO-enable ja 3 ADC-kanavaa nostavat 19:ään; varapinnit (GP15–GP20, GP22) kattavat erillisten LEDien vaihtoehdon. GPIO23–25 ja GPIO29 eivät ole padeilla (kortin sisäiseen käyttöön). Antennin avoimen piirin tila (EXTINT1 / ANT_DET_N) luetaan UBX-viesteillä, joten se ei tarvitse MCU-pinniä.

**UF2/BOOTSEL kotelossa:** RP2350-Plus:n BOOT-painike on kortilla (QSPI_SS), ei padeilla. Toteuta firmwareen "reboot to BOOTSEL" -komento USB-CDC:n yli (ja/tai 1200 baudin avaus), ja vie RUN (pad 30) pinniriville resetiä varten.

## Proto-PCB v0.1 (bring-up-levy) — vaatimukset (ehdotus, 2026-10-14)

**Tarkoitus:** validoida sähköinen arkkitehtuuri (LEA-M8S + RP2350-Plus + DAC + OCXO + puskurit + virrat) ennen kotelon mukaan mitoitettua v0.2:ta. Ei yritetä mahduttaa koteloon; helppo mitattavuus ja muunneltavuus ovat tärkeämpiä.

**Rakenne:**
- 4-kerroslevy (SIG/GND/PWR/SIG) tai 2-kerroslevy yhtenäisellä maatasolla; 4 kerrosta suositellaan RF_IN:n 50 Ω:n johdolle ja OCXO:n puhtaalle maalle. Koko noin 100 × 100 mm.
- RP2350-Plus: naaraspistokelistat (Plus-M) vaihdettavuuden vuoksi protossa; castellated-juotto v0.2:ssa. USB-C-liitin ulos levyn reunasta.
- OCXO: pistokepaikka tai sovittimen paikka (OCXO-valinta avoin); EFC-, Vcc-, GND- ja RF-out-signaalit nastarivillä.
- LEA-M8S: footprint HIM:n mukaan (22,4 × 17,0 mm, 28 pinniä), antennisupervisor (R_BIAS sarjassa V_ANT:iin per HIM 2.4.2–2.4.4), SMA-liitin RF_IN:iin.
- Puskurit: 1PPS (TIMEPULSE → Schmitt-puskuri → MCU GP6 + BNC 1PPS OUT 50 Ω:n sarjavastuksella); 10 MHz (OCXO → neliöinti/puskuri → MCU GP7 + BNC REF OUT).
- DAC: paikka sekä 12-bittiselle (MCP4725, nopeat ensikokeet) että 16-bittiselle I2C-DAC:lle + vähäkohinainen referenssi/puskurioperaatiovahvistin EFC:lle (EFC-herkkyys vaihtelee OCXO:ssa tyypillisesti ±0,1…±5 ppm koko jännitealueella → 12 bitin askel olisi suuruusluokkaa 0,05–2,4 ppb, arvio; 16 bittiä antaa varmuutta).
- Käyttöliittymä: 4-pinninen I2C-header OLEDille (GND/VCC/SCL/SDA, kuten protomoduulissa), enkooderin ja WS2812-ketjun liittimet (sekä varalla erilliset RGB-ledit), RUN-header.

**Virta (arvioita, mitattava):**

| Kuorma | Arvio | Lähde |
|---|---|---|
| LEA-M8S (3,0 V) | 22–24 mA seuranta, max 67 mA | datalehti UBX-16010205 |
| Aktiiviantenni | 10–30 mA tyypillisesti | antennista riippuva |
| RP2350-Plus + OLED + DAC + puskurit | noin 60–100 mA | arvio |
| OCXO lämmitys | 300–700 mA | OCXO-luokan tyypillinen, tarkentuu osavalinnassa |
| OCXO vakiotila | noin 100–250 mA | OCXO-luokan tyypillinen |

Lämmitysvaiheen kokonaisvirta voi ylittää USB 2.0:n oletus-500 mA:n. Ratkaisu protossa: OCXO:n 5 V load switch virrarajalla ja pehmeäkäynnistyksellä (GP21 ohjaa), valinnainen ulkoinen 5 V -syöttö (jakkiliitin/pinnirivi) diodi-OR:illa VBUS:in kanssa, ja virran mittaus (GP26). GNSS:lle oma vähäkohinainen 3,0–3,3 V LDO 5 V:sta (LEA-M8S VCC 2,7–3,6 V), ei RP2350-Plus:n 3V3-rail. V_BCKP (pin 11) tarvitsee varmistuksen (1,4–3,6 V, noin 15 µA) lämpimiä aloituksia varten: superkondensaattori tai nappiparisto.

**Suojaus:** RP2350-Plus:n VBUS-pad (pad 40) on suoraan USB-C:n VBUS eikä kortilla ole sulaketta → emolevylle resetoitava sulake/virtarajoitin (esim. PTC tai load-switch) ja TVS-diodi. Tarkista kortin VBUS-johtimen kestävyys 1 A:lle STEP-/layout-tiedoista ennen kuin OCXO:n virta kulkee sen kautta; vaihtoehtona ulkoinen 5 V -syöttö OCXO:lle.

**Testipisteet:** 5 V, 3V3 (MCU), 3V3_GNSS, VCC_RF, EFC, 1PPS (MCU-puoli ja BNC), 10 MHz (puskurin jälkeen), UART TX/RX, I2C0/I2C1, GND-silmukat oskilloskoopille.

**Rinnalla (ohjelmistoriski, ei vaadi omaa levyä):** breadboard-testi PIO-pohjaiselle 10 MHz -laskennalle ja 1PPS-aikaleimaukselle Pico 2 / RP2350-Plus + LEA-M8S -breakout. Kun toimii, GPIO-jako yllä vahvistetaan ennen levyn tilausta.

**Avoin ennen tilausta:** OCXO-osavalinta (sovittimen nastajako), tuotantonäyttö (protossa riittää header), 10 MHz -lähdön muoto (neliö vs. sini, REF OUT -taso), antennin bias-jännite (V_ANT).

## Alustava lohkokaavio (tekstinä)
```
Aktiivinen GNSS-antenni (SMA, V_ANT + R_BIAS, antennisupervisor)
        |
    LEA-M8S  --UART(UBX/NMEA)--> RP2350 (Pico 2) <--enkooderi (+painike)
        |TIMEPULSE (1PPS, RMS 30ns)      |
        |                                |--I2C--> 0.91" 128x32 OLED (valikko/status)
        |                                |--GPIO--> GPSDO-tilaledi (RGB, väri+vilkku)
        |                                |--GPIO--> NTP-tilaledi (RGB, väri+vilkku)
        |                                |--I2C --> MCP4725 DAC --EFC--> OCXO 10MHz (5V)
        |                                |                                    |
        +--------------> BNC 1PPS OUT    |<--taajuusmittaus (PIO/PWM-laskuri)-+
        |                                |
        |                          USB-C (native, RP2350, 5V):
        |                          - virransyöttö koko laitteelle
        |                          - CDC-ACM: NMEA/PPS-data -> host apuohjelma -> chrony SHM/PPS
        |                          - myös parametrikonfigurointi (rinnakkain enkooderin kanssa)
        |                          (myöh. vaihtoehto: virtuaalinen DCD tai USB-Ethernet+oma NTP)
        |
        +--------- puskuri/jakovahvistin <-- OCXO ---> BNC REF OUT (10 MHz tms., 50 ohm)
```

## Karkea BOM-kategorialista (tarkennetaan Vaiheessa 2)
- LEA-M8S (varastossa)
- Aktiivinen GNSS-antenni (ulkokäyttöön, esim. 3–5V bias)
- MCU: **Raspberry Pi Pico 2 (RP2350A) -kehityskortti** (natiivi USB), pistokelistoilla tai juotettuna; ei omaa RP2350-piiriä (rakennussarjaperiaate)
- OCXO: 5V, analoginen EFC (esim. Trimble 65256 / IsoTemp 143-141 / CTI OC5SVC25 / Bliley NV47M1008 -tyyppinen, surplus tai vastaava uusi)
- DAC: MCP4725 (I2C, 12-bit) + RC-silmukkasuodatin, OCXO:n EFC-ohjaukseen
- 10 MHz (tms.) -puskuri/jakovahvistin, BNC-ulostulo, 50 Ω
- Näyttö: mono-OLED, I2C, **0.91" 128x32** (SSD1306-ajuri, ~36×12,5mm PCB)
- Enkooderi: EC11-luokkaa, sisäänrakennetulla painikkeella, etupaneeliin
- Tilaledit: 2 kpl monivärinen (RGB/bi-color) — GPSDO, NTP
- Liittimet (kaikki takapaneelissa): SMA (GNSS-antenni), BNC (1PPS OUT), BNC (REF OUT), USB-C (host + virta 5V)
- Suurehko elektrolyyttikondensaattori OCXO:n lämmitysvirtapiikin puskurointiin USB-syötössä
- Kotelo: **Fischer Elektronik AKG 105.26 / AKG1052680ME** (105 × 100,3 × 26 mm, luonnonanodisoitu alumiini, 100 mm eurokortille)

## Vaiheistus (PM-tyyliin)
1. **Vaatimukset ja arkkitehtuuri** — tämä dokumentti.
2. **Proof-of-concept penkillä**: Pico 2 -kehityskortti, paljas LEA-M8S pienellä carrier-piirillä (tai u-blox EVK-M8), MCP4725-breakout, valittu OCXO, 0.91" OLED-breakout, USB-CDC+ntp-shm-tyylinen PC-apuohjelma. Tavoite: validoida PIO-pohjainen PPS-kaappaus ja taajuuslaskenta, disciplining-algoritmi, USB-kellopalvelu ja virransyötön riittävyys ennen omaa piirilevyä.
3. **Kytkentäkaavio (KiCad)** — LEA-M8S HIM:n minimisuunnittelu + antennisupervisor aktiiviantennille, Pico 2 -kortti, DAC, OCXO, OLED+tilaledit+enkooderi, USB-C, liittimet. Piirilevyn ääriviiva AKG 105.26:n sisämittojen mukaan (100 mm eurokortti, komponenttikorkeus ≤22 mm).
4. **PCB-layout** — RF-osuudet (antenni, 10 MHz -ulostulo) 50 Ω kontrolloidulla impedanssilla, HIM:n EMI-suositukset I/O-linjoilla, OCXO pois lämpölähteiden läheltä (HIM 2.5), kaikki liittimet reunalle takapaneelin kohdalle.
5. **Kotelo** — Fischer AKG1052680ME: etupaneeliin OLED-aukko, 2 tilaledin reiät ja enkooderin ø7 mm reikä; takapaneeliin SMA, 2× BNC ja USB-C -aukot.
6. **Firmware** — UBX-parsinta, PIO-pohjainen PPS-kaappaus/taajuuslaskenta ja disciplining-silmukka, OLED-status-UI + enkooderivalikko, tilaledien ohjaus, USB-CDC-kellopalvelu ja -konfigurointi.
7. **Kalibrointi ja verifiointi** — 10 MHz verrataan referenssitaajuuslaskuriin/toiseen GPSDO:hon, NTP/PPS-tarkkuus tarkistetaan (chronyc tracking), pitkän ajan holdover-testi, OCXO:n lämmitysvirtapiikin mittaus USB-syötöstä.

## Avoimet kysymykset / riskit seuraavaan kierrokseen
- **OCXO:n fyysinen korkeus AKG 105.26:n 26 mm sisätilaan** — tärkein avoin riski. Moni 5V surplus-OCXO (Trimble 65256, IsoTemp 143-141 ym.) on fyysisesti liian korkea/iso matalaan koteloon; OCXO-valinta pitää tehdä sekä sähköisin että mekaanisin perustein.
- Tarkka OCXO-osavalinta ja hankintakanava (surplus eBay vs. uusi vastaava) — hinta/saatavuus/koko selvitettävä ennen tilausta.
- USB-virransyötön mitoitus: mitataan OCXO:n todellinen lämmitysvirtapiikki ja päätetään puskurointi + tarvittava USB-lähteen virrankesto (itsevoimainen hubi / USB-C PD).
- USB-kellopalvelun toteutustapa v1:ssä: CDC-ACM+host-apuohjelma (nopein) vs. virtuaalinen DCD-PPS vs. USB-Ethernet+oma NTP (valitaan Vaiheessa 6, ei blokkaa PCB-suunnittelua).
- **USB-C takapaneelissa**: ratkaistu valitsemalla USB-C-korttina Waveshare RP2350-Plus (ks. "USB-C-kortin valinta"). Avoimet tarkistukset: liittimen sijainti ja korkeus takapaneelin aukkoon nähden (liitin työntyy 1,3 mm PCB:n yli, korkeus 3,25 mm), kortin kokonaiskorkeus (alle 22 mm kun juotettuna emolevyyn), 5 V -polun suojaus (ei sulaketta kortilla), laturin lepovirta ilman akkua sekä 4 MB vs. 16 MB flash.
- GPIO-budjetti: ratkaistu ehdotuksella (ks. "GPIO-jako"): 19 GPIO:ta käytössä 26:sta, varapinnit erillisille LEDeille — vahvistetaan breadboard-testissä.
- PIO-pohjaisen 10 MHz -taajuuslaskennan ja 1PPS-aikaleimauksen toteutus RP2350:llä — validoidaan proof-of-conceptissa (Vaihe 2).
- NTP-palvelin verkkoon (WiFi/Ethernet) ei kuulu v1:een; jos tarvitaan myöhemmin, vaihtoehdot ovat Pico 2 W tai USB-Ethernet (CDC-NCM).
- **Tuotantonäytön valinta** (ks. "Tuotantonäyttö (avoin)") sekä OLED-moduulin (0.91" 128x32, ei kiinnitysreikiä prototyypissä) kiinnitystapa etupaneeliin (leikkaus 2 mm:n kansilevyyn — liimaus tai painokehys), enkooderin akselin pituus/holkin läpivienti ja tilaledien sijoittelu — tarkentuu PCB/mekaniikkasuunnittelussa.
- 100 mm eurokortin todellinen käytettävä leveys AKG 105.26 -profiilin sisällä (kiskourat vievät osan 105 mm:stä) — mitattava/varmistettava ennen PCB-ääriviivan lyömistä lukkoon.
- Takapaneelin liitinasettelu (SMA + 2×BNC + USB-C 105 mm:n leveydellä) — mahtuu laskennallisesti hyvin, mutta tarkka sijoittelu tarkentuu mekaniikkasuunnittelussa.
- GPSDO- ja NTP-tilaledien tarkka väri-/vilkkulogiikka määritellään firmwaren suunnittelussa.
