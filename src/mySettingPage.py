import logging
import os
import sys
from collections import defaultdict

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QButtonGroup, QMessageBox, QFileDialog

from base import sys_config_path, BASE_DIR
from src.settingsPageConverted import Ui_Form
from src.utils import get_option, read_sys_config


class SettingPage(QFrame, Ui_Form):
    sgl_config_changed = pyqtSignal(str)
    option_changed = {}

    def __init__(self):
        super(SettingPage, self).__init__()
        self.button_group = QButtonGroup()
        self.init_ui()
        self.init_event()
        self.init_value()
        self.option_changed = defaultdict(str)

    def init_ui(self):
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.button_group.addButton(self.pb_universe)
        self.button_group.addButton(self.pb_ui)
        self.button_group.addButton(self.pb_project)
        self.button_group.addButton(self.pb_other)

        stream = QtCore.QFile(":assets/style/setting_page.qss")
        stream.open(QtCore.QIODevice.ReadOnly)
        self.setStyleSheet(QtCore.QTextStream(stream).readAll())

    def init_event(self):
        self.tb_template_database_path.clicked.connect(self.set_template_database_path)
        self.tb_database_path.clicked.connect(self.set_database_path)
        self.tb_image_path.clicked.connect(self.set_image_path)
        self.tb_project_path.clicked.connect(self.set_project_path)
        self.tb_open_option_path.clicked.connect(self.set_option_path)
        self.tb_close.clicked.connect(self.close_page)
        self.pb_universe.clicked.connect(lambda: self.change_stacked_page(0))
        self.pb_ui.clicked.connect(lambda: self.change_stacked_page(1))
        self.pb_project.clicked.connect(lambda: self.change_stacked_page(2))
        self.pb_other.clicked.connect(lambda: self.change_stacked_page(3))
        self.pb_reset_sys_config.clicked.connect(self.reset_sys_config)

        self.cb_clip_transparent_pixel.clicked.connect(self.on_erase_transparent_pixel_changed)
        self.cb_resize_hint.currentIndexChanged.connect(self.on_resize_hint_index_changed)

        self.le_supported_format.textChanged.connect(lambda: self.on_line_edit_changed("sys", "supported_formats"))
        self.le_option_path.textChanged.connect(lambda: self.on_line_edit_changed("sys", "customizable_option"))
        self.le_resize_ratio1.textChanged.connect(lambda: self.on_line_edit_changed("sys", "image_resize_ratio1"))
        self.le_resize_ratio2.textChanged.connect(lambda: self.on_line_edit_changed("sys", "image_resize_ratio2"))
        self.le_word_page_size.textChanged.connect(lambda: self.on_line_edit_changed("sys", "word_page_size"))
        self.le_word_margin.textChanged.connect(lambda: self.on_line_edit_changed("sys", "word_page_margin"))

        self.le_title_placehold.textChanged.connect(lambda: self.on_line_edit_changed("ui", "line_placeholder1"))
        self.le_line_name_placehold.textChanged.connect(lambda: self.on_line_edit_changed("ui", "line_placeholder2"))
        self.le_line_code_placehold.textChanged.connect(lambda: self.on_line_edit_changed("ui", "line_placeholder3"))
        self.le_defects_method_placehold.textChanged.connect(
            lambda: self.on_line_edit_changed("ui", "line_placeholder4"))
        self.le_defects_date_placehold.textChanged.connect(lambda: self.on_line_edit_changed("ui", "default_date"))
        self.le_photo_name_placehold.textChanged.connect(lambda: self.on_line_edit_changed("ui", "line_placeholder5"))

        self.le_project_path.textChanged.connect(
            lambda: self.on_line_edit_changed("file", "project_exporting_directory"))
        self.le_image_path.textChanged.connect(lambda: self.on_line_edit_changed("file", "image_saving_directory"))
        self.le_database_path.textChanged.connect(
            lambda: self.on_line_edit_changed("file", "database_saving_directory"))
        self.le_template_database_path.textChanged.connect(
            lambda: self.on_line_edit_changed("file", "template_database_file"))

    def init_value(self):
        self.le_supported_format.setText(get_option("sys", "supported_formats", "none"))
        is_checked = True if get_option("sys", "clip_transparent_pixel", "no") == "yes" else False
        self.cb_clip_transparent_pixel.setChecked(is_checked)
        self.le_option_path.setText(get_option("sys", "customizable_option", "none"))
        try:
            index = int(get_option("sys", "image_resize_hint", "1"))
        except Exception as e:
            index = 1
            logging.warning(str(e))
        self.cb_resize_hint.setCurrentIndex(index)
        if index == 0:
            self.le_resize_ratio1.setEnabled(False)
            self.le_resize_ratio2.setEnabled(False)
        else:
            self.le_resize_ratio1.setText(get_option("sys", "image_resize_ratio1", "none"))
            self.le_resize_ratio2.setText(get_option("sys", "image_resize_ratio2", "none"))
        self.le_word_page_size.setText(get_option("sys", "word_page_size", "none"))
        self.le_word_margin.setText(get_option("sys", "word_page_margin", "none"))

        self.le_title_placehold.setText(get_option("ui", "line_placeholder1", "none"))
        self.le_line_name_placehold.setText(get_option("ui", "line_placeholder2", "none"))
        self.le_line_code_placehold.setText(get_option("ui", "line_placeholder3", "none"))
        self.le_defects_method_placehold.setText(get_option("ui", "line_placeholder4", "none"))
        self.le_defects_date_placehold.setText(get_option("ui", "default_date", "none"))
        self.le_photo_name_placehold.setText(get_option("ui", "line_placeholder5", "none"))

        self.le_project_path.setText(get_option("file", "project_exporting_directory", "default"))
        self.le_image_path.setText(get_option("file", "image_saving_directory", "default"))
        self.le_database_path.setText(get_option("file", "database_saving_directory", "default"))
        self.le_template_database_path.setText(get_option("file", "template_database_file", "default"))

        self.lbl_log_path.setText(get_option("auto", "log_file", "none"))
        self.lbl_last_opened_directory.setText(get_option("auto", "last_opened_image_directory", "none"))

    def change_stacked_page(self, page_num):
        for button in self.button_group.children():
            if not button == self.sender():
                button.setChecked(not self.sender().isChecked())
        self.stackedWidget.setCurrentIndex(page_num)

    def on_line_edit_changed(self, section, key):
        value = self.sender().text()
        self.option_changed[section, key] = value

    def on_erase_transparent_pixel_changed(self):
        self.option_changed["sys", "clip_transparent_pixel"] = "yes" if self.sender().isChecked() else "no"

    def on_resize_hint_index_changed(self):
        self.option_changed["sys", "image_resize_hint"] = self.sender().currentIndex()

    def close_page(self):
        if self.option_changed:
            confirm = QMessageBox.information(self, "提示", "请确认是否保存改动",
                                              QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if confirm == QMessageBox.Yes:
                self.save_options()
                self.sgl_config_changed[str].emit("__config_changed__")
                self.close()
            elif confirm == QMessageBox.No:
                self.close()
            else:
                return
        else:
            self.close()

    def save_options(self):
        config = read_sys_config(sys_config_path)
        for k, v in self.option_changed.items():
            config.set(k[0], k[1], str(v))
        with open(os.path.join(BASE_DIR, sys_config_path), 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    def reset_sys_config(self):
        confirm = QMessageBox.information(self, "提示", "请确认是否恢复默认设置",
                                          QMessageBox.Ok | QMessageBox.Cancel)
        if confirm == QMessageBox.Ok:
            stream = QtCore.QFile(":assets/config/config.ini")
            stream.open(QtCore.QIODevice.ReadOnly)
            text_stream = QtCore.QTextStream(stream)
            text_stream.setCodec("utf-8")
            default_config = text_stream.readAll()
            with open("config.ini", "w", encoding="utf-8") as config:
                config.write(default_config)
            self.init_value()
            self.option_changed = {}

    def set_option_path(self):
        filename, _ = QFileDialog.getOpenFileName(self, "选择配置文件", "", "Option(*.txt *.ini);;All(*)")
        self.le_option_path.setText(filename)

    def set_project_path(self):
        dirname = QFileDialog.getExistingDirectory(self, "选择项目导出目录", "", )
        self.le_project_path.setText(dirname)

    def set_image_path(self):
        dirname = QFileDialog.getExistingDirectory(self, "选择截图保存目录", "", )
        self.le_image_path.setText(dirname)

    def set_database_path(self):
        dirname = QFileDialog.getExistingDirectory(self, "选择数据库目录", "", )
        self.le_database_path.setText(dirname)

    def set_template_database_path(self):
        filename, _ = QFileDialog.getOpenFileName(self, "选择模板数据库文件", "", "Database(*.db);;All(*)")
        self.le_template_database_path.setText(filename)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    auth_page = SettingPage()
    auth_page.show()

    sys.exit(app.exec_())
