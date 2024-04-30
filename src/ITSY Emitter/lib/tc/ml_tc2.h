/*
 * Author: Ben Westcott
 * Date created: 4/7/24
 */

#ifndef ML_TC1_H
#define ML_TC1_H

#include <Arduino.h>

#ifdef __cplusplus
extern "C"
{
#endif

void TC2_init(void);

void TC2_intset
(
    _Bool ovf, _Bool err, _Bool mc0, _Bool mc1, 
    _Bool nvic_enable, 
    const uint32_t nvic_prilvl
);

void TC2_intclr
(
    _Bool ovf, _Bool err, _Bool mc0, _Bool mc1,
    _Bool nvic_disable
);


#ifdef __cplusplus
}
#endif

#endif // ML_TC1_H