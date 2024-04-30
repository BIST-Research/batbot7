/*
 * Author: Ben Westcott
 * Date created: 8/25/23
 */

#ifndef ML_DAC0_H
#define ML_DAC0_H

#include <Arduino.h>
#include <ml_dac_common.h>

#ifdef __cplusplus
extern "C"
{
#endif

void DAC0_init(void);
int8_t DAC0_enable(void);
int8_t DAC0_disable(void);

int8_t DAC0_set_oversampling_ratio(const ml_dac_osr_t value);
int8_t DAC0_set_refresh_period(const uint8_t period_us);

int8_t DAC0_runstdby_enable(void);
int8_t DAC0_runstdby_disable(void);

int8_t DAC0_extfilt_enable(void);
int8_t DAC0_extfilt_disable(void);

int8_t DAC0_dither_enable(void);
int8_t DAC0_dither_disable(void);

int8_t DAC0_set_leftadj(void);
int8_t DAC0_set_rightadj(void);

void DAC0_write(const uint16_t value);
void DAC0_buffer_write(const uint16_t value);
uint16_t DAC0_get_interpol_result(void);

#define ML_DAC0_GET_READY_STATUS()          (DAC->STATUS.bit.READY0)
#define ML_DAC0_GET_EOC_STATUS()            (DAC->STATUS.bit.EOC0)

// EVCTRL is PAC write protected
#define ML_DAC0_STARTEI_ENABLE()            (DAC->EVCTRL.bit.STARTEI0 = 0x01)
#define ML_DAC0_STARTEI_DISABLE()           (DAC->EVCTRL.bit.STARTEI0 = 0x00)
#define ML_DAC0_EMPTYEO_ENABLE()            (DAC->EVCTRL.bit.EMPTYEO0 = 0x01)
#define ML_DAC0_EMPTYEO_DISABLE()           (DAC->EVCTRL.bit.EMPTYEO0 = 0x00)
#define ML_DAC0_INVEI_ENABLE()              (DAC->EVCTRL.bit.INVEI0 = 0x01)
#define ML_DAC0_INVEI_DISABLE()             (DAC->EVCTRL.bit.INVEI0 = 0x00)
#define ML_DAC0_RESRDYEO_ENABLE()           (DAC->EVCTRL.bit.RESRDYEO0 = 0x01)
#define ML_DAC0_RESRDYEO_DISABLE()          (DAC->EVCTRL.bit.RESRDYEO0 = 0x00)

#define ML_DAC0_INTSET_UNDERRUN()           (DAC->INTENSET.bit.UNDERRUN0 = 0x01)
#define ML_DAC0_INTSET_EMPTY()              (DAC->INTENSET.bit.EMPTY0 = 0x01)
#define ML_DAC0_INTSET_RESRDY()             (DAC->INTENSET.bit.RESRDY0 = 0x01)
#define ML_DAC0_INTSET_OVERRUN()            (DAC->INTENSET.bit.OVERRUN0 = 0x01)

#define ML_DAC0_INTCLR_UNDERRUN()           (DAC->INTENCLR.bit.UNDERRUN0 = 0x01)
#define ML_DAC0_INTCLR_EMPTY()              (DAC->INTENCLR.bit.EMPTY0 = 0x01)
#define ML_DAC0_INTCLR_RESRDY()             (DAC->INTENCLR.bit.RESRDY0 = 0x01)
#define ML_DAC0_INTCLR_OVERRUN()            (DAC->INTENCLR.bit.OVERRUN0 = 0x01)

#define ML_DAC0_UNDERRUN_CLR_INTFLAG()      (DAC->INTFLAG.bit.UNDERRUN0 = 0x01)
#define ML_DAC0_EMPTY_CLR_INTFLAG()         (DAC->INTFLAG.bit.EMPTY0 = 0x01)
#define ML_DAC0_RESRDY_CLR_INTFLAG()        (DAC->INTFLAG.bit.RESRDY0 = 0x01)
#define ML_DAC0_OVERRUN_CLR_INTFLAG()       (DAC->INTFLAG.bit.OVERRUN0 = 0x01)

#define ML_DAC0_UNDERRUN_INTFLAG()          (DAC->INTFLAG.bit.UNDERRUN0 == 0x01)
#define ML_DAC0_EMPTY_INTFLAG()             (DAC->INTFLAG.bit.EMPTY0 == 0x01)
#define ML_DAC0_RESRDY_INTFLAG()            (DAC->INTFLAG.bit.RESRDY0 == 0x01)
#define ML_DAC0_OVERRUN_INTFLAG()           (DAC->INTFLAG.bit.OVERRUN0 == 0x01)

#ifdef __cplusplus
}
#endif

#endif // ML_DAC0_H