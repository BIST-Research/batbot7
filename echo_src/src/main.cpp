/*
 * Author: Ben Westcott
 * Date created: 12/21/23
 */

#include <Arduino.h>
#include <ml_ac.h>
#include <ml_adc_common.h>
#include <ml_adc0.h>
#include <ml_adc1.h>
#include <ml_clocks.h>
#include <ml_dac_common.h>
#include <ml_dac0.h>
#include <ml_dmac.h>
#include <ml_eic.h>
#include <ml_port.h>
#include <ml_tc_common.h>
#include <ml_tc0.h>
#include <ml_tc1.h>
#include <ml_tcc_common.h>
#include <ml_tcc0.h>
#include <ml_tcc1.h>
#include <ml_tcc2.h>

#define MAX_BUFFER_LENGTH 80000
#define DEFAULT_CHIRP_LENGTH 5000
#define DEFAULT_LISTEN_LENGTH 30000
#define DEFAULT_WAIT_TIMER_PERIOD 100
#define DEFAULT_WAIT_TIMER_PRESCALER TCC_CTRLA_PRESCALER_DIV4_Val

#define CHIRP_DMAC_CHANNEL 0x00
#define LISTEN_R_DMAC_CHANNEL 0x01
#define LISTEN_L_DMAC_CHANNEL 0x02

#define WAIT_TIMER_START_CHANNEL 0x00
#define EXIT_TIMER_A_START_CHANNEL 0x01
#define EXIT_TIMER_B_START_CHANNEL 0x02
#define LISTEN_R_START_CHANNEL 0x03
#define LISTEN_L_START_CHANNEL 0x04
#define CHIRP_START_CHANNEL 0x05

#define LISTEN_START_SOFT_TRIGGER() (EVSYS->SWEVT.bit.CHANNEL0 = 0x01)
#define CHIRP_START_SOFT_TRIGGER() (EVSYS->SWEVT.bit.CHANNEL5 = 0x01)

#define EVSYS_ID_GEN_NONE 0x00

#define S_CHUNK_SIZE 64
#define S_ACK 0x55
#define S_UPDATE_COMPLETE 0x56

#define S_WRITE_ACK() (Serial.write(S_ACK))
#define S_WRITE_UPDATE_COMPLETE() (Serial.write(S_UPDATE_COMPLETE))

#define S_COMMAND 0x44
#define S_DATA 0x45

#define S_READ_BYTE() ((uint8_t)Serial.read())
#define S_READ_HALF_WORD() ((uint16_t)Serial.read() << 8 | (uint16_t)Serial.read())
#define S_COMMAND_AVAILABLE() (Serial.available() && Serial.read() == S_COMMAND)
#define S_DATA_AVAILABLE() (Serial.available() && SERIAL.read() == S_DATA)

static DmacDescriptor base_descriptor[3] __attribute__((aligned(16)));
static volatile DmacDescriptor wb_descriptor[3] __attribute__((aligned(16)));

typedef enum 
{
  NO_ACT = 0xff, START_JOB = 0xfe, AMP_ENABLE = 0xfd, 
  AMP_DISABLE = 0xfb, UPDATE_JOB = 0xfa
} host_action;

typedef enum
{
  UPDATE_BUFFER = 0xef, UPDATE_CHIRP = 0xed, UPDATE_WAIT_TIMER_PERIOD = 0xec,
  UPDATE_WAIT_TIMER_PRESCALER = 0xeb, UPDATE_FINISH = 0xea
} host_update_action;

typedef enum {IDLE, BUSY, UPDATE, SEND} device_state;

_Bool start_flag;
_Bool chirp_flag;
_Bool update_flag;
uint16_t wait_timer_val;
uint16_t wait_timer_prescaler;
uint16_t nchunks;
device_state dstate;

// D10 --> PA20
const ml_pin_settings amp_pin = {PORT_GRP_A, 20, PF_A, PP_EVEN, OUTPUT_PULL_DOWN, DRIVE_ON};
// A0 --> PA02
const ml_pin_settings dac_pin = {PORT_GRP_A, 2, PF_B, PP_EVEN, ANALOG, DRIVE_ON};
// A2 --> PB08 (ADC0, AIN2, listenR)
const ml_pin_settings adc0_pin = {PORT_GRP_B, 8, PF_B, PP_EVEN, ANALOG, DRIVE_OFF};
// A3 --> PB09 (ADC1, AIN1, listenL)
const ml_pin_settings adc1_pin = {PORT_GRP_B, 9, PF_B, PP_ODD, ANALOG, DRIVE_OFF};
// D11 --> PA21
const ml_pin_settings tcc0_pin = {PORT_GRP_A, 21, PF_G, PP_ODD, OUTPUT_PULL_DOWN, DRIVE_OFF};

