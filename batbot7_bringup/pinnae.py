#!/usr/bin/env python

# controls the pinnaes using SPI connection to the grandcentral controllers
# author: Mason Lopez

import logging
import signal
logging.basicConfig(level=logging.DEBUG)
from serial import Serial
from batbot7_bringup.serial.bb_serial import BB_Serial

signal.signal(signal.SIGINT, signal.SIG_DFL)

# for developing on not the PI we create fake library
# that mimics spidev
try:
    from spidev import SpiDev
except ImportError:
    logging.error("pinnae.py:: no spidev found, developing on different os ")
    from batbot7_bringup.serial.fake_spidev import fake_SpiDev as SpiDev

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
    QErrorMessage,
    QMenu,
    QTableWidget,
    QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import sys
import qdarkstyle

from batbot7_bringup.PinnaeController import PinnaeController, NUM_PINNAE_MOTORS

class PinnaWidget(QWidget):
    main_v_layout = QVBoxLayout()

    def __init__(self,l_pinna:PinnaeController, r_pinna:PinnaeController):
        QWidget.__init__(self)
        
        self.pinnae = l_pinna
        
        self.setWindowTitle("Tendon Controller")
        self.setWindowIcon(QIcon('HBAT.jpg'))
        self.add_settings_box()
        self.add_motor_controls()
        self.add_table()
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
        
        self.setLayout(self.main_v_layout)

    def add_settings_box(self):
        grid_lay = QGridLayout()

        self.read_limits_PB = QPushButton("Query Limits")
        grid_lay.addWidget(self.read_limits_PB,0,0)

        self.calibrate_limits = QPushButton("Calibrate Motors")
        grid_lay.addWidget(self.calibrate_limits,1,0)

        self.load_file = QPushButton("Load File")
        self.load_file.clicked.connect(self.load_file_CB)
        grid_lay.addWidget(self.load_file,0,1)

        self.create_file = QPushButton("Create File")
        self.create_file.clicked.connect(self.create_file_CB)
        grid_lay.addWidget(self.create_file,1,1)

        # grid_lay.addWidget(QLabel("Motion File:"),0,2)
        # self.file_name = QLineEdit()
        # grid_lay.addWidget(self.file_name,0,3)


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
        self.instruction_T = QTableWidget(1,NUM_PINNAE_MOTORS+1)
        hlay.addWidget(self.instruction_T)
        self.instruction_T.setHorizontalHeaderLabels(["M1","M2","M3","M4","M5","M6","M7","Time"])
        
        #-------------------------------------------------
        buttonGB = QGroupBox("Settings")
        vlay = QVBoxLayout()

        self.run_angles_PB = QPushButton("Run")
        vlay.addWidget(self.run_angles_PB)

        self.step_back_PB = QPushButton("Step Backward")
        vlay.addWidget(self.step_back_PB)

        self.step_forward_PB = QPushButton("Step Forward")
        vlay.addWidget(self.step_forward_PB)

        self.new_row_PB = QPushButton("+ Row")
        vlay.addWidget(self.new_row_PB)

        self.delete_row_PB = QPushButton("- Row")
        vlay.addWidget(self.delete_row_PB)

        self.paste_angles_PB = QPushButton("Paste Current Angles")
        vlay.addWidget(self.paste_angles_PB)


        buttonGB.setLayout(vlay)
        #-------------------------------------------------
        hlay.addWidget(buttonGB)

        self.main_v_layout.addLayout(hlay)
        
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
            
        # adjust the slider and spinbox range
        for i in range(NUM_PINNAE_MOTORS):
            self.motor_max_limit_changed_CB(i)


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
        self.pinnae.set_motor_to_max(index)
        self.motor_value_SB[index].setValue(self.motor_max_limit_SB[index].value())
        self.motor_value_SLIDER[index].setValue(self.motor_max_limit_SB[index].value())
        
        
    def motor_min_PB_pressed(self,index):
        """Sets the current motor to its min value

        Args:
            index (_type_): index of motor
        """
        self.pinnae.set_motor_to_min(index)
        self.motor_value_SB[index].setValue(self.motor_min_limit_SB[index].value())
        self.motor_value_SLIDER[index].setValue(self.motor_min_limit_SB[index].value())
        
        
    def motor_value_SB_valueChanged(self,index):
        """Sets the new spin

        Args:
            index (_type_): index to change
        """
        if self.motor_value_SB[index].value() != self.motor_value_SLIDER[index].value():
            self.motor_value_SLIDER[index].setValue(self.motor_value_SB[index].value())
            self.pinnae.set_motor_angle(index, self.motor_value_SB[index].value())
        
        
    def motor_value_SLIDER_valueChanged(self,index):
        """Sets the slider value

        Args:
            index (_type_): index to change
        """
        if self.motor_value_SLIDER[index].value() != self.motor_value_SB[index].value():
            self.motor_value_SB[index].setValue(self.motor_value_SLIDER[index].value())
            self.pinnae.set_motor_angle(index,self.motor_value_SLIDER[index].value())
    
    
    def motor_set_zero_PB_callback(self,index):
        """Callback for when the set new zero push button is set

        Args:
            index (_type_): changing motor new zero position
        """
        self.pinnae.set_new_zero_position(index)
        [min,max] = self.pinnae.get_motor_limit(index)
        
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
        
        if  self.pinnae.set_motor_max_limit(index,new_value):
            [min,max] = self.pinnae.get_motor_limit(index)
            self.motor_value_SLIDER[index].setRange(min,max)
            self.motor_value_SB[index].setRange(min,max)
            


        else:
            self.motor_max_limit_SB[index].setValue(self.pinnae.get_motor_max_limit(index))
            error_msg = QErrorMessage(self)
            error_msg.showMessage("New max is greater than current angle!")

    def motor_min_limit_changed_CB(self,index):
        """callback when limit spinbox is changed

        Args:
            index (_type_): index of motors
        """
        
        new_value = self.motor_min_limit_SB[index].value()
        
        if self.pinnae.set_motor_min_limit(index,new_value):
            [min,max] = self.pinnae.get_motor_limit(index)
            self.motor_value_SLIDER[index].setRange(min,max)
            self.motor_value_SB[index].setRange(min,max)

        else:
            self.motor_min_limit_SB[index].setValue(self.pinnae.get_motor_min_limit(index))
            error_msg = QErrorMessage(self)
            error_msg.showMessage("New min is less than current angle!")
    

if __name__ == "__main__":
    app = QApplication([])
    widget = PinnaWidget(PinnaeController(serial_dev = BB_Serial("/dev/ttyACM0")),PinnaeController(spiObj = SpiDev(0, 0)))
    widget.show()
    sys.exit(app.exec())