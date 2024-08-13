/**
 * @file
 * 
 * This file does something???
 */

#include <Arduino.h>
#include <ADC.h>

#include <AnalogBufferDMA.h>
#include <DMAChannel.h>

#define ADC_DUAL_ADCS

const int readPin_adc_0 = A0; /** The pin for adc 0 */
const int readPin_adc_1 = A2; /** The pin for adc 1 */
const int emit_chirp_pin = 17;  /** This pin does something */
const int itsy_emitting_chirp = 18; /** This pin does something */

ADC *adc = new ADC();

extern void dumpDMA_structures(DMABaseClass *dmabc);

// Going to try two buffers here  using 2 dmaSettings and a DMAChannel
const uint32_t buffer_size = 1000;
DMAMEM static volatile uint16_t __attribute__((aligned(32)))
dma_adc_buff1[buffer_size];
DMAMEM static volatile uint16_t __attribute__((aligned(32)))
dma_adc_buff2[buffer_size];
AnalogBufferDMA abdma1(dma_adc_buff1, buffer_size, dma_adc_buff2, buffer_size);

DMAMEM static volatile uint16_t __attribute__((aligned(32)))
dma_adc_buff2_1[buffer_size];
DMAMEM static volatile uint16_t __attribute__((aligned(32)))
dma_adc_buff2_2[buffer_size];
AnalogBufferDMA abdma2(dma_adc_buff2_1, buffer_size, dma_adc_buff2_2, buffer_size);

#define UART_BUF_SIZE buffer_size * 2
volatile uint16_t uart_send_buffer[UART_BUF_SIZE];

void GetData(bool);

// void print_debug_information();

// void ProcessAnalogData(AnalogBufferDMA *pabdma, int8_t adc_num);

/**
 * @brief Enum containing host serial commands
 */
enum LISTENER_SERIAL_CMD
{
  NONE = 0,           /** No command from host */
  START_LISTEN = 1,   /** start recording */
  STOP_LISTEN = 2,    /** stop recording */
  ACK_REQ = 3,        /** acknowledge request */
  ACK = 4,            /** acknowledge */
  ERROR = 100         /** error */
};

/**
 * @brief
 * 
 * Long description
 * 
 * @param send a bool
 */
void GetData(bool send)
{
  volatile uint16_t *adc0_pbuffer = abdma1.bufferLastISRFilled();
  volatile uint16_t *adc0_end_pbuffer = abdma1.bufferCountLastISRFilled() + adc0_pbuffer;

  volatile uint16_t *adc1_pbuffer = abdma2.bufferLastISRFilled();
  volatile uint16_t *adc1_end_pbuffer = abdma2.bufferCountLastISRFilled() + adc1_pbuffer;

  if ((uint32_t)adc0_pbuffer >= 0x20200000u)
    arm_dcache_delete((void *)adc0_pbuffer, sizeof(dma_adc_buff1));
  if ((uint32_t)adc1_pbuffer >= 0x20200000u)
    arm_dcache_delete((void *)adc1_pbuffer, sizeof(dma_adc_buff1));

  // uart_send_buffer[0] = 0x00;
  // uart_send_buffer[1] = ('L' << 8) | 'E';
  // size_t index = 3;
  size_t index = 0;

  while (adc0_pbuffer < adc0_end_pbuffer)
  {
    uart_send_buffer[index] = *adc0_pbuffer;
    adc0_pbuffer++;
    index += 2;
  }
  // uart_send_buffer[2] = index;

  // index = UART_BUF_SIZE/2;
  // uart_send_buffer[index] = ('R'<<8)
  index = 1;
  while (adc1_pbuffer < adc1_end_pbuffer)
  {
    uart_send_buffer[index] = *adc1_pbuffer;
    adc1_pbuffer++;
    index += 2;
  }

  index = UART_BUF_SIZE;

  // Serial.println(abdma1.interruptDeltaTime());

  abdma1.clearInterrupt();
  abdma2.clearInterrupt();

  // send data
  if (!send)
  {
    // clear flags
    Serial.flush();
    return;
  }

  for (size_t i = 0; i < index; i++)
  {
    Serial.write(uart_send_buffer[i] & 0xff);
    Serial.write(uart_send_buffer[i] >> 8 & 0xff);
    if (i % 64 == 0)
    {
      Serial.send_now();
      Serial.flush();
    }
  }
  Serial.send_now();
  Serial.flush();
}

