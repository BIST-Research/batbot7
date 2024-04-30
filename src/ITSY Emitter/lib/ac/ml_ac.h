/*
 * Author: Ben Westcott
 * Date created: 3/12/23
 */

#ifndef ML_AC_H
#define ML_AC_H

#include <Arduino.h>

#ifdef __cplusplus
extern "C"
{
#endif

#define ML_AC_ENABLE()(AC->CTRLA.reg |= AC_CTRLA_ENABLE)

#define ML_AC_DISABLE()(AC->CTRLA.reg &= ~AC_CTRLA_ENABLE)

#define ML_AC_SWRST()(AC->CTRLA.reg |= AC_CTRLA_SWRST)

#define ML_AC_SET_CONT_MEASURE(channel)(AC->COMPCTRL[channel].reg &= ~AC_COMPCTRL_SINGLE)

#define ML_AC_SET_SINGLE_MEASURE(channel)(AC->COMPCTRL[channel].reg |= AC_COMPCTRL_SINGLE)

#define ML_AC_CLR_COMP0_INTFLAG() (AC->INTFLAG.bit.COMP0 = 0x1)

#define ML_AC_IS_COMP0_INT() (AC->INTFLAG.bit.COMP0)

void AC_sync(void);
void AC_init(void);

#ifdef __cplusplus
}
#endif

#endif // ML_AC_H