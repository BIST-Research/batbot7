/*
 * Author: Ben Westcott
 * Date created: 12/20/23
 */

#include <ml_adc1.h>
#include <ml_adc_common.h>

void ADC1_init(void)
{

  ADC_disable(ADC1);
  ADC_swrst(ADC1);
  /*
  ADC1->CALIB.reg = 
  (
    ADC1_FUSES_BIASREFBUF(refbuf) |
    ADC1_FUSES_BIASCOMP(comp) |
    ADC1_FUSES_BIASR2R(r2r)
  );*/

  ADC1->CTRLA.reg |= ADC_CTRLA_PRESCALER_DIV8;

  ADC1->SAMPCTRL.reg |= ADC_SAMPCTRL_SAMPLEN(3U - 1);
  while(ADC1->SYNCBUSY.bit.SAMPCTRL)
  {
    /* Wait for sync */
  }   

  ADC1->REFCTRL.reg |= ADC_REFCTRL_REFSEL_INTVCC1;
  while(ADC1->SYNCBUSY.bit.REFCTRL)
  {
    /* Wait for sync */
  }

  ADC1->INPUTCTRL.reg = 
  (
    ADC_INPUTCTRL_MUXPOS_AIN1 |
    ADC_INPUTCTRL_MUXNEG_GND
  );
  while(ADC1->SYNCBUSY.bit.INPUTCTRL)
  {
    /* Wait for sync */
  }

  ADC1->CTRLB.reg =
  (
    ADC_CTRLB_RESSEL_12BIT |
    ADC_CTRLB_WINMODE(0U) |
    ADC_CTRLB_FREERUN
  );
  while(ADC1->SYNCBUSY.bit.CTRLB)
  {
    /* Wait for sync */
  }

  ML_ADC_CLR_INTFLAGS(ADC1);
  
  ML_ADC_WINMON_INTSET(ADC1);
  ML_ADC_OVERRUN_INTSET(ADC1);
  ML_ADC_RESRDY_INTSET(ADC1);

}