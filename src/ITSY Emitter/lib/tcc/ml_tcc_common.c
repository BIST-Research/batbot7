/*
 * Author: Ben Westcott
 * Date created: 3/8/23
 */
#include <ml_tcc_common.h>

void TCC_enable(Tcc *instance)
{
  instance->CTRLA.bit.ENABLE = 0x01;
  while(instance->SYNCBUSY.bit.ENABLE)
  {
    /* Wait for sync */
  }
}

void TCC_disable(Tcc *instance)
{
  instance->CTRLA.bit.ENABLE = 0x00;
  while(instance->SYNCBUSY.bit.ENABLE)
  {
    /* Wait for sync */
  }
}

void TCC_swrst(Tcc *instance)
{
  instance->CTRLA.bit.SWRST = 0x01;
  while(instance->SYNCBUSY.bit.SWRST)
  {
    /* Wait for sync */
  }
}

void TCC_sync(Tcc *instance)
{
    while(instance->SYNCBUSY.reg);
}

// TCC_PER_PER.reg holds 18 bit period value!
void TCC_set_period(Tcc *instance, uint32_t value)
{
    instance->PER.reg = TCC_PER_PER(value);
    while(instance->SYNCBUSY.bit.PER)
    {
       /* Wait for sync */
    }
}

void TCC_channel_capture_compare_set(Tcc *instance, const uint8_t channel, const uint8_t value)
{
    instance->CC[channel].reg = TCC_CC_CC(value);
    while(instance->SYNCBUSY.reg)
    {
       /* Wait for sync */
    }
}

void TCC_set_oneshot(Tcc *instance)
{
  instance->CTRLBSET.bit.ONESHOT = 0x01;
  while(instance->SYNCBUSY.bit.CTRLB)
  {
    /* Wait for sync */
  }
}

void TCC_clr_oneshot(Tcc *instance)
{
  instance->CTRLBCLR.bit.ONESHOT = 0x01;
  while(instance->SYNCBUSY.bit.CTRLB)
  {
    /* Wait for sync */
  }
}

void TCC_force_stop(Tcc *instance)
{
  instance->CTRLBSET.bit.CMD = TCC_CTRLBSET_CMD_STOP_Val;
  while(instance->SYNCBUSY.bit.CTRLB)
  {
    /* Wait for sync */
  }
}

void TCC_update_period(Tcc *instance, uint16_t val)
{
  instance->PERBUF.bit.PERBUF = val;
}

void TCC_lock_update(Tcc *instance)
{
  instance->CTRLBSET.bit.LUPD = 0x01;
  while(instance->SYNCBUSY.bit.CTRLB)
  {
    /* Wait for sync */
  }
}

void TCC_unlock_update(Tcc *instance)
{
  instance->CTRLBCLR.bit.LUPD = 0x01;
  while(instance->SYNCBUSY.bit.CTRLB)
  {
    /* Wait for sync */
  }

}

void TCC_force_retrigger(Tcc *instance)
{
  instance->CTRLBSET.bit.CMD = TCC_CTRLBSET_CMD_RETRIGGER_Val;
  while(instance->SYNCBUSY.bit.CTRLB)
  {
    /* Wait for sync */
  }
}

// TCC cant be enabled!
void TCC_update_prescaler(Tcc *instance, uint8_t prescaler)
{
  instance->CTRLA.bit.PRESCALER = (uint32_t)prescaler;
  while(instance->SYNCBUSY.reg)
  {
    /* Wait for sync */
  }
}

void TCC_intenset(Tcc *instance, const IRQn_Type IRQn, const uint8_t interrupt_mask, const uint32_t priority_level)
{

    TCC2->INTENSET.reg |= interrupt_mask;

    NVIC_SetPriority(IRQn, priority_level);

    NVIC_EnableIRQ(IRQn);

}

void TCC0_DT_set(uint8_t dth, uint8_t dtl)
{
  TCC0->WEXCTRL.reg |= (TCC_WEXCTRL_DTIEN0 | TCC_WEXCTRL_DTLS(dtl) | TCC_WEXCTRL_DTHS(dth));
}

