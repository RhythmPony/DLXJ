import csv
import logging
import math
import os
import sqlite3
from operator import add

import numpy as np

from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QTextCursor
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox, QHeaderView
from PyQt5.QtCore import Qt

from src.dbReaderConverted import Ui_Form
from base import BASE_DIR
from src.databaseFrameworkTree import DatabaseFrameworkTree
from src.tableViewer import TableViewer
from src.utils import get_option


def init_model(records):
    if records:
        try:
            row = (len(records))
            column = len(records[0])
            model = QStandardItemModel(row, column)
            for r in range(row):
                for c in range(column):
                    item = QStandardItem(str(records[r][c]))
                    if c == 0:
                        item.setEditable(False)
                    model.setItem(r, c, item)
            return model
        except Exception as e:
            print("error at init_model__" + str(e))
    else:
        model = QStandardItemModel(1, 1)
        item = QStandardItem("No data")
        model.setItem(0, 0, item)
        return model


def model_to_table(model):
    row_count = model.rowCount()
    column_count = model.columnCount()

    table = np.matrix(np.zeros(shape=(row_count, column_count)), dtype=str)

    for row in range(row_count):
        for column in range(column_count):
            table[row, column] = model.item(row, column).text()
    return table


class DbReader(QWidget, Ui_Form):
    DATABASE = None
    CURSOR = None
    MODEL = None
    targetPage = 0
    recordPerPage = 0
    recordsModified = None
    modifiedDict = {}
    lastTableName = None

    def __init__(self, parent=None):
        super(DbReader, self).__init__(parent)
        self.db_framework_tree = DatabaseFrameworkTree()
        self.table_view = TableViewer()
        self.setupUi(self)
        self.setWindowFlag(Qt.Window)
        self.setWindowModality(Qt.WindowModal)

        self.init_UI()
        self.init_event()

        stream = QtCore.QFile(":assets/style/db_reader.qss")
        stream.open(QtCore.QIODevice.ReadOnly)
        self.setStyleSheet(QtCore.QTextStream(stream).readAll())

    def init_UI(self):
        self.vl_db_framework.addWidget(self.db_framework_tree)
        self.table_view.setAlternatingRowColors(True)
        self.vl_table_view.addWidget(self.table_view)
        self.frame_sql_query.setHidden(True)
        self.te_sql_query_input.setHidden(True)
        self.tb_execute_sql_query.setHidden(True)
        self.txtb_show_result.setHidden(True)

    def init_event(self):
        self.tb_show_result.clicked.connect(self.set_text_browser_visibility)
        self.tb_create_database.clicked.connect(self.do_create_database)
        self.tb_open_database.clicked.connect(self.do_connect_database)
        self.cb_table_name.currentTextChanged.connect(self.change_table)
        self.tb_export_csv.clicked.connect(self.export_csv)
        self.sb_num_per_page.valueChanged.connect(self.record_per_page_changed)
        self.pb_previsous.clicked.connect(self.turn_previous)
        self.pb_next.clicked.connect(self.turn_next)
        self.pb_skip.clicked.connect(self.fast_skip)
        self.tb_search.clicked.connect(lambda: self.search_keyword(self.le_search.text()))
        self.tb_refresh.clicked.connect(self.refresh_table)
        self.tb_execute_sql_query.clicked.connect(self.execute_user_query)
        self.tb_save.clicked.connect(self.save_modification)
        self.tb_create_db_with_template.clicked.connect(self.create_db_with_template)

    def init_db_framework(self, database):
        table_info_list = self.get_table_creations(database)
        table_framework = []
        for i in table_info_list:
            table_name = i[0]
            table_framework.append(self.format_database_framework(self.get_table_info(table_name)))
        table_framework_list = [table_info_list, table_framework]
        self.db_framework_tree.init_subtitle(table_framework_list)

    def get_table_info(self, table_name):
        sql = f"PRAGMA  table_info({table_name})"
        self.CURSOR.execute(sql)
        table_info = (table_name, [i for i in self.CURSOR.fetchall()])
        return table_info

    @staticmethod
    def format_database_framework(raw_table_info):
        table_info = []
        for i in raw_table_info[1]:
            name = i[1]
            r_type = i[2]
            framework = ['"' + name + '"', r_type]
            if i[3] == 1:
                framework.append("NOT NULL")
            if i[5] == 1:
                framework.append("UNIQUE")
            table_info.append([name, r_type, ' '.join(framework)])
        return raw_table_info[0], table_info

    def set_text_browser_visibility(self):
        self.frame_sql_query.setHidden(not (self.frame_sql_query.isHidden()))
        self.te_sql_query_input.setHidden(not (self.te_sql_query_input.isHidden()))
        self.tb_execute_sql_query.setHidden(not (self.tb_execute_sql_query.isHidden()))
        self.txtb_show_result.setHidden(not (self.txtb_show_result.isHidden()))

    def do_create_database(self):
        path = os.path.abspath(get_option("file", "database_saving_directory", "databases"))
        if os.path.isfile(path):
            path = os.path.dirname(path)
        path = os.path.normcase(path)
        file_name, selected_filter = QFileDialog.getSaveFileName(self, "新建数据库", path, "Databases (*.db)")
        if file_name:
            try:
                from src.myMainWindow import UiMainWindow
                database, cursor = UiMainWindow.create_database(file_name)
                if self.DATABASE:
                    self.DATABASE.close()
                self.DATABASE = database
                self.CURSOR = cursor

                QMessageBox.information(None, "提示", "数据库创建成功")
            except Exception as e:
                print(e)

    def do_connect_database(self):
        path = get_option("file", "database_saving_directory", "databases")
        if os.path.isfile(path):
            path = os.path.dirname(path)
        path = os.path.normcase(path)

        file_name, selected_filter = QFileDialog.getOpenFileName(self, "打开数据库", path, "Databases (*.db)")
        if file_name:
            try:
                # 获取数据库中的所有表名
                if self.DATABASE:
                    self.DATABASE.close()
                self.DATABASE = sqlite3.connect(file_name)
                self.CURSOR = self.DATABASE.cursor()
                table_names = self.get_table_names()
                self.cb_table_name.clear()
                self.cb_table_name.addItems(table_names)

                self.refresh_table(table_names[0])
                self.init_db_framework(self.DATABASE)
            except Exception as e:
                print(e)

    def change_table(self, event):
        if event == self.lastTableName:
            return
        if self.modifiedDict:
            confirm = QMessageBox.warning(self, "警告", "有修改的内容未保存，确认放弃修改", QMessageBox.Cancel | QMessageBox.Yes)
            if confirm == QMessageBox.Cancel:
                self.cb_table_name.setCurrentText(self.lastTableName)
                return
        self.modifiedDict = {}
        self.refresh_table(event)

    def refresh_table(self, table_name=None, conditions: list = None):
        if not table_name:
            try:
                table_name = self.cb_table_name.currentText() if self.cb_table_name else None
                if not table_name:
                    return
            except Exception as e:
                print(e)
        record_per_page = self.recordPerPage
        target_page = 1 if self.targetPage == 0 else self.targetPage
        start_index = (target_page - 1) * record_per_page
        records = self.select_records(table_name, start_index, record_per_page, conditions)

        self.MODEL = init_model(records)
        if not self.MODEL:
            self.init_when_error(table_name)
        headers = self.get_table_headers(table_name)
        self.MODEL.setHorizontalHeaderLabels(headers)
        self.MODEL.itemChanged.connect(self.cell_changed)
        self.table_view.setModel(self.MODEL)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.lastTableName = self.cb_table_name.currentText()
        if len(records) > 0:
            total_record_count = self.get_table_record_count(table_name)
            record_per_page = total_record_count if record_per_page == 0 else record_per_page
            total_page_count = int(math.ceil(total_record_count / record_per_page))
            cur_page_num = int((start_index / record_per_page) + 1)

            self.lbl_cur_page_num.setText(str(cur_page_num))

            self.sb_skip_to_num.setValue(cur_page_num)

            self.lbl_total_page_count.setText(str(total_page_count))

    def init_when_error(self, table_name):
        self.recordPerPage = 0
        self.targetPage = 0
        self.refresh_table(table_name)
        self.sb_num_per_page.setValue(0)

    def get_table_names(self):
        table_names = [i[0] for i in
                       self.CURSOR.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return table_names

    def get_table_record_count(self, table_name):
        sql = f"SELECT COUNT(*) FROM {table_name}"
        self.CURSOR.execute(sql)
        total_record_count = self.CURSOR.fetchall()[0][0]
        return total_record_count

    def select_records(self, table_name, start_index=0, record_count=0, params: list = None):
        if record_count == 0:
            sql = f"SELECT * FROM {table_name}"
        else:
            sql = f"SELECT * FROM {table_name} LIMIT {start_index} ,{record_count}"

        if params:
            sub_sql = " WHERE"
            condition = [" id = " + str(i) for i in params]
            sub_sql += " OR".join(condition)
            sql += sub_sql

        self.CURSOR.execute(sql)
        records = self.CURSOR.fetchall()
        return records

    def export_csv(self):
        try:
            model = self.MODEL
            table = model_to_table(model)

            with open(r"F:\123.csv", 'w+', encoding="utf-8", newline='') as csv_file:
                writer = csv.writer(csv_file)
                for row in table.tolist():
                    writer.writerow(row)
            QMessageBox.information(self, "提示", "CSV导出完成")

        except Exception as e:
            print("数据库未连接或数据表为空\n" + str(e))

    def get_table_headers(self, table_name):
        sql = f"PRAGMA  table_info({table_name})"
        self.CURSOR.execute(sql)
        headers = [i[1] for i in self.CURSOR.fetchall()]
        return headers

    def record_per_page_changed(self, event):
        self.recordPerPage = event

    def turn_previous(self):
        cur_page_num = int(self.lbl_cur_page_num.text())
        if cur_page_num > 1:
            self.lbl_cur_page_num.setText(str(cur_page_num - 1))
            self.targetPage = cur_page_num - 1
            self.refresh_table(self.cb_table_name.currentText())

    def turn_next(self):
        cur_page_num = int(self.lbl_cur_page_num.text())
        total_page_count = int(self.lbl_total_page_count.text())
        if cur_page_num < total_page_count:
            self.lbl_cur_page_num.setText(str(cur_page_num + 1))
            self.targetPage = cur_page_num + 1
            self.refresh_table(self.cb_table_name.currentText())

    def fast_skip(self):
        target_page_num = int(self.sb_skip_to_num.text())
        total_page_count = int(self.lbl_total_page_count.text())
        if 0 <= target_page_num <= total_page_count:
            self.lbl_cur_page_num.setText(str(target_page_num))
            self.targetPage = target_page_num
            self.refresh_table(self.cb_table_name.currentText())

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        if self.recordsModified:
            confirm = QMessageBox.warning(None, "警告", "修改未保存，确认关闭本窗口？", QMessageBox.Cancel | QMessageBox.Yes)
            if not confirm == QMessageBox.Yes:
                a0.ignore()

    def get_keyword_contained_lines(self, keyword):
        if not keyword:
            return
        model = self.MODEL
        if not model:
            return
        table = model_to_table(model)
        rows = []
        for i in range(table.shape[0]):
            for j in range(table.shape[1]):
                if keyword in table[i, j]:
                    rows.append(table[i, 0])
        return rows

    def search_keyword(self, keyword):
        rows = self.get_keyword_contained_lines(keyword)
        table_name = self.cb_table_name.currentText()
        self.refresh_table(table_name, rows)

    def execute_user_query(self):
        if not self.te_sql_query_input.toPlainText():
            return
        if not self.CURSOR:
            return
        sql_list = self.te_sql_query_input.toPlainText().split(';')
        cursor = self.CURSOR
        for sql in sql_list:
            raw_text = [self.txtb_show_result.toPlainText()]
            try:
                cursor.execute(sql)
                res = cursor.fetchall()
                self.txtb_show_result.clear()
                if not res:
                    raw_text.append("查询成功" + sql + "\n返回值：\n无\n")
                else:
                    output = ""
                    for i in res:
                        line = (" , ".join([str(j) for j in i]))
                        output += line + "\n"
                    raw_text.append("查询成功" + sql + "\n返回值：\n" + output)
            except Exception as e:
                raw_text.append("查询失败" + sql)
                print(e)
                continue
            finally:
                self.txtb_show_result.moveCursor(QTextCursor.End)
                self.txtb_show_result.setText("\n".join(raw_text))
                self.txtb_show_result.repaint()
                self.DATABASE.commit()

    def cell_changed(self, event: QStandardItem):
        row = event.index().row()
        column = event.index().column()
        text = event.text()
        record_id = int(self.MODEL.item(row, 0).text())
        attr_name = self.MODEL.horizontalHeaderItem(column).text()
        if not record_id in self.modifiedDict.keys():
            self.modifiedDict[record_id] = {}
        elif not attr_name in self.modifiedDict[record_id].keys():
            self.modifiedDict[record_id][attr_name] = ""
        self.modifiedDict[record_id][attr_name] = text

    def save_modification(self):
        try:
            table_name = self.cb_table_name.currentText()
            data = []
            for k, v in self.modifiedDict.items():
                attrs = list(v.keys())
                equals = ['='] * len(attrs)
                temp = list(map(add, attrs, equals))
                texts = ["\'" + i + "\'" for i in v.values()]
                modifications = ','.join(list(map(add, temp, texts)))
                data.append([table_name, modifications, k])
            self.multi_update(data)
            self.modifiedDict = {}
        except Exception as e:
            print(e)

    def multi_update(self, data):
        if not data:
            return
        confirm = QMessageBox.warning(self, "警告", "确认保存修改", QMessageBox.Cancel | QMessageBox.Yes)
        if confirm == QMessageBox.Cancel:
            return
        for d in data:
            sql = f"UPDATE {d[0]} SET {d[1]} WHERE id={d[2]}"
            self.CURSOR.execute(sql)
        self.DATABASE.commit()

    def cancel_modifications(self):
        confirm = QMessageBox.warning(self, "警告", "有修改的内容未保存，确认放弃修改", QMessageBox.Cancel | QMessageBox.Yes)
        if confirm == QMessageBox.Cancel:
            return
        self.modifiedDict = {}

    def create_db_with_template(self):
        path = get_option("file", "template_database_file", "databases/template.db")
        try:
            database = sqlite3.connect(path)
            creations = self.get_table_creations(database)
            database.close()
            if creations:
                file_name, selected_filter = QFileDialog.getSaveFileName(self, "从模板创建数据库", BASE_DIR, "Database(*.db)")
                if file_name:
                    database = sqlite3.connect(file_name)
                    cursor = database.cursor()
                    for i in creations:
                        cursor.execute(i[1])
                    database.commit()
                    database.close()
                    QMessageBox.information(self, "提示", "数据库创建成功")
        except Exception as e:
            QMessageBox.warning(self, "警告", "没有找到模板数据库")
            logging.warning(str(e))

    def get_table_creations(self, database):
        try:
            cursor = database.cursor()
            cursor.execute("SELECT name,sql FROM sqlite_master WHERE type='table'")
            table_info_list = [(i[0], i[1]) for i in cursor.fetchall() if "sqlite_sequence" not in i[0]]
            return table_info_list
        except Exception as e:
            QMessageBox.critical(self, "错误", "模板数据库已损坏")
            print(e)
