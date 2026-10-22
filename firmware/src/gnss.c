/* Minimal NMEA parser: RMC validity + GGA satellite count. Author: Erik, OH2LAK */
#include "gnss.h"
#include "pins.h"
#include "hardware/uart.h"
#include "hardware/gpio.h"
#include "pico/time.h"
#include <string.h>
#include <stdlib.h>

static char line[128];
static int  len;
static uint32_t last_valid_ms;
static int sats;

void gnss_init(void)
{
    gpio_init(PIN_GNSS_RESET_N);
    gpio_set_dir(PIN_GNSS_RESET_N, GPIO_OUT);
    gpio_put(PIN_GNSS_RESET_N, 1);
    uart_init(GNSS_UART, GNSS_BAUD);
    gpio_set_function(PIN_GNSS_TX, GPIO_FUNC_UART);
    gpio_set_function(PIN_GNSS_RX, GPIO_FUNC_UART);
}

static const char *field(const char *s, int n)
{
    while (n-- > 0) { s = strchr(s, ','); if (!s) return NULL; s++; }
    return s;
}

static void parse(const char *s)
{
    if (strlen(s) < 6 || s[0] != '$') return;
    if (!strncmp(s + 3, "RMC", 3)) {
        const char *f = field(s, 2);
        if (f && *f == 'A') last_valid_ms = to_ms_since_boot(get_absolute_time());
    } else if (!strncmp(s + 3, "GGA", 3)) {
        const char *f = field(s, 7);
        if (f) sats = atoi(f);
    }
}

void gnss_poll(void)
{
    while (uart_is_readable(GNSS_UART)) {
        char ch = (char)uart_getc(GNSS_UART);
        if (ch == '\n' || ch == '\r') {
            if (len) { line[len] = 0; parse(line); len = 0; }
        } else if (len < (int)sizeof(line) - 1) {
            line[len++] = ch;
        } else {
            len = 0;
        }
    }
}

bool gnss_time_valid(void)
{
    return last_valid_ms &&
           (to_ms_since_boot(get_absolute_time()) - last_valid_ms) < 3000;
}

int gnss_sats(void) { return sats; }
