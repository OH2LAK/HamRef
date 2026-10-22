/*
 * HamREF firmware PoC: PIO PPS/10 MHz gate counter + GNSS disciplining loop.
 * Prints one status line per second on USB CDC:
 *   $HAMREF,state,locked,phase_ns,freq_ppb,dac,sats,glitches
 * Author: Erik, OH2LAK
 */
#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/pio.h"
#include "hamref_gate.pio.h"
#include "pins.h"
#include "dac.h"
#include "gnss.h"
#include "disciplining.h"

int main(void)
{
    stdio_init_all();
    dac_init();
    gnss_init();

    PIO pio = pio0;
    uint sm = pio_claim_unused_sm(pio, true);
    uint off = pio_add_program(pio, &hamref_gate_program);
    hamref_gate_init(pio, sm, off, PIN_PPS_IN);

    gpio_init(PIN_OCXO_EN);
    gpio_set_dir(PIN_OCXO_EN, GPIO_OUT);
    gpio_put(PIN_OCXO_EN, 1);

    disc_cfg_t cfg;
    disc_default_cfg(&cfg);
    disc_t d;
    disc_init(&d, &cfg);
    dac_write16(d.dac_code);

    bool have_prev = false;
    uint32_t prev = 0;
    absolute_time_t last_pps = get_absolute_time();

    for (;;) {
        gnss_poll();
        if (!pio_sm_is_rx_fifo_empty(pio, sm)) {
            uint32_t x = pio_sm_get(pio, sm);
            /* X counts down: cycles = prev - x (mod 2^32) */
            if (have_prev) {
                uint32_t cycles = prev - x;
                disc_update(&d, cycles, gnss_time_valid());
                dac_write16(d.dac_code);
                printf("$HAMREF,%s,%d,%.0f,%.2f,%u,%d,%u\n",
                       disc_state_name(d.state), d.locked, d.phase_ns,
                       d.freq_avg_ppb, d.dac_code, gnss_sats(), d.glitches);
            }
            prev = x;
            have_prev = true;
            last_pps = get_absolute_time();
        } else if (absolute_time_diff_us(last_pps, get_absolute_time()) > 1500000) {
            disc_no_pps(&d);
            last_pps = get_absolute_time();
        }
    }
}
