import sys
import os
import geopandas as gpd
import pandas as pd
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFileDialog, QPushButton, QLineEdit,
                                QRadioButton, QTableWidget, QToolBar, QComboBox, QButtonGroup, QStyledItemDelegate,
                                QHeaderView, QTableWidgetItem, QStatusBar, QLabel, QAbstractItemDelegate, QFrame, 
                                QCheckBox, QVBoxLayout, QHBoxLayout, QSpacerItem, QDockWidget, QGroupBox, QSizePolicy, QAbstractItemView)
from PySide6.QtCore import Qt, QRect, Signal, QTimer, Slot
from PySide6.QtGui import QFontMetrics, QKeySequence, QPainter, QPen, QColor, QIcon, QAction
import icons_rc
import pickle   
from geometric_search import find_id_within_linearbuffer, find_attributes_containing_point
from shp2report import ReportFromDataframe
from shp2report_callbacks import insert_image, str_add, str_deco, hangul_date, toBL
from cif_converter import CifGeoDataFrame
import pickle
from CodeDownload_codegokr import CodeGoKr
from custom_image_editor import ImageEditor

class CustomToggleButton(QWidget):
    stateChanged = Signal(bool)  # 상태 변경 시그널

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        # 토글 버튼 생성
        self.toggleButton = QPushButton(self)
        self.toggleButton.setCheckable(True)
        self.toggleButton.setFixedSize(90, 40)  # 버튼 크기 조정
        self.toggleButton.toggled.connect(self.onToggle)
        self.toggleButton.setChecked(True)
        self.toggleButton.setStyleSheet("border: none")

        # 레이아웃에 위젯 추가
        layout.addWidget(self.toggleButton)
        layout.setAlignment(Qt.AlignLeft)
        layout.setContentsMargins(0, 0, 0, 0)

    def onToggle(self, checked):
        if checked:
            self.toggleButton.setIcon(QIcon('toggle-off-circle-svgrepo-com.svg'))
            self.toggleButton.setText("테이블 편집")

        else:
            self.toggleButton.setIcon(QIcon('toggle-on-circle-svgrepo-com.svg'))
            self.toggleButton.setText("이미지 편집")
        self.stateChanged.emit(checked)

    def isChecked(self):
        return self.toggleButton.isChecked()

    def setChecked(self, checked):
        self.toggleButton.setChecked(checked)

