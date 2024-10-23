#ifndef TENDON_HARDWARE_INTERFACE_HPP
#define TENDON_HARDWARE_INTERFACE_HPP

/**
 * @author Jayson De La Vega
 * @date 2024-10-17
 * @ Interface for communicating with tendon controller
 * 
 */

#include "serial_object.hpp"
#include "stdint.h"

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
#define TENDON_CONTROL_GET_UPPER_16B(a) (uint8_t)(((uint16_t)a >> 8) & 0xFF)
#define TENDON_CONTROL_GET_LOWER_16B(a) (uint8_t)((uint16_t)a & 0xFF)

/**
 * @brief Enum defining opcodes for motor tendon control
 * 
 * The protocol parses data packets (see the data packet structure) and performs the following functions as follows:
 * 
 * READ_STATUS: Reads the status of the motor specified by motor ID. If motor ID is given to be 0xFF, then READ_STATUS
 * will perform a multiple read command. In this case you must pass the ID of each motor whose status you want to read.
 * The order of the IDs does not matter.
 * 
 * For instance if you would like to read the status of motors 2, 4, 6, the params would be:
 * 
 * [ 0x02 ][ 0x04 ][ 0x06 ]
 *               
 * READ_ANGLE: Reads the angle of the motor specified my motor ID. If the specified ID is 0xFF, then READ_ANGLE
 * will perform a multiple read command. You must pass the ID of each motor whose angle you want to read. The 
 * order of the IDs does not matter.
 *  
 * For instance if you would like to read the angles of motors 2, 4, 6, the params would be:
 * 
 * [ 0x02 ][ 0x04 ][ 0x06 ]
 * 
 * WRITE_ANGLE: Writes a goal angle (signed 16-bit integer) to the motor specifed by motor ID. This function requires 2 parameters in 
 * the following order:
 * 
 * Param 1                  Param 2
 * [ GOAL ANGLE BYTES HIGH ][ GOAL ANGLE BYTES LOW ]
 * 
 * If the specified ID is 0xFE, then the request becomes a multiple write command. You must pass as a parameter the ID of each
 * motor you want to write immediately followed by the goal angle high and low bytes. The order of motor IDs does not matter,
 * however, the goal angle high and low bytes must immediately follow their corresponding motor ID.
 * 
 * For instance, if you would like to write motor 2 to 0 degrees and motor 4 to 5 degrees, the params would be:
 * 
 * Motor ID 1  Goal Angle 1 High   Goal Angle 1 Low    Motor ID 2  Goal Angle 2 High   Goal Angle 2 Low
 * [   0x02   ][       0x00       ][       0x00       ][   0x04   ][       0x00       ][       0x00       ]
 * 
 * [ MOTOR ID 1 ][ MOTOR ID 1 GOAL ANGLE HIGH BYTES ][ MOTOR ID 2 GOAL ANGLE HIGH BYTES ]
 * 
 * For each motor you wish to write.
 * 
 * WRITE_PID: Writes the PID parameters (signed 16-bit integers) to the motor specifed by motor ID. This function requires 6 parameters in 
 * the following order:
 * 
 * [ P BYTES HIGH ][ P BYTES LOW ][ I BYTES HIGH ][ I BYTES LOW ][ D BYTES HIGH ][ D BYTES LOW ]
 * 
 * This function does not support multiple write operations.
 * 
 * *Note*: Look into the possibility of multiple write operations. Only problem is that the messages can get very long. Need to test if this 
 * causes any significant input lag.
 * 
 */
typedef enum {
  ECHO,
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


class TendonHardwareInterface
{
public:

    TendonHardwareInterface(std::string portName);
    ~TendonHardwareInterface();


    typedef struct {
        uint8_t motorId;
        uint8_t opcode;
        uint8_t numParams;
        uint8_t pkt_params[TENDON_CONTROL_PKT_MAX_NUM_PARAM_BYTES];
    } TendonHardwareResponse;

    void BuildPacket(uint8_t id, uint8_t opcode, uint8_t* params, std::size_t num_params);

    void SendTxRx();

    void SendTx();
    
private:

    uint16_t CRC16(uint16_t crc_accum, uint8_t *data, uint16_t data_blk_size);

    SerialObject* ser;

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

    TendonControl_data_packet_s rx;
    TendonControl_data_packet_s tx;
};

#endif