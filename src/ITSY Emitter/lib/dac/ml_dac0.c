/*
 * Author: Ben Westcott
 * Date created: 8/25/23
 */

#include <ml_dac0.h>
#include <ml_clocks.h>
#include <stdbool.h>
#include <ml_dmac.h>

void DAC0_init(void)
{
    if(DAC0_disable() < 0)
    {
        DAC_disable();
        DAC0_disable();
    }

    DAC->DACCTRL[0].bit.OSR = OSR1;
    DAC->DACCTRL[0].bit.REFRESH = 0x00;
    DAC->DACCTRL[0].bit.DITHER = false;
    DAC->DACCTRL[0].bit.RUNSTDBY = false;
    DAC->DACCTRL[0].bit.FEXT = false;
    DAC->DACCTRL[0].bit.LEFTADJ = 0x00;
    DAC->DACCTRL[0].bit.CCTRL = CC12MEG;

}

#define _DAC0_CHKEN()         (DAC->CTRLA.bit.ENABLE)

int8_t DAC0_enable(void)
{
    if(_DAC0_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[0].bit.ENABLE = 0x01;
    return 0;
}

int8_t DAC0_disable(void)
{
    if(_DAC0_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[0].bit.ENABLE = 0x00;
    return 0;
}

int8_t DAC0_set_oversampling_ratio(const ml_dac_osr_t value)
{
    if(_DAC0_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[0].bit.OSR = value;
    return 0;
}

int8_t DAC0_set_refresh_period(const uint8_t period_us)
{
    if(_DAC0_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[0].bit.REFRESH = (uint8_t)ML_DAC_GET_REFRESH_VALUE(period_us);
    return 0;
}

int8_t DAC0_runstdby_enable(void)
{
    if(_DAC0_CHKEN())
    {
        return -1;
    }
    
    DAC->DACCTRL[0].bit.RUNSTDBY = 0x01;
    return 0;
}
int8_t DAC0_runstdby_disable(void)
{
    if(_DAC0_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[0].bit.RUNSTDBY = 0x00;
    return 0;
}

int8_t DAC0_extfilt_enable(void)
{
    if(_DAC0_CHKEN())
    {
        return -1;
    }
    
    DAC->DACCTRL[0].bit.FEXT = 0x01;
    return 0;
}

int8_t DAC0_extfilt_disable(void)
{
    if(_DAC0_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[0].bit.FEXT = 0x00;
    return 0;
}

int8_t DAC0_dither_enable(void)
{
    if(_DAC0_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[0].bit.DITHER = 0x01;
    return 0;
}

int8_t DAC0_dither_disable(void)
{
    if(_DAC0_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[0].bit.DITHER = 0x00;
    return 0;
}


int8_t DAC0_set_leftadj(void)
{
    if(_DAC0_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[0].bit.LEFTADJ = 0x01;
    return 0;
}
int8_t DAC0_set_rightadj(void)
{
    if(_DAC0_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[0].bit.LEFTADJ = 0x00;
    return 0;
}

void DAC0_write(const uint16_t value)
{
    DAC->DATA[0].reg = value;
    while(DAC->SYNCBUSY.bit.DATA0 != 0U)
    {
        /* Wait for sync */
    }
}

void DAC0_buffer_write(const uint16_t value)
{
    DAC->DATABUF[0].reg = value;
    while(DAC->SYNCBUSY.bit.DATABUF0 != 0U)
    {
        /* Wait for sync */
    }

}

uint16_t DAC0_get_interpol_result(void)
{
    return (uint16_t)DAC->RESULT[0].reg;
}

#define DAC0_DMAC_INTMSK        (DMAC_CHINTENSET_TCMPL | DMAC_CHINTENSET_TERR)

const uint32_t dac0_dmac_channel_settings = 
(
    DMAC_CHCTRLA_BURSTLEN_SINGLE |
    DMAC_CHCTRLA_TRIGACT_BURST |
    DMAC_CHCTRLA_TRIGSRC(TC1_DMAC_ID_MC_0)
);

const uint16_t dac0_dmac_descriptor_settings = 
(
    DMAC_BTCTRL_VALID |
    DMAC_BTCTRL_BLOCKACT_BOTH |
    DMAC_BTCTRL_BEATSIZE_HWORD |
    DMAC_BTCTRL_SRCINC
);

const ml_dmac_s dac0_dmac_prototype =
{
    .chan_prilvl = PRILVL0,
    .ex_chnum = DMAC_CH2,
    .irqn = DMAC_2_IRQn,
    .irqn_prilvl = 2,
    .chan_settings = dac0_dmac_channel_settings,
    .descriptor_settings = dac0_dmac_descriptor_settings,
    .intmsk = DAC0_DMAC_INTMSK,
    .nvic = true
};

