/*
 * Author: Ben Westcott
 * Date created: 12/22/23
 */

#include <ml_tcc1.h>
#include <ml_tcc_common.h>

void TCC1_init(void)
{

    TCC_disable(TCC1);
    TCC_swrst(TCC1);

    TCC1->CTRLA.reg =
    (
        TCC_CTRLA_PRESCALER_DIV256 |
        TCC_CTRLA_PRESCSYNC_PRESC
    );

    TCC1->WAVE.reg = TCC_WAVE_WAVEGEN_NFRQ;

    TCC1->PER.reg = 60000;
    TCC1->CC[1].reg = 30000;

    //TCC_set_oneshot(TCC1);

    //TCC1->INTENSET.bit.MC1 = 0x01;
    //TCC1->INTENSET.bit.OVF = 0x01;
    TCC1->INTENSET.bit.MC0 = 0x01;
    NVIC_EnableIRQ(TCC1_1_IRQn);
    NVIC_SetPriority(TCC1_1_IRQn, 1);

}