// mode: 4, 5, 6
void TCC0_DITH_set(uint8_t mode, uint64_t cycles, uint64_t period, uint64_t compare)
{

  uint64_t CTRLA_res_msk;
  uint64_t PER_DITH_msk, CC_DITH_msk;
  switch(mode){
    case 5: {
      CTRLA_res_msk = TCC_CTRLA_RESOLUTION_DITH5;
      PER_DITH_msk = TCC_PER_DITH5_PER(period) | TCC_PER_DITH5_DITHER(cycles);
      CC_DITH_msk = TCC_CC_DITH5_CC(compare) | TCC_CC_DITH5_DITHER(cycles);
      break;
    }

    case 6: {
      CTRLA_res_msk = TCC_CTRLA_RESOLUTION_DITH6;
      PER_DITH_msk = TCC_PER_DITH6_PER(period) | TCC_PER_DITH6_DITHER(cycles);
      CC_DITH_msk = TCC_CC_DITH6_CC(compare) | TCC_CC_DITH6_DITHER(cycles);
      break;
    }

    default: {
      CTRLA_res_msk = TCC_CTRLA_RESOLUTION_DITH4;
      PER_DITH_msk = TCC_PER_DITH4_PER(period) | TCC_PER_DITH4_DITHER(cycles);
      CC_DITH_msk = TCC_CC_DITH4_CC(compare) | TCC_CC_DITH4_DITHER(cycles);
      break;
    }
  }

  TCC0->CTRLA.reg |= CTRLA_res_msk;

  TCC0->PER.reg = PER_DITH_msk;
  //TCC_sync(TCC0);

  TCC0->CC[0].reg = CC_DITH_msk;
  TCC0->CC[0].reg = CC_DITH_msk;
  TCC_sync(TCC0);
}

void TCC0_init_alt(void)
{
      
  // disable TCC
  TCC_DISABLE(TCC0);
  TCC_sync(TCC0);
  
  // send software reset of TCC CTRLA.SWRST
  TCC_SWRST(TCC0);
  TCC_sync(TCC0);

  /*
  * Syncronization:
  * 
  * bits SYNCED on write: CTRLA.SWRST, CTRLA.ENABLE
  * regs SYNCED on write: CTRLBCLR, CTRLBSET, STATUS, WAVE, COUNT, PER/PERBUF, CCx/CCBUFx
  * regs SYNCED on read: CTRLBCLR, CTRLBSET, COUNT, WAVE, PER/PERBUF, CCx/CCBUFx
  */

  // DMA channel match request: set CTRLA.DMAOS=0
  
  // Sleep mode: CTRLA.RUNSTDBY
  // set prescalar, and prescalar sync
  // STOP cmd: CTRLB.CMD=0x2
  // PAUSE event: EVCTRL.EVACT1=0x3, STOP, EVCTRL.EVACT0=0x3, START
  // EVENT ACTIONS**
  TCC0->CTRLA.reg = TCC_CTRLA_PRESCALER_DIV1 |
                    TCC_CTRLA_PRESCSYNC_PRESC;                         // try TC_CTRLA_PRESYNC_GCLK or TC_CTRLA_PRESYNC_RESYNC
   //               TCC_CTRLA_DMAOS;     
   //               TCC_CTRLA_RESOLUTION_DITH4 |                           // enable dithering every 16 PWM frames
   //               TCC_CTRLA_RUNSTDBY;                                    // run TCC when MP in standby
   
  // TCC0->CTRLA.reg &= ~TCC_CTRLA_DMAOS;
  // dead time reg
  /*
  TCC0->WEXCTRL.reg = TCC_WEXCTRL_DTIEN0       |                         // DT insertion gen 0 enable
                      TCC_WEXCTRL_DTHS(0x1)      |                       // DT high side value set
                      TCC_WEXCTRL_DTLS(0x1)      |                       // DT low side value set
  //                  TCC_WEXCTRL_OTMX(0x0);                             // default output matrix config 
  */
  
  /*
  * Interrupts
  * 
  * Enable in INTENSET reg
  * Disable in INTENCLR reg
  * Status/CLR: INTFLAG reg
  * 
  * counter val continuously compared to each CC channel. When match, INTFLAG.MCx is set
  */
  /*
  TCC0->INTENSET.reg = TCC_INTENSET_OVF |                               // overflow fault
                    TCC_INTENSET_TRG |                                  // retigger
                    TCC_INTENSET_CNT |                                  // counter
                    TCC_INTENSET_ERR |                                  // error
                    TCC_INTENSET_UFS |                                  // non-recoverable update fault
                    TCC_INTENSET_FAULTA |                               // recoverable fault A/B
                    TCC_INTENSET_FAULTB |                      
                    TCC_INTENSET_FAULT0 |                               // non-recoverable fault 0/1
                    TCC_INTENSET_FAULT1 |  
                    TCC_INTENSET_MC(0)  |                               // Match or capture channel x
  */

  //TCC0->INTENSET.reg = TCC_INTENSET_OVF;
  // NVIC_EnableIRQ(TCC0_0_IRQn);
  // NVIC_SetPriority(TCC0_0_IRQn, 0);

  
  // TCCO->INTFLAG.reg                                                  // for reading interrupt status (pg 1866)
  // TCC0->STATUS.reg                                                   // reading tcc status (pg 1868)
  // TCC0->COUNT.reg                                                    // reading counter value, set CTRLBSET.CMD=READSYNC prior to read
                                                  
  
  // waveform generation option: WAVE.WAVEGEN
  // waveform output polarity WAVE.POL
  // RAMP operation: consider ramp2, CTRLBSET.IDXCMD
  // Count direction: CTRLB.DIR, When count reaches TOP or ZERO, INTFLAG.OVF set
  // waveform inversion: DRVCTRL.INVEN
  // sync required on read and write**
  /*
  * Single slope PWM:
  * 
  * R_PWM = log(TOP + 1)/log(2)
  * f_pwm = f_GCLK/(N*(TOP+1)), N is prescalar
  * 
  */
  TCC0->WAVE.reg = TCC_WAVE_WAVEGEN_NFRQ |                             // normal frequency operation
                   TCC_WAVE_RAMP_RAMP2   |                              // ramp 2 operation
                   TCC_WAVE_POL0 | TCC_WAVE_POL1;           
                                             // channel x polarity set


  
  //TCC_sync(TCC0);
  
  
  // period reg
  TCC_set_period(TCC0, 30);                                     // period value set
  //              TCC_PER_DITH4_DITHER(1) |                             // dithering cycle number
  //              TCC_PER_DITH4_PER(1)    |                             // period value set (if dithering enabled)

  //TCC_sync(TCC0);
  
  // period buffer reg
  // sync required on read and write
  /*
  TCC0->PERBUF.reg = TCC_PERBUF_PERBUF(1);                              // value copied to PER on UPDATE condition
  //                 TCC_PERBUF_DITH4_DITHERBUF(1) |                    // dithering buffer update bits
  //                 TCC_PERBUF_DITH4_PERBUF(1)    |                    // period update if dithering enabled
  while(TCC00>SYNCBUSY.bit.PERBUF);
  */
  
  // capture compare reg
  // sync require on read and write
  
  //TCC0->CC[ML_TCC0_CH0].reg = TCC_CC_CC(50);                             // CC value (18 bits)
  //              TCC_CC_DITH4_DITHER(1)                                // dithering cycle number
  //              TCC_CC_DITH4_CC(1)                                    // CC value (if dithering enabled)

  //TCC0->CC[ML_TCC0_CH1].reg = TCC_CC_CC(50);

  //TCC_sync(TCC0);

  //TCC0_PORT_init();
  
  // TCC0->DRVCTRL.reg |= TCC_DRVCTRL_INVEN1;                              // inverts ch3 wave, we want complimentary outs
  
  // Channel x CC buffer value regs: CCBUFx (force update w/ CTRLBSET.CMD=0x3)
  // capture compare buffer reg TCC0->CCBUF.reg, similar to PERBUF (pg 1882), NEEDS to wait for SYNC on read and write*                                                              
}

