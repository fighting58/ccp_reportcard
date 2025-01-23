from PySide6.QtWidgets import (QApplication, QPushButton, QHBoxLayout, QFormLayout, QGridLayout, 
                               QListWidget, QComboBox, QLineEdit, QDialog, QMenu, QTabWidget, QWidget)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction

from environment_manage import EnvironmentManager
from QCustomModals import QCustomModals

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
        self.resize(500, 246)
        self.setup_UI()
        self.settings = None
        self.api_key = ''
        self.expiring_date = ''

        self.load_config()

    def setup_UI(self):

        main_layout= QGridLayout(self)
        main_layout.setSpacing(20)

        self.setting_tab = QTabWidget(self)        
        self.setting_tab.setObjectName("setting_tab")
        self.setting_tab.setFixedHeight(200)
        tab1 = QWidget(self)        
        # 사용자 추가
        control_layout = QHBoxLayout(tab1)
        control_layout.setSpacing(20)

        self.user_list = CustomListWidget(tab1)
        self.user_list.setFixedHeight(160)
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.user_name = QLineEdit("", tab1)
        self.user_license = QComboBox(tab1)
        self.user_license.addItems(["지적기술사", "지적기사", "지적산업기사", "지적기능사"])
        self.user_grade = QLineEdit("", tab1)
        self.user_license.setCurrentIndex(1)
        self.machine_serial = QLineEdit("", tab1)
        self.summit = QPushButton("저장", tab1)

        form_layout.addRow("팀         장 :", self.user_name)
        form_layout.addRow("자         격 :", self.user_license)
        form_layout.addRow("직         급 :", self.user_grade)
        form_layout.addRow("안테나번호 :", self.machine_serial)
        form_layout.addRow("", self.summit)

        control_layout.addWidget(self.user_list)
        control_layout.addLayout(form_layout)

        # vworld_api 설정
        tab2 = QWidget(self)
        vworld_api_layout = QFormLayout(tab2)
        self.api_key_input = QLineEdit(tab2)
        self.expiring_date_input = QLineEdit(tab2)
        self.expiring_date_input.setPlaceholderText("ex) 2024-11-20")
        self.summit2 = QPushButton("저장", tab1)

        vworld_api_layout.addRow("VWorld API 키 :", self.api_key_input)
        vworld_api_layout.addRow("인 증 만 료 일 :", self.expiring_date_input)
        vworld_api_layout.addRow("", self.summit2)
        
        self.setting_tab.addTab(tab1, "사용자 추가")
        self.setting_tab.addTab(tab2, "VWorld API 설정")

        # 확인 취소 버튼
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        cancel_button = QPushButton("취소", self)
        ok_button = QPushButton("확인", self)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)

        main_layout.addWidget(self.setting_tab, 0, 0, 1, 3)
        main_layout.addLayout(button_layout, 1, 1, 1, 2)

        # 시그널-슬롯 연결        
        self.user_list.item_removed.connect(self.remove_user)
        self.user_list.list_cleared.connect(lambda: self.settings.clear_environment())
        self.summit.clicked.connect(self.save_settings)
        self.summit2.clicked.connect(self.save_api_settings)
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
        self.load_api_settings()
    
    def load_api_settings(self):
        api_key = self.settings.get_section("VWORLD_API_SETTINGS").get("api_key", '')
        expiring_date = self.settings.get_section("VWORLD_API_SETTINGS").get("expiring_date", '')
        self.api_key_input.setText(api_key)
        self.expiring_date_input.setText(expiring_date)

    def load_user_list(self):
        users = self.settings.get_all_user()
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
        license = self.user_license.currentText().strip()
        grade = self.user_grade.text().strip()
        machine_serial = self.machine_serial.text().strip()
        if any(key=='' for key in [section, license, grade, machine_serial]):
            self.show_modal("error", parent=self.setting_tab, title=" Empty Field", description="누락된 입력값이 있습니다. 입력된 값을 확인하세요.")
            return
        key_value_pairs = {"license": license, "grade": grade, "machine_serial": machine_serial}
        self.settings.add_section(section, key_value_pairs)
        self.load_config()

    def save_api_settings(self):
        section = "VWORLD_API_SETTINGS"
        api_key = self.api_key_input.text().strip()
        expiring_date = self.expiring_date_input.text().strip()

        if any(key=='' for key in [api_key, expiring_date]):
            self.show_modal("error", parent=self.setting_tab, title=" Empty Field", description="API 키 또는 인증 만료 날짜가 입력되지 않았습니다.")
            return

        key_value_pairs = {"api_key": api_key, "expiring_date": expiring_date}
        self.settings.add_section(section, key_value_pairs)
        self.load_config()
    
    def show_modal(self, modal_type, **kargs):
        """ 메시지 송출 """
        default_settings = {'position': 'bottom-right', 'duration': 2000, 'closeIcon': ':resources/icons/x.svg'}
        modal_collection = {'info':QCustomModals.InformationModal, 
                            'success':QCustomModals.SuccessModal, 
                            'error':QCustomModals.ErrorModal, 
                            'warning':QCustomModals.WarningModal, 
                            'custom':QCustomModals.CustomModal}
        if modal_type not in ['info', 'success', 'error', 'warning', 'custom']: modal_type = 'custom'

        for key, value in kargs.items():
            default_settings[key] = value    

        modal = modal_collection[modal_type](**default_settings)
        modal.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Settings()
    with open('resources\styles\dialogrenameimage.qss', 'r') as file:
        style_sheet = file.read()
        app.setStyleSheet(style_sheet)

    isAccepted = window.exec()
    if isAccepted == QDialog.Accepted:
        env = EnvironmentManager()
        env.remove_section("CUR_USER")        
        print(env.get_current_user())
        print(env.get_all_user())
    app.quit()
    sys.exit(0)








