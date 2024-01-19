/*
 * Author: Ben Westcott
 * Date created: 1/18/24
 */
#include <serial_handler.hpp>

#include <ml_clocks.h>
#include <ml_dac_common.h>
#include <ml_dac0.h>
#include <ml_dmac.h>
#include <ml_port.h>
#include <ml_tcc_common.h>
#include <ml_tcc2.h>

// 2**15
#define EMIT_BUF_LEN 32768

#define DEFAULT_EMIT_LEN 3000
#define DEFAULT_RECV_CHNKS 12

#define EMIT_CHANNEL 0x02

#define EMIT_SOFT_TRIGGER() (EVSYS->SWEVT.bit.CHANNEL0 = 0x01)

uint16_t emit_buffer[EMIT_BUF_LEN];
uint16_t cpy_buffer[EMIT_BUF_LEN];
uint8_t *cpy_ptr;

uint16_t emit_len;
uint16_t upd_emit_len;

uint16_t n_chunks_cnt;
uint16_t n_recv_chunks;

_Bool recv;
_Bool block_chirp;
_Bool chirping;

static DmacDescriptor base_descriptor[3] __attribute__((aligned(16)));
static volatile DmacDescriptor wb_descriptor[3] __attribute__((aligned(16)));

// D4 --> PA14
const ml_pin_settings dac_timer_pin = {PORT_GRP_A, 14, PF_F, PP_EVEN, OUTPUT_PULL_DOWN, DRIVE_ON};
// D10 --> PA20
const ml_pin_settings amp_pin = {PORT_GRP_A, 20, PF_A, PP_EVEN, OUTPUT_PULL_DOWN, DRIVE_ON};
// A0 --> PA02
const ml_pin_settings dac_pin = {PORT_GRP_A, 2, PF_B, PP_EVEN, ANALOG, DRIVE_ON};

#define AMP_DISABLE() (logical_set(&amp_pin))
#define AMP_ENABLE() (logical_unset(&amp_pin))

const uint32_t emit_dmac_channel_settings =
(
  DMAC_CHCTRLA_BURSTLEN_SINGLE |
  DMAC_CHCTRLA_TRIGACT_BURST |
  DMAC_CHCTRLA_TRIGSRC(TCC2_DMAC_ID_OVF)
);

const uint16_t emit_dmac_descriptor_settings = 
(
  DMAC_BTCTRL_BLOCKACT_BOTH |
  DMAC_BTCTRL_BEATSIZE_HWORD |
  DMAC_BTCTRL_EVOSEL_BLOCK |
  DMAC_BTCTRL_SRCINC |
  DMAC_BTCTRL_VALID
);

void _set_emit_dmac_descriptor(uint32_t btcnt)
{
    DMAC_descriptor_init
    (
        emit_dmac_descriptor_settings,
        btcnt,
        (uint32_t)emit_buffer + (btcnt * sizeof(uint16_t)),
        (uint32_t)&DAC->DATA[0].reg,
        (uint32_t)&base_descriptor[EMIT_CHANNEL],
        &base_descriptor[EMIT_CHANNEL]
    );
}

void _emit_dmac_init(void)
{
    DMAC_init(base_descriptor, wb_descriptor);

    DMAC_channel_init
    (
        (ml_dmac_chnum_t)EMIT_CHANNEL,
        emit_dmac_channel_settings,
        (ml_dmac_chprilvl_t)DMAC_CHPRILVL_PRILVL_LVL0
    );

    EVSYS->USER[EVSYS_ID_USER_DMAC_CH_2].bit.CHANNEL = EMIT_CHANNEL + 0x01;
    EVSYS->Channel[EMIT_CHANNEL].CHANNEL.reg = 
    (
        EVSYS_CHANNEL_EDGSEL_RISING_EDGE |
        EVSYS_CHANNEL_PATH_RESYNCHRONIZED |
        EVSYS_CHANNEL_EVGEN(0x00)
    );

    DMAC->Channel[EMIT_CHANNEL].CHEVCTRL.bit.EVACT = DMAC_CHEVCTRL_EVACT_RESUME_Val;
    DMAC->Channel[EMIT_CHANNEL].CHEVCTRL.bit.EVIE = 0x01;

    _set_emit_dmac_descriptor(DEFAULT_EMIT_LEN);

    DMAC_channel_intenset((ml_dmac_chnum_t)EMIT_CHANNEL, DMAC_2_IRQn, DMAC_CHINTENSET_TCMPL, 1);

    ML_DMAC_ENABLE();
    ML_DMAC_CHANNEL_ENABLE(EMIT_CHANNEL);
    DMAC_suspend_channel(EMIT_CHANNEL);
}

