import signal
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QDockWidget,
    QScrollArea,
    QVBoxLayout,
    QLabel
)

import PyQt6.QtCore as QtCore

from batbot7_bringup.gui.CollapsibleBox import CollapsibleBox
from batbot7_bringup.gui.BBGui import BBGui

signal.signal(signal.SIGINT, signal.SIG_DFL)

if __name__ == "__main__":
    app = QApplication([])
    w = QMainWindow()
    w.setCentralWidget(QWidget())
    dock = QDockWidget("Collapsible Demo")
    w.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock)
    controls = BBGui()
    dock.setWidget(controls)

    # lay = QVBoxLayout()
    # for i in range(10):
    #     label = QLabel(f'Label {i}')
    #     label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    #     lay.addWidget(label)

    # collapsible.setContentLayout(lay)

    w.resize(640, 480)
    w.show()

    sys.exit(app.exec())
