from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QSpinBox,
    QHBoxLayout,
    QPushButton
)

import PyQt6.QtCore as QtCore

class MotorWidget(QWidget):

    def __init__(self, title="", parent=None):
        super(MotorWidget, self).__init__(parent)
        
        self.lay = QVBoxLayout(self)

        self.max_angle_SB = QSpinBox()
        self.max_angle_SB.setValue(180)
        self.max_angle_SB.setRange(0, 180)

        self.min_angle_SB = QSpinBox()
        self.min_angle_SB.setValue(-180)
        self.min_angle_SB.setRange(-180, 0)

        self.pid_widget = QWidget()
        self.pid_lay = QHBoxLayout()
        self.pid_lay.addWidget(QLabel("P"))
        self.pid_lay.addWidget(QSpinBox())
        self.pid_lay.addWidget(QLabel("I"))
        self.pid_lay.addWidget(QSpinBox())
        self.pid_lay.addWidget(QLabel("D"))
        self.pid_lay.addWidget(QSpinBox())
        self.pid_widget.setLayout(self.pid_lay)

        self.lay.addWidget(QLabel(title))
        self.lay.addWidget(QLabel("Max Angle"))
        self.lay.addWidget(self.max_angle_SB)
        self.lay.addWidget(QLabel("Min Angle"))
        self.lay.addWidget(self.min_angle_SB)
        self.lay.addWidget(QLabel("PID Parameters"))
        self.lay.addWidget(self.pid_widget)

        self.lay.addWidget(QPushButton("Go to Max Angle"))
        self.lay.addWidget(QPushButton("Go to Min Angle"))

        self.setLayout(self.lay)

