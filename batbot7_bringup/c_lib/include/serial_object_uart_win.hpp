#ifndef SERIAL_OBJECT_UART_WIN_HPP
#define SERIAL_OBJECT_UART_WIN_HPP

/**
 * @author Jayson De La Vega
 * @date 2024-10-17
 * @ C Library for serial communication
 */

#include <string>
#include <termios.h>

#include "serial_object.hpp"

#define BB_SERIAL_BAUD B115200

class SerialObject_UART_Win : public SerialObject {

public:
  /**
   * @brief Constructor for batbot serial object
   * 
   * @param portName The linux device port
   */
  SerialObject_UART_Win(std::string portName);

  /**
   * @brief Destroy the bb serial object
   */
  ~SerialObject_UART_Win();

  /**
   * @brief Set the serial object's attributes
   * 
   * @param speed the baudrate
   * @param parity the parity
   * @return int serial status code
   * 
   * This serial unix library is developed using the unix termios struct,
   * which can be read about here: https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap11.html#tag_11
   */
  int set_attributes(int speed, int parity);

  /**
   * @brief This function en/disables serial read blocking
   * 
   * @param should_block a boolean specifying if serial read should block
   * 
   * When disabled, the serial object will read bytes as they enter the receive buffer.
   * The way serial works is that we specify VMIN, which specifies the minimum number of bytes we want to receive.
   * The readBytes() function will block until it receives this number of bytes or more.
   * The second important parameter is VTIME, which gives us an internal timer for how long we are willing to wait before 
   * receiving another character. 
   * 
   * If VTIME has passed, and we have satisfied our VMIN requirement, readBytes will return.
   */
  void enable_blocking(bool should_block);

  /**
   * @brief This function writes a buffer of size numBytes.
   * 
   * @param bytes the buffer to write
   * @param numBytes the number of bytes in the buffer to write
   */
  void writeBytes(const uint8_t* bytes, int numBytes);

  /**
   * @brief This function reads from the serial device.
   * 
   * @param buff the buffer to receive our data in
   * @param numBytes the size of our buffer.
   * @return int the number of bytes received.
   * 
   * As mentioned in the notes for the enable_blocking function, this function will block if enabled_blocking was set to true.
   * Of course, the the amount of bytes received will always be at most the size of our buffer. We may also receive less bytes than the
   * size of our buffer, as read will return when a new line character is received.
   */
  int readBytes(uint8_t* buff, int numBytes);

  /**
   * @brief Closes the serial port
   */
  void closePort() override;

private:
  /**
   * @brief The name of the terminal device
   */
  std::string _portName;

  /**
   * @brief The file descriptor of the tty
   * 
   */
  int _fd;
};

#endif