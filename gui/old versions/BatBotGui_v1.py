"""Author: Mason Lopez
    Date: November 13th
    About: This GUI controls the BatBot system, Tendons, GPS, and Sonar
    """
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
    QTabBar,
    QTabWidget,
    QGridLayout,
    QLineEdit,
    QSpacerItem,
    QDoubleSpinBox,
    QSizePolicy,

)
from PyQt6.QtCore import Qt, QFile, QTextStream, QThread, pyqtSignal,QObject
import sys
import serial
import serial.tools.list_ports
import time
import math
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from datetime import datetime 

# showing plots in qt from matlab
class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


# logging stuff
import logging
logging.basicConfig(level=logging.DEBUG)


class Widget(QWidget):
    """GUI for controlling Bat Bot"""
    
    # main vertical layout everything is added to
    mainVLay = QVBoxLayout()
    
    
    
    def __init__(self):
        """Adds all the widgets to GUI"""
        QWidget.__init__(self)
        self.setWindowTitle("Bat Bot 7 GUI")
        
        # add status layout
        # self.add_status_layout()
        
        # add experiment box
        self.add_experiment_layout()

        # add sonar and GPS controller box
        self.Add_Sonar_Box()

        # add pinnae controls layout
        self.add_pinnaeControlBox_layout()

        
        self.setLayout(self.mainVLay)
        
        
#----------------------------------------------------------------------
    # def add_status_layout(self):
    #     """Adds the status box layout"""
    #     self.statusBox = QGroupBox("Status")
    #     statusHLay = QHBoxLayout()
        
    #     # create status labels
    #     self.sonarStatusL = QLabel("Sonar: disconnected")
    #     self.gpsStatusL = QLabel("GPS: disconnected")
    #     self.leftEarStatusL = QLabel("Left Ear: disconnected")
    #     self.rightEarStatusL = QLabel("Right Ear: disconnected")
    #     # add to layout
    #     statusHLay.addWidget(self.sonarStatusL)
    #     statusHLay.addWidget(self.gpsStatusL)
    #     statusHLay.addWidget(self.leftEarStatusL)
    #     statusHLay.addWidget(self.rightEarStatusL)
        
    #     # create search button
    #     self.searchSPIDevsPB = QPushButton("Search")
    #     self.searchSPIDevsPB.pressed.connect(self.searchSPIDevsPB_callback)

    #     statusHLay.addWidget(self.searchSPIDevsPB)
        
    
    #     self.statusBox.setLayout(statusHLay)
        
    #     self.mainVLay.addWidget(self.statusBox)

    def searchSPIDevsPB_callback(self):
        logging.debug("searchSPIDevsPB called")

