/*
 * Author: Ben Westcott
 * Date created: 3/6/23
 */

#ifndef ML_DMAC_H
#define ML_DMAC_H

#include <Arduino.h>

#ifdef __cplusplus
extern "C"
{
#endif

typedef enum _ml_dmac_chnum_t
{
    DMAC_CH0, DMAC_CH1, DMAC_CH2, DMAC_CH3, DMAC_CH4,
    DMAC_CH5, DMAC_CH6, DMAC_CH7, DMAC_CH8, DMAC_CH9,
    DMAC_CH10, DMAC_CH11, DMAC_CH12, DMAC_CH13, DMAC_CH14,
    DMAC_CH15, DMAC_CH16, DMAC_CH17, DMAC_CH18, DMAC_CH19,
    DMAC_CH20, DMAC_CH21, DMAC_CH22, DMAC_CH23, DMAC_CH24,
    DMAC_CH26, DMAC_CH27, DMAC_CH28, DMAC_CH29, DMAC_CH30,
    DMAC_CH31, DMAC_CH32
} ml_dmac_chnum_t;

typedef enum _ml_dmac_chprilvl_t
{
    PRILVL0, PRILVL1, PRILVL2, PRILVL3
} ml_dmac_chprilvl_t;

typedef struct _ml_dmac_s
{
    const ml_dmac_chnum_t ex_chnum;
    const uint32_t chan_settings;
    uint8_t chan_prilvl;

    uint16_t ex_len;
    volatile uint8_t const * ex_ptr;
    const uint16_t descriptor_settings;
    uint8_t intmsk;

    const _Bool nvic;
    const IRQn_Type irqn;
    uint32_t irqn_prilvl;
} ml_dmac_s;

#define ML_DMAC_ENABLE()                            (DMAC->CTRL.reg |= DMAC_CTRL_DMAENABLE)
#define ML_DMAC_DISABLE()                           (DMAC->CTRL.reg &= ~DMAC_CTRL_DMAENABLE)
#define ML_DMAC_SWRST()                             (DMAC->CTRL.reg |= DMAC_CTRL_SWRST)

#define ML_DMAC_CHANNEL_ENABLE(channel)             (DMAC->Channel[channel].CHCTRLA.reg |= DMAC_CHCTRLA_ENABLE)
#define ML_DMAC_CHANNEL_DISABLE(channel)            (DMAC->Channel[channel].CHCTRLA.reg &= ~DMAC_CHCTRLA_ENABLE)
#define ML_DMAC_CHANNEL_SWRST(channel)              (DMAC->Channel[channel].CHCTRLA.reg |= DMAC_CHCTRLA_SWRST)

#define ML_DMAC_CHANNEL_RESUME(channel)             (DMAC->Channel[channel].CHCTRLB.reg |= DMAC_CHCTRLB_CMD_RESUME)
#define ML_DMAC_CHANNEL_SUSPEND(channel)            (DMAC->Channel[channel].CHCTRLB.reg |= DMAC_CHCTRLB_CMD_SUSPEND)

#define ML_DMAC_CHANNEL_INTSET_TCMPL(channel)       (DMAC->Channel[channel].CHINTENSET.bit.TCMPL = 0x01)
#define ML_DMAC_CHANNEL_INTSET_SUSP(channel)        (DMAC->Channel[channel].CHINTENSET.bit.SUSP = 0x01)
#define ML_DMAC_CHANNEL_INTSET_TERR(channel)        (DMAC->Channel[channel].CHINTENSET.bit.TERR = 0x01)

#define ML_DMAC_CHANNEL_CLR_TCMPL_INTFLAG(channel)  (DMAC->Channel[channel].CHINTFLAG.bit.TCMPL = 0x01)
#define ML_DMAC_CHANNEL_CLR_SUSP_INTFLAG(channel)   (DMAC->Channel[channel].CHINTFLAG.bit.SUSP = 0x01)
#define ML_DMAC_CHANNEL_CLR_TERR_INTFLAG(channel)   (DMAC->Channel[channel].CHINTFLAG.bit.TERR = 0x01)

#define ML_DMAC_CHANNEL_TCMPL_INTFLAG(channel)      (DMAC->Channel[channel].CHINTFLAG.bit.TCMPL == 0x01)
#define ML_DMAC_CHANNEL_SUSP_INTFLAG(channel)       (DMAC->Channel[channel].CHINTFLAG.bit.SUSP == 0x01)
#define ML_DMAC_CHANNEL_TERR_INTFLAG(channel)       (DMAC->Channel[channel].CHINTFLAG.bit.TERR == 0x01)

#define ML_DMAC_CLEAR_DESCRIPTOR_VALID_BIT(settings) (settings &= ~DMAC_BTCTRL_VALID)
#define ML_DMAC_SET_DESCRIPTOR_VALID_BIT(settings) (settings |= DMAC_BTCTRL_VALID)

void DMAC_channel_intenset(const ml_dmac_chnum_t channel, const IRQn_Type IRQn, const uint8_t intmsk, const uint32_t priority_level);

void DMAC_init(DmacDescriptor *base_descriptor, volatile DmacDescriptor *writeback_descriptor);

void DMAC_channel_init(const ml_dmac_chnum_t channel, const uint32_t settings, const ml_dmac_chprilvl_t priority_level);

void DMAC_descriptor_init(const uint16_t btsettings, 
                                const uint16_t btcnt, 
                                const uint32_t srcaddr, 
                                const uint32_t dstaddr, 
                                const uint32_t descaddr,
                                DmacDescriptor *cpy);

void DMAC_descriptor_cpyto
(
  DmacDescriptor *descriptor_target,
  DmacDescriptor *descriptor_src
);

uint32_t DMAC_extract_btsize(const uint16_t descriptor_settings);

void DMAC_suspend_channel
(
  uint8_t chnum
);

#ifdef __cplusplus
}
#endif

#endif // ML_DMAC_H