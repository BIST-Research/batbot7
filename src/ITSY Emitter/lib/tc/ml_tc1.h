/*
 * Author: Ben Westcott
 * Date created: 8/24/23
 */

#ifndef ML_TC1_H
#define ML_TC1_H

#include <Arduino.h>

#ifdef __cplusplus
extern "C"
{
#endif

void TC1_init(void);

void TC1_CC0_pinout(void);

void TC1_intset
(
    _Bool ovf, _Bool err, _Bool mc0, _Bool mc1, 
    _Bool nvic_enable, 
    const uint32_t nvic_prilvl
);

void TC1_intclr
(
    _Bool ovf, _Bool err, _Bool mc0, _Bool mc1,
    _Bool nvic_disable
);


#ifdef __cplusplus
}
#endif

#endif // ML_TC1_H