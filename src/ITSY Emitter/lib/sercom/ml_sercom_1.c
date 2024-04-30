/*
 * Author: Ben Westcott, Jayson De La Vega
 * Date created: 8/11/23
 */
#include <ml_sercom_1.h>
#include <ml_dmac.h>

// BAUD = fref/(2*fbaud) - 1
#define SERCOM1_SPI_BAUD 0x04

/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                        PAD0
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * DIPO = 0x00 from spi_init
 * Data in (DI) on PAD0
 *     ==> For master, DI is MISO
 *     ==> For slave, DI is MOSI
 * 
 * PA00 --> SERCOM1/PAD0
 *   - IB: x
 *   - GC: x
 */
const ml_pin_settings ml_sercom1_spi_pad0_pin = 
{
    PORT_GRP_A, 0, PF_D, PP_EVEN, OUTPUT_PULL_DOWN, DRIVE_OFF
};


/* * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                        PAD1
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * DOPO = 0x02 from spi_init
 * SCK on PAD1
 *     ==> For master, SCK is output (default)
 *     ==> For slave, SCK is input
 * 
 * PA01 --> SERCOM1/PAD1
 *   - IB: x
 *   - GC: x
 */
const ml_pin_settings ml_sercom1_spi_pad1_pin = 
{
    PORT_GRP_A, 1, PF_D, PP_ODD, OUTPUT_PULL_DOWN, DRIVE_OFF
};


/* * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                        PAD2
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * DOPO = 0x02 from spi_init
 * SS' on PAD2
 *     ==> For master, SS' is output
 *     ==> For slave, SS' is input
 * 
 * PA14 --> SERCOM4/PAD2
 *   - IB: D4
 *   - GC: D28
 * 
 * If MSSEN = 1, we use PAD2 for SS', but this only works
 * for communication between a master and one slave.
 * 
 * Instead, we will ignore PAD2 for master mode and provide a
 * list of GPIO pins the master can use as SS lines.
 */
const ml_pin_settings ml_sercom1_spi_pad2_pin =
{
    PORT_GRP_A, 18, PF_C, PP_EVEN, INPUT_STANDARD, DRIVE_OFF
};

/* * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                     Master SS pins
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * */

/*
 * PA18
 *   - IB: D7
 *   - GC: D35
 */
const ml_pin_settings ml_sercom1_spi_ss0_pin = 
{
    PORT_GRP_A, 18, PF_L, PP_EVEN, OUTPUT_PULL_DOWN, DRIVE_OFF 
};

/* 
 * PA19
 *   - IB: D9
 *   - GC: D34
 */
const ml_pin_settings ml_sercom1_spi_ss1_pin = 
{
    PORT_GRP_A, 19, PF_L, PP_ODD, OUTPUT_PULL_DOWN, DRIVE_OFF 
};

/* 
 * PA20
 *   - IB: D10 
 *   - GC: D33
 */
const ml_pin_settings ml_sercom1_spi_ss2_pin = 
{
    PORT_GRP_A, 20, PF_L, PP_EVEN, OUTPUT_PULL_DOWN, DRIVE_OFF 
};

/* 
 * PA21
 *   - IB: D11
 *   - GC: D32
 */
const ml_pin_settings ml_sercom1_spi_ss3_pin = 
{
    PORT_GRP_A, 21, PF_L, PP_ODD, OUTPUT_PULL_DOWN, DRIVE_OFF 
};


/* * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                        PAD3
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * DOPO = 0x02 from spi_init
 * Data out (DO) on PAD3 
 *     ==> For master, DO is MOSI
 *     ==> For slave, DO is MISO
 * 
 * PB23 --> SERCOM1/PAD3
 *   - IB: x
 *   - GC: x
 */
const ml_pin_settings ml_sercom1_spi_pad3_pin =
{
    PORT_GRP_B, 23, PF_C, PP_ODD, INPUT_STANDARD, DRIVE_OFF
};


