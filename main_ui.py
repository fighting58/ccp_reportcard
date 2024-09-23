import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QDialog, QPushButton, QLineEdit,
                                QRadioButton, QTableWidget, QToolBar, QComboBox, QButtonGroup,
                                QCheckBox, QVBoxLayout, QHBoxLayout, QSpacerItem, QDockWidget, QGroupBox, QSizePolicy, QAbstractItemView)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QFontMetrics, QKeySequence, QPainter, QPen, QColor, QIcon, QAction
import icons_rc

class CustomTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setMouseTracking(True)
        self.start_item = None
        self.end_item = None
        self.dragging = False
        self.fill_handle_size = 6
        self.drag_rect = None

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
            if col + 1 < self.columnCount():
                next_item = self.item(row, col + 1)
            else:
                next_item = self.item(row + 1, 0)
            if next_item:
                self.setCurrentItem(next_item)
                self.editItem(next_item)


class QCcpManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_extension = ".jpg"
        self.is_same_name = False
        self.add_toolbar()
        self.setupUi()
        # self.add_menubar()
        

        self.show()

    def setupUi(self):

        self.button_group = QButtonGroup(self)
        # QDockWidget
        side_container = QWidget()
        side_layout = QVBoxLayout()

        # 데이터 입력 ==========
        self.input_data_button = QPushButton(side_container)
        self.input_data_button.setText('데이터 입력')
        self.input_data_button.setCheckable(True)
        side_layout.addWidget(self.input_data_button)
        self.button_group.addButton(self.input_data_button)
        
        # 데이터 입력 - 서브
        input_data_sub = QWidget(side_container)
        input_data_sub_layout = QVBoxLayout()
        self.tr_dat_button = QPushButton(side_container)
        self.tr_dat_button.setText('tr.dat 입력')
        self.load_project_button = QPushButton(side_container)
        self.load_project_button.setText('기존 프록젝트')
        input_data_sub_layout.addWidget(self.tr_dat_button)
        input_data_sub_layout.addWidget(self.load_project_button)
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

        self.grade_input = QLineEdit(side_container)
        self.name_input = QLineEdit(side_container)
        self.install_input = QLineEdit(side_container)
        self.survey_input = QLineEdit(side_container)
        self.surveyor_position_input = QLineEdit(side_container)
        self.surveyor_input = QLineEdit(side_container)
        self.findings_input = QLineEdit(side_container)
        self.origin_input = QLineEdit(side_container)

        self.grade_input.setPlaceholderText('도선등급 ex) 1')
        self.name_input.setPlaceholderText('도선명 ex) 가')
        self.install_input.setPlaceholderText('설치년월일 ex) 2020-10-12')
        self.survey_input.setPlaceholderText('조사년월일 ex) 2021-02-23')
        self.surveyor_position_input.setPlaceholderText('조사자(직)')
        self.surveyor_input.setPlaceholderText('조사자')
        self.findings_input.setPlaceholderText('조사내용')
        self.origin_input.setText('세계중부')

        common_input_sub_layout.addWidget(self.grade_input)
        common_input_sub_layout.addWidget(self.name_input)
        common_input_sub_layout.addWidget(self.install_input)
        common_input_sub_layout.addWidget(self.survey_input)
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
        common_input_sub.setLayout(common_input_sub_layout)
        
        common_input_sub.setVisible(False)
        side_layout.addWidget(common_input_sub)

        # 사진관리 ================
        self.picture_management_button = QPushButton(side_container)
        self.picture_management_button.setText('사진 관리')
        self.picture_management_button.setCheckable(True)
        side_layout.addWidget(self.picture_management_button)
        self.button_group.addButton(self.picture_management_button)

        # 사진관리 - 서브
        picture_management_sub = QWidget(side_container)
        picture_management_sub_layout = QVBoxLayout()

        self.get_picture_button = QPushButton(side_container)
        self.get_picture_button.setText('사진폴더 선택')
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
        hspacer2 = QSpacerItem(10,10, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.picture_apply_button = QPushButton(side_container)
        self.picture_apply_button.setText('적용')
        hlayout2.addItem(hspacer2)
        hlayout2.addWidget(self.picture_apply_button)

        picture_management_sub_layout.addWidget(self.get_picture_button)
        picture_management_sub_layout.addWidget(extension_group)
        picture_management_sub_layout.addWidget(self.same_filename_check)
        picture_management_sub_layout.addLayout(hlayout2)
        picture_management_sub.setLayout(picture_management_sub_layout)
        picture_management_sub.setVisible(False)
        side_layout.addWidget(picture_management_sub)

        # 토지소재지 입력 ==================
        self.land_data_button = QPushButton(side_container)
        self.land_data_button.setText('토지소재지 입력')
        self.land_data_button.setCheckable(True)
        side_layout.addWidget(self.land_data_button)
        self.button_group.addButton(self.land_data_button)
        
        # 토지소재지 입력 - 서브
        land_data_sub = QWidget(side_container)
        land_data_sub_layout = QVBoxLayout()
        self.cif_button = QPushButton(side_container)
        self.cif_button.setText('Cif 입력')
        self.shp_button = QPushButton(side_container)
        self.shp_button.setText('Shp 입력')
        land_data_sub_layout.addWidget(self.cif_button)
        land_data_sub_layout.addWidget(self.shp_button)
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
        export_data_sub_layout = QVBoxLayout()
        self.export_project_button = QPushButton(side_container)
        self.export_project_button.setText('프로젝트 저장')
        self.export_xlsx_button = QPushButton(side_container)
        self.export_xlsx_button.setText('성과표 엑셀저장')
        export_data_sub_layout.addWidget(self.export_project_button)
        export_data_sub_layout.addWidget(self.export_xlsx_button)
        export_data_sub.setLayout(export_data_sub_layout)
        export_data_sub.setVisible(False)
        side_layout.addWidget(export_data_sub)

        self.button_group.setExclusive(True)
        side_container.setLayout(side_layout)
        self.sidemenu = self.add_dockableWidget("테이블 입력", side_container, 450)

        self.input_data_button.toggled.connect(input_data_sub.setVisible)
        self.common_input_button.toggled.connect(common_input_sub.setVisible)
        self.picture_management_button.toggled.connect(picture_management_sub.setVisible)
        self.land_data_button.toggled.connect(land_data_sub.setVisible)
        self.export_button.toggled.connect(export_data_sub.setVisible)

        self.table_widget = CustomTableWidget()
        self.table_widget.setRowCount(5)
        self.table_widget.setColumnCount(10)
        self.setCentralWidget(self.table_widget)
    

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



    def add_dockableWidget(self, title:str, wdg:QWidget, maxheight:int=0):
        dock = QDockWidget(title, self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        dock.setWidget(wdg)
        dock.setMaximumHeight(maxheight)
        dock.setMinimumWidth(200)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)    
        return dock    


if __name__ == "__main__":
    app=QApplication(sys.argv)
    ex = QCcpManager()
    sys.exit(app.exec())