/*
void TCC1_init(void)
{

  //ML_SET_GCLK7_PCHCTRL(TCC1_GCLK_ID);

  // disable TCC
  TCC_DISABLE(TCC1);
  TCC_sync(TCC1);
  // send software reset of TCC CTRLA.SWRST
  TCC_SWRST(TCC1);
  TCC_sync(TCC1);
  
  TCC1->CTRLA.reg = TCC_CTRLA_PRESCALER_DIV1 |
                    TCC_CTRLA_PRESCSYNC_PRESC;                         
   
  // When one-shot mode set to 0, TCC will generate DMA request on OVF trigger
  TCC1->CTRLA.reg &= ~TCC_CTRLA_DMAOS;
                                    

  TCC1->WAVE.reg = TCC_WAVE_WAVEGEN_NPWM;                      
  //TCC_sync(TCC1);
  
  
  // period reg
  // We want a full duty cycle range out of ch3 from values given from DMA
  // Thus, make the TCC period = the maximum amplitude of the wavetable which is 0xff
  // TCC1->PER.reg = TCC_PER_PER(ML_TCC1_CH3_INITIAL_PER);   
  TCC_set_period(TCC1, 1200);

  TCC1->CTRLA.bit.DMAOS = 0x0;

  //TCC1->CTRLBSET.bit.ONESHOT = 0x1;
  //TCC_sync(TCC1);
  
  
  // start timer @ 50% duty cycle which would mean counting to half the period
  // TCC1->CC[ML_TCC1_CH3].reg = TCC_CC_CC((unsigned)(ML_TCC1_CH3_INITIAL_PER / 2));
  //TCC1->CC[ML_TCC1_CH3].reg = TCC_CC_CC(128);

  //TCC1->CC[0].reg = TCC_CC_CC(128);
  //TCC_sync(TCC1);

  //TCC1_PORT_init();

   //TCC1->INTENSET.reg = TCC_INTENSET_OVF;
  // NVIC_EnableIRQ(TCC1_0_IRQn);
   //NVIC_SetPriority(TCC1_0_IRQn, 0);

  // TCC0->DRVCTRL.reg |= TCC_DRVCTRL_INVEN1;   
}*/