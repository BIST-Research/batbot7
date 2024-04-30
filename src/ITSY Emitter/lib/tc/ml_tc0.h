/*
 * Author: Ben Westcott
 * Date created: 8/18/23
 */

#ifndef ML_TC0_H
#define ML_TC0_H

#include <Arduino.h>

#ifdef __cplusplus
extern "C"
{
#endif

void TC0_init(void);

void TC0_CC0_pinout(void);

void TC0_intset
(
    _Bool ovf, _Bool err, _Bool mc0, _Bool mc1, 
    _Bool nvic_enable, 
    const uint32_t nvic_prilvl
);

void TC0_intclr
(
    _Bool ovf, _Bool err, _Bool mc0, _Bool mc1,
    _Bool nvic_disable
);


#ifdef __cplusplus
}
#endif

#endif // ML_TC0_H