#define AMP_DISABLE() (logical_set(&amp_pin))
#define AMP_ENABLE() (logical_unset(&amp_pin))

// One buffer holds chirp (supplied by host), and both listen buffers
static volatile uint16_t data_buffer[MAX_BUFFER_LENGTH];
/*
 *
 * The following global variables should
 * NEVER be modified outside partition_data_buffer
 * 
 */
uint16_t *base_chirp_ptr;
uint16_t *base_listenR_ptr;
uint16_t *base_listenL_ptr;
uint16_t *base_listen_ptr;

uint16_t *top_listen_ptr;

uint16_t chirp_len;
uint16_t listenR_len;
uint16_t listenL_len;

// MAX_BUFFER_LEN > max(uint16_t)
uint32_t listen_len;
uint32_t total_len;

_Bool do_chirp;
_Bool do_right;
_Bool do_left;

uint8_t event_selector;

/*
 *
 * can only be called in update state (no active transfers)
 *
 * This function rebuilds the data buffer depending on the number
 * of chirp, and right/left listen samples are wanted (supplied by host)
 * 
 * This is the only function which will modify the variables above.
 * They are meant to be used as refernces for finishing the update chain
 * and for traversing the data buffer.
 *
 */
void partition_data_buffer(uint16_t clen, uint16_t rlen, uint16_t llen)
{
  // enforce total length on host
  uint16_t *ptr = (uint16_t *)&data_buffer[0];
  
  base_chirp_ptr = ptr;

  ptr += clen;

  base_listenR_ptr = ptr;
  base_listen_ptr = ptr;

  ptr += rlen;

  base_listenL_ptr = ptr;

  ptr += llen;

  top_listen_ptr = ptr;

  chirp_len = clen;
  listenR_len = rlen;
  listenL_len = llen;
  listen_len = (uint32_t)rlen + (uint32_t)llen;
  total_len = listen_len + (uint32_t)clen;

  do_chirp = (_Bool)clen;
  do_right = (_Bool)rlen;
  do_left = (_Bool)llen;

  event_selector = ((uint8_t)do_right << 1) | ((uint8_t) do_left << 0);
}


// can only be called in update state (no active transfers)
// needs to be called AFTER calling partition_data_buffer in update chain
void update_transfer_descriptors(void)
{

  base_descriptor[CHIRP_DMAC_CHANNEL].BTCTRL.bit.VALID = do_chirp;
  base_descriptor[LISTEN_R_DMAC_CHANNEL].BTCTRL.bit.VALID = do_right;
  base_descriptor[LISTEN_L_DMAC_CHANNEL].BTCTRL.bit.VALID = do_left;

  //ML_DMAC_CHANNEL_DISABLE(CHIRP_DMAC_CHANNEL);

  if(do_chirp)
  {
    base_descriptor[CHIRP_DMAC_CHANNEL].BTCNT.reg = chirp_len;
    base_descriptor[CHIRP_DMAC_CHANNEL].SRCADDR.reg = (uint32_t)base_chirp_ptr + (sizeof(uint16_t) * chirp_len);
  }

  if(do_right)
  {
    base_descriptor[LISTEN_R_DMAC_CHANNEL].BTCNT.reg = listenR_len;
    base_descriptor[LISTEN_R_DMAC_CHANNEL].DSTADDR.reg = (uint32_t)base_listenR_ptr + (sizeof(uint16_t) * listenR_len);
  }

  if(do_left)
  {
    base_descriptor[LISTEN_L_DMAC_CHANNEL].BTCNT.reg = listenL_len;
    base_descriptor[LISTEN_L_DMAC_CHANNEL].DSTADDR.reg = (uint32_t)base_listenL_ptr + (sizeof(uint16_t) * listenL_len);
  }
}           

const uint32_t chirp_dmac_channel_settings =
(
  DMAC_CHCTRLA_BURSTLEN_SINGLE |
  DMAC_CHCTRLA_TRIGACT_BURST |
  DMAC_CHCTRLA_TRIGSRC(TCC2_DMAC_ID_OVF)
);

const uint16_t chirp_dmac_descriptor_settings = 
(
  DMAC_BTCTRL_BLOCKACT_BOTH |
  DMAC_BTCTRL_BEATSIZE_HWORD |
  DMAC_BTCTRL_EVOSEL_BLOCK |
  DMAC_BTCTRL_SRCINC |
  DMAC_BTCTRL_VALID
);

