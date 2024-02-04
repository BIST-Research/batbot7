# controls the pinnaes using SPI connection to the grandcentral controllers
# author: Mason Lopez
import numpy as np

import logging
logging.basicConfig(level=logging.DEBUG)
import argparse

# for developing on not the PI we create fake library
# that mimics spidev
try:
    from spidev import SpiDev
except ImportError:
    logging.error("no spidev found, developing on different os ")
    from fake_spidev import fake_SpiDev as SpiDev

# global variables holding number of motors in A ear
NUM_PINNAE_MOTORS = 6

# setting the limits on each motor
DEFAULT_MIN_ANGLE_LIMIT = -180
DEFAULT_MAX_ANGLE_LIMIT = 180

class PinnaeController:
    def __init__(self,spi_bus=0,spi_select=0) -> None:
        # holds the current angles of the motors
        self.current_angles = np.zeros(NUM_PINNAE_MOTORS,dtype=np.int16)

        ## holds the limits for the motor
        # holds the limits of the motors
        self.min_angle_limits = np.zeros(NUM_PINNAE_MOTORS,dtype=np.int16)
        self.min_angle_limits[:] = DEFAULT_MIN_ANGLE_LIMIT
        # max angle for each motor
        self.max_angle_limits = np.zeros(NUM_PINNAE_MOTORS,dtype=np.int16)
        self.max_angle_limits[:] = DEFAULT_MAX_ANGLE_LIMIT
        
        ## for spidev library
        self.spi = SpiDev()
        self.spi.open(spi_bus,spi_select)
        self.spi.mode = 0
        # self.spi.max_speed_hz = 500000
        

    def send_MCU_angles(self,zero_index = -1) -> None:
        """Sends all 6 of the angles to the Grand Central, 
        in a fashion of 2 bytes for each motor angle. The original 
        angles are represented as signed 16 int, here we break them into 
        bytes and send them

        """
        data_buffer = np.zeros(NUM_PINNAE_MOTORS*2 + 1,dtype=np.byte)

        # first index is for setting telling MCU to use its current encoder 
        # angle as the zero, we will just set for zero
        data_buffer[0] = zero_index+1
        
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
        
        # convert the data to list so we can send it
        write_data = data_buffer.tolist()
        self.spi.xfer2(write_data)
        return write_data
        


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
        return True
        
    

    def get_motor_limit(self,motor_index:np.uint8)->np.int16:
        """Returns the given motor indexes current limits

        Args:
            motor_index (np.uint8): index of the motor to get

        Returns:
            np.int16: [min_angle,max_angle]
        """
        return(self.min_angle_limits[motor_index],self.max_angle_limits[motor_index])




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
        if angle > self.max_angle_limits[motor_index] or angle < self.min_angle_limits[motor_index]:
            logging.error("set_motor_angle: angle out of limits!")
            return False
        
        # set the angle
        self.current_angles[motor_index] = angle

        self.send_MCU_angles()
        return True


    def set_motor_angles(self,angles:np.int16)->bool:
        if not isinstance(angles,list) or len(angles) != NUM_PINNAE_MOTORS:
            return False
        
        
        # check if values in range
        if any(angles > self.max_angle_limits) or any(angles < self.min_angle_limits):
            logging.error("set_motor_angles: angles out of bounds!")
            return False
        
        # set the values
        self.current_angles[:] = angles[:]
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
        self.send_MCU_angles(motor_index)

    # set motors to max angle
    def set_motor_to_max(self,motor_index:np.uint8)->None:
        assert motor_index < NUM_PINNAE_MOTORS, f"Motor index: {motor_index} exceded maximum index{NUM_PINNAE_MOTORS}"
        self.current_angles[motor_index] = self.max_angle_limits[motor_index]
        self.send_MCU_angles()


    def set_motors_to_max(self)->None:
        """Set all motors to their max angle
        """
        self.current_angles[:] = self.max_angle_limits[:]
        self.send_MCU_angles()

    # set motors to min angle
    def set_motor_to_min(self,motor_index:np.uint8)->None:
        assert motor_index < NUM_PINNAE_MOTORS, f"Motor index: {motor_index} exceded maximum index{NUM_PINNAE_MOTORS}"
        self.current_angles[motor_index] = self.min_angle_limits[motor_index]
        self.send_MCU_angles()


    def set_motors_to_min(self)->None:
        self.current_angles[:] = self.min_angle_limits[:]
        self.send_MCU_angles()

    # set motors to zero
    def set_motor_to_zero(self,motor_index:np.uint8)->bool:
        assert motor_index < NUM_PINNAE_MOTORS, f"Motor index: {motor_index} exceded maximum index{NUM_PINNAE_MOTORS}"
        
        if self.min_angle_limits[motor_index] > 0:
            return False
    
        self.current_angles[motor_index] = 0
        self.send_MCU_angles()
        
        return True

    def set_motors_to_zero(self)->bool:
        if any(self.min_angle_limits > 0):
            return False
        
        self.current_angles[:] = 0
        self.send_MCU_angles()
        
        return True
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