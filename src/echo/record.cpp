/*
 * Author: Ben Westcott
 * Date created: 1/16/23
 */

#include <record.hpp>

#include <stdbool.h>
#include <ml_adc_common.h>
#include <ml_adc0.h>
#include <ml_adc1.h>
#include <ml_clocks.h>
#include <ml_dmac.h>
#include <ml_port.h>
#include <ml_eic.h>

#define MAX_BUF_LEN 64

#define RIGHT_RECORD_CHANNEL 0x00
#define LEFT_RECORD_CHANNEL 0x01

static volatile uint16_t record_buffer[2*MAX_BUF_LEN];

static DmacDescriptor base_descriptor[3] __attribute__((aligned(16)));
static volatile DmacDescriptor wb_descriptor[3] __attribute__((aligned(16)));

const uint32_t recordR_dmac_channel_settings = 
(
  DMAC_CHCTRLA_TRIGACT_BURST |
  DMAC_CHCTRLA_TRIGSRC(ADC0_DMAC_ID_RESRDY)
);

const uint16_t recordR_dmac_descriptor_settings = 
(
  DMAC_BTCTRL_BEATSIZE_HWORD |
  DMAC_BTCTRL_DSTINC |
  DMAC_BTCTRL_EVOSEL_BLOCK |
  DMAC_BTCTRL_BLOCKACT_BOTH |
  DMAC_BTCTRL_VALID
);

const uint32_t recordL_dmac_channel_settings = 
(
  DMAC_CHCTRLA_TRIGACT_BURST |
  DMAC_CHCTRLA_TRIGSRC(ADC1_DMAC_ID_RESRDY)
);

const uint16_t recordL_dmac_descriptor_settings = 
(
  DMAC_BTCTRL_BEATSIZE_HWORD |
  DMAC_BTCTRL_DSTINC |
  DMAC_BTCTRL_EVOSEL_BLOCK |
  DMAC_BTCTRL_BLOCKACT_BOTH |
  DMAC_BTCTRL_VALID
);

void _init_record_dma(void)
{
  DMAC_init(base_descriptor, wb_descriptor);

  DMAC_channel_init
  (
    (ml_dmac_chnum_t)RIGHT_RECORD_CHANNEL,
    recordR_dmac_channel_settings,
    (ml_dmac_chprilvl_t)DMAC_CHPRILVL_PRILVL_LVL0
  );

  EVSYS->USER[EVSYS_ID_USER_DMAC_CH_0].bit.CHANNEL = RIGHT_RECORD_CHANNEL + 0x01;
  EVSYS->Channel[RIGHT_RECORD_CHANNEL].CHANNEL.reg =
  (
    EVSYS_CHANNEL_EDGSEL_RISING_EDGE |
    EVSYS_CHANNEL_PATH_RESYNCHRONIZED |
    EVSYS_CHANNEL_EVGEN(0x00)
  );

  DMAC->Channel[RIGHT_RECORD_CHANNEL].CHEVCTRL.bit.EVOMODE = DMAC_CHEVCTRL_EVOMODE_TRIGACT_Val;
  DMAC->Channel[RIGHT_RECORD_CHANNEL].CHEVCTRL.bit.EVACT = DMAC_CHEVCTRL_EVACT_RESUME_Val;
  DMAC->Channel[RIGHT_RECORD_CHANNEL].CHEVCTRL.bit.EVIE = 0x01;
  DMAC->Channel[RIGHT_RECORD_CHANNEL].CHEVCTRL.bit.EVOE = 0x01;

  DMAC_descriptor_init
  (
    recordR_dmac_descriptor_settings,
    MAX_BUF_LEN,
    (uint32_t)&ADC0->RESULT.reg,
    (uint32_t)record_buffer + sizeof(record_buffer)/2,
    (uint32_t)&base_descriptor[RIGHT_RECORD_CHANNEL],
    &base_descriptor[RIGHT_RECORD_CHANNEL]
  );

  DMAC_channel_init
  (
    (ml_dmac_chnum_t)LEFT_RECORD_CHANNEL, 
    recordL_dmac_channel_settings, 
    (ml_dmac_chprilvl_t)DMAC_CHPRILVL_PRILVL_LVL0
  );

  EVSYS->USER[EVSYS_ID_USER_DMAC_CH_1].bit.CHANNEL = LEFT_RECORD_CHANNEL + 0x01;
  EVSYS->Channel[LEFT_RECORD_CHANNEL].CHANNEL.reg = 
  (
    EVSYS_CHANNEL_EDGSEL_RISING_EDGE |
    EVSYS_CHANNEL_PATH_RESYNCHRONIZED |
    EVSYS_CHANNEL_EVGEN(0x00)
  );

  DMAC->Channel[LEFT_RECORD_CHANNEL].CHEVCTRL.bit.EVOMODE = DMAC_CHEVCTRL_EVOMODE_TRIGACT_Val;
  DMAC->Channel[LEFT_RECORD_CHANNEL].CHEVCTRL.bit.EVACT = DMAC_CHEVCTRL_EVACT_RESUME_Val;
  DMAC->Channel[LEFT_RECORD_CHANNEL].CHEVCTRL.bit.EVIE = 0x01;
  DMAC->Channel[LEFT_RECORD_CHANNEL].CHEVCTRL.bit.EVOE = 0x01;

  DMAC_descriptor_init
  (
    recordL_dmac_descriptor_settings,
    MAX_BUF_LEN,
    (uint32_t)&ADC1->RESULT.reg,
    (uint32_t)&record_buffer[MAX_BUF_LEN] + sizeof(record_buffer)/2,
    (uint32_t)&base_descriptor[LEFT_RECORD_CHANNEL],
    &base_descriptor[LEFT_RECORD_CHANNEL]
  );

  DMAC_channel_intenset((ml_dmac_chnum_t)RIGHT_RECORD_CHANNEL, DMAC_0_IRQn, DMAC_CHINTENSET_TCMPL, 1);
  DMAC_channel_intenset((ml_dmac_chnum_t)LEFT_RECORD_CHANNEL, DMAC_1_IRQn, DMAC_CHINTENSET_TCMPL, 1);

  ML_DMAC_ENABLE();
  ML_DMAC_CHANNEL_ENABLE(RIGHT_RECORD_CHANNEL);
  DMAC_suspend_channel(RIGHT_RECORD_CHANNEL);

  ML_DMAC_CHANNEL_ENABLE(LEFT_RECORD_CHANNEL);
  DMAC_suspend_channel(LEFT_RECORD_CHANNEL);

}

