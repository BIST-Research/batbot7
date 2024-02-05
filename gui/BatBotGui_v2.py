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
    QErrorMessage

)
from PyQt6.QtCore import Qt, QFile, QTextStream, QThread, pyqtSignal,QObject
import sys,os
import serial
import serial.tools.list_ports
import time
import math
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) )
from pinnae import PinnaeController

# frequency of dac and adc
DAC_ADC_FREQ = 1e6

class Widget(QWidget):
    """GUI for controlling Bat Bot"""
    
    # main vertical layout everything is added to
    mainVLay = QVBoxLayout()
    
    
    pinnae = PinnaeController()
    
    def __init__(self):
        """Adds all the widgets to GUI"""
        QWidget.__init__(self)
        self.setWindowTitle("Bat Bot 7 GUI")
        
        # add experiment box
        self.Add_Experiment_GB()

        # add sonar and GPS controller box
        self.Add_Echo_GB()

        # add pinnae controls layout
        self.Add_Pinnae_Control_GB()

        
        self.setLayout(self.mainVLay)
        

#----------------------------------------------------------------------
    def Add_Experiment_GB(self):
        """Adds layout for where to save data for this experient"""
        self.experiment_settings_GB = QGroupBox("Experiment")
        # -------------------------------------------------------------------
        # directory groupbox
        directory_grid = QGridLayout()        
        directory_GB = QGroupBox("Directory Settings")

        # where to save directory
        self.directory_TE = QLineEdit("/home/batbot/experiments/")
        self.directory_TE.setObjectName("directory_TE")
        directory_grid.addWidget(QLabel("Directory:"),0,0)
        directory_grid.addWidget(self.directory_TE,0,1)

        # name of experiment
        curExperiment = self.get_current_experiment_time()
        # set the window title the name of experiment
        self.setWindowTitle("BatBot 7 GUI:\t\t\t\t" + curExperiment)
        
        # set the name
        self.experiment_folder_name_TE = QLineEdit(curExperiment)
        self.experiment_folder_name_TE.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.experiment_folder_name_TE.customContextMenuRequested.connect(self.experiment_folder_name_TE_contextMenu)
        
        directory_grid.addWidget(QLabel("Experiment Folder:"),1,0)
        directory_grid.addWidget(self.experiment_folder_name_TE,1,1)
        directory_GB.setLayout(directory_grid)
        
        # -------------------------------------------------------------------
        # settings for chirps
        chirp_GB = QGroupBox("Chirp && Listen Settings")
        chirp_grid = QGridLayout()
        # start freq
        self.chirp_start_freq_SB = QSpinBox()
        self.chirp_start_freq_SB.setSuffix(" kHz")
        self.chirp_start_freq_SB.setValue(50)
        self.chirp_start_freq_SB.setRange(0,300)
        self.chirp_start_freq_SB.valueChanged.connect(self.chirp_settings_changed_callback)
        chirp_grid.addWidget(QLabel("Start:"),0,0)
        chirp_grid.addWidget(self.chirp_start_freq_SB,0,1)

        # end freq
        self.chirp_stop_freq_SB = QSpinBox()
        self.chirp_stop_freq_SB.setSuffix(" kHz")
        self.chirp_stop_freq_SB.setRange(0,300)
        self.chirp_stop_freq_SB.setValue(150)
        self.chirp_stop_freq_SB.valueChanged.connect(self.chirp_settings_changed_callback)
        chirp_grid.addWidget(QLabel("Stop:"),1,0)
        chirp_grid.addWidget(self.chirp_stop_freq_SB,1,1)

        # length of chirp
        self.chirp_duration_SB = QSpinBox()
        self.chirp_duration_SB.setValue(1)
        self.chirp_duration_SB.setSuffix(" mS")
        self.chirp_duration_SB.valueChanged.connect(self.chirp_settings_changed_callback)
        chirp_grid.addWidget(QLabel("Duration:"),0,2)
        chirp_grid.addWidget(self.chirp_duration_SB,0,3)
        
        # type of chirp
        self.chirp_type_CB = QComboBox()
        self.chirp_type_CB.addItem('linear')
        self.chirp_type_CB.addItem('quadratic')
        self.chirp_type_CB.addItem('logarithmic')
        self.chirp_type_CB.addItem('hyperbolic')
        self.chirp_type_CB.currentTextChanged.connect(self.chirp_settings_changed_callback)
        chirp_grid.addWidget(QLabel("Type:"),1,2)
        chirp_grid.addWidget(self.chirp_type_CB,1,3)
        
        buffer_col_len = 90
        # length of chirp buffer
        self.chirp_buffer_length_SB = QLineEdit()
        self.chirp_buffer_length_SB.setReadOnly(True)
        self.chirp_buffer_length_SB.setMaximumWidth(buffer_col_len)
        # chirp_grid.addWidget(QLabel("Chirp:"),0,4)
        # chirp_grid.addWidget(self.chirp_buffer_length_SB,0,5)
        
        # lengthf of listen buffers
        self.listen_buffer_length_SB = QLineEdit()
        self.listen_buffer_length_SB.setReadOnly(True)
        self.listen_buffer_length_SB.setMaximumWidth(buffer_col_len)
        # chirp_grid.addWidget(QLabel("Listen:"),1,4)
        # chirp_grid.addWidget(self.listen_buffer_length_SB,1,5)
        
        # preview chirp
        self.preview_chirp_PB = QPushButton("Preview")
        self.preview_chirp_PB.clicked.connect(self.preview_chirp_PB_Clicked)
        chirp_grid.addWidget(self.preview_chirp_PB,0,6)
        
        # upload to board
        self.upload_chirp_PB = QPushButton("Upload")
        self.upload_chirp_PB.clicked.connect(self.upload_chirp_PB_Clicked)
        chirp_grid.addWidget(self.upload_chirp_PB,1,6)
        
        chirp_GB.setLayout(chirp_grid)
        
        
        
        # -------------------------------------------------------------------
        # put together two groupboxes
        hLay = QHBoxLayout()
        hLay.addWidget(directory_GB)
        hLay.addWidget(chirp_GB)
        
        self.chirp_settings_changed_callback()
        
        self.experiment_settings_GB.setLayout(hLay)
        self.mainVLay.addWidget(self.experiment_settings_GB)
        

    def get_current_experiment_time(self):
        """Get the current time string that can be used as a file name or folder name"""
        return datetime.now().strftime("experiment_%m-%d-%Y_%H-%M-%S%p")
    
    def experiment_folder_name_TE_contextMenu(self,position):
        """Custom context menu for experiment folder name"""
        context_menu = QMenu()
        
        set_current_time = context_menu.addAction("Set Current Time")
        copy_name = context_menu.addAction("Copy")
        paste_name = context_menu.addAction("Paste")
        # action = context_menu.exec(self.experiment_folder_name_TE.viewport().mapToGlobal(position))
        action = context_menu.exec(self.experiment_folder_name_TE.mapToGlobal(position))
        
        if action == set_current_time:
            self.experiment_folder_name_TE.setText(self.get_current_experiment_time())
            
    
    # callback
    def preview_chirp_PB_Clicked(self):
        """_summary_
        """
        logging.debug("preview_chirp_PB_Clicked")
        

        plt.close('Chirp Preview')
        plt.figure("Chirp Preview")
        
        duration = self.chirp_duration_SB.value() * 1e-3
        start = self.chirp_start_freq_SB.value() * 1e3
        stop = self.chirp_stop_freq_SB.value() * 1e3
        method = self.chirp_type_CB.currentText()
        sample_rate = 1e6  # Define your desired sample rate (1 MHz in this case)
        t = np.arange(0, duration, 1 / sample_rate)

        y_chirp = signal.chirp(t, f0=start, f1=stop, t1=t[-1], method=method)

        # Plotting the spectrogram
        plt.specgram(y_chirp, Fs=sample_rate)
        plt.xlabel('Time (s)')
        plt.ylabel('Frequency (Hz)')
        plt.title('Spectrogram of Chirp Signal')
        plt.colorbar(label='Intensity')
        plt.show()


    def upload_chirp_PB_Clicked(self):
        """ when clicked"""
        logging.debug("upload_chirp_PB_Clicked")
        print(plt.get_figlabels())
        
    def chirp_settings_changed_callback(self):
        open_figures = plt.get_figlabels()
        
        duration = self.chirp_duration_SB.value()
        
        # display chirp buffer length
        chirp_len = duration*1e-3*1e6
        self.chirp_buffer_length_SB.setText(f"{chirp_len:.0f}")
        
        # display listen buffer length
        listen_buffer_len = np.floor((80000 - chirp_len)/2)
        listen_buffer_time = listen_buffer_len*1e-3
        self.listen_buffer_length_SB.setText(f"{listen_buffer_len:.0f} {listen_buffer_time:.1f} mS")
        
        
        if 'Chirp Preview' in open_figures:
            self.preview_chirp_PB_Clicked()
        
        
