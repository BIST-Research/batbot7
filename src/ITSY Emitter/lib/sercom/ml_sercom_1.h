/*
 * Author: Ben Westcott, Jayson De La Vega
 * Date created: 8/11/23
 */

#ifndef ML_SERCOM_1_H
#define ML_SERCOM_1_H

#include <Arduino.h>
#include <ml_spi_common.h>
#include <ml_port.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C"
{
#endif

void sercom1_spi_init(const ml_spi_opmode_t opmode);

//void spi_port_init(void);

const extern ml_spi_s sercom1_spi_dmac_master_prototype;
const extern ml_spi_s sercom1_spi_dmac_slave_prototype;

const extern ml_pin_settings ml_sercom1_spi_ss0_pin;
const extern ml_pin_settings ml_sercom1_spi_ss1_pin;
const extern ml_pin_settings ml_sercom1_spi_ss2_pin;
const extern ml_pin_settings ml_sercom1_spi_ss3_pin;

#define ML_SERCOM1_SPI_SS0_PULL() (logical_unset(&ml_sercom1_spi_ss0_pin))
#define ML_SERCOM1_SPI_SS0_PUSH() (logical_set(&ml_sercom1_spi_ss0_pin))

#define ML_SERCOM1_SPI_SS1_PULL() (logical_unset(&ml_sercom1_spi_ss1_pin))
#define ML_SERCOM1_SPI_SS1_PUSH() (logical_set(&ml_sercom1_spi_ss1_pin))

#define ML_SERCOM1_SPI_SS2_PULL() (logical_unset(&ml_sercom1_spi_ss2_pin))
#define ML_SERCOM1_SPI_SS2_PUSH() (logical_set(&ml_sercom1_spi_ss2_pin))

#define ML_SERCOM1_SPI_SS3_PULL() (logical_unset(&ml_sercom1_spi_ss3_pin))
#define ML_SERCOM1_SPI_SS3_PUSH() (logical_set(&ml_sercom1_spi_ss3_pin))

#ifdef __cplusplus
}
#endif

#endif // ML_SERCOM_H