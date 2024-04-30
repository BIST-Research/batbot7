/*
 * Author: Ben Westcott
 * Date created: 12/21/23
 */

#include <ml_tcc0.h>
#include <ml_tcc_common.h>

void TCC0_init(void)
{
  // 120 MHz

  TCC_disable(TCC0);
  TCC_swrst(TCC0);

  TCC0->CTRLA.reg = 
  (
    TCC_CTRLA_PRESCALER_DIV256 |
    TCC_CTRLA_PRESCSYNC_PRESC
  );

  TCC0->WAVE.reg = TCC_WAVE_WAVEGEN_NFRQ;

  // 120 MHz / (2 * 60) = 1 MHz
  TCC_set_period(TCC0, 60);

  //  D = 0.50
  //TCC_channel_capture_compare_set(TCC0, 1, 30);
}