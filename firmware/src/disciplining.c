/*
 * HamREF - GPSDO disciplining loop. See disciplining.h.
 * Author: Erik, OH2LAK
 */
#include "disciplining.h"

#include <math.h>
#include <string.h>

void disc_default_cfg(disc_cfg_t *c)
{
    c->nominal_hz        = 10000000u;
    c->dac_mid           = 32768u;
    /* Placeholder: ~+-3 ppm over the 16-bit range. MUST be calibrated for the
     * real OCXO (CTI OSC5A2B02): step the DAC and measure the frequency. */
    c->efc_ppb_per_lsb   = 0.1;
    c->warmup_s          = 300;
    c->freq_window_s     = 16;
    c->freq_lock_ppb     = 30.0;
    c->freq_lock_windows = 3;
    c->pll_tau_s         = 400.0;
    c->pll_zeta          = 1.0;
    c->glitch_counts     = 100;      /* 10 ppm */
    c->holdover_after_s  = 5;
    c->reacquire_s       = 10;
    c->locked_phase_ns   = 300.0;
    c->locked_seconds    = 60;
}

const char *disc_state_name(disc_state_t s)
{
    switch (s) {
    case DISC_WARMUP:     return "WARMUP";
    case DISC_FREQ_LOCK:  return "FREQ_LOCK";
    case DISC_PHASE_LOCK: return "PHASE_LOCK";
    case DISC_HOLDOVER:   return "HOLDOVER";
    }
    return "?";
}

static void apply_dac(disc_t *d)
{
    double lsb_per_ppb = 1.0 / d->cfg.efc_ppb_per_lsb;
    double code = (double)d->cfg.dac_mid + (d->ppb_int + d->p_term) * lsb_per_ppb;

    d->dac_saturated = false;
    if (code > 65535.0) {                      /* anti-windup: pull integrator back */
        d->ppb_int -= (code - 65535.0) * d->cfg.efc_ppb_per_lsb;
        code = 65535.0;
        d->dac_saturated = true;
    } else if (code < 0.0) {
        d->ppb_int -= code * d->cfg.efc_ppb_per_lsb;
        code = 0.0;
        d->dac_saturated = true;
    }
    d->dac_code = (uint16_t)(code + 0.5);
    d->ppb_cmd = (d->ppb_int + d->p_term);
}

void disc_init(disc_t *d, const disc_cfg_t *cfg)
{
    memset(d, 0, sizeof(*d));
    d->cfg = *cfg;
    d->state = DISC_WARMUP;
    d->warm_left = cfg->warmup_s;
    apply_dac(d);
}

static void enter_freq_lock(disc_t *d)
{
    d->state = DISC_FREQ_LOCK;
    d->win_s = 0;
    d->win_err = 0;
    d->good_windows = 0;
    d->locked = false;
    d->locked_run = 0;
}

static void enter_phase_lock(disc_t *d)
{
    d->state = DISC_PHASE_LOCK;
    d->phase_ns = 0.0;
    d->hist_n = 0;
    d->locked_run = 0;
    d->p_term = 0.0;
}

void disc_no_pps(disc_t *d)
{
    d->seconds++;
    d->glitches++;
    d->good_run = 0;
    d->bad_run++;
    d->locked = false;
    if (d->state == DISC_WARMUP) {
        if (d->warm_left) d->warm_left--;
        if (d->warm_left == 0) d->state = DISC_WARMUP;   /* stay until we see PPS */
        return;
    }
    if (d->bad_run >= d->cfg.holdover_after_s)
        d->state = DISC_HOLDOVER;
}

void disc_update(disc_t *d, uint32_t count, bool gnss_valid)
{
    const uint32_t nom = d->cfg.nominal_hz;
    d->seconds++;

    /* A missed PPS shows up as k * nominal counts. Accept k = 1..3. */
    uint32_t k = (uint32_t)(((uint64_t)count + nom / 2) / nom);
    int64_t err = (int64_t)count - (int64_t)k * (int64_t)nom;
    int64_t aerr = err < 0 ? -err : err;

    if (!gnss_valid || k == 0 || k > 3 || aerr > (int64_t)d->cfg.glitch_counts) {
        d->glitches++;
        d->good_run = 0;
        d->bad_run++;
        d->locked = false;
        d->locked_run = 0;
        if (d->state != DISC_WARMUP && d->bad_run >= d->cfg.holdover_after_s)
            d->state = DISC_HOLDOVER;
        if (d->state == DISC_WARMUP && d->warm_left) d->warm_left--;
        return;
    }
    d->bad_run = 0;
    d->good_run++;

    switch (d->state) {
    case DISC_WARMUP:
        if (d->warm_left > k) d->warm_left -= k; else d->warm_left = 0;
        if (d->warm_left == 0) enter_freq_lock(d);
        break;

    case DISC_HOLDOVER:
        if (d->good_run >= d->cfg.reacquire_s) enter_freq_lock(d);
        break;

    case DISC_FREQ_LOCK: {
        d->win_s += k;
        d->win_err += err;
        if (d->win_s >= d->cfg.freq_window_s) {
            double eps_ppb = (double)d->win_err / ((double)d->win_s * (double)nom) * 1e9;
            d->freq_avg_ppb = eps_ppb;
            if (fabs(eps_ppb) < d->cfg.freq_lock_ppb) {
                if (++d->good_windows >= d->cfg.freq_lock_windows) {
                    enter_phase_lock(d);
                    break;
                }
            } else {
                d->good_windows = 0;
            }
            d->ppb_int -= 0.9 * eps_ppb;          /* coarse correction, slightly under-damped gain */
            apply_dac(d);
            d->win_s = 0;
            d->win_err = 0;
        }
        break;
    }

    case DISC_PHASE_LOCK: {
        const double ns_per_cycle = 1e9 / (double)nom;
        d->phase_ns += (double)err * ns_per_cycle;

        const double wn = 1.0 / d->cfg.pll_tau_s;
        const double kp = 2.0 * d->cfg.pll_zeta * wn;     /* ppb per ns */
        const double ki = wn * wn;                        /* ppb per (ns*s) */

        d->ppb_int -= ki * d->phase_ns * (double)k;
        d->p_term   = -kp * d->phase_ns;
        apply_dac(d);

        /* 100 s frequency estimate and lock flag */
        d->phase_hist[d->hist_n % DISC_HIST_LEN] = d->phase_ns;
        d->hist_n++;
        if (d->hist_n > DISC_HIST_LEN) {
            double old = d->phase_hist[d->hist_n % DISC_HIST_LEN];
            d->freq_avg_ppb = (d->phase_ns - old) / (double)DISC_HIST_LEN;
        }
        if (fabs(d->phase_ns) < d->cfg.locked_phase_ns) {
            if (++d->locked_run >= d->cfg.locked_seconds) d->locked = true;
        } else {
            d->locked_run = 0;
            d->locked = false;
        }
        break;
    }
    }
}
