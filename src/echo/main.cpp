#include <Arduino.h>
#include <ml_clocks.h>
#include <ml_port.h>
#include <ml_tc_common.h>
#include <ml_tc2.h>

#include <serial_handler.hpp>
#include <record.hpp>
#include <emit.hpp>

//#define BUILD_RECORD
//#define BUILD_EMIT
//#define SERIAL_BLOCK

uint8_t rx_buffer[SER_BUF_LEN];
uint8_t tx_buffer[SER_BUF_LEN];
uint16_t ser_action;
uint8_t rx_frame_type;

void setup(void)
{
    MCLK_init();
    GCLK_init();

    dotstar_init();
    init_serial_handler();

    TC2_init();
    TC2_intset(true, false, false, false, true, 1);
    TC_enable(TC2);
    TC_force_stop(TC2);
    
    ser_action = 0;
    rx_frame_type = RX_NONE;

#if defined(BUILD_RECORD)
    record_setup();
#elif defined(BUILD_EMIT)
    emit_setup();
#endif //BUILD_RECORD
}

void loop(void)
{

#if defined(SERIAL_BLOCK)
    while(!Serial);
#endif

#if defined(BUILD_RECORD)
    ser_action = record_loop(rx_buffer, rx_frame_type, tx_buffer);
#elif defined(BUILD_EMIT)
    ser_action = emit_loop(rx_buffer, rx_frame_type, tx_buffer);
#endif //BUILD_RECORF


    if(ser_action & SER_RET_WRITE)
    {
        if(Serial.availableForWrite())
        {        
            uint8_t tx_frame_type = SER_RET_FRAME(ser_action);
            write_buffer(tx_buffer, tx_frame_type);
        }

    }

    if(ser_action & SER_RET_READ)
    {
        if((rx_frame_type = w_read_loop(rx_buffer)) == RX_ERR)
        {
            TC_force_retrigger(TC2);
        }
    }


}

void TC2_Handler(void)
{
    static _Bool blinker = true;

    if(ML_TC_OVF_INTFLAG(TC2))
    {
        if(blinker)
        {
            DOTSTAR_SET_RED();
        } else
        {
            DOTSTAR_SET_OFF();
        }

    }

    blinker = !blinker;
    ML_TC_CLR_INTFLAGS(TC2);
}

