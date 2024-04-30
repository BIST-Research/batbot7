/*
 * Author: Ben Westcott
 * Date created: 8/25/23
 */

#include <ml_dac1.h>
#include <ml_dmac.h>

void DAC1_init(void)
{
    if(DAC1_disable() < 0)
    {
        DAC_disable();
        DAC1_disable();
    }

    DAC->DACCTRL[1].bit.OSR = OSR1;
    DAC->DACCTRL[1].bit.REFRESH = 0x00;
    DAC->DACCTRL[1].bit.DITHER = false;
    DAC->DACCTRL[1].bit.RUNSTDBY = false;
    DAC->DACCTRL[1].bit.FEXT = false;
    DAC->DACCTRL[1].bit.LEFTADJ = 0x00;
    DAC->DACCTRL[1].bit.CCTRL = CC12MEG;
}

#define _DAC1_CHKEN()         (DAC->CTRLA.bit.ENABLE)

int8_t DAC1_enable(void)
{
    if(_DAC1_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[1].bit.ENABLE = 0x01;
    return 0;
}

int8_t DAC1_disable(void)
{
    if(_DAC1_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[1].bit.ENABLE = 0x00;
    return 0;
}

int8_t DAC1_set_oversampling_ratio(const ml_dac_osr_t value)
{
    if(_DAC1_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[1].bit.OSR = value;
    return 0;
}

int8_t DAC1_set_refresh_period(const uint8_t period_us)
{
    if(_DAC1_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[1].bit.REFRESH = (uint8_t)ML_DAC_GET_REFRESH_VALUE(period_us);
    return 0;
}

int8_t DAC1_runstdby_enable(void)
{
    if(_DAC1_CHKEN())
    {
        return -1;
    }
    
    DAC->DACCTRL[1].bit.RUNSTDBY = 0x01;
    return 0;
}
int8_t DAC1_runstdby_disable(void)
{
    if(_DAC1_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[1].bit.RUNSTDBY = 0x00;
    return 0;
}

int8_t DAC1_extfilt_enable(void)
{
    if(_DAC1_CHKEN())
    {
        return -1;
    }
    
    DAC->DACCTRL[1].bit.FEXT = 0x01;
    return 0;
}

int8_t DAC1_extfilt_disable(void)
{
    if(_DAC1_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[1].bit.FEXT = 0x00;
    return 0;
}

int8_t DAC1_dither_enable(void)
{
    if(_DAC1_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[1].bit.DITHER = 0x01;
    return 0;
}

int8_t DAC1_dither_disable(void)
{
    if(_DAC1_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[1].bit.DITHER = 0x00;
    return 0;
}


int8_t DAC1_set_leftadj(void)
{
    if(_DAC1_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[1].bit.LEFTADJ = 0x01;
    return 0;
}
int8_t DAC1_set_rightadj(void)
{
    if(_DAC1_CHKEN())
    {
        return -1;
    }

    DAC->DACCTRL[1].bit.LEFTADJ = 0x00;
    return 0;
}

void DAC1_write(const uint16_t value)
{
    DAC->DATA[1].reg = value;
    while(DAC->SYNCBUSY.bit.DATA1 != 0U)
    {
        /* Wait for sync */
    }
}

void DAC1_buffer_write(const uint16_t value)
{
    DAC->DATABUF[1].reg = value;
    while(DAC->SYNCBUSY.bit.DATABUF1 != 0U)
    {
        /* Wait for sync */
    }

}

uint16_t DAC1_get_interpol_result(void)
{
    return (uint16_t)DAC->RESULT[1].reg;
}

#define DAC1_DMAC_INTMSK        (DMAC_CHINTENSET_TCMPL | DMAC_CHINTENSET_TERR)

const uint32_t dac1_dmac_channel_settings = 
(
    DMAC_CHCTRLA_BURSTLEN_SINGLE |
    DMAC_CHCTRLA_TRIGACT_BURST |
    DMAC_CHCTRLA_TRIGSRC(TC1_DMAC_ID_MC_1)
);

const uint16_t dac1_dmac_descriptor_settings = 
(
    DMAC_BTCTRL_VALID |
    DMAC_BTCTRL_BLOCKACT_BOTH |
    DMAC_BTCTRL_BEATSIZE_HWORD |
    DMAC_BTCTRL_SRCINC
);

const ml_dmac_s dac0_dmac_prototype =
{
    .chan_prilvl = PRILVL0,
    .ex_chnum = DMAC_CH3,
    .irqn = DMAC_3_IRQn,
    .irqn_prilvl = 2,
    .chan_settings = dac1_dmac_channel_settings,
    .descriptor_settings = dac1_dmac_descriptor_settings,
    .intmsk = DAC1_DMAC_INTMSK,
    .nvic = true
};
