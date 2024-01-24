# controls the pinnaes using SPI connection to the grandcentral controllers
# author: Mason Lopez
import numpy as np

# global variables holding number of motors in A ear
NUM_PINNAE_MOTORS = 6

# setting the limits on each motor
DEFAULT_MIN_ANGLE_LIMIT = -180
DEFAULT_MAX_ANGLE_LIMIT = 180
class PinnaeController():
    def __init__(self) -> None:
        # holds the current angles of the motors
        self.current_angles = np.zeros(NUM_PINNAE_MOTORS,dtype=np.int16)

        ## holds the limits for the motor
        # holds the limits of the motors
        self.min_angle_limits = np.zeros(NUM_PINNAE_MOTORS,dtype=np.int16)
        self.min_angle_limits[:] = DEFAULT_MIN_ANGLE_LIMIT
        # max angle for each motor
        self.max_angle_limits = np.zeros(NUM_PINNAE_MOTORS,dtype=np.int16)
        self.max_angle_limits[:] = DEFAULT_MAX_ANGLE_LIMIT
        

    def send_angles(self) -> None:
        """Sends all 6 of the angles to the Grand Central, 
        in a fashion of 2 bytes for each motor angle

        """
        pass


    def set_motor_limit(self,motor_index: np.uint8, min: np.int16, max: np.int16)-> bool:
        """For a given motor, this function will update its limit. Will do error checking
        if the new limit falls into the current angle of the motor
    

        Args:
            motor_index (np.uint8): index of the motor to control
            min (np.int16): new minimun angle in degrees
            max (np.int16): new maximum angle in degrees
        """
        pass
    

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
        pass

    def set_motor_angles(self,angles:np.int16)->bool:
        pass


    def set_new_zero_position(self,motor_index:np.uint8)->None:
        """Tells the MCU to accept the current encoder angle as its new
        zero position.

        Args:
            motor_index (np.uint8): index to reset to zero
        """
        pass

    # set motors to max angle
    def set_motor_to_max(self,motor_index:np.uint8)->None:
        pass

    def set_motors_to_max(self)->None:
        pass

    # set motors to min angle
    def set_motor_to_min(self,motor_index:np.uint8)->None:
        pass

    def set_motors_to_min(self)->None:
        pass

    # set motors to zero
    def set_motor_to_zero(self,motor_index:np.uint8)->None:
        pass
    
    def set_motors_to_zero(self)->None:
        pass

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