from PyQt5 import QtCore
from PyQt5.QtWidgets import QTableView


class TableViewer(QTableView):

    def __init__(self):
        super(TableViewer, self).__init__()
        self.init_event()

    def init_event(self):
        self.doubleClicked.connect(self.double_clicked)
        self.entered.connect(self.cell_entered)

    def currentChanged(self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex) -> None:
        current = current.row(), current.column()
        previous = previous.row(), previous.column()

    def double_clicked(self, event):
        current = event.row(), event.column()

    def cell_entered(self, event):
        current = event.row(), event.column()
