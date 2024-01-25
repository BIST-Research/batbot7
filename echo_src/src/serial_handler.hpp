/*
 * Author: Ben Westcott
 * Date created: 1/9/24
 */

#ifndef SERIAL_HANDLER_H
#define SERIAL_HANDLER_H

#include <Arduino.h>
#include <ml_port.h>

#define B_TO_H(b1, b2) (((uint16_t)b1 << 8) | ((uint16_t) b2))

#define SERIAL_BAUD 460800
#define SER_BUF_LEN 256
#define SER_RAW_BUF_LEN (2*SER_BUF_LEN + 3)

#define SER_RET_READ 0b01
#define SER_RET_READ_MASK 1

#define SER_RET_WRITE 0b10
#define SER_RET_WRITE_MASK 2

#define TX_SONAR_RECORD_FRAME 0x65

#define SER_RET_FRAME_MASK 0xff00
#define SER_RET_FRAME(ret_val) ((uint8_t)((ret_val & SER_RET_FRAME_MASK) >> 8))

#define RX_ERR  0x40
#define RX_NONE 0x41
#define RX_MSG_FRAME 0x42
#define RX_DATA_FRAME 0x43

#define SER_FRAME_START 0x7e
#define SER_FRAME_END 0x7f
#define SER_ESC 0x7d
#define SER_XOR 0x20

void init_serial_handler(void);
void write_buffer(uint8_t src[SER_BUF_LEN], uint8_t frame_type);
uint8_t decode_frame(uint8_t src[SER_RAW_BUF_LEN], uint8_t dst[SER_BUF_LEN]);
uint8_t w_read_loop(uint8_t dst[SER_BUF_LEN]);
uint8_t wb_read_loop(uint8_t dst[SER_BUF_LEN]);



#endif // SERIAL_HANDLER_H