#----------------------------------------------------------------------
    def Add_Pinnae_Control_GB(self):
        """Adds the controls box layout"""

        self.pinnae_controls_GB = QGroupBox("Controls")
        
        control_h_lay = QHBoxLayout()
        
        motor_GB = [
            QGroupBox("Motor 1"),
            QGroupBox("Motor 2"),
            QGroupBox("Motor 3"),
            QGroupBox("Motor 4"),
            QGroupBox("Motor 5"),
            QGroupBox("Motor 6")
        ]

        self.motor_max_PB = [
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
        ]

        self.motor_max_limit_SB = [
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
            QSpinBox()
        ]

        self.motor_value_SB = [
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
        ]
        
        self.motor_set_zero_PB = [
            QPushButton("Set Zero"),
            QPushButton("Set Zero"),
            QPushButton("Set Zero"),
            QPushButton("Set Zero"),
            QPushButton("Set Zero"),
            QPushButton("Set Zero")
        ]
        
        number_motors = 6
        max_value = 10000
        
        for index in range(number_motors):
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
            vertical_layout.addWidget(self.motor_set_zero_PB[index])
        
            motor_GB[index].setMaximumWidth(160)
            
            motor_GB[index].setLayout(vertical_layout)
            control_h_lay.addWidget(motor_GB[index])
        
        vertical_layout = QVBoxLayout()
        vertical_layout.addLayout(control_h_lay)
        
        # attach callbacks for controller tendon api
        self.add_motor_control_CB()
        
        hLay = QHBoxLayout()
        # add the instruction table
        self.instruction_TABLE = QTableWidget(1,number_motors)
        hLay.addWidget(self.instruction_TABLE)
        
        
        # create layout for buttons side of table
        table_side_v_lay = QVBoxLayout()
        
        # settings for making ears realistic
        self.realistic_ears_CB = QCheckBox("Realistic Ears")
        self.realistic_ears_CB.setToolTip("Each ear will be out of phase if checked like a real bat")
        table_side_v_lay.addWidget(self.realistic_ears_CB)
        
        # create 
        table_side_grid = QGridLayout()
        self.start_stop_instruction_PB = QPushButton("Start")
        table_side_grid.addWidget(self.start_stop_instruction_PB,0,0)
        self.intstruction_speed_SB = QSpinBox()
        self.intstruction_speed_SB.setSuffix(" Hz")
        table_side_grid.addWidget(self.intstruction_speed_SB,0,1)
        
        
        table_side_v_lay.addLayout(table_side_grid)

        hLay.addLayout(table_side_v_lay)        
        vertical_layout.addLayout(hLay)
        
        self.pinnae_controls_GB.setLayout(vertical_layout)
        self.mainVLay.addWidget(self.pinnae_controls_GB)
        
    def add_motor_control_CB(self):
        """Connects the motor tendons sliders to the api"""
        
        # attach max buttons
        for i in range(6):
            self.motor_max_PB[i].pressed.connect(lambda index=i: self.motor_max_PB_pressed(index))
        
        # attach max limit spinbox
        for i in range(6):
            self.motor_max_limit_SB[i].editingFinished.connect(lambda index=i: self.motor_max_limit_changed_CB(index))

            
        # attach min buttons
        for i in range(6):
            self.motor_min_PB[i].pressed.connect(lambda index=i: self.motor_min_PB_pressed(index))

        # attach min limit spinbox
        for i in range(6):
            self.motor_min_limit_SB[i].editingFinished.connect(lambda index=i: self.motor_min_limit_changed_CB(index))
            
            
        # attach set to zero buttons
        for i in range(6):
            self.motor_set_zero_PB[i].pressed.connect(lambda index=i: self.motor_set_zero_PB_callback(index))

        # attach sliders
        for i in range(6):
            self.motor_value_SLIDER[i].valueChanged.connect(lambda value, index=i: self.motor_value_SLIDER_valueChanged(index))
        
        # attach spinbox
        for i in range(6):
            self.motor_value_SB[i].editingFinished.connect(lambda index=i: self.motor_value_SB_valueChanged(index))
            
        # adjust the slider and spinbox range
        for i in range(6):
            self.motor_max_limit_changed_CB(i)
        
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
        # print(f"value {index}")
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
    
#----------------------------------------------------------------------
    def init_echoControl_box(self):
        """Adds the sonar box layout"""
        self.sonarControlBox = QGroupBox("Echos")
        self.sonarControlBox.setMinimumHeight(300)
        vLay = QVBoxLayout()

        gridLay = QGridLayout()
        # # show directory pulling from
        # self.echoPlotDirectoryCB = QComboBox()
        # self.echoPlotDirectoryCB.addItem(self.directory_TE.text() +self.experiment_folder_name_TE.text()+"/gpsdata")
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
 

    def Add_Echo_GB(self):
        """adds sonar and gps box"""
        self.init_echoControl_box()

        self.sonarAndGPSLay = QHBoxLayout()
        self.sonarAndGPSLay.addWidget(self.sonarControlBox)
        # self.sonarAndGPSLay.addWidget(self.gpsBox)

        self.mainVLay.addLayout(self.sonarAndGPSLay)
        
    def closeEvent(self,event):
        plt.close('all')
        event.accept()
        
if __name__ == "__main__":
    app = QApplication([])
    widget = Widget()
    widget.show()
    sys.exit(app.exec())