/*
 * Author: Ben Westcott
 * Date created: 8/1/23
 */

#include <ml_adc_common.h>

void ADC_sync(Adc *instance) 
{ 
    while(instance->SYNCBUSY.reg); 
}

void ADC_enable(Adc *instance)
{
    instance->CTRLA.bit.ENABLE = 0x01;
    while(instance->SYNCBUSY.bit.ENABLE)
    {
        /* Wait for sync */
    }
}

void ADC_disable(Adc *instance)
{
    instance->CTRLA.bit.ENABLE = 0x00;
    while(instance->SYNCBUSY.bit.ENABLE)
    {
        /* Wait for sync */
    }       
}

void ADC_swrst(Adc *instance)
{
    instance->CTRLA.bit.SWRST = 0x01;
    while(instance->SYNCBUSY.bit.SWRST)
    {
        /* Wait for sync */
    }

}

void ADC_swtrig_start(Adc *instance)
{
    instance->SWTRIG.bit.START = 0x01;
    while(instance->SYNCBUSY.bit.SWTRIG)
    {
        /* Wait for sync */
    }
}

void ADC_flush(Adc *instance)
{
    instance->SWTRIG.bit.FLUSH = 0x01;
    while(instance->SYNCBUSY.bit.SWTRIG)
    {
        /* Wait for sync */
    }
}
