# HamREF

A small GNSS-disciplined 10 MHz frequency reference and precision time server for the amateur radio shack — built around the u-blox LEA-M8S GNSS module.

> **Status: early architecture / pre-prototype.** No firmware or PCB yet. This README documents the design as currently planned so the repo has a real starting point; sections below are marked `TODO` where work hasn't started.

<p align="center">
  <img width="600" alt="HamREF mockup" src="https://github.com/user-attachments/assets/82779c23-fe5e-4b1a-90e0-4775c3bd64c9" />
</p>

## What this is

HamREF provides two things a well-equipped station needs and usually has to buy separately:

- A **10 MHz reference output** (or any other, programmable) (SMA, 50 Ω) to lock transceivers, synthesizers, and test equipment.
- A **precision time source for the shack computer**, disciplined by GNSS, accurate enough for FT8 and other digital modes.

Status (GNSS lock, satellite count, PPS accuracy, OCXO discipline state) is shown on a small monochrome OLED plus two multicolor status LEDs (GPSDO / NTP) on the front panel — color and blink/steady pattern indicate different states. A front-panel rotary encoder drives the menu; full parameter configuration is also available over USB (see [Enclosure](#enclosure) below).

## Why not just use the GNSS module's own 10 MHz output?

The LEA-M8S can output a configurable timepulse from 0.25 Hz to 10 MHz directly, but that signal is a digitally synthesized pulse train (derived from the module's internal TCXO + fractional-N synthesizer), not a clean analog oscillator. At 10 MHz its jitter (the module's spec is 30 ns RMS / 60 ns 99% at 1 Hz) is significant relative to the 100 ns period, it can show small phase steps at each second boundary, and it provides no holdover if GNSS lock is lost.

HamREF instead uses the classic GPSDO approach: the LEA-M8S's single TIMEPULSE output is configured as **1PPS**, and that one pulse-per-second reference is used by the MCU to discipline a separate free-running OCXO via a DAC-driven EFC loop with a long time constant. The 10 MHz output comes from the OCXO itself — far lower phase noise, plus holdover if satellite lock drops. The same 1PPS/NMEA data feeds the time service to the host computer.

Full rationale and the architecture decision log: [`docs/architecture-and-plan.md`](docs/architecture-and-plan.md) `TODO: copy in from the project doc`.

## Enclosure

**Fischer Elektronik AKG 105.26** (part AKG1052680ME) — an extruded aluminum mini case for 100 mm eurocards, 105 × 100.3 × 26 mm, natural anodized, with integrated cooling-fin channels. Front and rear panels are separate 2 mm cover plates.

The 26 mm case height (≈22 mm usable panel height) ruled out the originally planned 240x240 color TFT. An EC11-class rotary encoder does fit, though (body ≈11.7×12–13×4.5–8.5 mm, ø7 mm panel bushing — verified against the Farnell EC11 datasheet), so the front panel keeps a physical control after all:

| Panel | Contents |
|---|---|
| Front | 0.91" 128x32 OLED (status), 2 multicolor LEDs (GPSDO, NTP), rotary encoder (menu/control) |
| Rear | SMA (GNSS antenna), BNC (1PPS OUT), BNC (REF OUT), USB-C (host + 5V power) |

The 22 mm limit also constrains component height on the PCB (OCXO included) — still an open item, see the architecture doc.

## Architecture overview

```
Active GNSS antenna
        |
    LEA-M8S  --UART (UBX/NMEA)--> ESP32-S3 <-- encoder (menu/control)
        |TIMEPULSE (1PPS)                |
        v                                |--I2C --> 0.91" 128x32 OLED
   (fan out / buffer)                    |--GPIO --> RGB LED "GPSDO"
        |                                |--GPIO --> RGB LED "NTP"
        |                                |--I2C --> DAC --EFC--> OCXO (10 MHz, 5V)
        |                                                              |
        +--------------------------------+                             |
                                          |<--freq. measurement---------+
                                          |
                                    USB-C (native, ESP32-S3):
                                    - powers the whole device (5V, host link)
                                    - CDC-ACM: PPS/NMEA data -> host helper -> chrony SHM/PPS
                                    - also carries parameter configuration
                                          |
                              1PPS OUT <-- buffer <-- LEA-M8S TIMEPULSE
                              (BNC, rear panel)

                              REF OUT <-- buffer/distribution amp <-- OCXO
                              (BNC, 50 ohm, rear panel)
```

Key hardware decisions so far:

| Item | Decision | Notes |
|---|---|---|
| GNSS module | u-blox LEA-M8S | Fixed — parts already on hand. |
| Antenna | Active, external | Antenna supervisor + R_BIAS per u-blox HIM. |
| MCU | ESP32-S3 | Native USB, WiFi, enough peripherals for PPS capture + DAC + display. |
| Oscillator | 5 V OCXO, analog EFC | e.g. Trimble 65256 / IsoTemp 143-141 / CTI OC5SVC25 / Bliley NV47M1008 class part — physical height inside the 22 mm case is still open, see architecture doc. |
| Enclosure | Fischer Elektronik AKG 105.26 (AKG1052680ME) | 105 × 100.3 × 26 mm extruded aluminum, 100 mm eurocard. |
| Display | 0.91" 128x32 mono OLED, I2C | SSD1306-class, ~36×12.5 mm PCB — fits the 22 mm panel height with margin; 0.96" 128x64 modules do not. |
| Front panel | OLED + 2 multicolor LEDs (GPSDO, NTP) + rotary encoder | EC11-class encoder confirmed to fit the 22 mm panel height. LED color/blink pattern encodes state (firmware TBD). |
| Rear panel | SMA (GNSS antenna), BNC (1PPS OUT), BNC (REF OUT), USB-C (host + 5V power) | All connectors on the back; layout across the 105 mm width still to be confirmed at PCB stage. |
| Power + host link | USB-C | Powers the device (5V); CDC-ACM carries PPS/NMEA to a host-side helper feeding chrony (SHM/PPS refclock), and doubles as the configuration interface alongside the encoder/OLED menu. |

See the architecture doc for the full reasoning, open questions, and the phased project plan.

## Status / roadmap

- [x] Requirements and architecture defined
- [x] Enclosure selected (Fischer AKG 105.26) and display/panel layout locked to it
- [ ] Breadboard proof of concept (PPS capture, disciplining loop, USB time delivery)
- [ ] KiCad schematic
- [ ] PCB layout
- [ ] Enclosure machining (panel cutouts)
- [ ] Firmware
- [ ] Calibration and verification against a reference

## Repository structure

`TODO` — not yet populated. Planned layout:

```
/hardware       KiCad project (schematic, PCB, BOM)
/firmware       ESP32-S3 firmware
/enclosure      Panel cutout drawings for the Fischer AKG 105.26
/docs           Architecture notes, test results, photos
```

## Building it yourself

`TODO` — no build instructions yet; this section will cover bill of materials, toolchain, flashing, and bring-up once the proof-of-concept stage is complete.

## Hardware reference documents

Design decisions are based on:
- u-blox LEA-M8S Data Sheet (UBX-16010205)
- u-blox LEA-M8S/M8T Hardware Integration Manual (UBX-15030060)
- Fischer Elektronik AKG1052680ME data sheet (enclosure)

## License

`TODO` — pick a license (e.g. MIT/CERN-OHL-S for hardware, MIT/GPL for firmware) before the first public commit.

## Authors

Erik, OH2LAK
Others will be too, when I find them and convince them this is a good project :)