void start_record(void)
{
  EVSYS->SWEVT.bit.CHANNEL0 = 0x01;
  EVSYS->SWEVT.bit.CHANNEL1 = 0x01;

  DOTSTAR_SET_BLUE();
}

// A2 --> PB08 (ADC0, AIN2, listenR)
const ml_pin_settings adc0_pin = {PORT_GRP_B, 8, PF_B, PP_EVEN, ANALOG, DRIVE_OFF};
// A3 --> PB09 (ADC1, AIN1, listenL)
const ml_pin_settings adc1_pin = {PORT_GRP_B, 9, PF_B, PP_ODD, ANALOG, DRIVE_OFF};

const ml_pin_settings record_trigger_pin = {PORT_GRP_A, 16, PF_A, PP_EVEN, INPUT_PULL_DOWN, DRIVE_OFF}; 

#define RECORD_START 0x33

void record_setup(void)
{
  DOTSTAR_SET_ORANGE();
  //DOTSTAR_SET_LIGHT_GREEN();

  ADC0_init();
  peripheral_port_init(&adc0_pin);
  ADC_enable(ADC0);
  
  ADC1_init();
  peripheral_port_init(&adc1_pin);
  ADC_enable(ADC1);

  ADC_swtrig_start(ADC0);
  ADC_swtrig_start(ADC1);
  ADC_flush(ADC0);
  ADC_flush(ADC1);

  OSCULP32K_init();
  eic_init();
  hardware_int_init();
  peripheral_port_init(&record_trigger_pin);
  eic_enable();

  _init_record_dma();

}

_Bool left_finished = false;
_Bool right_finished = false;

_Bool ser_write = false;
_Bool ser_read =  false;
uint16_t ser_ret_val = 0;

_Bool recording = false;


uint16_t record_loop
(
  uint8_t rx_buffer[SER_BUF_LEN], 
  uint8_t rx_frame_type,
  uint8_t tx_buffer[SER_BUF_LEN]
)
{
 // while(!Serial);
  ser_ret_val = 0;
  if(left_finished & right_finished)
  {
    memcpy((void *)tx_buffer, (const void *)record_buffer, sizeof(record_buffer));
    ML_DMAC_CHANNEL_RESUME(RIGHT_RECORD_CHANNEL);
    ML_DMAC_CHANNEL_RESUME(LEFT_RECORD_CHANNEL);

    left_finished = right_finished = false;

    //Serial.write(tx_buffer, SER_BUF_LEN);
    ser_ret_val |= (uint16_t)(TX_SONAR_RECORD_FRAME << 8);
    ser_ret_val |= SER_RET_WRITE;
    //write_buffer(tx_buffer, TX_SONAR_RECORD_FRAME);
  }

#ifdef SERIAL_TRIGGER
  if(rx_frame_type == RECORD_START && !recording)
  {
    start_record();
    recording = true;
  }
#endif

  if(!recording)
  {
    ser_ret_val |= SER_RET_READ;
  }

  return ser_ret_val;
}

void DMAC_0_Handler(void)
{
  right_finished = true;
  DMAC->Channel[0].CHINTFLAG.reg = DMAC_CHINTFLAG_MASK;
}

void DMAC_1_Handler(void)
{
  left_finished = true;
  DMAC->Channel[1].CHINTFLAG.reg = DMAC_CHINTFLAG_MASK;
}

#if defined(BUILD_RECORD) && defined(EIC_TRIGGER)
void EIC_0_Handler(void)
{
    // clr flags
    EIC->INTFLAG.reg = EIC_INTFLAG_MASK;

    //DOTSTAR_SET_ORANGE();

    if(!recording)
    {
      start_record();
      recording = true;
    }
}
#endif // BUILD_RECORD