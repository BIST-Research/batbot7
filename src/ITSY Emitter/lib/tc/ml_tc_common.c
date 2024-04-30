/*
 * Author: Jayson De La Vega, Ben Westcott
 * Date created: 8/3/23
 */
#include <ml_tc_common.h>

void TC_enable(Tc *instance)
{
    instance->COUNT16.CTRLA.bit.ENABLE = 0x01;
    while(instance->COUNT16.SYNCBUSY.bit.ENABLE)
    {
        /* wait for sync */
    }
}

void TC_disable(Tc *instance)
{
    instance->COUNT16.CTRLA.bit.ENABLE = 0x00;
    while(instance->COUNT16.SYNCBUSY.bit.ENABLE)
    {
        /* wait for sync */
    }
}

void TC_swrst(Tc *instance)
{
    instance->COUNT16.CTRLA.bit.SWRST = 0x01;
    while(instance->COUNT16.SYNCBUSY.bit.SWRST)
    {
        /* wait for sync */
    }
}

void TC_channel_capture_compare_set
(
    Tc *instance, 
    const ml_tc_cc_t channel, 
    const uint8_t ccval
)
{
    instance->COUNT16.CCBUF[channel].reg |= TC_COUNT16_CCBUF_CCBUF(ccval);
    while(instance->COUNT16.SYNCBUSY.bit.CC0 | instance->COUNT16.SYNCBUSY.bit.CC1)
    {
        /* wait for sync */
    }

}

void TC_set_oneshot(Tc *instance)
{
    instance->COUNT16.CTRLBSET.bit.ONESHOT = true;
    while(instance->COUNT16.SYNCBUSY.bit.CTRLB)
    {
        /* wait for sync */
    }

}

void TC_force_stop(Tc *instance)
{
    instance->COUNT16.CTRLBSET.bit.CMD = CMD_STOP;
    while(instance->COUNT16.SYNCBUSY.bit.CTRLB)
    {
        /* wait for sync */
    }
}

void TC_force_retrigger(Tc *instance)
{
    instance->COUNT16.CTRLBSET.bit.CMD = CMD_RETRIGGER;
    while(instance->COUNT16.SYNCBUSY.bit.CTRLB)
    {
        /* wait for sync */
    }
}