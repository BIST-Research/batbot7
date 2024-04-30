/*
 * Author: Ben Westcott
 * Date created: 8/24/23
 */

#include <ml_dac_common.h>
#include <ml_tc1.h>

void DAC_enable(void)
{
    DAC->CTRLA.bit.ENABLE = 0x01;
    while(DAC->SYNCBUSY.bit.ENABLE != 0U)
    {
        /* Wait for sync */
    }
}

void DAC_disable(void)
{
    DAC->CTRLA.bit.ENABLE = 0x00;
    while(DAC->SYNCBUSY.bit.ENABLE != 0U)
    {
        /* Wait for sync */
    }
}
void DAC_swrst(void)
{
    DAC->CTRLA.bit.SWRST = 0x01;
    while(DAC->SYNCBUSY.bit.SWRST != 0U)
    {
        /* Wait for sync */
    }
}

void DAC_init(void)
{
    DAC_disable();
    DAC_swrst();

    DAC->INTFLAG.reg = DAC_INTFLAG_MASK;

    ML_DAC_SET_REFSEL(VREF_VREFAB);
    ML_DAC_UNSET_DIFFMODE();

    //TC1_init();
    //TC1_CC0_pinout();
}

