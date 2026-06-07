import sys

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QTextCursor, QTextBlockFormat, QBrush, QPixmap, QIcon
from PyQt5.QtWidgets import QFrame, QMenu, QColorDialog, QFileDialog

from src.richTextEditorConverted import Ui_frm_rich_text


class RichTextEditor(QFrame, Ui_frm_rich_text):
    sglPixmap = pyqtSignal(str)

    # 字体大小字典
    FONT_SIZE = {
        '42.0': '初号', '36.0': '小初',
        '26.0': '一号', '24.0': '小一',
        '22.0': '二号', '18.0': '小二',
        '16.0': '三号', '15.0': '小三',
        '14.0': '四号', '12.0': '小四',
        '10.5': '五号', '9.0': '小五',
        '7.5': '六号', '6.5': '小六',
        '6': '6', '7': '7',
        '8': '8', '9': '9',
        '10': '10', '11': '11',
        '12': '12', '14': '14',
        '16': '16', '18': '18',
        '20': '20', '22': '22',
        '24': '24', '26': '26',
        '28': '28', '36': '36',
        '48': '48', '60': '60',
        '72': '72', '96': '96',
    }
    recently_text_color = ['#000000', '#C00000', '#FFC000', '#FFFF00', '#92D050']  # 最近使用的字体颜色
    recently_text_shadow_color = ['#FFFFFF', '#C00000', '#FFC000', '#FFFF00', '#92D050']  # 最近使用的字体背景色

    current_text_color = None
    current_text_shadow_color = None

    rich_text_mode = False

    moveFlag = False
    movePosition = None

    def __init__(self):
        super(RichTextEditor, self).__init__()
        self.setupUi(self)
        self.init_ui()
        self.init_event()
        self.textEdit.setAcceptRichText(True)

    def init_ui(self):
        self.textBrowser.setHidden(True)
        self.update_recently_colors(color_type='text_color')
        self.update_recently_colors(color_type='text_shadow_color')

        self.setWindowFlag(Qt.FramelessWindowHint)
        stream = QtCore.QFile(":assets/style/rich_text_editor.qss")
        stream.open(QtCore.QIODevice.ReadOnly)

        self.setStyleSheet(QtCore.QTextStream(stream).readAll())

        [self.cb_font_size.addItem(self.FONT_SIZE[key], key) for key in self.FONT_SIZE.keys()]  # 添加选项
        self.cb_font_size.setCurrentText('四号')  # 默认四号

        self.tb_vtop.setEnabled(False)
        self.tb_vtop.setToolTip(self.tb_vtop.toolTip() + ":不可用")
        self.tb_vmid.setEnabled(False)
        self.tb_vmid.setToolTip(self.tb_vmid.toolTip() + ":不可用")
        self.tb_vbottom.setEnabled(False)
        self.tb_vbottom.setToolTip(self.tb_vbottom.toolTip() + ":不可用")
        # self.dsb_line_height.setEnabled(False)
        # self.dsb_line_height.setToolTip(self.dsb_line_height.toolTip() + ":不可用")
        # self.tb_reset_line_height.setEnabled(False)
        # self.tb_reset_line_height.setToolTip(self.tb_reset_line_height.toolTip() + ":不可用")

    def init_event(self):
        self.tb_close.clicked.connect(self.close_page)
        self.tb_bold.clicked.connect(lambda: self.set_text_format("bold"))
        self.tb_underline.clicked.connect(lambda: self.set_text_format("underline"))
        self.tb_italic.clicked.connect(lambda: self.set_text_format("italic"))
        self.textEdit.currentCharFormatChanged.connect(self.char_format_changed)
        self.tb_vtop.clicked.connect(lambda: self.set_v_alignment("top"))
        self.tb_vmid.clicked.connect(lambda: self.set_v_alignment("mid"))
        self.tb_vbottom.clicked.connect(lambda: self.set_v_alignment("bottom"))
        self.tb_hleft.clicked.connect(lambda: self.set_h_alignment("left"))
        self.tb_hmid.clicked.connect(lambda: self.set_h_alignment("mid"))
        self.tb_hright.clicked.connect(lambda: self.set_h_alignment("right"))
        self.textEdit.cursorPositionChanged.connect(self.block_alignment_changed)

        # 调整行高
        self.dsb_line_height.editingFinished.connect(self.change_line_height)
        self.tb_reset_line_height.clicked.connect(self.reset_line_height)
        self.textEdit.cursorPositionChanged.connect(self.cursor_position_changed)

        self.fcb_font_style.currentFontChanged.connect(self.set_font_name)
        self.cb_font_size.currentTextChanged.connect(self.set_font_size)
        self.cb_rich_text.clicked.connect(self.switch_rich_text_mode)
        self.tb_open.clicked.connect(self.open_doc)
        self.tb_save.clicked.connect(self.save_doc)

    def init_font(self):
        pass

    def close_page(self):
        text = self.render_text_widget()
        self.sglPixmap[str].emit(text)
        self.close()

    def open_doc(self):
        filename, selected_filter = QFileDialog().getOpenFileName(self, "打开文档", "",
                                                                  "文本(*.txt *.csv);;Markdown(*.md)")

        if not filename:
            return

        with open(filename, "r", encoding="utf-8") as file:
            text = file.read()
        self.textEdit.setPlainText(text)

    def save_doc(self):
        if self.textBrowser.isHidden():
            text_widget = self.textEdit
        else:
            text_widget = self.textBrowser

        filename, selected_filter = QFileDialog().getSaveFileName(self, "打开文档", "",
                                                                  "文本(*.txt *.csv);;网页(*.html);;Markdown(*.md)")
        if not filename:
            return

        if selected_filter == "文本(*.txt *.csv)":
            text = text_widget.toPlainText()
        elif selected_filter == "网页(*.html)":
            text = text_widget.toHtml()
        elif selected_filter == "Markdown(*.md)":
            text = text_widget.toMarkdown()
        else:
            text = None

        if not text:
            return

        with open(filename, "w", encoding="utf-8") as file:
            file.write(text)

    def render_text_widget(self):
        if not self.textBrowser.isHidden():
            text_widget = self.textBrowser
        else:
            text_widget = self.textEdit

        text = text_widget.toHtml()
        return text

    def set_font_name(self, event):
        self.set_text_format("font_name", event)

    def set_font_size(self, event):
        self.set_text_format("font_size", event)

    def set_text_format(self, t_format, param=None):
        text_cursor = self.textEdit.textCursor()
        current_cursor_position = text_cursor.position()
        if text_cursor.hasSelection():
            move_distance = len(text_cursor.selectedText())
            if current_cursor_position == text_cursor.selectionStart():
                text_cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, move_distance)
                text_cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, move_distance)
        else:
            text_cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.MoveAnchor)
            text_cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
        # self.textEdit.setTextCursor(text_cursor)
        char_format = text_cursor.charFormat()
        font = char_format.font()
        if t_format == "bold":
            font.setBold(not font.bold())
        elif t_format == "underline":
            font.setUnderline(not font.underline())
        elif t_format == "italic":
            font.setItalic(not font.italic())
        elif t_format == "font_name":
            if param:
                font = param
        elif t_format == "font_size":
            if param:
                font_size = [k for k, v in self.FONT_SIZE.items() if v == param][0]
                font_size = int(float(font_size))
                font.setPointSize(font_size)
                self.change_line_height(font_size * 1.5)
                self.dsb_line_height.setValue(font_size * 1.5)
        elif t_format == "text_color":
            if param:
                char_format.setForeground(QBrush(QColor(param)))
        elif t_format == "text_shadow_color":
            if param:
                char_format.setBackground(QBrush(QColor(param)))
        char_format.setFont(font)
        text_cursor.mergeCharFormat(char_format)
        text_cursor.setPosition(current_cursor_position)
        self.textEdit.setTextCursor(text_cursor)

    def change_line_height(self, height=None):
        if not height:
            height = self.dsb_line_height.value()
        text_cursor = self.textEdit.textCursor()
        block = text_cursor.block()
        block_format = block.blockFormat()
        block_format.setLineHeight(height, QTextBlockFormat.FixedHeight)
        text_cursor.setBlockFormat(block_format)

    def reset_line_height(self):
        text_cursor = self.textEdit.textCursor()
        block = text_cursor.block()
        block_format = block.blockFormat()

        text_format = block.charFormat()
        height = text_format.font().pointSize()
        block_format.setLineHeight(1, QTextBlockFormat.SingleHeight)

        self.dsb_line_height.setValue(block_format.lineHeight())

        text_cursor.setBlockFormat(block_format)

    def set_h_alignment(self, h_align):
        text_cursor = self.textEdit.textCursor()
        block = text_cursor.block()
        block_format = block.blockFormat()
        if h_align == "left":
            block_format.setAlignment(Qt.AlignLeft)
        elif h_align == "mid":
            block_format.setAlignment(Qt.AlignHCenter)
        elif h_align == "right":
            block_format.setAlignment(Qt.AlignRight)
        text_cursor.setBlockFormat(block_format)
        self.block_alignment_changed()

    def set_v_alignment(self, v_align):
        text_cursor = self.textEdit.textCursor()
        block = text_cursor.block()
        block_format = block.blockFormat()
        if v_align == "top":
            block_format.setAlignment(Qt.AlignTop)
        elif v_align == "mid":
            block_format.setAlignment(Qt.AlignVCenter)
        elif v_align == "bottom":
            block_format.setAlignment(Qt.AlignBottom)
        text_cursor.setBlockFormat(block_format)
        self.block_alignment_changed()

    def char_format_changed(self, char_format):
        font = char_format.font()
        self.tb_bold.setChecked(font.bold())
        self.tb_italic.setChecked(font.italic())
        self.tb_underline.setChecked(font.underline())

        self.fcb_font_style.blockSignals(True)
        self.fcb_font_style.setCurrentFont(font)
        self.fcb_font_style.blockSignals(False)

        # 设置字号
        font_size = char_format.fontPointSize()
        if font_size:
            font_size_text = [v for k, v in self.FONT_SIZE.items() if float(k) == font_size][0]
            self.cb_font_size.blockSignals(True)
            self.cb_font_size.setCurrentText(str(font_size_text))
            self.cb_font_size.blockSignals(False)

    def cursor_position_changed(self):
        text_cursor = self.textEdit.textCursor()
        block = text_cursor.block()
        block_format = block.blockFormat()
        text_format = block.charFormat()
        height = text_format.font().pointSize()
        if not block_format.lineHeightType() == QTextBlockFormat.SingleHeight:
            height = block_format.lineHeight()

        self.dsb_line_height.blockSignals(True)
        self.dsb_line_height.setValue(height)
        self.dsb_line_height.blockSignals(False)

    def block_alignment_changed(self):
        text_cursor = self.textEdit.textCursor()
        block = text_cursor.block()
        alignment = block.blockFormat().alignment()
        self.tb_hleft.setChecked(alignment == Qt.AlignLeft)
        self.tb_hmid.setChecked(alignment == Qt.AlignHCenter)
        self.tb_hright.setChecked(alignment == Qt.AlignRight)

    def update_recently_colors(self, color_type):
        """ 更新最近使用颜色 """
        if color_type == 'text_color':
            # 更新最近使用字体色
            colors = self.recently_text_color
            color_button = self.pb_foreground
            button_style = """
                border:1px solid black;
                border-radius:4px;
                text-align:center;
                background-color:white;
            """
            if colors:
                button_style += "color:{};".format(colors[0])
        elif color_type == 'text_shadow_color':
            # 更新最近使用字体背景色
            colors = self.recently_text_shadow_color
            color_button = self.pb_background
            button_style = """
                border:1px solid black;
                border-radius:4px;
                text-align:center;
            """
            if colors:
                button_style += "background-color:{}".format(colors[0])
        else:
            return
        old_menu = color_button.menu()
        if old_menu:
            old_menu.deleteLater()  # 删除原按钮
        menu = QMenu()
        for color_item in colors:
            pixmap = QPixmap(20, 20)
            pixmap.fill(QColor(color_item))
            icon = QIcon(pixmap)
            action = menu.addAction(icon, color_item)
            action.triggered.connect(lambda: self.change_current_color(color_type))
        # 添加更多选项
        more_action = menu.addAction(QIcon(':assets/icon/more.png'), '更多颜色')
        more_action.triggered.connect(lambda: self.select_more_color(color_type))
        color_button.setStyleSheet(button_style)
        color_button.setMenu(menu)

    def select_more_color(self, color_type):
        """ 选择更多的颜色 """
        color = QColorDialog.getColor(parent=self, title='选择颜色')  # 不选默认为黑色
        color_str = color.name()
        # 改变对应颜色情况
        self.set_current_color(color_str.upper(), color_type)

    def change_current_color(self, color_type):
        """ 改变当前字体或字体背景的颜色 """
        action = self.sender()
        color = action.text()
        self.set_current_color(color, color_type)

    def set_current_color(self, color, color_type):

        if color_type == 'text_color':
            colors = self.recently_text_color
        elif color_type == 'text_shadow_color':
            colors = self.recently_text_shadow_color
        else:
            return
        if color in colors:
            color_index = colors.index(color)
            colors.insert(0, colors.pop(color_index))  # 将颜色插入到起始
        else:
            # 将颜色第一个替换掉
            colors[0] = color
        # 更新当前颜色
        self.update_recently_colors(color_type)

        self.set_text_format(color_type, colors[0])

    def switch_rich_text_mode(self):
        mode = not self.rich_text_mode
        if mode:
            self.textEdit.textChanged.connect(self.display_markdown)
        else:
            self.textEdit.textChanged.disconnect(self.display_markdown)
        self.textBrowser.setHidden(not mode)
        self.display_markdown()
        self.rich_text_mode = mode

    def display_markdown(self):
        text = self.textEdit.toHtml()
        self.textBrowser.setMarkdown(text)

    def mousePressEvent(self, event):  # 鼠标左键按下时获取鼠标坐标,按下右键取消
        if event.button() == Qt.LeftButton:
            self.moveFlag = True
            self.movePosition = event.globalPos() - self.pos()
            event.accept()
        elif event.button() == Qt.RightButton:
            self.moveFlag = False

    def mouseMoveEvent(self, QMouseEvent):  # 鼠标在按下左键的情况下移动时,根据坐标移动界面
        if Qt.LeftButton and self.moveFlag:
            self.move(QMouseEvent.globalPos() - self.movePosition)
            QMouseEvent.accept()

    def mouseReleaseEvent(self, QMouseEvent):  # 鼠标按键释放时,取消移动
        self.moveFlag = False


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    auth_page = RichTextEditor()
    auth_page.show()

    sys.exit(app.exec_())
