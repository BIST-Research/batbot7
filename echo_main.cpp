#include <Arduino.h>
#include <ml_clocks.h>
#include <ml_dac_common.h>
#include <ml_dac0.h>
#include <ml_dmac.h>
#include <ml_port.h>
#include <ml_tcc_common.h>
#include <ml_tcc2.h>
#include <ml_eic.h>
#include <ml_tc_common.h>
#include <ml_tc2.h>
#include <CRC32.h>

// 2**15
#define EMIT_BUF_LEN 65000


uint32_t calcHashCRC32(uint16_t* array, size_t length){
  CRC32 crc;
  for (size_t i = 0; i < length; i++){
    crc.update(array[i]);
  }
  return crc.finalize();
}



static uint16_t chirp_out_buffer[EMIT_BUF_LEN];

uint32_t init_chirp_buffer(void)
{
  bzero((void *)chirp_out_buffer, sizeof(uint16_t) * EMIT_BUF_LEN);
  return (uint32_t)&chirp_out_buffer[0] + EMIT_BUF_LEN * sizeof(uint16_t);
}


static DmacDescriptor base_descriptor[1] __attribute__((aligned(16)));
static volatile DmacDescriptor wb_descriptor[1] __attribute__((aligned(16)));

// D4 --> PA14
const ml_pin_settings dac_sample_timer_pin = {PORT_GRP_A, 21, PF_G, PP_ODD, OUTPUT_PULL_DOWN, DRIVE_OFF};
// D10 --> PA20
const ml_pin_settings amp_pin = {PORT_GRP_A, 20, PF_A, PP_EVEN, OUTPUT_PULL_DOWN, DRIVE_ON};
// A0 --> PA02
const ml_pin_settings dac_pin = {PORT_GRP_A, 2, PF_B, PP_EVEN, ANALOG, DRIVE_ON};

const ml_pin_settings emit_trigger_pin = {PORT_GRP_A, 16, PF_A, PP_EVEN, INPUT_PULL_DOWN, DRIVE_OFF};

#define AMP_DISABLE() (logical_set(&amp_pin))
#define AMP_ENABLE() (logical_unset(&amp_pin))

const uint32_t chirp_out_dmac_channel_settings = DMAC_CHCTRLA_BURSTLEN_SINGLE | //check when testing evsys
                                                 DMAC_CHCTRLA_TRIGACT_BURST |
                                                 //DMAC_CHCTRLA_TRIGSRC(DAC_DMAC_ID_EMPTY_0);
                                                 DMAC_CHCTRLA_TRIGSRC(TCC0_DMAC_ID_OVF);

const uint16_t chirp_out_dmac_descriptor_settings = DMAC_BTCTRL_VALID |
                                           //         DMAC_BTCTRL_EVOSEL_BURST | //check when testing evsys
                                                    DMAC_BTCTRL_BLOCKACT_BOTH | //check when testing evsys
                                                    DMAC_BTCTRL_BEATSIZE_HWORD |
                                                    DMAC_BTCTRL_SRCINC;

uint32_t chirp_out_source_address;

void dac_sample_timer_init(void)
{
  TCC_disable(TCC0);
  TCC_swrst(TCC0);

  TCC0->CTRLA.reg = 
  (
    //  TCC_CTRLA_PRESCALER_DIV2 |
      TCC_CTRLA_PRESCSYNC_PRESC
  );

  TCC0->WAVE.reg = TCC_WAVE_WAVEGEN_NFRQ;

  // 12 MHz / (2 * 6) = 1 MHz
  TCC_set_period(TCC0, 11);
  TCC_channel_capture_compare_set(TCC0, 1, 3);

  //peripheral_port_init(PORT_PMUX_PMUXE(PF_E), 7, OUTPUT_PULL_DOWN, DRIVE_ON);

  TCC_enable(TCC0);

  peripheral_port_init(&dac_sample_timer_pin);
}

#define DAC_DMAC_CHANNEL DMAC_CH0
#define DAC_DMAC_PRILVL PRILVL0

