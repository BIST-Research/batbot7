/*
 * Author: Ben Westcott
 * Date created: 12/20/23
 */

// Currently just holds the setup function for sonar mics

#ifndef ML_ADC0_H
#define ML_ADC0_H

#include <Arduino.h>

#ifdef __cplusplus
extern "C"
{
#endif

void ADC0_init(void);

#ifdef __cplusplus
}
#endif

#endif // ML_ADC0_H