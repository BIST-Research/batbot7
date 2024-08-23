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
 * @brief Maximum packet size acceptable for this application
 */
#define TENDON_CONTROL_PKT_MAX_NUM_BYTES_IN_FRAME 32

/**
 * @brief Number of bytes consumer by packet header
 */
#define TENDON_CONTROL_PKT_NUM_HEADER_BYTES 2

/**
 * @brief Number of bytes used for opcpde
 */
#define TENDON_CONTROL_PKT_NUM_OPCODE_BYTES  1

/**
 * @brief Number of bytes used for motor ID
 */
#define TENDON_CONTROL_PKT_NUM_ID_BYTES 1

/**
 * @brief Number of bytes used for packet length field
 */
#define TENDON_CONTROL_PKT_NUM_LEN_BYTES 1

/**
 * @brief Number of bytes used for CRC
 */
#define TENDON_CONTROL_PKT_NUM_CRC_BYTES 2

/**
 * @brief Maximum number of bytes in the parameters array
 */
#define TENDON_CONTROL_PKT_MAX_NUM_PARAM_BYTES    TENDON_CONTROL_PKT_MAX_NUM_BYTES_IN_FRAME - \
                                                    TENDON_CONTROL_PKT_NUM_HEADER_BYTES - \
                                                    TENDON_CONTROL_PKT_NUM_OPCODE_BYTES - \
                                                    TENDON_CONTROL_PKT_NUM_ID_BYTES - \
                                                    TENDON_CONTROL_PKT_NUM_LEN_BYTES

#define TENDON_CONTROL_MAKE_16B_WORD(a, b) ((uint16_t)a << 8) | ((uint16_t)b)

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
  COMM_CRC_ERROR,
  COMM_ID_ERROR,
  COMM_PARAM_ERROR
} tendon_comm_result_t;

/**
 * @brief Struct to define tendon control data packet
 * 
 * This struct defines the data packets defined by the tendon control communication protocol
 * The structure of a packet is as follows:
 * 
 * [ HEADER 1 ][ HEADER 2 ][ LENGTH ][ MOTOR ID ][ OPCODE ][ PARAMS ][ CRC HIGH ][ CRC LOW ]
 * 
 * HEADER 1+2: Used as a packet delimiter to signifify the start of a new packet. Always the bytes 0xFF 0x00.
 * LENGTH: 8-bit integer used to specify the length of the packet. The header and length fields
 *          are not taken into account when calculating length, so the length is calculated as
 *          4 + number of params (4 comes from opcode, params, and both CRC fields).
 * MOTOR ID: The id of the motor to read/write. Motors are assumed to be 1 indexed, so 0x00
 *            is used to read/write all motors.
 * OPCODE: 8-bit integer used to command the tendon controller to perform a certain action
 *          (e.g. read/write angles, write PID, etc.)
 * PARAMS: An array of 8-bit integers. Used as the "arguments" for the opcode.
 * CRC HIGH+LOW: Together, form a a 16-bit CRC used for checking data corruption
 * 
 * NOTE: When modifying this struct, keep field order and byte-alignment in mind.
 * 
 * This data structure takes advantage of byte-alignment, allowing for direct
 * casting of the input buffer directly to this object. This also allows for
 * accessing fields using either array or struct accessors.
 */
typedef struct
{
  union
  {
    uint8_t data_packet[TENDON_CONTROL_PKT_MAX_NUM_BYTES_IN_FRAME];

    struct {
      uint8_t header[TENDON_CONTROL_PKT_NUM_HEADER_BYTES];
      uint8_t len;
      uint8_t motorId;
      uint8_t opcode;
      uint8_t pkt_params[TENDON_CONTROL_PKT_MAX_NUM_PARAM_BYTES];
    } data_packet_s;
  } data_packet_u;
} TendonControl_data_packet_s;

typedef struct
{
  union 
  {
    TendonControl_data_packet_s rx_packet;
    TendonControl_data_packet_s tx_packet;
  };

  tendon_comm_result_t comm_result;

} TendonControl_packet_handler_t;

/**
 * @brief Function used to obtain 116-bit CRC
 * 
 * @param crc_accum Used to input running crc
 * @param data The data to check
 * @param data_blk_size The number of bytes in the data
 * @return The 16-bit CRC as a uint16_t 
 */
uint16_t updateCRC(uint16_t crc_accum, uint8_t *data, uint16_t data_blk_size);