void sercom1_spi_init(const ml_spi_opmode_t opmode)
{

    ml_pin_settings pad0 = ml_sercom1_spi_pad0_pin;
    ml_pin_settings pad1 = ml_sercom1_spi_pad1_pin;
    ml_pin_settings pad3 = ml_sercom1_spi_pad3_pin;

    MCLK->APBAMASK.bit.SERCOM1_ = true;
    ML_SET_GCLK0_PCHCTRL(SERCOM1_GCLK_ID_CORE);

    spi_disable(SERCOM1);
    spi_swrst(SERCOM1);


    SERCOM1->SPI.CTRLA.reg |= XFERMODE0;
    SERCOM1->SPI.CTRLA.bit.MODE = opmode;
    SERCOM1->SPI.CTRLA.bit.DIPO = DIPO_PAD3;
    SERCOM1->SPI.CTRLA.bit.DOPO = DOPO_PAD0;
    SERCOM1->SPI.CTRLA.bit.DORD = DORD_MSBFIRST;
    SERCOM1->SPI.CTRLA.bit.FORM = FRAME_SPI;
    SERCOM1->SPI.CTRLA.bit.RUNSTDBY = true;
    SERCOM1->SPI.CTRLA.bit.IBON = true;

    SERCOM1->SPI.CTRLB.bit.CHSIZE = CHARSIZE_8BIT;
    //SERCOM1->SPI.CTRLB.bit.MSSEN = false;
    //SERCOM1->SPI.CTRLB.bit.SSDE = false;
    //SERCOM1->SPI.CTRLB.bit.AMODE = ADDRMODE_MASK;
    while(SERCOM1->SPI.SYNCBUSY.bit.CTRLB != 0U)
    {
        /* Wait for sync */
    }

    //SERCOM1->SPI.CTRLC.bit.ICSPACE = 0x00;
    SERCOM1->SPI.CTRLC.bit.DATA32B = false;

    SERCOM1->SPI.BAUD.bit.BAUD = SERCOM1_SPI_BAUD;

    ML_SERCOM_SPI_INTSET_DRE(SERCOM1);
    ML_SERCOM_SPI_INTSET_ERR(SERCOM1);
    ML_SERCOM_SPI_INTSET_RXC(SERCOM1);
    ML_SERCOM_SPI_INTSET_TXC(SERCOM1);

    if(opmode == OPMODE_SLAVE)
    {
        SERCOM1->SPI.CTRLA.bit.DIPO = DIPO_PAD0;
        SERCOM1->SPI.CTRLA.bit.DOPO = DOPO_PAD3;

        SERCOM1->SPI.CTRLB.bit.PLOADEN = true;
        SERCOM1->SPI.CTRLB.bit.SSDE = true;
        while(SERCOM1->SPI.SYNCBUSY.bit.CTRLB != 0U)
        {
            /* Wait for sync */
        }

        ML_SERCOM_SPI_INTSET_SSL(SERCOM1);
        NVIC_EnableIRQ(SERCOM1_3_IRQn);
        NVIC_SetPriority(SERCOM1_3_IRQn, 2);

        pad0.conf = INPUT_STANDARD;
        pad1.conf = INPUT_STANDARD;
        pad3.conf = INPUT_STANDARD;

        peripheral_port_init(&ml_sercom1_spi_pad2_pin);

    }
    else 
    {
        peripheral_port_init(&ml_sercom1_spi_ss0_pin);
        port_pmux_disable(&ml_sercom1_spi_ss0_pin);
        ML_SERCOM1_SPI_SS0_PUSH();

        peripheral_port_init(&ml_sercom1_spi_ss1_pin);
        port_pmux_disable(&ml_sercom1_spi_ss1_pin);
        ML_SERCOM1_SPI_SS1_PUSH();

        peripheral_port_init(&ml_sercom1_spi_ss2_pin);
        port_pmux_disable(&ml_sercom1_spi_ss2_pin);
        ML_SERCOM1_SPI_SS2_PUSH();

        peripheral_port_init(&ml_sercom1_spi_ss3_pin);
        port_pmux_disable(&ml_sercom1_spi_ss3_pin);
        ML_SERCOM1_SPI_SS3_PUSH();
    }

    peripheral_port_init(&pad0);
    peripheral_port_init(&pad1);
    peripheral_port_init(&pad3);

}

const uint32_t sercom1_spi_rx_dmac_channel_settings = 
(
    DMAC_CHCTRLA_BURSTLEN_SINGLE |
    DMAC_CHCTRLA_TRIGSRC(SERCOM1_DMAC_ID_RX) |
    DMAC_CHCTRLA_TRIGACT_BURST
);

