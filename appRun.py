import logging

import base
from src import AESCrypto
from src import authPageConverted
from src import bezierEditConverted
from src import checkAuth
from src import customGraphicsPathItem
from src import databaseFrameworkTree
from src import databaseTemplate
from src import dbReaderConverted
from src import DLXJMainWindowConverted
from src import floatBarConverted
from src import getHardwareInfo
from src import imageViewer
from src import myAuthPage
from src import myBezierEditor
from src import myDbReader
from src import myFloatBar
from src import myMainWindow
from src import myRichTextEditor
from src import mySettingPage
from src import pluginLoader
from src import richTextEditorConverted
from src import screenshot
from src import settingsPageConverted
from src import tableViewer
from src import utils
from src import wordTemplate

import time
from multiprocessing import freeze_support

import sys
from PyQt5 import QtWidgets

from src.myAuthPage import AuthPage
from src.myMainWindow import UiMainWindow
from src.utils import get_option

log_file = get_option("auto", "log_file", "appRun.log")
logging.basicConfig(filename=log_file, format='%(asctime)s  [%(levelname)s]>>>  %(message)s',
                    datefmt='%Y/%m/%d %H:%M:%S', level=logging.WARNING)

if __name__ == "__main__":

    # 使用multiprocessing模块必须把下面这句放在main函数开始的位置
    freeze_support()

    app = QtWidgets.QApplication(sys.argv)
    auth_page = AuthPage()
    auth_page.show()
    time.sleep(0.5)

    from src.checkAuth import get_sys_info, is_authed, update_sys_info

    auth_info = get_sys_info()

    if is_authed(auth_info):
        auth_page.close()
        update_sys_info(auth_info)

        mainWindow = UiMainWindow()
        mainWindow.setWindowTitle("电力巡检APP")
        mainWindow.show()

    sys.exit(app.exec_())
