"""Current working tendon controller for the BatBot. This system works with SPI to control one pinnae."""

import typing
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLayout,
    QGroupBox,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QComboBox,
    QSlider,
    QSpinBox,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QCheckBox,
    QAbstractItemView,
    QMenu,
    QLineEdit,
)
from PyQt6.QtCore import Qt, QFile, QTextStream, QThread, pyqtSignal, QObject

import sys, os
import serial
import serial.tools.list_ports
import time
import numpy as np

# logging stuff
import logging

logging.basicConfig(level=logging.DEBUG)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# for developing on not the PI we create fake library
# that mimics spidev
try:
    from spidev import SpiDev
except ImportError:
    logging.error("no spidev found, developing on different os ")
    from fake_spidev import fake_SpiDev as SpiDev


class Widget(QWidget):
    # thread stuff
    serialThread = None
    instructionThread = None
    instructionThreadRunning = False

    row2 = None
    allMotorsBox = None
    instructionsBox = None

    spiBus = 0
    spiDev = 0
    spi = SpiDev()

    def __init__(self):
        QWidget.__init__(self)
        # ~ self.setGeometry(0, 0, 400, 400)
        self.setWindowTitle("Tendon Motor Controller")

        # main layout of system
        self.mainVerticalLayout = QVBoxLayout()

        # add serial box
        self.add_spi_layout()

        # add individual motor control box
        self.add_indiviual_motor_control_box()
        self.connect_valueChanged()

        # add mapped instruction box
        self.add_allMotor_and_instruction_box()

        # set final layout
        self.setLayout(self.mainVerticalLayout)

    # ---------------------------------------------------------------------------------
    # adding layouts
    def add_spi_layout(self):
        """Adds the serial box layout"""
        # box container
        serialGB = QGroupBox("SPI")
        hLay = QHBoxLayout()

        # search port button
        self.searchSPIPortPB = QPushButton("Search")
        self.searchSPIPortPB.setFixedWidth(65)
        self.searchSPIPortPB.setToolTip("Click to search for SPI..")
        hLay.addWidget(self.searchSPIPortPB)

        # add horizontal layout to box
        serialGB.setLayout(hLay)

        # set max serial box height
        serialGB.setFixedHeight(80)

        # push box to main layout
        self.mainVerticalLayout.addWidget(serialGB)

        self.spi.open(self.spiBus, self.spiDev)
        self.spi.mode = 0
        self.spi.max_speed_hz = 500000

        # connect callbacks
        # ~ self.serialObj = None
        # ~ self.isSerialObjConnected = False

    def add_indiviual_motor_control_box(self):
        """Adds individual motor control box"""
        # box container
        motorControlGB = QGroupBox("Individual Motor Control")

        # horizontal layout for 6 motors
        hLay = QHBoxLayout()

        # min endpoint to spin motor
        self.minMotorAngleSB = [
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
        ]

        # max endpoint to spin motor
        self.maxMotorAngleSB = [
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
        ]

        # sets value to max
        self.setMotorAngleMaxPB = [
            QPushButton("Max"),
            QPushButton("Max"),
            QPushButton("Max"),
            QPushButton("Max"),
            QPushButton("Max"),
            QPushButton("Max"),
        ]

        # set value to min
        self.setMotorAngleMinPB = [
            QPushButton("Min"),
            QPushButton("Min"),
            QPushButton("Min"),
            QPushButton("Min"),
            QPushButton("Min"),
            QPushButton("Min"),
        ]

        # sliders for motor angle
        self.motorAngleSliders = [
            QSlider(Qt.Orientation.Horizontal),
            QSlider(Qt.Orientation.Horizontal),
            QSlider(Qt.Orientation.Horizontal),
            QSlider(Qt.Orientation.Horizontal),
            QSlider(Qt.Orientation.Horizontal),
            QSlider(Qt.Orientation.Horizontal),
        ]

        # spinbox for angle
        self.motorAngleSB = [
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
        ]

        # tells MCU to mark as new center
        self.setNewMotorZeroPB = [
            QPushButton("Set as zero"),
            QPushButton("Set as zero"),
            QPushButton("Set as zero"),
            QPushButton("Set as zero"),
            QPushButton("Set as zero"),
            QPushButton("Set as zero"),
        ]

        # limits for angles
        min = -180
        max = 180

        # add items to hLay
        for i in range(6):
            # each motor gets invididual box
            motorGB = QGroupBox(f"Motor {i+1}")
            vMotorLay = QVBoxLayout()

            # config slider
            self.motorAngleSliders[i].setRange(min, max)
            self.motorAngleSliders[i].setValue(0)
            # self.motorAngleSliders[i].setTickPosition(QSlider.TicksAbove)
            self.motorAngleSliders[i].setToolTip("Drag to change angle of motor")

            # config angle spinbox
            self.motorAngleSB[i].setRange(min, max)
            self.motorAngleSB[i].setValue(0)
            self.motorAngleSB[i].setSuffix(" deg")

            # config min max angle spinboxes
            self.minMotorAngleSB[i].setRange(-10000, 10000)
            self.minMotorAngleSB[i].setValue(min)
            self.maxMotorAngleSB[i].setRange(-10000, 10000)
            self.maxMotorAngleSB[i].setValue(max)
            self.minMotorAngleSB[i].setToolTip("Change min value for slider bar")
            self.minMotorAngleSB[i].setToolTip("Change max value for slider bar")

            # min max zero buttons
            self.setMotorAngleMaxPB[i].setToolTip("Set motor angle to max")
            self.setMotorAngleMaxPB[i].setFixedWidth(50)
            self.setMotorAngleMinPB[i].setToolTip("Set motor angle to min")
            self.setNewMotorZeroPB[i].setToolTip(
                "Tells drive board this is new 0 location"
            )

            # add min max SB horizontally
            minMaxGB = QGroupBox("Limits")
            minMaxHLay = QHBoxLayout()
            minMaxHLay.addWidget(self.minMotorAngleSB[i])
            minMaxHLay.addWidget(self.maxMotorAngleSB[i])
            minMaxGB.setLayout(minMaxHLay)
            minMaxGB.setFixedHeight(80)
            vMotorLay.addWidget(minMaxGB)

            # adjustment box with slider and spinner
            controlBox = QGroupBox("Control")
            controlVLay = QVBoxLayout()
            PBHLay = QHBoxLayout()
            PBHLay.addWidget(self.setMotorAngleMinPB[i])  # min PB
            PBHLay.addWidget(self.setMotorAngleMaxPB[i])  # max PB
            controlVLay.addLayout(PBHLay)  # add to control layout
            controlVLay.addWidget(self.motorAngleSliders[i])  # add slider
            controlVLay.addWidget(self.motorAngleSB[i])  # add spinbox
            controlVLay.addWidget(self.setNewMotorZeroPB[i])

            controlBox.setLayout(controlVLay)
            controlBox.setMinimumWidth(80)
            vMotorLay.addWidget(controlBox)  # add box to layout

            motorGB.setLayout(vMotorLay)
            hLay.addWidget(motorGB)

        # add to motor control layout
        motorControlGB.setLayout(hLay)
        self.row2 = motorControlGB

        # push to main vertical layout
        self.mainVerticalLayout.addWidget(motorControlGB)

    def add_allMotor_and_instruction_box(self):
        """adds instruction box to widget"""
        min = -180
        max = 180
        rowLay = QHBoxLayout()

        # ----------------------------------------------------
        # all motor controller box
        allMotorGB = QGroupBox("All Motors")
        allMotorVLay = QVBoxLayout()
        ### limits box
        limitsGB = QGroupBox("Limits")
        limitsHLay = QHBoxLayout()

        # min angle
        self.allMinMotorAngleSB = QSpinBox()
        self.allMinMotorAngleSB.setRange(-10000, 10000)
        self.allMinMotorAngleSB.setValue(min)

        # max angle
        self.allMaxMotorAngleSB = QSpinBox()
        self.allMaxMotorAngleSB.setRange(-10000, 10000)
        self.allMaxMotorAngleSB.setValue(max)

        # add to layout
        limitsHLay.addWidget(self.allMinMotorAngleSB)
        limitsHLay.addWidget(self.allMaxMotorAngleSB)
        limitsGB.setLayout(limitsHLay)
        allMotorVLay.addWidget(limitsGB)

        ### controls box
        controlsGB = QGroupBox("Controls")
        controlsVLay = QVBoxLayout()
        PBHLay = QHBoxLayout()
        # min zero max button layout
        self.setAllMotorsAngleMinPB = QPushButton("Min")
        self.setAllMotorsAngleZeroPB = QPushButton("Zero")
        self.setAllMotorsAngleMaxPB = QPushButton("Max")
        PBHLay.addWidget(self.setAllMotorsAngleMinPB)
        PBHLay.addWidget(self.setAllMotorsAngleZeroPB)
        PBHLay.addWidget(self.setAllMotorsAngleMaxPB)
        controlsVLay.addLayout(PBHLay)
        # slider
        self.allMotorAngleSlider = QSlider(Qt.Orientation.Horizontal)
        self.allMotorAngleSlider.setRange(min, max)
        self.allMotorAngleSlider.setValue(0)
        controlsVLay.addWidget(self.allMotorAngleSlider)
        # spinner
        self.allMotorAngleSB = QSpinBox()
        self.allMotorAngleSB.setRange(min, max)
        self.allMotorAngleSB.setValue(0)
        self.allMotorAngleSB.setSuffix(" deg")
        controlsVLay.addWidget(self.allMotorAngleSB)
        # adds to individual angles checkbox
        self.addToAngleCB = QCheckBox("Add to individual angles")
        controlsVLay.addWidget(self.addToAngleCB)
        controlsGB.setLayout(controlsVLay)
        allMotorVLay.addWidget(controlsGB)

        allMotorGB.setLayout(allMotorVLay)
        allMotorGB.setFixedWidth(250)
        self.allMotorsBox = allMotorGB
        rowLay.addWidget(allMotorGB)

        # connect callbacks
        #   slider and spinbox value changes
        self.allMotorAngleSB.editingFinished.connect(
            self.allMotorAngleSB_editingFinished_callback
        )
        self.allMotorAngleSlider.valueChanged.connect(
            self.allMotorAngleSlider_valueChanged_callback
        )

        #   max min zero buttons
        self.setAllMotorsAngleZeroPB.pressed.connect(
            lambda: self.allMotorAngleSlider.setValue(0)
        )
        self.setAllMotorsAngleMaxPB.pressed.connect(
            lambda: self.allMotorAngleSlider.setValue(self.allMaxMotorAngleSB.value())
        )
        self.setAllMotorsAngleMinPB.pressed.connect(
            lambda: self.allMotorAngleSlider.setValue(self.allMinMotorAngleSB.value())
        )

        # limits change
        self.allMaxMotorAngleSB.editingFinished.connect(
            self.allMaxMotorAngleSB_editingFinished_callback
        )
        self.allMinMotorAngleSB.editingFinished.connect(
            self.allMinMotorAngleSB_editingFinished_callback
        )

        # ----------------------------------------------------
        instGB = QGroupBox("Instructions")
        instHLay = QHBoxLayout()

        # serial ouput
        self.serialOutputTE = QTextEdit()
        self.serialOutputTE.setFixedWidth(300)
        self.serialOutputTE.setFixedHeight(275)
        instHLay.addWidget(self.serialOutputTE)

        # yaml instructions
        self.inputT = QTableWidget()
        self.inputT.setRowCount(1)
        self.inputT.setColumnCount(6)

        # connect callback
        self.inputT.cellChanged.connect(self.inputT_cellChanged_callback)

        # set zero values
        for i in range(6):
            intNum = QTableWidgetItem()
            intNum.setData(0, 0)
            self.inputT.setItem(0, i, intNum)

        # add contenx menu
        self.inputT.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.inputT.customContextMenuRequested.connect(self.inputT_contextMenu)

        # set column widths
        widthVal = 60
        for i in range(6):
            self.inputT.setColumnWidth(i, widthVal)
        self.inputT.setFixedWidth(widthVal * 6 + 20)

        instHLay.addWidget(self.inputT)

        # settings group box
        buttonGB = QGroupBox("Settings")
        # buttonGB.setFixedWidth(100)
        buttonVLay = QVBoxLayout()

        # start button
        self.startInstPB = QPushButton("Start")
        self.startInstPB.pressed.connect(self.startInstPB_pressed_callback)
        self.startInstPB.setToolTip("runs through defined angles")
        buttonVLay.addWidget(self.startInstPB)

        # time between instructions time
        self.timeStepSB = QSpinBox()
        self.timeStepSB.setSuffix(" hz")
        self.timeStepSB.setValue(1)
        self.timeStepSB.setToolTip("frequency motors change position")
        buttonVLay.addWidget(self.timeStepSB)

        # count of number of cycles
        self.cycleCountSB = QSpinBox()
        self.cycleCountSB.setDisabled(True)
        self.cycleCountSB.setSuffix(" cycles")
        self.cycleCountSB.setRange(0, 2147483647)
        buttonVLay.addWidget(self.cycleCountSB)

        # add row button
        self.addRowPB = QPushButton("Add")
        self.addRowPB.pressed.connect(self.addRowPB_pressed_callback)
        self.addRowPB.setToolTip("add new row to instruction table")
        buttonVLay.addWidget(self.addRowPB)

        # duplicate row button
        self.duplicateRowPB = QPushButton("Duplicate")
        self.duplicateRowPB.setToolTip("Duplicates highlighted row")
        buttonVLay.addWidget(self.duplicateRowPB)

        # copy current angles
        self.copyCurAnglesPB = QPushButton("Copy Current Angles")
        self.copyCurAnglesPB.setToolTip("copies current angles into row")
        self.copyCurAnglesPB.pressed.connect(self.copyCurAnglesPB_pressed_callback)
        buttonVLay.addWidget(self.copyCurAnglesPB)

        # remove row button
        self.removeRowPB = QPushButton("Remove")
        self.removeRowPB.pressed.connect(self.removeRowPB_callback)
        buttonVLay.addWidget(self.removeRowPB)

        buttonGB.setLayout(buttonVLay)
        instHLay.addWidget(buttonGB)

        instGB.setLayout(instHLay)
        rowLay.addWidget(instGB)

        self.instructionsBox = instGB

        self.mainVerticalLayout.addLayout(rowLay)

    # ---------------------------------------------------------------------------------
    # individual motor control setup
    def connect_valueChanged(self):
        """Connects value changed slider and spinbox"""

        # connects slider changed to spinbox
        self.motorAngleSliders[0].valueChanged.connect(
            lambda: self.motorAngleSliders_valueChanged_callback(0)
        )
        self.motorAngleSliders[1].valueChanged.connect(
            lambda: self.motorAngleSliders_valueChanged_callback(1)
        )
        self.motorAngleSliders[2].valueChanged.connect(
            lambda: self.motorAngleSliders_valueChanged_callback(2)
        )
        self.motorAngleSliders[3].valueChanged.connect(
            lambda: self.motorAngleSliders_valueChanged_callback(3)
        )
        self.motorAngleSliders[4].valueChanged.connect(
            lambda: self.motorAngleSliders_valueChanged_callback(4)
        )
        self.motorAngleSliders[5].valueChanged.connect(
            lambda: self.motorAngleSliders_valueChanged_callback(5)
        )

        # connects spin box
        self.motorAngleSB[0].editingFinished.connect(
            lambda: self.motorAngleSB_editingFinished_callback(0)
        )
        self.motorAngleSB[1].editingFinished.connect(
            lambda: self.motorAngleSB_editingFinished_callback(1)
        )
        self.motorAngleSB[2].editingFinished.connect(
            lambda: self.motorAngleSB_editingFinished_callback(2)
        )
        self.motorAngleSB[3].editingFinished.connect(
            lambda: self.motorAngleSB_editingFinished_callback(3)
        )
        self.motorAngleSB[4].editingFinished.connect(
            lambda: self.motorAngleSB_editingFinished_callback(4)
        )
        self.motorAngleSB[5].editingFinished.connect(
            lambda: self.motorAngleSB_editingFinished_callback(5)
        )

        # connect max value button
        self.setMotorAngleMaxPB[0].pressed.connect(
            lambda: self.motorAngleSliders[0].setValue(self.maxMotorAngleSB[0].value())
        )
        self.setMotorAngleMaxPB[1].pressed.connect(
            lambda: self.motorAngleSliders[1].setValue(self.maxMotorAngleSB[1].value())
        )
        self.setMotorAngleMaxPB[2].pressed.connect(
            lambda: self.motorAngleSliders[2].setValue(self.maxMotorAngleSB[2].value())
        )
        self.setMotorAngleMaxPB[3].pressed.connect(
            lambda: self.motorAngleSliders[3].setValue(self.maxMotorAngleSB[3].value())
        )
        self.setMotorAngleMaxPB[4].pressed.connect(
            lambda: self.motorAngleSliders[4].setValue(self.maxMotorAngleSB[4].value())
        )
        self.setMotorAngleMaxPB[5].pressed.connect(
            lambda: self.motorAngleSliders[5].setValue(self.maxMotorAngleSB[5].value())
        )

        # connect min value button
        self.setMotorAngleMinPB[0].pressed.connect(
            lambda: self.motorAngleSliders[0].setValue(self.minMotorAngleSB[0].value())
        )
        self.setMotorAngleMinPB[1].pressed.connect(
            lambda: self.motorAngleSliders[1].setValue(self.minMotorAngleSB[1].value())
        )
        self.setMotorAngleMinPB[2].pressed.connect(
            lambda: self.motorAngleSliders[2].setValue(self.minMotorAngleSB[2].value())
        )
        self.setMotorAngleMinPB[3].pressed.connect(
            lambda: self.motorAngleSliders[3].setValue(self.minMotorAngleSB[3].value())
        )
        self.setMotorAngleMinPB[4].pressed.connect(
            lambda: self.motorAngleSliders[4].setValue(self.minMotorAngleSB[4].value())
        )
        self.setMotorAngleMinPB[5].pressed.connect(
            lambda: self.motorAngleSliders[5].setValue(self.minMotorAngleSB[5].value())
        )

        # connect minAngle spinbox
        self.minMotorAngleSB[0].editingFinished.connect(
            lambda: self.minMotorAngleSB_editingFinished_callback(0)
        )
        self.minMotorAngleSB[1].editingFinished.connect(
            lambda: self.minMotorAngleSB_editingFinished_callback(1)
        )
        self.minMotorAngleSB[2].editingFinished.connect(
            lambda: self.minMotorAngleSB_editingFinished_callback(2)
        )
        self.minMotorAngleSB[3].editingFinished.connect(
            lambda: self.minMotorAngleSB_editingFinished_callback(3)
        )
        self.minMotorAngleSB[4].editingFinished.connect(
            lambda: self.minMotorAngleSB_editingFinished_callback(4)
        )
        self.minMotorAngleSB[5].editingFinished.connect(
            lambda: self.minMotorAngleSB_editingFinished_callback(5)
        )

        # connect maxAngle spinbox
        self.maxMotorAngleSB[0].editingFinished.connect(
            lambda: self.maxMotorAngleSB_editingFinished_callback(0)
        )
        self.maxMotorAngleSB[1].editingFinished.connect(
            lambda: self.maxMotorAngleSB_editingFinished_callback(1)
        )
        self.maxMotorAngleSB[2].editingFinished.connect(
            lambda: self.maxMotorAngleSB_editingFinished_callback(2)
        )
        self.maxMotorAngleSB[3].editingFinished.connect(
            lambda: self.maxMotorAngleSB_editingFinished_callback(3)
        )
        self.maxMotorAngleSB[4].editingFinished.connect(
            lambda: self.maxMotorAngleSB_editingFinished_callback(4)
        )
        self.maxMotorAngleSB[5].editingFinished.connect(
            lambda: self.maxMotorAngleSB_editingFinished_callback(5)
        )

        # connect setZero
        self.setNewMotorZeroPB[0].pressed.connect(
            lambda: self.setNewMotorZeroPB_pressed_callback(0)
        )
        self.setNewMotorZeroPB[1].pressed.connect(
            lambda: self.setNewMotorZeroPB_pressed_callback(1)
        )
        self.setNewMotorZeroPB[2].pressed.connect(
            lambda: self.setNewMotorZeroPB_pressed_callback(2)
        )
        self.setNewMotorZeroPB[3].pressed.connect(
            lambda: self.setNewMotorZeroPB_pressed_callback(3)
        )
        self.setNewMotorZeroPB[4].pressed.connect(
            lambda: self.setNewMotorZeroPB_pressed_callback(4)
        )
        self.setNewMotorZeroPB[5].pressed.connect(
            lambda: self.setNewMotorZeroPB_pressed_callback(5)
        )

    def motorAngleSB_editingFinished_callback(self, index):
        """Sets the slider and spin box values to 0"""
        # this prevents double calling since SB and slider and connected together
        if self.motorAngleSliders[index].value() != self.motorAngleSB[index].value():
            self.motorAngleSliders[index].setValue(
                int(self.motorAngleSB[index].value())
            )
            logging.debug("slider value chagned")
            # self.motorAngleSliders[index].setSliderPosition(int(self.motorAngleSB[index].value()))
            self.writeAllSPIData()

    def motorAngleSliders_valueChanged_callback(self, index):
        """When value is changed this gets called"""
        # this prevents double calling since SB and slider are connected together
        if self.motorAngleSliders[index].value() != self.motorAngleSB[index].value():
            self.motorAngleSB[index].setValue(
                int(self.motorAngleSliders[index].value())
            )
            logging.debug("SB value chagned")
            self.writeAllSPIData()

    def minMotorAngleSB_editingFinished_callback(self, index):
        """When min limits are changed"""
        logging.debug(f"minMotorAngleSB called: {index}")

        # change limits on slider and spinbox
        self.motorAngleSB[index].setMinimum(self.minMotorAngleSB[index].value())
        self.motorAngleSliders[index].setMinimum(self.minMotorAngleSB[index].value())

    def maxMotorAngleSB_editingFinished_callback(self, index):
        """When max limits are changed"""
        logging.debug(f"maxMotorAngleSB called: {index}")

        # change limits on slider and spinbox
        self.motorAngleSB[index].setMaximum(self.maxMotorAngleSB[index].value())
        self.motorAngleSliders[index].setMaximum(self.maxMotorAngleSB[index].value())

    def setNewMotorZeroPB_pressed_callback(self, index):
        """User requests that current angle be set as the zero point"""

        # change the limits
        self.maxMotorAngleSB[index].setValue(180)
        self.minMotorAngleSB[index].setValue(-180)

        # set the current value as zero
        self.motorAngleSliders[index].setValue(0)
        self.motorAngleSB[index].setValue(0)

        writeData = np.zeros(13, dtype=np.byte)

        # first index is used for telling motors to
        # set their current encoder positions as zero
        writeData[0] = index + 1

        writeData[1] = (self.motorAngleSB[0].value() >> 8) & 0xFF
        writeData[2] = (self.motorAngleSB[0].value()) & 0xFF

        writeData[3] = (self.motorAngleSB[1].value() >> 8) & 0xFF
        writeData[4] = (self.motorAngleSB[1].value()) & 0xFF

        writeData[5] = (self.motorAngleSB[2].value() >> 8) & 0xFF
        writeData[6] = (self.motorAngleSB[2].value()) & 0xFF

        writeData[7] = (self.motorAngleSB[3].value() >> 8) & 0xFF
        writeData[8] = (self.motorAngleSB[3].value()) & 0xFF

        writeData[9] = (self.motorAngleSB[4].value() >> 8) & 0xFF
        writeData[10] = (self.motorAngleSB[4].value()) & 0xFF

        writeData[11] = (self.motorAngleSB[5].value() >> 8) & 0xFF
        writeData[12] = (self.motorAngleSB[5].value()) & 0xFF
        writeData = writeData.tolist()

        self.spi.xfer2(writeData)

    # ---------------------------------------------------------------------------------
    # all motor control callbacks
    def allMotorAngleSB_editingFinished_callback(self):
        """when spin box value is changed"""
        if self.allMotorAngleSB.value() != self.allMotorAngleSlider.value():
            self.allMotorAngleSlider.setValue(self.allMotorAngleSB.value())
            logging.debug("allMotorAngleSB called")
            self.writeAllSPIData()

    def allMotorAngleSlider_valueChanged_callback(self):
        """when slider value is changed"""
        if self.allMotorAngleSB.value() != self.allMotorAngleSlider.value():
            self.allMotorAngleSB.setValue(self.allMotorAngleSlider.value())
            logging.debug("allMotorAngleSlider called")
            self.writeAllSPIData()

    def allMinMotorAngleSB_editingFinished_callback(self):
        """when all min value changes"""
        logging.debug("allMinMotorAngleSB called")
        self.allMotorAngleSB.setMinimum(self.allMinMotorAngleSB.value())
        self.allMotorAngleSlider.setMinimum(self.allMinMotorAngleSB.value())

    def allMaxMotorAngleSB_editingFinished_callback(self):
        """when all max value changes"""
        logging.debug("allMaxMotorAngleSB called")
        self.allMotorAngleSB.setMaximum(self.allMaxMotorAngleSB.value())
        self.allMotorAngleSlider.setMaximum(self.allMaxMotorAngleSB.value())

    # ---------------------------------------------------------------------------------
    # instruction table stuff
    def addRowPB_pressed_callback(self):
        """Adds new row to inputT, making the new table all 0's"""
        rows = self.inputT.rowCount() + 1
        self.inputT.setRowCount(rows)
        self.inputT.update()
        for i in range(6):
            intNum = QTableWidgetItem()
            intNum.setData(0, 0)
            self.inputT.setItem(rows - 1, i, intNum)
        logging.debug(f"inputT rows {rows}")

    def startInstPB_pressed_callback(self):
        """processes input table for usable data and sends to microcontroller"""
        logging.debug("startInstPB callback")

        if not self.instructionThreadRunning:
            # ~ dataArray = np.zeros((self.inputT.rowCount(),12),dtype=np.byte)
            dataArray = [bytearray(13) for _ in range(self.inputT.rowCount())]

            for row in range(self.inputT.rowCount()):
                # this is used to tell mcu which motor to set new zero position
                dataArray[row][0] = 0

                val = int(self.inputT.item(row, 0).text())
                dataArray[row][1] = (val >> 8) & 0xFF
                dataArray[row][2] = val & 0xFF
                val = int(self.inputT.item(row, 1).text())
                dataArray[row][3] = (val >> 8) & 0xFF
                dataArray[row][4] = val & 0xFF
                val = int(self.inputT.item(row, 2).text())
                dataArray[row][5] = (val >> 8) & 0xFF
                dataArray[row][6] = val & 0xFF
                val = int(self.inputT.item(row, 3).text())
                dataArray[row][7] = (val >> 8) & 0xFF
                dataArray[row][8] = val & 0xFF
                val = int(self.inputT.item(row, 4).text())
                dataArray[row][9] = (val >> 8) & 0xFF
                dataArray[row][10] = val & 0xFF
                val = int(self.inputT.item(row, 5).text())
                dataArray[row][11] = (val >> 8) & 0xFF
                dataArray[row][12] = val & 0xFF

            # print(dataArray)
            self.instructionThread = RunInstructionsThread(
                dataArray, self.timeStepSB.value(), self.spi
            )
            self.instructionThread.start()
            self.instructionThread.cycle_complete.connect(
                self.cycle_complete_emit_callback
            )
            self.instructionThreadRunning = True
            self.startInstPB.setText("Stop")
        else:
            self.instructionThreadRunning = False
            self.startInstPB.setText("Start")
            if (
                self.instructionThread is not None
                and self.instructionThread.isRunning()
            ):
                self.instructionThread.stop()

    def cycle_complete_emit_callback(self, dataIn):
        self.cycleCountSB.setValue(dataIn)

    def copyCurAnglesPB_pressed_callback(self):
        """Copies the current angles into table row"""
        logging.debug("copyCurAnglesPB called")
        rows = self.inputT.rowCount() + 1
        self.inputT.setRowCount(rows)
        self.inputT.update()
        for i in range(6):
            intNum = QTableWidgetItem()
            intNum.setData(0, self.motorAngleSB[i].value())
            self.inputT.setItem(rows - 1, i, intNum)

    def inputT_cellChanged_callback(self, row, column):
        """When values are changed in the table function is called to
        check if they are valid and not out of the scope"""
        logging.debug("inputT cellChanged")

        # check against its limits
        newVal = float(self.inputT.item(row, column).text())
        if newVal > self.maxMotorAngleSB[column].value():
            # clamp the value
            newItem = QTableWidgetItem()
            newItem.setData(0, self.maxMotorAngleSB[column].value())
            self.inputT.setItem(row, column, newItem)
            logging.debug("clamped to max")

        # clamp min value
        if newVal < self.minMotorAngleSB[column].value():
            # clamp the value
            newItem = QTableWidgetItem()
            newItem.setData(0, self.minMotorAngleSB[column].value())
            self.inputT.setItem(row, column, newItem)
            logging.debug("clamped to min")

    def removeRowPB_callback(self):
        """removes a row from the instruction table (instT)"""
        if self.inputT.rowCount() > 1:
            self.inputT.setRowCount(self.inputT.rowCount() - 1)

    def inputT_contextMenu(self, position):
        context_menu = QMenu()

        add_row_action = context_menu.addAction("Add Row")
        delete_row_action = context_menu.addAction("Delete Row")
        duplicate_row_action = context_menu.addAction("Duplicate Row")
        paste_max_action = context_menu.addAction("Paste Max's")
        paste_min_action = context_menu.addAction("Paste Min's")
        action = context_menu.exec(self.inputT.viewport().mapToGlobal(position))

        if action == add_row_action:
            self.addRowPB_pressed_callback()
        elif action == delete_row_action:
            self.inputT_CM_delete_row()
        elif action == duplicate_row_action:
            self.inputT_CM_duplicate_row()
        elif action == paste_max_action:
            self.inputT_CM_paste_max()
        elif action == paste_min_action:
            self.inputT_CM_paste_min()

    def inputT_CM_delete_row(self):
        """For context menu will delete the row that is selected"""
        if self.inputT.currentRow() >= 0:
            # remove the row
            self.inputT.removeRow(self.inputT.currentRow())
            logging.debug("inputT_CM_delete_row ")

    def inputT_CM_duplicate_row(self):
        """For context menu will duplicate the selected line"""
        selected_row = self.inputT.currentRow()
        num_rows = self.inputT.rowCount()

        if selected_row >= 0:
            # duplicate lines
            if selected_row >= 0:
                row_items = [
                    self.inputT.item(selected_row, col).text()
                    for col in range(self.inputT.columnCount())
                ]
                self.inputT.setRowCount(num_rows + 1)

                for col, text in enumerate(row_items):
                    newItem = QTableWidgetItem()
                    newItem.setData(0, float(text))
                    self.inputT.setItem(num_rows, col, newItem)

    def inputT_CM_paste_max(self):
        """pastes the max values into the row from the spinner box"""
        selected_row = self.inputT.currentRow()

        if selected_row >= 0:
            logging.debug("inputT CM past max")
            for col, maxSpinner in enumerate(self.maxMotorAngleSB):
                newItem = QTableWidgetItem()
                newItem.setData(0, float(maxSpinner.value()))
                self.inputT.setItem(selected_row, col, newItem)

    def inputT_CM_paste_min(self):
        """pastes the min values into the row from the spinner box"""
        selected_row = self.inputT.currentRow()

        if selected_row >= 0:
            logging.debug("inputT CM paste min")
            for col, minSpinner in enumerate(self.minMotorAngleSB):
                newItem = QTableWidgetItem()
                newItem.setData(0, float(minSpinner.value()))
                self.inputT.setItem(selected_row, col, newItem)

    # ---------------------------------------------------------------------------------

    def writeAllSPIData(self):
        """writes all spi data to device"""
        logging.debug("writeAllSPIData")
        # ~ writeData = bytearray(12)
        writeData = np.zeros(13, dtype=np.byte)

        # first index is used for telling motors to
        # set their current encoder positions as zero
        writeData[0] = 0

        writeData[1] = (self.motorAngleSB[0].value() >> 8) & 0xFF
        writeData[2] = (self.motorAngleSB[0].value()) & 0xFF

        writeData[3] = (self.motorAngleSB[1].value() >> 8) & 0xFF
        writeData[4] = (self.motorAngleSB[1].value()) & 0xFF

        writeData[5] = (self.motorAngleSB[2].value() >> 8) & 0xFF
        writeData[6] = (self.motorAngleSB[2].value()) & 0xFF

        writeData[7] = (self.motorAngleSB[3].value() >> 8) & 0xFF
        writeData[8] = (self.motorAngleSB[3].value()) & 0xFF

        writeData[9] = (self.motorAngleSB[4].value() >> 8) & 0xFF
        writeData[10] = (self.motorAngleSB[4].value()) & 0xFF

        writeData[11] = (self.motorAngleSB[5].value() >> 8) & 0xFF
        writeData[12] = (self.motorAngleSB[5].value()) & 0xFF
        writeData = writeData.tolist()

        self.spi.xfer2(writeData)

    def serialThread_emit_callback(self, dataIn):
        self.serialOutputTE.append(dataIn)

    def enableWidgets(self, isEnabled):
        """enables or disables all the widgets"""
        logging.debug(f"enableWidgets {isEnabled} called")
        self.row2.setEnabled(isEnabled)
        self.instructionsBox.setEnabled(isEnabled)
        self.allMotorsBox.setEnabled(isEnabled)

    def closeEvent(self, event):
        """When QtPy gets the request to close window, function makes sure
        the serial port and thread get closed safely"""
        logging.debug("Close event called")

        # close the thread
        if self.serialThread is not None and self.serialThread.isRunning():
            self.serialThread.stop()

        # check if serial object has been created and try to close it
        # ~ if self.serialObj is not None:
        # ~ self.serialObj.close()
        # ~ logging.debug("Serial object is closed")

        event.accept()


