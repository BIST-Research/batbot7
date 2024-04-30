/*
 * Author: Ben Westcott
 * Date created: 8/25/23
 */

#ifndef ML_DAC1_H
#define ML_DAC1_H

#include <Arduino.h>
#include <ml_dac_common.h>

#ifdef __cplusplus
extern "C"
{
#endif

void DAC1_init(void);
int8_t DAC1_enable(void);
int8_t DAC1_disable(void);

int8_t DAC1_set_oversampling_ratio(const ml_dac_osr_t value);
int8_t DAC1_set_refresh_period(const uint8_t period_us);

int8_t DAC1_runstdby_enable(void);
int8_t DAC1_runstdby_disable(void);

int8_t DAC1_extfilt_enable(void);
int8_t DAC1_extfilt_disable(void);

int8_t DAC1_dither_enable(void);
int8_t DAC1_dither_disable(void);

int8_t DAC1_set_leftadj(void);
int8_t DAC1_set_rightadj(void);

void DAC1_write(const uint16_t value);
void DAC1_buffer_write(const uint16_t value);
uint16_t DAC1_get_interpol_result(void);

#define ML_DAC1_GET_READY1_STATUS()          (DAC->STATUS.bit.READY1)
#define ML_DAC1_GET_EOC1_STATUS()            (DAC->STATUS.bit.EOC1)

// EVCTRL is PAC write protected
#define ML_DAC1_STARTEI_ENABLE()            (DAC->EVCTRL.bit.STARTEI1 = 0x01)
#define ML_DAC1_STARTEI_DISABLE()           (DAC->EVCTRL.bit.STARTEI1 = 0x00)
#define ML_DAC1_EMPTYEO_ENABLE()            (DAC->EVCTRL.bit.EMPTYEO1 = 0x01)
#define ML_DAC1_EMPTYEO_DISABLE()           (DAC->EVCTRL.bit.EMPTYEO1 = 0x00)
#define ML_DAC1_INVEI_ENABLE()              (DAC->EVCTRL.bit.INVEI1 = 0x01)
#define ML_DAC1_INVEI_DISABLE()             (DAC->EVCTRL.bit.INVEI1 = 0x00)
#define ML_DAC1_RESRDYEO_ENABLE()           (DAC->EVCTRL.bit.RESRDYEO1 = 0x01)
#define ML_DAC1_RESRDYEO_DISABLE()          (DAC->EVCTRL.bit.RESRDYEO1 = 0x00)

#define ML_DAC1_INTSET_UNDERRUN()           (DAC->INTENSET.bit.UNDERRUN1 = 0x01)
#define ML_DAC1_INTSET_EMPTY()              (DAC->INTENSET.bit.EMPTY1 = 0x01)
#define ML_DAC1_INTSET_RESRDY()             (DAC->INTENSET.bit.RESRDY1 = 0x01)
#define ML_DAC1_INTSET_OVERRUN()            (DAC->INTENSET.bit.OVERRUN1 = 0x01)

#define ML_DAC1_INTCLR_UNDERRUN()           (DAC->INTENCLR.bit.UNDERRUN1 = 0x01)
#define ML_DAC1_INTCLR_EMPTY()              (DAC->INTENCLR.bit.EMPTY1 = 0x01)
#define ML_DAC1_INTCLR_RESRDY()             (DAC->INTENCLR.bit.RESRDY1 = 0x01)
#define ML_DAC1_INTCLR_OVERRUN()            (DAC->INTENCLR.bit.OVERRUN1 = 0x01)

#define ML_DAC1_UNDERRUN_CLR_INTFLAG()      (DAC->INTFLAG.bit.UNDERRUN1 = 0x01)
#define ML_DAC1_EMPTY_CLR_INTFLAG()         (DAC->INTFLAG.bit.EMPTY1 = 0x01)
#define ML_DAC1_RESRDY_CLR_INTFLAG()        (DAC->INTFLAG.bit.RESRDY1 = 0x01)
#define ML_DAC1_OVERRUN_CLR_INTFLAG()       (DAC->INTFLAG.bit.OVERRUN1 = 0x01)

#define ML_DAC11_UNDERRUN_INTFLAG()         (DAC->INTFLAG.bit.UNDERRUN1 == 0x01)
#define ML_DAC1_EMPTY_INTFLAG()             (DAC->INTFLAG.bit.EMPTY1 == 0x01)
#define ML_DAC1_RESRDY_INTFLAG()            (DAC->INTFLAG.bit.RESRDY1 == 0x01)
#define ML_DAC1_OVERRUN_INTFLAG()           (DAC->INTFLAG.bit.OVERRUN1 == 0x01)

#ifdef __cplusplus
}
#endif

#endif // ML_DAC1_H