void dac_init(void)
{
  // Disable DAC
  DAC->CTRLA.bit.ENABLE = 0;
  DAC->CTRLA.bit.SWRST = 1;
  while (DAC->SYNCBUSY.bit.ENABLE || DAC->SYNCBUSY.bit.SWRST);

  // Use an external reference voltage (see errata; the internal reference is busted)
  DAC->CTRLB.reg = DAC_CTRLB_REFSEL_VREFPB;
  while (DAC->SYNCBUSY.bit.ENABLE || DAC->SYNCBUSY.bit.SWRST);

  DAC->DACCTRL[0].reg |= DAC_DACCTRL_CCTRL_CC12M;

  DAC->DACCTRL[0].bit.ENABLE = 1;
  while(DAC->SYNCBUSY.bit.ENABLE || DAC->SYNCBUSY.bit.SWRST);

  DMAC_channel_init
  (
    DAC_DMAC_CHANNEL,
    chirp_out_dmac_channel_settings,
    DAC_DMAC_PRILVL
  );


  //check when testing evsys
  DMAC_channel_intenset(DAC_DMAC_CHANNEL, DMAC_2_IRQn, DMAC_CHINTENSET_TCMPL, 0);

  DMAC_descriptor_init
  (
    chirp_out_dmac_descriptor_settings,
    EMIT_BUF_LEN,
    chirp_out_source_address,
    (uint32_t) &DAC->DATA[0].reg,
    (uint32_t) &base_descriptor[DAC_DMAC_CHANNEL],
    &base_descriptor[DAC_DMAC_CHANNEL]
  );

  peripheral_port_init(&dac_pin);
}



enum ECHO_SERIAL_CMD{
  NONE = 0,
  EMIT_CHIRP = 1,
  CHIRP_DATA = 2,
  ACK_REQ = 3,
  ACK = 4,
  ERROR = 100,
  CHIRP_DATA_TOO_LONG = 6,
  GET_MAX_UINT16_CHIRP_LEN = 7,
  START_AMP = 8,
  STOP_AMP = 9,
  CLEAR_SERIAL = 10
};

ECHO_SERIAL_CMD cmd = ECHO_SERIAL_CMD::NONE;

void drain_buffer(){
  DOTSTAR_SET_ORANGE();
  while(Serial.available()){
    Serial.read();
  }
  DOTSTAR_SET_LIGHT_RED();
}

void setup()
{
  Serial.begin(960000);
  chirp_out_source_address = init_chirp_buffer();

  MCLK_init();
  GCLK_init();

  DMAC_init(&base_descriptor[DAC_DMAC_CHANNEL],&wb_descriptor[DAC_DMAC_CHANNEL]);
  dotstar_init();



  dac_init();
  dac_sample_timer_init();
  DAC_enable();

 TCC_enable(TCC2);
 TCC_force_stop(TCC2);


  ML_DMAC_ENABLE();
  ML_DMAC_CHANNEL_ENABLE(DAC_DMAC_CHANNEL);
  ML_DMAC_CHANNEL_SUSPEND(DAC_DMAC_CHANNEL);

  DOTSTAR_SET_OFF();


  
}

