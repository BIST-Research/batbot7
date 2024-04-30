/*
 * Author: Ben Westcott, Jayson De La Vega
 * Date created: 8/11/23
 */

#include <ml_spi_common.h>

void spi_enable(Sercom *coms)
{
    coms->SPI.CTRLA.bit.ENABLE = 0x01;
    while(coms->SPI.SYNCBUSY.bit.ENABLE != 0U)
    {
        /* Wait for sync */
    }
}

void spi_disable(Sercom *coms)
{
    coms->SPI.CTRLA.bit.ENABLE = 0x00;
    while(coms->SPI.SYNCBUSY.bit.ENABLE != 0U)
    {
        /* Wait for sync */
    }
}

void spi_swrst(Sercom *coms)
{
    coms->SPI.CTRLA.bit.SWRST = 0x01;
    while(coms->SPI.SYNCBUSY.bit.SWRST != 0U)
    {
        /* Wait for sync */
    }
}

void spi_reciever_enable(Sercom *coms)
{
    coms->SPI.CTRLB.bit.RXEN = true;
    while(coms->SPI.SYNCBUSY.bit.CTRLB != 0U)
    {
        /* Wait for sync */
    }
}
void spi_reciever_disable(Sercom *coms)
{
    coms->SPI.CTRLB.bit.RXEN = false;
    while(coms->SPI.SYNCBUSY.bit.CTRLB != 0U)
    {
        /* Wait for sync */
    }
}

uint32_t spi_read32b(Sercom *coms, uint32_t data)
{
    while(coms->SPI.INTFLAG.bit.DRE == 0)
    {
        /* Wait for data ready flag */
    }
    coms->SPI.DATA.reg = data;
    while(coms->SPI.INTFLAG.bit.RXC == 0)
    {
        /* Wait for recieve complete intflag */
    }
    return (uint32_t)coms->SPI.DATA.reg;
}

uint8_t spi_read8b(Sercom *coms, uint8_t data)
{
    while(coms->SPI.INTFLAG.bit.DRE == 0)
    {
        /* Wait for data ready flag */
    }
    coms->SPI.DATA.reg = data;
    while(coms->SPI.INTFLAG.bit.RXC == 0)
    {
        /* Wait for recieve complete intflag */
    }
    return (uint8_t)coms->SPI.DATA.reg;
}

void spi_dmac_tx_init
(
    ml_dmac_s *dmac_s,
    Sercom *coms_inst,
    DmacDescriptor *cpy
)
{
    ml_dmac_chnum_t chnum = dmac_s->ex_chnum;

    DMAC_channel_init
    (
        chnum,
        dmac_s->chan_settings,
        dmac_s->chan_prilvl
    );

    uint32_t btsize = DMAC_extract_btsize(dmac_s->descriptor_settings);

    DMAC_descriptor_init
    (
        dmac_s->descriptor_settings,
        dmac_s->ex_len,
        (uint32_t)dmac_s->ex_ptr + (btsize * dmac_s->ex_len),
        (uint32_t)&coms_inst->SPI.DATA.reg,
        (uint32_t) cpy, cpy
    );

    DMAC_channel_intenset
    (
        chnum,
        dmac_s->irqn,
        dmac_s->intmsk,
        dmac_s->irqn_prilvl
    );

}

void spi_dmac_rx_init
(
    ml_dmac_s *dmac_s,
    Sercom *coms_inst,
    DmacDescriptor *cpy
)
{
    ml_dmac_chnum_t chnum = dmac_s->ex_chnum;

    DMAC_channel_init
    (
        chnum,
        dmac_s->chan_settings,
        dmac_s->chan_prilvl
    );

    uint32_t btsize = DMAC_extract_btsize(dmac_s->descriptor_settings);

    DMAC_descriptor_init
    (
        dmac_s->descriptor_settings,
        dmac_s->ex_len,
        (uint32_t)&coms_inst->SPI.DATA.reg,
        (uint32_t)dmac_s->ex_ptr + (btsize * dmac_s->ex_len),
        (uint32_t) cpy, cpy
    );

    DMAC_channel_intenset
    (
        chnum,
        dmac_s->irqn,
        dmac_s->intmsk,
        dmac_s->irqn_prilvl
    );
}


