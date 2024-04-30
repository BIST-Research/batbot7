/*
 * Author: Ben Westcott
 * Date created: 8/1/23
 */

#include <ml_ac.h>

void AC_sync(void) 
{ 
    while(AC->SYNCBUSY.reg); 
}

#define AC_CHANNEL 0x00

void AC_init(void)
{

    ML_AC_DISABLE();
    AC_sync();

    ML_AC_SWRST();
    AC_sync();

    AC->COMPCTRL[AC_CHANNEL].reg |= (AC_COMPCTRL_MUXPOS_PIN3|
                                     AC_COMPCTRL_MUXNEG_GND  | 
                                     AC_COMPCTRL_SPEED_HIGH  |
                                     AC_COMPCTRL_HYST_HYST150|
                                     AC_COMPCTRL_FLEN_MAJ5   |
                                     AC_COMPCTRL_INTSEL_TOGGLE |
                                     AC_COMPCTRL_OUT_SYNC);

    AC->COMPCTRL[AC_CHANNEL].bit.SINGLE = 0x0;
   // AC->COMPCTRL[0].bit.HYSTEN = 0x1;
   // AC->COMPCTRL[0].bit.SWAP = 0x1;

   // AC->SCALER[0].reg = AC_SCALER_VALUE(20); 

    AC->INTENSET.reg |= AC_INTENSET_COMP0;

    NVIC_SetPriority(AC_IRQn, 0);
    NVIC_EnableIRQ(AC_IRQn);

    AC->COMPCTRL[AC_CHANNEL].reg |= AC_COMPCTRL_ENABLE;
    AC_sync();

    ML_AC_ENABLE();
    AC_sync();
}