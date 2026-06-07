pyuic5 ./UI/DLXJ/mainwindow.ui -o ./src/DLXJMainWindowConverted.py
pyuic5 ./UI/DLXJ/dbReader.ui -o ./src/dbReaderConverted.py
pyuic5 ./UI/DLXJ/floatBar.ui -o ./src/floatBarConverted.py
pyuic5 ./UI/DLXJ/authPage.ui -o ./src/authPageConverted.py
pyuic5 ./UI/DLXJ/richTextEditor.ui -o ./src/richTextEditorConverted.py
pyuic5 ./UI/DLXJ/bezierEdit.ui -o ./src/bezierEditConverted.py
pyuic5 ./UI/DLXJ/settingsPage.ui -o ./src/settingsPageConverted.py

pyrcc5 ./UI/DLXJ/DLXJResources.qrc -o ./src/DLXJResources_rc.py
