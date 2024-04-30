/*
 * Author: Ben Westcott
 * Date created: 7/31/23
 */

#ifndef ML_EIC_H
#define ML_EIC_H

#include <Arduino.h>

#ifdef __cplusplus
extern "C"
{
#endif

const extern void EIC0_callback(void);
const extern void EIC1_callback(void);

void eic_init();
void eic_enable(void);
void eic_swrst(void);
void eic_disable(void);

void both_edge_int_init(void);
void rise_edge_int_init(void);

#define ML_EIC_CLR_INTFLAG(channel) (EIC->INTFLAG.reg |= EIC_INTFLAG_EXTINT(channel))
#define ML_EIC_DEBOUNCEN(channel) (EIC->DEBOUNCEN.reg |= (1 << EIC_DEBOUNCEN_DEBOUNCEN(channel)))
#define ML_EIC_INTSET(channel) (EIC->INTENSET.reg |= (1 << EIC_INTENSET_EXTINT(channel)))
#define ML_EIC_CLR_INTFLAG(channel) (EIC->INTFLAG.reg |= (1 << EIC_INTFLAG_EXTINT(channel)))

#ifdef __cplusplus
}
#endif

#endif // ML_EIC_H