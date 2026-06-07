# coding:utf-8
import os
import subprocess

import numpy as np
from enum import Enum

import pyperclip
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QRect, QRectF, QSize, Qt, pyqtSignal, QLineF, QPoint
from PyQt5.QtGui import (QPainter, QPixmap, QColor, QBrush, QPolygon, QPolygonF,
                         QTextDocument, QIcon, QCursor, QPen)
from PyQt5.QtWidgets import (QGraphicsView, QRubberBand, QMenu, QAction)

from src.customGraphicsPathItem import CustomGraphicsPathItem
from src.myFloatBar import BrushShape
from src.myRichTextEditor import RichTextEditor


class imageViewerFlag(Enum):
    normal = 1011
    middle_button_painting = 1012
    left_button_painting = 1003
    capturing = 1014
    rubber_banding = 1015
    bezier_curve_editing = 1016
    bezier_node_moving = 1017
    bezier_handler_moving = 1018


class graphicsItemDataFlags(Enum):
    pixmap_item = 1021
    text_widget_item = 1022


class ImageViewer(QGraphicsView):
    status = imageViewerFlag.normal.value
    pre_status = imageViewerFlag.normal.value
    preItemsCount = 0
    prePosition = None
    curStrokeWeight = 0
    curEdgeColor = QColor("#FF0000")
    curFillColor = QColor("#F5C640")
    curBrushShape = 0
    colorFilling = False

    cur_bezier_curve_item = None
    cur_bezier_vertex = {}

    vertex_pen = QPen(QColor("black"))
    vertex_brush = QBrush()

    selected_vertex_pen = QPen(QColor("red"))
    selected_vertex_brush = QBrush(QColor("red"))

    bezier_node_movable = False
    bezier_handler_movable = False
    handler_type = 0
    bezier_path_item_names = []

    sgl_viewport_resize = pyqtSignal(int)
    sgl_item_increased = pyqtSignal(bool)

    # rubber_band = None

    def __init__(self, parent=None):
        super(ImageViewer, self).__init__(parent)
        self.zoomInTimes = 0
        self.maxZoomInTimes = 22

        self.setDragMode(self.ScrollHandDrag)  # 设置为鼠标左键拖动
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 设置为关闭垂直滚动条
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 设置为关闭水平滚动条

        self.init_ui()

    def init_ui(self):
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        pos = event.pos()
        item = self.itemAt(pos)
        if not item:
            return
        popMenu = QMenu()

        if item.data(graphicsItemDataFlags.pixmap_item.value):
            action1 = QAction(QIcon(QPixmap(":/assets/icon/copy_link.png")), "复制路径")
            action1.triggered.connect(lambda: self.copy_tree_item_data(item))
            popMenu.addAction(action1)

            action2 = QAction(QIcon(QPixmap(":/assets/icon/open_path.png")), "打开路径")
            action2.triggered.connect(lambda: self.open_tree_item_path(item))
            popMenu.addAction(action2)

        elif item.data(graphicsItemDataFlags.text_widget_item.value):
            action3 = QAction(QIcon(QPixmap(":/assets/icon/edit_text_widget.png")), "编辑")
            action3.triggered.connect(lambda: self.edit_text_widget(item))
            popMenu.addAction(action3)

            action4 = QAction(QIcon(QPixmap(":/assets/icon/move.png")), "移动")
            action4.triggered.connect(lambda: self.edit_text_widget(item))
            popMenu.addAction(action4)

            action5 = QAction(QIcon(QPixmap(":/assets/icon/resize.png")), "调整尺寸")
            action5.triggered.connect(lambda: self.edit_text_widget(item))
            popMenu.addAction(action5)

        popMenu.exec_(QCursor.pos())  # 执行之后菜单可以显示

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        super(ImageViewer, self).mousePressEvent(event)

        if self.status == imageViewerFlag.normal.value:
            if event.button() == Qt.MiddleButton:
                self.status = imageViewerFlag.middle_button_painting.value
                self.setDragMode(QGraphicsView.ScrollHandDrag)

        elif self.status == imageViewerFlag.left_button_painting.value:
            self.setDragMode(QGraphicsView.NoDrag)

        elif self.status == imageViewerFlag.rubber_banding.value:
            self.setDragMode(QGraphicsView.NoDrag)
            self.rubber_band.setGeometry(QRect(event.pos(), QSize()))
            self.rubber_band.show()

        elif self.status == imageViewerFlag.bezier_node_moving.value:
            if not event.button() == Qt.LeftButton:
                return
            if not self.cur_bezier_curve_item:
                return
            if not self.cur_bezier_curve_item.selected_node:
                return
            pos = event.pos()
            selected_node_pos = self.mapFromScene(self.cur_bezier_curve_item.selected_node[1])
            x1 = pos.x()
            y1 = pos.y()
            x2 = selected_node_pos.x()
            y2 = selected_node_pos.y()
            v = np.array([x2 - x1, y2 - y1])
            distance = np.linalg.norm(v)
            if distance < 12:
                self.bezier_node_movable = True

        elif self.status == imageViewerFlag.bezier_handler_moving.value:
            if not event.button() == Qt.LeftButton:
                return
            if not self.cur_bezier_curve_item:
                return
            if not self.cur_bezier_curve_item.selected_node:
                return
            pos = event.pos()
            self.find_handler(pos)
            self.bezier_handler_movable = True

        self.preItemsCount = len(self.scene().items())
        self.prePosition = event.pos()

    def find_handler(self, pos):
        x1 = pos.x()
        y1 = pos.y()
        for item in self.scene().items():
            data = item.data(0)
            if data and (type(data) is list):
                item_pos = self.mapFromScene(data[1])
                x2 = item_pos.x()
                y2 = item_pos.y()
                v = np.array([x2 - x1, y2 - y1])
                distance = np.linalg.norm(v)
                if distance < 12:
                    if data[0] == "pre_handler":
                        self.handler_type = 0
                        return
                    elif data[0] == "handler":
                        self.handler_type = 1
                        return

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        super(ImageViewer, self).mouseMoveEvent(event)
        if self.status == imageViewerFlag.rubber_banding.value:
            self.resize_rubber_band(self.prePosition, event.pos())

        elif self.status == imageViewerFlag.middle_button_painting.value \
                or self.status == imageViewerFlag.left_button_painting.value:
            self.mark(self.prePosition, event.pos())

        elif self.status == imageViewerFlag.bezier_node_moving.value:
            if self.bezier_node_movable:
                node_index = self.cur_bezier_curve_item.selected_node[0]
                pos = self.mapToScene(event.pos())
                self.cur_bezier_curve_item.move_node(node_index, pos)
                self.remove_bezier_vertex()
                self.add_bezier_vertex()
                self.update()

        elif self.status == imageViewerFlag.bezier_handler_moving.value:
            if self.bezier_handler_movable:
                node_index = self.cur_bezier_curve_item.selected_node[0]
                pos = self.mapToScene(event.pos())
                self.cur_bezier_curve_item.move_handler(node_index, self.handler_type, pos)
                self.remove_bezier_vertex()
                self.remove_bezier_handler()
                self.display_handlers(node_index)
                self.update()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        super(ImageViewer, self).mouseReleaseEvent(event)

        if self.status == imageViewerFlag.middle_button_painting.value:
            self.preItemsCount += 1
            self.sgl_item_increased[bool].emit(True)
            self.prePosition = None
            self.status = imageViewerFlag.normal.value
        elif self.status == imageViewerFlag.left_button_painting.value:
            self.preItemsCount += 1
            self.sgl_item_increased[bool].emit(True)
            self.prePosition = None
        elif self.status == imageViewerFlag.rubber_banding.value:
            if self.rubber_band and (not self.rubber_band.isHidden()):
                self.show_text_edit()
                self.rubber_band.hide()
                self.setDragMode(QGraphicsView.ScrollHandDrag)
                self.status = imageViewerFlag.normal.value
        elif self.status == imageViewerFlag.bezier_curve_editing.value:
            # 如果处于编辑贝塞尔曲线状态：
            #   左键:拖动视口、添加节点、选中节点
            #       如果鼠标从按下到释放期间移动，则是拖动视口
            #       如果鼠标点击时没有移动，且当前位置没有节点，则新建节点
            #       如果鼠标点击时没有移动，且当前位置有节点，则选中节点
            #   右键：删除节点、闭合曲线
            #       如果当前位置有节点，则删除节点
            #       如果当前位置没有节点，则闭合曲线
            end_pos = event.pos()
            start_pos = self.prePosition
            y_shift = abs(end_pos.y() - start_pos.y())
            x_shift = abs(end_pos.x() - start_pos.x())
            if event.button() == Qt.LeftButton:
                if (y_shift < 1) and (x_shift < 1):
                    pos = self.mapToScene(start_pos)

                    if not self.cur_bezier_curve_item:
                        pen = QPen(self.curEdgeColor, self.curStrokeWeight)
                        brush = QBrush(self.curFillColor) if self.colorFilling else QBrush()
                        self.cur_bezier_curve_item = CustomGraphicsPathItem(pos, pen, brush)
                        item_name = f"bezier_path_item_{str(len(self.bezier_path_item_names))}"
                        self.cur_bezier_curve_item.setData(0, item_name)
                        self.bezier_path_item_names.append(item_name)
                        self.scene().addItem(self.cur_bezier_curve_item)
                    else:
                        mouse_pos = event.pos()
                        selected_node_pos = self.mapFromScene(self.cur_bezier_curve_item.bezier_node_set[0])
                        x1 = mouse_pos.x()
                        y1 = mouse_pos.y()
                        x2 = selected_node_pos.x()
                        y2 = selected_node_pos.y()
                        v = np.array([x2 - x1, y2 - y1])
                        distance = np.linalg.norm(v)
                        if not distance > 10:
                            if len(self.cur_bezier_curve_item.bezier_node_set) > 2:
                                self.cur_bezier_curve_item.close_path()

                        node_index = self.cur_bezier_curve_item.collision_detection(pos)
                        if node_index == "none":
                            self.cur_bezier_curve_item.add_node(pos)
                        else:
                            self.select_bezier_vertex(node_index)
            elif event.button() == Qt.RightButton:
                if self.cur_bezier_curve_item:
                    pos = self.mapToScene(event.pos())
                    node_index = self.cur_bezier_curve_item.collision_detection(pos)
                    if node_index == "none":
                        if len(self.cur_bezier_curve_item.bezier_node_set) > 2:
                            self.cur_bezier_curve_item.close_path()
                    else:
                        self.cur_bezier_curve_item.remove_node(node_index)
                        item = self.cur_bezier_vertex[self.cur_bezier_curve_item][node_index]
                        self.scene().removeItem(item)
            if not self.cur_bezier_curve_item:
                return
            if self.cur_bezier_curve_item.bezier_node_set:
                if not (self.cur_bezier_curve_item in self.cur_bezier_vertex.keys()):
                    self.cur_bezier_vertex.update({self.cur_bezier_curve_item: []})
                self.remove_bezier_vertex()
                self.add_bezier_vertex()
        elif self.status == imageViewerFlag.bezier_node_moving.value:
            self.bezier_node_movable = False
        elif self.status == imageViewerFlag.bezier_handler_moving.value:
            self.bezier_handler_movable = False

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.status = imageViewerFlag.normal.value
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        elif event.key() == Qt.Key_Control:
            self.pre_status = self.status
            self.remove_bezier_handler()
            self.status = imageViewerFlag.bezier_node_moving.value
        elif event.key() == Qt.Key_Alt:
            self.pre_status = self.status
            self.status = imageViewerFlag.bezier_handler_moving.value

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == Qt.Key_Control:
            if self.status == imageViewerFlag.bezier_node_moving.value:
                self.status = self.pre_status
                self.pre_status = imageViewerFlag.normal.value
        elif event.key() == Qt.Key_Alt:
            if self.status == imageViewerFlag.bezier_handler_moving.value:
                self.status = self.pre_status
                self.pre_status = imageViewerFlag.normal.value

    def remove_current_bezier(self):
        for item in self.scene().items():
            if item.data(0) == self.bezier_path_item_names[-1]:
                self.scene().removeItem(item)
                del item
                self.update()

    def remove_bezier_vertex(self):
        for item in self.scene().items():
            if item.data(0) == "bezier_vertex":
                self.scene().removeItem(item)
                del item
        self.update()

    def add_bezier_vertex(self):
        for p in self.cur_bezier_curve_item.bezier_node_set:
            if p == self.cur_bezier_curve_item.selected_node[1]:
                pen = self.selected_vertex_pen
                brush = self.selected_vertex_brush
            else:
                pen = self.vertex_pen
                brush = self.vertex_brush
            rectF = self.mapToScene(self.mapFromScene(p).x() - 4, self.mapFromScene(p).y() - 4, 8, 8)
            rectF = rectF.boundingRect()
            item = self.scene().addEllipse(rectF, pen, brush)
            item.setCursor(Qt.CrossCursor)
            item.setData(0, "bezier_vertex")
            self.cur_bezier_vertex[self.cur_bezier_curve_item].append(item)
        self.update()

    def select_bezier_vertex(self, node_index):
        self.display_handlers(node_index)
        node = self.cur_bezier_curve_item.bezier_node_set[node_index]
        self.cur_bezier_curve_item.selected_node = [node_index, node]
        self.remove_bezier_vertex()
        self.add_bezier_vertex()
        self.remove_bezier_handler()
        self.display_handlers(node_index)

    def display_handlers(self, node_index):
        pen = QPen(QColor("black"))
        brush = QBrush(QColor("white"))
        if not len(self.cur_bezier_curve_item.bezier_node_set) > 1:
            return
        try:
            pre_handler = self.cur_bezier_curve_item.bezier_handler_set[node_index][0]
        except:
            pre_handler = None
        try:
            next_handler = self.cur_bezier_curve_item.bezier_handler_set[node_index][1]
        except:
            next_handler = None

        cur_node = self.cur_bezier_curve_item.bezier_node_set[node_index]
        if pre_handler:
            lineF1 = QLineF(cur_node, pre_handler)
            line1 = self.scene().addLine(lineF1)
            line1.setData(0, "bezier_handler_line")
            rectF1 = self.mapToScene(self.mapFromScene(pre_handler).x() - 3,
                                     self.mapFromScene(pre_handler).y() - 3, 6, 6)
            rectF1 = rectF1.boundingRect()
            point1 = self.scene().addEllipse(rectF1, pen, brush)
            point1.setData(0, ["pre_handler", pre_handler])

        if next_handler:
            if next_handler == "__end__":
                return
            lineF2 = QLineF(cur_node, next_handler)
            line2 = self.scene().addLine(lineF2)
            line2.setData(0, "bezier_handler_line")
            rectF2 = self.mapToScene(self.mapFromScene(next_handler).x() - 3,
                                     self.mapFromScene(next_handler).y() - 3, 6, 6)
            rectF2 = rectF2.boundingRect()
            point2 = self.scene().addEllipse(rectF2, pen, brush)
            point2.setData(0, ["handler", next_handler])

    def remove_bezier_handler(self):
        for item in self.scene().items():
            if (item.data(0) == "bezier_handler_line") or (type(item.data(0)) is list):
                self.scene().removeItem(item)
                del item

    # treeWidgetItem右键菜单复制文件路径功能
    @staticmethod
    def copy_tree_item_data(item):
        filename = item.data(graphicsItemDataFlags.pixmap_item.value)
        pyperclip.copy(os.path.normcase(filename))

    # treeWidgetItem右键菜单打开文件路径功能
    @staticmethod
    def open_tree_item_path(item):
        filename = item.data(graphicsItemDataFlags.pixmap_item.value)
        cmd = 'EXPLORER.EXE /SELECT,\"' + os.path.normcase(filename) + '\"'
        subprocess.Popen(cmd)

    def edit_text_widget(self, item):
        html = item.data(graphicsItemDataFlags.text_widget_item.value)
        self.show_text_edit(html)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoomIn()
        else:
            self.zoomOut()

    def zoomIn(self, viewAnchor=QGraphicsView.AnchorUnderMouse):
        if self.zoomInTimes < self.maxZoomInTimes:
            self.zoomInTimes += 1
            self.setTransformationAnchor(viewAnchor)

            self.scale(1.1, 1.1)

            # 还原 anchor
            self.setTransformationAnchor(self.AnchorUnderMouse)

    def zoomOut(self, viewAnchor=QGraphicsView.AnchorUnderMouse):
        if self.zoomInTimes > -5:
            self.zoomInTimes -= 1
            self.setTransformationAnchor(viewAnchor)

            self.scale(1 / 1.1, 1 / 1.1)

            # 还原 anchor
            self.setTransformationAnchor(self.AnchorUnderMouse)

    def mark(self, startPoint, endPoint):
        try:
            if startPoint and endPoint:

                startPointF = self.mapToScene(startPoint)
                endPointF = self.mapToScene(endPoint)
                while len(self.scene().items()) > self.preItemsCount:
                    self.scene().removeItem(self.scene().items()[0])
                if self.curBrushShape == BrushShape.brLine.value:
                    self.scene().addLine(QLineF(startPointF, endPointF),
                                         QtGui.QPen(self.curEdgeColor, self.curStrokeWeight))
                else:
                    rect = QtCore.QRectF(startPointF, endPointF)
                    pen = QtGui.QPen(self.curEdgeColor, self.curStrokeWeight)
                    brush = QBrush(self.curFillColor) if self.colorFilling else QBrush()
                    if self.curBrushShape == BrushShape.brRect.value:
                        self.scene().addRect(rect, pen, brush)
                    elif self.curBrushShape == BrushShape.brCircle.value:
                        self.scene().addEllipse(rect, pen, brush)
                    elif self.curBrushShape == BrushShape.brStar.value:
                        polygon = self.get_star(startPointF, endPointF)
                        self.scene().addPolygon(polygon, pen, brush)
                self.scene().update()
        except Exception as e:
            print(e)

    def resize_rubber_band(self, startPoint, endPoint):
        if startPoint and endPoint:
            self.rubber_band.setGeometry(QRect(startPoint, endPoint))

    def show_text_edit(self, html=None):
        rich_text_edit = RichTextEditor()
        rich_text_edit.sglPixmap.connect(self.render_html)
        rich_text_edit.show()
        if html:
            rich_text_edit.textEdit.setHtml(html)

    def render_html(self, html):
        geometry = self.rubber_band.geometry()
        raw_size = geometry.size()
        pixmap = QPixmap(raw_size)
        pixmap.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pixmap)
        document = QTextDocument()
        document.setHtml(html)
        document.setTextWidth(pixmap.width())
        document.drawContents(painter)
        painter.end()

        p_top_left = self.mapToScene(geometry.topLeft())
        p_bottom_right = self.mapToScene(geometry.bottomRight())
        rect = QRectF(p_top_left, p_bottom_right)
        target_size = rect.size()
        pixmap = pixmap.scaled(target_size.width(), target_size.height())

        pixmap_item = self.scene().addPixmap(pixmap)
        pixmap_item.setData(graphicsItemDataFlags.text_widget_item.value, html)

        pos = p_top_left
        pixmap_item.setPos(pos)

        self.preItemsCount += 1
        self.sgl_item_increased[bool].emit(True)

    @staticmethod
    def get_star(startPointF, endPointF):
        sx = startPointF.x()
        sy = startPointF.y()
        ex = endPointF.x()
        ey = endPointF.y()
        v = np.array([ex - sx, ey - sy])
        unit_vec = np.array([sx + 1, sy])
        vec_dot = np.dot(v, unit_vec)
        if np.linalg.norm(v) == 0:
            return
        arc_cos = np.arccos(vec_dot / (np.linalg.norm(v) * np.linalg.norm(unit_vec)))

        r = np.linalg.norm(v)
        in_r = r * np.cos(np.radians(72)) / np.cos(np.radians(36))

        points = []
        for i in range(5):
            points.append(QPoint(sx + r * np.cos(arc_cos + np.radians(i * 72)),
                                 sy + r * np.sin(arc_cos + np.radians(i * 72))))
            points.append(QPoint(sx + in_r * np.cos(arc_cos + np.radians(i * 72 + 36)),
                                 sy + in_r * np.sin(arc_cos + np.radians(i * 72 + 36))))
        polygon = QPolygon(points)
        polygon = (QPolygonF(polygon))
        return polygon

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        self.sgl_viewport_resize[int].emit(1)
