import os
import sys

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics, QKeySequence
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QCheckBox,
                             QDialog, QDialogButtonBox, QFileDialog, QFrame,
                             QGroupBox, QHBoxLayout, QHeaderView, QLabel,
                             QLineEdit, QMainWindow, QPushButton, QRadioButton,
                             QStyledItemDelegate, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget)

from searchFromDB import NotDecodingError, find_features_containing_point
from shp2report import ReportFromDataframe
from shp2report_callbacks import insert_image, str_add


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


class CommonInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):

        layout = QVBoxLayout(self)
        self.setWindowTitle("공통값 입력")
        self.texts = ["도선등급", "도선명", "설치년월일", "조사년월일", "조사자(직)", "조사자(성명)", "조사내용"]
        self.labels = []
        self.inputs = []
        self.setFixedSize(210, 220)

        for text in self.texts:
            hlayout = QHBoxLayout()
            label = QLabel(text)
            label.setFixedWidth(70)
            input_value = QLineEdit()
            input_value.setFixedWidth(110)
            hlayout.addWidget(label)
            hlayout.addWidget(input_value)
            self.labels.append(label)
            self.inputs.append(input_value)
            layout.addLayout(hlayout)

        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        layout.addWidget(self.line)

        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout.addWidget(self.buttonBox)

        self.setLayout(layout)  # Set the layout to the dialog itself


class ImagePathDialog(QDialog):
    def __init__(self):
        super().__init__()
        self._imagePath = ''
        self._imageExt = ''
        self.option = None
        
        self.initUI()

    @property
    def imagePath(self):
        return self._imagePath
    
    @imagePath.setter
    def imagePath(self, path):
        self._imagePath = path

    @property
    def imageExt(self):
        return self._imageExt
    
    @imageExt.setter
    def imageExt(self, ext):
        self._imageExt = ext


    def initUI(self):
        self.setWindowTitle("사진 폴더 선택")
        main_layout = QVBoxLayout(self)

        path_frame = QWidget()
        path_layout= QHBoxLayout(path_frame)
        label = QLabel("Image Folder: ", path_frame)
        self.folderInput = QLineEdit(path_frame)
        self.folderInput.setMinimumWidth(200)
        self.folderInput.setPlaceholderText("사진 경로를 입력하세요")
        self.getFolder_but = QPushButton("...")
        self.getFolder_but.setFixedWidth(30)
        self.getFolder_but.clicked.connect(self.getPicPath)

        path_layout.addWidget(label)
        path_layout.addWidget(self.folderInput)
        path_layout.addWidget(self.getFolder_but)
        path_frame.setLayout(path_layout)

        self.option_check = QCheckBox("점 번호와 같도록 자동으로 파일명을 입력합니다.",  self)
        self.option_check.toggled.connect(self.onCheckToggled)       

        self.ext_group = QGroupBox("확장자 선택")
        self.ext_group.setEnabled(False)
        ext_layout = QHBoxLayout(self.ext_group)
        ext_list = ['jpg', 'jpeg', 'png', 'bmp']
        self.radioButtons =[]
        for ext in ext_list:
            radioBut = QRadioButton(ext, self.ext_group)
            radioBut.toggled.connect(self.onRadioToggled)
            ext_layout.addWidget(radioBut)
            self.radioButtons.append(radioBut)
        
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        main_layout.addWidget(path_frame)
        main_layout.addWidget(self.option_check)
        main_layout.addWidget(self.ext_group)
        main_layout.addWidget(self.buttonBox)

        self.setLayout(main_layout)


    def getPicPath(self):
        image_path = QFileDialog.getExistingDirectory(self, "Image Path")
        if image_path:
            self.folderInput.setText(image_path)
            self.imagePath = image_path

    def onRadioToggled(self):
        for btn in self.radioButtons:
            if btn.isChecked():
                self.imageExt = btn.text() 
                break

    def onCheckToggled(self):
        self.option = False
        self.option_check.setEnabled(False)
        if self.option_check.isChecked():
            self.ext_group.setEnabled(True)
            self.option = True


