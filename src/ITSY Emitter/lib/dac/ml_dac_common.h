/*
 * Author: Ben Westcott
 * Date created: 8/24/23
 */

#ifndef ML_DAC_COMMON_H
#define ML_DAC_COMMON_H

#include <Arduino.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C"
{
#endif

#define ML_DAC_REFSEL_VREFAU            0x00
#define ML_DAC_REFSEL_VDDANA            0x01
#define ML_DAC_REFSEL_VREFAB            0x02
#define ML_DAC_REFSEL_INTREF            0x03

typedef enum _ml_dac_refsel_t 
{
    VREF_VREFAU = ML_DAC_REFSEL_VREFAU,
    VREF_VDDANA = ML_DAC_REFSEL_VDDANA,
    VREF_VREFAB = ML_DAC_REFSEL_VREFAB,
    VREF_INTREF = ML_DAC_REFSEL_INTREF
} ml_dac_refsel_t;

#define ML_DAC_SET_REFSEL(set)          (DAC->CTRLB.bit.REFSEL = set)
#define ML_DAC_SET_DIFFMODE()           (DAC->CTRLB.bit.DIFF = 0x01)
#define ML_DAC_UNSET_DIFFMODE()         (DAC->CTRLB.bit.DIFF = 0x00)

#define ML_DAC_OSR1                     0x00
#define ML_DAC_OSR2                     0x01
#define ML_DAC_OSR4                     0x02
#define ML_DAC_OSR8                     0x03
#define ML_DAC_OSR16                    0x04
#define ML_DAC_OSR32                    0x05

typedef enum _ml_dac_osr_t
{
    OSR1 = ML_DAC_OSR1,
    OSR2 = ML_DAC_OSR2,
    OSR4 = ML_DAC_OSR4,
    OSR8 = ML_DAC_OSR8,
    OSR16 = ML_DAC_OSR16,
    OSR32 = ML_DAC_OSR32
} ml_dac_osr_t;

#define ML_DAC_GET_REFRESH_VALUE(period)        (period/30E-6)

// GCLK_DAC <= 1.2 MHz (100 kSPS)
#define ML_DAC_CCTRL_CC100K             0x00
// 1.2 MHz < GCLK_DAC <= 6 MHz (500 kSPS)
#define ML_DAC_CCTRL_CC1MEG             0x01
// 6 MHz < GCLK_DAC <= 12 MHz (1 MSPS)
#define ML_DAC_CCTRL_CC12MEG            0x02

typedef enum _ml_dac_cctrl_t
{
    CC100K = ML_DAC_CCTRL_CC100K,
    CC1MEG = ML_DAC_CCTRL_CC1MEG,
    CC12MEG = ML_DAC_CCTRL_CC12MEG
} ml_dac_cctrl_t;

void DAC_enable(void);
void DAC_disable(void);
void DAC_swrst(void);
void DAC_init(void);

#ifdef __cplusplus
}
#endif

#endif // ML_DAC_H