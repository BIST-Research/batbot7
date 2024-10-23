import numpy as np
from serial import Serial

import logging
logging.basicConfig(level=logging.DEBUG)
from enum import Enum

import time

# for developing on not the PI we create fake library
# that mimics spidepc 
try:
    from spidev import SpiDev
except ImportError:
    logging.error("pinnae.py:: no spidev found, developing on different os ")
    from batbot7_bringup.serial.fake_spidev import fake_SpiDev as SpiDev

import platform

# if platform.system() == "Linux" or platform.system() == "Darwin":
from batbot7_bringup.serial.bb_serial import BB_Serial as Serial
# else:
    # from serial import Serial

# global variables holding number of motors in A ear
NUM_PINNAE_MOTORS = 7

# setting the limits on each motor
DEFAULT_MIN_ANGLE_LIMIT = np.int16(-180)
DEFAULT_MAX_ANGLE_LIMIT = np.int16(180)

class COM_TYPE(Enum):
    NONE = -1
    SPI = 0
    FAKE_SPI = 1
    UART = 2

class MOTOR_COMMAND(Enum):
    READ_STATUS = 0
    READ_ANGLE = 1
    WRITE_ANGLE = 2
    WRITE_PID = 3

class COMM_RESULT(Enum):
    COMM_SUCCESS = 0
    COMM_FAIL = 1
    COMM_INSTRUCTION_ERROR = 2
    COMM_CRC_ERROR = 3
    COMM_ID_ERROR = 4
    COMM_PARAM_ERROR = 5

def crc16(data: bytes):
    '''
    CRC-16 (CCITT) implemented with a precomputed lookup table
    '''
    table = [ 0x0000,
        0x8005, 0x800F, 0x000A, 0x801B, 0x001E, 0x0014, 0x8011,
        0x8033, 0x0036, 0x003C, 0x8039, 0x0028, 0x802D, 0x8027,
        0x0022, 0x8063, 0x0066, 0x006C, 0x8069, 0x0078, 0x807D,
        0x8077, 0x0072, 0x0050, 0x8055, 0x805F, 0x005A, 0x804B,
        0x004E, 0x0044, 0x8041, 0x80C3, 0x00C6, 0x00CC, 0x80C9,
        0x00D8, 0x80DD, 0x80D7, 0x00D2, 0x00F0, 0x80F5, 0x80FF,
        0x00FA, 0x80EB, 0x00EE, 0x00E4, 0x80E1, 0x00A0, 0x80A5,
        0x80AF, 0x00AA, 0x80BB, 0x00BE, 0x00B4, 0x80B1, 0x8093,
        0x0096, 0x009C, 0x8099, 0x0088, 0x808D, 0x8087, 0x0082,
        0x8183, 0x0186, 0x018C, 0x8189, 0x0198, 0x819D, 0x8197,
        0x0192, 0x01B0, 0x81B5, 0x81BF, 0x01BA, 0x81AB, 0x01AE,
        0x01A4, 0x81A1, 0x01E0, 0x81E5, 0x81EF, 0x01EA, 0x81FB,
        0x01FE, 0x01F4, 0x81F1, 0x81D3, 0x01D6, 0x01DC, 0x81D9,
        0x01C8, 0x81CD, 0x81C7, 0x01C2, 0x0140, 0x8145, 0x814F,
        0x014A, 0x815B, 0x015E, 0x0154, 0x8151, 0x8173, 0x0176,
        0x017C, 0x8179, 0x0168, 0x816D, 0x8167, 0x0162, 0x8123,
        0x0126, 0x012C, 0x8129, 0x0138, 0x813D, 0x8137, 0x0132,
        0x0110, 0x8115, 0x811F, 0x011A, 0x810B, 0x010E, 0x0104,
        0x8101, 0x8303, 0x0306, 0x030C, 0x8309, 0x0318, 0x831D,
        0x8317, 0x0312, 0x0330, 0x8335, 0x833F, 0x033A, 0x832B,
        0x032E, 0x0324, 0x8321, 0x0360, 0x8365, 0x836F, 0x036A,
        0x837B, 0x037E, 0x0374, 0x8371, 0x8353, 0x0356, 0x035C,
        0x8359, 0x0348, 0x834D, 0x8347, 0x0342, 0x03C0, 0x83C5,
        0x83CF, 0x03CA, 0x83DB, 0x03DE, 0x03D4, 0x83D1, 0x83F3,
        0x03F6, 0x03FC, 0x83F9, 0x03E8, 0x83ED, 0x83E7, 0x03E2,
        0x83A3, 0x03A6, 0x03AC, 0x83A9, 0x03B8, 0x83BD, 0x83B7,
        0x03B2, 0x0390, 0x8395, 0x839F, 0x039A, 0x838B, 0x038E,
        0x0384, 0x8381, 0x0280, 0x8285, 0x828F, 0x028A, 0x829B,
        0x029E, 0x0294, 0x8291, 0x82B3, 0x02B6, 0x02BC, 0x82B9,
        0x02A8, 0x82AD, 0x82A7, 0x02A2, 0x82E3, 0x02E6, 0x02EC,
        0x82E9, 0x02F8, 0x82FD, 0x82F7, 0x02F2, 0x02D0, 0x82D5,
        0x82DF, 0x02DA, 0x82CB, 0x02CE, 0x02C4, 0x82C1, 0x8243,
        0x0246, 0x024C, 0x8249, 0x0258, 0x825D, 0x8257, 0x0252,
        0x0270, 0x8275, 0x827F, 0x027A, 0x826B, 0x026E, 0x0264,
        0x8261, 0x0220, 0x8225, 0x822F, 0x022A, 0x823B, 0x023E,
        0x0234, 0x8231, 0x8213, 0x0216, 0x021C, 0x8219, 0x0208,
        0x820D, 0x8207, 0x0202 
    ]
    
    crc = 0x0000
    for byte in data:
        crc = (crc << 8) ^ table[(crc >> 8) ^ byte & 0xFF]
        crc &= 0xFFFF                                   # important, crc must stay 16bits all the way through
    return crc

