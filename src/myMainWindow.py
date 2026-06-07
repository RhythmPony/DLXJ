import sqlite3
import subprocess
from enum import Enum
from multiprocessing import Pool, Manager
from threading import Thread

import pyperclip
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QDir, QFileInfo, QVariant, QCoreApplication, QUrl
from PyQt5.QtGui import QIcon, QColor, QCursor, QDesktopServices
from PyQt5.QtWidgets import (QMessageBox, QMainWindow, QTreeWidgetItem, QStatusBar, QMenu, QAction,
                             QProgressDialog, QLineEdit, QGraphicsView, QFileDialog, QButtonGroup, QRadioButton,
                             QVBoxLayout)

from src.DLXJMainWindowConverted import Ui_MainWindow
from src.myBezierEditor import BezierEditWidget
from src.mySettingPage import SettingPage
from src.screenshot import CaptureScreen
from src.myFloatBar import FloatBar
from src.pluginLoader import LoadPlugins
from src.utils import *
from src.imageViewer import ImageViewer, imageViewerFlag, graphicsItemDataFlags
from src.databaseTemplate import init_database_with_template


class ExportDocx(Thread):
    def __init__(self):
        super().__init__()

    def run(self) -> None:
        pool_num = len(self.sql_sentences) if 0 < len(self.sql_sentences) < os.cpu_count() else None
        with Pool(pool_num) as p:
            # Pool.map只能传字符串数组参数，子进程有多个参数应该使用starmap
            res = p.starmap_async(write_docx, self.args)
            print(res.get())
            self.q.put("_process_total_end")

    def init_params(self, sql_sentences, args, q):
        self.sql_sentences = sql_sentences
        self.args = args
        self.q = q


class TreeItemType(Enum):
    tvTopItem = 1001
    tvGroupItem = 1002
    tvImageItem = 1003


