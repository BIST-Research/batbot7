#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <termios.h>
#include <unistd.h>

#include <cstring>
#include <string.h>
#include <iostream>

#include "serial_object_uart_linux.hpp"

SerialObject_UART_Win::SerialObject_UART_Win(std::string portName)
{
}

SerialObject_UART_Win::~SerialObject_UART_Win()
{
}

int SerialObject_UART_Win::set_attributes(int speed, int parity) {
  return 0;
}

void SerialObject_UART_Win::enable_blocking(bool should_block) {

}

void SerialObject_UART_Win::writeBytes(const uint8_t* bytes, int numBytes) {

}

int SerialObject_UART_Win::readBytes(uint8_t * buff, int numBytes) {
  return 0;
}

void SerialObject_UART_Win::closePort() {

}