from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame
from src.bezierEditConverted import Ui_Form


class BezierEditWidget(QFrame, Ui_Form):
    sgl_cancel = pyqtSignal(str)
    sgl_save = pyqtSignal(str)

    def __init__(self, parent=None):
        super(BezierEditWidget, self).__init__(parent)

        self.init_ui()
        self.init_event()
        self.setStyleSheet("""
            QFrame{
                background:none;
                background-color:#AAFFFFFF;
            }
        """)

    def init_ui(self):
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showMaximized()

    def init_event(self):
        self.pb_save.clicked.connect(self.save_edit)
        self.pb_cancel.clicked.connect(self.cancel)

    def save_edit(self):
        self.sgl_save[str].emit("completed")
        self.close()

    def cancel(self):
        self.sgl_cancel[str].emit("canceled")
        self.close()
