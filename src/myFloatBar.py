import time
from enum import Enum

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QCoreApplication, QSize, QRectF, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QPixmap
from src.utils import *

from PyQt5.QtWidgets import QFrame, QColorDialog

from src.floatBarConverted import Ui_float_bar


class BrushShape(Enum):
    brRect = 0
    brCircle = 1
    brStar = 2
    brLine = 3


class FloatBar(QFrame, Ui_float_bar):
    sgl_brush_color_changed = pyqtSignal(tuple)
    sgl_brush_shape_changed = pyqtSignal(int)

    curEdgeColor = QColor("#FF0000")
    curFillColor = QColor("#F5C640")
    colorFilling = False
    curStrokeWeight = 10
    # 浮动条透明度
    curOpacityValue = 0.80

    def __init__(self, parent=None):
        super(FloatBar, self).__init__(parent)
        self.setupUi(self)

        self.cb_brush_shape.setIconSize(QSize(26, 26))

        stream = QtCore.QFile(":assets/style/float_bar_style.qss")
        stream.open(QtCore.QIODevice.ReadOnly)

        self.setStyleSheet(QtCore.QTextStream(stream).readAll())

        self.reset_opacity()
        self.init_ui()
        self.init_event()

    def init_event(self):
        self.tb_palette.clicked.connect(self.change_edge_color)
        self.tb_color_fill.clicked.connect(self.change_fill_color)
        self.cb_color_fill.clicked.connect(self.change_if_color_filling)
        self.sld_stroke_weight.valueChanged.connect(self.change_stroke_weight)
        self.tb_stroke_weight.clicked.connect(self.reset_stroke_weight)
        self.cb_brush_shape.currentIndexChanged.connect(self.change_brush_shape)

    def init_ui(self):
        pixmap = self.set_color()
        self.lbl_palette.setPixmap(pixmap)

        self.sld_stroke_weight.setValue(self.curStrokeWeight)
        self.sld_stroke_weight.setToolTip(str(self.curStrokeWeight))

        self.cb_brush_shape.setToolTip("绘制矩形")

    def enterEvent(self, a0: QtCore.QEvent) -> None:
        self.show_or_hide(a0)

    def leaveEvent(self, a0: QtCore.QEvent) -> None:
        self.show_or_hide(a0)

    def show_or_hide(self, status: QtCore.QEvent):
        if status.type() == QtCore.QEvent.Enter:
            while self.curOpacityValue < 1:
                self.curOpacityValue = round(self.curOpacityValue + 0.02, 2)
                time.sleep(0.01)
                self.reset_opacity()
        elif status.type() == QtCore.QEvent.Leave:
            while self.curOpacityValue > 0.02:
                self.curOpacityValue = round(self.curOpacityValue - 0.02, 2)
                time.sleep(0.01)
                self.reset_opacity()

    def reset_opacity(self):
        op1 = QtWidgets.QGraphicsOpacityEffect()
        op1.setOpacity(self.curOpacityValue)
        self.tb_palette.setGraphicsEffect(op1)

        op2 = QtWidgets.QGraphicsOpacityEffect()
        op2.setOpacity(self.curOpacityValue)
        self.tb_stroke_weight.setGraphicsEffect(op2)

        op3 = QtWidgets.QGraphicsOpacityEffect()
        op3.setOpacity(self.curOpacityValue)
        self.sld_stroke_weight.setGraphicsEffect(op3)

        op4 = QtWidgets.QGraphicsOpacityEffect()
        op4.setOpacity(self.curOpacityValue)
        self.setGraphicsEffect(op4)

        QCoreApplication.processEvents()
        # self.update()

    def change_edge_color(self):
        color = QColorDialog().getColor(parent=self, title="选择边界颜色")
        if color == 0:
            return
        self.curEdgeColor = color
        pixmap = self.set_color()
        self.lbl_palette.setPixmap(pixmap)

    def change_fill_color(self):
        color = QColorDialog().getColor(parent=self, title="选择填充颜色")
        if color == 0:
            return
        self.curFillColor = color
        pixmap = self.set_color()
        self.lbl_palette.setPixmap(pixmap)

    def change_if_color_filling(self):
        self.colorFilling = not self.colorFilling
        pixmap = self.set_color()
        self.lbl_palette.setPixmap(pixmap)

    def set_color(self):
        pixmap = QPixmap(80, 32)
        pixmap.fill(QColor("white"))
        painter = QPainter()
        painter.begin(pixmap)
        painter.setPen(QPen(QColor(self.curEdgeColor), 4))
        brush = QBrush(QColor(self.curFillColor)) if self.colorFilling else QBrush()
        painter.setBrush(brush)
        painter.drawRect(QRectF(2, 2, 76, 28))
        painter.end()
        self.lbl_palette.setToolTip(f"描边：{self.curEdgeColor.name()}，填充：{self.curFillColor.name()}")
        self.sgl_brush_color_changed[tuple].emit((self.curEdgeColor.name(), self.curFillColor.name()))
        return pixmap

    def change_brush_shape(self, event):
        if event == BrushShape.brRect.value:
            self.cb_brush_shape.setToolTip("绘制矩形")
            self.sgl_brush_shape_changed[int].emit(BrushShape.brRect.value)
        elif event == BrushShape.brCircle.value:
            self.cb_brush_shape.setToolTip("绘制圆形")
            self.sgl_brush_shape_changed[int].emit(BrushShape.brCircle.value)
        elif event == BrushShape.brStar.value:
            self.cb_brush_shape.setToolTip("绘制星形")
            self.sgl_brush_shape_changed[int].emit(BrushShape.brStar.value)
        elif event == BrushShape.brLine.value:
            self.cb_brush_shape.setToolTip("绘制直线")
            self.sgl_brush_shape_changed[int].emit(BrushShape.brLine.value)

    def change_stroke_weight(self, weight):
        self.curStrokeWeight = weight
        self.sld_stroke_weight.setToolTip(str(self.curStrokeWeight))

    def reset_stroke_weight(self):
        self.sld_stroke_weight.setValue(10)
