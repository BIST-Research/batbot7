# """Author: Mason Lopez
# Date: November 13th
# About: This GUI controls the BatBot system, Tendons, GPS, and Sonar
# """

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
    QButtonGroup,
    QRadioButton,
    QErrorMessage,
    QFileDialog,
)
from PyQt6.QtCore import Qt, QFile, QTextStream, QThread, pyqtSignal, QObject
from PyQt6.QtSerialPort import QSerialPortInfo
from PyQt6.QtGui import QIcon

import sys, os
import serial
import serial.tools.list_ports
import time
import math
import yaml

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colorbar import Colorbar
import matplotlib.mlab as mlab
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import numpy as np
import scipy
import signal

import threading
from datetime import datetime
import platform
import qdarkstyle
import pyqtgraph as pg

from batbot7_bringup.sonar.bb_emitter import EchoEmitter
from batbot7_bringup.sonar.bb_listener import EchoRecorder
from batbot7_bringup.bb_gps import bb_gps2
from batbot7_bringup.serial.serial_helper import get_port_from_serial_num
from batbot7_bringup.pinnae import PinnaeController

matplotlib.set_loglevel("error")

signal.signal(signal.SIGINT, signal.SIG_DFL)

# showing plots in qt from matlab
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


def remove_colorbars(fig):
    # Iterate through each colorbar in the figure and remove it
    for ax in fig.get_axes():
        # Get the children of the axis
        for child in ax.get_children():
            # If the child is a colorbar, remove it
            print(f"{type(child)}")
            if isinstance(child, matplotlib.colorbar._ColorbarSpine):
                child.remove()


def plot_spec(
    ax: plt.axes,
    fig: plt.figure,
    spec_tup,
    fbounds=(30e3, 100e3),
    dB_range=40,
    plot_title="spec",
    use_cb=True,
):
    fmin, fmax = fbounds
    s, f, t = spec_tup

    lfc = (f >= fmin).argmax()
    s = 20 * np.log10(s)
    f_cut = f[lfc:]
    s_cut = s[:][lfc:]

    max_s = np.amax(s_cut)
    s_cut = s_cut - max_s

    [rows_s, cols_s] = np.shape(s_cut)

    dB = -dB_range

    for col in range(cols_s):
        for row in range(rows_s):
            if s_cut[row][col] < dB:
                s_cut[row][col] = dB

    cf = ax.pcolormesh(t, f_cut, s_cut, cmap="jet", shading="auto")

    if use_cb:
        cbar = fig.colorbar(cf, ax=ax)
        cbar.ax.set_ylabel("dB")

    ax.set_ylim(fmin, fmax)
    ax.set_yticks(range(30000, 100000 + 1, 10000))
    ax.set_ylabel("Frequency (Hz)")
    ytick_labels = [f"{int(val)} kHz" for val in ax.get_yticks() / 1000]
    ax.set_yticks(ax.get_yticks())
    ax.set_yticklabels(ytick_labels)
    ax.set_ylim(fmin, fmax)
    ax.set_xlabel("Time (sec)")
    ax.title.set_text(plot_title)


def process(raw, spec_settings, time_offs=0):
    unraw_balanced = raw - np.mean(raw)
    # unraw_balanced = raw

    pt_cut = unraw_balanced[time_offs:]
    remainder = unraw_balanced[:time_offs]

    Fs, NFFT, noverlap, window = spec_settings
    spec_tup = mlab.specgram(pt_cut, Fs=Fs, NFFT=NFFT, noverlap=noverlap, window=window)

    return spec_tup, pt_cut, remainder


class ComboBox(QComboBox):
    popupAboutToBeShown = pyqtSignal()

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super(ComboBox, self).showPopup()


# logging stuff
import logging

logging.basicConfig(level=logging.DEBUG)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from spidev import SpiDev
except ImportError:
    logging.error("pinnae.py:: no spidev found, developing on different os ")
    from batbot7_bringup.serial.fake_spidev import fake_SpiDev as SpiDev

# frequency of dac and adc
DAC_ADC_FREQ = 1e6

NUM_PINNAE = 7


