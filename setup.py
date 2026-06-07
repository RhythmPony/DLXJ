# 使用python setup.py build_ext --inplace运行

from distutils.core import setup
from Cython.Build import cythonize

py_files = [
    "base.py",
    "src/AESCrypto.py",
    "src/authPageConverted.py",
    "src/bezierEditConverted.py",
    "src/checkAuth.py",
    "src/customGraphicsPathItem.py",
    "src/databaseFrameworkTree.py",
    "src/databaseTemplate.py",
    "src/dbReaderConverted.py",
    "src/DLXJMainWindowConverted.py",
    "src/floatBarConverted.py",
    "src/getHardwareInfo.py",
    "src/imageViewer.py",
    "src/myAuthPage.py",
    "src/myBezierEditor.py",
    "src/myDbReader.py",
    "src/myFloatBar.py",
    "src/myMainWindow.py",
    "src/myRichTextEditor.py",
    "src/mySettingPage.py",
    "src/pluginLoader.py",
    "src/richTextEditorConverted.py",
    "src/screenshot.py",
    "src/settingsPageConverted.py",
    "src/tableViewer.py",
    "src/utils.py",
    "src/wordTemplate.py",
]

setup(
    ext_modules=cythonize(py_files)
)