#----------------------------------------------------------------------
    def add_experiment_layout(self):
        """Adds layout for where to save data for this experient"""
        self.experimentBox = QGroupBox("Experiment Settings")
        vLay = QVBoxLayout()

        gridLay = QGridLayout()

        # where to save directory
        self.directoryTE = QLineEdit("/home/batbot/experiments/")
        gridLay.addWidget(QLabel("Directory:"),0,0)
        gridLay.addWidget(self.directoryTE,0,1)

        # name of experiment
        curExperiment = self.get_current_experiment_time()
        # set the window title the name of experiment
        self.setWindowTitle("BatBot 7 GUI:\t\t\t\t" + curExperiment)
        
        # set the name
        self.experimentFolderNameTE = QLineEdit(curExperiment)
        self.experimentFolderNameTE.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.experimentFolderNameTE.customContextMenuRequested.connect(self.experimentFolderNameTE_contextMenu)
        
        gridLay.addWidget(QLabel("Experiment Folder:"),1,0)
        gridLay.addWidget(self.experimentFolderNameTE,1,1)

        vLay.addLayout(gridLay)
        
        # settings for chirps
        gridLay2 = QGridLayout()
        # start freq
        self.startFreqSB = QSpinBox()
        self.startFreqSB.setSuffix(" kHz")
        self.startFreqSB.setValue(50)
        self.startFreqSB.setRange(0,300)
        gridLay2.addWidget(QLabel("Start Frequency:"),0,0)
        gridLay2.addWidget(self.startFreqSB,0,1)

        # end freq
        self.endFreqSB = QSpinBox()
        self.endFreqSB.setSuffix(" kHz")
        self.endFreqSB.setRange(0,300)
        self.endFreqSB.setValue(150)
        gridLay2.addWidget(QLabel("End Frequency:"),1,0)
        gridLay2.addWidget(self.endFreqSB,1,1)

        # time for microcontroller to sample
        self.samplePeriodSB = QSpinBox()
        self.samplePeriodSB.setValue(1)
        self.samplePeriodSB.setSuffix(" uS")
        gridLay2.addWidget(QLabel("Sample Period:"),0,2)
        gridLay2.addWidget(self.samplePeriodSB,0,3)

        # num of ADC samples
        self.numADCSamplesSB = QSpinBox()
        self.numADCSamplesSB.setRange(1,20000)
        self.numADCSamplesSB.setValue(8000)
        gridLay2.addWidget(QLabel("Number ADC Samples:"),1,2)
        gridLay2.addWidget(self.numADCSamplesSB,1,3)
        
        hLay = QHBoxLayout()
        hLay.addLayout(vLay)
        hLay.addLayout(gridLay2)
        
        # vLay.addLayout(gridLay2)

        # start button 
        self.startCollectionPB = QPushButton("Start Collections")
        vLay.addWidget(self.startCollectionPB)

        
        self.experimentBox.setLayout(hLay)
        self.mainVLay.addWidget(self.experimentBox)

    def get_current_experiment_time(self):
        """Get the current time string that can be used as a file name or folder name"""
        return datetime.now().strftime("experiment_%m-%d-%Y_%H-%M-%S%p")
    
    def experimentFolderNameTE_contextMenu(self,position):
        """Custom context menu for experiment folder name"""
        context_menu = QMenu()
        
        set_current_time = context_menu.addAction("Set Current Time")
        copy_name = context_menu.addAction("Copy")
        paste_name = context_menu.addAction("Paste")
        # action = context_menu.exec(self.experimentFolderNameTE.viewport().mapToGlobal(position))
        action = context_menu.exec(self.experimentFolderNameTE.mapToGlobal(position))
        
        if action == set_current_time:
            self.experimentFolderNameTE.setText(self.get_current_experiment_time())

