/*
 * Author: Ben Westcott
 * Date created: 3/6/23
 */

#ifndef ML_ADC_COMMON_H
#define ML_ADC_COMMON_H

#include <Arduino.h>

#ifdef __cplusplus
extern "C"
{
#endif

void ADC_sync(Adc *instance);
void ADC_enable(Adc *instance);
void ADC_disable(Adc *instance);
void ADC_swrst(Adc *instance);
void ADC_swtrig_start(Adc *instance);
void ADC_flush(Adc *instance);

#define ML_ADC_START(instance) \
{\
    ADC_enable(instance); \
    ADC_flush(instance);\
    ADC_swtrig_start(instance); \
}

#define ML_ADC_WINMON_INTSET(instance)      (instance->INTENSET.bit.WINMON = 0x01)
#define ML_ADC_OVERRUN_INTSET(instance)     (instance->INTENSET.bit.OVERRUN = 0x01)
#define ML_ADC_RESRDY_INTSET(instance)       (instance->INTENSET.bit.RESRDY = 0x01)

#define ML_ADC_WINMON_INTCLR(instance)      (instance->INTENCLR.bit.WINMON = 0x01)
#define ML_ADC_OVERRUN_INTCLR(instance)     (instance->INTENCLR.bit.OVERRUN = 0x01)
#define ML_ADC_RESRDY_INTCLR(instance)      (instance->INTENCLR.bit.RESRDY = 0x01)

#define ML_ADC_WINMON_INTFLAG(instance)      (instance->INTFLAG.bit.WINMON == 0x01)
#define ML_ADC_OVERRUN_INTFLAG(instance)     (instance->INTFLAG.bit.OVERRUN == 0x01)
#define ML_ADC_RESRDY_INTFLAG(instance)      (instance->INTFLAG.bit.RESRDY == 0x01)

#define ML_ADC_WINMON_CLR_INTFLAG(instance)      (instance->INTFLAG.bit.WINMON = 0x01)
#define ML_ADC_OVERRUN_CLR_INTFLAG(instance)     (instance->INTFLAG.bit.OVERRUN = 0x01)
#define ML_ADC_RESRDY_CLR_INTFLAG(instance)      (instance->INTFLAG.bit.RESRDY = 0x01)

#define ML_ADC_CLR_INTFLAGS(instance)           (instance->INTFLAG.reg = ADC_INTFLAG_MASK)

//#define PASTE_FUSE(REG) ((*((uint32_t *) (REG##_ADDR)) & (REG##_Msk)) >> (REG##_Pos))


#ifdef __cplusplus
}
#endif

#endif // ML_ADC_COMMON_H