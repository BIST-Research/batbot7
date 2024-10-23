#ifndef SERIAL_OBJECT_HPP
#define SERIAL_OBJECT_HPP

/**
 * @author Jayson De La Vega
 * @date 2024-10-17
 * @ C Library for serial communication (Win)
 *
 * Adapted from
 * https://stackoverflow.com/questions/6947413/how-to-open-read-and-write-from-serial-port-in-c
 */

#include "stdint.h"
#include <string>

class SerialObject {

public:
    SerialObject() {

    }

    ~SerialObject() {
        closePort();
    }

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
    virtual void writeBytes(const uint8_t* bytes, int numBytes) = 0;

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
    virtual int readBytes(uint8_t* buff, int numBytes) = 0;

    /**
     * @brief Closes the serial port
     */
    virtual void closePort() {
      
    };

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