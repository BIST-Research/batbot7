/*
 * Author: Ben Westcott
 * Date created: 1/27/23
 */

#include <ml_clocks.h>

/*
 * Initializes the main clock, the clock used by the CPU.
 */
void MCLK_init(void)
{
  //DPLL1_init();                         

  // initial main clk division of 1
  MCLK->CPUDIV.reg = ML_MCLK_CPUDIV1;
  MCLK->AHBMASK.bit.DMAC_ = true;

  // set peripheral bus access, so we can access their registers in setup and main loop
  MCLK->APBAMASK.bit.TC0_ = true;
  MCLK->APBAMASK.bit.EIC_ = true;

  MCLK->APBBMASK.bit.TCC0_ = true;
  MCLK->APBBMASK.bit.TCC1_ = true;
  MCLK->APBBMASK.bit.TC2_ = true;
  MCLK->APBBMASK.bit.TC3_ = true;
  MCLK->APBBMASK.bit.EVSYS_ = true;
  MCLK->APBCMASK.bit.TCC2_ = true;
  MCLK->APBBMASK.bit.TC2_ = true;

  //MCLK->APBCMASK.bit.AC_ = true;
  //MCLK->APBCMASK.bit.CCL_ = true;

  MCLK->APBDMASK.bit.DAC_ = true;
  //MCLK->APBDMASK.bit.SERCOM5_ = true;

  //MCLK->APBDMASK.reg |= MCLK_APBDMASK_SERCOM4;

}


/*
 * Initializes digital phase locked loop 1. 
 * This is a clock generator which takes in a 32 kHz clock
 * And uses a phase locked loop and a frequency multiplier to 
 * Obtain the frequency we want. This clock signal is then fed to 
 * The generic clock controller 7 (GCLK7) to feed our peripherals.
 * 
 * We need to setup DPLL1 because we want to feed the analog to
 * digital converter (ADC0) with a specific clock frequency which
 * cannot be obtained with normal clock divisions.
 * 
 * f_dppln = f_ckr * (LDR + 1 + LDRFRAC/32)
 * 
 * where f_ckr = 32 kHz in our case 
 * (this is set by with OSCCTRL_DPLLCTRLB_REFCLK_XOSC32)
 * 
 * We want f_dpll1 = 104 MHz, so LDR = 3249 and LDRFRAC = 0
 * 
 */

#define DPLL1_INTEGER_MULTIPLICATION_VALUE (3249)

void DPLL1_init(void)
{

    OSCCTRL->Dpll[1].DPLLCTRLB.reg = OSCCTRL_DPLLCTRLB_REFCLK_XOSC32;

    OSCCTRL->Dpll[1].DPLLRATIO.reg = OSCCTRL_DPLLRATIO_LDR(DPLL1_INTEGER_MULTIPLICATION_VALUE);

    OSCCTRL->Dpll[1].DPLLCTRLA.bit.ENABLE = 0x1;

}

/*
 * Initializes the generic clock (GCLK7) to be used by peripherals (TCC, ADC, AC, etc)
 */
void GCLK_init(void)
{ 


  // GCLK divider, GCLK7_FREQ = ML_MCLK_UNDIV/(ML_MCLK_CPUDIV * ML_GCLK_GENCTRL_DIV) 
  // 50/50 duty 
  // Source multiplexer selects DPLL1
  // Output enable, Generator enable
  GCLK->GENCTRL[ML_GCLK_CH].reg = GCLK_GENCTRL_DIV(1) |                
                                  GCLK_GENCTRL_IDC |                  
                                  GCLK_GENCTRL_SRC_DPLL0 |             
                                  GCLK_GENCTRL_GENEN;

  // wait for GEN7 sync
  while(GCLK->SYNCBUSY.bit.GENCTRL7);

  ML_SET_GCLK4_PCHCTRL(DAC_GCLK_ID);
  ML_SET_GCLK4_PCHCTRL(TC2_GCLK_ID);
  ML_SET_GCLK4_PCHCTRL(TCC0_GCLK_ID);
  ML_SET_GCLK4_PCHCTRL(EIC_GCLK_ID);


  ML_SET_GCLK1_PCHCTRL(SERCOM5_GCLK_ID_CORE);

  ML_SET_GCLK7_PCHCTRL(ADC1_GCLK_ID);
  ML_SET_GCLK7_PCHCTRL(ADC0_GCLK_ID);
  ML_SET_GCLK7_PCHCTRL(TCC2_GCLK_ID);


  ML_SET_GCLK0_PCHCTRL(EVSYS_GCLK_ID_0);
  ML_SET_GCLK0_PCHCTRL(EVSYS_GCLK_ID_1);
  ML_SET_GCLK0_PCHCTRL(EVSYS_GCLK_ID_2);
  ML_SET_GCLK0_PCHCTRL(EVSYS_GCLK_ID_3);
  ML_SET_GCLK0_PCHCTRL(EVSYS_GCLK_ID_4);
  ML_SET_GCLK0_PCHCTRL(EVSYS_GCLK_ID_5);

  ML_SET_GCLK0_PCHCTRL(TC0_GCLK_ID);
  ML_SET_GCLK0_PCHCTRL(TC1_GCLK_ID);

}

void OSCULP32K_init(void)
{
  OSC32KCTRL->OSCULP32K.reg |= 
  (
    OSC32KCTRL_OSCULP32K_EN1K |
    OSC32KCTRL_OSCULP32K_EN32K |
    OSC32KCTRL_OSCULP32K_WRTLOCK
  );
}