#----------------------------------------------------------------------
    def add_pinnaeControlBox_layout(self):
        """Adds the controls box layout"""
        self.pinnaeControlBox = QGroupBox("Pinnae Control")
        controlsHLay = QHBoxLayout()
        
        # create tabs for each ear mode
        self.singleEarTab = QWidget()
        self.dualEarTab = QWidget()
        
        # create tabs 
        self.tabs = QTabWidget()
        self.tabs.addTab(self.singleEarTab,"Single")
        self.tabs.addTab(self.dualEarTab,"Dual")
        
        # init left controls
        self.init_leftControls()
        # init right controls
        self.init_rightControls()
        
        # init box for both ears
        self.init_bothControls()

        # init sonar controls
        
        # init the tabs
        self.init_singleEarTab()
        self.init_dualEarTab()
        
        
        controlsHLay.addWidget(self.tabs)
        self.pinnaeControlBox.setLayout(controlsHLay)
        self.mainVLay.addWidget(self.pinnaeControlBox)

        
        
    def init_leftControls(self):
        """Creates box of left controls"""
        self.leftControlBox = QGroupBox("Left Pinnae")

        minAngleSBHlay = QHBoxLayout()
        self.leftMinAngleSB = [
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
        ]
        maxAngleSBHlay = QHBoxLayout()
        self.leftMaxAngleSB = [
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
        ]
        
        angleSliderBHlay = QHBoxLayout()
        self.leftAngleSlider = [
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
        ]
        
        for SB in self.leftMinAngleSB:
            SB.setRange(-1000,1000)
            SB.setFixedWidth(48)
            SB.setValue(-180)
            minAngleSBHlay.addWidget(SB)

        for SB in self.leftMaxAngleSB:
            SB.setFixedWidth(48)
            SB.setRange(-1000,1000)
            SB.setValue(180)
            maxAngleSBHlay.addWidget(SB)
            
        for slider in self.leftAngleSlider:
            angleSliderBHlay.addWidget(slider)
            
        vLay = QVBoxLayout()
        vLay.addLayout(minAngleSBHlay)
        vLay.addLayout(angleSliderBHlay)
        vLay.addLayout(maxAngleSBHlay)
        
        self.leftControlBox.setLayout(vLay)

    def init_rightControls(self):
        """Creates box of left controls"""
        self.rightControlBox = QGroupBox("Right Pinnae")

        minAngleSBHlay = QHBoxLayout()
        self.rightMinAngleSB = [
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
        ]
        maxAngleSBHlay = QHBoxLayout()
        self.rightMaxAngleSB = [
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
        ]

        angleSBHlay = QHBoxLayout()
        self.rightAngleSB = [
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
        ]
        
        angleSliderBHlay = QHBoxLayout()
        self.rightAngleSlider = [
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
        ]
        
        for SB in self.rightMinAngleSB:
            SB.setRange(-10000,10000)
            SB.setFixedWidth(48)
            SB.setValue(-180)
            minAngleSBHlay.addWidget(SB)

        for SB in self.rightMaxAngleSB:
            SB.setFixedWidth(48)
            SB.setRange(-10000,10000)
            SB.setValue(180)
            maxAngleSBHlay.addWidget(SB)

        for SB in self.rightAngleSB:
            SB.setFixedWidth(48)
            SB.setRange(-10000,10000)
            SB.setValue(180)
            angleSBHlay.addWidget(SB)
            
        for slider in self.rightAngleSlider:
            angleSliderBHlay.addWidget(slider)
            
        vLay = QVBoxLayout()
        vLay.addLayout(minAngleSBHlay)
        vLay.addLayout(angleSliderBHlay)
        vLay.addLayout(maxAngleSBHlay)

        
        self.rightControlBox.setLayout(vLay)
   
    def init_bothControls(self):
        """Creates box of left controls"""
        self.bothControlBox = QGroupBox("Both")
        self.bothControlBox.setFixedHeight(230)

        minAngleSBHlay = QHBoxLayout()
        self.bothMinAngleSB = [
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
        ]
        maxAngleSBHlay = QHBoxLayout()
        self.bothMaxAngleSB = [
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
        ]
        
        self.bothAngleSB = [
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
        ]
        
        angleSliderBHlay = QHBoxLayout()
        self.bothAngleSlider = [
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
            QSlider(Qt.Orientation.Vertical),
        ]
        
        for SB in self.bothMinAngleSB:
            SB.setRange(-1000,1000)
            SB.setFixedWidth(48)
            SB.setValue(-180)
            minAngleSBHlay.addWidget(SB)

        for SB in self.bothMaxAngleSB:
            SB.setFixedWidth(48)
            SB.setRange(-1000,1000)
            SB.setValue(180)
            maxAngleSBHlay.addWidget(SB)
            
        for slider in self.bothAngleSlider:
            angleSliderBHlay.addWidget(slider)
            
        vLay = QVBoxLayout()
        vLay.addLayout(minAngleSBHlay)
        vLay.addLayout(angleSliderBHlay)
        vLay.addLayout(maxAngleSBHlay)

        
        self.bothControlBox.setLayout(vLay)
        # gridLay  = [
        #     QGridLayout(),
        #     QGridLayout(),
        #     QGridLayout(),
        #     QGridLayout(),
        #     QGridLayout(),
        #     QGridLayout(),
        # ]

        # hLay = QHBoxLayout()

        # for i, lay in enumerate(gridLay):
        #     lay.addWidget(self.bothMinAngleSB[i],0,0)
        #     lay.addWidget(self.bothMaxAngleSB[i],0,1)
        #     lay.addWidget(self.bothAngleSlider[i],1,0,1,2)
        #     hLay.addLayout(lay)
        
        # self.bothControlBox.setLayout(hLay)
        
        
        
    def init_singleEarTab(self):
        """inits the single ear tab"""
        vLay = QVBoxLayout()
        vLay.addWidget(self.bothControlBox)

        
        tableHLay = QHBoxLayout()
        tableBox = QGroupBox("Instructions")
        self.singleEarInstructionTable = QTableWidget()
        self.init_singleEarInstructionTable()

        tableHLay.addWidget(self.singleEarInstructionTable)

        buttonsVLay = QVBoxLayout()
        # start button
        self.singleEarStartPB = QPushButton("Start")
        buttonsVLay.addWidget(self.singleEarStartPB)

        # hz options
        self.singleEarHzSB = QSpinBox()
        self.singleEarHzSB.setRange(0,400)
        self.singleEarHzSB.setValue(1)
        self.singleEarHzSB.setSuffix('Hz')
        buttonsVLay.addWidget(self.singleEarHzSB)

        # read from file
        self.singleEarReadFilePB = QPushButton("Read File")
        buttonsVLay.addWidget(self.singleEarReadFilePB)


        tableHLay.addLayout(buttonsVLay)
        tableBox.setLayout(tableHLay)

        vLay.addWidget(tableBox)


        self.singleEarTab.setLayout(vLay)
    
    def init_singleEarInstructionTable(self):
        self.singleEarInstructionTable.setRowCount(1)
        self.singleEarInstructionTable.setColumnCount(6)

        # preload with zeros and set width
        widthValue = 80
        for i in range(6):
            intNum = QTableWidgetItem()
            intNum.setData(0,0)
            self.singleEarInstructionTable.setItem(0,i,intNum)
            self.singleEarInstructionTable.setColumnWidth(i,widthValue)
        self.singleEarInstructionTable.setFixedWidth(widthValue*6+20)

    def init_dualEarTab(self):
        """inits the dual ear tab"""
        vLay = QVBoxLayout()
        hLay = QHBoxLayout()
        hLay.addWidget(self.leftControlBox)
        hLay.addWidget(self.rightControlBox)
        # add left and right control box
        vLay.addLayout(hLay)

        tableHLay = QHBoxLayout()
        tableBox = QGroupBox("Instructions")
        self.dualEarInstructionTable = QTableWidget()
        self.init_dualEarInstructionTable()

        tableHLay.addWidget(self.dualEarInstructionTable)

        buttonsVLay = QVBoxLayout()
        # start button
        self.dualEarStartPB = QPushButton("Start")
        buttonsVLay.addWidget(self.dualEarStartPB)

        # hz options
        self.dualEarHzSB = QSpinBox()
        self.dualEarHzSB.setRange(0,400)
        self.dualEarHzSB.setValue(1)
        self.dualEarHzSB.setSuffix('Hz')
        buttonsVLay.addWidget(self.dualEarHzSB)

        # read from file
        self.dualEarReadFilePB = QPushButton("Read File")
        buttonsVLay.addWidget(self.dualEarReadFilePB)


        tableHLay.addLayout(buttonsVLay)
        tableBox.setLayout(tableHLay)

        vLay.addWidget(tableBox)



        self.dualEarTab.setLayout(vLay)

    def init_dualEarInstructionTable(self):
        self.dualEarInstructionTable.setRowCount(1)
        self.dualEarInstructionTable.setColumnCount(12)

        # preload with zeros and set width
        widthValue = 50
        for i in range(12):
            intNum = QTableWidgetItem()
            intNum.setData(0,0)
            self.dualEarInstructionTable.setItem(0,i,intNum)
            self.dualEarInstructionTable.setColumnWidth(i,widthValue)

        self.dualEarInstructionTable.setFixedWidth(widthValue*12+20)
        self.dualEarInstructionTable.setHorizontalHeaderLabels(["L1", "L2","L3","L4","L5","L6","R1","R2","R3","R4","R5","R6",])
        
        
