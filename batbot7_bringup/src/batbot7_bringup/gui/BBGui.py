from PyQt6.QtWidgets import (
    QWidget,
    QScrollArea,
    QVBoxLayout,
    QLabel,
    QSpinBox,
    QComboBox,
    QPushButton
)

import PyQt6.QtCore as QtCore

from batbot7_bringup.gui.CollapsibleBox import CollapsibleBox
from batbot7_bringup.gui.MotorWidget import MotorWidget

class BBGui(QWidget):

    def __init__(self, title="", parent=None):
        super(BBGui, self).__init__(parent)

        self.scrollArea = QScrollArea(self)
        self.sonar_collapsible = CollapsibleBox("Sonar")
        self.motor_collapsible = CollapsibleBox("Motor Control")
        self.content = QWidget()
        self.scrollboxlay = QVBoxLayout()

        self.scrollboxlay.setSpacing(0)
        self.scrollboxlay.setContentsMargins(0,0,0,0);

        self.fillSonarControls()
        self.fillMotorControls()

        self.scrollboxlay.addWidget(self.sonar_collapsible)
        self.scrollboxlay.addWidget(self.motor_collapsible)

        self.content.setLayout(self.scrollboxlay)
        self.scrollArea.setWidget(self.content)

        self.vlay = QVBoxLayout(self)
        self.vlay.addWidget(self.scrollArea)

    def fillSonarControls(self):

        sonar_lay = QVBoxLayout()

        sonar_lay.addWidget(QLabel("Emitter Device Port"))
        emitter_ports_CB = QComboBox()
        # emitter_ports_CB.setFixedWidth(CB_WIDTH)
        emitter_ports_CB.setPlaceholderText("SEARCH")
        sonar_lay.addWidget(emitter_ports_CB)
        emitter_connect_PB = QPushButton("Connect")
        emitter_connect_PB.setCheckable(True)
        emitter_connect_PB.setAutoExclusive(False)
        sonar_lay.addWidget(emitter_connect_PB)

        # listener
        sonar_lay.addWidget(QLabel("Listener"))
        listener_ports_CB = QComboBox()
        # listener_ports_CB.setFixedWidth(CB_WIDTH)
        listener_ports_CB.setPlaceholderText("SEARCH")
        sonar_lay.addWidget(listener_ports_CB)
        listener_connect_PB = QPushButton("Connect")
        listener_connect_PB.setCheckable(True)
        listener_connect_PB.setAutoExclusive(False)
        sonar_lay.addWidget(listener_connect_PB)

        # start freq
        chirp_start_freq_SB = QSpinBox()
        chirp_start_freq_SB.setSuffix(" kHz")
        chirp_start_freq_SB.setValue(50)
        chirp_start_freq_SB.setRange(0, 100)
        sonar_lay.addWidget(QLabel("Start"))
        sonar_lay.addWidget(chirp_start_freq_SB)

        # # end freq
        chirp_stop_freq_SB = QSpinBox()
        chirp_stop_freq_SB.setSuffix(" kHz")
        chirp_stop_freq_SB.setRange(0, 100)
        chirp_stop_freq_SB.setValue(100)
        sonar_lay.addWidget(QLabel("Stop"))
        sonar_lay.addWidget(chirp_stop_freq_SB)

        # # length of chirp
        chirp_duration_SB = QSpinBox()
        chirp_duration_SB.setValue(3)
        chirp_duration_SB.setRange(1, 65)
        chirp_duration_SB.setSuffix(" mS")
        # self.chirp_duration_SB.editingFinished.connect(self.chirp_duration_SB_ef_cb)
        sonar_lay.addWidget(QLabel("Duration"))
        sonar_lay.addWidget(chirp_duration_SB)

        # # type of chirp
        chirp_type_CB = QComboBox()
        chirp_type_CB.addItem("Linear")
        chirp_type_CB.addItem("Quadratic")
        chirp_type_CB.addItem("Logarithmic")
        chirp_type_CB.addItem("Hyperbolic")
        sonar_lay.addWidget(QLabel("Chirp Type"))
        sonar_lay.addWidget(chirp_type_CB)

        # # gain of chirp
        chirp_gain_SB = QSpinBox()
        chirp_gain_SB.setRange(1, 4096)
        chirp_gain_SB.setValue(512)
        sonar_lay.addWidget(QLabel("Gain"))
        sonar_lay.addWidget(chirp_gain_SB)

        # # offset of chirp
        chirp_offset_SB = QSpinBox()
        chirp_offset_SB.setRange(1, 4096)
        chirp_offset_SB.setValue(2048)
        sonar_lay.addWidget(QLabel("Offset"))
        sonar_lay.addWidget(chirp_offset_SB)

        # # upload to board
        upload_chirp_PB = QPushButton("Upload")
        # upload_chirp_PB.clicked.connect(self.upload_chirp_PB_Clicked)
        sonar_lay.addWidget(upload_chirp_PB)

        run_PB = QPushButton("RUN")
        # run_PB.clicked.connect(self.run_PB_Clicked)
        sonar_lay.addWidget(run_PB)

        times_to_chirp_SB = QSpinBox()
        times_to_chirp_SB.setSuffix(" chirps")
        times_to_chirp_SB.setRange(1, 2000)
        times_to_chirp_SB.setValue(30)
        sonar_lay.addWidget(times_to_chirp_SB)

        time_to_listen_SB = QSpinBox()
        time_to_listen_SB.setPrefix("listen: ")
        time_to_listen_SB.setSuffix(" ms")
        time_to_listen_SB.setRange(1, 30000)
        time_to_listen_SB.setValue(30)
        sonar_lay.addWidget(time_to_listen_SB)

        sonar_lay.addStretch()
        self.sonar_collapsible.setContentLayout(sonar_lay)

    def fillMotorControls(self):
        motor_lay = QVBoxLayout()

        for i in range(0, 8):
            motor_lay.addWidget(MotorWidget(f"Motor {i + 1}"))

        self.motor_collapsible.setContentLayout(motor_lay)