const uint32_t listenR_dmac_channel_settings = 
(
  DMAC_CHCTRLA_TRIGACT_BURST |
  DMAC_CHCTRLA_TRIGSRC(ADC0_DMAC_ID_RESRDY)
);

const uint16_t listenR_dmac_descriptor_settings = 
(
  DMAC_BTCTRL_BEATSIZE_HWORD |
  DMAC_BTCTRL_DSTINC |
  DMAC_BTCTRL_EVOSEL_BLOCK |
  DMAC_BTCTRL_BLOCKACT_BOTH |
  DMAC_BTCTRL_VALID
);

const uint32_t listenL_dmac_channel_settings = 
(
  DMAC_CHCTRLA_TRIGACT_BURST |
  DMAC_CHCTRLA_TRIGSRC(ADC1_DMAC_ID_RESRDY)
);

const uint16_t listenL_dmac_descriptor_settings = 
(
  DMAC_BTCTRL_BEATSIZE_HWORD |
  DMAC_BTCTRL_DSTINC |
  DMAC_BTCTRL_EVOSEL_BLOCK |
  DMAC_BTCTRL_BLOCKACT_BOTH |
  DMAC_BTCTRL_VALID
);


typedef struct _ev_sel_s 
{
  uint32_t wait_gen;
  uint32_t exit_A_gen;
  uint32_t exit_B_gen;
  uint32_t listen_R_gen;
  uint32_t listen_L_gen;
} ev_sel_s;

ev_sel_s ev_selectors[4] = 
{
  // 0b00
  {EVSYS_ID_GEN_NONE, EVSYS_ID_GEN_TCC1_OVF, EVSYS_ID_GEN_TCC1_OVF, EVSYS_ID_GEN_NONE, EVSYS_ID_GEN_NONE},
  // 0b01
  {EVSYS_ID_GEN_NONE, EVSYS_ID_GEN_DMAC_CH_2, EVSYS_ID_GEN_DMAC_CH_2, EVSYS_ID_GEN_NONE, EVSYS_ID_GEN_TCC1_OVF},
  // 0b10
  {EVSYS_ID_GEN_NONE, EVSYS_ID_GEN_DMAC_CH_1, EVSYS_ID_GEN_DMAC_CH_1, EVSYS_ID_GEN_TCC1_OVF, EVSYS_ID_GEN_NONE},
  // 0b11
  {EVSYS_ID_GEN_NONE, EVSYS_ID_GEN_DMAC_CH_1, EVSYS_ID_GEN_DMAC_CH_2, EVSYS_ID_GEN_TCC1_OVF, EVSYS_ID_GEN_TCC1_OVF}
};

void update_event_generators(void)
{
  ev_sel_s select = ev_selectors[event_selector];

  EVSYS->Channel[WAIT_TIMER_START_CHANNEL].CHANNEL.bit.EVGEN = select.wait_gen;
  EVSYS->Channel[EXIT_TIMER_A_START_CHANNEL].CHANNEL.bit.EVGEN = select.exit_A_gen;
  EVSYS->Channel[EXIT_TIMER_B_START_CHANNEL].CHANNEL.bit.EVGEN = select.exit_B_gen;
  EVSYS->Channel[LISTEN_R_START_CHANNEL].CHANNEL.bit.EVGEN = select.listen_R_gen;
  EVSYS->Channel[LISTEN_L_START_CHANNEL].CHANNEL.bit.EVGEN = select.listen_L_gen;
}