#----------------------------------------------------------------------
    def init_echoControl_box(self):
        """Adds the sonar box layout"""
        self.sonarControlBox = QGroupBox("Echos")
        self.sonarControlBox.setMinimumHeight(280)
        vLay = QVBoxLayout()

        gridLay = QGridLayout()
        # # show directory pulling from
        # self.echoPlotDirectoryCB = QComboBox()
        # self.echoPlotDirectoryCB.addItem(self.directoryTE.text() +self.experimentFolderNameTE.text()+"/gpsdata")
        # self.echoPlotDirectoryCB.setEditable(True)
        # self.echoPlotDirectoryCB.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred)
        # gridLay.addWidget(QLabel("Plot Data:"),0,0)
        # gridLay.addWidget(self.echoPlotDirectoryCB,0,1)
        
        # # show plots found
        # self.plotsFoundLE = QLineEdit("0")
        # self.plotsFoundLE.setReadOnly(True)

        # gridLay.addWidget(QLabel("Plots found:"),0,2)
        # gridLay.addWidget(self.plotsFoundLE,0,3)
    
        vLay.addLayout(gridLay)


        # left pinnae spectogram
        hLay = QHBoxLayout()
        self.leftPinnaeSpec = MplCanvas(self,width=5,height=4,dpi=100)
        self.leftPinnaeSpec.axes.set_title("Left Pinnae")
        
        Time_difference = 0.0001
        Time_Array = np.linspace(0, 5, math.ceil(5 / Time_difference))
        Data = 20*(np.sin(3 * np.pi * Time_Array))
        self.leftPinnaeSpec.axes.specgram(Data,Fs=6,cmap="rainbow")
        hLay.addWidget(self.leftPinnaeSpec)


        # middle section---------------------------------
        hLay2 = QHBoxLayout()

        # plot check button
        self.plotSpecCB = QCheckBox("Plot")
        # hLay.addWidget(self.plotSpecCB)
        hLay2.addWidget(self.plotSpecCB)

        # refreshrate for plots
        self.refreshRateSpecPlotsSB = QDoubleSpinBox()
        self.refreshRateSpecPlotsSB.setSuffix(" Sec")
        self.refreshRateSpecPlotsSB.setRange(0.1,100)
        self.refreshRateSpecPlotsSB.setValue(1)
        self.refreshRateSpecPlotsSB.setDecimals(1)
 
        # hLay.addWidget(QLabel("Plot Every:"))
        # hLay.addWidget(self.refreshRateSpecPlotsSB)
        hLay2.addWidget(QLabel("Plot Every:"))
        hLay2.addWidget(self.refreshRateSpecPlotsSB)

        vLay.addLayout(hLay2)

        # ---------------------------------------------
        # right pinnae spectogram
        self.rightPinnaeSpec = MplCanvas(self,width=5,height=4,dpi=100)
        self.rightPinnaeSpec.axes.set_title("Right Pinnae")
        Time_difference = 0.0001
        Time_Array = np.linspace(0, 5, math.ceil(5 / Time_difference))
        Data = 20*(np.sin(3 * np.pi * Time_Array))
        self.rightPinnaeSpec.axes.specgram(Data,Fs=6,cmap="rainbow")
        hLay.addWidget(self.rightPinnaeSpec)

        vLay.addLayout(hLay)
        self.sonarControlBox.setLayout(vLay)

    def init_GPS_box(self):
        """Inits the gps box"""
        self.gpsBox = QGroupBox("GPS")
        hLay = QHBoxLayout()
        gridLay = QGridLayout()

        # fakemap = QTextEdit("this is a map")
        fakemap = MplCanvas(self,width=5,height=4,dpi=100)
        Time_difference = 0.0001
        Time_Array = np.linspace(0, 5, math.ceil(5 / Time_difference))
        Data = 20*(np.sin(3 * np.pi * Time_Array))
        fakemap.axes.specgram(Data,Fs=6,cmap="rainbow")

        
        gridLay.addWidget(fakemap,0,0)

        # name to save file
        self.gpsFileNameTE = QLineEdit("gpsDataSave.txt")
        gridLay.addWidget(QLabel("File Name:"),0,1)
        gridLay.addWidget(self.gpsFileNameTE,0,2)
        
        self.gpsBox.setLayout(gridLay)
 

    def Add_Sonar_Box(self):
        """adds sonar and gps box"""
        self.init_echoControl_box()

        self.sonarAndGPSLay = QHBoxLayout()
        self.sonarAndGPSLay.addWidget(self.sonarControlBox)
        # self.sonarAndGPSLay.addWidget(self.gpsBox)

        self.mainVLay.addLayout(self.sonarAndGPSLay)
        
    
        
if __name__ == "__main__":
    app = QApplication([])
    widget = Widget()
    widget.show()
    sys.exit(app.exec())