class ReadSerialThread(QThread):
    serialData = pyqtSignal(str)

    def __init__(self, serialDev):
        QThread.__init__(self)
        self.runThread = True
        self.serialObj = serialDev

    def run(self):
        logging.debug("ReadSerialThread starting")
        while self.runThread and self.serialObj.is_open:
            data = self.serialObj.readline().decode()
            # print(data)
            self.serialData.emit(data)
        logging.debug("ReadSerialThread exiting")

    def stop(self):
        self.runThread = False
        self.terminate()


class RunInstructionsThread(QThread):
    cycle_complete = pyqtSignal(int)

    def __init__(self, dataArray, freq, spiObj):
        QThread.__init__(self)
        self.data = dataArray
        self.timeBetween = 1 / freq
        self.runThread = True
        self.curIndex = 0
        self.maxIndex = len(dataArray)
        self.spiObj = spiObj
        self.cycle_count = 0

    def run(self):
        logging.debug("RunInstructionsThread starting")
        while self.runThread:
            self.spiObj.xfer2(self.data[self.curIndex])
            self.curIndex += 1
            if self.curIndex >= self.maxIndex:
                self.curIndex = 0
                self.cycle_count += 1
                self.cycle_complete.emit(self.cycle_count)

            time.sleep(self.timeBetween)

        logging.debug("RunInstructionsThread exiting")

    def stop(self):
        self.runThread = False
        self.terminate()


if __name__ == "__main__":
    app = QApplication([])

    widget = Widget()
    widget.show()

    sys.exit(app.exec())