class PinnaeController:
    def __init__(self,spiObj:SpiDev = None,serial_dev:Serial = None) -> None:
        # holds the current angles of the motors
        self.current_angles = np.zeros(NUM_PINNAE_MOTORS, dtype=np.int16)

        ## holds the limits for the motor
        # holds the limits of the motors
        self.min_angle_limits = np.zeros(NUM_PINNAE_MOTORS,dtype=np.int16)
        self.min_angle_limits[:] = DEFAULT_MIN_ANGLE_LIMIT
        # max angle for each motor
        self.max_angle_limits = np.zeros(NUM_PINNAE_MOTORS,dtype=np.int16)
        self.max_angle_limits[:] = DEFAULT_MAX_ANGLE_LIMIT
        
        self.com_type = COM_TYPE.NONE

        # serial_dev.set_attributes(115200, 1)
        # serial_dev.enable_blocking(True)

        self.spi = spiObj
        self.serial = serial_dev
    
        if spiObj != None:
            self.com_type = COM_TYPE.SPI
            self.spi.mode = 0
            self.spi.max_speed_hz = 10000000
            logging.debug("Using SPI object")
        elif serial_dev != None:
            self.serial.set_attributes(115200, 1)
            self.serial.enable_blocking(True)
            self.com_type = COM_TYPE.UART
            logging.debug("Using Serial object")
        else:
            self.com_type = COM_TYPE.NONE
    
    def config_uart(self,serial_obj:Serial)->None:
        self.serial = serial_obj
        self.com_type = COM_TYPE.UART
        logging.debug("Using UART NOW!")
        
    def close_uart(self)->None:
        if self.serial:
            if self.serial.is_open:
                self.serial.close()
                self.serial = None
                self.com_type = COM_TYPE.NONE
                
    def connection_status(self)->bool:
        if self.com_type == COM_TYPE.NONE:
            return False
        
        elif self.com_type == COM_TYPE.FAKE_SPI:
            return False
        elif self.com_type == COM_TYPE.SPI:
            return True
        elif self.com_type == COM_TYPE.UART:
            return self.serial.is_open
        
    def disconnect_serial(self):
        try:
            self.serial.close()
        except:
            pass
        
        
    def config_spi(self,spi:SpiDev)->None:
        """Sets the internal SPI object to this new one

        Args:
            spiObj (SpiDev): new spi object
        """
        self.serial = None
        self.com_type = COM_TYPE.SPI
        self.spi = spi
        self.spi.mode = 0
        self.spi.max_speed_hz = 10000000
        
    def get_ack(self)->bool:
        return False
    
    def reset_zero_position(self,index:np.uint16)->None:
        
        data_buffer = bytearray((NUM_PINNAE_MOTORS*2)+1)
        
        data_buffer[0] = (0x80) | index
        
        # first motor
        data_buffer[1] = (self.current_angles[0] >> 8) & 0xff
        data_buffer[2] =  self.current_angles[0] & 0xff
        
        # second motor
        data_buffer[3] = (self.current_angles[1] >> 8) & 0xff
        data_buffer[4] =  self.current_angles[1] & 0xff
        
        # third motor
        data_buffer[5] = (self.current_angles[2] >> 8) & 0xff
        data_buffer[6] =  self.current_angles[2] & 0xff
        
        # fourth motor
        data_buffer[7] = (self.current_angles[3] >> 8) & 0xff
        data_buffer[8] =  self.current_angles[3] & 0xff
        
        # fifth motor
        data_buffer[9] = (self.current_angles[4] >> 8) & 0xff
        data_buffer[10] = self.current_angles[4] & 0xff
        
        # sixth motor
        data_buffer[11] = (self.current_angles[5] >> 8) & 0xff
        data_buffer[12] =  self.current_angles[5] & 0xff
        
        # seventh motor
        data_buffer[13] = (self.current_angles[6] >> 8) & 0xff
        data_buffer[14] =  self.current_angles[6] & 0xff
        
        if self.com_type == COM_TYPE.SPI:
            if self.spi:
                self.spi.xfer2(data_buffer)
            else:
                logging.error("SPI NOT CONNECTED!")
                self.com_type = COM_TYPE.NONE
        elif self.com_type == COM_TYPE.UART:
            if self.serial:
                logging.debug(f'Resetting zero position of motor {index}')
                # self.serial.write(data_buffer)
            else:
                logging.error("UART NOT CONNECTED!")
                self.com_type == COM_TYPE.NONE
        else:
            logging.error("NO COM TYPE SELECTED CHOOSE UART OR SPI!")
    
    def move_to_min(self,index:np.uint8, move_cw:bool = True)->None:
        data_buffer = bytearray((NUM_PINNAE_MOTORS*2) +1)
        
        if move_cw:
            cw_flag = 0x20
        else:
            cw_flag = 0x00
            
        data_buffer[0] = 0x40 | index | cw_flag
        
         # first motor
        data_buffer[1] = (self.current_angles[0] >> 8) & 0xff
        data_buffer[2] =  self.current_angles[0] & 0xff
        
        # second motor
        data_buffer[3] = (self.current_angles[1] >> 8) & 0xff
        data_buffer[4] =  self.current_angles[1] & 0xff
        
        # third motor
        data_buffer[5] = (self.current_angles[2] >> 8) & 0xff
        data_buffer[6] =  self.current_angles[2] & 0xff
        
        # fourth motor
        data_buffer[7] = (self.current_angles[3] >> 8) & 0xff
        data_buffer[8] =  self.current_angles[3] & 0xff
        
        # fifth motor
        data_buffer[9] = (self.current_angles[4] >> 8) & 0xff
        data_buffer[10] = self.current_angles[4] & 0xff
        
        # sixth motor
        data_buffer[11] = (self.current_angles[5] >> 8) & 0xff
        data_buffer[12] =  self.current_angles[5] & 0xff
        
        # seventh motor
        data_buffer[13] = (self.current_angles[6] >> 8) & 0xff
        data_buffer[14] =  self.current_angles[6] & 0xff
        
        if self.com_type == COM_TYPE.SPI:
            if self.spi:
                self.spi.xfer2(data_buffer)
            else:
                logging.error("SPI NOT CONNECTED!")
                self.com_type = COM_TYPE.NONE
        elif self.com_type == COM_TYPE.UART:
            if self.serial:
                logging.debug(f"Moving to min motor {index}")
                # self.serial.write(data_buffer)
            else:
                logging.error("UART NOT CONNECTED!")
                self.com_type == COM_TYPE.NONE
        else:
            logging.error("NO COM TYPE SELECTED CHOOSE UART OR SPI!")
            

    def send_MCU_angles(self) -> None:
        """Sends all 7 of the angles to the Grand Central, 
        in a fashion of 2 bytes for each motor angle. The original 
        angles are represented as signed 16 int, here we break them into 
        bytes and send them

        """
        # data_buffer = np.zeros( NUM_PINNAE_MOTORS*2 +1,dtype=np.uint8)
        data_buffer = bytearray((NUM_PINNAE_MOTORS*2)+1)
        
        # first motor
        data_buffer[1] = (self.current_angles[0] >> 8) & 0xff
        data_buffer[2] =  self.current_angles[0] & 0xff
        
        # second motor
        data_buffer[3] = (self.current_angles[1] >> 8) & 0xff
        data_buffer[4] =  self.current_angles[1] & 0xff
        
        # third motor
        data_buffer[5] = (self.current_angles[2] >> 8) & 0xff
        data_buffer[6] =  self.current_angles[2] & 0xff
        
        # fourth motor
        data_buffer[7] = (self.current_angles[3] >> 8) & 0xff
        data_buffer[8] =  self.current_angles[3] & 0xff
        
        # fifth motor
        data_buffer[9] = (self.current_angles[4] >> 8) & 0xff
        data_buffer[10] = self.current_angles[4] & 0xff
        
        # sixth motor
        data_buffer[11] = (self.current_angles[5] >> 8) & 0xff
        data_buffer[12] =  self.current_angles[5] & 0xff
        
        # seventh motor
        data_buffer[13] = (self.current_angles[6] >> 8) & 0xff
        data_buffer[14] =  self.current_angles[6] & 0xff
        
        # convert the data to list so we can send it
        # write_data = data_buffer.tolist()
    
        
        if self.com_type == COM_TYPE.SPI:
            if self.spi:
                self.spi.xfer2(data_buffer)
            else:
                logging.error("SPI NOT CONNECTED!")
                self.com_type = COM_TYPE.NONE
        elif self.com_type == COM_TYPE.UART:
            if self.serial:
                logging.debug("Writing data to serial!")
                # self.serial.write(data_buffer)
            else:
                logging.error("UART NOT CONNECTED!")
                self.com_type == COM_TYPE.NONE
        else:
            logging.error("NO COM TYPE SELECTED CHOOSE UART OR SPI!")
            
        
    def calibrate_and_get_motor_limits(self)->np.int16:
        pass 


    def set_motor_limit(self,motor_index: np.uint8, min: np.int16, max: np.int16)-> bool:
        """For a given motor, this function will update its limit. Will do error checking
        if the new limit falls into the current angle of the motor
    

        Args:
            motor_index (np.uint8): index of the motor to control
            min (np.int16): new minimun angle in degrees
            max (np.int16): new maximum angle in degrees
        """
        if self.current_angles[motor_index] > max or self.current_angles[motor_index] < min:
            logging.error("set_motor_limit: new limits out of range for current angle!")
            return False
        
        # set the new limits
        self.max_angle_limits[motor_index] = max
        self.min_angle_limits[motor_index] = min

        return True
    
    def set_motor_min_limit(self,motor_index: np.uint8, min: np.int16) -> bool:
        """sets the motor min limit if it is greater than current angle

        Args:
            motor_index (np.uint8): motor of choice
            min (np.int16): new min value to use

        Returns:
            bool: true if possible
        """
        if self.current_angles[motor_index] < min:
            logging.error("set_motor_min_limit: new limit out of range")
            return False
        
        self.min_angle_limits[motor_index] = min
        logging.debug(f"Success changing min on {motor_index} to {min}")
        return True

    def set_motor_max_limit(self,motor_index: np.uint8, max: np.int16) -> bool:
        """sets the motor max limit if it is greater than current angle

        Args:
            motor_index (np.uint8): motor of choice
            max (np.int16): new max value to use

        Returns:
            bool: true if possible
        """
        if self.current_angles[motor_index] > max:
            logging.error("set_motor_max_limit: new limit out of range")
            return False
        
        self.max_angle_limits[motor_index] = max
        logging.debug(f"Success changing max on {motor_index} to {max}")
        return True
        
    

    def get_motor_limit(self,motor_index:np.uint8)->np.int16:
        """Returns the given motor indexes current limits

        Args:
            motor_index (np.uint8): index of the motor to get

        Returns:
            np.int16: [min_angle,max_angle]
        """

        assert motor_index < NUM_PINNAE_MOTORS, f"Motor index: {motor_index} greater than NUM_PINNAE_MOTORS: {NUM_PINNAE_MOTORS}"
        return(self.min_angle_limits[motor_index],self.max_angle_limits[motor_index])
    
    def get_motor_max_limit(self,motor_index:np.uint8)->np.int16:
        """Returns the max limit of specific motor

        Args:
            motor_index (np.uint8): motor to get max index for 

        Returns:
            np.int16: current max value
        """
        assert motor_index < NUM_PINNAE_MOTORS, f"Motor index: {motor_index} greater than NUM_PINNAE_MOTORS: {NUM_PINNAE_MOTORS}"
        return(self.max_angle_limits[motor_index])

    def get_motor_min_limit(self,motor_index:np.uint8)->np.int16:
        """Returns the min limit of specific motor

        Args:
            motor_index (np.uint8): motor to get min value for 

        Returns:
            np.int16: current min value
        """
        assert motor_index < NUM_PINNAE_MOTORS, f"Motor index: {motor_index} greater than NUM_PINNAE_MOTORS: {NUM_PINNAE_MOTORS}"
        return(self.min_angle_limits[motor_index])



    # --------------------------------------------------------------------------------------
    #                       Setting motor value funcitons

    # set the new angle of the motor
    def set_motor_angle(self,motor_index: np.uint8, angle: np.int16)->bool:
        """Checks if the new motor angle requested is valid. Meaning if 
        it falls between the current angle.

        Args:
            motor_index (np.uint8): _description_
            angle (np.int16): _description_

        Returns:
            bool: _description_
        """
        assert motor_index < NUM_PINNAE_MOTORS, f"Motor index: {motor_index} greater than NUM_PINNAE_MOTORS: {NUM_PINNAE_MOTORS}"
        if angle > self.max_angle_limits[motor_index] or angle < self.min_angle_limits[motor_index]:
            logging.error("set_motor_angle: angle out of limits!")
            return False
        
        # set the angle
        angle_h = np.uint8((angle >> 8) & 0xff)
        angle_l = np.uint8(angle & 0xff)

        self.send_motor_command(motor_index, MOTOR_COMMAND.WRITE_ANGLE, [angle_h, angle_l])
        return True


    def set_motor_angles(self,angles:np.int16)->bool:        
        if not isinstance(angles,list) and not isinstance(angles,np.ndarray):
            return False
        
        if isinstance(angles,list):
            if len(angles) != NUM_PINNAE_MOTORS:
                return False
            
        if isinstance(angles,np.ndarray):
            if angles.size != NUM_PINNAE_MOTORS:
                return False
        
        
        # check if values in range
        if any(angles > self.max_angle_limits) or any(angles < self.min_angle_limits):
            logging.error("set_motor_angles: angles out of bounds!")
            return False
        
        # set the values
        self.current_angles[:] = np.int16(angles[:])
        self.send_MCU_angles()
        return True


    def set_new_zero_position(self,motor_index:np.uint8)->None:
        """Tells the MCU to accept the current encoder angle as its new
        zero position.

        Args:
            motor_index (np.uint8): index to reset to zero
        """
        assert motor_index < NUM_PINNAE_MOTORS, f"Motor index: {motor_index} exceded maximum index{NUM_PINNAE_MOTORS}"
        # this has not been implemented yet but will basically send MCU 
        # tells the MCU this is the new zero point
        self.current_angles[motor_index] = 0
        # self.send_MCU_angles(motor_index)
        self.reset_zero_position(motor_index)
        
        logging.debug(f"Setting motor: {motor_index} new zero position")
        
    def set_all_new_zero_position(self) ->None:
        """Tells the MCU to accept the current encoder angle as its new zero position
        """
        for i in range(NUM_PINNAE_MOTORS):
            self.current_angles[i] = 0
            self.max_angle_limits[i] = DEFAULT_MAX_ANGLE_LIMIT
            self.min_angle_limits[i] = DEFAULT_MIN_ANGLE_LIMIT
            self.send_MCU_angles(i)

    # set motors to max angle
    def set_motor_to_max(self,motor_index:np.uint8)->None:
        assert motor_index < NUM_PINNAE_MOTORS, f"Motor index: {motor_index} exceded maximum index{NUM_PINNAE_MOTORS}"
        self.set_motor_angle(motor_index, self.max_angle_limits[motor_index])
        logging.debug(f"Setting motor: {motor_index} to max value")


    def set_motors_to_max(self)->None:
        """Set all motors to their max angle
        """
        self.current_angles[:] = self.max_angle_limits[:]
        self.send_MCU_angles()
        logging.debug("Setting motors to max")

    # set motors to min angle
    def set_motor_to_min(self,motor_index:np.uint8)->None:
        assert motor_index < NUM_PINNAE_MOTORS, f"Motor index: {motor_index} exceded maximum index{NUM_PINNAE_MOTORS}"
        self.set_motor_angle(motor_index, self.min_angle_limits[motor_index])
        logging.debug(f"Setting motor: {motor_index} to min")


    def set_motors_to_min(self)->None:
        self.current_angles[:] = self.min_angle_limits[:]
        self.send_MCU_angles()
        logging.debug("Setting motors to min")


    # set motors to zero
    def set_motor_to_zero(self,motor_index:np.uint8)->bool:
        assert motor_index < NUM_PINNAE_MOTORS, f"Motor index: {motor_index} exceded maximum index{NUM_PINNAE_MOTORS}"
        
        if self.min_angle_limits[motor_index] > 0:
            logging.debug(f"Failed to set motor: {motor_index} to zero")
            return False
    
        self.set_motor_angle(motor_index, 0)
        logging.debug(f"Success setting motor: {motor_index} to zero")
        
        return True


    def set_motors_to_zero(self)->bool:
        if any(self.min_angle_limits > 0):
            logging.debug("Failed to set motors to zero")
            return False
        
        self.current_angles[:] = 0
        self.send_MCU_angles()
        logging.debug("Setting all motors to zero")
        return True
    
    def send_motor_command(self, index:np.uint8, command:MOTOR_COMMAND, params:list[np.uint8])->bool:

        start = time.time()
        data = [0xFF, 0x00]
        data.append(4 + len(params))
        data.append(index)
        data.append(command.value)
        data = data + params
        crc = crc16(data)
        data.append(crc >> 8)
        data.append(crc & 0xFF)
        print("".join('{:02x} '.format(x) for x in data))

        end = time.time()
        elapsed_time_ms = 1000* (end - start)
        logging.debug(f'Took {elapsed_time_ms} to construct packet')

        start = time.time()
        self.serial.writeBytes(data, len(data))
        end = time.time()
        elapsed_time_ms = 1000 * (end - start)
        logging.debug(f'Took {elapsed_time_ms} to send data')

        start = time.time()
        n, buff = self.serial.readBytes(16)
        end = time.time()
        elapsed_time_ms = 1000 * (end - start)
        logging.debug(f'Took {elapsed_time_ms} to read data')

        # print("".join('{:02x} '.format(x) for x in buff))
        # print("".join(map(chr, buff)))

        if (buff[5] == COMM_RESULT.COMM_SUCCESS.value):
            logging.debug('Successfully processed motor command')
        else:
            logging.error('Error with motor command')

    # --------------------------------------------------------------------------------------
    #           Functions for moving the motors

    def actuate_motors(self,frequency:np.uint8,times =None)->None:
        """This function creates a new thread and will move the 
        pinnae motors between its max and minimums

        Args:
            frequency (np.uint8): speed in hertz to actuate the ears
        """
        pass

    def sweep_motors(self,frequency:np.uint8, times=None)->None:
        """Will move each ear in order to max and then min in a sweeping 
        order

        Args:
            frequency (np.uint8): speed in hertz to actuate
            times (np.uint8, optional): times to sweep through. Defaults to None.
        """
        pass

    def flap_pinnae(self,frequency:np.uint8,times=1)->None:
        """Makes all motors go to their max and then min after some time (1/Frequency)

        Args:
            frequency (np.uint8): _description_
            times (int, optional): _description_. Defaults to 1.
        """
        pass