void emit_setup(void)
{
    DOTSTAR_SET_ORANGE();

    DAC_init();
    DAC0_init();
    peripheral_port_init(&dac_pin);
    DAC0_enable();
    DAC_enable();

    TCC2_init();
    peripheral_port_init(&dac_timer_pin);
    TCC_enable(TCC2);

    _emit_dmac_init();

    //memset((void *)cpy_buffer, 0, sizeof(cpy_buffer));
    //memset((void *)emit_buffer, 0, sizeof(emit_buffer));

    emit_len = upd_emit_len = DEFAULT_EMIT_LEN;
    n_recv_chunks = DEFAULT_RECV_CHNKS;
    n_chunks_cnt = 0;
    cpy_ptr = (uint8_t *)cpy_buffer;

    recv = false;
    block_chirp = false;
    chirping = false;
}

uint16_t e_ser_ret_val = 0;

uint16_t emit_loop
(
    uint8_t rx_buffer[SER_BUF_LEN], 
    uint8_t rx_frame_type, 
    uint8_t tx_buffer[SER_BUF_LEN]
)
{
    if(recv)
    {
        //DOTSTAR_SET_RED();
        if (rx_frame_type == RX_DATA_FRAME)
        {
            memcpy((void *)cpy_ptr, (const void *)rx_buffer, SER_BUF_LEN);
            cpy_ptr += SER_BUF_LEN;
            n_chunks_cnt++;
        }

        if(n_chunks_cnt == n_recv_chunks && !chirping)
        {
            EIC->INTENCLR.reg |= (1 << EIC_INTENCLR_EXTINT(0));

            memcpy((void *)emit_buffer, (const void *)cpy_buffer, sizeof(uint16_t) * upd_emit_len);

            _set_emit_dmac_descriptor(upd_emit_len);
            emit_len = upd_emit_len;

            n_chunks_cnt = 0;
            cpy_ptr = (uint8_t *)cpy_buffer;

            recv = false;
            
            EIC->INTENSET.reg |= (1 << EIC_INTENSET_EXTINT(0));
            DOTSTAR_SET_GREEN();

            uint16_t i=0;
            for(; i < 3000; i++)
            {
                if(emit_buffer[i] != 4096)
                {
                    break;
                }
            }
            if(i == 3000)
            {
                DOTSTAR_SET_YELLOW();
            }
        }
    }


    if(rx_frame_type == RX_MSG_FRAME && !recv)
    {
        _Bool buffer_update = (_Bool)rx_buffer[0];
        if(buffer_update)
        {
            upd_emit_len = B_TO_H(rx_buffer[1], rx_buffer[2]);
            n_recv_chunks = B_TO_H(rx_buffer[3], rx_buffer[4]);
            recv = true;
        }
    }

    //frame_type = w_read_loop(rx_msg_buffer);
    return SER_RET_READ;
}

void DMAC_2_Handler(void)
{
    DMAC->Channel[2].CHINTFLAG.bit.TCMPL = 0x01;
    chirping = false;
}

void EIC_0_Handler(void)
{
    // clr flags
    EIC->INTFLAG.reg = EIC_INTFLAG_MASK;

    if(!chirping)
    {
        EMIT_SOFT_TRIGGER();
        chirping = true;
    }
}
