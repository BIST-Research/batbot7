/*
 * Author: Ben Westcott, Jayson De La Vega
 * Date created: 8/11/23
 */

#ifndef ML_SERCOM_SPI_H
#define ML_SERCOM_SPI_H

#include <Arduino.h>
#include <ml_port.h>
#include <ml_tc_common.h>
#include <ml_clocks.h>
#include <ml_sercom.h>
#include <ml_dmac.h>

#ifdef __cplusplus
extern "C"
{
#endif


#define ML_SERCOM_SPI_FRAME_SPI             0x00
#define ML_SERCOM_SPI_FRAME_SPI_WITH_ADDR   0x02

typedef enum _ml_spi_frame_t
{
    FRAME_SPI = ML_SERCOM_SPI_FRAME_SPI,
    FRAME_SPI_WADDR = ML_SERCOM_SPI_FRAME_SPI_WITH_ADDR
} ml_spi_frame_t;

#define ML_SERCOM_SPI_DIPO_PAD0             0x00
#define ML_SERCOM_SPI_DIPO_PAD1             0x01
#define ML_SERCOM_SPI_DIPO_PAD2             0x02
#define ML_SERCOM_SPI_DIPO_PAD3             0x03

typedef enum _ml_spi_dipo_t
{
    DIPO_PAD0 = ML_SERCOM_SPI_DIPO_PAD0,
    DIPO_PAD1 = ML_SERCOM_SPI_DIPO_PAD1,
    DIPO_PAD2 = ML_SERCOM_SPI_DIPO_PAD2,
    DIPO_PAD3 = ML_SERCOM_SPI_DIPO_PAD3
} ml_spi_dipo_t;

#define ML_SERCOM_SPI_DOPO_DO0              0x00
#define ML_SERCOM_SPI_DOPO_DO3              0x02

typedef enum _ml_spi_dopo_t
{
    DOPO_PAD0 = ML_SERCOM_SPI_DOPO_DO0,
    DOPO_PAD3 = ML_SERCOM_SPI_DOPO_DO3
} ml_spi_dopo_t;

#define ML_SERCOM_SPI_ADDR_MODE_MASK        0x00
#define ML_SERCOM_SPI_ADDR_MODE_2ADDRS      0x01
#define ML_SERCOM_SPI_ADDR_MODE_RANGE       0x02

typedef enum _ml_spi_addrmode_t
{
    ADDRMODE_MASK = ML_SERCOM_SPI_ADDR_MODE_MASK,
    ADDRMODE_2ADDRS = ML_SERCOM_SPI_ADDR_MODE_2ADDRS,
    ADDRMODE_RANGE = ML_SERCOM_SPI_ADDR_MODE_RANGE
} ml_spi_addrmode_t;

#define ML_SERCOM_SPI_CHSIZE_8BIT           0x00
#define ML_SERCOM_SPI_CHSIZE_9BIT           0x01

typedef enum _ml_spi_charsize_t
{
    CHARSIZE_8BIT = ML_SERCOM_SPI_CHSIZE_8BIT,
    CHARSIZE_9BIT = ML_SERCOM_SPI_CHSIZE_9BIT
} ml_spi_charsize_t;

// CPOL = 0, CPHA = 0
#define ML_SERCOM_SPI_MODE0                 (0x00 << SERCOM_SPI_CTRLA_CPHA_Pos)
// CPOL = 1, CPHA = 0
#define ML_SERCOM_SPI_MODE2                 (0x02 << SERCOM_SPI_CTRLA_CPHA_Pos)
// CPOL = 0, CPHA = 1
#define ML_SERCOM_SPI_MODE1                 (0x01 << SERCOM_SPI_CTRLA_CPHA_Pos)
// CPOL = 1, CPHA = 1
#define ML_SERCOM_SPI_MODE3                 (0x03 << SERCOM_SPI_CTRLA_CPHA_Pos)

typedef enum _ml_spi_xfermode_t
{
    XFERMODE0 = ML_SERCOM_SPI_MODE0,
    XFERMODE1 = ML_SERCOM_SPI_MODE1,
    XFERMODE2 = ML_SERCOM_SPI_MODE2,
    XFERMODE3 = ML_SERCOM_SPI_MODE3
} ml_spi_xfermode_t;

#define ML_SERCOM_SPI_MODE_SLAVE            0x02
#define ML_SERCOM_SPI_MODE_MASTER           0x03

typedef enum _ml_spi_opmode_t
{
    OPMODE_MASTER = ML_SERCOM_SPI_MODE_MASTER,
    OPMODE_SLAVE = ML_SERCOM_SPI_MODE_SLAVE
} ml_spi_opmode_t;

#define ML_SERCOM_SPI_DORD_MSBFIRST              0x00
#define ML_SERCOM_SPI_DORD_LSBFIRST              0x01

typedef enum _ml_spi_dord_t
{
    DORD_MSBFIRST = ML_SERCOM_SPI_DORD_MSBFIRST,
    DORD_LSBFIRST = ML_SERCOM_SPI_DORD_LSBFIRST
} ml_spi_dord_t;

typedef struct _ml_spi_s
{
    Sercom *com_inst;
    ml_spi_opmode_t opmode;

    ml_tc_cc_t ss_timer_idx;
    Tc *ss_timer_inst;
    
    ml_dmac_s rx_dmac_s;
    ml_dmac_s tx_dmac_s;

} ml_spi_s;

typedef enum _ml_spi_state
{
    IDLE= 0x00,
    SS_LOW_WAIT,
    XFER_START,
    XFER_DMAC,
    SS_HIGH_WAIT
} ml_spi_state;

void spi_enable(Sercom *coms);
void spi_disable(Sercom *coms);
void spi_swrst(Sercom *coms);
void spi_reciever_enable(Sercom *coms);
void spi_reciever_disable(Sercom *coms);

uint32_t spi_read32b(Sercom *coms, uint32_t val);
uint8_t spi_read8b(Sercom *coms, uint8_t val);

void spi_dmac_tx_init
(
    ml_dmac_s *dmac_s,
    Sercom *coms_inst,
    DmacDescriptor *cpy
);

void spi_dmac_rx_init
(
    ml_dmac_s *dmac_s,
    Sercom *coms_inst,
    DmacDescriptor *cpy
);

#define ML_SERCOM_SPI_INTSET_DRE(instance)          (instance->SPI.INTENSET.bit.DRE = 0x01)
#define ML_SERCOM_SPI_INTSET_TXC(instance)          (instance->SPI.INTENSET.bit.TXC = 0x01)
#define ML_SERCOM_SPI_INTSET_RXC(instance)          (instance->SPI.INTENSET.bit.RXC = 0x01)
#define ML_SERCOM_SPI_INTSET_SSL(instance)          (instance->SPI.INTENSET.bit.SSL = 0x01)
#define ML_SERCOM_SPI_INTSET_ERR(instance)          (instance->SPI.INTENSET.bit.ERROR = 0x01)

#define ML_SERCOM_SPI_INTCLR_DRE(instance)          (instance->SPI.INTENCLR.bit.DRE = 0x01)
#define ML_SERCOM_SPI_INTCLR_TXC(instance)          (instance->SPI.INTENCLR.bit.TXC = 0x01)
#define ML_SERCOM_SPI_INTCLR_RXC(instance)          (instance->SPI.INTENCLR.bit.RXC = 0x01)
#define ML_SERCOM_SPI_INTCLR_SSL(instance)          (instance->SPI.INTENCLR.bit.SSL = 0x01)
#define ML_SERCOM_SPI_INTCLR_ERR(instance)          (instance->SPI.INTENCLR.bit.ERROR = 0x01)

#define ML_SERCOM_SPI_DRE_CLR_INTFLAG(instance)     (instance->SPI.INTFLAG.bit.DRE = 0x01)
#define ML_SERCOM_SPI_TXC_CLR_INTFLAG(instance)     (instance->SPI.INTFLAG.bit.TXC = 0x01)
#define ML_SERCOM_SPI_RXC_CLR_INTFLAG(instance)     (instance->SPI.INTFLAG.bit.RXC = 0x01)
#define ML_SERCOM_SPI_SSL_CLR_INTFLAG(instance)     (instance->SPI.INTFLAG.bit.SSL = 0x01)
#define ML_SERCOM_SPI_ERR_CLR_INTFLAG(instance)     (instance->SPI.INTFLAG.bit.ERROR = 0x01)

#define ML_SERCOM_SPI_DRE_INTFLAG(instance)         (instance->SPI.INTFLAG.bit.DRE == 0x01)
#define ML_SERCOM_SPI_TXC_INTFLAG(instance)         (instance->SPI.INTFLAG.bit.TXC == 0x01)
#define ML_SERCOM_SPI_RXC_INTFLAG(instance)         (instance->SPI.INTFLAG.bit.RXC == 0x01)
#define ML_SERCOM_SPI_SSL_INTFLAG(instance)         (instance->SPI.INTFLAG.bit.SSL == 0x01)
#define ML_SERCOM_SPI_ERR_INTFLAG(instance)         (instance->SPI.INTFLAG.bit.ERROR == 0x01)

#ifdef __cplusplus
}
#endif

#endif // ML_SERCOM_SPI_H