void init_dmac_channels(void)
{

  DMAC_init(&base_descriptor[0], &wb_descriptor[0]);

  DMAC_channel_init
  (
    (ml_dmac_chnum_t)CHIRP_DMAC_CHANNEL, 
    chirp_dmac_channel_settings, 
    (ml_dmac_chprilvl_t)DMAC_CHPRILVL_PRILVL_LVL0
  );

  EVSYS->USER[EVSYS_ID_USER_DMAC_CH_0].bit.CHANNEL = CHIRP_START_CHANNEL + 0x01;
  EVSYS->Channel[CHIRP_START_CHANNEL].CHANNEL.reg = 
  (
    EVSYS_CHANNEL_EDGSEL_RISING_EDGE |
    EVSYS_CHANNEL_PATH_RESYNCHRONIZED |
    EVSYS_CHANNEL_EVGEN(0x00)
  );

  DMAC->Channel[CHIRP_DMAC_CHANNEL].CHEVCTRL.bit.EVACT = DMAC_CHEVCTRL_EVACT_RESUME_Val;
  DMAC->Channel[CHIRP_DMAC_CHANNEL].CHEVCTRL.bit.EVIE = 0x01;

  DMAC_channel_init
  (
    (ml_dmac_chnum_t)LISTEN_R_DMAC_CHANNEL, 
    listenR_dmac_channel_settings, 
    (ml_dmac_chprilvl_t)DMAC_CHPRILVL_PRILVL_LVL0
  );

  EVSYS->USER[EVSYS_ID_USER_DMAC_CH_1].bit.CHANNEL = LISTEN_R_START_CHANNEL + 0x01;
  EVSYS->Channel[LISTEN_R_START_CHANNEL].CHANNEL.reg = 
  (
    EVSYS_CHANNEL_EDGSEL_RISING_EDGE |
    EVSYS_CHANNEL_PATH_RESYNCHRONIZED |
   // EVSYS_CHANNEL_EVGEN(EVSYS_ID_GEN_TCC1_OVF)
    EVSYS_CHANNEL_EVGEN(0x00)
  );

  DMAC->Channel[LISTEN_R_DMAC_CHANNEL].CHEVCTRL.bit.EVOMODE = DMAC_CHEVCTRL_EVOMODE_TRIGACT_Val;
  DMAC->Channel[LISTEN_R_DMAC_CHANNEL].CHEVCTRL.bit.EVACT = DMAC_CHEVCTRL_EVACT_RESUME_Val;
  DMAC->Channel[LISTEN_R_DMAC_CHANNEL].CHEVCTRL.bit.EVIE = 0x01;
  DMAC->Channel[LISTEN_R_DMAC_CHANNEL].CHEVCTRL.bit.EVOE = 0x01;

  DMAC_channel_init
  (
    (ml_dmac_chnum_t)LISTEN_L_DMAC_CHANNEL, 
    listenL_dmac_channel_settings, 
    (ml_dmac_chprilvl_t)DMAC_CHPRILVL_PRILVL_LVL0
  );

  EVSYS->USER[EVSYS_ID_USER_DMAC_CH_2].bit.CHANNEL = LISTEN_L_START_CHANNEL + 0x01;
  EVSYS->Channel[LISTEN_L_START_CHANNEL].CHANNEL.reg = 
  (
    EVSYS_CHANNEL_EDGSEL_RISING_EDGE |
    EVSYS_CHANNEL_PATH_RESYNCHRONIZED |
    //EVSYS_CHANNEL_EVGEN(EVSYS_ID_GEN_TCC1_OVF)
    EVSYS_CHANNEL_EVGEN(0x00)
  );

  DMAC->Channel[LISTEN_L_DMAC_CHANNEL].CHEVCTRL.bit.EVOMODE = DMAC_CHEVCTRL_EVOMODE_TRIGACT_Val;
  DMAC->Channel[LISTEN_L_DMAC_CHANNEL].CHEVCTRL.bit.EVACT = DMAC_CHEVCTRL_EVACT_RESUME_Val;
  DMAC->Channel[LISTEN_L_DMAC_CHANNEL].CHEVCTRL.bit.EVIE = 0x01;
  DMAC->Channel[LISTEN_L_DMAC_CHANNEL].CHEVCTRL.bit.EVOE = 0x01;
}

// can only be called in update state (no active transfers)
// needs to be called AFTER calling partition_data_buffer in update chain
void init_dmac_descriptors(void)
{
  DMAC_descriptor_init
  (
    chirp_dmac_descriptor_settings,
    chirp_len,
    (uint32_t)base_chirp_ptr + (sizeof(uint16_t) * chirp_len),
    (uint32_t)&DAC->DATA[0].reg,
    (uint32_t)&base_descriptor[CHIRP_DMAC_CHANNEL],
    &base_descriptor[CHIRP_DMAC_CHANNEL]
  );

  DMAC_descriptor_init
  (
    listenR_dmac_descriptor_settings,
    listenR_len,
    (uint32_t)&ADC0->RESULT.reg,
    (uint32_t)base_listenR_ptr + (sizeof(uint16_t) * listenR_len),
    (uint32_t)&base_descriptor[LISTEN_R_DMAC_CHANNEL],
    &base_descriptor[LISTEN_R_DMAC_CHANNEL]
  );

  DMAC_descriptor_init
  (
    listenL_dmac_descriptor_settings,
    listenL_len,
    (uint32_t)&ADC1->RESULT.reg,
    (uint32_t)base_listenL_ptr + (sizeof(uint16_t) * listenL_len),
    (uint32_t)&base_descriptor[LISTEN_L_DMAC_CHANNEL],
    &base_descriptor[LISTEN_L_DMAC_CHANNEL]
  );

  //DMAC_channel_intenset((ml_dmac_chnum_t)CHIRP_DMAC_CHANNEL, DMAC_0_IRQn, DMAC_CHINTENSET_TCMPL, 1);
  //DMAC_channel_intenset((ml_dmac_chnum_t)LISTEN_R_DMAC_CHANNEL, DMAC_1_IRQn, DMAC_CHINTENSET_TCMPL, 1);
  //DMAC_channel_intenset((ml_dmac_chnum_t)LISTEN_L_DMAC_CHANNEL, DMAC_2_IRQn, DMAC_CHINTENSET_TCMPL, 1);
}

