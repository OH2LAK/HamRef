# HamREF – arkkitehtuuri ja projektisuunnitelma (v0.4)

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
- MCU: **~~ESP32-S3~~ → RP2350 (Raspberry Pi Pico 2)** — lukittu 2026-10-14, ks. "MCU-valinta" alla. Perusteet: PIO-lohkot antavat deterministisen 10 MHz -laskennan ja 1PPS-aikaleimauksen ilman WiFi-häiriötä, natiivi USB (TinyUSB), UF2-päivitys. WiFi ei ole v1:ssä tarpeen, koska USB hoitaa kellopalvelun.
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

## OCXO/TCXO-suositus

Ehdotus: **5 V:n analogisella EFC-tulolla varustettu OCXO**, koska se sopii suoraan USB-virransyöttöön (ei tarvita 12V-hakkuria) ja koska tämä on juuri se komponenttiluokka jota ham-yhteisön GPSDO-rakentajat ovat käyttäneet vuosia — hyvin dokumentoitu, halpa ja helposti saatavilla surplus-markkinoilta (eBay), esim. paulvdiyblogs-GPSDO-projektin testaamat ja monen muun DIY-GPSDO:n käyttämät:
- **Trimble 65256** (5V, sini-ulostulo)
- **IsoTemp 143-141** (5V, neliöaalto-ulostulo)
- **CTI OC5SVC25** (5V, neliöaalto)
- **Bliley NV47M1008** (5V, neliöaalto)

Nämä ovat kaikki 5V analogisella EFC-piikillä varustettuja, eli MCU→I2C-DAC (esim. MCP4725)→RC-suodatin→EFC toimii suoraan, ilman erillistä jännitesäädintä OCXO:lle.

Vaihtoehto (jos halutaan välttää analoginen DAC+silmukkasuodatin kokonaan): **SiTime-sarjan digitaalisesti viritettävät MEMS-OCXO:t** (esim. SiT5711-tyyppinen, 3.3V, I2C-ohjaus) tarjoavat erittäin hyvän ±5–8 ppb -stabiiliuden ja pienen koon (9×7mm) ilman analogista EFC-silmukkaa — MCU kirjoittaa taajuuskorjauksen suoraan I2C:n yli. Huom: SiT5711 on merkitty "Not recommended for new designs" (SiTime ohjaa SiT5801:een), ja SiTime-osat yleensä hankitaan jakelijan kautta (Mouser/Digikey/SiTimeDirect) eivätkä ole yhtä helposti/halvasti saatavilla pienissä erissä kuin surplus-OCXO:t eBaysta. Prototyyppivaiheeseen suosittelen aloittamaan halvemmalla ja paremmin dokumentoidulla analogisella 5V OCXO:lla; SiTime-reitti kannattaa harkita vasta jos päädytään pieneen sarjaan asti.

**Huomio virransyötöstä (liittyy USB-kysymykseen alla):** pienetkin OCXO:t vetävät lämmitysvaiheessa (ensimmäiset ~3–5 min kylmästä käynnistyksestä) merkittävästi enemmän virtaa (tyypillisesti 300–700 mA) kuin stabiloituneena (~100–200 mA). Tämä pitää ottaa huomioon USB-virtabudjetissa ja mahdollisesti puskuroida isolla elektrolyyttikondensaattorilla, ettei isäntäkoneen USB-portin virtarajoitus laukea käynnistyksessä.

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
- **Mekaniikka**: Pico 2 -moduuli n. 51 × 21 mm, mahtuu 22 mm:n sisäkorkeuteen. Voidaan juottaa suoraan eurokortille (reunapadit) tai myöhemmin korvata RP2350-piirillä + flash + kide omassa KiCad-layoutissa.

**Mitä menetetään ESP32-S3:een verrattuna:**
- Ei WiFiä (Pico 2 W:ssä olisi, jos tarvitaan myöhemmin). Ei WiFi-NTP:tä eikä web-UI:ta v1:ssä — korvataan USB-yhteydellä ja enkooderi+OLED-valikolla.
- Ei OTA-päivityksiä — UF2 USB:n yli riittää laitteelle, joka on tietokoneen vieressä.

**Yhteiset ratkaisut (ei muutu):** DAC on edelleen ulkoinen I2C-DAC (MCP4725 tms.) EFC-ohjaukseen; OLED I2C:llä; u-blox UART:lla; 10 MHz kannattaa puskuroida/jakaa ennen MCU:ta signaalitasojen ja laskentataajuuden hallitsemiseksi. Vaihtoehtona myöhemmin STM32 (hyvä timer-capture), ei tarpeen v1:ssä.