class BBGUI(QWidget):
    """GUI for controlling Bat Bot"""

    # main vertical layout everything is added to
    mainVLay = QVBoxLayout()

    left_pinna = PinnaeController(SpiDev(0, 0))
    right_pinna = PinnaeController(SpiDev(0, 1))
    emitter = EchoEmitter()
    listener = EchoRecorder()
    gps = bb_gps2()

    instructionThread = None
    instructionThreadRunning = False

    gpsThread = None
    gpsThreadRunning = False

    left_pinna_plotted = False
    right_pinna_plotted = False

    dir_path = os.path.dirname(os.path.realpath(__file__))

    def __init__(
        self,
        emitter: EchoRecorder = None,
        listener: EchoEmitter = None,
        l_pinna: PinnaeController = None,
        r_pinna: PinnaeController = None,
    ):
        """Adds all the widgets to GUI"""
        QWidget.__init__(self)
        self.setWindowTitle("Bat Bot 7 GUI")

        # add experiment box
        self.Add_Experiment_GB()

        # add sonar and GPS controller box
        self.Add_Echo_GB()

        # add pinnae controls layout
        self.Add_Pinnae_Control_GB()

        self.setWindowIcon(QIcon("HBAT.jpg"))

        self.setLayout(self.mainVLay)

        # dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(self.dir_path + "/config/bb_conf.yaml", "r") as f:
            self.bb_config = yaml.safe_load(f)

        # make experiments
        if not os.path.exists(self.dir_path + "/experiments"):
            os.makedirs(self.dir_path + "/experiments")
            print("Made experiments folder")
        else:
            print("Experiments folder exists")

        self.selected_pinna_QB.setCurrentText("both")
        self.experiment_path = self.dir_path + "/experiments/" + self.curExperiment
        os.makedirs(self.experiment_path)

        self.gps_dump_path = self.experiment_path + "/GPS"
        os.makedirs(self.gps_dump_path)

        self.runs_path = self.experiment_path + "/RUNS"
        os.makedirs(self.runs_path)

        self.connect_MCUs()

        for i in range(NUM_PINNAE):
            if i < 3:
                self.motor_min_limit_SB[i].setValue(0)
                self.motor_max_limit_SB[i].setValue(170)
            else:
                self.motor_min_limit_SB[i].setValue(-170)
                self.motor_max_limit_SB[i].setValue(0)

            # self.motor_min_limit_SB[i].setValue(0)
            # self.motor_max_limit_SB[i].setValue(170)

            self.motor_min_limit_changed_CB(i)
            self.motor_max_limit_changed_CB(i)

    def connect_MCUs(self):
        if not self.bb_config:
            return

        baud = self.bb_config["emit_MCU"]["baud"]
        sn = self.bb_config["emit_MCU"]["serial_num"]
        port = get_port_from_serial_num(sn)
        try:
            self.emitter.connect_Serial(serial.Serial(port=port, baudrate=baud))
            time.sleep(0.01)
            if not self.emitter.connection_status():
                raise
            self.emitter.disconnect_serial()
            port = port.split("/")
            port = "".join(port[::-2])

            self.emitter_ports_CB.clear()
            self.emitter_ports_CB.addItem(port)
            self.emitter_ports_CB.setCurrentText(port)
            self.emitter_connect_PB.click()
            print("ran")
        except:
            print("failed")
            pass

        baud = self.bb_config["record_MCU"]["baud"]
        sn = self.bb_config["record_MCU"]["serial_num"]
        port = get_port_from_serial_num(sn)
        try:
            self.listener.connect_Serial(serial.Serial(port=port, baudrate=baud))
            time.sleep(0.01)
            if not self.listener.connection_status():
                raise
            self.listener.disconnect_serial()

            port = port.split("/")
            port = "".join(port[::-2])

            self.listener_ports_CB.clear()
            self.listener_ports_CB.addItem(port)
            self.listener_ports_CB.setCurrentText(port)
            self.listener_connect_PB.click()

        except:
            pass
        pass

        baud = self.bb_config["gps_MCU"]["baud"]
        sn = self.bb_config["gps_MCU"]["serial_num"]
        port = get_port_from_serial_num(sn)
        try:
            self.gps.connect_Serial(serial.Serial(port=port, baudrate=baud))
            time.sleep(0.01)
            if not self.gps.connection_status():
                raise
            self.gps.disconnect_serial()

            port = port.split("/")
            port = "".join(port[::-2])

            self.gps_ports_CB.clear()
            self.gps_ports_CB.addItem(port)
            self.gps_ports_CB.setCurrentIndex(0)
            self.gps_connect_PB.click()

            # self.gpsThread = threading.Thread(target=self.gps.run,args=(self.gps_dump_path,None))

            # self.gpsThread.start()
        except:
            pass
        pass

    # ----------------------------------------------------------------------
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
        directory_grid.addWidget(QLabel("Directory:"), 0, 0)
        directory_grid.addWidget(self.directory_TE, 0, 1)

        # name of experiment
        self.curExperiment = self.get_current_experiment_time()
        # set the window title the name of experiment
        self.setWindowTitle("BatBot 7 GUI:\t\t\t\t" + self.curExperiment)

        # set the name
        self.experiment_folder_name_TE = QLineEdit(self.curExperiment)
        self.experiment_folder_name_TE.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.experiment_folder_name_TE.customContextMenuRequested.connect(
            self.experiment_folder_name_TE_contextMenu
        )

        directory_grid.addWidget(QLabel("Experiment Folder:"), 1, 0)
        directory_grid.addWidget(self.experiment_folder_name_TE, 1, 1)
        directory_GB.setLayout(directory_grid)

        # -------------------------------------------------------------------
        # communication settings
        self.mcu_grid = QGridLayout()
        pinna_MCU = QGroupBox("Pinna MCU")

        spi_CB = QCheckBox("SPI")
        spi_CB.setChecked(True)
        uart_CB = QCheckBox("UART")

        # objects depending on the selected object
        self.left_pinna_spi_ss_SB = QSpinBox()
        self.left_pinna_spi_ss_SB.setPrefix("SS: ")
        self.left_pinna_spi_ss_SB.setValue(0)
        self.left_pinna_spi_bus_SB = QSpinBox()
        self.left_pinna_spi_bus_SB.setPrefix("BUS: ")
        self.left_pinna_spi_bus_SB.setValue(0)

        self.right_pinna_spi_ss_SB = QSpinBox()
        self.right_pinna_spi_ss_SB.setPrefix("SS: ")
        self.right_pinna_spi_ss_SB.setValue(1)
        self.right_pinna_spi_bus_SB = QSpinBox()
        self.right_pinna_spi_bus_SB.setPrefix("BUS: ")
        self.right_pinna_spi_bus_SB.setValue(0)

        # uart config stuff
        self.left_pinna_uart_name_CB = ComboBox()
        self.left_pinna_uart_name_CB.popupAboutToBeShown.connect(
            lambda: self.populate_serial_ports_CB(self.left_pinna_uart_name_CB)
        )
        self.left_pinna_uart_connect_PB = QPushButton("Connect")
        self.left_pinna_uart_connect_PB.setCheckable(True)

        self.right_pinna_uart_name_CB = ComboBox()
        self.right_pinna_uart_name_CB.popupAboutToBeShown.connect(
            lambda: self.populate_serial_ports_CB(self.right_pinna_uart_name_CB)
        )
        self.right_pinna_uart_connect_PB = QPushButton("Connect")
        self.right_pinna_uart_connect_PB.setCheckable(True)

        # connect their callbacks
        self.left_pinna_spi_ss_SB.valueChanged.connect(
            lambda: self.mcu_spi_options_pressed()
        )
        self.left_pinna_spi_bus_SB.valueChanged.connect(
            lambda: self.mcu_spi_options_pressed()
        )
        self.left_pinna_uart_connect_PB.pressed.connect(
            lambda: self.connect_uart_PB_CB(
                self.left_pinna_uart_name_CB, self.left_pinna_uart_connect_PB
            )
        )

        self.right_pinna_spi_ss_SB.valueChanged.connect(
            lambda: self.mcu_spi_options_pressed()
        )
        self.right_pinna_spi_bus_SB.valueChanged.connect(
            lambda: self.mcu_spi_options_pressed()
        )
        self.right_pinna_uart_connect_PB.pressed.connect(
            lambda: self.connect_uart_PB_CB(
                self.right_pinna_uart_name_CB, self.right_pinna_uart_connect_PB
            )
        )
        # self.right_pinna_uart_connect_PB.pressed.connect(lambda: self.uart_connect_PB_pressed('right'))

        # create button group taht only allows one at a time
        self.pinna_protocol_BG = QButtonGroup()
        self.pinna_protocol_BG.setExclusive(True)
        self.pinna_protocol_BG.addButton(spi_CB, id=1)
        self.pinna_protocol_BG.addButton(uart_CB, id=2)
        # attach callback to add settings to it
        self.pinna_protocol_BG.buttonReleased.connect(self.pinna_protocol_BG_CB)
        # call the method to initialize
        self.pinna_protocol_BG_CB()

        self.mcu_grid.addWidget(QLabel("Comm. Type"), 0, 0)
        self.mcu_grid.addWidget(QLabel("Left"), 0, 1)
        self.mcu_grid.addWidget(QLabel("Right"), 0, 2)
        self.mcu_grid.addWidget(spi_CB, 1, 0)
        self.mcu_grid.addWidget(uart_CB, 2, 0)
        pinna_MCU.setLayout(self.mcu_grid)

        # -------------------------------------------------------------------
        # sonar and chirp and GPS MCU
        sonar_MCU_GB = QGroupBox("MCU CONFIG")
        sonar_MCU_grid = QGridLayout()

        CB_WIDTH = 130
        # GPS
        sonar_MCU_grid.addWidget(QLabel("GPS"), 0, 0)
        self.gps_ports_CB = ComboBox()
        self.gps_ports_CB.setFixedWidth(CB_WIDTH)
        self.gps_ports_CB.popupAboutToBeShown.connect(
            lambda: self.populate_serial_ports_CB(self.gps_ports_CB)
        )
        self.gps_ports_CB.setPlaceholderText("SEARCH")
        sonar_MCU_grid.addWidget(self.gps_ports_CB, 1, 0)
        self.gps_connect_PB = QPushButton("Connect")
        self.gps_connect_PB.setCheckable(True)
        self.gps_connect_PB.setAutoExclusive(False)
        self.gps_connect_PB.pressed.connect(
            lambda: self.connect_uart_PB_CB(self.gps_ports_CB, self.gps_connect_PB)
        )
        sonar_MCU_grid.addWidget(self.gps_connect_PB, 2, 0)

        # emitter
        sonar_MCU_grid.addWidget(QLabel("Emitter"), 0, 1)
        self.emitter_ports_CB = ComboBox()
        self.emitter_ports_CB.setFixedWidth(CB_WIDTH)
        self.emitter_ports_CB.setPlaceholderText("SEARCH")
        self.emitter_ports_CB.popupAboutToBeShown.connect(
            lambda: self.populate_serial_ports_CB(self.emitter_ports_CB)
        )
        sonar_MCU_grid.addWidget(self.emitter_ports_CB, 1, 1)
        self.emitter_connect_PB = QPushButton("Connect")
        self.emitter_connect_PB.setCheckable(True)
        self.emitter_connect_PB.setAutoExclusive(False)

        self.emitter_connect_PB.pressed.connect(
            lambda: self.connect_uart_PB_CB(
                self.emitter_ports_CB, self.emitter_connect_PB
            )
        )
        sonar_MCU_grid.addWidget(self.emitter_connect_PB, 2, 1)

        # listener
        sonar_MCU_grid.addWidget(QLabel("Listener"), 0, 2)
        self.listener_ports_CB = ComboBox()
        self.listener_ports_CB.setFixedWidth(CB_WIDTH)
        self.listener_ports_CB.setPlaceholderText("SEARCH")
        self.listener_ports_CB.popupAboutToBeShown.connect(
            lambda: self.populate_serial_ports_CB(self.listener_ports_CB)
        )
        sonar_MCU_grid.addWidget(self.listener_ports_CB, 1, 2)
        self.listener_connect_PB = QPushButton("Connect")
        self.listener_connect_PB.setCheckable(True)
        self.listener_connect_PB.setAutoExclusive(False)
        self.listener_connect_PB.pressed.connect(
            lambda: self.connect_uart_PB_CB(
                self.listener_ports_CB, self.listener_connect_PB
            )
        )
        sonar_MCU_grid.addWidget(self.listener_connect_PB, 2, 2)

        sonar_MCU_GB.setLayout(sonar_MCU_grid)

        # -------------------------------------------------------------------
        # settings for chirps
        chirp_GB = QGroupBox("Chirp && Listen Settings")
        chirp_grid = QGridLayout()
        # start freq
        self.chirp_start_freq_SB = QSpinBox()
        self.chirp_start_freq_SB.setSuffix(" kHz")
        self.chirp_start_freq_SB.setValue(50)
        self.chirp_start_freq_SB.setRange(0, 100)
        chirp_grid.addWidget(QLabel("Start:"), 0, 0)
        chirp_grid.addWidget(self.chirp_start_freq_SB, 0, 1)

        # end freq
        self.chirp_stop_freq_SB = QSpinBox()
        self.chirp_stop_freq_SB.setSuffix(" kHz")
        self.chirp_stop_freq_SB.setRange(0, 100)
        self.chirp_stop_freq_SB.setValue(100)
        chirp_grid.addWidget(QLabel("Stop:"), 1, 0)
        chirp_grid.addWidget(self.chirp_stop_freq_SB, 1, 1)

        # length of chirp
        self.chirp_duration_SB = QSpinBox()
        self.chirp_duration_SB.setValue(3)
        self.chirp_duration_SB.setRange(1, 65)
        self.chirp_duration_SB.setSuffix(" mS")
        self.chirp_duration_SB.editingFinished.connect(self.chirp_duration_SB_ef_cb)
        chirp_grid.addWidget(QLabel("Duration:"), 0, 2)
        chirp_grid.addWidget(self.chirp_duration_SB, 0, 3)

        # type of chirp
        self.chirp_type_CB = QComboBox()
        self.chirp_type_CB.addItem("linear")
        self.chirp_type_CB.addItem("quadratic")
        self.chirp_type_CB.addItem("logarithmic")
        self.chirp_type_CB.addItem("hyperbolic")
        chirp_grid.addWidget(QLabel("Type:"), 1, 2)
        chirp_grid.addWidget(self.chirp_type_CB, 1, 3)

        # gain of chirp
        self.chirp_gain_SB = QSpinBox()
        self.chirp_gain_SB.setRange(1, 4096)
        self.chirp_gain_SB.setValue(512)
        self.chirp_gain_SB.setPrefix("Gain ")
        chirp_grid.addWidget(self.chirp_gain_SB, 0, 6)

        # offset of chirp
        self.chirp_offset_SB = QSpinBox()
        self.chirp_offset_SB.setRange(1, 4096)
        self.chirp_offset_SB.setValue(2048)
        self.chirp_offset_SB.setPrefix("Offset ")
        chirp_grid.addWidget(self.chirp_offset_SB, 1, 6)

        # upload to board
        self.upload_chirp_PB = QPushButton("Upload")
        self.upload_chirp_PB.clicked.connect(self.upload_chirp_PB_Clicked)
        chirp_grid.addWidget(self.upload_chirp_PB, 0, 7)

        self.run_PB = QPushButton("RUN")
        self.run_PB.clicked.connect(self.run_PB_Clicked)
        chirp_grid.addWidget(self.run_PB, 1, 7)

        self.times_to_chirp_SB = QSpinBox()
        self.times_to_chirp_SB.setSuffix(" chirps")
        self.times_to_chirp_SB.setRange(1, 2000)
        self.times_to_chirp_SB.setValue(30)
        chirp_grid.addWidget(self.times_to_chirp_SB, 0, 8)

        self.time_to_listen_SB = QSpinBox()
        self.time_to_listen_SB.setPrefix("listen: ")
        self.time_to_listen_SB.setSuffix(" ms")
        self.time_to_listen_SB.setRange(1, 30000)
        self.time_to_listen_SB.setValue(30)
        chirp_grid.addWidget(self.time_to_listen_SB, 1, 8)

        chirp_GB.setLayout(chirp_grid)

        # -------------------------------------------------------------------
        # put together two groupboxes
        hLay = QHBoxLayout()
        # hLay.addWidget(directory_GB)
        hLay.addWidget(sonar_MCU_GB)
        hLay.addWidget(pinna_MCU)
        hLay.addWidget(chirp_GB)

        self.experiment_settings_GB.setLayout(hLay)
        self.mainVLay.addWidget(self.experiment_settings_GB)

    def populate_serial_ports_CB(self, box: ComboBox):
        available_ports = QSerialPortInfo.availablePorts()
        if len(available_ports) == 0:
            return

        curIndex = box.currentIndex()
        cur_port = box.currentText()

        box.clear()
        box.setEnabled(True)
        for i, port_info in enumerate(available_ports):
            box.addItem(port_info.portName())
            if curIndex != -1 and port_info.portName() == cur_port:
                box.setCurrentIndex(i)

    def chirp_duration_SB_ef_cb(self) -> None:
        self.time_off_SB.setValue(self.chirp_duration_SB.value() + 0.5)

    def connect_uart_PB_CB(self, cb: ComboBox, pb: QPushButton):
        # have to append for linux based systems
        port = cb.currentText()
        cb.setEnabled(True)

        if pb == self.gps_connect_PB:
            yaml_name = "gps_MCU"

        elif pb == self.emitter_connect_PB:
            yaml_name = "emit_MCU"

        elif pb == self.listener_connect_PB:
            yaml_name = "record_MCU"

        elif pb == self.left_pinna_uart_connect_PB:
            yaml_name = "left_pinnae_MCU"

        elif pb == self.right_pinna_uart_connect_PB:
            yaml_name = "right_pinnae_MCU"

        baud = self.bb_config[yaml_name]["baud"]

        if pb.isChecked():  # connected
            pb.setChecked(True)
            pb.setText("Connect")
            print(f"Disconnecting")
            if pb == self.gps_connect_PB:
                self.gps.stop()
                while self.gpsThread.is_alive():
                    self.gpsThread.join()
                self.gps.disconnect_serial()

            elif pb == self.emitter_connect_PB:
                self.emitter.disconnect_serial()

            elif pb == self.listener_connect_PB:
                self.listener.disconnect_serial()

            elif pb == self.left_pinna_uart_connect_PB:
                self.left_pinna.disconnect_serial()

            elif pb == self.right_pinna_uart_connect_PB:
                self.right_pinna.disconnect_serial()

        else:  # not connected
            if port == "":
                pb.setChecked(True)
                return

            if platform.system() == "Linux" or platform.system() == "Darwin":
                port = "/dev/" + port
                logging.debug(f"On platform: {platform.system()}")

            try:
                test = serial.Serial(port, baudrate=baud)
                if not test.is_open:
                    raise
                test.close()

                if pb == self.gps_connect_PB:
                    self.gps = bb_gps.bb_gps2(serial.Serial(port, baudrate=baud))
                    time.sleep(0.01)
                    if not self.gps.connection_status():
                        raise

                    self.gps.stop_event.clear()
                    self.gpsThread = threading.Thread(
                        target=self.gps.run, args=(self.gps_dump_path,)
                    )
                    self.gpsThread.start()

                elif pb == self.emitter_connect_PB:
                    self.emitter.connect_Serial(serial.Serial(port, baudrate=baud))
                    time.sleep(0.01)
                    if not self.emitter.connection_status():
                        raise

                elif pb == self.listener_connect_PB:
                    self.listener.connect_Serial(serial.Serial(port, baudrate=baud))
                    time.sleep(0.01)
                    if not self.listener.connection_status():
                        raise

                elif pb == self.left_pinna_uart_connect_PB:
                    self.left_pinna.config_uart(serial.Serial(port, baudrate=baud))
                    time.sleep(0.01)
                    if not self.left_pinna.connection_status():
                        raise

                elif pb == self.right_pinna_uart_connect_PB:
                    self.right_pinna.config_uart(serial.Serial(port, baudrate=baud))
                    time.sleep(0.01)
                    if not self.right_pinna.connection_status():
                        raise

            except:
                print(f"Failed to connect to {port}")
                pb.setChecked(True)

            print(f"Success connecting to: {port}")
            pb.setChecked(False)
            pb.setText("Disconnect")
            cb.setEnabled(False)

    def uart_connect_PB_pressed(self, ear) -> None:
        if ear == "left":
            new_serial_str = self.left_pinna_uart_name_CB.currentText()
        else:
            new_serial_str = self.right_pinna_uart_name_CB.currentText()

        # have to append for linux based systems
        port = new_serial_str
        if platform.system() == "Linux" or platform.system() == "Darwin":
            port = "/dev/" + new_serial_str
            logging.debug(f"On platform: {platform.system()}")

        # if the button is connect then make it disconnect
        if ear == "left":
            if self.left_pinna_uart_connect_PB.text() == "Disconnect":
                self.left_pinna_uart_connect_PB.setText("Connect")
                self.left_pinna.close_uart()
                self.left_pinna_uart_name_CB.setEnabled(True)
                return
        else:
            if self.right_pinna_uart_connect_PB.text() == "Disconnect":
                self.right_pinna_uart_connect_PB.setText("Connect")
                self.left_pinna.close_uart()
                self.right_pinna_uart_name_CB.setEnabled(True)
                return

        try:
            test = serial.Serial(port, baudrate=115200)
            test.close()

            if ear == "left":
                self.left_pinna.config_uart(port)
                logging.debug(f"left pinna using serial: {new_serial_str}")
                self.left_pinna_uart_connect_PB.setText("Disconnect")
                self.left_pinna_uart_name_CB.setEnabled(False)
            else:
                self.right_pinna.config_uart(port)
                logging.debug(f"left pinna using serial: {new_serial_str}")
                self.right_pinna_uart_connect_PB.setText("Disconnect")
                self.right_pinna_uart_name_CB.setEnabled(False)

            self.set_motor_GB_enabled(True)
        except:
            if ear == "left":
                self.left_pinna_uart_connect_PB.setText("Connect")
                self.left_pinna_uart_name_CB.setEnabled(True)
            else:
                self.right_pinna_uart_connect_PB.setText("Connect")
                self.right_pinna_uart_name_CB.setEnabled(True)

            self.set_motor_GB_enabled(False)
            logging.error(f"FAILED TO CONNECT TO {port}")
            error_msg = QErrorMessage(self)
            error_msg.showMessage(f"Serial port: {port} did not work!")

    def pinna_protocol_BG_CB(self) -> None:
        """When pinna_protocol_BG is pressed this function changes the configuration
        settings seen in the gui
        """
        button_id = self.pinna_protocol_BG.checkedId()
        if button_id == 1:  # spi
            self.mcu_grid.addWidget(self.left_pinna_spi_bus_SB, 1, 1)
            self.mcu_grid.addWidget(self.left_pinna_spi_ss_SB, 2, 1)
            self.left_pinna_spi_bus_SB.setVisible(True)
            self.left_pinna_spi_ss_SB.setVisible(True)

            self.mcu_grid.addWidget(self.right_pinna_spi_bus_SB, 1, 2)
            self.mcu_grid.addWidget(self.right_pinna_spi_ss_SB, 2, 2)
            self.right_pinna_spi_bus_SB.setVisible(True)
            self.right_pinna_spi_ss_SB.setVisible(True)

            self.mcu_grid.removeWidget(self.left_pinna_uart_name_CB)
            self.mcu_grid.removeWidget(self.left_pinna_uart_connect_PB)
            self.left_pinna_uart_name_CB.setVisible(False)
            self.left_pinna_uart_connect_PB.setVisible(False)
            self.left_pinna_uart_name_CB.setEnabled(False)
            self.left_pinna_uart_connect_PB.setEnabled(False)

            self.mcu_grid.removeWidget(self.right_pinna_uart_name_CB)
            self.mcu_grid.removeWidget(self.right_pinna_uart_connect_PB)
            self.right_pinna_uart_name_CB.setVisible(False)
            self.right_pinna_uart_connect_PB.setVisible(False)
            self.right_pinna_uart_name_CB.setEnabled(False)
            self.right_pinna_uart_connect_PB.setEnabled(False)

            self.mcu_spi_options_pressed()
            self.left_pinna.close_uart()
            self.left_pinna_uart_connect_PB.setText("Connect")
            self.set_motor_GB_enabled(True)
        else:  # UART
            # remove spi stuff
            self.mcu_grid.removeWidget(self.left_pinna_spi_bus_SB)
            self.mcu_grid.removeWidget(self.left_pinna_spi_ss_SB)
            self.left_pinna_spi_bus_SB.setVisible(False)
            self.left_pinna_spi_ss_SB.setVisible(False)

            self.mcu_grid.removeWidget(self.right_pinna_spi_bus_SB)
            self.mcu_grid.removeWidget(self.right_pinna_spi_ss_SB)
            self.right_pinna_spi_bus_SB.setVisible(False)
            self.right_pinna_spi_ss_SB.setVisible(False)

            # add uart stuff
            self.mcu_grid.addWidget(self.left_pinna_uart_name_CB, 1, 1)
            self.mcu_grid.addWidget(self.left_pinna_uart_connect_PB, 2, 1)
            self.left_pinna_uart_name_CB.setVisible(True)
            self.left_pinna_uart_name_CB.setEnabled(True)
            self.left_pinna_uart_connect_PB.setVisible(True)
            self.left_pinna_uart_connect_PB.setEnabled(True)

            self.mcu_grid.addWidget(self.right_pinna_uart_name_CB, 1, 2)
            self.mcu_grid.addWidget(self.right_pinna_uart_connect_PB, 2, 2)
            self.right_pinna_uart_name_CB.setVisible(True)
            self.right_pinna_uart_name_CB.setEnabled(True)
            self.right_pinna_uart_connect_PB.setVisible(True)
            self.right_pinna_uart_connect_PB.setEnabled(True)

            # self.set_motor_GB_enabled(False)

    def mcu_spi_options_pressed(self) -> None:
        """When option is pressed in uart or spi config area
        this calls and sets the values
        """

        bus = self.left_pinna_spi_bus_SB.value()
        ss = self.left_pinna_spi_ss_SB.value()
        self.left_pinna.config_spi(SpiDev(bus, ss))

        bus = self.right_pinna_spi_bus_SB.value()
        ss = self.right_pinna_spi_ss_SB.value()
        self.right_pinna.config_spi(SpiDev(bus, ss))
        logging.debug(f"SPI settings changed, bus: {bus}, ss: {ss}")

    def get_current_experiment_time(self):
        """Get the current time string that can be used as a file name or folder name"""
        return datetime.now().strftime("experiment_%m-%d-%Y_%H-%M-%S%p")

    def get_current_time_str(self) -> str:
        return datetime.now().strftime("%H_%M_%S")

    def experiment_folder_name_TE_contextMenu(self, position):
        """Custom context menu for experiment folder name"""
        context_menu = QMenu()

        set_current_time = context_menu.addAction("Set Current Time")
        copy_name = context_menu.addAction("Copy")
        paste_name = context_menu.addAction("Paste")
        # action = context_menu.exec(self.experiment_folder_name_TE.viewport().mapToGlobal(position))
        action = context_menu.exec(self.experiment_folder_name_TE.mapToGlobal(position))

        if action == set_current_time:
            self.experiment_folder_name_TE.setText(self.get_current_experiment_time())

    def upload_chirp_PB_Clicked(self):
        """when clicked"""

        if not self.emitter_connect_PB.isChecked():
            win = QErrorMessage(self)
            win.showMessage("EMITTER IS NOT CONNECTED!")
            return

        gain = self.chirp_gain_SB.value()
        offset = self.chirp_offset_SB.value()

        fs = self.chirp_start_freq_SB.value()
        fe = self.chirp_stop_freq_SB.value()
        tend = self.chirp_duration_SB.value()
        meth = self.chirp_type_CB.currentText()
        s, t = self.emitter.gen_chirp(
            fs * 1e3,
            fe * 1e3,
            tend,
            method=meth,
            gain=float(gain),
            offset=float(offset),
        )
        self.emitter.upload_chirp(s)

    def run_PB_Clicked(self):
        """ """

        if not self.listener_connect_PB.isChecked():
            win = QErrorMessage(self)
            win.showMessage("LISTENER IS NOT CONNECTED!")
            return

        count = 0

        Fs = 1e6
        NFFT = 512
        noverlap = 400
        spec_settings = (Fs, NFFT, noverlap, scipy.signal.windows.hann(NFFT))
        DB_range = 40
        f_plot_bounds = (30e3, 100e3)

        listen_time = self.time_to_listen_SB.value()
        times_to_chirp = self.times_to_chirp_SB.value()

        cur_time = self.get_current_time_str()
        cur_dir = self.runs_path + f"/{cur_time}"
        os.makedirs(cur_dir)
        self.emitter.save_chirp_info(cur_dir + "/chirp_info.txt")

        while True:
            raw, L, R = self.listener.listen(listen_time)

            np.save(cur_dir + f"/left_ear_{count}.npy", L)
            np.save(cur_dir + f"/right_ear_{count}.npy", R)
            # np.save(self.runs_path+f"/left_ear_{count}.npy",L)
            # np.save(self.runs_path+f"/right_ear_{count}.npy",R)

            time_off = int(self.time_off_SB.value() * 1000)
            times_plot = self.plot_frequency_SB.value()

            if count % times_plot == 0:
                spec_tup1, pt_cut1, pt1 = process(L, spec_settings, time_offs=time_off)
                spec_tup2, pt_cut2, pt2 = process(R, spec_settings, time_offs=time_off)
                self.leftPinnaeSpec.axes.cla()  # Clear the canva
                plot_spec(
                    self.leftPinnaeSpec.axes,
                    self.leftPinnaeSpec.figure,
                    spec_tup1,
                    fbounds=f_plot_bounds,
                    dB_range=DB_range,
                    plot_title="Left Pinna",
                    use_cb=not self.left_pinna_plotted,
                )
                self.leftPinnaeSpec.draw()
                self.leftPinnaeSpec.axes.set_ybound(30e3, 100e3)
                self.leftPinnaeSpec.figure.tight_layout()

                self.rightPinnaeSpec.axes.cla()  # Clear the canvas.
                plot_spec(
                    self.rightPinnaeSpec.axes,
                    self.rightPinnaeSpec.figure,
                    spec_tup2,
                    fbounds=f_plot_bounds,
                    dB_range=DB_range,
                    plot_title="Right Pinna",
                    use_cb=not self.right_pinna_plotted,
                )
                self.rightPinnaeSpec.draw()
                self.rightPinnaeSpec.figure.tight_layout()

                # self.echo_GB.update()
                self.left_pinna_plotted = self.right_pinna_plotted = True
                QApplication.processEvents()

            if count >= times_to_chirp:
                break
            count += 1

    # ----------------------------------------------------------------------
    def Add_Pinnae_Control_GB(self):
        """Adds the controls box layout"""

        self.pinnae_controls_GB = QGroupBox("Controls")

        control_h_lay = QHBoxLayout()

        self.motor_GB = [
            QGroupBox("Motor 1"),
            QGroupBox("Motor 2"),
            QGroupBox("Motor 3"),
            QGroupBox("Motor 4"),
            QGroupBox("Motor 5"),
            QGroupBox("Motor 6"),
            QGroupBox("Motor 7"),
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
            QSpinBox(),
        ]

        self.motor_min_limit_SB = [
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
        ]

        self.motor_value_SB = [
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
            QSpinBox(),
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
            QPushButton("Set Zero"),
        ]

        # number_motors = 6
        max_value = 10000

        lim_val = 90

        for index in range(NUM_PINNAE):
            vertical_layout = QVBoxLayout()

            temp_CB = QGroupBox("Control")

            # 4 row by 2 columns
            grid_lay = QGridLayout()

            # add max button
            grid_lay.addWidget(self.motor_max_PB[index], 0, 0)

            # add max spinbox
            self.motor_max_limit_SB[index].setRange(-max_value, max_value)
            self.motor_max_limit_SB[index].setValue(lim_val)
            grid_lay.addWidget(self.motor_max_limit_SB[index], 0, 1)

            # add value spinbox
            self.motor_value_SB[index].setRange(-max_value, max_value)
            grid_lay.addWidget(self.motor_value_SB[index], 1, 0)

            # add value slider
            self.motor_value_SLIDER[index].setMinimumHeight(100)
            self.motor_value_SLIDER[index].setRange(-lim_val, lim_val)
            self.motor_value_SLIDER[index].setValue(0)
            grid_lay.addWidget(self.motor_value_SLIDER[index], 1, 1)

            # add min button
            grid_lay.addWidget(self.motor_min_PB[index], 2, 0)

            # add min spinbox
            self.motor_min_limit_SB[index].setRange(-max_value, max_value)
            self.motor_min_limit_SB[index].setValue(-lim_val)
            grid_lay.addWidget(self.motor_min_limit_SB[index], 2, 1)

            ## add the layout
            vertical_layout.addLayout(grid_lay)

            # add set zero
            # vertical_layout.addWidget(self.motor_set_zero_PB[index])

            # set max width
            self.motor_GB[index].setMaximumWidth(160)

            # attach custom context menu
            self.motor_GB[index].setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu
            )
            self.motor_GB[index].customContextMenuRequested.connect(
                lambda pos, i=index: self.motor_GB_contextMenu(pos, i)
            )

            self.motor_GB[index].setLayout(vertical_layout)
            control_h_lay.addWidget(self.motor_GB[index])

        vertical_layout = QVBoxLayout()
        vertical_layout.addLayout(control_h_lay)

        hLay = QHBoxLayout()
        # add the instruction table
        self.instruction_TABLE = QTableWidget(1, NUM_PINNAE)
        hLay.addWidget(self.instruction_TABLE)

        # create layout for buttons side of table
        table_side_v_lay = QVBoxLayout()

        table_side_grid = QGridLayout()
        # control type
        self.selected_pinna_QB = QComboBox()
        self.selected_pinna_QB.addItem("left")
        self.selected_pinna_QB.addItem("right")
        self.selected_pinna_QB.addItem("both")
        table_side_grid.addWidget(QLabel("Control:"))
        table_side_grid.addWidget(self.selected_pinna_QB, 0, 1)

        # load from file
        self.load_movements_PB = QPushButton("LOAD")
        self.load_movements_PB.pressed.connect(self.load_movements_PB_cb)
        table_side_grid.addWidget(self.load_movements_PB, 1, 0)

        # HOME
        self.save_movements_PB = QPushButton("SAVE")
        self.save_movements_PB.pressed.connect(self.save_movements_PB_cb)
        table_side_grid.addWidget(self.save_movements_PB, 1, 1)

        # create start button
        self.start_stop_instruction_PB = QPushButton("Start")
        self.start_stop_instruction_PB.pressed.connect(
            self.start_stop_instruction_PB_pressed_CB
        )
        table_side_grid.addWidget(self.start_stop_instruction_PB, 2, 0)

        # acuation rate
        self.intstruction_speed_SB = QSpinBox()
        self.intstruction_speed_SB.setValue(1)
        self.intstruction_speed_SB.setRange(1, 50)
        self.intstruction_speed_SB.setSuffix(" Hz")
        table_side_grid.addWidget(self.intstruction_speed_SB, 2, 1)

        # cycle counter
        table_side_grid.addWidget(QLabel("Count:"), 3, 0)
        self.cycle_counter_SB = QSpinBox()
        self.cycle_counter_SB.setEnabled(False)
        table_side_grid.addWidget(self.cycle_counter_SB, 3, 1)

        # out of phase option
        # self.ear_phase_CB = QCheckBox("PHASE EARS")
        # self.ear_phase_CB.pressed.connect(self.ear_phase_CB_cb)
        # table_side_grid.addWidget(self.ear_phase_CB,4,0)

        # add context menu for instruction table
        self.instruction_TABLE.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.instruction_TABLE.customContextMenuRequested.connect(
            self.instruction_TABLE_contextMenu
        )

        # connect instruction table cell change callback
        self.instruction_TABLE.cellChanged.connect(
            self.instruction_TABLE_cellChanged_callback
        )

        # set default values in table
        for i in range(NUM_PINNAE):
            intNum = QTableWidgetItem()
            intNum.setData(0, 0)
            self.instruction_TABLE.setItem(0, i, intNum)

        # attach callbacks for controller tendon api
        self.add_motor_control_CB()

        table_side_v_lay.addLayout(table_side_grid)

        hLay.addLayout(table_side_v_lay)
        vertical_layout.addLayout(hLay)

        self.pinnae_controls_GB.setLayout(vertical_layout)
        self.mainVLay.addWidget(self.pinnae_controls_GB)

    def ear_phase_CB_cb(self):
        pass

    def save_movements_PB_cb(self):
        fd = QFileDialog(self)

        file_path, _ = fd.getSaveFileName(
            None, "Save movements", "", "YAML Files (*.yaml)"
        )

        if file_path:
            num_rows = self.instruction_TABLE.rowCount()

            array_2d = [[0] * NUM_PINNAE for _ in range(num_rows)]

            for row in range(num_rows):
                for col in range(NUM_PINNAE):
                    data = self.instruction_TABLE.item(row, col)
                    array_2d[row][col] = int(data.text())

            data = {
                "pinna_movements": {
                    "speed": self.intstruction_speed_SB.value(),
                    "angles": array_2d,
                }
            }

            splitted = file_path.split(".")
            file_path = splitted[0] + "_PM.yaml"
            print(f" save path {file_path}")

            with open(file_path, "w") as f:
                yaml.dump(data, f)
        else:
            print("no save")

    def load_movements_PB_cb(self):
        fd = QFileDialog(self)
        fd.setWindowTitle("Open File")
        fd.setNameFilter("YAML files (*.yaml)")
        fd.setFileMode(QFileDialog.FileMode.ExistingFiles)

        if fd.exec():
            selected_files = fd.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                print("Selected file:", file_path)
                with open(file_path, "r") as f:
                    yam_file = yaml.safe_load(f)

                if not "pinna_movements" in yam_file:
                    win = QErrorMessage(self)
                    win.showMessage("Did not find valid 'pinna_movements' in file!")
                    return

                angles = yam_file["pinna_movements"]["angles"]
                print("Angles:")

                num_rows = len(angles)

                self.instruction_TABLE.clear()
                self.instruction_TABLE.setRowCount(num_rows)

                for row, angle_row in enumerate(angles):
                    for col, angle in enumerate(angle_row):
                        newItem = QTableWidgetItem()
                        newItem.setData(0, int(angle))
                        self.instruction_TABLE.setItem(row, col, newItem)

                self.intstruction_speed_SB.setValue(
                    int(yam_file["pinna_movements"]["speed"])
                )

            else:
                return
        else:
            return

    def motor_GB_contextMenu(self, position, index) -> None:
        """Create menu for each motor box to reduce the number of buttons

        Args:
            position (int): passed from qt, position on context menu
            index (int): which motor box this is coming from
        """
        assert index < NUM_PINNAE, f"{index} is greater than number of pinnaes!"
        context_menu = QMenu()
        context_menu.addMenu(f"Motor {index+1}:")

        set_zero = context_menu.addAction("Set Zero")
        max_value = context_menu.addAction("Max")
        min_value = context_menu.addAction("Min")
        cw_home_value = context_menu.addAction("HOME CW")
        ccw_home_value = context_menu.addAction("HOME CCW")

        action = context_menu.exec(self.motor_GB[index].mapToGlobal(position))

        if action == set_zero:
            self.motor_set_zero_PB_callback(index)
        elif action == max_value:
            self.motor_max_PB_pressed(index)
        elif action == min_value:
            self.motor_min_PB_pressed(index)
        elif action == cw_home_value:
            if self.selected_pinna_QB.currentText() == "left":
                self.left_pinna.move_to_min(index, move_cw=True)
            elif self.selected_pinna_QB.currentText() == "right":
                self.right_pinna.move_to_min(index, move_cw=True)
            elif self.selected_pinna_QB.currentText() == "both":
                self.left_pinna.move_to_min(index, move_cw=True)
                self.right_pinna.move_to_min(index, move_cw=True)

            self.motor_value_SB[index].blockSignals()
            self.motor_value_SLIDER[index].blockSignals()
            self.motor_value_SB[index].setValue(0)
            self.motor_value_SLIDER[index].setValue(0)
            self.motor_value_SB[index].blockSignals(False)
            self.motor_value_SLIDER[index].blockSignals(False)

        elif action == ccw_home_value:
            if self.selected_pinna_QB.currentText() == "left":
                self.left_pinna.move_to_min(index, move_cw=False)
                self.left
            elif self.selected_pinna_QB.currentText() == "right":
                self.right_pinna.move_to_min(index, move_cw=False)
            elif self.selected_pinna_QB.currentText() == "both":
                self.left_pinna.move_to_min(index, move_cw=False)
                self.right_pinna.move_to_min(index, move_cw=False)

            self.motor_value_SB[index].blockSignals()
            self.motor_value_SLIDER[index].blockSignals()
            self.motor_value_SB[index].setValue(0)
            self.motor_value_SLIDER[index].setValue(0)
            self.motor_value_SB[index].blockSignals(False)
            self.motor_value_SLIDER[index].blockSignals(False)

    def set_motor_GB_enabled(self, enabled: bool) -> None:
        """Sets the motor control boxes to desired state making the user not able to touch them

        Args:
            enabled (bool): state to set control box
        """
        try:
            for i in range(NUM_PINNAE):
                self.motor_GB[i].setEnabled(enabled)
        except:
            pass

    def instruction_TABLE_cellChanged_callback(self, row, column):
        """called when table cell values are changed

        Args:
            row (int): row index
            column (int): col index
        """
        logging.debug("instruction_TABLE_cellChanged")

        new_value = float(self.instruction_TABLE.item(row, column).text())
        # clamp against max value
        if new_value > self.left_pinna.get_motor_max_limit(column):
            # clamp the value
            newItem = QTableWidgetItem()
            newItem.setData(0, int(self.left_pinna.get_motor_max_limit(column)))
            print(self.left_pinna.get_motor_max_limit(column))
            self.instruction_TABLE.setItem(row, column, newItem)
            logging.debug("Clamped value max")

        # clamp against min value
        if new_value < self.left_pinna.get_motor_min_limit(column):
            # clamp
            newItem = QTableWidgetItem()
            newItem.setData(0, int(self.left_pinna.get_motor_min_limit(column)))
            self.instruction_TABLE.setItem(row, column, newItem)
            logging.debug("Clamped value min")

    def start_stop_instruction_PB_pressed_CB(self):
        if not self.instructionThreadRunning:
            rows = self.instruction_TABLE.rowCount()
            dataArray = np.zeros((rows, NUM_PINNAE), np.int16)

            for row in range(self.instruction_TABLE.rowCount()):
                dataArray[row][0] = int(self.instruction_TABLE.item(row, 0).text())
                dataArray[row][1] = int(self.instruction_TABLE.item(row, 1).text())
                dataArray[row][2] = int(self.instruction_TABLE.item(row, 2).text())
                dataArray[row][3] = int(self.instruction_TABLE.item(row, 3).text())
                dataArray[row][4] = int(self.instruction_TABLE.item(row, 4).text())
                dataArray[row][5] = int(self.instruction_TABLE.item(row, 5).text())
                dataArray[row][6] = int(self.instruction_TABLE.item(row, 6).text())

            # print(dataArray)
            if self.selected_pinna_QB.currentText() == "left":
                self.instructionThread = RunInstructionsThread(
                    dataArray, self.intstruction_speed_SB.value(), self.left_pinna
                )

            elif self.selected_pinna_QB.currentText() == "right":
                self.instructionThread = RunInstructionsThread(
                    dataArray, self.intstruction_speed_SB.value(), self.right_pinna
                )

            elif self.selected_pinna_QB.currentText() == "both":
                self.instructionThread = RunInstructionsThread(
                    dataArray,
                    self.intstruction_speed_SB.value(),
                    self.left_pinna,
                    self.right_pinna,
                )

            self.instructionThread.start()
            self.instructionThread.cycle_complete.connect(
                self.cycle_complete_emit_callback
            )
            self.instructionThread.end_motor_angles.connect(
                self.end_motor_values_emit_callback
            )
            self.instructionThreadRunning = True
            self.start_stop_instruction_PB.setText("Stop")
            self.set_motor_GB_enabled(False)
        else:
            # see end_motor_values_emit_callback for enabling - we want to update values first before enabling
            #  self.set_motor_GB_enabled(True)
            self.instructionThreadRunning = False
            self.start_stop_instruction_PB.setText("Start")
            if (
                self.instructionThread is not None
                and self.instructionThread.isRunning()
            ):
                self.instructionThread.stop()

    def cycle_complete_emit_callback(self, dataIn):
        self.cycle_counter_SB.setValue(dataIn)

    def end_motor_values_emit_callback(self, dataIn):
        for i in range(NUM_PINNAE):
            self.motor_value_SB[i].blockSignals(True)
            self.motor_value_SLIDER[i].blockSignals(True)

            self.motor_value_SB[i].setValue(dataIn[i])
            self.motor_value_SLIDER[i].setValue(dataIn[i])

            self.motor_value_SB[i].blockSignals(False)
            self.motor_value_SLIDER[i].blockSignals(False)
        self.set_motor_GB_enabled(True)

    def instruction_TABLE_contextMenu(self, position):
        context_menu = QMenu()

        add_row_action = context_menu.addAction("Add Row")
        delete_row_action = context_menu.addAction("Delete Row")
        duplicate_row_action = context_menu.addAction("Duplicate Row")
        paste_max_action = context_menu.addAction("Paste Max's")
        paste_min_action = context_menu.addAction("Paste Min's")
        paste_current_angles_action = context_menu.addAction("Paste Current Angles")
        action = context_menu.exec(
            self.instruction_TABLE.viewport().mapToGlobal(position)
        )

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
        rows = self.instruction_TABLE.rowCount() + 1
        self.instruction_TABLE.setRowCount(rows)
        self.instruction_TABLE.update()

        for i in range(NUM_PINNAE):
            intNum = QTableWidgetItem()

            min = int(self.left_pinna.get_motor_min_limit(i))
            intNum.setData(0, min)
            self.instruction_TABLE.setItem(rows - 1, i, intNum)

    def instruction_TABLE_contextMenu_delete_row(self):
        if self.instruction_TABLE.currentRow() >= 0:
            self.instruction_TABLE.removeRow(self.instruction_TABLE.currentRow())
            logging.debug("deleted row")

        if self.instruction_TABLE.rowCount() == 0:
            self.instruction_TABLE_contextMenu_add_row()

    def instruction_TABLE_contextMenu_duplicate_row(self):
        selected_row = self.instruction_TABLE.currentRow()
        num_rows = self.instruction_TABLE.rowCount()

        if selected_row >= 0:
            row_items = [
                self.instruction_TABLE.item(selected_row, col).text()
                for col in range(NUM_PINNAE)
            ]
            self.instruction_TABLE.setRowCount(num_rows + 1)

            for col, text in enumerate(row_items):
                newItem = QTableWidgetItem()
                newItem.setData(0, int(text))
                self.instruction_TABLE.setItem(num_rows, col, newItem)

    def instruction_TABLE_contextMenu_paste_maxs(self):
        selected_row = self.instruction_TABLE.currentRow()

        if selected_row >= 0:
            for col, max_val in enumerate(self.motor_max_limit_SB):
                newItem = QTableWidgetItem()
                newItem.setData(0, int(max_val.value()))
                self.instruction_TABLE.setItem(selected_row, col, newItem)

    def instruction_TABLE_contextMenu_paste_mins(self):
        selected_row = self.instruction_TABLE.currentRow()

        if selected_row >= 0:
            for col, min_val in enumerate(self.motor_min_limit_SB):
                newItem = QTableWidgetItem()
                newItem.setData(0, int(min_val.value()))
                self.instruction_TABLE.setItem(selected_row, col, newItem)

    def instruction_TABLE_contextMenu_paste_current(self):
        selected_row = self.instruction_TABLE.currentRow()

        if selected_row >= 0:
            for col, motor_val in enumerate(self.motor_value_SB):
                newItem = QTableWidgetItem()
                newItem.setData(0, int(motor_val.value()))
                self.instruction_TABLE.setItem(selected_row, col, newItem)

    def add_motor_control_CB(self):
        """Connects the motor tendons sliders to the api"""

        # attach max buttons
        for i in range(NUM_PINNAE):
            self.motor_max_PB[i].pressed.connect(
                lambda index=i: self.motor_max_PB_pressed(index)
            )

        # attach max limit spinbox
        for i in range(NUM_PINNAE):
            self.motor_max_limit_SB[i].editingFinished.connect(
                lambda index=i: self.motor_max_limit_changed_CB(index)
            )

        # attach min buttons
        for i in range(NUM_PINNAE):
            self.motor_min_PB[i].pressed.connect(
                lambda index=i: self.motor_min_PB_pressed(index)
            )

        # attach min limit spinbox
        for i in range(NUM_PINNAE):
            self.motor_min_limit_SB[i].editingFinished.connect(
                lambda index=i: self.motor_min_limit_changed_CB(index)
            )

        # attach set to zero buttons
        for i in range(NUM_PINNAE):
            self.motor_set_zero_PB[i].pressed.connect(
                lambda index=i: self.motor_set_zero_PB_callback(index)
            )

        # attach sliders
        for i in range(NUM_PINNAE):
            self.motor_value_SLIDER[i].valueChanged.connect(
                lambda value, index=i: self.motor_value_SLIDER_valueChanged(index)
            )

        # attach spinbox
        for i in range(NUM_PINNAE):
            self.motor_value_SB[i].editingFinished.connect(
                lambda index=i: self.motor_value_SB_valueChanged(index)
            )

        # adjust the slider and spinbox range
        for i in range(NUM_PINNAE):
            self.motor_max_limit_changed_CB(i)
            self.motor_min_limit_changed_CB(i)

    def motor_max_PB_pressed(self, index):
        """Sets the current motor to its max value

        Args:
            index (_type_): index of motor
        """
        if self.selected_pinna_QB.currentText() == "left":
            self.left_pinna.set_motor_to_max(index)

        elif self.selected_pinna_QB.currentText() == "right":
            self.right_pinna.set_motor_to_max(index)

        else:
            self.right_pinna.set_motor_to_max(index)
            self.left_pinna.set_motor_to_max(index)

        self.motor_value_SB[index].setValue(self.motor_max_limit_SB[index].value())
        self.motor_value_SLIDER[index].setValue(self.motor_max_limit_SB[index].value())

    def motor_min_PB_pressed(self, index):
        """Sets the current motor to its min value

        Args:
            index (_type_): index of motor
        """
        if self.selected_pinna_QB.currentText() == "left":
            self.left_pinna.set_motor_to_min(index)

        elif self.selected_pinna_QB.currentText() == "right":
            self.right_pinna.set_motor_to_min(index)

        else:
            self.right_pinna.set_motor_to_min(index)
            self.left_pinna.set_motor_to_min(index)

        self.motor_value_SB[index].setValue(self.motor_min_limit_SB[index].value())
        self.motor_value_SLIDER[index].setValue(self.motor_min_limit_SB[index].value())

    def motor_value_SB_valueChanged(self, index):
        """Sets the new spin


        Args:
            index (_type_): index to change
        """
        if self.motor_value_SB[index].value() != self.motor_value_SLIDER[index].value():
            self.motor_value_SLIDER[index].setValue(self.motor_value_SB[index].value())

            if self.selected_pinna_QB.currentText() == "left":
                self.left_pinna.set_motor_angle(
                    index, self.motor_value_SB[index].value()
                )

            elif self.selected_pinna_QB.currentText() == "right":
                self.right_pinna.set_motor_angle(
                    index, self.motor_value_SB[index].value()
                )

            else:
                # if index >= 3:
                #     mult = -1
                # else:
                #     mult = 1
                mult = 1

                if index != 6 and index != 5:
                    self.left_pinna.set_motor_angle(
                        index, self.motor_value_SLIDER[index].value() * mult
                    )
                    self.right_pinna.set_motor_angle(
                        index, self.motor_value_SLIDER[index].value() * mult
                    )
                else:
                    if index == 5:
                        self.left_pinna.set_motor_angle(
                            index, self.motor_value_SLIDER[index].value() * mult
                        )
                    elif index == 6:
                        self.right_pinna.set_motor_angle(
                            5, self.motor_value_SLIDER[index].value() * mult
                        )

    def motor_value_SLIDER_valueChanged(self, index):
        """Sets the slider value

        Args:
            index (_type_): index to change
        """
        if self.motor_value_SLIDER[index].value() != self.motor_value_SB[index].value():
            self.motor_value_SB[index].setValue(self.motor_value_SLIDER[index].value())

            if self.selected_pinna_QB.currentText() == "left":
                self.left_pinna.set_motor_angle(
                    index, self.motor_value_SLIDER[index].value()
                )

            elif self.selected_pinna_QB.currentText() == "right":
                self.right_pinna.set_motor_angle(
                    index, self.motor_value_SLIDER[index].value()
                )

            else:
                # if index >= 3:
                #     mult = -1
                # else:
                #     mult = 1
                mult = 1

                if index != 6 and index != 5:
                    self.left_pinna.set_motor_angle(
                        index, self.motor_value_SLIDER[index].value() * mult
                    )
                    self.right_pinna.set_motor_angle(
                        index, self.motor_value_SLIDER[index].value() * mult
                    )
                else:
                    if index == 5:
                        self.left_pinna.set_motor_angle(
                            index, self.motor_value_SLIDER[index].value() * mult
                        )
                    elif index == 6:
                        self.right_pinna.set_motor_angle(
                            5, self.motor_value_SLIDER[index].value() * mult
                        )

    def motor_set_zero_PB_callback(self, index):
        """Callback for when the set new zero push button is set

        Args:
            index (_type_): changing motor new zero position
        """

        if self.selected_pinna_QB.currentText() == "left":
            self.left_pinna.set_new_zero_position(index)
            [min, max] = self.left_pinna.get_motor_limit(index)
        elif self.selected_pinna_QB.currentText() == "right":
            self.right_pinna.set_new_zero_position(index)
            [min, max] = self.right_pinna.get_motor_limit(index)
        else:
            self.left_pinna.set_new_zero_position(index)
            self.right_pinna.set_new_zero_position(index)
            [min, max] = self.right_pinna.get_motor_limit(index)

        # adjust the new limits of spinbox
        self.motor_max_limit_SB[index].setValue(max)
        self.motor_min_limit_SB[index].setValue(min)

        # set new values to 0
        self.motor_value_SB[index].setValue(0)
        self.motor_value_SLIDER[index].setValue(0)

    def motor_max_limit_changed_CB(self, index):
        """callback when limit spinbox is changed

        Args:
            index (_type_): index of motors
        """

        new_value = self.motor_max_limit_SB[index].value()

        if self.selected_pinna_QB.currentText() == "left":
            if self.left_pinna.set_motor_max_limit(index, new_value):
                [min, max] = self.left_pinna.get_motor_limit(index)
                self.motor_value_SLIDER[index].setRange(min, max)
                self.motor_value_SB[index].setRange(min, max)

                num_rows = self.instruction_TABLE.rowCount()
                for i in range(num_rows):
                    self.instruction_TABLE_cellChanged_callback(i, index)
            else:
                self.motor_max_limit_SB[index].setValue(
                    self.left_pinna.get_motor_max_limit(index)
                )
                error_msg = QErrorMessage(self)
                error_msg.showMessage("New max is greater than current angle!")

        elif self.selected_pinna_QB.currentText() == "right":
            if self.right_pinna.set_motor_max_limit(index, new_value):
                [min, max] = self.left_pinna.get_motor_limit(index)
                self.motor_value_SLIDER[index].setRange(min, max)
                self.motor_value_SB[index].setRange(min, max)

                num_rows = self.instruction_TABLE.rowCount()
                for i in range(num_rows):
                    self.instruction_TABLE_cellChanged_callback(i, index)
            else:
                self.motor_max_limit_SB[index].setValue(
                    self.right_pinna.get_motor_max_limit(index)
                )
                error_msg = QErrorMessage(self)
                error_msg.showMessage("New max is greater than current angle!")
        else:
            if self.right_pinna.set_motor_max_limit(
                index, new_value
            ) and self.left_pinna.set_motor_max_limit(index, new_value):
                [min, max] = self.left_pinna.get_motor_limit(index)
                self.motor_value_SLIDER[index].setRange(min, max)
                self.motor_value_SB[index].setRange(min, max)

                num_rows = self.instruction_TABLE.rowCount()
                for i in range(num_rows):
                    self.instruction_TABLE_cellChanged_callback(i, index)
            else:
                self.motor_max_limit_SB[index].setValue(
                    self.right_pinna.get_motor_max_limit(index)
                )
                error_msg = QErrorMessage(self)
                error_msg.showMessage("New max is greater than current angle!")

    def motor_min_limit_changed_CB(self, index):
        """callback when limit spinbox is changed

        Args:
            index (_type_): index of motors
        """

        new_value = self.motor_min_limit_SB[index].value()

        if self.selected_pinna_QB.currentText() == "left":
            if self.left_pinna.set_motor_min_limit(index, new_value):
                [min, max] = self.left_pinna.get_motor_limit(index)
                self.motor_value_SLIDER[index].setRange(min, max)
                self.motor_value_SB[index].setRange(min, max)

                num_rows = self.instruction_TABLE.rowCount()
                for i in range(num_rows):
                    self.instruction_TABLE_cellChanged_callback(i, index)
            else:
                self.motor_min_limit_SB[index].setValue(
                    self.left_pinna.get_motor_min_limit(index)
                )
                error_msg = QErrorMessage(self)
                error_msg.showMessage("New min is less than current angle!")

        elif self.selected_pinna_QB.currentText() == "right":
            if self.right_pinna.set_motor_min_limit(index, new_value):
                [min, max] = self.right_pinna.get_motor_limit(index)
                self.motor_value_SLIDER[index].setRange(min, max)
                self.motor_value_SB[index].setRange(min, max)

                num_rows = self.instruction_TABLE.rowCount()
                for i in range(num_rows):
                    self.instruction_TABLE_cellChanged_callback(i, index)
            else:
                self.motor_min_limit_SB[index].setValue(
                    self.right_pinna.get_motor_min_limit(index)
                )
                error_msg = QErrorMessage(self)
                error_msg.showMessage("New min is less than current angle!")
        else:
            if self.right_pinna.set_motor_min_limit(
                index, new_value
            ) and self.left_pinna.set_motor_min_limit(index, new_value):
                [min, max] = self.right_pinna.get_motor_limit(index)
                self.motor_value_SLIDER[index].setRange(min, max)
                self.motor_value_SB[index].setRange(min, max)

                num_rows = self.instruction_TABLE.rowCount()
                for i in range(num_rows):
                    self.instruction_TABLE_cellChanged_callback(i, index)
            else:
                self.motor_min_limit_SB[index].setValue(
                    self.right_pinna.get_motor_min_limit(index)
                )
                error_msg = QErrorMessage(self)
                error_msg.showMessage("New min is less than current angle!")

    # ----------------------------------------------------------------------
    def init_echoControl_box(self):
        """Adds the sonar box layout"""
        self.echo_GB = QGroupBox("Echos")
        self.echo_GB.setMinimumHeight(300)
        vLay = QVBoxLayout()

        settings_lay = QHBoxLayout()

        self.plot_frequency_SB = QSpinBox()
        self.plot_frequency_SB.setPrefix("Plot every ")
        self.plot_frequency_SB.setSuffix(" chirps")
        self.plot_frequency_SB.setRange(0, 100)
        self.plot_frequency_SB.setValue(2)
        settings_lay.addWidget(self.plot_frequency_SB)

        self.time_off_SB = QDoubleSpinBox()
        self.time_off_SB.setPrefix("Plot cut off: ")
        self.time_off_SB.setSuffix(" ms")
        self.time_off_SB.setRange(0, 1000)
        self.time_off_SB.setDecimals(2)
        self.time_off_SB.setSingleStep(0.25)
        settings_lay.addWidget(self.time_off_SB)
        self.chirp_duration_SB_ef_cb()

        vLay.addLayout(settings_lay)

        # left pinnae spectogram
        hLay = QHBoxLayout()
        self.leftPinnaeSpec = MplCanvas(self, width=5, height=4, dpi=100)
        self.leftPinnaeSpec.axes.set_title("Left Pinna")

        hLay.addWidget(self.leftPinnaeSpec)

        # ---------------------------------------------
        # right pinnae spectogram
        self.rightPinnaeSpec = MplCanvas(self, width=5, height=4, dpi=100)
        self.rightPinnaeSpec.axes.set_title("Right Pinna")

        hLay.addWidget(self.rightPinnaeSpec)
        vLay.addLayout(hLay)
        self.echo_GB.setLayout(vLay)

    def Add_Echo_GB(self):
        """adds sonar and gps box"""
        self.init_echoControl_box()

        self.echo_layout = QVBoxLayout()
        self.echo_layout.addWidget(self.echo_GB)

        self.mainVLay.addLayout(self.echo_layout)

    def closeEvent(self, event):
        plt.close("all")
        try:
            self.listener.disconnect_serial()
        except:
            pass
        try:
            self.emitter.disconnect_serial
        except:
            pass

        try:
            self.gps.stop()
            while self.gpsThread.is_alive():
                self.gpsThread.join()
        except:
            pass

        try:
            self.gps.disconnect_serial
        except:
            pass
        event.accept()


class RunInstructionsThread(QThread):
    cycle_complete = pyqtSignal(int)
    end_motor_angles = pyqtSignal(list)

    def __init__(
        self,
        dataArray,
        freq,
        l_pinna: PinnaeController,
        r_pinna: PinnaeController = None,
    ):
        QThread.__init__(self)
        self.data = dataArray
        self.timeBetween = 1 / freq
        self.runThread = True
        self.curIndex = 0
        self.maxIndex = len(dataArray)
        self.l_pinna = l_pinna
        self.r_pinna = r_pinna
        self.cycle_count = 0

    def run(self):
        logging.debug("RunInstructionsThread starting")
        right_data = self.data
        if self.r_pinna is not None:
            right_data[:, 5] = self.data[:, 6]

        while self.runThread:
            self.l_pinna.set_motor_angles(self.data[self.curIndex])
            self.r_pinna.set_motor_angles(right_data[self.curIndex])

            print(self.data[self.curIndex])
            self.curIndex += 1
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
    try:
        app = QApplication([])
        widget = BBGUI()
        widget.show()
        sys.exit(app.exec())
    except KeyboardInterrupt:
        exit()
