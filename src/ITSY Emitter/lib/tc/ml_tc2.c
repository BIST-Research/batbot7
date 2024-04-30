/*
 * Author: Ben Westcott
 * Date created: 4/7/24
 */

#include <ml_tc2.h>
#include <ml_tc_common.h>
#include <ml_port.h>

void TC2_init(void)
{
    TC_disable(TC2);
    TC_swrst(TC2);

    TC2->COUNT16.CTRLA.bit.PRESCALER = PRESCALER_DIV256;
    TC2->COUNT16.CTRLA.bit.MODE = MODE_COUNT16;
    TC2->COUNT16.CTRLA.bit.PRESCSYNC = PRESCSYNC_PRESC;

    TC2->COUNT16.WAVE.bit.WAVEGEN = WAVEGEN_NFRQ;

    TC2->COUNT16.CC[0].reg = TC_COUNT16_CC_CC(50);
    while(TC2->COUNT16.SYNCBUSY.bit.CC0)
    {
        /* Wait for sync */
    }

    ML_TC_CLR_INTFLAGS(TC2);

    //ML_TC_OVF_INTSET(TC1);
    //NVIC_EnableIRQ(TC1_IRQn);
    //NVIC_SetPriority(TC1_IRQn, 2);

    //ML_TC_OVF_CLR_INTFLAG(TC0);
}

void TC2_intset
(
    _Bool ovf, _Bool err, _Bool mc0, _Bool mc1, 
    _Bool nvic_enable, 
    const uint32_t nvic_prilvl
)
{
    TC2->COUNT16.INTENSET.bit.OVF = ovf;
    TC2->COUNT16.INTENSET.bit.ERR = err;
    TC2->COUNT16.INTENSET.bit.MC0 = mc0;
    TC2->COUNT16.INTENSET.bit.MC1 = mc1;

    if(nvic_enable)
    {
        NVIC_EnableIRQ(TC2_IRQn);
        NVIC_SetPriority(TC2_IRQn, nvic_prilvl);
    }
}

void TC2_intclr
(
    _Bool ovf, _Bool err, _Bool mc0, _Bool mc1,
    _Bool nvic_disable
)
{    
    TC2->COUNT16.INTENCLR.bit.OVF = ovf;
    TC2->COUNT16.INTENCLR.bit.ERR = err;
    TC2->COUNT16.INTENCLR.bit.MC0 = mc0;
    TC2->COUNT16.INTENCLR.bit.MC1 = mc1;

    if(nvic_disable)
    {
        NVIC_DisableIRQ(TC2_IRQn);
    }

}
