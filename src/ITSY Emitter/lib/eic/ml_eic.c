/*
 * Author: Ben Westcott
 * Date created: 7/31/23
 */

#include <ml_eic.h>

#define EIC_CHANNELS_PER_REG 7

void eic_init(void)
{
    //ML_SET_GCLK7_PCHCTRL(EIC_GCLK_ID);

    EIC->CTRLA.reg &= ~EIC_CTRLA_ENABLE;
    EIC->CTRLA.reg |= EIC_CTRLA_SWRST;
    while(EIC->SYNCBUSY.bit.ENABLE & EIC->SYNCBUSY.bit.SWRST);

    // CLK_ULP32K = 0x1, else GCLK
    // EIC->CTRLA.reg |= EIC_CTRLA_CKSEL;
    // EIC->CTRLA.reg = 0;

    // Set all EXTINTs to trigger syncrhonously
    // I believe this is default, i.e., this register is 
    // initialized to a value of 0x0
    // EIC->ASYNCH.reg &= ~EIC_ASYNCH_ASYNCH(0);
    
}

void eic_enable(void)
{
    EIC->CTRLA.bit.ENABLE = 0x01;
    while(EIC->SYNCBUSY.bit.ENABLE);
}

void eic_swrst(void)
{
    EIC->CTRLA.bit.SWRST = 0x01;
    while(EIC->SYNCBUSY.bit.SWRST)
    {
        /* Wait for sync */
    }
}

void eic_disable(void)
{
    EIC->CTRLA.bit.ENABLE = 0x01;
    while(EIC->SYNCBUSY.bit.ENABLE)
    {
        /* Wait for sync */
    }
}


/*
 * PA16 --> EXTINT[0]
 *   - IB: D0
 *   - GC: D37
 */
/*
 * PA02 --> EXTINT[2]
 *   - IB: A0
 *   - GC: A0
 */
/*const ml_pin_settings ml_hardware_int_pin = 
{
    PORT_GRP_A, 2, PF_A, PP_EVEN, INPUT_PULL_DOWN, DRIVE_OFF
};*/

void rise_edge_int_init(void)
{
    // Rising edge detection
    EIC->CONFIG[0].bit.SENSE0 = EIC_CONFIG_SENSE0_RISE_Val;
    // Take multiple samples
    // Disabled because we will debounce the input
    //EIC->CONFIG[0].bit.FILTEN0 = 0x01;
    
    ML_EIC_DEBOUNCEN(0);
    ML_EIC_INTSET(0);

    NVIC_EnableIRQ(EIC_0_IRQn);
    NVIC_SetPriority(EIC_0_IRQn, 0);

    //peripheral_port_init(&ml_hardware_int_pin);
}

void both_edge_int_init(void)
{
    EIC->CONFIG[0].bit.SENSE1 = EIC_CONFIG_SENSE1_BOTH_Val;
    ML_EIC_INTSET(0);
    
    NVIC_EnableIRQ(EIC_1_IRQn);
    NVIC_SetPriority(EIC_1_IRQn, 0);
}

/*
void EIC_0_Handler(void)
{
    ML_EIC_CLR_INTFLAG(0);
    EIC0_callback();
}

void EIC_1_Handler(void)
{
    ML_EIC_CLR_INTFLAG(1);
    EIC1_callback();
}
*/



