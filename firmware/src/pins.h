/* HamREF proto-v0.1 GPIO map (RP2350, Waveshare RP2350-Plus). Author: Erik, OH2LAK */
#ifndef HAMREF_PINS_H
#define HAMREF_PINS_H

#define PIN_GNSS_TX      0   /* UART0 TX -> LEA-M8S RXD */
#define PIN_GNSS_RX      1   /* UART0 RX <- LEA-M8S TXD */
#define PIN_DAC_SDA      2   /* I2C1 */
#define PIN_DAC_SCL      3
#define PIN_OLED_SDA     4   /* I2C0 */
#define PIN_OLED_SCL     5
#define PIN_PPS_IN       6   /* GNSS TIMEPULSE (1PPS)   -- must be PIN_TEN_MHZ_IN - 1 */
#define PIN_TEN_MHZ_IN   7   /* OCXO 10 MHz (squared)   -- PIO in_base = PIN_PPS_IN   */
#define PIN_PPS_OUT      8
#define PIN_GNSS_RESET_N 9
#define PIN_GNSS_EXTINT0 10
#define PIN_ENC_A        11
#define PIN_ENC_B        12
#define PIN_ENC_BTN      13
#define PIN_WS2812       14
#define PIN_OCXO_FLT     16
#define PIN_OCXO_EN      21
#define PIN_ADC_5V       26
#define PIN_ADC_NTC      27
#define PIN_ADC_EFC      28

#define DAC_I2C          i2c1
#define DAC_I2C_ADDR     0x60  /* MCP4725 A0=GND; check the schematic */
#define GNSS_UART        uart0
#define GNSS_BAUD        9600

#endif
