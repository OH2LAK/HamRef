# HamREF firmware (proof of concept)

RP2350 (Pico 2 / Waveshare RP2350-Plus) firmware for the GNSS-disciplined 10 MHz reference.

| File | Purpose |
|---|---|
| `src/hamref_gate.pio` | PIO program: free-running count of 10 MHz cycles, latched on every PPS edge (100 ns quantisation, no cycles lost) |
| `src/disciplining.[ch]` | Hardware-independent loop: WARMUP -> FREQ_LOCK (FLL) -> PHASE_LOCK (PI PLL) -> HOLDOVER, glitch rejection, anti-windup |
| `src/dac.[ch]` | MCP4725 EFC DAC on I2C1 (16-bit API, upper 12 bits used) |
| `src/gnss.[ch]` | Minimal NMEA parser (RMC validity, GGA satellites) |
| `src/pins.h` | GPIO map, matches proto-v0.1 |
| `sim/sim_main.c` | Host simulation of the loop (OCXO drift, EFC gain error, PPS jitter, outage) |

## Build

```
export PICO_SDK_PATH=/path/to/pico-sdk      # SDK 2.x with submodules (tinyusb)
mkdir build && cd build
cmake ..            # PICO_BOARD defaults to pico2
make -j4            # produces hamref.uf2; hold BOOTSEL, plug in, copy the file
```

Needs `gcc-arm-none-eabi`, `libnewlib-arm-none-eabi`, `libstdc++-arm-none-eabi-newlib`.

## Host simulation

```
cc -O2 -o /tmp/hamref_sim sim/sim_main.c src/disciplining.c -Isrc -lm
/tmp/hamref_sim 1       # argument = random seed
```

Typical result (8 h, 4 seeds): locks in ~25 min, PLL phase rms 80-100 ns (limited by the 100 ns counter resolution), frequency error below ~0.7 ppb over a 1 h GNSS outage. These are model numbers, not measurements.

## Status output (USB CDC, 1 line per second)

`$HAMREF,state,locked,phase_ns,freq_ppb,dac_code,sats,glitches`

## Not done yet / must be calibrated on hardware

- `efc_ppb_per_lsb` and `dac_mid` in `disc_default_cfg()` are placeholders. Step the DAC and measure the real OCXO sensitivity.
- Verify the PIO program on a real board (10 MHz level, PPS polarity); PPS is assumed active-high rising edge.
- OLED, encoder, LEDs, Si5351C, UBX configuration of the LEA-M8S (TIMEPULSE = 1 Hz, NMEA only), host helper for chrony SHM.
- Finer phase resolution (time-interval counter or ADC-based) would remove the 100 ns quantisation.
