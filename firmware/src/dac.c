/* MCP4725 fast-mode write on I2C1. Author: Erik, OH2LAK */
#include "dac.h"
#include "pins.h"
#include "hardware/i2c.h"
#include "hardware/gpio.h"

void dac_init(void)
{
    i2c_init(DAC_I2C, 400 * 1000);
    gpio_set_function(PIN_DAC_SDA, GPIO_FUNC_I2C);
    gpio_set_function(PIN_DAC_SCL, GPIO_FUNC_I2C);
    gpio_pull_up(PIN_DAC_SDA);
    gpio_pull_up(PIN_DAC_SCL);
}

void dac_write16(uint16_t code)
{
    uint16_t v = code >> 4;
    uint8_t buf[2] = { (uint8_t)(v >> 8), (uint8_t)(v & 0xFF) };   /* fast mode, PD=0 */
    i2c_write_timeout_us(DAC_I2C, DAC_I2C_ADDR, buf, 2, false, 5000);
}
