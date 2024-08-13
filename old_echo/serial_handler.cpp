/*
 * Author: Ben Westcott
 * Date created: 12/21/23
 */
#include <stdbool.h>
#include <serial_handler.hpp>

typedef enum _rx_state { WAIT, ACCEPT, ESCAPE } rx_state;

void init_serial_handler(void)
{
    Serial.begin(SERIAL_BAUD);
   //while(!Serial);
 //   DOTSTAR_SET_LIGHT_GREEN();
}

_Bool get_frame(uint8_t new_char)
{
    static rx_state state = WAIT;
    static uint8_t raw_buf[SER_BUF_LEN];
    static uint8_t frame_end = 0;

    uint8_t raw_char = new_char;

    switch(state)
    {
        case WAIT:
        {
            if(raw_char == SER_FRAME_START)
            {
                state = ACCEPT;
            }
            break;
        }
        case ACCEPT:
        {
            if(raw_char == SER_FRAME_START)
            {
                frame_end = 0;
                state = WAIT;
            }
            if(raw_char == SER_ESC)
            {
                state = ESCAPE;
            }
            else
            {
                raw_buf[frame_end++] = raw_char;
            }
            break;
        }
        case ESCAPE:
        {
            raw_buf[frame_end++] = raw_char ^ SER_XOR;
            state = ACCEPT;
            break;
        }
    }

    if(frame_end == SER_BUF_LEN)
    {
        //memcpy((void *)rx_buffer, (const void *)raw_buf, sizeof(raw_buf));
        frame_end = 0;
        state = WAIT;
        return true;
    }
    return false;
}

uint8_t decode_frame(uint8_t src[SER_RAW_BUF_LEN], uint8_t dst[SER_BUF_LEN])
{
    rx_state state = ACCEPT;

    uint8_t tmp_buffer[SER_BUF_LEN];
    uint8_t *rptr = src;
    uint8_t *wptr = tmp_buffer;

    uint16_t n = 0;

    uint8_t rx_frame_type = RX_ERR;

    if(*(rptr++) != SER_FRAME_START)
    {
        return RX_ERR;
    }

    rx_frame_type = *(rptr++);

    for(; n < SER_RAW_BUF_LEN; n++, rptr++)
    {
        uint8_t b = *rptr;
        if(state == ACCEPT)
        {
            if(b == SER_FRAME_START)
            {
                return RX_ERR;
            }
            if(b == SER_FRAME_END)
            {
                break;
            }

            if(b == SER_ESC)
            {
                state = ESCAPE;
            }
            else
            {
                *(wptr++) = b;
            }
            continue;
        }

        if(state == ESCAPE)
        {
            *(wptr++) = (b ^ SER_XOR);
            state = ACCEPT;
        }
    }

    memcpy((void *)dst, (const void *)tmp_buffer, sizeof(tmp_buffer));
    return rx_frame_type;
}

uint8_t w_read_loop(uint8_t dst[SER_BUF_LEN])
{
    static uint8_t raw_buf[SER_RAW_BUF_LEN];
    static uint16_t frame_idx = 0;

    if(frame_idx == SER_RAW_BUF_LEN)
    {
        frame_idx = 0;
        return decode_frame(raw_buf, dst);
    }

    if(Serial.available())
    {
        raw_buf[frame_idx++] = (uint8_t)Serial.read();
    }

    return RX_NONE;
}

uint8_t wb_read_loop(uint8_t dst[SER_BUF_LEN])
{
    uint8_t raw_buf[SER_RAW_BUF_LEN];
    if(Serial.available())
    {
        Serial.readBytes((char *)raw_buf, SER_RAW_BUF_LEN);
        return decode_frame(raw_buf, dst);
    }
    return RX_NONE;
}

void write_buffer(uint8_t src[SER_BUF_LEN], uint8_t frame_type)
{

    uint8_t *ptr = src;

    char raw_buf[(2 * SER_BUF_LEN) + 3];
    uint16_t n = 0;

    raw_buf[n++] = SER_FRAME_START;
    raw_buf[n++] = frame_type;

    for(uint16_t i=0; i < SER_BUF_LEN; i++, ptr++)
    {
        uint8_t b = *ptr;
        if(b == SER_FRAME_START || b == SER_FRAME_END || b == SER_ESC)
        {
            raw_buf[n++] = SER_ESC;
            raw_buf[n++] = b ^ SER_XOR;
        }
        else
        {
            raw_buf[n++] = b;
        }

    }

    raw_buf[n] = SER_FRAME_END;
    Serial.write(raw_buf, sizeof(raw_buf));
}


