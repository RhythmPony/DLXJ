from enum import Enum

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidgetItem, QTreeWidget


class DbFrameworkTreeItemType(Enum):
    itTopItem = 2001
    itDbItem = 2002
    itTableItem = 2003
    itRecordItem = 2004


class DbFrameworkTreeCol(Enum):
    colName = 0
    colType = 1
    colFramework = 2


class DatabaseFrameworkTree(QTreeWidget):
    dbFrameworkTreeItemFlags = (Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsAutoTristate)
    lastCellWidth = 810

    def __init__(self, parent=None):
        super(DatabaseFrameworkTree, self).__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setColumnCount(3)
        self.setColumnWidth(0, 256)
        self.setColumnWidth(1, 128)
        self.setHeaderHidden(True)

        self.init_tree_head()
        head_item = self.topLevelItem(0)
        titles = self.init_title(["表", "索引", "视图", "触发器"])
        head_item.addChildren(titles)
        head_item.setExpanded(True)

    def init_tree_head(self):
        item = QTreeWidgetItem(DbFrameworkTreeItemType.itTopItem.value)
        item = self.init_tree_item(item, ["名称", "类型", "架构"])
        self.addTopLevelItem(item)

    def init_title(self, title_list: list):
        item_list = []
        for title in title_list:
            item = QTreeWidgetItem(DbFrameworkTreeItemType.itDbItem.value)
            item = self.init_tree_item(item, [title, "", ""])
            item_list.append(item)
        return item_list

    def init_subtitle(self, table_framework_list: list):
        current_item = self.itemAt(0, 0).child(0)
        creations = table_framework_list[0]
        table_framework = table_framework_list[1]
        item_list = []
        for creation in creations:
            item = QTreeWidgetItem(DbFrameworkTreeItemType.itTableItem.value)
            item = self.init_tree_item(item, [creation[0], "TABLE", creation[1]])
            item_list.append(item)
        current_item.addChildren(item_list)
        current_item.setExpanded(True)
        self.init_table_framework(item_list, table_framework)

    def init_table_framework(self, item_list, table_framework):
        for current_item in item_list:
            table_name = current_item.text(0)
            for table_info in table_framework:
                item_list = []
                if table_name == table_info[0]:
                    for table_filed in table_info[1]:
                        item = QTreeWidgetItem(DbFrameworkTreeItemType.itRecordItem.value)
                        item = self.init_tree_item(item, table_filed)
                        item_list.append(item)
                current_item.addChildren(item_list)

    def init_tree_item(self, item: QTreeWidgetItem, head_texts: list):
        for i in range(len(head_texts)):
            item.setText(i, str(head_texts[i]))
            item.setToolTip(i, str(head_texts[i]))
        item.setFlags(self.dbFrameworkTreeItemFlags)
        return item
