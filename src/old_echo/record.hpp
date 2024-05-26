/*
 * Author: Ben Westcott
 * Date created: 1/9/24
 */

#ifndef RECORD_H
#define RECORD_H

#include <Arduino.h>
#include <serial_handler.hpp>

void record_setup(void);
uint16_t record_loop
(
    uint8_t rx_buffer[SER_BUF_LEN], 
    uint8_t rx_frame_type, 
    uint8_t tx_buffer[SER_BUF_LEN]
);

#endif // RECORD_H