class UiMainWindow(QMainWindow, Ui_MainWindow):
    treeItemFlags = (Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsAutoTristate)
    treeItemPreviousText = None
    db_name = None
    DATABASE = None
    CURSOR = None
    COUNT_INIT_ITEMS = 0
    COUNT_ITEMS_IN_SCENE = 0
    UNDO_LIST = []
    REDO_LIST = []

    def __init__(self, parent=None):
        super(UiMainWindow, self).__init__(parent)

        self.gv_main_viewport = ImageViewer()
        self.gv_main_viewport.sgl_viewport_resize.connect(self.relocate_bar)
        self.gv_main_viewport.sgl_item_increased.connect(self.scene_item_increased)

        # 初始化状态栏
        self.statusBar = QStatusBar()
        super(QStatusBar, self.statusBar).__init__()

        self.setupUi(self)
        self.init_UI()

        self.bar = FloatBar(self.centralwidget)
        self.bar.setMouseTracking(True)
        self.bar.sld_stroke_weight.valueChanged.connect(self.update_stroke_weight)
        self.bar.cb_color_fill.clicked.connect(self.change_color_filling)
        self.bar.sgl_brush_color_changed.connect(self.update_brush_weight)
        self.bar.sgl_brush_shape_changed.connect(self.update_brush_shape)
        self.bar.tb_draw_text.clicked.connect(self.draw_text)
        self.bar.tb_bezier_curve.clicked.connect(self.draw_bezier_curve)
        self.update_stroke_weight(self.bar.sld_stroke_weight.value())

        stream = QtCore.QFile(":assets/style/main_window.qss")
        stream.open(QtCore.QIODevice.ReadOnly)
        self.setStyleSheet(QtCore.QTextStream(stream).readAll())

        self.showMaximized()

    def init_UI(self):

        self.tv_work_path_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tv_work_path_tree.customContextMenuRequested.connect(self.treeWidgetItem_fun)

        date = QtCore.QDate().currentDate()
        self.dateEdit.setDate(date)

        # 初始化主视口场景
        main_viewport_scene = QtWidgets.QGraphicsScene()
        self.gv_main_viewport.setScene(main_viewport_scene)
        self.hl_main_viewport.addWidget(self.gv_main_viewport)
        # 初始化预览窗口1场景
        tb1_preview_scene = QtWidgets.QGraphicsScene()
        self.gv_tb1.setScene(tb1_preview_scene)

        # 初始化预览窗口2场景
        tb2_preview_scene = QtWidgets.QGraphicsScene()
        self.gv_tab2.setScene(tb2_preview_scene)

        self.init_actions()
        self.init_tree()
        self.connect_events()
        self.init_operate_pad()

        self.action_undo.setEnabled(False)
        self.action_redo.setEnabled(False)

        self.set_line_placeholder()
        self.set_date_placeholder()

    def set_line_placeholder(self):
        holder1 = get_option("ui", "line_placeholder1", "none")
        holder2 = get_option("ui", "line_placeholder2", "none")
        holder3 = get_option("ui", "line_placeholder3", "none")
        holder4 = get_option("ui", "line_placeholder4", "none")
        holder5 = get_option("ui", "line_placeholder5", "none")
        if (not holder1) or (holder1 == "none"):
            self.lineEdit.setPlaceholderText("")
        else:
            self.lineEdit.setPlaceholderText(holder1)
        if (not holder2) or (holder2 == "none"):
            self.lineEdit_2.setPlaceholderText("")
        else:
            self.lineEdit_2.setPlaceholderText(holder2)
        if (not holder3) or (holder3 == "none"):
            self.lineEdit_3.setPlaceholderText("")
        else:
            self.lineEdit_3.setPlaceholderText(holder3)
        if (not holder4) or (holder4 == "none"):
            self.lineEdit_4.setPlaceholderText("")
        else:
            self.lineEdit_4.setPlaceholderText(holder4)
        if (not holder5) or (holder5 == "none"):
            self.lineEdit_5.setPlaceholderText("")
        else:
            self.lineEdit_5.setPlaceholderText(holder5)

    def set_date_placeholder(self):
        try:
            date_config = get_option("ui", "default_date", "today")
            if date_config == "today":
                date = QtCore.QDate().currentDate()
            else:
                if ' ' in date_config:
                    y, m, d = tuple(date_config.split(' '))
                elif '-' in date_config:
                    y, m, d = tuple(date_config.split('-'))
                elif '/' in date_config:
                    y, m, d = tuple(date_config.split('/'))
                else:
                    y, m, d = (None, None, None)
                date = QtCore.QDate(int(y), int(m), int(d))
        except Exception as e:
            logging.warning(str(e))
            date = QtCore.QDate().currentDate()
        self.dateEdit.setDate(date)

    def relocate_bar(self):
        x = ((self.gv_main_viewport.pos().x() * 2) + self.gv_main_viewport.size().width()
             - self.bar.size().width()) / 2 + self.gv_main_viewport.pos().x()
        y = self.gv_main_viewport.pos().y() + self.gv_main_viewport.size().height() - self.bar.size().height()
        self.bar.move(x, y)

    def connect_events(self):
        self.action_open.triggered.connect(self.act_open_dir)
        self.action_link_db.triggered.connect(self.connect_database)
        self.action_close_db.triggered.connect(self.close_database)
        self.action_export_docx.triggered.connect(self.export_docx)
        self.action_edit_db.triggered.connect(self.show_db_reader)
        self.action_paint.triggered.connect(self.start_paint)
        self.action_free_clip.triggered.connect(self.free_screenshot)
        self.action_clip.triggered.connect(self.capture_current_viewport)
        self.action_undo.triggered.connect(self.undo)
        self.action_redo.triggered.connect(self.redo)
        self.action_previous.triggered.connect(self.prev_item)
        self.action_next.triggered.connect(self.next_item)
        self.action_export_xlsx.triggered.connect(self.__export_xlsx)
        self.action_options.triggered.connect(self.open_settings_page)
        self.action_about.triggered.connect(self.open_help_url)

        self.tb_reload_option.clicked.connect(self.init_operate_pad)
        self.tb_reload_work_path.clicked.connect(lambda: self.refresh_dir(self.lbl_work_path.text()))
        self.tb_refresh_photo.clicked.connect(self.refresh_photo)
        self.tb_open.clicked.connect(self.act_open_dir)
        self.pb_commit_Db.clicked.connect(self.on_btn_commit_clicked)
        self.tb_clear_tab1.clicked.connect(self.clear_current_tab)
        self.tb_clear_tb2.clicked.connect(self.clear_current_tab)
        self.tv_work_path_tree.itemChanged.connect(self.on_tv_work_path_tree_item_changed)
        self.cb_cb1.currentTextChanged.connect(self.__change_screenshot_name)
        self.cb_cb2.currentTextChanged.connect(self.__change_screenshot_name)

    # 初始化动作
    def init_actions(self):

        self.action_close_db.setEnabled(False)
        self.action_export_docx.setEnabled(False)
        self.action_export_xlsx.setEnabled(False)
        self.pb_commit_Db.setEnabled(False)

    def open_settings_page(self):
        self.setting_page = SettingPage()
        self.setting_page.setWindowModality(Qt.WindowModal)
        self.setting_page.show()
        self.setting_page.sgl_config_changed.connect(self.on_config_changed)

    def on_config_changed(self, event):
        if event == "__config_changed__":
            self.init_operate_pad()
            self.set_line_placeholder()
            self.set_date_placeholder()

    def update_stroke_weight(self, event):
        self.gv_main_viewport.curStrokeWeight = event

    def change_color_filling(self):
        self.gv_main_viewport.colorFilling = not self.gv_main_viewport.colorFilling

    def update_brush_weight(self, event):
        self.gv_main_viewport.curEdgeColor = QColor(event[0])
        self.gv_main_viewport.curFillColor = QColor(event[1])

    def update_brush_shape(self, event):
        self.gv_main_viewport.curBrushShape = event

    def draw_text(self):
        if not self.gv_main_viewport.status == imageViewerFlag.capturing.value:
            self.gv_main_viewport.status = imageViewerFlag.rubber_banding.value
            self.gv_main_viewport.setFocus(Qt.OtherFocusReason)

    def draw_bezier_curve(self):
        if not self.gv_main_viewport.status == imageViewerFlag.capturing.value:
            self.gv_main_viewport.status = imageViewerFlag.bezier_curve_editing.value
            self.gv_main_viewport.setFocus(Qt.OtherFocusReason)

        self.bezier_edit = BezierEditWidget(self)
        self.bezier_edit.hl_main.addWidget(self.gv_main_viewport)
        self.bezier_edit.setWindowModality(Qt.WindowModal)
        self.bezier_edit.show()
        self.bezier_edit.sgl_save.connect(self.bezier_edit_saved)
        self.bezier_edit.sgl_cancel.connect(self.bezier_edit_canceled)

    def bezier_edit_saved(self, event):
        if event == "completed":
            self.hl_main_viewport.addWidget(self.gv_main_viewport)
            self.gv_main_viewport.status = imageViewerFlag.normal.value
            self.gv_main_viewport.remove_bezier_vertex()
            self.gv_main_viewport.remove_bezier_handler()
            self.gv_main_viewport.cur_bezier_curve_item = None
            self.gv_main_viewport.preItemsCount += 1
            self.scene_item_increased(True)

    def scene_item_increased(self, b):
        if b:
            self.action_redo.setEnabled(False)
            self.action_undo.setEnabled(True)
            self.UNDO_LIST = []
            self.REDO_LIST = []

    def bezier_edit_canceled(self, event):
        if event == "canceled":
            self.hl_main_viewport.addWidget(self.gv_main_viewport)
            self.gv_main_viewport.status = imageViewerFlag.normal.value
            self.gv_main_viewport.remove_bezier_vertex()
            self.gv_main_viewport.remove_bezier_handler()
            self.gv_main_viewport.remove_current_bezier()
            self.gv_main_viewport.status = imageViewerFlag.normal.value

    # 根据照片名自动填写属性面板
    def __auto_fill(self, filename: str):
        auto_fill_func = LoadPlugins("autoFill")
        autoFill = auto_fill_func.plugin_source.load_plugin("autoFill")

        texts = autoFill.auto_fill(filename)
        if not len(texts):
            return
        if not self.lineEdit.placeholderText():
            self.lineEdit.setText(texts[0])
        if not self.lineEdit_2.placeholderText():
            self.lineEdit_2.setText(texts[1])
        if not self.lineEdit_3.placeholderText():
            self.lineEdit_3.setText(texts[2])
        if not self.lineEdit_4.placeholderText():
            self.lineEdit_4.setText(texts[3])
        if not self.lineEdit_5.placeholderText():
            self.lineEdit_5.setText(texts[4])

    # 创建treeWidgetItem右键菜单
    def treeWidgetItem_fun(self, pos):
        item = self.tv_work_path_tree.itemAt(pos)

        if item:  # 判断菜单是否为空
            popMenu = QMenu()
            action1 = QAction(QIcon(QPixmap(":/assets/icon/rename.png")), "重命名")
            action1.triggered.connect(lambda: self.rename_tree_item(pos))
            popMenu.addAction(action1)

            action2 = QAction(QIcon(QPixmap(":/assets/icon/copy_text.png")), "复制文本")
            action2.triggered.connect(lambda: self.copy_tree_item_text(pos))
            popMenu.addAction(action2)

            action3 = QAction(QIcon(QPixmap(":/assets/icon/copy_link.png")), "复制路径")
            action3.triggered.connect(lambda: self.copy_tree_item_data(pos))
            popMenu.addAction(action3)

            action4 = QAction(QIcon(QPixmap(":/assets/icon/open_path.png")), "打开路径")
            action4.triggered.connect(lambda: self.open_tree_item_path(pos))
            popMenu.addAction(action4)

            popMenu.exec_(QCursor.pos())  # 执行之后菜单可以显示

    # treeWidgetItem右键菜单重命名功能
    def rename_tree_item(self, event):
        current_item = self.tv_work_path_tree.itemAt(event)
        self.treeItemPreviousText = self.tv_work_path_tree.itemAt(event).text(0)
        current_item.setFlags(self.treeItemFlags | Qt.ItemIsEditable)
        self.tv_work_path_tree.editItem(current_item)

    # treeWidgetItem右键菜单复制文件名功能
    def copy_tree_item_text(self, event):
        filename = self.tv_work_path_tree.itemAt(event).text(0)
        pyperclip.copy(filename)

    # treeWidgetItem右键菜单复制文件路径功能
    def copy_tree_item_data(self, event):
        filename = self.tv_work_path_tree.itemAt(event).data(0, Qt.UserRole)
        pyperclip.copy(filename)

    # treeWidgetItem右键菜单打开文件路径功能
    def open_tree_item_path(self, event):
        filename = self.tv_work_path_tree.itemAt(event).data(0, Qt.UserRole)
        cmd = 'EXPLORER.EXE /SELECT,\"' + os.path.normcase(filename) + '\"'
        subprocess.Popen(cmd)

    def on_tv_work_path_tree_item_changed(self, event: QTreeWidgetItem):
        if not self.treeItemPreviousText:
            return
        treeItemNowText = event.text(0)
        treeItemPreviousData = event.data(0, Qt.UserRole)
        if self.treeItemPreviousText != treeItemNowText:
            try:
                data = treeItemPreviousData.replace(self.treeItemPreviousText, treeItemNowText)
                event.setData(0, Qt.UserRole, data)
                event.setToolTip(0, data)
                if os.path.exists(treeItemPreviousData):
                    os.rename(treeItemPreviousData, os.path.normcase(data))
                self.treeItemPreviousText = None
                event.setFlags(self.treeItemFlags)
            except Exception as e:
                logging.warning(str(e))

    def init_operate_pad(self):
        """
        初始化操作面板
        :return:None
        """
        try:
            from base import BASE_DIR
            options_dir = get_option("sys", "customizable_option", "")
            options = read_options(options_dir)
            if options == -1:
                raise Exception('缺陷设置初始化失败')

            for k in options.keys():
                if 'cb1_' in k:
                    title = re.search(r'(?<=_)\w*(?=])', k)[0]
                    self.cb_cb1.clear()
                    self.cb_cb1.addItem(title)
                    for cb1_items in options.get(k):
                        if len(cb1_items) > 13:
                            self.cb_cb1.addItem(cb1_items[: 13] + '...')
                        else:
                            self.cb_cb1.addItem(cb1_items)

                elif 'cb2_' in k:
                    title = re.search(r'(?<=_)\w*(?=])', k)[0]
                    self.cb_cb2.clear()
                    self.cb_cb2.addItem(title)
                    for cb2_items in options.get(k):
                        if len(cb2_items) > 13:
                            self.cb_cb2.addItem(cb2_items[:13] + '...')
                        else:
                            self.cb_cb2.addItem(cb2_items)

                elif 'rb1_' in k:
                    title = re.search(r'(?<=_)\w*(?=])', k)[0]
                    self.gb_rb1.setTitle(title)
                    for child in self.gb_rb1.findChildren((QButtonGroup, QRadioButton)):
                        child.setParent(None)
                        del child
                    rb1_button_group = QtWidgets.QButtonGroup(self.gb_rb1)
                    for rb1_item_title in options.get(k):
                        rb1_item = QtWidgets.QRadioButton(self.gb_rb1)
                        font = QtGui.QFont()
                        font.setPointSize(10)
                        font.setBold(False)
                        font.setWeight(50)
                        rb1_item.setFont(font)
                        rb1_item.setObjectName("rb_defects_part_" + rb1_item_title)
                        rb1_item.setText(rb1_item_title)
                        rb1_button_group.addButton(rb1_item)
                        self.gl_rb1.addWidget(rb1_item)
                    rb1_button_group.buttonClicked.connect(self.__change_screenshot_name)
                    if rb1_button_group.buttons():
                        rb1_button_group.buttons()[0].setChecked(True)

                elif 'rb2_' in k:
                    title = re.search(r'(?<=_)\w*(?=])', k)[0]
                    self.gb_rb2.setTitle(title)
                    for child in self.gb_rb2.findChildren((QButtonGroup, QRadioButton)):
                        child.setParent(None)
                        del child
                    rb2_button_group = QtWidgets.QButtonGroup(self.gb_rb2)
                    for rb2_item_title in options.get(k):
                        rb2_item = QtWidgets.QRadioButton(self.gb_rb2)
                        font = QtGui.QFont()
                        font.setPointSize(10)
                        font.setBold(False)
                        font.setWeight(50)
                        rb2_item.setFont(font)
                        rb2_item.setObjectName("rb_defects_level_" + rb2_item_title)
                        rb2_item.setText(rb2_item_title)
                        rb2_button_group.addButton(rb2_item)
                        self.gl_rb2.addWidget(rb2_item)
                    rb2_button_group.buttonClicked.connect(self.__change_screenshot_name)
                    if rb2_button_group.buttons():
                        rb2_button_group.buttons()[0].setChecked(True)

        except Exception as e:
            logging.warning(str(e))
            QMessageBox.warning(self, '警告', str(e))

    # 初始化树
    def init_tree(self, working_path: str = None):
        self.tv_work_path_tree.headerItem().setText(0, "工作路径")
        self.tv_work_path_tree.clear()
        icon = QIcon("./assets/icon/folder.png")
        item = QTreeWidgetItem(TreeItemType.tvTopItem.value)
        item.setIcon(0, icon)
        item.setText(0, working_path)
        item.setFlags(self.treeItemFlags)
        item.setCheckState(1, Qt.Checked)
        item.setData(1, Qt.UserRole, "")
        item.setData(0, Qt.CheckStateRole, QVariant())
        self.tv_work_path_tree.addTopLevelItem(item)

    # 打开文件夹动作
    def act_open_dir(self):
        """
        打开照片文件夹
        :return:None
        """
        last_opened_image_directory = get_option("auto", "last_opened_image_directory", "")

        try:
            directory = QtWidgets.QFileDialog.getExistingDirectory(directory=last_opened_image_directory)
            # 如果上一次打开的路径和配置文件不一样，则修改配置文件中的默认路径为上次打开的路径
            if directory != last_opened_image_directory:
                reset_option("auto", "last_opened_image_directory", directory)

            if len(directory) >= 33:
                self.lbl_work_path.setText(directory[:30] + '...')
                self.lbl_work_path.setToolTip(directory)
            else:
                self.lbl_work_path.setText(directory)
                self.lbl_work_path.setToolTip(directory)
            self.refresh_dir(directory)

        except Exception as e:
            logging.warning(str(e))

    def refresh_dir(self, working_path: str):
        try:
            if not os.path.exists(working_path):
                return -1
            self.init_tree(working_path)

            curItem = self.tv_work_path_tree.topLevelItem(0)
            self.add_one_dir(working_path, curItem)
            self.tv_work_path_tree.itemDoubleClicked.connect(self.on_tv_work_path_tree_double_clicked)
        except Exception as e:
            print(e)

    def add_one_dir(self, dir_path: str = None, curTreeItem: QTreeWidgetItem = None):
        try:
            if not (dir_path and curTreeItem):
                return
            supported_formats = get_option("sys", "supported_formats",
                                           r"BMP|GIF|JPG|JPEG|PNG|PBM|PGM|PPM|XBM|XPM")

            for dir_ in os.listdir(dir_path):
                dirStr = os.path.join(dir_path, dir_)

                if os.path.isdir(dirStr):
                    icon = QIcon(":/assets/icon/folder.png")
                    dirObj = QDir(dirStr)
                    nodeText = dirObj.dirName()
                    item = QTreeWidgetItem(TreeItemType.tvGroupItem.value)
                    item.setIcon(0, icon)
                    item.setText(0, nodeText)
                    item.setFlags(self.treeItemFlags)
                    item.setCheckState(0, Qt.Checked)
                    item.setData(0, Qt.UserRole, dirStr)
                    item.setData(0, Qt.CheckStateRole, QVariant())
                    item.setToolTip(0, dirStr)
                    curTreeItem.addChild(item)
                    curTreeItem.setExpanded(True)
                elif os.path.isfile(dirStr):
                    if re.findall(dirStr.split('.')[-1].upper(), supported_formats):
                        icon = QIcon(":/assets/icon/picture.png")
                        fileInfo = QFileInfo(dirStr)
                        nodeText = fileInfo.fileName()
                        item = QTreeWidgetItem(TreeItemType.tvImageItem.value)
                        item.setIcon(0, icon)
                        item.setText(0, nodeText)
                        item.setFlags(self.treeItemFlags)
                        item.setCheckState(0, Qt.Checked)
                        item.setData(0, Qt.UserRole, dirStr)
                        item.setData(0, Qt.CheckStateRole, QVariant())
                        item.setToolTip(0, dirStr)
                        curTreeItem.addChild(item)
                        curTreeItem.setExpanded(True)
            if curTreeItem.childCount() > 0:
                for i in range(curTreeItem.childCount()):
                    nextTreeItem = curTreeItem.child(i)
                    nextDirStr = nextTreeItem.data(0, Qt.UserRole)
                    if os.path.isdir(nextDirStr):
                        self.add_one_dir(nextDirStr, nextTreeItem)
        except Exception as e:
            print(e)

    def __change_screenshot_name(self):
        params_dict = self.get_filled_in_text()
        dirname, filename = self.get_image_name(params_dict)
        dirname = get_option("file", "image_saving_directory", "images")
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        screenshot_count = self.get_screenshot_count()
        for i in range(screenshot_count):
            j = 1
            while True:
                full_path = os.path.normcase(os.path.join(dirname, (filename + '_' + str(j) + ".png")))
                if os.path.exists(full_path):
                    j += 1
                    continue
                else:
                    if i == 0:
                        text = self.get_screenshot_name_by_index(1)
                        if text == full_path:
                            j += 1
                            continue
                        else:
                            self.set_screenshot_name_by_index(0, full_path)
                            break
                    elif i == 1:
                        text = self.get_screenshot_name_by_index(0)
                        if text == full_path:
                            j += 1
                            continue
                        else:
                            self.set_screenshot_name_by_index(1, full_path)
                            break
                    else:
                        return

    def get_screenshot_count(self):
        pixmap_count = 0
        if self.tab.findChild(QGraphicsView):
            view = self.tab.findChild(QGraphicsView)
            if len(view.scene().items()) > 0:
                pixmap_count += 1
        if self.tab_2.findChild(QGraphicsView):
            view = self.tab_2.findChild(QGraphicsView)
            if len(view.scene().items()) > 0:
                pixmap_count += 1
        return pixmap_count

    def connect_database(self):
        """
        创建/连接到数据库，数据库名只能包括英文、数字、下划线
        :return:None
        """
        try:
            while True:
                # 弹出对话框获取数据库名
                ipt_db_name = QtWidgets.QInputDialog()
                ipt_db_name.setOkButtonText('确认')
                ipt_db_name.setCancelButtonText('取消')
                db_name, ok = ipt_db_name.getText(self, '打开/连接到数据库', '请输入数据库名')
                if ok:
                    from base import BASE_DIR, sys_config_path
                    if re.match(r'[A-Za-z_0-9]+$', db_name):
                        path = get_option("file", "database_saving_directory", "databases")

                        # 如果保存路径不存在则先创建文件夹
                        if not os.path.exists(path):
                            os.makedirs(path)
                        database_name = path + '/' + db_name + '.db'
                        self.db_name = database_name
                        database, cursor = self.create_database(database_name)
                        self.DATABASE = database
                        self.CURSOR = cursor

                        self.action_link_db.setEnabled(False)
                        self.action_close_db.setEnabled(True)
                        self.action_export_docx.setEnabled(True)
                        self.action_export_xlsx.setEnabled(True)
                        self.pb_commit_Db.setEnabled(True)
                        break
                    else:
                        QtWidgets.QMessageBox.warning(self, '警告', '数据库名只能包括字母数字下划线')
                else:
                    break
        except Exception as e:
            print(e)

    # 关闭数据库
    def close_database(self):
        """
        关闭并断开数据库连接
        :return:None
        """
        self.DATABASE.close()
        self.action_link_db.setEnabled(True)
        self.action_close_db.setEnabled(False)
        self.action_export_docx.setEnabled(False)
        self.action_export_xlsx.setEnabled(False)
        self.pb_commit_Db.setEnabled(False)

    def export_docx(self):
        """
        导出数据库中的每个数据表到独立的 word 文档
        :return:
        """
        try:
            cursor = self.CURSOR
            tables = cursor.execute("SELECT * FROM sqlite_master WHERE type = 'table'")
            sql_sentences = []
            for t in tables:
                table_name = t[2]
                if table_name != 'sqlite_sequence':
                    sql_sentences.append(f"SELECT * FROM {table_name}")
            if not len(sql_sentences) > 0:
                return
            from base import BASE_DIR, sys_config_path
            doc_export_path = get_option("file", "project_exporting_directory", "projects")

            args = []
            q = Manager().Queue(4)
            total_count = 0

            for sql in sql_sentences:
                filename = [self.db_name.split('/')[1].split('.')[0], sql.split()[-1]]
                filename = '_'.join(filename) + '.docx'
                records = cursor.execute(sql)
                records = list(records)
                total_count += len(records)
                args.append([doc_export_path, filename, records, q])

            export_docx_instance = ExportDocx()
            export_docx_instance.init_params(sql_sentences, args, q)
            export_docx_instance.start()

            qpd = QProgressDialog()
            qpd.setWindowTitle("正在导出...")
            qpd.setAutoClose(True)
            qpd.setRange(0, total_count)
            i = 0
            while True:
                res = q.get(timeout=3)
                if res == "_process_total_end":
                    break
                i += 1
                qpd.setValue(i)
                QCoreApplication.processEvents()
            self.statusBar.showMessage('导出成功', 5000)
            QMessageBox.information(self, '提示', '导出成功')
        except Exception as e:
            print(e)
            logging.warning(str(e))

    def __export_xlsx(self):
        """
        导出数据库中的每个数据表的所有记录到Excel，数据库名对应Excel名，数据表名对应worksheet名
        :return:
        """
        try:
            if not self.db_name:
                QMessageBox.warning(self, "警告", "数据库未连接")
                return
            xlsx_name, selected_filter = QFileDialog.getSaveFileName(self, "导出Excel", "", "Excel(*.xlsx)")
            if write_xlsx(self.db_name, xlsx_name) == 200:
                QMessageBox.information(self, '提示', '导出成功')
        except Exception as e:
            logging.warning(str(e))

    def display_image(self, image_path):
        """
        显示图片
        :param image_path:图片路径
        :return:None
        """
        try:
            self.clear_completed_info()
            self.gv_main_viewport.scene().clear()

            pixmap = QtGui.QPixmap(image_path)
            gvs_pixmapItem = QtWidgets.QGraphicsPixmapItem(pixmap)
            self.gv_main_viewport.scene().addItem(gvs_pixmapItem)
            gvs_pixmapItem.setData(graphicsItemDataFlags.pixmap_item.value, image_path)

            self.gv_main_viewport.fitInView(gvs_pixmapItem, Qt.KeepAspectRatio)
            self.gv_main_viewport.zoomInTimes = 1
            self.COUNT_INIT_ITEMS = 1
            self.COUNT_ITEMS_IN_SCENE = 1

            fileInfo = QFileInfo(image_path)
            fileName = fileInfo.fileName()
            self.label_8.setText(os.path.normcase(image_path))
            self.__auto_fill(fileName)
        except Exception as e:
            logging.warning(str(e))

    def refresh_photo(self):
        try:
            self.display_image(self.label_8.text())
        except Exception as e:
            logging.warning(str(e))

    def clear_completed_info(self):
        self.lineEdit.setText("")
        self.lineEdit_2.setText("")
        self.lineEdit_3.setText("")
        self.lineEdit_4.setText("")
        self.lineEdit_5.setText("")
        self.label_8.setText("")
        self.cb_cb1.setCurrentIndex(0)
        self.cb_cb2.setCurrentIndex(0)
        self.clear_tab_by_index(0)
        self.clear_tab_by_index(1)
        self.tabWidget.setCurrentIndex(0)

    # 双击目录树中的照片，打开并显示
    def on_tv_work_path_tree_double_clicked(self, event: QTreeWidgetItem, col):
        try:
            self.display_image(event.data(col, Qt.UserRole))
        except Exception as e:
            print(e)

    # 打开编辑数据库子窗口
    def show_db_reader(self):
        try:
            from src.myDbReader import DbReader

            self.db_reader = QMainWindow()
            widget = DbReader(self)
            self.db_reader.setCentralWidget(widget)
            self.db_reader.setWindowTitle("编辑数据库")
            self.db_reader.resize(1280, 768)
            self.db_reader.setWindowModality(Qt.ApplicationModal)
            self.db_reader.show()
        except Exception as e:
            print(e)

    # 左键绘制
    def start_paint(self):
        if not self.gv_main_viewport.status == imageViewerFlag.capturing.value:
            self.gv_main_viewport.status = imageViewerFlag.left_button_painting.value
            self.gv_main_viewport.setFocus(Qt.OtherFocusReason)
            icon = QPixmap(":/assets/icon/stroke_weight.png")
            icon = icon.scaled(25, 25, Qt.KeepAspectRatio)
            self.gv_main_viewport.setCursor(QCursor(icon))
            self.gv_main_viewport.update()

    def free_screenshot(self):
        """
        自由截图
        :return:None
        """
        try:
            if self.gv_main_viewport:
                self.gv_main_viewport.status = imageViewerFlag.capturing.value
            self.statusBar.showMessage('开始截图，按Esc取消', 5000)
            self.screenshot_widget = CaptureScreen()
            self.screenshot_widget.show()
            self.screenshot_widget.screenshot.connect(self.preview_screenshot)
        except Exception as e:
            logging.warning(str(e))

    def preview_screenshot(self, event):

        try:
            if not event:
                return
            if self.gv_main_viewport:
                self.gv_main_viewport.status = imageViewerFlag.normal.value
            pixmap = event

            if not self.gv_tb1.items():
                pixmapItem = QtWidgets.QGraphicsPixmapItem(pixmap)
                self.gv_tb1.scene().addItem(pixmapItem)
                self.tabWidget.setCurrentIndex(0)
                self.gv_tb1.fitInView(pixmapItem, Qt.KeepAspectRatio)
                self.__change_screenshot_name()
            elif not self.gv_tab2.items():
                pixmapItem = QtWidgets.QGraphicsPixmapItem(pixmap)
                self.gv_tab2.scene().addItem(pixmapItem)
                self.tabWidget.setCurrentIndex(self.tabWidget.indexOf(self.tabWidget.currentWidget()) + 1)
                self.gv_tab2.fitInView(pixmapItem, Qt.KeepAspectRatio)
                self.__change_screenshot_name()
            else:
                return

            while len(self.gv_main_viewport.scene().items()) > 1:
                self.gv_main_viewport.scene().removeItem(self.gv_main_viewport.scene().items()[0])
            self.gv_main_viewport.update()

        except Exception as e:
            print(e)
            logging.warning(str(e))

    # 提交数据库
    def on_btn_commit_clicked(self):
        if (self.cb_cb1.currentIndex() == 0) or (self.cb_cb2.currentIndex() == 0):
            QMessageBox.warning(self, "警告", "信息填写不完整")
            return
        self.commit_db()

    # 随着页面尺寸变化，自动定位浮动工具栏位置
    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        super(UiMainWindow, self).resizeEvent(a0)
        self.relocate_bar()

    # 截取主视口当前可见范围，快捷键B
    def capture_current_viewport(self):
        # 获取视图窗口
        rect = self.gv_main_viewport.viewport().rect()

        # 创建和视图窗口尺寸相同的Pixmap
        # 当前也可以不相同
        pixmap = QtGui.QPixmap(rect.size())
        pixmap.fill(Qt.transparent)
        painter = QtGui.QPainter(pixmap)

        # 渲染视图至pixmap并保存
        painter.begin(pixmap)
        # render必须放置在begin()和end()之间，否则闪退
        self.gv_main_viewport.render(painter, QtCore.QRectF(pixmap.rect()), rect)
        painter.end()

        clip_transparent_pixel_config = get_option("sys", "clip_transparent_pixel", "no")
        clip_transparent_pixel = True if clip_transparent_pixel_config == "yes" else False
        if clip_transparent_pixel:
            try:
                # 去黑边
                cv2_image = q_image_2_cv2(pixmap.toImage())
                cv2_image = remove_black_border(cv2_image)
                pixmap = QPixmap(cv2_2_q_image(cv2_image))
            except Exception as e:
                logging.warning(str(e))

        self.preview_screenshot(pixmap)

    # 点击提交按钮，提交数据库，保存截图，清空界面
    def commit_db(self):
        try:
            pixmap1 = self.gv_tb1.scene().items()[0].pixmap()
        except:
            pixmap1 = None
        try:
            pixmap2 = self.gv_tab2.scene().items()[0].pixmap()
        except:
            pixmap2 = None
        pixmap_list = []

        image_resize_ratio1, image_resize_ratio2 = self.get_ratios()

        if pixmap1:
            if pixmap2:
                pixmap1 = resize_pixmap(pixmap1, image_resize_ratio2)
                pixmap_list.append(pixmap1)
                pixmap2 = resize_pixmap(pixmap2, image_resize_ratio2)
                pixmap_list.append(pixmap2)
            else:
                pixmap1 = resize_pixmap(pixmap1, image_resize_ratio1)
                pixmap_list.append(pixmap1)

        params_dict = self.get_filled_in_text()

        full_path_list = self.save_images(pixmap_list)
        sql_sentences, values = self.get_one_sql(full_path_list, params_dict)
        self.CURSOR.execute(sql_sentences, values)
        self.DATABASE.commit()

        self.clear_completed_info()
        self.gv_main_viewport.scene().clear()

    @staticmethod
    def get_ratios():
        ratio1 = get_option("sys", "image_resize_ratio1", "1,1")
        image_resize_ratio1 = ratio1.split(",")
        image_resize_ratio1 = [float(i) for i in image_resize_ratio1]
        if len(image_resize_ratio1) < 2:
            image_resize_ratio1 = [1, 1]
        ratio2 = get_option("sys", "image_resize_ratio2", "1,1")
        image_resize_ratio2 = ratio2.split(",")
        image_resize_ratio2 = [float(i) for i in image_resize_ratio2]

        if len(image_resize_ratio2) < 2:
            image_resize_ratio2 = [1, 1]
        return image_resize_ratio1, image_resize_ratio2

    # 获取填写的内容，以字典形式返回
    def get_filled_in_text(self) -> dict:
        lineEdit1_text = self.lineEdit.text() if self.lineEdit.text() else self.lineEdit.placeholderText()
        lineEdit2_text = self.lineEdit_2.text() if self.lineEdit_2.text() else self.lineEdit_2.placeholderText()
        lineEdit3_text = self.lineEdit_3.text() if self.lineEdit_3.text() else self.lineEdit_3.placeholderText()
        lineEdit4_text = self.lineEdit_4.text() if self.lineEdit_4.text() else self.lineEdit_4.placeholderText()
        lineEdit5_text = self.lineEdit_5.text() if self.lineEdit_5.text() else self.lineEdit_5.placeholderText()
        dateEdit_text = self.dateEdit.text()
        cb1_text = self.cb_cb1.currentText()
        cb2_text = self.cb_cb2.currentText()
        rb1_text = self.gb_rb1.findChildren(QtWidgets.QButtonGroup)[0].checkedButton().text()
        rb2_text = self.gb_rb2.findChildren(QtWidgets.QButtonGroup)[0].checkedButton().text()
        params_dict = {"lineEdit1_text": lineEdit1_text, "lineEdit2_text": lineEdit2_text,
                       "lineEdit3_text": lineEdit3_text, "lineEdit4_text": lineEdit4_text,
                       "lineEdit5_text": lineEdit5_text, "dateEdit_text": dateEdit_text,
                       "cb1_text": cb1_text, "cb2_text": cb2_text,
                       "rb1_text": rb1_text, "rb2_text": rb2_text}
        return params_dict

    # 根据[保存路径]和[文件名]自动保存提供的[图像列表]，若文件已存在，编号自动递增
    def save_images(self, pixmap_list: list):
        full_path_list = []
        for i in range(len(pixmap_list)):
            pixmap_list[i].save(self.get_screenshot_name_by_index(i))
            full_path_list.append(self.get_screenshot_name_by_index(i))
        return full_path_list

    # 清空当前tabWidget页面
    def clear_current_tab(self):
        current_index = self.tabWidget.currentIndex()
        self.clear_tab_by_index(current_index)

    # 根据索引清空tabWidget页面
    def clear_tab_by_index(self, index):
        try:
            if not index in range(self.tabWidget.count()):
                return
            else:
                widget = self.tabWidget.widget(index)
                widget.findChildren(QLineEdit)[0].clear()
                widget.findChildren(QGraphicsView)[0].scene().clear()
        except Exception as e:
            print(str(e))

    def set_screenshot_name_by_index(self, index, text):
        widget = self.tabWidget.widget(index)
        line_edit = widget.findChildren(QLineEdit)[0]
        line_edit.setText(text)

    def get_screenshot_name_by_index(self, index):
        widget = self.tabWidget.widget(index)
        line_edit = widget.findChildren(QLineEdit)[0]
        text = line_edit.text()
        return text

    # 根据填写的内容，返回二元组（照片保存路径，照片名称）
    @staticmethod
    def get_image_name(params_dict):
        auto_generate_func = LoadPlugins("generateImageName")
        generateImageName = auto_generate_func.plugin_source.load_plugin("generateImageName")
        return generateImageName.generate_image_name(params_dict)

    # 根据数据库名，返回二元组（数据库连接，游标）
    @staticmethod
    def create_database(database_name):
        """
        创建/连接数据库
        :param database_name:数据库名，只能包括英文数字下划线
        :return:None
        """
        database = sqlite3.connect(database_name)
        cursor = database.cursor()
        try:
            database, cursor = init_database_with_template(database, cursor)
        except Exception as e:
            QtWidgets.QMessageBox.warning(None, '警告', '初始化数据库失败')
            logging.warning(str(e))
        finally:
            return database, cursor

    def count_screenshot(self):
        count = 0
        if self.gv_tb1.scene().items():
            count += 1
        if self.gv_tab2.scene().items():
            count += 1
        return count

    @staticmethod
    def get_one_sql(params_list, params_dict):
        generate_one_sql_func = LoadPlugins("generateOneSql")
        generateOneSql = generate_one_sql_func.plugin_source.load_plugin("generateOneSql")
        return generateOneSql.generate_one_sql(params_list, params_dict)

    def undo(self):
        """
        撤销绘制
        :return: None
        """
        if len(self.UNDO_LIST) < 10:
            self.action_redo.setEnabled(True)
            if len(self.gv_main_viewport.scene().items()) > self.COUNT_INIT_ITEMS:
                self.UNDO_LIST.append(self.gv_main_viewport.scene().items()[0])
                self.REDO_LIST.append(self.gv_main_viewport.scene().items()[0])
                self.gv_main_viewport.scene().removeItem(self.gv_main_viewport.scene().items()[0])
                self.gv_main_viewport.scene().update()
                if not len(self.UNDO_LIST) > 0:
                    self.action_undo.setEnabled(False)
                if not len(self.UNDO_LIST) < 10:
                    self.action_undo.setEnabled(False)

    def redo(self):
        """
        重做绘制
        :return: None
        """
        if len(self.REDO_LIST) > 0:
            self.action_undo.setEnabled(True)
            self.gv_main_viewport.scene().addItem(self.REDO_LIST[-1])
            self.gv_main_viewport.scene().update()
            self.REDO_LIST.pop(-1)
            self.UNDO_LIST.pop(-1)
            if not len(self.REDO_LIST) > 0:
                self.action_redo.setEnabled(False)

    def prev_item(self):
        """
        切换至前一张照片
        :return: None
        """
        try:
            if self.tv_work_path_tree.currentItem():
                prev_item = self.find_prev_item(self.tv_work_path_tree.currentItem())
                if prev_item == -1:
                    return
                self.tv_work_path_tree.setCurrentItem(prev_item)
                self.display_image(prev_item.data(0, Qt.UserRole))
        except Exception as e:
            logging.warning(str(e))

    def find_prev_item(self, item, order="positive"):
        index = self.tv_work_path_tree.indexFromItem(item, 0)
        parent = item.parent()
        row = index.row()
        row_limit = 0 if order == "positive" else parent.childCount() - 1
        if row == row_limit:
            if parent.type() == TreeItemType.tvTopItem.value:
                return -1
            elif parent.type() == TreeItemType.tvGroupItem.value:
                return self.find_prev_item(parent, order)
            else:
                return self.find_prev_item(parent, order)
        else:
            direction = -1 if order == "positive" else 1
            prev_item = parent.child(row + direction)
            if prev_item.type() == TreeItemType.tvImageItem.value:
                return prev_item
            elif prev_item.type() == TreeItemType.tvGroupItem.value:
                prev_prev_item_ = self.__check_null_dir(prev_item, order)
                if prev_prev_item_:
                    return prev_prev_item_
                else:
                    return self.find_prev_item(prev_item, order)

    def __check_null_dir(self, group: QTreeWidgetItem, order="positive"):
        if order == "positive":
            num = group.childCount() - 1
        elif order == "negative":
            num = 0
        else:
            return
        if group.childCount() == 0:
            return self.find_prev_item(group, order)
        else:
            if group.child(num).type() == TreeItemType.tvImageItem.value:
                return group.child(num)
            elif group.child(num).type() == TreeItemType.tvGroupItem.value:
                return self.__check_null_dir(group.child(num), order)

    def next_item(self):
        """
        切换至后一张照片
        :return: None
        """
        try:
            if self.tv_work_path_tree.currentItem():
                prev_item = self.find_prev_item(self.tv_work_path_tree.currentItem(), "negative")
                if prev_item == -1:
                    return
                self.tv_work_path_tree.setCurrentItem(prev_item)
                self.display_image(prev_item.data(0, Qt.UserRole))
        except Exception as e:
            logging.warning(str(e))

    @staticmethod
    def open_help_url():
        """
        打开官网
        :return: None
        """
        QDesktopServices.openUrl(QUrl("https://daradara.xyz/"))
