import numpy as np
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainterPath, QColor, QBrush, QPen
from PyQt5.QtWidgets import QGraphicsPathItem


class CustomGraphicsPathItem(QGraphicsPathItem):

    def __init__(self, pos: QPointF, pen: QPen = None, brush: QBrush = None):
        self.is_closed = False
        self.bezier_node_set = []
        self.bezier_handler_set = []
        self.selected_node = []

        super(CustomGraphicsPathItem, self).__init__()
        self.add_node(pos)

        if pen:
            self.setPen(pen)
        if brush:
            self.setBrush(brush)

    def draw_path(self, node_list, handler_list):
        start_end_x = (node_list[0].x() + node_list[-1].x()) / 2
        start_end_y = (node_list[0].y() + node_list[-1].y()) / 2
        start_end = QPointF(start_end_x, start_end_y)

        painter_path = QPainterPath()
        if not self.is_closed:
            for i in range(len(node_list)):
                if i == 0:
                    painter_path.moveTo(node_list[0])
                    if len(handler_list) == 0:
                        handler_list = [["__start__", "__end__"]]
                else:
                    mid_point_x = (node_list[i].x() + node_list[i - 1].x()) / 2
                    mid_point_y = (node_list[i].y() + node_list[i - 1].y()) / 2
                    mid_point = QPointF(mid_point_x, mid_point_y)
                    try:
                        handler1 = handler_list[i - 1][1]
                        if handler1 == "__end__":
                            raise Exception("this is the end node")
                    except Exception as e:
                        if str(e) == "this is the end node":
                            handler_list[i - 1][1] = mid_point
                        else:
                            handler_list[i - 1].append(mid_point)
                        handler1 = mid_point
                    try:
                        handler2 = handler_list[i][0]
                        if handler2 == "__start__":
                            raise Exception("this is the start end")
                    except Exception as e:
                        handler2 = mid_point
                        handler_list.append([handler2, "__end__"])
                    painter_path.cubicTo(handler1, handler2, node_list[i])

        else:
            painter_path.closeSubpath()
            if not handler_list:
                self.is_closed = False
                self.bezier_node_set = node_list
                self.bezier_handler_set = handler_list
                self.draw_path(self.bezier_node_set, self.bezier_handler_set)
                return
            if handler_list[-1][1] == "__end__":
                handler_list[-1][1] = start_end

            dx = node_list[0].x()
            dy = node_list[0].y()
            for i in range(len(node_list)):
                if i == 0:
                    pass
                elif i == 1:
                    handler1 = QPointF(handler_list[0][1].x() - dx, handler_list[0][1].y() - dy)
                    handler2 = QPointF(handler_list[1][0].x() - dx, handler_list[1][0].y() - dy)
                    pointF = QPointF(node_list[1].x() - dx, node_list[1].y() - dy)
                    painter_path.cubicTo(handler1, handler2, pointF)
                    painter_path.translate(dx, dy)
                elif i == len(node_list) - 1:
                    handler1 = handler_list[i - 1][1]
                    handler2 = handler_list[i][0]
                    pointF = node_list[i]
                    painter_path.cubicTo(handler1, handler2, pointF)

                    handler3 = handler_list[i][1]
                    handler4 = handler_list[0][0]
                    pointF2 = node_list[0]
                    painter_path.cubicTo(handler3, handler4, pointF2)
                else:
                    handler1 = handler_list[i - 1][1]
                    handler2 = handler_list[i][0]
                    pointF = node_list[i]
                    painter_path.cubicTo(handler1, handler2, pointF)

        if handler_list[0][0] == "__start__":
            handler_list[0][0] = start_end

        painter_path.setFillRule(Qt.WindingFill)

        self.setPath(painter_path)
        self.bezier_handler_set = handler_list

    def add_node(self, pos: QPointF):
        if not self.is_closed:
            self.bezier_node_set.append(pos)
            self.draw_path(self.bezier_node_set, self.bezier_handler_set)
            index_ = len(self.bezier_node_set) - 1
            self.selected_node = [index_, self.bezier_node_set[index_]]

    def remove_node(self, node_index: int):
        if len(self.bezier_node_set) > 1:
            if node_index == 0:
                pre_node = self.bezier_node_set[-1]
                next_node = self.bezier_node_set[node_index + 1]
            elif node_index == len(self.bezier_node_set) - 1:
                pre_node = self.bezier_node_set[node_index - 1]
                next_node = self.bezier_node_set[0]
            else:
                pre_node = self.bezier_node_set[node_index - 1]
                next_node = self.bezier_node_set[node_index + 1]
            start_end_x = (pre_node.x() + next_node.x()) / 2
            start_end_y = (pre_node.y() + next_node.y()) / 2
            start_end = QPointF(start_end_x, start_end_y)

            if node_index == 0:
                self.bezier_handler_set[-1][1] = start_end
                self.bezier_handler_set[node_index + 1][0] = start_end
            elif node_index == len(self.bezier_node_set) - 1:
                self.bezier_handler_set[node_index - 1][1] = start_end
                self.bezier_handler_set[0][0] = start_end
            else:
                self.bezier_handler_set[node_index - 1][1] = start_end
                self.bezier_handler_set[node_index + 1][0] = start_end

            self.bezier_node_set.pop(node_index)
            self.bezier_handler_set.pop(node_index)

            if len(self.bezier_node_set) == 1:
                self.bezier_handler_set = []

            self.draw_path(self.bezier_node_set, self.bezier_handler_set)

    def move_node(self, node_index: int, new_pos: QPointF):
        self.bezier_node_set[node_index] = new_pos
        self.draw_path(self.bezier_node_set, self.bezier_handler_set)
        self.selected_node = [node_index, self.bezier_node_set[node_index]]

    def move_handler(self, node_index: int, direction: int, new_pos: QPointF):
        try:
            self.bezier_handler_set[node_index][direction] = new_pos
            self.draw_path(self.bezier_node_set, self.bezier_handler_set)
            self.selected_node = [node_index, self.bezier_node_set[node_index]]
        except Exception as e:
            print(str(e))

    def collision_detection(self, pos: QPointF):
        sx = pos.x()
        sy = pos.y()
        min_dist = None
        node_set = enumerate(self.bezier_node_set)
        for node in node_set:
            nx = node[1].x()
            ny = node[1].y()
            v = np.array([nx - sx, ny - sy])
            distance = np.linalg.norm(v)
            if not min_dist:
                min_dist = (node[0], distance)
            if distance < min_dist[1]:
                min_dist = (node[0], distance)
        if min_dist[1] < 100:
            return min_dist[0]
        else:
            return "none"

    def close_path(self):
        if not self.is_closed:
            self.is_closed = True
            # start_pos = self.bezier_node_set[0]
            # self.bezier_node_set.append(start_pos)
            self.draw_path(self.bezier_node_set, self.bezier_handler_set)
