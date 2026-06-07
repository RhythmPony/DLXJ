import datetime
import json
import logging

import win32con, win32api

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QProcess
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFrame, QAction, QLineEdit, QFileDialog, qApp

from base import *
from src.AESCrypto import *
from src.authPageConverted import Ui_frm_auth_page
from src.getHardwareInfo import *
from src.myMainWindow import UiMainWindow


class AuthPage(QFrame, Ui_frm_auth_page):
    def __init__(self, parent=None):
        super(AuthPage, self).__init__(parent)
        self.action_1 = QAction()
        self.action_2 = QAction()
        self.setupUi(self)
        self.init_ui()
        self.init_event()

    def init_ui(self):
        self.setWindowFlag(Qt.FramelessWindowHint)
        stream = QtCore.QFile(":assets/style/auth_page.qss")
        stream.open(QtCore.QIODevice.ReadOnly)
        self.setStyleSheet(QtCore.QTextStream(stream).readAll())

        self.action_1.setIcon(QIcon(":assets/icon/request.png"))
        self.action_1.triggered.connect(self.get_local_code)
        self.action_1.setToolTip("获取机器码")
        self.le_local_code.addAction(self.action_1, QLineEdit.LeadingPosition)
        self.get_local_code()

        self.action_2.setIcon(QIcon(":assets/icon/authorize.png"))
        self.action_2.triggered.connect(self.get_auth_path)
        self.action_2.setToolTip("打开授权文件")
        self.le_auth_file.addAction(self.action_2, QLineEdit.LeadingPosition)

    def init_event(self):
        self.pb_confirm.clicked.connect(self.activate_app)
        self.pb_cancel.clicked.connect(self.close)

    def get_local_code(self):
        self.le_local_code.setText(crypto())

    def get_auth_path(self):
        filename, file_filter = QFileDialog.getOpenFileName(caption="打开授权文件", filter="*.auth")
        self.le_auth_file.setText(filename)

    def activate_app(self):
        filename = self.le_auth_file.text()
        if not filename:
            return
        local_code = hashlib.md5()
        local_code.update((crypto() + '_shakunage_3000_').encode())
        local_code = local_code.hexdigest()
        with open(filename, 'r+') as auth:
            auth_info = {}
            for line in auth.readlines():
                auth_info.update({line.strip().split(':')[0]: line.strip().split(':')[1]})
            if not auth_info.get('register_code') == local_code:
                QtWidgets.QMessageBox.warning(self, '警告', '序列号有误,激活失败')
                return
            data = {
                "register_code": auth_info['register_code'],
                "expire": auth_info['expire'],
                "last_login_time": AESCipher().encrypt(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            }

        try:
            res = json.dumps(data, indent=4)
            with open("LICENSE", "w") as lcs:
                lcs.write(res)
            win32api.SetFileAttributes("LICENSE", win32con.FILE_ATTRIBUTE_HIDDEN)
            QtWidgets.QMessageBox.information(self, '提示', '激活成功')
            restart_real_live()
        except Exception as e:
            logging.warning(str(e))
            QtWidgets.QMessageBox.warning(self, '警告', '未发现系统数据库，激活失败')


def restart_real_live():
    """ 进程控制实现自动重启

    :return:
    """
    qApp.quit()
    # QProcess 类的作用是启动一个外部的程序并与之交互，并且没有父子关系。
    p = QProcess
    # applicationFilePath() 返回应用程序可执行文件的文件路径
    p.startDetached(qApp.applicationFilePath())


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    auth_page = AuthPage()
    auth_page.show()

    sys.exit(app.exec_())