void init_wait_timer(void)
{
  TCC1->CTRLA.bit.PRESCALER = DEFAULT_WAIT_TIMER_PRESCALER;
  TCC1->PER.bit.PER = DEFAULT_WAIT_TIMER_PERIOD;

  EVSYS->USER[EVSYS_ID_USER_TCC1_EV_0].bit.CHANNEL = WAIT_TIMER_START_CHANNEL + 0x01;
  EVSYS->Channel[WAIT_TIMER_START_CHANNEL].CHANNEL.reg = 
  (
    EVSYS_CHANNEL_EDGSEL_RISING_EDGE |
    EVSYS_CHANNEL_PATH_RESYNCHRONIZED |
    EVSYS_CHANNEL_EVGEN(0x00)
  );

  TCC1->EVCTRL.reg = 
  (
    TCC_EVCTRL_TCEI0 |
    TCC_EVCTRL_OVFEO |
    TCC_EVCTRL_EVACT0_RETRIGGER
  );
  
  TCC1->INTENSET.bit.OVF = 0x01;
  NVIC_EnableIRQ(TCC1_0_IRQn);

  TCC1->CTRLBSET.bit.ONESHOT = 0x01;
  while(TCC1->SYNCBUSY.bit.CTRLB)
  {
    /* Wait for sync */
  }
}

void init_exit_timers(void)
{

  TC0->COUNT16.CTRLA.bit.PRESCALER = TC_CTRLA_PRESCALER_DIV1_Val;
  TC0->COUNT16.CTRLA.bit.MODE = TC_CTRLA_MODE_COUNT16_Val;

  EVSYS->USER[EVSYS_ID_USER_TC0_EVU].bit.CHANNEL = EXIT_TIMER_A_START_CHANNEL + 0x01;
  EVSYS->Channel[EXIT_TIMER_A_START_CHANNEL].CHANNEL.reg = 
  (
    EVSYS_CHANNEL_EDGSEL_FALLING_EDGE |
    EVSYS_CHANNEL_PATH_RESYNCHRONIZED |
    //EVSYS_CHANNEL_EVGEN(EVSYS_ID_GEN_DMAC_CH_1)
    EVSYS_CHANNEL_EVGEN(0x00)
  );

  TC0->COUNT16.EVCTRL.reg = 
  (
    TC_EVCTRL_TCEI |
    TC_EVCTRL_EVACT_RETRIGGER
  );

  TC0->COUNT16.INTENSET.bit.OVF = 0x01;
  NVIC_EnableIRQ(TC0_IRQn);

  TC0->COUNT16.CTRLBSET.bit.ONESHOT = 0x01;
  while(TC0->COUNT16.SYNCBUSY.bit.CTRLB)
  {
    /* Wait for sync*/
  }

  TC1->COUNT16.CTRLA.bit.PRESCALER = TC_CTRLA_PRESCALER_DIV1_Val;
  TC1->COUNT16.CTRLA.bit.MODE = TC_CTRLA_MODE_COUNT16_Val;

  EVSYS->USER[EVSYS_ID_USER_TC1_EVU].bit.CHANNEL = EXIT_TIMER_B_START_CHANNEL + 0x01;
  EVSYS->Channel[EXIT_TIMER_B_START_CHANNEL].CHANNEL.reg = 
  (
    EVSYS_CHANNEL_EDGSEL_FALLING_EDGE |
    EVSYS_CHANNEL_PATH_RESYNCHRONIZED |
    //EVSYS_CHANNEL_EVGEN(EVSYS_ID_GEN_DMAC_CH_2)
    EVSYS_CHANNEL_EVGEN(0x00)
  );

  TC1->COUNT16.EVCTRL.reg = 
  (
    TC_EVCTRL_TCEI |
    TC_EVCTRL_EVACT_RETRIGGER
  );

  TC1->COUNT16.INTENSET.bit.OVF = 0x01;
  NVIC_EnableIRQ(TC1_IRQn);

  TC1->COUNT16.CTRLBSET.bit.ONESHOT = 0x01;
  while(TC1->COUNT16.SYNCBUSY.bit.CTRLB)
  {
    /* Wait for sync*/
  }
}