void setup()
{
  // Serial.println("Starting");

  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(readPin_adc_0, INPUT_DISABLE); // Not sure this does anything for us
  pinMode(readPin_adc_1, INPUT_DISABLE);
  pinMode(emit_chirp_pin,OUTPUT);
  pinMode(itsy_emitting_chirp,INPUT_PULLDOWN);
  

  // Setup both ADCs
  adc->adc0->setAveraging(0);   // set number of averages
  adc->adc0->setResolution(10); // set bits of resolution
  adc->adc0->setSamplingSpeed(ADC_SAMPLING_SPEED::VERY_HIGH_SPEED);
  adc->adc0->setConversionSpeed(ADC_CONVERSION_SPEED::VERY_HIGH_SPEED);

  adc->adc1->setAveraging(0);   // set number of averages
  adc->adc1->setResolution(10); // set bits of resolution
  adc->adc1->setSamplingSpeed(ADC_SAMPLING_SPEED::VERY_HIGH_SPEED);
  adc->adc1->setConversionSpeed(ADC_CONVERSION_SPEED::VERY_HIGH_SPEED);

  // enable DMA and interrupts
  // Serial.println("before enableDMA"); Serial.flush();

  // setup a DMA Channel.
  // Now lets see the different things that RingbufferDMA setup for us before
  abdma1.init(adc, ADC_0 /*, DMAMUX_SOURCE_ADC_ETC*/);

  abdma2.init(adc, ADC_1 /*, DMAMUX_SOURCE_ADC_ETC*/);

  // Start the dma operation..
  adc->adc0->startSingleRead(
      readPin_adc_0);             // call this to setup everything before the Timer starts,
                                  // differential is also possible
  adc->adc0->startTimer(2000000); // frequency in Hz

  // // Start the dma operation..
  adc->adc1->startSingleRead(
      readPin_adc_1); // call this to setup everything before the Timer starts,
  //                                // differential is also possible
  adc->adc1->startTimer(2000000); // frequency in Hz

  // adc->startSynchronizedSingleRead(readPin_adc_0,readPin_adc_1);

  digitalWriteFast(LED_BUILTIN, LOW);
}


volatile bool sendData = false;
unsigned long sendStartTime = 0;
uint16_t times_to_send = 0;
volatile uint16_t times_sent = 0;

void loop()
{

  // Maybe only when both have triggered?
  if (abdma1.interrupted() && abdma2.interrupted())
  {
    GetData(sendData);
  }


  if (Serial.available())
  {
    LISTENER_SERIAL_CMD cmd = (LISTENER_SERIAL_CMD)Serial.read();

    switch (cmd)
    {
    case LISTENER_SERIAL_CMD::ACK:
    {
    }
    break;
    case LISTENER_SERIAL_CMD::ACK_REQ:
    {
      Serial.flush();
      Serial.write(LISTENER_SERIAL_CMD::ACK);
      Serial.send_now();
      Serial.flush();
      sendData = false;
      digitalWriteFast(emit_chirp_pin,LOW);
      digitalWriteFast(LED_BUILTIN, LOW);
      abdma1.clearInterrupt();
      abdma2.clearInterrupt();
      Serial.flush();
    }
    break;
    case LISTENER_SERIAL_CMD::START_LISTEN:
    {
      sendData = true;
      digitalWriteFast(LED_BUILTIN, HIGH);
      digitalWriteFast(emit_chirp_pin,HIGH);



      while (true)
      {
        if(digitalReadFast(itsy_emitting_chirp) == HIGH){
          break;
        }
      }
      

      abdma1.clearInterrupt();
      abdma2.clearInterrupt();
      // Serial.flush();
      sendStartTime = millis();
    }
    break;
    case LISTENER_SERIAL_CMD::STOP_LISTEN:
    {
      sendData = false;
      digitalWriteFast(LED_BUILTIN, LOW);
      digitalWriteFast(emit_chirp_pin,LOW);
      abdma1.clearInterrupt();
      abdma2.clearInterrupt();
      Serial.flush();
    }
    break;
    case LISTENER_SERIAL_CMD::ERROR:
    {
    }
    break;
    default:
      break;
    }

    // if (sendData)
    // {
    //   if (millis() - sendStartTime > 10 * 1000)
    //   {
    //     sendData = false;
    //     digitalWriteFast(LED_BUILTIN, LOW);
    //     digitalWriteFast(emit_chirp_pin,LOW);
    //     abdma1.clearInterrupt();
    //     abdma2.clearInterrupt();
    //     Serial.flush();
    //   }
    // }
  }
}