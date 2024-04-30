# controls the pinnaes using SPI connection to the grandcentral controllers
# author: Mason Lopez
import numpy as np

import logging
logging.basicConfig(level=logging.DEBUG)
import argparse
from serial import Serial
from enum import Enum


# for developing on not the PI we create fake library
# that mimics spidev
try:
    from spidev import SpiDev
except ImportError:
    logging.error("pinnae.py:: no spidev found, developing on different os ")
    from fake_spidev import fake_SpiDev as SpiDev

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
        

        # communication objects
        self.spi = spiObj
        self.serial = serial_dev
    
            
        if spiObj != None:
            self.com_type = COM_TYPE.SPI
            self.spi.mode = 0
            self.spi.max_speed_hz = 10000000
            logging.debug("Using SPI object")
        elif serial_dev != None:
            self.com_type = COM_TYPE.UART
            logging.debug("Using Serial object")
        else:
            self.com_type = COM_TYPE.NONE
    
    def config_uart(self,serial_obj:Serial)->None:
        """configures the current serial object to be the one passed through. 
        Changes the communication type to be serial.

        Args:
            serial_obj (Serial): new serial object to use, does not verify
        """
        self.serial = serial_obj
        self.com_type = COM_TYPE.UART
        logging.debug("Using UART NOW!")
        
    def close_uart(self)->None:
        """If there is a serial object open, this closes the port.
        """
        if self.serial:
            if self.serial.is_open:
                self.serial.close()
                self.serial = None
                self.com_type = COM_TYPE.NONE
                
    def connection_status(self)->bool:
        """Returns the connection status of the object, this needs to be updated
        as it does not poll the Grandcentral for acknowledgement

        Returns:
            bool: True if the Grand Central is connected
        """
        if self.com_type == COM_TYPE.NONE:
            return False
        
        elif self.com_type == COM_TYPE.FAKE_SPI:
            return False
        elif self.com_type == COM_TYPE.SPI:
            return True
        elif self.com_type == COM_TYPE.UART:
            return self.serial.is_open
        
    def disconnect_serial(self):
        """Disconnects the serial connection 
        """
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
        """Polls the MCU to see if it is connected. This is not implemented 
        yet so simply returns no each time.

        Returns:
            bool: _description_
        """
        return False
    
    def reset_zero_position(self,index:np.uint8)->None:
        """Resets the encoder zero to whatever position the motor is currently at. 
        Ie say the motor is currently sitting at angle 34 degrees, after sending this 
        the MCU will reset its current position to 0. 

        Args:
            index (np.uint8): motor index to reset its zero position 
        """
        
        data_buffer = bytearray((NUM_PINNAE_MOTORS*2)+1)
        
        # to reset zero set the MSB to 1 and lower 3 bits to the motor index
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
            if self.serial and self.serial.is_open:
                self.serial.write(data_buffer)
            else:
                logging.error("UART NOT CONNECTED!")
                self.com_type == COM_TYPE.NONE
        else:
            logging.error("NO COM TYPE SELECTED CHOOSE UART OR SPI!")
    
    def move_to_min(self,index:np.uint8, move_cw:bool = True)->None:
        """Makes the MCU find its hardware min or maximum end stop - depending
        on the move_cw bool and the orientation of the motor respective to you.

        Args:
            index (np.uint8): motor index to move
            move_cw (bool, optional): which direction it should spin to find its end stop. Defaults to True.
        """
        data_buffer = bytearray((NUM_PINNAE_MOTORS*2) +1)
        
        if move_cw:
            cw_flag = 0x20
        else:
            cw_flag = 0x00
        # set the 7th bit to 1 and or the index that should move
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
            if self.serial and self.serial.is_open:
                self.serial.write(data_buffer)
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
        
    
        
        if self.com_type == COM_TYPE.SPI:
            if self.spi:
                self.spi.xfer2(data_buffer)
            else:
                logging.error("SPI NOT CONNECTED!")
                self.com_type = COM_TYPE.NONE
        elif self.com_type == COM_TYPE.UART:
            if self.serial and self.serial.is_open:
                self.serial.write(data_buffer)
            else:
                logging.error("UART NOT CONNECTED!")
                self.com_type == COM_TYPE.NONE
        else:
            logging.error("NO COM TYPE SELECTED CHOOSE UART OR SPI!")
            
        
    def calibrate_and_get_motor_limits(self)->np.int16:
        """Should command the MCU to make each motor move and find its end points
        such that it can calibrate its zero position and know its limits and have
        it send it back. 

            NOT IMPLEMENTED

        Returns:
            np.int16: New limits returned from MCU
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
        """Sets the angle of the motor.

        Args:
            motor_index (np.uint8): motor you want to move
            angle (np.int16): new angle to move to

        Returns:
            bool: True if the new angle is within limits
        """
        assert motor_index < NUM_PINNAE_MOTORS, f"Motor index: {motor_index} greater than NUM_PINNAE_MOTORS: {NUM_PINNAE_MOTORS}"
        if angle > self.max_angle_limits[motor_index] or angle < self.min_angle_limits[motor_index]:
            logging.error("set_motor_angle: angle out of limits!")
            return False
        
        # set the angle
        self.current_angles[motor_index] = angle
        self.send_MCU_angles()
        return True


    def set_motor_angles(self,angles:np.int16)->bool:
        """Sets the angle of the motors from the passed array.
        Size of the angle should be equal to the number of motors
        
        Args: 
            angle (np.int16): new angles for the motors
            
        Returns:
            bool: True if all angles fall within each motor's limits
        """   
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
        self.current_angles[motor_index] = self.max_angle_limits[motor_index]
        self.send_MCU_angles()
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
        self.current_angles[motor_index] = self.min_angle_limits[motor_index]
        self.send_MCU_angles()
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
    
        self.current_angles[motor_index] = 0
        self.send_MCU_angles()
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

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QGroupBox,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QComboBox,
    QSlider,
    QLineEdit,
    QSpinBox,
    QGridLayout,
    QTableWidgetItem,
    QErrorMessage,
    QMenu,
    QTableWidget,
    QFileDialog,
    
)
from PyQt6.QtCore import Qt,QThread,pyqtSignal
from PyQt6.QtGui import QIcon
import sys
import qdarkstyle
import time
import yaml

class PinnaWidget(QWidget):
    main_v_layout = QVBoxLayout()

    instructionThread = None
    instructionThreadRunning = None

    def __init__(self,l_pinna:PinnaeController, r_pinna:PinnaeController):
        QWidget.__init__(self)
        
        self.left_pinna = l_pinna
        self.right_pinna = r_pinna

        self.setWindowTitle("Tendon Controller")
        self.setWindowIcon(QIcon('HBAT.jpg'))
        # self.add_settings_box()
        self.add_motor_controls()
        self.add_table()
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())

        for i in range(NUM_PINNAE_MOTORS):
            if i < 3:
                self.motor_min_limit_SB[i].setValue(0)
                self.motor_max_limit_SB[i].setValue(170)
            else:
                self.motor_min_limit_SB[i].setValue(-170)
                self.motor_max_limit_SB[i].setValue(0)

                
            self.motor_min_limit_changed_CB(i)
            self.motor_max_limit_changed_CB(i)
        
        self.setLayout(self.main_v_layout)

    def add_settings_box(self):
        grid_lay = QGridLayout()

        self.read_limits_PB = QPushButton("Query Limits")
        grid_lay.addWidget(self.read_limits_PB,0,0)

        self.calibrate_limits = QPushButton("Calibrate Motors")
        grid_lay.addWidget(self.calibrate_limits,1,0)

        self.load_file = QPushButton("Load File")
        self.load_file.clicked.connect(self.load_file_CB)
        grid_lay.addWidget(self.load_file,0,0)

        self.create_file = QPushButton("Save File")
        self.create_file.clicked.connect(self.create_file_CB)
        grid_lay.addWidget(self.create_file,0,1)




        self.main_v_layout.addLayout(grid_lay)
        
    def load_file_CB(self):
        file_path,_ = QFileDialog.getOpenFileName(self,'Load File')
        
    def create_file_CB(self):
        file_path, _ = QFileDialog.getSaveFileName(self,'Save File')


    def add_motor_controls(self):
 
        
        control_h_lay = QHBoxLayout()
        
        self.motor_GB = [
            QGroupBox("Motor 1"),
            QGroupBox("Motor 2"),
            QGroupBox("Motor 3"),
            QGroupBox("Motor 4"),
            QGroupBox("Motor 5"),
            QGroupBox("Motor 6"),
            QGroupBox("Motor 7")
        ]

        self.motor_max_PB = [
            QPushButton("Max"),
            QPushButton("Max"),
            QPushButton("Max"),
            QPushButton("Max"),
            QPushButton("Max"),
            QPushButton("Max"),
            QPushButton("Max"),
        ]
        
        self.motor_min_PB = [
            QPushButton("Min"),
            QPushButton("Min"),
            QPushButton("Min"),
            QPushButton("Min"),
            QPushButton("Min"),
            QPushButton("Min"),
            QPushButton("Min"),
        ]

        self.motor_max_limit_SB = [
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox()
        ]

        self.motor_min_limit_SB = [
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox()
        ]

        self.motor_value_SB = [
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox()
        ]
        
        self.motor_value_SLIDER = [
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
        ]
        
        self.motor_set_zero_PB = [
            QPushButton("Set Zero"),
            QPushButton("Set Zero"),
            QPushButton("Set Zero"),
            QPushButton("Set Zero"),
            QPushButton("Set Zero"),
            QPushButton("Set Zero"),
            QPushButton("Set Zero")
        ]
        
        # number_motors = 6
        max_value = 10000
        
        for index in range(NUM_PINNAE_MOTORS):
            vertical_layout = QVBoxLayout()
            
            temp_CB = QGroupBox("Control")
            
            # 4 row by 2 columns
            grid_lay = QGridLayout()
            
            # add max button
            grid_lay.addWidget(self.motor_max_PB[index],0,0)
            
            # add max spinbox
            self.motor_max_limit_SB[index].setRange(-max_value,max_value)
            self.motor_max_limit_SB[index].setValue(180)
            grid_lay.addWidget(self.motor_max_limit_SB[index],0,1)
            
            # add value spinbox
            self.motor_value_SB[index].setRange(-max_value,max_value)
            grid_lay.addWidget(self.motor_value_SB[index],1,0)
            
            # add value slider
            self.motor_value_SLIDER[index].setMinimumHeight(100)
            self.motor_value_SLIDER[index].setRange(-max_value,max_value)
            self.motor_value_SLIDER[index].setValue(0)
            grid_lay.addWidget(self.motor_value_SLIDER[index],1,1)
            
            # add min button
            grid_lay.addWidget(self.motor_min_PB[index],2,0)
            
            # add min spinbox
            self.motor_min_limit_SB[index].setRange(-max_value,max_value)
            self.motor_min_limit_SB[index].setValue(-180)
            grid_lay.addWidget(self.motor_min_limit_SB[index],2,1)
            
            ## add the layout
            vertical_layout.addLayout(grid_lay)
            
            # add set zero
            # vertical_layout.addWidget(self.motor_set_zero_PB[index])
        
            # set max width
            self.motor_GB[index].setMaximumWidth(160)
            
            # attach custom context menu
            self.motor_GB[index].setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.motor_GB[index].customContextMenuRequested.connect(lambda pos,i = index: self.motor_GB_contextMenu(pos,i))
            
            self.motor_GB[index].setLayout(vertical_layout)
            control_h_lay.addWidget(self.motor_GB[index])
        
        self.main_v_layout.addLayout(control_h_lay)

        
        
        # attach callbacks for controller tendon api
        self.add_motor_control_CB()

    def add_table(self):
        hlay = QHBoxLayout()
        self.instruction_TABLE = QTableWidget(1,NUM_PINNAE_MOTORS)
        hlay.addWidget(self.instruction_TABLE)
        self.instruction_TABLE.setHorizontalHeaderLabels(["M1","M2","M3","M4","M5","M6","M7"])

        # set default values in table
        for i in range(NUM_PINNAE_MOTORS):
            intNum = QTableWidgetItem()
            intNum.setData(0,0)
            self.instruction_TABLE.setItem(0,i,intNum)
        
        #-------------------------------------------------
        buttonGB = QGroupBox("Settings")
        vlay = QVBoxLayout()

        self.run_angles_PB = QPushButton("Run")
        self.run_angles_PB.pressed.connect(self.start_stop_instruction_PB_pressed_CB)
        vlay.addWidget(self.run_angles_PB)

        self.load_file_PB = QPushButton("Load")
        self.load_file_PB.pressed.connect(self.load_movements_PB_cb)
        vlay.addWidget(self.load_file_PB)
        
        self.save_file_PB = QPushButton("Save")
        self.save_file_PB.pressed.connect(self.save_movements_PB_cb)
        vlay.addWidget(self.save_file_PB)

        self.speed_SB = QSpinBox()
        self.speed_SB.setSuffix(' Hz')
        self.speed_SB.setRange(1,100)
        vlay.addWidget(self.speed_SB)

        self.instruction_TABLE.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.instruction_TABLE.customContextMenuRequested.connect(self.instruction_T_contextMenu)


        buttonGB.setLayout(vlay)
        #-------------------------------------------------
        hlay.addWidget(buttonGB)

        self.main_v_layout.addLayout(hlay)

    def start_stop_instruction_PB_pressed_CB(self):
        if not self.instructionThreadRunning:
            rows = self.instruction_TABLE.rowCount()
            dataArray = np.zeros((rows,NUM_PINNAE_MOTORS),np.int16)
             
            for row in range(self.instruction_TABLE.rowCount()):
                dataArray[row][0] = int(self.instruction_TABLE.item(row,0).text())
                dataArray[row][1] = int(self.instruction_TABLE.item(row,1).text())
                dataArray[row][2] = int(self.instruction_TABLE.item(row,2).text())
                dataArray[row][3] = int(self.instruction_TABLE.item(row,3).text())
                dataArray[row][4] = int(self.instruction_TABLE.item(row,4).text())
                dataArray[row][5] = int(self.instruction_TABLE.item(row,5).text())
                dataArray[row][6] = int(self.instruction_TABLE.item(row,6).text())
                 
            print(dataArray)

            self.instructionThread = RunInstructionsThread(dataArray,self.speed_SB.value(),self.left_pinna,self.right_pinna)
                
            self.instructionThread.start()
            self.instructionThread.end_motor_angles.connect(self.end_motor_values_emit_callback)
            self.instructionThreadRunning = True
            self.run_angles_PB.setText("Stop")
            # self.set_motor_GB_enabled(False)
        else:
            # see end_motor_values_emit_callback for enabling - we want to update values first before enabling
            #  self.set_motor_GB_enabled(True)
             self.instructionThreadRunning = False
             self.run_angles_PB.setText("Run")
             if self.instructionThread is not None and self.instructionThread.isRunning():
                 self.instructionThread.stop()
    
    def end_motor_values_emit_callback(self,dataIn):
        for i in range(NUM_PINNAE_MOTORS):
            self.motor_value_SB[i].blockSignals(True)
            self.motor_value_SLIDER[i].blockSignals(True)
            
            self.motor_value_SB[i].setValue(dataIn[i])
            self.motor_value_SLIDER[i].setValue(dataIn[i])
            
            self.motor_value_SB[i].blockSignals(False)
            self.motor_value_SLIDER[i].blockSignals(False)
        # self.set_motor_GB_enabled(True)

    def instruction_T_contextMenu(self,position):
        context_menu = QMenu()

        add_row_action = context_menu.addAction("Add Row")
        delete_row_action = context_menu.addAction("Delete Row")
        duplicate_row_action = context_menu.addAction("Duplicate Row")
        paste_max_action = context_menu.addAction("Paste Max's")
        paste_min_action = context_menu.addAction("Paste Min's")
        paste_current_angles_action = context_menu.addAction("Paste Current Angles")
        action = context_menu.exec(self.instruction_TABLE.viewport().mapToGlobal(position))
        
        if action == add_row_action:
            self.instruction_TABLE_contextMenu_add_row()
        elif action == delete_row_action:
            self.instruction_TABLE_contextMenu_delete_row()
        elif action == duplicate_row_action:
            self.instruction_TABLE_contextMenu_duplicate_row()
        elif action == paste_max_action:
            self.instruction_TABLE_contextMenu_paste_maxs()
        elif action == paste_min_action:
            self.instruction_TABLE_contextMenu_paste_mins()
        elif action == paste_current_angles_action:
            self.instruction_TABLE_contextMenu_paste_current()

    def instruction_TABLE_contextMenu_add_row(self):
        rows = self.instruction_TABLE.rowCount() +1
        self.instruction_TABLE.setRowCount(rows)
        self.instruction_TABLE.update()

        for i in range(NUM_PINNAE_MOTORS):
            intNum = QTableWidgetItem()

            min = int(self.left_pinna.get_motor_min_limit(i))
            intNum.setData(0,min)
            self.instruction_TABLE.setItem(rows-1,i,intNum)


    def instruction_TABLE_contextMenu_delete_row(self):
        if self.instruction_TABLE.currentRow() >= 0:
            self.instruction_TABLE.removeRow(self.instruction_TABLE.currentRow())
            logging.debug("deleted row")

        if self.instruction_TABLE.rowCount() == 0:
            self.instruction_TABLE_contextMenu_add_row()

    def instruction_TABLE_contextMenu_duplicate_row(self):
        selected_row = self.instruction_TABLE.currentRow()
        num_rows = self.instruction_TABLE.rowCount()

        if selected_row >=0:
            row_items = [self.instruction_TABLE.item(selected_row,col).text() for col in range(NUM_PINNAE_MOTORS)]
            self.instruction_TABLE.setRowCount(num_rows+1)

            for col,text in enumerate(row_items):
                newItem = QTableWidgetItem()
                newItem.setData(0,int(text))
                self.instruction_TABLE.setItem(num_rows,col,newItem)

    def instruction_TABLE_contextMenu_paste_maxs(self):
        selected_row = self.instruction_TABLE.currentRow()

        if selected_row >=0:
            for col, max_val in enumerate(self.motor_max_limit_SB):
                newItem = QTableWidgetItem()
                newItem.setData(0,int(max_val.value()))
                self.instruction_TABLE.setItem(selected_row,col,newItem)

    def instruction_TABLE_contextMenu_paste_mins(self):
        selected_row = self.instruction_TABLE.currentRow()

        if selected_row >=0:
            for col, min_val in enumerate(self.motor_min_limit_SB):
                newItem = QTableWidgetItem()
                newItem.setData(0,int(min_val.value()))
                self.instruction_TABLE.setItem(selected_row,col,newItem)

    def instruction_TABLE_contextMenu_paste_current(self):
        selected_row = self.instruction_TABLE.currentRow()

        if selected_row >=0:
            for col, motor_val in enumerate(self.motor_value_SB):
                newItem = QTableWidgetItem()
                newItem.setData(0,int(motor_val.value()))
                self.instruction_TABLE.setItem(selected_row,col,newItem)
        
    
    def save_movements_PB_cb(self):
        fd = QFileDialog(self)

        file_path,_ = fd.getSaveFileName(None, "Save movements","","YAML Files (*.yaml)")
        
        if file_path:
            num_rows = self.instruction_TABLE.rowCount()
            
            array_2d = [[0] * NUM_PINNAE_MOTORS for _ in range(num_rows)]
            
            for row in range(num_rows):
                for col in range(NUM_PINNAE_MOTORS):
                    data = self.instruction_TABLE.item(row,col)
                    array_2d[row][col] = int(data.text())
                    
            data = {
                'pinna_movements': {
                    'speed': self.speed_SB.value(),
                    'angles': 
                        array_2d
                }
            }
            
                
            splitted = file_path.split(".")
            file_path = splitted[0]+"_PM.yaml" 
            print(f" save path {file_path}")
        
                
            with open(file_path,'w') as f:
                yaml.dump(data,f)
        else:
            print("no save")    
    
    
    def load_movements_PB_cb(self):
        fd = QFileDialog(self)
        fd.setWindowTitle("Open File")
        fd.setNameFilter('YAML files (*.yaml)')
        fd.setFileMode(QFileDialog.FileMode.ExistingFiles)
        
        if fd.exec():
            
            selected_files = fd.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                print("Selected file:", file_path)
                with open(file_path,'r') as f:
                    yam_file = yaml.safe_load(f)
                    
                if not 'pinna_movements' in yam_file:
                    win = QErrorMessage(self)
                    win.showMessage("Did not find valid 'pinna_movements' in file!")
                    return
                
                angles = yam_file["pinna_movements"]["angles"]
                print("Angles:")
                
                num_rows = len(angles)

                self.instruction_TABLE.clear()
                self.instruction_TABLE.setRowCount(num_rows)

                for row, angle_row in enumerate(angles):
                    for col,angle in enumerate(angle_row):
                        newItem = QTableWidgetItem()
                        newItem.setData(0,int( angle ))
                        self.instruction_TABLE.setItem(row,col,newItem)    
                
                self.speed_SB.setValue(int(yam_file["pinna_movements"]["speed"]))
                        
                    
                    
            else:
                return
        else:
            return


    def add_motor_control_CB(self):
        """Connects the motor tendons sliders to the api"""
        
        # attach max buttons
        for i in range(NUM_PINNAE_MOTORS):
            self.motor_max_PB[i].pressed.connect(lambda index=i: self.motor_max_PB_pressed(index))
        
        # attach max limit spinbox
        for i in range(NUM_PINNAE_MOTORS):
            self.motor_max_limit_SB[i].editingFinished.connect(lambda index=i: self.motor_max_limit_changed_CB(index))

            
        # attach min buttons
        for i in range(NUM_PINNAE_MOTORS):
            self.motor_min_PB[i].pressed.connect(lambda index=i: self.motor_min_PB_pressed(index))

        # attach min limit spinbox
        for i in range(NUM_PINNAE_MOTORS):
            self.motor_min_limit_SB[i].editingFinished.connect(lambda index=i: self.motor_min_limit_changed_CB(index))
            
            
        # attach set to zero buttons
        for i in range(NUM_PINNAE_MOTORS):
            self.motor_set_zero_PB[i].pressed.connect(lambda index=i: self.motor_set_zero_PB_callback(index))

        # attach sliders
        for i in range(NUM_PINNAE_MOTORS):
            self.motor_value_SLIDER[i].valueChanged.connect(lambda value, index=i: self.motor_value_SLIDER_valueChanged(index))
        
        # attach spinbox
        for i in range(NUM_PINNAE_MOTORS):
            self.motor_value_SB[i].editingFinished.connect(lambda index=i: self.motor_value_SB_valueChanged(index))
            



    def motor_GB_contextMenu(self,position,index) -> None:
        """Create menu for each motor box to reduce the number of buttons

        Args:
            position (int): passed from qt, position on context menu
            index (int): which motor box this is coming from
        """
        assert index < NUM_PINNAE_MOTORS, f"{index} is greater than number of pinnaes!"
        context_menu = QMenu()
        context_menu.addMenu(f"Motor {index+1}:")
        
        set_zero = context_menu.addAction("Set Zero")
        max_value = context_menu.addAction("Max")
        min_value = context_menu.addAction("Min")
        calibrate = context_menu.addAction("Calibrate Zero")
        
        action = context_menu.exec(self.motor_GB[index].mapToGlobal(position))
        
        if action == set_zero:
            self.motor_set_zero_PB_callback(index)
        elif action == max_value:
            self.motor_max_PB_pressed(index)
        elif action == min_value:
            self.motor_min_PB_pressed(index)
        elif action == calibrate:
            pass

        
    def motor_max_PB_pressed(self,index):
        """Sets the current motor to its max value

        Args:
            index (_type_): index of motor 
        """
        self.left_pinna.set_motor_to_max(index)
        self.right_pinna.set_motor_to_max(index)
        self.motor_value_SB[index].setValue(self.motor_max_limit_SB[index].value())
        self.motor_value_SLIDER[index].setValue(self.motor_max_limit_SB[index].value())
        
        
    def motor_min_PB_pressed(self,index):
        """Sets the current motor to its min value

        Args:
            index (_type_): index of motor
        """
        self.left_pinna.set_motor_to_min(index)
        self.right_pinna.set_motor_to_min(index)
        self.motor_value_SB[index].setValue(self.motor_min_limit_SB[index].value())
        self.motor_value_SLIDER[index].setValue(self.motor_min_limit_SB[index].value())
        
        
    def motor_value_SB_valueChanged(self,index):
        """Sets the new spin

        Args:
            index (_type_): index to change
        """
        if self.motor_value_SB[index].value() != self.motor_value_SLIDER[index].value():
            self.motor_value_SLIDER[index].setValue(self.motor_value_SB[index].value())
            if index != 6 and index != 5:
                self.left_pinna.set_motor_angle(index, self.motor_value_SLIDER[index].value())
                self.right_pinna.set_motor_angle(index, self.motor_value_SLIDER[index].value())
            else:
                if index == 5:
                    self.left_pinna.set_motor_angle(index, self.motor_value_SLIDER[index].value())
                elif index == 6:    
                    self.right_pinna.set_motor_angle(5, self.motor_value_SLIDER[index].value())
        
        
    def motor_value_SLIDER_valueChanged(self,index):
        """Sets the slider value

        Args:
            index (_type_): index to change
        """
        if self.motor_value_SLIDER[index].value() != self.motor_value_SB[index].value():
            self.motor_value_SB[index].setValue(self.motor_value_SLIDER[index].value())
            if index != 6 and index != 5:
                self.left_pinna.set_motor_angle(index, self.motor_value_SLIDER[index].value())
                self.right_pinna.set_motor_angle(index, self.motor_value_SLIDER[index].value())
            else:
                if index == 5:
                    self.left_pinna.set_motor_angle(index, self.motor_value_SLIDER[index].value())
                elif index == 6:    
                    self.right_pinna.set_motor_angle(5, self.motor_value_SLIDER[index].value())
    
    
    def motor_set_zero_PB_callback(self,index):
        """Callback for when the set new zero push button is set

        Args:
            index (_type_): changing motor new zero position
        """
        self.left_pinna.set_new_zero_position(index)
        self.right_pinna.set_new_zero_position(index)
        [min,max] = self.left_pinna.get_motor_limit(index)
        
        # adjust the new limits of spinbox
        self.motor_max_limit_SB[index].setValue(max)
        self.motor_min_limit_SB[index].setValue(min)
        
        # set new values to 0
        self.motor_value_SB[index].setValue(0)
        self.motor_value_SLIDER[index].setValue(0)
        
        
    def motor_max_limit_changed_CB(self,index):
        """callback when limit spinbox is changed

        Args:
            index (_type_): index of motors
        """
        
        new_value = self.motor_max_limit_SB[index].value()
        
        if  self.left_pinna.set_motor_max_limit(index,new_value) and self.right_pinna.set_motor_max_limit(index,new_value):
            [min,max] = self.left_pinna.get_motor_limit(index)
            self.motor_value_SLIDER[index].setRange(min,max)
            self.motor_value_SB[index].setRange(min,max)
            num_rows = self.instruction_TABLE.rowCount()
            for i in range(num_rows):
                self.instruction_TABLE_cellChanged_callback(i,index)


        else:
            self.motor_max_limit_SB[index].setValue(self.left_pinna.get_motor_max_limit(index))
            error_msg = QErrorMessage(self)
            error_msg.showMessage("New max is greater than current angle!")

    def motor_min_limit_changed_CB(self,index):
        """callback when limit spinbox is changed

        Args:
            index (_type_): index of motors
        """
        
        new_value = self.motor_min_limit_SB[index].value()
        
        if self.left_pinna.set_motor_min_limit(index,new_value) and self.right_pinna.set_motor_min_limit(index,new_value):
            [min,max] = self.left_pinna.get_motor_limit(index)
            self.motor_value_SLIDER[index].setRange(min,max)
            self.motor_value_SB[index].setRange(min,max)
            num_rows = self.instruction_TABLE.rowCount()
            for i in range(num_rows):
                self.instruction_TABLE_cellChanged_callback(i,index)

        else:
            self.motor_min_limit_SB[index].setValue(self.left_pinna.get_motor_min_limit(index))
            error_msg = QErrorMessage(self)
            error_msg.showMessage("New min is less than current angle!")

    def instruction_TABLE_cellChanged_callback(self,row,column):
        """called when table cell values are changed

        Args:
            row (int): row index
            column (int): col index
        """
        logging.debug("instruction_TABLE_cellChanged")

        new_value = float(self.instruction_TABLE.item(row,column).text())
        # clamp against max value
        if new_value > self.left_pinna.get_motor_max_limit(column):
            # clamp the value
            newItem = QTableWidgetItem()
            newItem.setData(0,int(self.left_pinna.get_motor_max_limit(column)))
            print(self.left_pinna.get_motor_max_limit(column))
            self.instruction_TABLE.setItem(row,column,newItem)
            logging.debug("Clamped value max")

        # clamp against min value
        if new_value < self.left_pinna.get_motor_min_limit(column):
            # clamp
            newItem = QTableWidgetItem()
            newItem.setData(0,int(self.left_pinna.get_motor_min_limit(column)))
            self.instruction_TABLE.setItem(row,column,newItem)
            logging.debug("Clamped value min")
class RunInstructionsThread(QThread):
   cycle_complete = pyqtSignal(int)
   end_motor_angles = pyqtSignal(list)

   def __init__(self,dataArray,freq,l_pinna: PinnaeController, r_pinna: PinnaeController = None):
       QThread.__init__(self)
       self.data = dataArray
       self.timeBetween = 1/freq
       self.runThread = True
       self.curIndex = 0
       self.maxIndex = len(dataArray)
       self.l_pinna = l_pinna
       self.r_pinna = r_pinna
       self.cycle_count = 0
       
   def run(self):
       logging.debug("RunInstructionsThread starting")
       right_data = self.data.copy()
       if self.r_pinna is not None:
           right_data[:,5] = self.data[:,6]

           
       while self.runThread:
           self.l_pinna.set_motor_angles(self.data[self.curIndex])
           self.r_pinna.set_motor_angles(right_data[self.curIndex])
           
        #    print(self.data[self.curIndex])
           self.curIndex+=1
           if self.curIndex >= self.maxIndex:
               self.curIndex = 0
               self.cycle_count += 1
               self.cycle_complete.emit(self.cycle_count)
           
           time.sleep(self.timeBetween)
       
       self.end_motor_angles.emit(self.l_pinna.current_angles)
       logging.debug("RunInstructionsThread exiting")
       
   def stop(self):
       self.runThread = False

if __name__ == "__main__":
    app = QApplication([])
    widget = PinnaWidget(PinnaeController(SpiDev(0,0)),PinnaeController(SpiDev(0,1)))
    widget.show()
    sys.exit(app.exec())