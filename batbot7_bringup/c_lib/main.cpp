#include "serial.hpp"

#include "unistd.h"

#include <iostream>
#include "string"

int main(int argc, char* argv[])
{
    if (argc != 2) {
        printf("Usage: %s <serial port>\n", argv[0]);
        return -1;
    }

    std::string portName = argv[1];

    BB_Serial ser(portName);

    int ser_status = ser.set_attributes(BB_SERIAL_BAUD, 0);
    if (ser_status != 0)
    {
        std::cout << "Error configuring serial object";
        return -1;
    }
    ser.enable_blocking(1);

    uint8_t datapacket[] = {
        0xFF, 0x05, 0x01, 0x01, 0x00, 0x00, 0x00
    };

    std::string strToWrite;
    while (true) {
        std::cout << "Enter a string to write: ";
        std::cin >> strToWrite;
        strToWrite += '\n';

        ser.writeBytes(datapacket, 7);
        std::cout << "Wrote " << 14 << " bytes\n";

        usleep((7 + 25) * 100);

        uint8_t buff[100];
        
        int n = ser.readBytes(buff, sizeof(buff));

        std::cout << "Read " << n << " bytes: " << buff << "\n";
    }
    
    return 0;
}