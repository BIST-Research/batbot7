/*
 * Author: Ben Westcott
 * Date created: 8/24/23
 */
#include <ml_tc0.h>
#include <ml_tc_common.h>

void TC1_init(void)
{
    TC_disable(TC1);
    TC_swrst(TC1);

    TC1->COUNT16.CTRLA.bit.PRESCALER = PRESCALER_DIV2;
    TC1->COUNT16.CTRLA.bit.MODE = MODE_COUNT16;
    TC1->COUNT16.CTRLA.bit.PRESCSYNC = PRESCSYNC_PRESC;

    TC1->COUNT16.WAVE.bit.WAVEGEN = WAVEGEN_MFRQ;

    TC1->COUNT16.CC[0].reg = TC_COUNT16_CC_CC(50);
    while(TC1->COUNT16.SYNCBUSY.bit.CC0)
    {
        /* Wait for sync */
    }

    TC1->COUNT16.CC[1].reg = TC_COUNT16_CC_CC(50);
    while(TC1->COUNT16.SYNCBUSY.bit.CC1)
    {
        /* Wait for sync */
    }

    TC_set_oneshot(TC1);

    ML_TC_CLR_INTFLAGS(TC1);

    //ML_TC_OVF_INTSET(TC1);
    //NVIC_EnableIRQ(TC1_IRQn);
    //NVIC_SetPriority(TC1_IRQn, 2);

    //ML_TC_OVF_CLR_INTFLAG(TC0);
}

/*
 * IBM4:
 * A5 --> PA06 --> TC0[CC0]
 * 
 */
/*const ml_pin_settings tc1_cc0_pin = 
{
    PORT_GRP_A, 6, PF_E, PP_EVEN, OUTPUT_PULL_DOWN, DRIVE_ON
};

void TC1_CC0_pinout(void)
{
    peripheral_port_init(&tc1_cc0_pin);
}*/

void TC1_intset
(
    _Bool ovf, _Bool err, _Bool mc0, _Bool mc1, 
    _Bool nvic_enable, 
    const uint32_t nvic_prilvl
)
{
    TC1->COUNT16.INTENSET.bit.OVF = ovf;
    TC1->COUNT16.INTENSET.bit.ERR = err;
    TC1->COUNT16.INTENSET.bit.MC0 = mc0;
    TC1->COUNT16.INTENSET.bit.MC1 = mc1;

    if(nvic_enable)
    {
        NVIC_EnableIRQ(TC1_IRQn);
        NVIC_SetPriority(TC1_IRQn, nvic_prilvl);
    }
}

void TC1_intclr
(
    _Bool ovf, _Bool err, _Bool mc0, _Bool mc1,
    _Bool nvic_disable
)
{    
    TC1->COUNT16.INTENCLR.bit.OVF = ovf;
    TC1->COUNT16.INTENCLR.bit.ERR = err;
    TC1->COUNT16.INTENCLR.bit.MC0 = mc0;
    TC1->COUNT16.INTENCLR.bit.MC1 = mc1;

    if(nvic_disable)
    {
        NVIC_DisableIRQ(TC1_IRQn);
    }

}