void disable_event_inputs(void)
{
  TC0->COUNT32.EVCTRL.bit.TCEI = 0x00;
  TC1->COUNT32.EVCTRL.bit.TCEI = 0x00;
  TCC1->EVCTRL.bit.TCEI0 = 0x00;
  DMAC->Channel[CHIRP_DMAC_CHANNEL].CHEVCTRL.bit.EVIE = 0x00;
  DMAC->Channel[LISTEN_R_DMAC_CHANNEL].CHEVCTRL.bit.EVIE = 0x00;
  DMAC->Channel[LISTEN_L_DMAC_CHANNEL].CHEVCTRL.bit.EVIE = 0x00;
}

void enable_event_inputs(void)
{

  TC0->COUNT32.EVCTRL.bit.TCEI = 0x01;
  TC1->COUNT32.EVCTRL.bit.TCEI = 0x01;
  TCC1->EVCTRL.bit.TCEI0 = 0x01;
  DMAC->Channel[CHIRP_DMAC_CHANNEL].CHEVCTRL.bit.EVIE = 0x01;
  DMAC->Channel[LISTEN_R_DMAC_CHANNEL].CHEVCTRL.bit.EVIE = 0x01;
  DMAC->Channel[LISTEN_L_DMAC_CHANNEL].CHEVCTRL.bit.EVIE = 0x01;
}

void disable_peripherals(void)
{
  TC_disable(TC0);
  TC_disable(TC1);
  TCC_disable(TCC1);
  ML_DMAC_CHANNEL_DISABLE(CHIRP_DMAC_CHANNEL);
  ML_DMAC_CHANNEL_DISABLE(LISTEN_R_DMAC_CHANNEL);
  ML_DMAC_CHANNEL_DISABLE(LISTEN_L_DMAC_CHANNEL);
}

void enable_peripherals(void)
{
  ML_DMAC_CHANNEL_ENABLE(CHIRP_DMAC_CHANNEL);
  DMAC_suspend_channel(CHIRP_DMAC_CHANNEL);
  ML_DMAC_CHANNEL_ENABLE(LISTEN_R_DMAC_CHANNEL);
  DMAC_suspend_channel(LISTEN_R_DMAC_CHANNEL);
  ML_DMAC_CHANNEL_ENABLE(LISTEN_L_DMAC_CHANNEL);
  DMAC_suspend_channel(LISTEN_L_DMAC_CHANNEL);
  TC_enable(TC0);
  TC_enable(TC1);
  TCC_enable(TCC1);
}

void handle_serial_command(void)
{
  host_action action = (host_action)Serial.read();

  chirp_flag = false;
  start_flag = false;
  update_flag = false;
  
  switch(action)
  {
    case START_JOB:
    {
      chirp_flag = (_Bool)Serial.read();
      start_flag = true;
      break;
    }
    case UPDATE_JOB:
    {
      update_flag = true;
      break;
    }
    case AMP_ENABLE:
    {
      AMP_ENABLE();
      DOTSTAR_SET_GREEN();
      break;
    }
    case AMP_DISABLE:
    {
      AMP_DISABLE();
      DOTSTAR_SET_GREEN();
      break;
    }
    default:
    {
      break;
    }
  }
}

uint16_t determine_chunk_size(void)
{
  uint16_t num_chunks = 2*listen_len/S_CHUNK_SIZE;
  if((2*listen_len) % S_CHUNK_SIZE)
  {
    num_chunks++;
  }
  return num_chunks;
}

