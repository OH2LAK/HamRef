# HamREF

A small GNSS-disciplined 10 MHz frequency reference and precision time server for the amateur radio shack — built around the u-blox LEA-M8S GNSS module.

> **Status: early architecture / pre-prototype.** No firmware or PCB yet. This README documents the design as currently planned so the repo has a real starting point; sections below are marked `TODO` where work hasn't started.

## What this is

HamREF provides two things a well-equipped station needs and usually has to buy separately:

- A continuous **10 MHz reference output** (SMA, 50 Ω) to lock transceivers, synthesizers, and test equipment.
- A **precision time source for the shack computer**, disciplined by GNSS, accurate enough for FT8 and other digital modes.

Status and basic parameters (GNSS lock, satellite count, PPS accuracy, OCXO discipline state) are shown on a small color TFT.

## Why not just use the GNSS module's own 10 MHz output?

The LEA-M8S can output a configurable timepulse from 0.25 Hz to 10 MHz directly, but that signal is a digitally synthesized pulse train (derived from the module's internal TCXO + fractional-N synthesizer), not a clean analog oscillator. At 10 MHz its jitter (the module's spec is 30 ns RMS / 60 ns 99% at 1 Hz) is significant relative to the 100 ns period, it can show small phase steps at each second boundary, and it provides no holdover if GNSS lock is lost.

HamREF instead uses the classic GPSDO approach: the LEA-M8S's single TIMEPULSE output is configured as **1PPS**, and that one pulse-per-second reference is used by the MCU to discipline a separate free-running OCXO via a DAC-driven EFC loop with a long time constant. The 10 MHz output comes from the OCXO itself — far lower phase noise, plus holdover if satellite lock drops. The same 1PPS/NMEA data feeds the time service to the host computer.

Full rationale and the architecture decision log: [`docs/architecture-and-plan.md`](docs/architecture-and-plan.md) `TODO: copy in from the project doc`.

## Architecture overview

```
Active GNSS antenna
        |
    LEA-M8S  --UART (UBX/NMEA)--> ESP32-S3
        |TIMEPULSE (1PPS)                |
        v                                |--SPI--> color TFT (status/menu)
   (fan out / buffer)                    |--I2C --> DAC --EFC--> OCXO (10 MHz, 5V)
        |                                |                             |
        +--------------------------------+                             |
                                          |<--freq. measurement---------+
                                          |
                                    USB (native, ESP32-S3):
                                    - powers the whole device
                                    - CDC-ACM: PPS/NMEA data -> host helper -> chrony SHM/PPS
                                          |
                              10 MHz out <-- buffer/distribution amp <-- OCXO
                              (SMA, 50 ohm)
```

Key hardware decisions so far:

| Item | Decision | Notes |
|---|---|---|
| GNSS module | u-blox LEA-M8S | Fixed — parts already on hand. |
| Antenna | Active, external | Antenna supervisor + R_BIAS per u-blox HIM. |
| MCU | ESP32-S3 | Native USB, WiFi, enough peripherals for PPS capture + DAC + display. |
| Oscillator | 5 V OCXO, analog EFC | e.g. Trimble 65256 / IsoTemp 143-141 / CTI OC5SVC25 / Bliley NV47M1008 class part. |
| Display | Color TFT, SPI, 240x240 | ST7789-class. |
| Power + host link | USB | Powers the device; CDC-ACM carries PPS/NMEA to a host-side helper feeding chrony (SHM/PPS refclock). |

See the architecture doc for the full reasoning, open questions, and the phased project plan.

## Status / roadmap

- [x] Requirements and architecture defined
- [ ] Breadboard proof of concept (PPS capture, disciplining loop, USB time delivery)
- [ ] KiCad schematic
- [ ] PCB layout
- [ ] Enclosure
- [ ] Firmware
- [ ] Calibration and verification against a reference

## Repository structure

`TODO` — not yet populated. Planned layout:

```
/hardware       KiCad project (schematic, PCB, BOM)
/firmware       ESP32-S3 firmware
/enclosure      3D-printable enclosure design files
/docs           Architecture notes, test results, photos
```

## Building it yourself

`TODO` — no build instructions yet; this section will cover bill of materials, toolchain, flashing, and bring-up once the proof-of-concept stage is complete.

## Hardware reference documents

Design decisions are based on:
- u-blox LEA-M8S Data Sheet (UBX-16010205)
- u-blox LEA-M8S/M8T Hardware Integration Manual (UBX-15030060)

## License

`TODO` — pick a license (e.g. MIT/CERN-OHL-S for hardware, MIT/GPL for firmware) before the first public commit.

## Author

Erik, OH2LAK / OH2CH