class CustomTableWidget(QTableWidget):
    item_double_clicked = Signal(int, str, str, str)

    def __init__(self, parent=None):
        super().__init__()        
        self.setMouseTracking(True)
        self.start_item = None
        self.end_item = None
        self.dragging = False
        self.fill_handle_size = 6
        self.drag_rect = None
        self._is_edit_mode = True
        self.itemDoubleClicked.connect(self.on_item_double_clicked)

    @property
    def mode(self):
        return self._is_edit_mode
    @mode.setter
    def set_mode(self, mode: bool):
        self._is_edit_mode = mode

    def on_item_double_clicked(self, item):
        if not self.mode:
            row = item.row()
            num = self.item(row, 0).text()  # 점번호
            path = self.item(row, 18).text()  # 사진파일(경로)
            name = self.item(row, 19).text()  # 사진파일명

            # 신호 발송
            self.item_double_clicked.emit(row, num, path, name)
            print(num, path, name)

    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if item and self.is_on_fill_handle(event.position().toPoint(), item):
            self.start_item = item
            self.dragging = True
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.end_item = self.itemAt(event.position().toPoint())
            if self.end_item:
                self.update_drag_rect()
            self.viewport().update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.dragging = False
            if self.start_item and self.end_item:
                self.fill_items()
            self.drag_rect = None
            self.viewport().update()
        else:
            super().mouseReleaseEvent(event)

    def fill_items(self):
        start_row = self.start_item.row()
        start_col = self.start_item.column()
        end_row = self.end_item.row()
        end_col = self.end_item.column()
        value = self.start_item.text()

        row_step = 1 if start_row < end_row else -1
        col_step = 1 if start_col < end_col else -1        

        for row in range(start_row, end_row + 1 * row_step, row_step):
            for col in range(start_col, end_col + 1 * col_step, col_step):
                if row != start_row or col != start_col:
                    item = self.item(row, col)
                    if not item:
                        item = QTableWidgetItem()
                        item.setTextAlignment(Qt.AlignCenter)
                        self.setItem(row, col, item)
                    item.setText(value)

    def is_on_fill_handle(self, pos, item):
        rect = self.visualItemRect(item)
        handle_rect = QRect(rect.right() - self.fill_handle_size, rect.bottom() - self.fill_handle_size, self.fill_handle_size, self.fill_handle_size)
        return handle_rect.contains(pos)

    def update_drag_rect(self):
        start_rect = self.visualItemRect(self.start_item)
        end_rect = self.visualItemRect(self.end_item)
        self.drag_rect = start_rect.united(end_rect)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        for item in self.selectedItems():
            rect = self.visualItemRect(item)
            handle_rect = QRect(rect.right() - self.fill_handle_size, rect.bottom() - self.fill_handle_size, self.fill_handle_size, self.fill_handle_size)
            painter.fillRect(handle_rect, QColor(0, 0, 0))
        if self.drag_rect:
            painter.setPen(QColor(0, 0, 255))
            painter.drawRect(self.drag_rect)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            self.copySelection()
        elif event.matches(QKeySequence.Paste):
            self.pasteSelection()
        elif event.key() == Qt.Key_Delete:
            self.deleteSelection()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.state() != QAbstractItemView.EditingState:
                # 딜레이를 주어 편집 모드로 진입
                QTimer.singleShot(100, lambda: self.editItem(self.currentItem()))
            else:
                self.moveToNextCell() 
        else:
            super().keyPressEvent(event)

    def copySelection(self):
        selection = self.selectedRanges()
        if selection:
            rows = sorted(range(selection[0].topRow(), selection[0].bottomRow() + 1))
            columns = sorted(range(selection[0].leftColumn(), selection[0].rightColumn() + 1))
            rowcount = len(rows)
            colcount = len(columns)
            table = [[''] * colcount for _ in range(rowcount)]
            for i, row in enumerate(rows):
                for j, col in enumerate(columns):
                    item = self.item(row, col)
                    table[i][j] = item.text() if item else ''
            stream = '\n'.join(['\t'.join(row) for row in table])
            QApplication.clipboard().setText(stream)

    def pasteSelection(self):
        clipboard = QApplication.clipboard()
        if clipboard.mimeData().hasText():
            text = clipboard.text()
            rows = text.split('\n')
            selected = self.selectedRanges()
            if selected:
                start_row = selected[0].topRow()
                start_col = selected[0].leftColumn()
                for i, row in enumerate(rows):
                    columns = row.split('\t')
                    for j, column in enumerate(columns):
                        if start_row + i < self.rowCount() and start_col + j < self.columnCount():
                            self.setCellItemAligned(start_row + i, start_col + j, column)

    def setCellItemAligned(self, row, column, value, align=Qt.AlignCenter):
        item = QTableWidgetItem(str(value))
        item.setTextAlignment(align)
        self.setItem(row, column, item)
                
    def deleteSelection(self):
        for item in self.selectedItems():
            item.setText("")

    def moveToNextCell(self):
        current = self.currentItem()
        if current:
            row = current.row()
            col = current.column()
            if row + 1 < self.rowCount():
                next_item = self.item(row+1, col)
            else:
                next_item = self.item(0, col+1)

            if next_item:
                self.setCurrentItem(next_item)
                 # 딜레이를 주어 편집 모드로 진입
                QTimer.singleShot(100, lambda: self.editItem(self.currentItem()))
    
    def get_column_header(self) -> list:
        return [self.horizontalHeaderItem(i).text() for i in range(self.columnCount())]

    def set_column_value(self, columnname, value):
        headers = self.get_column_header()
        col = headers.index(columnname)
        for row in range(self.rowCount()):
            self.setCellItemAligned(row, col, value)

    def hide_columns(self, column_names):
        """주어진 컬럼명을 기반으로 컬럼을 숨기는 함수"""
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            if header_item and header_item.text() in column_names:
                self.setColumnHidden(col, True)  # 컬럼 숨기기
    
    def show_all_columns(self):
        """모든 숨겨진 컬럼을 표시하는 함수"""
        for col in range(self.columnCount()):
            self.setColumnHidden(col, False)  # 모든 컬럼 숨김 해제

class AutoResizeDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(AutoResizeDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        option.font.setPointSize(self.calculateFontSize(option, index))
        super(AutoResizeDelegate, self).paint(painter, option, index)

    def calculateFontSize(self, option, index):
        text = index.data()
        if not text:
            return option.font.pointSize()

        base_size = 10
        font = option.font
        font.setPointSize(base_size)
        metrics = QFontMetrics(font)

        while metrics.horizontalAdvance(text) > option.rect.width() or metrics.height() > option.rect.height():
            base_size -= 1
            font.setPointSize(base_size)
            metrics = QFontMetrics(font)
            if base_size <= 1:
                break

        return base_size

class QCcpManager(QMainWindow):

    HEADER_LABELS = ['점번호', 'X', 'Y', '도선등급', '도선명', '표지재질', '토지소재(동리)', 
                      '토지소재(지번)', '지적(임야)도', '설치년월일', '조사년월일', '조사자(직)', 
                      '조사자(성명)', '조사내용', '경위도(B)', '경위도(L)', '원점', '표고', '사진파일(경로)', '사진파일명']
    TEMPLATE = 'template.xlsx'

    def __init__(self):
        super().__init__()
        self.image_folder = None
        self.image_extension = ".jpg"
        self.is_same_name = False
        self.mode = "edit-table"   # ['edit-table', 'edit-image']
        self.add_toolbar()
        self.setupUi()
        # self.add_menubar()
        
        self.show()

    def setupUi(self):

        self.button_group = QButtonGroup(self)
        # QDockWidget
        side_container = QWidget()
        side_layout = QVBoxLayout()
        side_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 데이터 입력 ==========
        self.input_data_button = QPushButton(side_container)
        self.input_data_button.setText('데이터 입력')
        self.input_data_button.setCheckable(True)
        side_layout.addWidget(self.input_data_button)
        self.button_group.addButton(self.input_data_button)
        
        # 데이터 입력 - 서브
        input_data_sub = QWidget(side_container)
        input_data_sub.setFixedHeight(100)
        input_data_sub_layout = QVBoxLayout()
        self.tr_dat_button = QPushButton(side_container)
        self.tr_dat_button.setText('tr.dat 입력')
        self.load_project_button = QPushButton(side_container)
        self.load_project_button.setText('기존 프로젝트')
        input_data_sub_layout.addWidget(self.tr_dat_button)
        input_data_sub_layout.addWidget(self.load_project_button)
        input_data_sub_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        input_data_sub.setLayout(input_data_sub_layout)
        input_data_sub.setVisible(False)
        side_layout.addWidget(input_data_sub)
        
        # 공통값 입력 ==========
        self.common_input_button = QPushButton(side_container)
        self.common_input_button.setText('공통값 입력')
        self.common_input_button.setCheckable(True)
        side_layout.addWidget(self.common_input_button)
        self.button_group.addButton(self.common_input_button)

        # 공통값 입력 - 서브
        common_input_sub = QWidget(side_container)
        common_input_sub_layout = QVBoxLayout()
        common_input_sub.setFixedHeight(290)

        self.grade_input = QLineEdit(side_container)
        self.name_input = QLineEdit(side_container)
        self.install_date_input = QLineEdit(side_container)
        self.survey_date_input = QLineEdit(side_container)
        self.surveyor_position_input = QLineEdit(side_container)
        self.surveyor_input = QLineEdit(side_container)
        self.findings_input = QLineEdit(side_container)
        self.origin_input = QLineEdit(side_container)

        self.grade_input.setPlaceholderText('도선등급 ex) 1')
        self.name_input.setPlaceholderText('도선명 ex) 가')
        self.install_date_input.setPlaceholderText('설치년월일 ex) 2020-10-12')
        self.survey_date_input.setPlaceholderText('조사년월일 ex) 2021-02-23')
        self.surveyor_position_input.setPlaceholderText('조사자(직)')
        self.surveyor_input.setPlaceholderText('조사자')
        self.findings_input.setPlaceholderText('조사내용')
        self.origin_input.setPlaceholderText('원점')
        self.origin_input.setText('세계중부')

        common_input_sub_layout.addWidget(self.grade_input)
        common_input_sub_layout.addWidget(self.name_input)
        common_input_sub_layout.addWidget(self.install_date_input)
        common_input_sub_layout.addWidget(self.survey_date_input)
        common_input_sub_layout.addWidget(self.surveyor_position_input)
        common_input_sub_layout.addWidget(self.surveyor_input)
        common_input_sub_layout.addWidget(self.findings_input)
        common_input_sub_layout.addWidget(self.origin_input)

        hlayout1 = QHBoxLayout()
        hspacer1 = QSpacerItem(10,10, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.common_apply_button = QPushButton(side_container)
        self.common_apply_button.setText('적용')
        hlayout1.addItem(hspacer1)
        hlayout1.addWidget(self.common_apply_button)
        common_input_sub_layout.addLayout(hlayout1)
        common_input_sub_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        common_input_sub.setLayout(common_input_sub_layout)
        
        common_input_sub.setVisible(False)
        side_layout.addWidget(common_input_sub)

        # 사진관리 ================
        self.image_management_button = QPushButton(side_container)
        self.image_management_button.setText('사진 관리')
        self.image_management_button.setCheckable(True)
        side_layout.addWidget(self.image_management_button)
        self.button_group.addButton(self.image_management_button)

        # 사진관리 - 서브
        image_management_sub = QWidget(side_container)
        image_management_sub.setFixedHeight(230)
        image_management_sub_layout = QVBoxLayout()

        self.get_image_button = QPushButton(side_container)
        self.get_image_button.setText('사진폴더 선택')
        extension_group = QGroupBox(side_container)
        extension_group.setTitle('확장자')
        vlayout1 = QVBoxLayout()
        self.jpg_radio = QRadioButton('.jpg', extension_group)
        self.jpg_radio.setChecked(True)
        self.jpeg_radio = QRadioButton('.jpeg', extension_group)
        self.png_radio = QRadioButton('.png', extension_group)
        vlayout1.addWidget(self.jpg_radio)
        vlayout1.addWidget(self.jpeg_radio)
        vlayout1.addWidget(self.png_radio)
        extension_group.setLayout(vlayout1)
        self.same_filename_check = QCheckBox(side_container)
        self.same_filename_check.setText('도근번호 파일명 일치')
        hlayout2 = QHBoxLayout()
        hspacer2 = QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.image_apply_button = QPushButton(side_container)
        self.image_apply_button.setText('적용')
        hlayout2.addItem(hspacer2)
        hlayout2.addWidget(self.image_apply_button)
        
        image_management_sub_layout.addWidget(self.get_image_button)
        image_management_sub_layout.addWidget(extension_group)
        image_management_sub_layout.addWidget(self.same_filename_check)
        image_management_sub_layout.addLayout(hlayout2)
        image_management_sub_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        image_management_sub.setLayout(image_management_sub_layout)
        image_management_sub.setVisible(False)
        side_layout.addWidget(image_management_sub)

        # 토지소재지 입력 ==================
        self.land_data_button = QPushButton(side_container)
        self.land_data_button.setText('토지소재지 입력')
        self.land_data_button.setCheckable(True)
        side_layout.addWidget(self.land_data_button)
        self.button_group.addButton(self.land_data_button)
        
        # 토지소재지 입력 - 서브
        land_data_sub = QWidget(side_container)
        land_data_sub.setFixedHeight(100)
        land_data_sub_layout = QVBoxLayout()
        self.cif_button = QPushButton(side_container)
        self.cif_button.setText('Cif 입력')
        self.shp_button = QPushButton(side_container)
        self.shp_button.setText('Shp 입력')
        land_data_sub_layout.addWidget(self.cif_button)
        land_data_sub_layout.addWidget(self.shp_button)
        land_data_sub_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        land_data_sub.setLayout(land_data_sub_layout)
        
        land_data_sub.setVisible(False)
        side_layout.addWidget(land_data_sub)

        # 내보내기 ==================
        self.export_button = QPushButton(side_container)
        self.export_button.setText('내보내기')
        self.export_button.setCheckable(True)
        side_layout.addWidget(self.export_button)
        self.button_group.addButton(self.export_button)
        
        # 내보내기 - 서브
        export_data_sub = QWidget(side_container)
        export_data_sub.setFixedHeight(100)
        export_data_sub_layout = QVBoxLayout()
        self.export_project_button = QPushButton(side_container)
        self.export_project_button.setText('프로젝트 저장')
        self.export_xlsx_button = QPushButton(side_container)
        self.export_xlsx_button.setText('성과표 엑셀저장')
        export_data_sub_layout.addWidget(self.export_project_button)
        export_data_sub_layout.addWidget(self.export_xlsx_button)
        export_data_sub_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        export_data_sub.setLayout(export_data_sub_layout)
        export_data_sub.setVisible(False)
        side_layout.addWidget(export_data_sub)
        side_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.button_group.setExclusive(True)
        side_container.setLayout(side_layout)
        self.sidemenu = self.add_dockableWidget("테이블 입력", side_container, 600)

        self.input_data_button.toggled.connect(input_data_sub.setVisible)
        self.common_input_button.toggled.connect(common_input_sub.setVisible)
        self.image_management_button.toggled.connect(image_management_sub.setVisible)
        self.land_data_button.toggled.connect(land_data_sub.setVisible)
        self.export_button.toggled.connect(export_data_sub.setVisible)

        #### main widget
        main_frame = QFrame(self)
        main_frame_layout = QHBoxLayout()

        # custom table widget
        self.table_widget = CustomTableWidget(self)
        
        self.table_widget.setColumnCount(len(self.HEADER_LABELS))
        self.table_widget.setRowCount(5)
        self.table_widget.setHorizontalHeaderLabels(self.HEADER_LABELS)
        self.table_widget.setWordWrap(False)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_widget.setStyleSheet("QHeaderView::section { background-color: lightgray; border: 1px solid white; }")
        self.table_widget.verticalHeader().hide()

        # AutoResizeDelegate 설정
        delegate = AutoResizeDelegate(self.table_widget)
        self.table_widget.setItemDelegate(delegate)        
        self.table_widget.setContextMenuPolicy(Qt.NoContextMenu)
        self.alignAllCellsCenter()

        ## image editor widget
        self.image_editor_frame = QFrame(self)
        image_editor_frame_layout = QHBoxLayout()
        self.image_editor = ImageEditor(self.image_editor_frame)
        image_editor_frame_layout.addWidget(self.image_editor)
        self.image_editor_frame.setLayout(image_editor_frame_layout)
        self.image_editor_frame.hide()

        main_frame_layout.addWidget(self.table_widget)
        main_frame_layout.addWidget(self.image_editor_frame)
       
        main_frame.setLayout(main_frame_layout)
        self.setCentralWidget(main_frame)
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)
        self.status_message = QLabel(self)
        self.statusbar.addPermanentWidget(self.status_message)

        # siganl-slot connection
        self.load_project_button.clicked.connect(self.loadProject)
        self.tr_dat_button.clicked.connect(self.getDatFile)
        self.common_apply_button.clicked.connect(self.apply_common_input)
        self.get_image_button.clicked.connect(self.get_image_folder)
        self.jpg_radio.toggled.connect(self.onRadioButtonToggled)
        self.jpeg_radio.toggled.connect(self.onRadioButtonToggled)
        self.png_radio.toggled.connect(self.onRadioButtonToggled)
        self.image_apply_button.clicked.connect(self.apply_image_settings)
        self.cif_button.clicked.connect(lambda: self.setLocation("cif"))
        self.shp_button.clicked.connect(lambda: self.setLocation("shp"))
        self.export_project_button.clicked.connect(self.saveProject)
        self.export_xlsx_button.clicked.connect(self.saveToExcel)
        self.table_widget.item_double_clicked.connect(self.on_item_double_clicked)
        self.image_editor.table_update_request.connect(self.on_table_update_request)

        self.change_mode_toggle.stateChanged.connect(self.change_mode)
    
    @Slot(int, str, str, str)
    def on_item_double_clicked(self, row, num, path, name):
        orginal_image = os.path.join(path, name)
        self.status_message.setText(' '.join([num, orginal_image]))
        self.image_editor.open_image_from(orginal_image)
        self.image_editor.table_row = (row, num)

    @Slot(int, str, str)
    def on_table_update_request(self, row, path, filename):
        self.table_widget.setCellItemAligned(row, self._headerindex("사진파일(경로)"), path)
        self.table_widget.setCellItemAligned(row, self._headerindex("사진파일명"), filename)


    def alignAllCellsCenter(self):
        for row in range(self.table_widget.rowCount()):
            for col in range(self.table_widget.columnCount()):
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter)
                self.table_widget.setItem(row, col, item)

    def add_menubar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('파일')

        new_action = QAction(QIcon(':/icons/document-add-svgrepo-com.svg'), '새 문서', self)
        # new_action.triggered.connect(self.new_document)
        file_menu.addAction(new_action)

        open_action = QAction(QIcon(':/icons/album-svgrepo-com.svg'), '열기', self)
        # open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)

        save_action = QAction(QIcon(':/icons/diskette-svgrepo-com.svg'), '저장', self)
        # save_action.triggered.connect(self.save_image)
        file_menu.addAction(save_action)

        view_menu = menubar.addMenu('보기')
        self.show_layer_action = QAction(QIcon(':/icons/layers-svgrepo-com.svg'), '레이어', self)
        # self.show_layer_action.triggered.connect(self.show_layer_win)
        self.show_layer_action.setEnabled(False)
        self.show_explorer_action = QAction(QIcon(':/icons/library-svgrepo-com.svg'), "탐색기", self)
        # self.show_explorer_action.triggered.connect(self.show_explorer_win)
        self.show_explorer_action.setEnabled(False)
        self.show_preview_action = QAction(QIcon(':/icons/gallery-svgrepo-com.svg'), "미리보기", self)
        # self.show_preview_action.triggered.connect(self.show_preview_win)
        self.show_preview_action.setEnabled(False)
        view_menu.addAction(self.show_layer_action)
        view_menu.addAction(self.show_explorer_action)
        view_menu.addAction(self.show_preview_action)

    def change_mode(self):
        if self.change_mode_toggle.isChecked():
            self.mode = "edit-table"
            self.sidemenu.show()
            self.table_widget.set_mode = True
            self.image_editor_frame.setHidden(True)
            self.table_widget.setSelectionBehavior(QAbstractItemView.SelectItems)
            self.table_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
            self.table_widget.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
            self.table_widget.show_all_columns()
            self.table_widget.setMinimumWidth(0)
            self.table_widget.setMaximumWidth(16777215)
        else:
            self.mode = "edit-image"
            self.sidemenu.hide()
            self.table_widget.set_mode = False
            self.image_editor_frame.setVisible(True)
            self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
            self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers) 
            self.table_widget.hide_columns(['X', 'Y', '도선등급', '도선명', '표지재질', '토지소재(동리)', '토지소재(지번)', '지적(임야)도', '설치년월일', '조사년월일', '조사자(직)', '조사자(성명)', '조사내용', '경위도(B)', '경위도(L)', '원점', '표고'])
            self.table_widget.setColumnWidth(self.table_widget.get_column_header().index("사진파일(경로)"), 350)
            table_size = sum([self.table_widget.columnWidth(col) for col in range(self.table_widget.columnCount()) if self.table_widget.isColumnHidden(col) == False])
            self.table_widget.setFixedWidth(table_size)


    def add_toolbar(self):
        self.toolbar = QToolBar()
        self.toolbar.setWindowTitle('MainToolbar')
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
        
        # 툴바 아이콘 추가
        new_action = QAction(QIcon(':/icons/document-add-svgrepo-com.svg'), '새 문서', self)
        # new_action.triggered.connect(self.new_document)
        self.toolbar.addAction(new_action)

        open_action = QAction(QIcon(':/icons/album-svgrepo-com.svg'), '열기', self)
        # open_action.triggered.connect(self.open_image)
        self.toolbar.addAction(open_action)

        save_action = QAction(QIcon(':/icons/diskette-svgrepo-com.svg'), '저장', self)
        # save_action.triggered.connect(self.save_image)
        self.toolbar.addAction(save_action)

        self.change_mode_toggle = CustomToggleButton()
        self.toolbar.addWidget(self.change_mode_toggle)

    def load_table_from_pickle(self, table_widget: QTableWidget, file_path: str):
        try:
            # pickle 파일에서 데이터 로드
            with open(file_path, mode='rb') as file:
                data = pickle.load(file)

            # QTableWidget 초기화
            table_widget.setRowCount(0)  # 기존 데이터 초기화
            table_widget.setColumnCount(0)

            # 데이터가 비어있지 않은 경우
            if data:
                # 열 수 설정
                column_count = len(data[0])
                table_widget.setColumnCount(column_count)

                # 헤더 설정
                headers = list(data[0].keys())
                table_widget.setHorizontalHeaderLabels(headers)

                # 데이터 추가
                for row_data in data:
                    row_index = table_widget.rowCount()
                    table_widget.insertRow(row_index)
                    for column_index, header in enumerate(headers):
                        item = QTableWidgetItem(row_data[header] if row_data[header] is not None else "")
                        table_widget.setItem(row_index, column_index, item)
                        item.setTextAlignment(Qt.AlignCenter)
            
            self.status_message.setText(f"파일이 성공적으로 로드되었습니다: {file_path}")

        except Exception as e:
            self.status_message.setText(f"파일 로드 중 오류 발생: {e}")    

    def loadProject(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Load project", "", "Pickle Files (*.pickle)", options=options)
        if fileName:
            self.load_table_from_pickle(self.table_widget, fileName)

    def save_table_to_pickle(self, table_widget: QTableWidget, file_path: str):
        try:
            data = []
            row_count = table_widget.rowCount()
            column_count = table_widget.columnCount()

            # 헤더 가져오기
            headers = []
            for column in range(column_count):
                headers.append(table_widget.horizontalHeaderItem(column).text())

            # 데이터 가져오기
            for row in range(row_count):
                row_data = {}
                for column in range(column_count):
                    item = table_widget.item(row, column)
                    if item is not None:
                        row_data[headers[column]] = item.text()
                    else:
                        row_data[headers[column]] = None  # 빈 셀은 None으로 설정
                data.append(row_data)

            # pickle 파일로 저장
            with open(file_path, mode='wb') as file:
                pickle.dump(data, file)

            self.status_message.setText(f"파일이 성공적으로 저장되었습니다: {file_path}")
        except Exception as e:
            self.status_message.setText(f"파일 저장 중 오류 발생: {e}") 
    
    def getDatFile(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Open TR.DAT File", "", "DAT Files (*.dat);;All Files (*)", options=options)
        if fileName:
            self.loadDataToTable(fileName)
            self.status_message.setText(f"파일이 성공적으로 로드되었습니다: {fileName}")

    def loadDataToTable(self, fileName):
        with open(fileName, 'r') as file:
            lines = file.readlines()            
        self.rowCount = len(lines)
        self.table_widget.setRowCount(self.rowCount)
        
        for row, line in enumerate(lines):
            # line에 있는 중복된 공백을 공백하나로 합치고 tab으로 변경
            while True:
                if "  " in line:
                    line = line.replace("  ",' ')
                else:
                    break
            line = line.replace(' ', '\t')

            data = line.strip().split('\t')
            if len(data) >= 3:
                self.table_widget.setCellItemAligned(row, 0, data[0])  # 점번호
                self.table_widget.setCellItemAligned(row, 1, f"{float(data[1])/100:.2f}")  # X
                self.table_widget.setCellItemAligned(row, 2, f"{float(data[2])/100:.2f}")  # Y
                # 나머지는 빈 문자
                for i in range(3, self.table_widget.columnCount()+1):
                    self.table_widget.setCellItemAligned(row, i, '')

    def apply_common_input(self):
        grade = self.grade_input.text()
        name = self.name_input.text()
        install_date = self.install_date_input.text()
        survey_date = self.survey_date_input.text()        
        surveyor_position = self.surveyor_position_input.text()
        surveyor = self.surveyor_input.text()
        findings = self.findings_input.text()
        origin = self.origin_input.text()

        input_data = {'도선등급': grade, '도선명': name, '설치년월일': install_date, '조사년월일': survey_date, 
                      "조사자(직)": surveyor_position, "조사자(성명)": surveyor, "조사내용": findings, "원점": origin}

        for k, v in input_data.items():
            self.table_widget.set_column_value(k, v)
        
        self.status_message.setText('공통값 입력을 완료했습니다.')

    def get_image_folder(self):
        image_path = QFileDialog.getExistingDirectory(self, "Image Path")
        if image_path:
            self.image_folder = image_path

    def onRadioButtonToggled(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            self.image_extension = radioButton.text()
            self.status_message.setText(f'{self.image_extension}를 확장자로 선택했습니다.')

    def apply_image_settings(self):
        if self.image_folder:
            self.table_widget.set_column_value("사진파일(경로)", self.image_folder)
        if self.same_filename_check.isChecked():
            for row in range(self.table_widget.rowCount()):
                num = self.table_widget.item(row, 0).text()
                self.table_widget.setCellItemAligned(row, self._headerindex("사진파일명"), ''.join([num, self.image_extension]))
        self.status_message.setText("사진정보를 갱신하였습니다.")

    def setLocation(self, kind_of_db):
        db_file = {'cif': 'Cif Files (*.cif)', 'shp': 'Esri Shp File (*.shp)'}

        jijuk, _ = QFileDialog.getOpenFileName(self,"Get Jijuk DB", "", f"{db_file.get(kind_of_db.lower())};;All Files (*)")
        try:
            if jijuk:
                if jijuk.lower().endswith(".cif"):
                    gdf = CifGeoDataFrame(jijuk).convert_to_geodataframe()
                if jijuk.lower().endswith(".shp"):
                    gdf = gpd.read_file(jijuk, encoding='euc-kr')
                
                if gdf is None: 
                    return
                
                for i in range(self.table_widget.rowCount()):
                    location = find_attributes_containing_point(gdf, (float(self.table_widget.item(i,2).text()), float(self.table_widget.item(i,1).text())), ["PNU", "JIBUN", "DOM"])
                    if not location is None:
                        pnu, jibun, dom = location.iloc[0, :]
                        self.table_widget.item(i, 6).setText(self.get_district_name(pnu))
                        self.table_widget.item(i, 7).setText(self.only_jibun(jibun))
                        self.table_widget.item(i, 8).setText(self.dom_to_doho(dom))    
                self.status_message.setText("주소검색을 마쳤습니다. 미작성된 소재지를 확인하세요.")
        except Exception as e:
            self.status_message.setText(str(e))
    
    def get_district_name(self, pnulike:str) -> str:
        cif_loader = CifGeoDataFrame()
        return cif_loader.getDistrictName(pnulike=pnulike)
    
    def dom_to_doho(self, dom):
        j_dom, _ = dom.split('/')
        return j_dom[1:-1]
    
    def only_jibun(self, jibun):
        jibun = jibun.replace(" ", "").strip()
        if not jibun[-1].isdigit():
            return jibun[:-1]
        return jibun

    def saveProject(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self, "Save project", "", "Pickle Files (*.pickle)", options=options)
        if fileName:
            self.save_table_to_pickle(self.table_widget, fileName)
            self.status_message.setText(f"파일이 성공적으로 저장되었습니다: {fileName}")

    def tablewidget_to_dataframe(self, table_widget: QTableWidget) -> pd.DataFrame:
        rows = table_widget.rowCount()
        columns = table_widget.columnCount()
        
        data = {}
        for column in range(columns):
            header = table_widget.horizontalHeaderItem(column).text()
            data[header] = []
            for row in range(rows):
                item = table_widget.item(row, column)
                data[header].append(item.text() if item else "")
        
        return pd.DataFrame(data)   

    def saveToExcel(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Excel File", "", "Excel Files (*.xlsx)")
        if fileName:
            table_df = self.tablewidget_to_dataframe(self.table_widget)
            table_df.fillna("", inplace=True)
            border_settings =[{"rng": "A3:AF25","edges": ["all"], "border_style": "hair", "reset": True },  
                            {"rng": "A3:AF25","edges": ["outer"], "border_style": "thin",  "reset": False },
                            {"rng": "A3:A4","edges": ["inner_horizontal"], "border_style": None,  "reset": False },
                            {"rng": "A6:A7","edges": ["inner_horizontal"], "border_style": None, "reset": False }, 
                            {"rng": "A16:AF19","edges": ["inner_vertical"], "border_style": None, "reset": False },
                            {"rng": "A16:AF19","edges": ["inner_horizontal"], "border_style": None, "reset": False },
                            {"rng": "B8:AF9","edges": ["inner_horizontal"], "border_style": None, "reset": False },
                            {"rng": "B10:AF11","edges": ["inner_horizontal"], "border_style": None, "reset": False },
                            {"rng": "B12:AF13","edges": ["inner_horizontal"], "border_style": None, "reset": False },
                            {"rng": "N14:AF15","edges": ["inner_horizontal"], "border_style": None, "reset": False },
                            {"rng": "N3:S4","edges": ["inner_vertical"], "border_style": None, "reset": False }
            ]
            mappings = [ {'fields': '점번호', 'address': 'B3', "callback":str_deco, 'kargs':{"postfix":"번"}},
                        {'fields': '도선등급', 'address': 'G3', "callback":str_deco, 'kargs':{"postfix":"등"}},
                        {'fields': '도선명', 'address': 'N3'},
                        {'fields': '표지재질', 'address': 'Z3'},
                        {'fields':['토지소재(동리)', '토지소재(지번)'], 'address': 'B5', 'callback': str_add, 'kargs':{'delim': ' ', 'postfix': "번지"}},  
                        {'fields': '지적(임야)도', 'address': 'Z5', "callback":str_deco, 'kargs':{"postfix":"호"}},
                        {'fields': '설치년월일', 'address': 'A8', 'callback': hangul_date},
                        {'fields': 'X', 'address': 'B9'},
                        {'fields': 'Y', 'address': 'F9'},
                        {'fields': '경위도(B)', 'address': 'M9', 'callback':toBL},
                        {'fields': '경위도(L)', 'address': 'W9', 'callback':toBL},
                        {'fields': '원점', 'address': 'B14'},
                        {'fields': '표고', 'address': 'N15'},
                        {'fields': '조사년월일', 'address': 'A22', 'callback': hangul_date},
                        {'fields': '조사자(직)', 'address': 'B22'},
                        {'fields': '조사자(성명)', 'address': 'F22'},
                        {'fields': '조사내용', 'address': 'L22'},
                        {'fields': ['사진파일(경로)', '사진파일명'], 'address': "A17:AF19", 'callback': insert_image, 'kargs':{'keep_ratio': True}}
            ]  ## insert image

            repoter = ReportFromDataframe(template='template.xlsx', sheetname='서식', savefile=fileName, dataframe=table_df, 
                                          max_row=26, border_settings=border_settings, mappings=mappings)
            repoter.report()
            self.status_message.setText(f"성과표가 성공적으로 저장되었습니다: {fileName}")

    def add_dockableWidget(self, title:str, wdg:QWidget, maxheight:int=0):
        dock = QDockWidget(title, self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        dock.setWidget(wdg)
        dock.setMaximumHeight(maxheight)
        dock.setMinimumWidth(180)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)    
        return dock    

    def _headerindex(self, label:str) -> int:
        return self.HEADER_LABELS.index(label)


if __name__ == "__main__":
    app=QApplication(sys.argv)
    ex = QCcpManager()
    sys.exit(app.exec())