void handle_serial_update_command(host_update_action action)
{
  switch(action)
  {
    case UPDATE_BUFFER:
    {
      //SERIAL_WRITE_ACK();
      uint16_t clen, rlen, llen;

      while(Serial.available() < 6)
      {}

      clen = S_READ_HALF_WORD();
      rlen = S_READ_HALF_WORD();
      llen = S_READ_HALF_WORD();

      disable_event_inputs();
      partition_data_buffer(clen, rlen, llen);
      update_transfer_descriptors();
      nchunks = determine_chunk_size();

      update_event_generators();

      enable_event_inputs();
      break;
    }

    case UPDATE_CHIRP:
    {
      while(Serial.available() < 1)
      {}

      if(S_READ_BYTE() == S_DATA)
      {
        char *dptr = (char *)base_chirp_ptr;
        Serial.readBytes(dptr, 2 * chirp_len);
        //SERIAL_WRITE_ACK2();
      }
      break;
    }
    
    case UPDATE_WAIT_TIMER_PERIOD:
    {
      while(Serial.available() < 2)
      {}

      wait_timer_val = S_READ_HALF_WORD();
      TCC_set_period(TCC1, wait_timer_val);
      break;
    }

    case UPDATE_WAIT_TIMER_PRESCALER:
    {
      while(Serial.available() < 1)
      {}

      wait_timer_prescaler = S_READ_BYTE();
      TCC_update_prescaler(TCC1, wait_timer_prescaler);
      break;
    }

    case UPDATE_FINISH:
    {
      update_flag = false;
      break;
    }

  }
}

void setup(void)
{
  Serial.begin(115200);
  //while(!Serial);

  MCLK_init();
  GCLK_init();

  // init amp enable pin and pull high (disables amp)
  peripheral_port_init(&amp_pin);
  port_pmux_disable(&amp_pin);

  dotstar_init();

  AMP_DISABLE();
  DOTSTAR_SET_BLUE();

  // DMAC init
  // zero data buffer
  bzero((void *)&data_buffer[0], sizeof(uint16_t) * MAX_BUFFER_LENGTH);
  //partition_data_buffer(DEFAULT_CHIRP_LENGTH, DEFAULT_LISTEN_LENGTH, DEFAULT_LISTEN_LENGTH);
  partition_data_buffer(DEFAULT_CHIRP_LENGTH, DEFAULT_LISTEN_LENGTH, DEFAULT_LISTEN_LENGTH);
  
  init_exit_timers();
  init_wait_timer();
  init_dmac_channels();

  update_event_generators();
  init_dmac_descriptors();

  nchunks = determine_chunk_size();

  ML_DMAC_ENABLE();

  ML_DMAC_CHANNEL_ENABLE(CHIRP_DMAC_CHANNEL);
  DMAC_suspend_channel(CHIRP_DMAC_CHANNEL);

  ML_DMAC_CHANNEL_ENABLE(LISTEN_R_DMAC_CHANNEL);
  DMAC_suspend_channel(LISTEN_R_DMAC_CHANNEL);

  ML_DMAC_CHANNEL_ENABLE(LISTEN_L_DMAC_CHANNEL);
  DMAC_suspend_channel(LISTEN_L_DMAC_CHANNEL);

  // DAC init
  DAC_init();
  DAC0_init();
  peripheral_port_init(&dac_pin);
  DAC_enable();
  DAC0_enable();

  // DAC timer init
  TCC2_init();
  peripheral_port_init(&tcc0_pin);
  TCC_enable(TCC2);
  
  // ADC init
  ADC0_init();
  peripheral_port_init(&adc0_pin);
  ADC_enable(ADC0);
  ADC_swtrig_start(ADC0);
  
  ADC1_init();
  peripheral_port_init(&adc1_pin);
  ADC_enable(ADC1);
  ADC_swtrig_start(ADC1);

  ADC_flush(ADC0);
  ADC_flush(ADC1);

  //uint32_t rdy = EVSYS->READYUSR.reg;

  TCC_enable(TCC1);
  //TCC_unlock_update(TCC1);
  TC_enable(TC0);
  TC_enable(TC1);

  dstate = IDLE;
}

_Bool exit_intflag_A = false;
_Bool exit_intflag_B = false;
_Bool wait_intflag = false;
_Bool listen_R_intflag = false;
_Bool listen_L_intflag = false;
_Bool chirp_intflag = false;
_Bool left_done = false;
_Bool right_done = false;

_Bool check = false;
_Bool checkA = false;
_Bool checkB = false;

