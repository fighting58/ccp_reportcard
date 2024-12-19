from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, 
                              QHBoxLayout, QFormLayout, QGridLayout, QListWidget, QComboBox, 
                              QLineEdit, QDialog, QMenu)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction

from environment_manage import EnvironmentManager
import sys

class CustomListWidget(QListWidget):
    item_removed = Signal(str)
    list_cleared = Signal()

    def __init__(self, parent=None):
        super().__init__()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openMenu)

    def openMenu(self, position):
        menu = QMenu()
        
        # Delete Action
        delete_action = QAction("이 항목 제거", self)
        delete_action.triggered.connect(self.deleteItem)
        menu.addAction(delete_action)
        
        # Delete All Action
        delete_all_action = QAction("리스트 클리어", self)
        delete_all_action.triggered.connect(self.deleteAllItems)
        menu.addAction(delete_all_action)        
        menu.exec(self.viewport().mapToGlobal(position))

    def deleteItem(self):
        selected_items = self.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            self.takeItem(self.row(item))
        self.item_removed.emit(selected_items[0].text())


    def deleteAllItems(self):
        self.clear()
        self.list_cleared.emit()

class Settings(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("환경 설정")
        self.resize(500, 300)
        self.setup_UI()
        self.settings = None

        self.load_config()


    def setup_UI(self):

        main_layout= QGridLayout(self)
        main_layout.setSpacing(20)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(20)

        self.user_list = CustomListWidget(self)
        self.user_list.setFixedHeight(160)
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.user_name = QLineEdit("", self)
        self.user_license = QComboBox(self)
        self.user_license.addItems(["지적기술사", "지적기사", "지적산업기사", "지적기능사"])
        self.user_grade = QLineEdit("", self)
        self.user_license.setCurrentIndex(1)
        self.machine_serial = QLineEdit("", self)
        self.summit = QPushButton("저장", self)

        form_layout.addRow("팀         장 :", self.user_name)
        form_layout.addRow("자         격 :", self.user_license)
        form_layout.addRow("직         급 :", self.user_grade)
        form_layout.addRow("안테나번호 :", self.machine_serial)
        form_layout.addRow("", self.summit)

        control_layout.addWidget(self.user_list)
        control_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        cancel_button = QPushButton("취소", self)
        ok_button = QPushButton("확인", self)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)

        main_layout.addLayout(control_layout, 0, 0, 1, 2)
        main_layout.addLayout(button_layout, 1, 1, 1, 2)

        self.user_list.item_removed.connect(self.remove_user)
        self.user_list.list_cleared.connect(lambda: self.settings.clear_environment())
        self.summit.clicked.connect(self.save_settings)
        self.user_list.itemDoubleClicked.connect(self.load_user_settings)
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.close)

    @Slot(str)
    def remove_user(self, user_name):
        self.settings.remove_section(user_name)

    def load_config(self):
        self.settings = EnvironmentManager()
        self.user_list.clear()
        self.load_user_list()

    def load_user_list(self):
        users = self.settings.get_all_section_names()
        if "CUR_USER" in users:
            users.pop(users.index("CUR_USER"))
        self.user_list.addItems(users)

    def load_user_settings(self):
        selected_user = self.user_list.currentItem().text()
        user_dict = self.settings.get_section(selected_user)
        self.user_name.setText(selected_user)
        self.user_license.setCurrentText(user_dict["license"])
        self.user_grade.setText(user_dict["grade"])
        self.machine_serial.setText(user_dict["machine_serial"])

    def save_settings(self):
        section = self.user_name.text().strip()
        if section == "":
            return
        key_value_pairs = {"license": self.user_license.currentText(), "grade": self.user_grade.text().strip(), "machine_serial": self.machine_serial.text().strip()}
        self.settings.add_section(section, key_value_pairs)
        self.load_config()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Settings()

    isAccepted = window.exec()
    if isAccepted == QDialog.Accepted:
        env = EnvironmentManager()
        env.remove_section("CUR_USER")        
        print(env.get_current_user())
        print(env.get_all_user())
    app.quit()
    sys.exit(0)