**Avoin:** PIO-pohjaisen taajuuslaskennan ja 1PPS-aikaleimauksen toteutus (laskurin laajennus 32 bittiin, PPS-latchi) validoidaan proof-of-conceptissa.

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
- MCU: **Raspberry Pi Pico 2 (RP2350)** -moduuli (natiivi USB); myöhemmin mahdollisesti RP2350-piiri suoraan omalle kortille
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
3. **Kytkentäkaavio (KiCad)** — LEA-M8S HIM:n minimisuunnittelu + antennisupervisor aktiiviantennille, Pico 2 -moduuli (tai RP2350), DAC, OCXO, OLED+tilaledit+enkooderi, USB-C, liittimet. Piirilevyn ääriviiva AKG 105.26:n sisämittojen mukaan (100 mm eurokortti, komponenttikorkeus ≤22 mm).
4. **PCB-layout** — RF-osuudet (antenni, 10 MHz -ulostulo) 50 Ω kontrolloidulla impedanssilla, HIM:n EMI-suositukset I/O-linjoilla, OCXO pois lämpölähteiden läheltä (HIM 2.5), kaikki liittimet reunalle takapaneelin kohdalle.
5. **Kotelo** — Fischer AKG1052680ME: etupaneeliin OLED-aukko, 2 tilaledin reiät ja enkooderin ø7 mm reikä; takapaneeliin SMA, 2× BNC ja USB-C -aukot.
6. **Firmware** — UBX-parsinta, PIO-pohjainen PPS-kaappaus/taajuuslaskenta ja disciplining-silmukka, OLED-status-UI + enkooderivalikko, tilaledien ohjaus, USB-CDC-kellopalvelu ja -konfigurointi.
7. **Kalibrointi ja verifiointi** — 10 MHz verrataan referenssitaajuuslaskuriin/toiseen GPSDO:hon, NTP/PPS-tarkkuus tarkistetaan (chronyc tracking), pitkän ajan holdover-testi, OCXO:n lämmitysvirtapiikin mittaus USB-syötöstä.

## Avoimet kysymykset / riskit seuraavaan kierrokseen
- **OCXO:n fyysinen korkeus AKG 105.26:n 26 mm sisätilaan** — tärkein avoin riski. Moni 5V surplus-OCXO (Trimble 65256, IsoTemp 143-141 ym.) on fyysisesti liian korkea/iso matalaan koteloon; OCXO-valinta pitää tehdä sekä sähköisin että mekaanisin perustein.
- Tarkka OCXO-osavalinta ja hankintakanava (surplus eBay vs. uusi vastaava) — hinta/saatavuus/koko selvitettävä ennen tilausta.
- USB-virransyötön mitoitus: mitataan OCXO:n todellinen lämmitysvirtapiikki ja päätetään puskurointi + tarvittava USB-lähteen virrankesto (itsevoimainen hubi / USB-C PD).
- USB-kellopalvelun toteutustapa v1:ssä: CDC-ACM+host-apuohjelma (nopein) vs. virtuaalinen DCD-PPS vs. USB-Ethernet+oma NTP (valitaan Vaiheessa 6, ei blokkaa PCB-suunnittelua).
- PIO-pohjaisen 10 MHz -taajuuslaskennan ja 1PPS-aikaleimauksen toteutus RP2350:llä — validoidaan proof-of-conceptissa (Vaihe 2).
- NTP-palvelin verkkoon (WiFi/Ethernet) ei kuulu v1:een; jos tarvitaan myöhemmin, vaihtoehdot ovat Pico 2 W tai USB-Ethernet (CDC-NCM).
- OLED-moduulin (0.91" 128x32) tarkka kiinnitystapa etupaneeliin (leikkaus 2 mm:n kansilevyyn — liimaus, pienet ruuvit vai painokehys), enkooderin akselin pituus/holkin läpivienti ja tilaledien sijoittelu — tarkentuu PCB/mekaniikkasuunnittelussa.
- 100 mm eurokortin todellinen käytettävä leveys AKG 105.26 -profiilin sisällä (kiskourat vievät osan 105 mm:stä) — mitattava/varmistettava ennen PCB-ääriviivan lyömistä lukkoon.
- Takapaneelin liitinasettelu (SMA + 2×BNC + USB-C 105 mm:n leveydellä) — mahtuu laskennallisesti hyvin, mutta tarkka sijoittelu tarkentuu mekaniikkasuunnittelussa.
- GPSDO- ja NTP-tilaledien tarkka väri-/vilkkulogiikka määritellään firmwaren suunnittelussa.
