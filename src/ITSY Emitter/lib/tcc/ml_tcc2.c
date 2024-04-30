/*
 * Author: Ben Westcott
 * Date created: 12/31/23
 */

#include <ml_tcc_common.h>
#include <ml_tcc2.h>

/*
 * Typically I use TCC2 for the DAC timing
 * so it will be on GCLK4
 */
void TCC2_init(void)
{

    TCC_disable(TCC2);
    TCC_swrst(TCC2);

    TCC2->CTRLA.reg = 
    (
        TCC_CTRLA_PRESCALER_DIV2 |
        TCC_CTRLA_PRESCSYNC_PRESC
    );

    TCC2->WAVE.reg = TCC_WAVE_WAVEGEN_NFRQ;

    // 12 MHz / (2 * 6) = 1 MHz
    TCC_set_period(TCC2, 6);
    TCC_channel_capture_compare_set(TCC2, 0, 3);

}