bool serial_error = false;
#define WAIT_TIME 2000
#define ACK_SEND_SIZE 250
void loop()
{
  // put your main code here, to run repeatedly:
  // Serial.println("running");

  if (Serial.available() >= 1){
    cmd = (ECHO_SERIAL_CMD)Serial.read();


    switch (cmd)
    {
    case ECHO_SERIAL_CMD::ACK:{

      break;
    }

    case ECHO_SERIAL_CMD::ACK_REQ:{
        Serial.write(ECHO_SERIAL_CMD::ACK);
        DOTSTAR_SET_BLUE();
      break;
    }
    
    case ECHO_SERIAL_CMD::CHIRP_DATA:{
      // DOTSTAR_SET_PINK();

      unsigned long recv_time = millis();
      while(Serial.available() < 1 && millis() - recv_time < WAIT_TIME);
      if (millis() - recv_time > WAIT_TIME+100 && Serial.available() <= 1){
        Serial.write(ECHO_SERIAL_CMD::ERROR);
        Serial.flush();
        DOTSTAR_SET_ORANGE();
        serial_error = true;
        return;
      }

      // DOTSTAR_SET_LIGHT_BLUE();

  
      uint16_t chirp_len = (uint8_t)Serial.read();
      chirp_len |= Serial.read()<<8;
      if (chirp_len > (uint16_t) EMIT_BUF_LEN){
        Serial.write(ECHO_SERIAL_CMD::CHIRP_DATA_TOO_LONG);
        Serial.flush();
        DOTSTAR_SET_RED();
        serial_error = true;
        return;
      }

      Serial.write(chirp_len&0xff);
      Serial.write((chirp_len>>8)&0xff);
      Serial.flush();

      // DOTSTAR_SET_LIGHT_BLUE();
      // pi waits for ack before flooding with data since serial buffer is so small
      Serial.write(ECHO_SERIAL_CMD::ACK);
      Serial.flush();

      for (int i = 0; i < EMIT_BUF_LEN; i++){
        chirp_out_buffer[i] = 0;
      }
      

      recv_time = millis();
      for(int i = 0; i < chirp_len;i++){

        while(Serial.available() < 2 && millis() - recv_time < WAIT_TIME);
        if(millis() - recv_time+100 > WAIT_TIME){
          Serial.flush();
          Serial.write(ECHO_SERIAL_CMD::ERROR);
          Serial.flush();
          DOTSTAR_SET_YELLOW();
          serial_error = true;
          return;
        }
        recv_time = millis();
        chirp_out_buffer[i] = (uint8_t)Serial.read();
        chirp_out_buffer[i] |= (uint8_t) Serial.read() <<8;
      }

      DOTSTAR_SET_LIGHT_GREEN();

      recv_time = millis();
      while(Serial.available() == 0 && millis() - recv_time < WAIT_TIME);
      if (millis() - recv_time+100 > WAIT_TIME){
        Serial.flush();
        Serial.write(ECHO_SERIAL_CMD::ERROR);
        Serial.flush();
        DOTSTAR_SET_RED();
        serial_error = true;
        return;
      }

      DOTSTAR_SET_PINK();
      cmd = (ECHO_SERIAL_CMD)Serial.read();
      if (cmd != ECHO_SERIAL_CMD::ACK_REQ){
        Serial.flush();
        Serial.write(ECHO_SERIAL_CMD::ERROR);
        Serial.flush();
        DOTSTAR_SET_RED();
        serial_error = true;
        return;
      }

      Serial.write(ECHO_SERIAL_CMD::ACK);
      Serial.flush();
      uint32_t crc_hash = calcHashCRC32(chirp_out_buffer,chirp_len);
      Serial.write(crc_hash&0xff);
      Serial.write((crc_hash >>8)&0xff);
      Serial.write((crc_hash >>16)&0xff);
      Serial.write((crc_hash >>24)&0xff);
      Serial.flush();
      // for(int i = 0; i < chirp_len; i++){
      //   Serial.write(chirp_out_buffer[i]&0xff);
      //   Serial.write(chirp_out_buffer[i]>>8&0xff);
      //   if (i%64 == 0){
      //     Serial.flush();
      //   }
      // }
 

      DOTSTAR_SET_GREEN();
    break;
    }
    case ECHO_SERIAL_CMD::EMIT_CHIRP:{
      ML_DMAC_CHANNEL_RESUME(DAC_DMAC_CHANNEL);
      // DMAC->SWTRIGCTRL.bit.SWTRIG0 = 0x01;
      
      Serial.write(ECHO_SERIAL_CMD::ACK);

      DOTSTAR_SET_LIGHT_GREEN();
      break;
    }
    case ECHO_SERIAL_CMD::ERROR:{

      break;
    }
    case ECHO_SERIAL_CMD::GET_MAX_UINT16_CHIRP_LEN:{
      Serial.write(ECHO_SERIAL_CMD::GET_MAX_UINT16_CHIRP_LEN);
      Serial.write(EMIT_BUF_LEN &0xff);
      Serial.write(EMIT_BUF_LEN >> 8 &0xff);
      Serial.flush();
      DOTSTAR_SET_LIGHT_GREEN();
      serial_error = true;
      break;
    }
    default:
      Serial.write(ECHO_SERIAL_CMD::ERROR);
      Serial.flush();
      DOTSTAR_SET_RED();
      serial_error = true;
      break;
    }

    // Serial.flush();
  }
  Serial.flush();
  
  if (serial_error){
    delay(5);
    drain_buffer();
    serial_error = false;
  }
}


void DMAC_2_Handler(void)
{
  
  if(DMAC->Channel[DAC_DMAC_CHANNEL].CHINTFLAG.bit.TCMPL)
  {

    // DOTSTAR_SET_YELLOW();

    ML_DMAC_CHANNEL_CLR_SUSP_INTFLAG(DAC_DMAC_CHANNEL);
    DMAC->Channel[DAC_DMAC_CHANNEL].CHINTFLAG.bit.TCMPL = 0x01;

  }

}