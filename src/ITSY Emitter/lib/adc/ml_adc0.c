/*
 * Author: Ben Westcott
 * Date created: 12/20/23
 */

#include <ml_adc0.h>
#include <ml_adc_common.h>

/*
const uint32_t refbuf = PASTE_FUSE(ADC0_FUSES_BIASREFBUF);
const uint32_t r2r = PASTE_FUSE(ADC0_FUSES_BIASR2R);
const uint32_t comp = PASTE_FUSE(ADC0_FUSES_BIASCOMP);
*/

void ADC0_init(void)
{

  ADC_disable(ADC0);
  ADC_swrst(ADC0);

  /*ADC0->CALIB.reg = 
  (
    ADC0_FUSES_BIASREFBUF(refbuf) |
    ADC0_FUSES_BIASCOMP(comp) |
    ADC0_FUSES_BIASR2R(r2r)
  );*/

  ADC0->CTRLA.reg |= ADC_CTRLA_PRESCALER_DIV8;

 
  ADC0->SAMPCTRL.reg |= ADC_SAMPCTRL_SAMPLEN(3U - 1);
  while(ADC0->SYNCBUSY.bit.SAMPCTRL)
  {
    /* Wait for sync */
  }   

  ADC0->REFCTRL.reg |= ADC_REFCTRL_REFSEL_INTVCC1;
  while(ADC0->SYNCBUSY.bit.REFCTRL)
  {
    /* Wait for sync */
  }

  ADC0->INPUTCTRL.reg = 
  (
    ADC_INPUTCTRL_MUXPOS_AIN2 |
    ADC_INPUTCTRL_MUXNEG_GND
  );
  while(ADC0->SYNCBUSY.bit.INPUTCTRL)
  {
    /* Wait for sync */
  }

  ADC0->CTRLB.reg =
  (
    ADC_CTRLB_RESSEL_12BIT |
    ADC_CTRLB_WINMODE(0U) |
    ADC_CTRLB_FREERUN
  );
  while(ADC0->SYNCBUSY.bit.CTRLB)
  {
    /* Wait for sync */
  }

  ML_ADC_CLR_INTFLAGS(ADC0);

  ML_ADC_WINMON_INTSET(ADC0);
  ML_ADC_OVERRUN_INTSET(ADC0);
  ML_ADC_RESRDY_INTSET(ADC0);
}