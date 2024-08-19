/**
 * @file 
 * @brief This file definies the serial communication protocol for tendon control 
 * 
 */
#include <stdint.h>


#define PKT_HEADER_POS_H 2
#define PKT_HEADER_POS_L 3
#define PKT_LENGTH_POS_H 4
#define PKT_LENGTH_POS_L 5
#define PKT_ID_POS_L 6
#define PKT_ID_POS_H 7
#define PKT_OPCODE_POS_H 8
#define PKT_OPCODE_POS_L 9
#define PKG_PARAM_BASE_POS_H 10
#define PKG_PARAM_BASE_POS_L 11

/**
 * @brief Enum defining opcodes for motor tendon control
 * 
 */
typedef enum {
  READ_STATUS,
  READ_ANGLE,
  WRITE_ANGLE,
  WRITE_PID,
} tendon_opcode_t;

/**
 * @brief Enum defining comm results for tendon control
 * 
 */
typedef enum {
  COMM_SUCCESS,
  COMM_FAIL,
  COMM_INSTRUCTION_ERROR,
  COMM_CRC_ERROR
} tendon_comm_result_t;

/**
 * @brief A struct defining a tendon controller data packet
 * 
 * A typical data packet will have the following format:
 * 
 * [ HEADER 1 ][ HEADER 2 ][ LENGTH ][ MOTOR ID ][ OP CODE ][ PARAM 1][ PARAM 2][ ... ][ CRC 1 ][ CRC 2 ]
 * 
 * HEADER: A packet delimiter, a character used to signify the start of a packet
 * LENGTH: The number of bytes in the data packet (i.e. 4 + number of parameters, with 4 coming from the bytes for motor id, op code, motor id, and crc)
 * PARAM N: The nth parameter of the op code
 * 
 */
typedef struct {
  tendon_opcode_t opcode;
  uint8_t motorId;
  uint8_t numParams;
  char* params;
  tendon_comm_result_t communicationResult;
} tendon_datapacket_t;


#define TENDON_CONTROL_PKT_MAX_NUM_BYTES_IN_FRAME  22
#define TENDON_CONTROL_PKT_NUM_HEADER_BYTES 2
#define TENDON_CONTROL_PKT_NUM_OPCODE_BYTES  1
#define TENDON_CONTROL_PKT_NUM_ID_BYTES 1
#define TENDON_CONTROL_PKT_NUM_LEN_BYTES 1
#define TENDON_CONTROL_PKT_NUM_CRC_BYTES  2
#define TENDON_CONTROL_PKT_MAX_NUM_PARAM_BYTES    TENDON_CONTROL_PKT_MAX_NUM_BYTES_IN_FRAME - \
                                                    TENDON_CONTROL_PKT_NUM_HEADER_BYTES - \
                                                    TENDON_CONTROL_PKT_NUM_OPCODE_BYTES - \
                                                    TENDON_CONTROL_PKT_NUM_ID_BYTES - \
                                                    TENDON_CONTROL_PKT_NUM_LEN_BYTES - \
                                                    TENDON_CONTROL_PKT_NUM_CRC_BYTES

typedef struct
{
  union
  {
    uint8_t data_packet[TENDON_CONTROL_PKT_MAX_NUM_BYTES_IN_FRAME];

    struct {
      uint8_t header[TENDON_CONTROL_PKT_NUM_HEADER_BYTES];
      uint8_t opcode;
      uint8_t motorId;
      uint8_t len;
      uint8_t pkt_params[TENDON_CONTROL_PKT_MAX_NUM_PARAM_BYTES];
      uint8_t crc[TENDON_CONTROL_PKT_NUM_CRC_BYTES];
    } data_packet_s;
  } data_packet_u;
} TendonControl_data_packet_s;

/**
 * @brief Unpacks serial data
 * 
 * @param buff 
 */
void unpack(char* buff, tendon_datapacket_t* packet);

/**
 * @brief 
 * 
 */
void sendStatus(char* buff);