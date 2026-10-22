#ifndef HAMREF_GNSS_H
#define HAMREF_GNSS_H
#include <stdbool.h>
void gnss_init(void);
void gnss_poll(void);          /* call often; parses NMEA from UART */
bool gnss_time_valid(void);    /* RMC status 'A' seen within the last 3 s */
int  gnss_sats(void);
#endif