void loop(void)
{
  switch(dstate)
  {
    case IDLE: 
    {
      if(S_COMMAND_AVAILABLE())
      {
        handle_serial_command();

        if(update_flag)
        {
          dstate = UPDATE;
          disable_peripherals();
          //SERIAL_WRITE_ACK();
        }

        else if(start_flag)
        {
          if(chirp_flag)
          {
            CHIRP_START_SOFT_TRIGGER();
          }
          LISTEN_START_SOFT_TRIGGER();
          dstate = BUSY;
        }
      }
      break;
    }

    case BUSY:
    {
      if(exit_intflag_A & exit_intflag_B)
      {
        if(listenL_len == 0 && listenR_len == 0)
        {
          dstate = IDLE;
        }
        else
        {
          dstate = SEND;
        }
        exit_intflag_A = exit_intflag_B = false;
      }
      break;
    }

    case UPDATE:
    {
      if(S_COMMAND_AVAILABLE())
      {
        host_update_action action = (host_update_action)Serial.read();
        //SERIAL_WRITE_ACK();
        handle_serial_update_command(action);

        if(!update_flag)
        {
          enable_peripherals();
          dstate = IDLE;
          S_WRITE_UPDATE_COMPLETE();
          check = true;
        }
      }
      break;
    }

    case SEND:
    {
      if(Serial.availableForWrite())
      {
        uint8_t *cptr = (uint8_t *)base_listen_ptr;
        for(uint16_t i=0; i < nchunks; i++, cptr += S_CHUNK_SIZE)
        {
          Serial.write(cptr, sizeof(uint8_t) * S_CHUNK_SIZE);
        }
        dstate = IDLE;
      }
      break;
    }
  }
}

int idx =0;
void loop_alt(void)
{
  if(exit_intflag_A)
  {
    //EVSYS->SWEVT.bit.CHANNEL1 = 0x01;
    Serial.println("Got exit timer A");
    exit_intflag_A = false;
    right_done = true;
  }

  if(exit_intflag_B)
  {
    //EVSYS->SWEVT.bit.CHANNEL2 = 0x01;
    Serial.println("Got exit timer B");
    exit_intflag_B = false;
    left_done = true;
  }

  if(wait_intflag)
  {
    Serial.println("Got wait");
    wait_intflag = false;
  }

  if(chirp_intflag)
  {
    Serial.println("got chirp");
    chirp_intflag = false;
    Serial.printf("%x, %x, %x\n", EVSYS->BUSYCH.reg, EVSYS->READYUSR.reg, EVSYS->Channel[LISTEN_R_START_CHANNEL].CHSTATUS.reg);
  }

  if(listen_R_intflag)
  {
    Serial.println("got listen right");
    listen_R_intflag = false;
  }

  if(listen_L_intflag)
  {
    Serial.println("got listen left");
    listen_L_intflag = false;
  }

  if(left_done & right_done)
  {
    uint16_t *tmpR = (uint16_t *)base_listenR_ptr;
    uint16_t *tmpL = (uint16_t *)base_listenL_ptr;

    for(; tmpR < base_listenR_ptr + 30; tmpR++)
    {
      Serial.printf("%d, ", *tmpR);
    }
    Serial.println();

    for(; tmpL < base_listenL_ptr + 30; tmpL++)
    {
      Serial.printf("%d, ", *tmpL);
    }
    Serial.println();
    left_done = false;
    right_done = false;

    //partition_data_buffer(DEFAULT_CHIRP_LENGTH, DEFAULT_LISTEN_LENGTH, 0);
    //init_dmac_descriptors();
    //update_event_generators();

    //EVSYS->SWEVT.bit.CHANNEL0 = 0x01;
    //EVSYS->SWEVT.bit.CHANNEL5 = 0x01;
  }

}

void TC0_Handler(void)
{
  if(ML_TC_OVF_INTFLAG(TC0))
  {
    exit_intflag_A = true;

    ML_TC_OVF_CLR_INTFLAG(TC0);
  }

}

void TC1_Handler(void)
{
  if(ML_TC_OVF_INTFLAG(TC1))
  {
    exit_intflag_B = true;
    ML_TC_OVF_CLR_INTFLAG(TC1);
  }
}

void DMAC_0_Handler(void)
{
  chirp_intflag = true;
  DMAC->Channel[0].CHINTFLAG.reg = DMAC_CHINTFLAG_MASK;
}

void DMAC_1_Handler(void)
{
  listen_R_intflag = true;
  DMAC->Channel[1].CHINTFLAG.reg = DMAC_CHINTFLAG_MASK;
}

void DMAC_2_Handler(void)
{
  listen_L_intflag = true;
  DMAC->Channel[2].CHINTFLAG.reg = DMAC_CHINTFLAG_MASK;
}
/*
void TCC1_1_Handler(void)
{
  dmac_intflag = true;
  TCC1->INTFLAG.reg = TCC_INTFLAG_MASK;
}*/

void TCC1_0_Handler(void)
{
  if(TCC1->INTFLAG.bit.OVF)
  {
    wait_intflag = true;
    TCC1->INTFLAG.reg = TCC_INTFLAG_MASK;
  }
}
