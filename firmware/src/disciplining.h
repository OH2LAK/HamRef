/*
 * HamREF - GPSDO disciplining loop (hardware independent, pure C).
 *
 * The loop is fed once per GNSS 1PPS with the number of OCXO cycles counted
 * between two consecutive PPS edges (nominally 10 000 000). It steers the
 * OCXO EFC voltage (via a 16-bit DAC code) in three stages:
 *
 *   WARMUP      OCXO oven heating, EFC parked at mid-scale, no steering.
 *   FREQ_LOCK   Frequency-locked loop: average the frequency error over a
 *               window and correct it in one step (coarse tuning).
 *   PHASE_LOCK  Second-order PI phase-locked loop on the accumulated phase
 *               error (OCXO vs GNSS time), time constant pll_tau_s.
 *   HOLDOVER    GNSS invalid / PPS missing: EFC is frozen at the last value.
 *
 * Units: phase in ns, frequency in ppb (= ns/s), DAC code 0..65535.
 *
 * Author: Erik, OH2LAK
 */
#ifndef HAMREF_DISCIPLINING_H
#define HAMREF_DISCIPLINING_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    DISC_WARMUP = 0,
    DISC_FREQ_LOCK,
    DISC_PHASE_LOCK,
    DISC_HOLDOVER
} disc_state_t;

typedef struct {
    uint32_t nominal_hz;        /* OCXO nominal frequency, 10 000 000 */
    uint16_t dac_mid;           /* EFC code at which the OCXO is (roughly) on frequency */
    double   efc_ppb_per_lsb;   /* DAC sensitivity, >0: higher code = higher frequency */
    uint32_t warmup_s;          /* seconds to wait for the oven before steering */
    uint32_t freq_window_s;     /* FLL averaging window */
    double   freq_lock_ppb;     /* FLL exit threshold (|avg freq error|) */
    uint32_t freq_lock_windows; /* consecutive good windows needed to leave FLL */
    double   pll_tau_s;         /* PLL time constant (wn = 1/tau) */
    double   pll_zeta;          /* PLL damping, 0.7 .. 1.0 */
    uint32_t glitch_counts;     /* reject a measurement if |count - k*nominal| exceeds this */
    uint32_t holdover_after_s;  /* bad seconds in a row before HOLDOVER */
    uint32_t reacquire_s;       /* good seconds in a row to leave HOLDOVER */
    double   locked_phase_ns;   /* |phase| below this ... */
    uint32_t locked_seconds;    /* ... for this long sets the 'locked' flag */
} disc_cfg_t;

#define DISC_HIST_LEN 100

typedef struct {
    disc_cfg_t cfg;
    disc_state_t state;

    /* outputs / status */
    uint16_t dac_code;
    bool     dac_saturated;
    bool     locked;
    double   phase_ns;          /* accumulated phase error, OCXO - GNSS */
    double   freq_avg_ppb;      /* OCXO frequency error averaged over ~100 s */
    double   ppb_cmd;           /* current total EFC command in ppb */
    uint32_t seconds;           /* seconds processed */
    uint32_t glitches;          /* rejected measurements */

    /* internals */
    double   ppb_int;           /* integrator / static frequency trim */
    double   p_term;
    uint32_t warm_left;
    uint32_t win_s;
    int64_t  win_err;
    uint32_t good_windows;
    uint32_t bad_run;
    uint32_t good_run;
    uint32_t locked_run;
    double   phase_hist[DISC_HIST_LEN];
    uint32_t hist_n;
} disc_t;

void disc_default_cfg(disc_cfg_t *cfg);
void disc_init(disc_t *d, const disc_cfg_t *cfg);

/* One measurement per PPS: count = OCXO cycles since the previous PPS edge.
 * gnss_valid: receiver reports a valid fix / timing solution. */
void disc_update(disc_t *d, uint32_t count, bool gnss_valid);

/* Call once per second when no PPS edge arrived (counts as a bad second). */
void disc_no_pps(disc_t *d);

const char *disc_state_name(disc_state_t s);

#ifdef __cplusplus
}
#endif
#endif /* HAMREF_DISCIPLINING_H */
