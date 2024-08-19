#include "ml_tendon_comm_protocol.hpp"

void unpack(char* buff, tendon_datapacket_t* packet)
{
    packet->motorId = (uint8_t)buff[2];
    packet->numParams = (uint8_t)buff[1] - 4;
    packet->opcode = (tendon_opcode_t)buff[3];

    packet->params = &buff[4];

    // validate crc
}