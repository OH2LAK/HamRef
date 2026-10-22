/*
 * Host simulation of the HamREF disciplining loop.
 * Models: OCXO with initial offset, EFC gain error (true gain != configured),
 * aging, thermal random walk; GNSS PPS jitter; 100 ns count quantisation;
 * missed PPS, count glitches and a 1 h GNSS outage (holdover).
 * Build: cc -O2 -o sim sim/sim_main.c src/disciplining.c -Isrc -lm
 * Author: Erik, OH2LAK
 */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "disciplining.h"

static double urand(void) { return (rand() + 1.0) / (RAND_MAX + 2.0); }
static double gauss(void) { return sqrt(-2.0 * log(urand())) * cos(2 * M_PI * urand()); }

int main(int argc, char **argv)
{
    unsigned seed = argc > 1 ? (unsigned)atoi(argv[1]) : 1;
    srand(seed);
    const int T = 8 * 3600;
    const int OUT_A = 3 * 3600, OUT_B = 4 * 3600;

    disc_cfg_t cfg; disc_default_cfg(&cfg);
    cfg.warmup_s = 120;
    disc_t d; disc_init(&d, &cfg);

    const double g_true = 0.13;          /* ppb/LSB, 30 % above configured */
    double off0 = 650.0;                 /* ppb at mid-scale */
    double aging_ppb_s = 0.5 / 86400.0;  /* 0.5 ppb/day */
    double wander = 0.0;
    double cum = urand();                /* cycles incl. random fractional start */
    double jprev = 0.0;
    long long prev_floor = (long long)floor(cum);
    double sum2 = 0; long n2 = 0, locked_at = -1;
    double max_hold = 0, phase_true = 0;   /* true OCXO-vs-GNSS phase (ns) */
    double sum_t2 = 0; long n_t2 = 0;
    const char *last = "";
    for (int t = 1; t <= T; t++) {
        wander += 0.002 * gauss();
        double f_ppb = off0 + g_true * ((double)d.dac_code - 32768.0)
                       + aging_ppb_s * t + wander;
        double jit = gauss() * 15.0 + (urand() < 0.002 ? gauss() * 200.0 : 0.0);  /* ns */
        double dcyc = 1e7 * (1.0 + f_ppb * 1e-9) + (jit - jprev) * 1e-9 * 1e7;
        jprev = jit;
        cum += dcyc;
        long long fl = (long long)floor(cum);
        uint32_t count = (uint32_t)(fl - prev_floor);
        prev_floor = fl;
        phase_true += f_ppb;                       /* ns/s */
        bool valid = !(t >= OUT_A && t < OUT_B);
        if (urand() < 0.0005) count += 3;          /* glitch */
        if (urand() < 0.0003) { disc_no_pps(&d); continue; }   /* missed PPS */
        disc_update(&d, count, valid);
        const char *s = disc_state_name(d.state);
        if (s != last) { printf("t=%6d s  state -> %s\n", t, s); last = s; }
        if (d.locked && locked_at < 0) { locked_at = t; printf("t=%6d s  LOCKED flag\n", t); }
        if (d.state == DISC_PHASE_LOCK && t > 2 * 3600 && t < OUT_A) {
            sum2 += d.phase_ns * d.phase_ns; n2++;
        }
        if (t == OUT_A) { max_hold = 0; }
        if (t >= OUT_A && t <= OUT_B) {
            /* measured error against steady-state frequency reference: use f_ppb */
            if (fabs(f_ppb) > max_hold) max_hold = fabs(f_ppb);
        }
        if (t % 3600 == 0)
            printf("t=%2dh %-10s locked=%d phase=%7.0f ns f_err=%+7.3f ppb dac=%5u sat=%d glitches=%u\n",
                   t / 3600, s, d.locked, d.phase_ns, f_ppb, d.dac_code, d.dac_saturated, d.glitches);
    }
    printf("\nPLL phase rms (2h..3h): %.1f ns\n", n2 ? sqrt(sum2 / n2) : -1.0);
    printf("Max |freq error| during 1 h outage: %.3f ppb\n", max_hold);
    printf("Final state: %s, locked=%d\n", disc_state_name(d.state), d.locked);
    (void)sum_t2; (void)n_t2;
    return 0;
}