const uint16_t sercom1_spi_rx_master_dmac_descriptor_settings = 
(
    DMAC_BTCTRL_BEATSIZE_BYTE |
    DMAC_BTCTRL_DSTINC |
    DMAC_BTCTRL_BLOCKACT_BOTH |
    DMAC_BTCTRL_VALID
);

const uint16_t sercom1_spi_rx_slave_dmac_descriptor_settings =
(
    DMAC_BTCTRL_BEATSIZE_BYTE |
    DMAC_BTCTRL_DSTINC |
    DMAC_BTCTRL_BLOCKACT_INT |
    DMAC_BTCTRL_VALID
);

const uint32_t sercom1_spi_tx_dmac_channel_settings = 
(
    DMAC_CHCTRLA_BURSTLEN_SINGLE |
    DMAC_CHCTRLA_TRIGACT_BURST |
    DMAC_CHCTRLA_TRIGSRC(SERCOM1_DMAC_ID_TX)
);

const uint16_t sercom1_spi_tx_master_dmac_descriptor_settings = 
(
    DMAC_BTCTRL_VALID |
    DMAC_BTCTRL_BLOCKACT_BOTH |
    DMAC_BTCTRL_BEATSIZE_BYTE |
    DMAC_BTCTRL_SRCINC
);

const uint16_t sercom1_spi_tx_slave_dmac_descriptor_settings = 
(
    DMAC_BTCTRL_VALID |
    DMAC_BTCTRL_BLOCKACT_INT |
    DMAC_BTCTRL_BEATSIZE_BYTE |
    DMAC_BTCTRL_SRCINC
);

#define SERCOM1_SPI_DMAC_INTMSK (DMAC_CHINTENSET_TCMPL | DMAC_CHINTENSET_TERR)

const ml_spi_s sercom1_spi_dmac_master_prototype = 
{
    .com_inst = SERCOM1,
    .opmode = OPMODE_MASTER,
    .ss_timer_inst = TC0,
    .ss_timer_idx = CC0,
    .rx_dmac_s = 
    {
        .chan_prilvl = PRILVL0,
        .ex_chnum = DMAC_CH0,
        .irqn = DMAC_0_IRQn,
        .irqn_prilvl = 2, 
        .chan_settings = sercom1_spi_rx_dmac_channel_settings,
        .descriptor_settings = sercom1_spi_rx_master_dmac_descriptor_settings,
        .intmsk = SERCOM1_SPI_DMAC_INTMSK,
        .nvic = true
    },
    .tx_dmac_s = 
    {
        .chan_prilvl = PRILVL0,
        .ex_chnum = DMAC_CH1,
        .irqn = DMAC_1_IRQn,
        .irqn_prilvl = 2,
        .chan_settings = sercom1_spi_tx_dmac_channel_settings,
        .descriptor_settings = sercom1_spi_tx_master_dmac_descriptor_settings,
        .intmsk = SERCOM1_SPI_DMAC_INTMSK,
        .nvic = true
    }
};

const ml_spi_s sercom1_spi_dmac_slave_prototype = 
{
    .com_inst = SERCOM1,
    .opmode = OPMODE_SLAVE,
    .rx_dmac_s = 
    {
        .chan_prilvl = PRILVL0,
        .ex_chnum = DMAC_CH4,
        .irqn = DMAC_4_IRQn,
        .irqn_prilvl = 2,
        .chan_settings = sercom1_spi_rx_dmac_channel_settings,
        .descriptor_settings = sercom1_spi_rx_slave_dmac_descriptor_settings,
        .intmsk = SERCOM1_SPI_DMAC_INTMSK,
        .nvic = true
    },
    .tx_dmac_s = 
    {
        .chan_prilvl = PRILVL0,
        .ex_chnum = DMAC_CH3,
        .irqn = DMAC_3_IRQn,
        .irqn_prilvl = 2,
        .chan_settings = sercom1_spi_tx_dmac_channel_settings,
        .descriptor_settings = sercom1_spi_tx_slave_dmac_descriptor_settings,
        .intmsk = SERCOM1_SPI_DMAC_INTMSK,
        .nvic = true
    }
};