class MyApp(QMainWindow):

    HEADER_LABELS = ['점번호', 'X', 'Y', '도선등급', '도선명', '표지재질', '토지소재(동리)', 
                          '토지소재(지번)', '지적(임야)도', '설치년월일', '조사년월일', '조사자(직)', 
                          '조사자(성명)', '조사내용', '경위도(B)', '경위도(L)', '표고', '사진파일(경로)', '사진파일명']
    TEMPLATE = 'template.xlsx'

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('MainWindow')
        self.setGeometry(300,300, 300,300)
        # self.showMaximized()
        self.rowCount = 5

        layout = QVBoxLayout()

        self.getDat_but = QPushButton("tr.dat", self)
        self.getDat_but.clicked.connect(self.getDatFile)

        self.commonInput_but = QPushButton("공통값 입력", self)
        self.commonInput_but.clicked.connect(self.showCommonInputDialog)

        self.pic_path_but = QPushButton("이미지 경로 입력", self)
        self.pic_path_but.clicked.connect(self.showImagePathDialog)

        self.jijuk_btn = QPushButton("토지소재지 입력(cif, shp)", self)
        self.jijuk_btn.clicked.connect(self.setLocation)

        self.report_btn = QPushButton("엑셀로 저장", self)
        self.report_btn.clicked.connect(self.saveToExcel)

        self.tableWidget = QTableWidget(self)
        
        self.tableWidget.setColumnCount(len(self.HEADER_LABELS))
        self.tableWidget.setRowCount(self.rowCount)
        self.tableWidget.setHorizontalHeaderLabels(self.HEADER_LABELS)
        self.tableWidget.setWordWrap(False)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tableWidget.setStyleSheet("QHeaderView::section { background-color: lightgray; border: 1px solid white; }")
        self.tableWidget.verticalHeader().hide()

        # AutoResizeDelegate 설정
        self.delegate = AutoResizeDelegate(self.tableWidget)
        self.tableWidget.setItemDelegate(self.delegate)

        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.tableWidget.setContextMenuPolicy(Qt.NoContextMenu)

        self.alignAllCellsCenter()

        layout.addWidget(self.getDat_but)
        layout.addWidget(self.commonInput_but)
        layout.addWidget(self.pic_path_but)
        layout.addWidget(self.jijuk_btn)
        layout.addWidget(self.report_btn)
        layout.addWidget(self.tableWidget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.show()

    def showCommonInputDialog(self):
        dialog = CommonInputDialog(self)
        if dialog.exec() == QDialog.Accepted:
            commoninput = {k:v.text() for k, v in zip(dialog.texts, dialog.inputs)}
            
            for k, v in commoninput.items():
                for row in range(self.rowCount):
                    self.setCellItemAligned(row, self._headerindex(k), v)
    
    def showImagePathDialog(self):
        dialog = ImagePathDialog()
        if dialog.exec() == QDialog.Accepted:
            path = dialog.imagePath
            ext = dialog.imageExt
            option = dialog.option
            for row in range(self.rowCount):
                self.setCellItemAligned(row, self._headerindex("사진파일(경로)"), path)
                if option:
                    num = self.tableWidget.item(row, 0).text()
                    self.setCellItemAligned(row, self._headerindex("사진파일명"), '.'.join([num, ext]))
    #######################

    def setLocation(self):
        jijuk, _ = QFileDialog.getOpenFileName(self,"Get Jijuk DB", "", "Cif Files (*.cif);;Shp Files (*.shp);;All Files (*)")
        if jijuk:
            if jijuk.lower().endswith(".cif"):
                ...

            if jijuk.lower().endswith(".shp"):
                ...

    def saveToExcel(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Excel File", "", "Excel Files (*.xlsx)")
        if fileName:
            table_df = self.tablewidget_to_dataframe(self.tableWidget)
            table_df["사진파일(경로))"] = "."
            table_df["사진파일명"] = "_abcd.jpg"
            table_df.fillna("", inplace=True)
            border_settings =[{"rng": "A3:AF24","edges": ["all"], "border_style": "hair", "reset": True },  
                            {"rng": "A3:AF24","edges": ["outer"], "border_style": "thin",  "reset": False },
                            {"rng": "A3:A4","edges": ["inner_horizontal"], "border_style": None,  "reset": False },
                            {"rng": "A6:A7","edges": ["inner_horizontal"], "border_style": None, "reset": False },  
                            {"rng": "A17:AF17","edges": ["inner_vertical"], "border_style": None, "reset": False },
                            {"rng": "B8:AF9","edges": ["inner_horizontal"], "border_style": None, "reset": False },
                            {"rng": "B10:AF11","edges": ["inner_horizontal"], "border_style": None, "reset": False },
                            {"rng": "B12:AF13","edges": ["inner_horizontal"], "border_style": None, "reset": False },
                            {"rng": "L3:M4","edges": ["right"], "border_style": None, "reset": False }
            ]
            mappings = [ {'fields': '점번호', 'address': 'B3'},
                        {'fields': '도선등급', 'address': 'G3'},
                        {'fields': '도선명', 'address': 'L3'},
                        {'fields': '표지재질', 'address': 'Z3'},
                        {'fields':['토지소재(동리)', '토지소재(지번)'], 'address': 'B5', 'callback': str_add, 'kargs':{'delim': ' '}},  
                        {'fields': '지적(임야)도', 'address': 'Z5'},
                        {'fields': '설치년월일', 'address': 'A8'},
                        {'fields': 'X', 'address': 'B9'},
                        {'fields': 'Y', 'address': 'E9'},
                        {'fields': '경위도(B)', 'address': 'K9'},
                        {'fields': '경위도(L)', 'address': 'V9'},
                        {'fields': '표고', 'address': 'L15'},
                        {'fields': '조사년월일', 'address': 'A21'},
                        {'fields': '조사자(직)', 'address': 'B21'},
                        {'fields': '조사자(성명)', 'address': 'E21'},
                        {'fields': '조사내용', 'address': 'J21'},
                        {'fields': ['사진파일(경로)', '사진파일명'], 'address': "A17:AF18", 'callback': insert_image, 'kargs':{'keep_ratio': True}}
            ]  ## insert image

            repoter = ReportFromDataframe(template='template.xlsx', sheetname='서식', savefile=fileName, dataframe=table_df, max_row=25, border_settings=border_settings, mappings=mappings)
            repoter.report()
            print("report exported")


    def tablewidget_to_dataframe(self, table_widget: QTableWidget) -> pd.DataFrame:
        rows = table_widget.rowCount()
        columns = table_widget.columnCount()
        
        data = {}
        for column in range(columns):
            header = table_widget.horizontalHeaderItem(column).text()
            data[header] = []
            for row in range(rows):
                item = table_widget.item(row, column)
                data[header].append(item.text() if item else None)
        
        return pd.DataFrame(data)           

    def _headerindex(self, label:str) -> int:
        return self.HEADER_LABELS.index(label)

    def setCellItemAligned(self, row, column, value, align=Qt.AlignCenter):
        item = QTableWidgetItem(str(value))
        item.setTextAlignment(align)
        self.tableWidget.setItem(row, column, item)

    def alignAllCellsCenter(self):
        for row in range(self.tableWidget.rowCount()):
            for col in range(self.tableWidget.columnCount()):
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, col, item)

    def getDatFile(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Open TR.DAT File", "", "DAT Files (*.dat);;All Files (*)", options=options)
        if fileName:
            self.loadDataToTable(fileName)

    def loadDataToTable(self, fileName):
        with open(fileName, 'r') as file:
            lines = file.readlines()
        self.rowCount = len(lines)
        self.tableWidget.setRowCount(self.rowCount)
        
        for row, line in enumerate(lines):
            data = line.strip().split('\t')
            if len(data) >= 3:
                self.setCellItemAligned(row, 0, data[0])  # 점번호
                self.setCellItemAligned(row, 1, f"{float(data[1])/100:.2f}")  # X
                self.setCellItemAligned(row, 2, f"{float(data[2])/100:.2f}")  # Y

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
        selection = self.tableWidget.selectedRanges()
        if selection:
            rows = sorted(range(selection[0].topRow(), selection[0].bottomRow() + 1))
            columns = sorted(range(selection[0].leftColumn(), selection[0].rightColumn() + 1))
            rowcount = len(rows)
            colcount = len(columns)
            table = [[''] * colcount for _ in range(rowcount)]
            for i, row in enumerate(rows):
                for j, col in enumerate(columns):
                    item = self.tableWidget.item(row, col)
                    table[i][j] = item.text() if item else ''
            stream = '\n'.join(['\t'.join(row) for row in table])
            QApplication.clipboard().setText(stream)

    def pasteSelection(self):
        clipboard = QApplication.clipboard()
        if clipboard.mimeData().hasText():
            text = clipboard.text()
            rows = text.split('\n')
            selected = self.tableWidget.selectedRanges()
            if selected:
                start_row = selected[0].topRow()
                start_col = selected[0].leftColumn()
                for i, row in enumerate(rows):
                    columns = row.split('\t')
                    for j, column in enumerate(columns):
                        if start_row + i < self.tableWidget.rowCount() and start_col + j < self.tableWidget.columnCount():
                            self.setCellItemAligned(start_row + i, start_col + j, column)
                
    def deleteSelection(self):
        for item in self.tableWidget.selectedItems():
            item.setText("")

    def moveToNextCell(self):
        current = self.tableWidget.currentItem()
        if current:
            row = current.row()
            col = current.column()
            if col + 1 < self.tableWidget.columnCount():
                next_item = self.tableWidget.item(row, col + 1)
            else:
                next_item = self.tableWidget.item(row + 1, 0)
            if next_item:
                self.tableWidget.setCurrentItem(next_item)
                self.tableWidget.editItem(next_item)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec())