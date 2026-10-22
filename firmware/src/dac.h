#ifndef HAMREF_DAC_H
#define HAMREF_DAC_H
#include <stdint.h>
void dac_init(void);
/* 16-bit code; MCP4725 uses the upper 12 bits (swap driver for 16-bit DAC later). */
void dac_write16(uint16_t code);
#endif
