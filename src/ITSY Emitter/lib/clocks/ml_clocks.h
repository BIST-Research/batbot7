/*
 * Author: Ben Westcott
 * Date created: 1/27/23
 */

#ifndef ML_CLOCKS_H
#define ML_CLOCKS_H

#include <Arduino.h>

#ifdef __cplusplus
extern "C"
{
#endif

#define ML_MCLK_UNDIV 120000000
#define ML_MCLK_CPUDIV1 (MCLK_CPUDIV_DIV(MCLK_CPUDIV_DIV_DIV1_Val))

void MCLK_init(void);

/*
        GCLK definitions
*/

#define ML_GCLK_CH 7

// Channel enable, GCLK7, WRTLCK - disable future writing to reg
#define ML_GCLK7_PCHCTRL (GCLK_PCHCTRL_CHEN | GCLK_PCHCTRL_GEN_GCLK7 )
// 48 MHz
#define ML_GCLK1_PCHCTRL (GCLK_PCHCTRL_CHEN | GCLK_PCHCTRL_GEN_GCLK1)
// 120 MHz
#define ML_GCLK0_PCHCTRL (GCLK_PCHCTRL_CHEN | GCLK_PCHCTRL_GEN_GCLK0)
// 12 MHz
#define ML_GCLK4_PCHCTRL (GCLK_PCHCTRL_CHEN | GCLK_PCHCTRL_GEN_GCLK4)
// 100 MHz
#define ML_GCLK2_PCHCTRL (GCLK_PCHCTRL_CHEN | GCLK_PCHCTRL_GEN_GCLK2)

#define ML_SET_GCLK2_PCHCTRL(id)(GCLK->PCHCTRL[id].reg = ML_GCLK2_PCHCTRL)
#define ML_SET_GCLK7_PCHCTRL(id)(GCLK->PCHCTRL[id].reg = ML_GCLK7_PCHCTRL)
#define ML_SET_GCLK1_PCHCTRL(id)(GCLK->PCHCTRL[id].reg = ML_GCLK1_PCHCTRL)
#define ML_SET_GCLK0_PCHCTRL(id)(GCLK->PCHCTRL[id].reg = ML_GCLK0_PCHCTRL)
#define ML_SET_GCLK4_PCHCTRL(id)(GCLK->PCHCTRL[id].reg = ML_GCLK4_PCHCTRL)

void GCLK_init(void);

void OSCULP32K_init(void);

#ifdef __cplusplus
}
#endif

#endif