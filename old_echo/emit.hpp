/*
 * Author: Ben Westcott
 * Date created: 1/18/24
 */

#ifndef EMIT_H
#define EMIT_H

#include <Arduino.h>

void emit_setup(void);
uint16_t emit_loop
(
    uint8_t rx_buffer[SER_BUF_LEN], 
    uint8_t rx_frame_type, 
    uint8_t tx_buffer[SER_BUF_LEN]
);

#endif // EMIT_H