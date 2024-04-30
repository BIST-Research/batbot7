/*
 * Author: Ben Westcott
 * Date created: 3/8/23
 */

#ifndef ML_TCC_COMMON_H
#define ML_TCC_COMMON_H

#include <Arduino.h>

#ifdef __cplusplus
extern "C"
{
#endif

#define ML_TCC0_CH0 0x0
#define ML_TCC0_CH1 0x1
#define ML_TCC0_CH2 0x2
#define ML_TCC0_CH3 0x3

#define ML_TCC1_CH0 0x0
#define ML_TCC1_CH1 0x1
#define ML_TCC1_CH2 0x2
#define ML_TCC1_CH3 0x3
#define ML_TCC1_CH7 0x7

// REQUIRES R/W SYNC
#define TCC_ENABLE(instance) (instance->CTRLA.reg |= TCC_CTRLA_ENABLE)

// REQUIRES R/W SYNC
#define TCC_DISABLE(instance) (instance->CTRLA.reg &= ~TCC_CTRLA_ENABLE)

// REQUIRES R/W SYNC
#define TCC_SWRST(instance) (instance->CTRLA.reg |= TCC_CTRLA_SWRST)

// REQUIRES R/W SYNC
#define TCC_SET_ONESHOT(instance) (instance->CTRLBSET.reg |= TCC_CTRLBSET_ONESHOT)

// REQUIRES R/W SYNC
#define TCC_CLR_ONESHOT(instance) (instance->CTRLBCLR.reg |= TCC_CTRLBCLR_ONESHOT)

// REQUIRES R/W SYNC
#define TCC_FORCE_STOP(instance) (instance->CTRLBSET.reg |= TCC_CTRLBSET_CMD_STOP)

// REQUIRES R/W SYNC
#define TCC_FORCE_RETRIGGER(instance) (instance->CTRLBSET.reg |= TCC_CTRLBSET_CMD_RETRIGGER)

#define TCC_IS_OVF(instance) (instance->INTFLAG.bit.OVF)

#define TCC_CLR_OVF_INTFLAG(instance) (instance->INTFLAG.bit.OVF = 0x1)

void TCC_enable(Tcc *instance);

void TCC_disable(Tcc *instance);

void TCC_swrst(Tcc *instance);

void TCC_sync(Tcc *instance);

void TCC_set_oneshot(Tcc *instance);

void TCC_clr_oneshot(Tcc *instance);

void TCC_force_stop(Tcc *instance);

void TCC_force_retrigger(Tcc *instance);

void TCC_set_period(Tcc *instance, uint32_t value);

void TCC_update_period(Tcc *instance, uint16_t val);

void TCC_lock_update(Tcc *instance);

void TCC_unlock_update(Tcc *instance);

void TCC_channel_capture_compare_set(Tcc *instance, const uint8_t channel, const uint8_t value);

void TCC_intenset(Tcc *instance, const IRQn_Type IRQn, const uint8_t interrupt_mask, const uint32_t priority_level);

void TCC_update_prescaler(Tcc *instance, uint8_t prescaler);

#ifdef __cplusplus
}
#endif

#endif // ML_TCC_COMMON_H