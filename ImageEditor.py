import sys
import os
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QAction, QFileDialog, QTreeView, QFileSystemModel, 
                             QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QListWidget, QListWidgetItem, QFrame, QDockWidget,
                             QColorDialog, QInputDialog, QComboBox,QMenu, QToolBar, QSpacerItem, QSizePolicy)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QMouseEvent, QCursor, QIcon, QFontDatabase, QKeyEvent
from PyQt5.QtCore import Qt, QSize, QRectF, QSizeF, pyqtSignal, pyqtSlot, QPointF, QSortFilterProxyModel, QRegExp

import icons_rc

class Layer:
    def __init__(self, pixmap=None):
        self.pixmap = pixmap
        self.lines = []
        self.texts = []

class TextItem:
    def __init__(self, text, position, font, color):
        self.text = text
        self.position = position
        self.current_font = font
        self.color = color
        self.rect = None
        self.is_selected = False

class LineItem:
    def __init__(self, start, end, mid, color, is_dashed):
        self.start = start
        self.mid = mid
        self.end = end
        self.color = color
        self.is_dashed = is_dashed
        self.is_selected = False

class MyListWidget(QListWidget):
    item_moved = pyqtSignal(int, int)  # 시그널: (from_index, to_index)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setEditTriggers(QListWidget.DoubleClicked | QListWidget.EditKeyPressed)

    def show_context_menu(self, position):
        item = self.itemAt(position)
        if item:
            self.setCurrentItem(item)
            
            menu = QMenu(self)
            move_up_action = QAction("위로 이동", self)
            move_down_action = QAction("아래로 이동", self)
            edit_action = QAction("편집", self)
            remove_action = QAction("제거", self)
            
            menu.addAction(move_up_action)
            menu.addAction(move_down_action)
            menu.addAction(edit_action)
            menu.addAction(remove_action)
            
            move_up_action.triggered.connect(self.move_item_up)
            move_down_action.triggered.connect(self.move_item_down)
            edit_action.triggered.connect(self.edit_current_item)
            remove_action.triggered.connect(self.remove_current_item)
            
            menu.exec_(self.mapToGlobal(position))

    def move_item_up(self):
        current_row = self.currentRow()
        if current_row > 0:
            self.move_item(current_row, current_row - 1)

    def move_item_down(self):
        current_row = self.currentRow()
        if current_row < self.count() - 1:
            self.move_item(current_row, current_row + 1)

    def move_item(self, from_index, to_index):
        item = self.takeItem(from_index)
        self.insertItem(to_index, item)
        self.setCurrentItem(item)
        self.item_moved.emit(from_index, to_index)

    def edit_current_item(self):
        current_item = self.currentItem()
        if current_item:
            current_item.setFlags(current_item.flags() | Qt.ItemIsEditable)
            self.editItem(current_item)

    def remove_current_item(self):
        current_row = self.currentRow()
        if current_row != -1:
            self.takeItem(current_row)
            self.item_moved.emit(current_row, -1)  # -1 indicates removal

    def add_item(self, text):
        item = QListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.addItem(item)
        self.item_moved.emit(-1, self.count() - 1)  # -1 as from_index indicates new item

class EditableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.lineEdit().returnPressed.connect(self.on_return_pressed)

    def on_return_pressed(self):
        if self.currentText().isdigit():
            size = int(self.currentText())
            if 1 <= size <= 1000:  # 적절한 폰트 크기 범위 설정
                if self.findText(self.currentText()) == -1:
                    self.addItem(self.currentText())
                self.setCurrentIndex(self.findText(self.currentText()))
            else:
                self.setCurrentIndex(self.findText(str(self.parent().current_font.pointSize())))
        else:
            self.setCurrentIndex(self.findText(str(self.parent().current_font.pointSize())))

class ImageFileFilterProxyModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        if self.sourceModel().isDir(index):
            return True
        file_name = self.sourceModel().fileName(index)
        return bool(re.match(r".*\.(jpg|jpeg|png)$", file_name, re.IGNORECASE))

class ImageExplorerWidget(QWidget):
    # Define a custom signal that emits the file path as a string
    fileDoubleClicked = pyqtSignal(str)
    fileClicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)
        self.model = QFileSystemModel()
        self.model.setRootPath('')

        self.proxyModel = ImageFileFilterProxyModel()
        self.proxyModel.setSourceModel(self.model)
        self.proxyModel.setFilterKeyColumn(0)  # Apply filter on the file names

        self.tree = QTreeView()
        self.tree.setModel(self.proxyModel)
        self.tree.setRootIndex(self.proxyModel.mapFromSource(self.model.index('')))

        # Hide other columns except the first one (name)
        for i in range(1, self.model.columnCount()):
            self.tree.hideColumn(i)
        self.layout.addWidget(self.tree)

        self.tree.clicked.connect(self.onClick)
        self.tree.doubleClicked.connect(self.onDoubleClick)

    def onClick(self, index):
        source_index = self.proxyModel.mapToSource(index)
        file_path = self.model.filePath(source_index)
        self.fileClicked.emit(file_path)

    def onDoubleClick(self, index):
        # Map the proxy index to the source index
        source_index = self.proxyModel.mapToSource(index)
        file_path = self.model.filePath(source_index)
        self.fileDoubleClicked.emit(file_path)

class ImageEditor(QMainWindow):
    IMAGE_SIZE = (800, 600)
    def __init__(self):
        super().__init__()
        self.layers = []
        self.current_layer = None
        self.drawing = False
        self.adding_text = False
        self.moving_text = False
        self.selected_text = None
        self.selected_texts = set()
        self.selected_line = None
        self.moving_vertex = None
        self.points = []
        self.temp_line = None
        self.line_color = QColor(Qt.blue)
        self.current_font_color = QColor(Qt.blue)
        self.current_font = QFont("굴림", pointSize=12, weight=1)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('이미지 편집기')
        self.setGeometry(100, 100, 1000, 620)
        self.setStyleSheet(
            """QLabel, QDockWidget { margin: 3px;} """
        )

        # 툴바 생성
        self.add_menubar()
        self.add_toolbar()
 
        # 레이어 컨트롤
        layer_frame = QFrame()
        layer_frame.setMinimumWidth(300)
        layer_layout = QVBoxLayout()
        self.layer_list = MyListWidget(layer_frame)
        self.layer_list.itemClicked.connect(self.select_layer)
        self.layer_list.item_moved.connect(self.update_items)
        
        layer_button_layout = QHBoxLayout()
        add_layer_btn = QPushButton('+', layer_frame)
        remove_layer_btn = QPushButton('-', layer_frame)
        add_layer_btn.setFixedWidth(24)
        remove_layer_btn.setFixedWidth(24)

        add_layer_btn.clicked.connect(lambda: self.add_layer(pixmap=None))
        remove_layer_btn.clicked.connect(lambda: self.layer_list.remove_current_item())

        verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        
        layer_button_layout.addWidget(add_layer_btn)
        layer_button_layout.addWidget(remove_layer_btn)
        layer_button_layout.addItem(verticalSpacer)

        layer_layout.addWidget(self.layer_list)
        layer_layout.addItem(verticalSpacer)
        layer_layout.addLayout(layer_button_layout)
        layer_frame.setLayout(layer_layout)

        # 레이어 창
        self.layers_win = self.add_dockableWidget("레이어", layer_frame, 150)
        self.layers_win.visibilityChanged.connect(self.show_layer_enabled)

        # 탐색창 
        explorer = ImageExplorerWidget()
        explorer.fileClicked.connect(self.preview_image_from)
        explorer.fileDoubleClicked.connect(self.open_image_from)
        explorer.tree.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.explorer_win = self.add_dockableWidget("탐색기", explorer, 250)
        self.explorer_win.visibilityChanged.connect(self.show_explorer_enabled)

        # 프리뷰창
        self.preview = QLabel()
        self.preview.setMinimumHeight(150)
        self.preview.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        self.preview_win = self.add_dockableWidget("Preview", self.preview, 200)
        self.preview_win.visibilityChanged.connect(self.show_preview_enabled)
    
        # 이미지 편집 영역
        layout = QHBoxLayout()
        editor = QWidget()
        self.image_label = QLabel()
        self.image_label.setFixedSize(*self.IMAGE_SIZE)
        self.image_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)    
        self.image_label.setStyleSheet("border: 1px solid black;")
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self.mousePressEvent
        self.image_label.mouseMoveEvent = self.mouseMoveEvent 
        self.image_label.mouseDoubleClickEvent = self.mouseDoubleClickEvent
        self.image_label.mouseReleaseEvent = self.mouseReleaseEvent

        layout.addWidget(self.image_label)
        editor.setLayout(layout)

        self.setCentralWidget(editor)

        # 키 이벤트를 처리하기 위해 포커스 정책 설정
        self.setFocusPolicy(Qt.StrongFocus)

    def add_toolbar(self):
        self.toolbar = QToolBar()
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
        
        # 툴바 아이콘 추가
        new_action = QAction(QIcon(':/icons/document-add-svgrepo-com.svg'), '새 문서', self)
        new_action.triggered.connect(self.new_document)
        self.toolbar.addAction(new_action)

        open_action = QAction(QIcon(':/icons/album-svgrepo-com.svg'), '열기', self)
        open_action.triggered.connect(self.open_image)
        self.toolbar.addAction(open_action)

        save_action = QAction(QIcon(':/icons/diskette-svgrepo-com.svg'), '저장', self)
        save_action.triggered.connect(self.save_image)
        self.toolbar.addAction(save_action)

        self.toolbar.addSeparator()

        # 폰트명 콤보 박스 추가
        self.font_family_combo = QComboBox(self)
        self.font_family_combo.addItems(self.get_korean_fonts())
        self.font_family_combo.setCurrentText("굴림")
        self.font_family_combo.currentTextChanged.connect(self.change_font_family)
        self.toolbar.addWidget(self.font_family_combo)

        # 폰트 크기 콤보 박스 추가
        self.font_size_combo = EditableComboBox(self)
        self.font_size_combo.addItems(['8', '9', '10', '11', '12', '14', '16', '18', '20'])
        self.font_size_combo.setCurrentText(str(self.current_font.pointSize()))
        self.font_size_combo.currentTextChanged.connect(self.change_font_size)
        self.toolbar.addWidget(self.font_size_combo)

        # 폰트 스타일 서브메뉴 생성
        font_style_menu = QMenu('폰트 스타일', self)
        self.font_style_action = QAction("가", self)
        self.font_style_action.setFont(QFont(self.current_font.family(), pointSize=12))
        self.font_style_action.setMenu(font_style_menu)
        
        normal_action = QAction(QIcon(':/icons/text-svgrepo-com.svg'),'Normal', self)
        bold_action = QAction(QIcon(':/icons/text-bold-svgrepo-com.svg'), 'Bold', self)
        italic_action = QAction(QIcon(':/icons/text-italic-svgrepo-com.svg'), 'Italic', self)
        bold_italic_action = QAction(QIcon(':/icons/text-italicBold-svgrepo-com.svg'), 'Bold Italic', self)

        normal_action.triggered.connect(lambda: self.change_font_style("Normal"))
        bold_action.triggered.connect(lambda: self.change_font_style("Bold"))
        italic_action.triggered.connect(lambda: self.change_font_style("Italic"))
        bold_italic_action.triggered.connect(lambda: self.change_font_style("Bold Italic"))

        font_style_menu.addAction(normal_action)
        font_style_menu.addAction(bold_action)
        font_style_menu.addAction(italic_action)
        font_style_menu.addAction(bold_italic_action)

        self.toolbar.addAction(self.font_style_action)

        # 글자색상 설정
        self.font_color_btn = QPushButton("T")
        self.font_color_btn.setFixedSize(QSize(24, 24))
        self.font_color_btn.setFont(QFont("Courier", 18, weight=QFont.Bold))
        self.font_color_btn.setToolTip('글자 색상')
        self.font_color_btn.setStyleSheet(f"color: {self.current_font_color.name()}")
        self.font_color_btn.clicked.connect(self.change_font_color)
        self.toolbar.addWidget(self.font_color_btn)

        self.toolbar.addSeparator()

        # 라인 종류 설정
        self.line_type_combo = QComboBox(self)
        self.line_type_combo.addItems(["────", "─ ─ ─"])
        self.line_type_combo.setCurrentText("─ ─ ─")
        self.line_type_combo.currentIndexChanged.connect(self.change_line_type)
        self.toolbar.addWidget(self.line_type_combo)

        # 라인 색상 설정
        self.line_color_menubtn = QPushButton("L")
        self.line_color_menubtn.setFixedSize(QSize(24, 24))
        self.line_color_menubtn.setFont(QFont("Courier", 18, weight=QFont.Bold))
        self.line_color_menubtn.setToolTip('라인 색상')
        self.line_color_menubtn.setStyleSheet(f"color: {self.line_color.name()}")
        self.line_color_menubtn.clicked.connect(self.change_line_color)
        self.toolbar.addWidget(self.line_color_menubtn)

        self.toolbar.addSeparator()

        # 거리 입력 버튼
        line_drawing_action = QAction(QIcon(':/icons/pen-2-svgrepo-com.svg'), '거리 입력', self)
        line_drawing_action.triggered.connect(self.start_drawing_line)
        self.toolbar.addAction(line_drawing_action)        

        # 텍스트 입력 버튼
        adding_text_action = QAction(QIcon(':/icons/text-selection-svgrepo-com.svg'), '텍스트 입력', self)
        adding_text_action.triggered.connect(self.start_adding_text)
        self.toolbar.addAction(adding_text_action)   

    def add_menubar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('파일')

        new_action = QAction(QIcon(':/icons/document-add-svgrepo-com.svg'), '새 문서', self)
        new_action.triggered.connect(self.new_document)
        file_menu.addAction(new_action)

        open_action = QAction(QIcon(':/icons/album-svgrepo-com.svg'), '열기', self)
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)

        save_action = QAction(QIcon(':/icons/diskette-svgrepo-com.svg'), '저장', self)
        save_action.triggered.connect(self.save_image)
        file_menu.addAction(save_action)

        view_menu = menubar.addMenu('보기')
        self.show_layer_action = QAction(QIcon(':/icons/layers-svgrepo-com.svg'), '레이어', self)
        self.show_layer_action.triggered.connect(self.show_layer_win)
        self.show_layer_action.setEnabled(False)
        self.show_explorer_action = QAction(QIcon(':/icons/library-svgrepo-com.svg'), "탐색기", self)
        self.show_explorer_action.triggered.connect(self.show_explorer_win)
        self.show_explorer_action.setEnabled(False)
        self.show_preview_action = QAction(QIcon(':/icons/gallery-svgrepo-com.svg'), "미리보기", self)
        self.show_preview_action.triggered.connect(self.show_preview_win)
        self.show_preview_action.setEnabled(False)
        view_menu.addAction(self.show_layer_action)
        view_menu.addAction(self.show_explorer_action)
        view_menu.addAction(self.show_preview_action)

    def add_dockableWidget(self, title:str, wdg:QWidget, maxheight:int=0):
        dock = QDockWidget(title, self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        dock.setWidget(wdg)
        dock.setMaximumHeight(maxheight)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)    
        return dock    

    # 새로운 메서드들
    def new_document(self):
        self.layers = []
        self.layer_list.clear()
        self.current_layer = None

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Delete:
            self.delete_selected_items()

    def show_layer_win(self):
        if self.layers_win.isHidden():
            self.layers_win.show()
        self.show_layer_action.setEnabled(False)
    
    @pyqtSlot(bool)
    def show_layer_enabled(self, visible):
        if not visible:
            self.show_layer_action.setEnabled(True)

    def show_explorer_win(self):
        if self.explorer_win.isHidden():
            self.explorer_win.show()
        self.show_explorer_action.setEnabled(False)

    @pyqtSlot(bool)
    def show_explorer_enabled(self, visible):
        if not visible:
            self.show_explorer_action.setEnabled(True)

    def show_preview_win(self):
        if self.preview_win.isHidden():
            self.preview_win.show()
        self.show_preview_action.setEnabled(False)
    
    @pyqtSlot(bool)
    def show_preview_enabled(self, visible):
        if not visible:
            self.show_preview_action.setEnabled(True)

    def delete_selected_items(self):
        if self.current_layer:
            # 선택된 선 삭제
            if self.selected_line:
                self.current_layer.lines.remove(self.selected_line)
                self.selected_line = None

            # 선택된 텍스트 삭제
            for text in list(self.selected_texts):
                if text in self.current_layer.texts:
                    self.current_layer.texts.remove(text)
            self.selected_texts.clear()

    def change_font_family(self):
        font_family = self.font_family_combo.currentText()
        self.current_font.setFamily(font_family)
        self.update_toolbar()
        self.update_selected_text_style()

    def update_toolbar(self):
        current_font = self.current_font
        current_font.setPointSize(12)
        self.font_style_action.setFont(QFont(current_font))

    def change_font_size(self, size):
        try:
            new_size = int(size)
            if 1 <= new_size <= 50:  # 적절한 폰트 크기 범위 설정
                self.current_font.setPointSize(new_size)
                self.update_selected_text_style()
            else:
                self.font_size_combo.setCurrentText(str(self.current_font.pointSize()))
        except ValueError:
            self.font_size_combo.setCurrentText(str(self.current_font.pointSize()))

    def get_korean_fonts(self):
        korean_fonts= []
        font_db = QFontDatabase()
        fonts = font_db.families()
        for font in fonts:
            writing_systems = font_db.writingSystems(font)
            for ws in writing_systems:
                if ws == QFontDatabase.Korean:
                    korean_fonts.append(font)
        return korean_fonts

    def change_font_style(self, style):        
        if style == "Bold":
            self.current_font.setBold(True)
            self.current_font.setItalic(False)
        elif style == "Italic":
            self.current_font.setBold(False)
            self.current_font.setItalic(True)
        elif style == "Bold Italic":
            self.current_font.setBold(True)
            self.current_font.setItalic(True)
        else:  # Normal
            self.current_font.setBold(False)
            self.current_font.setItalic(False)

        self.update_toolbar()        
        self.update_selected_text_style()

    def update_selected_text_style(self):
        if not self.selected_texts:
            return
        for text_item in self.selected_texts:
            text_item.current_font = QFont(self.current_font)
            text_item.color = QColor(self.current_font_color)

    def open_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "이미지 열기", "", "이미지 파일 (*.png *.jpg *.bmp *.jpeg)")
        if file_name:
            pixmap = QPixmap(file_name)
            scaled_pixmap = self.scale_pixmap(pixmap)
            self.add_layer(scaled_pixmap)

    @pyqtSlot(str)
    def open_image_from(self, file_name):
        self.new_document()        
        if os.path.isfile(file_name):
            pixmap = QPixmap(file_name)
            scaled_pixmap = self.scale_pixmap(pixmap)
            self.add_layer(scaled_pixmap)
    
    @pyqtSlot(str)
    def preview_image_from(self, file_name):        
        if os.path.isfile(file_name):
            pixmap = QPixmap(file_name)
            size = self.preview.size()          
            scaled_pixmap = self.scale_pixmap(pixmap, size=size)
            self.preview.setPixmap(scaled_pixmap)

    def save_image(self):
        if not self.layers:
            return
        self.unselect()
        file_name, _ = QFileDialog.getSaveFileName(self, "이미지 저장", "", "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)")
        if file_name:
            self.image_label.pixmap().save(file_name, quality=50)

    def scale_pixmap(self, pixmap, size=None):
        if size is None:
            return pixmap.scaled(QSize(*self.IMAGE_SIZE), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def add_layer(self, pixmap=None):
        if pixmap is None:
            pixmap = QPixmap(*self.IMAGE_SIZE)
            pixmap.fill(Qt.transparent)
        layer = Layer(pixmap=pixmap)
        self.layers.append(layer)
        self.layer_list.addItem(f"레이어 {len(self.layers)}")
        if len(self.layer_list) > 1:
            self.layer_list.move_item(len(self.layer_list)-1, 0)
        self.current_layer = layer
        self.update_image()

    def select_layer(self, item):
        index = self.layer_list.row(item)
        if 0 <= index < len(self.layers):
            self.current_layer = self.layers[index]

    def start_drawing_line(self):
        self.drawing = True
        self.points = []
        self.temp_line = None

    def start_adding_text(self):
        self.adding_text = True
    
    def change_font_color(self):
        color = QColorDialog.getColor(initial=self.line_color)
        if color.isValid():
            self.current_font_color = color
            self.font_color_btn.setStyleSheet(f"color: {color.name()};")
        self.update_selected_text_style()

    def update_items(self, from_index, to_index):
        if from_index == -1:  # 새 아이템 추가
            self.add_layer()
        elif to_index == -1:  # 아이템 제거
            del self.layers[from_index]
        else:  # 아이템 이동
            item = self.layers.pop(from_index)
            self.layers.insert(to_index, item)

    def mousePressEvent(self, event: QMouseEvent):
        if self.drawing:
            self.points.append(event.pos())
            if len(self.points) == 3:
                text, ok = QInputDialog.getText(self, "텍스트 입력", "텍스트:")
                if ok:
                    line_type = self.line_type_combo.currentText()
                    new_line = LineItem(self.points[0], self.points[1], self.points[2], QColor(self.line_color), line_type=="─ ─ ─")
                    self.current_layer.lines.append(new_line)
                    self.current_layer.texts.append(TextItem(text, self.points[2], QFont(self.current_font), QColor(self.current_font_color)))
                    self.update_image()
                self.drawing = False
                self.points = []
                self.temp_line = None
                self.update_image()
        elif self.adding_text:
            text, ok = QInputDialog.getText(self, "텍스트 입력", "텍스트:")
            self.unselect()
            if ok and text:
                self.current_layer.texts.append(TextItem(text, event.pos(), self.current_font, self.current_font_color))
                self.update_image()
            self.adding_text = False
        else:
            # 선 선택 로직
            for layer in self.layers:
                for line in layer.lines:
                    if self.is_near_line(event.pos(), line):
                        self.unselect()  # 기존 선택 해제
                        self.selected_line = line
                        self.selected_line.is_selected = True
                        self.moving_vertex = self.get_nearest_vertex(event.pos(), line)
                        self.update_image()
                        return
            
            # 텍스트 선택 로직
            for layer in self.layers:
                for text_item in layer.texts:
                    if text_item.rect and text_item.rect.contains(event.pos()):
                        if not (event.modifiers() & Qt.ControlModifier):
                            self.unselect()  # Ctrl 키가 눌리지 않았다면 기존 선택 해제
                        self.selected_text = text_item
                        self.add_selected_text(text_item)
                        self.moving_text = True
                        self.offset = event.pos() - text_item.position
                        self.update_image()
                        return            
            self.unselect()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.drawing:
            if len(self.points) == 1:
                self.temp_line = (self.points[0], event.pos())
            elif len(self.points) == 2:
                self.temp_line = (self.points[0], event.pos(), self.points[1])
        elif self.moving_text and self.selected_text:
            new_pos = event.pos() - self.offset
            self.selected_text.position = new_pos
        elif self.selected_line and self.moving_vertex:
            new_pos = event.pos()
            if self.moving_vertex == 'start':
                self.selected_line.start = new_pos
            elif self.moving_vertex == 'mid':
                self.selected_line.mid = new_pos
            elif self.moving_vertex == 'end':
                self.selected_line.end = new_pos
        self.update_image()        
        self.update_cursor(event.pos())

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.moving_text:
            self.moving_text = False
        if self.selected_line:
            self.moving_vertex = None
        self.update_image()
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        for layer in self.layers:
            for text_item in layer.texts:
                if text_item.rect and text_item.rect.contains(event.pos()):
                    new_text, ok = QInputDialog.getText(self, "텍스트 수정", "새 텍스트:", text=text_item.text)
                    if ok:
                        text_item.text = new_text
                    return

    def unselect(self):
        self.selected_texts.clear()
        if self.selected_line:
            self.selected_line.is_selected = False
            self.selected_line = None
    
    def add_selected_text(self, text):
        self.selected_texts.add(text)
        self.update_image()

    def is_near_line(self, point, line, threshold=5):
        return (self.point_to_line_distance(point, line.start, line.mid) < threshold or
                self.point_to_line_distance(point, line.mid, line.end) < threshold)

    def point_to_line_distance(self, point, line_start, line_end):
        p = QPointF(point)
        a = QPointF(line_start)
        b = QPointF(line_end)
        ap = p - a
        ab = b - a
        proj = QPointF.dotProduct(ap, ab) / QPointF.dotProduct(ab, ab)
        proj = max(0, min(1, proj))
        closest = a + proj * ab
        return (p - closest).manhattanLength()

    def get_nearest_vertex(self, point, line):
        distances = [
            (point - line.start).manhattanLength(),
            (point - line.mid).manhattanLength(),
            (point - line.end).manhattanLength()
        ]
        min_distance = min(distances)
        if min_distance == distances[0]:
            return 'start'
        elif min_distance == distances[1]:
            return 'mid'
        else:
            return 'end'

    def change_line_color(self):
        color = QColorDialog.getColor(initial=self.line_color)
        if color.isValid():
            self.line_color = color
            self.line_color_menubtn.setStyleSheet(f"color: {color.name()};")
        if self.selected_line:
            self.selected_line.color = color
    
    def change_line_type(self):
        is_dashed = self.line_type_combo.currentText() == "─ ─ ─"
        if self.selected_line:
            self.selected_line.is_dashed = is_dashed

    def initialize_pixmap(self):
        result = QPixmap(*self.IMAGE_SIZE)
        result.fill(Qt.transparent)
        self.image_label.setPixmap(result)

    def update_image(self):
        if not self.layers:
            self.initialize_pixmap()
            return
        
        result = QPixmap(*self.IMAGE_SIZE)
        result.fill(Qt.transparent)
        painter = QPainter(result)
        
        for layer in self.layers[::-1]:
            painter.setOpacity(0.8)
            painter.drawPixmap(0, 0, layer.pixmap)            
            
            for line in layer.lines:
                pen = QPen(line.color)
                if line.is_dashed:
                    pen.setStyle(Qt.DashLine)
                if line.is_selected:
                    pen.setWidth(3)
                painter.setPen(pen)
                painter.drawLine(line.start, line.mid)
                painter.drawLine(line.mid, line.end)
                
                if line.is_selected:
                    painter.setBrush(Qt.red)
                    painter.drawEllipse(line.start, 5, 5)
                    painter.drawEllipse(line.mid, 5, 5)
                    painter.drawEllipse(line.end, 5, 5)
            
            for text_item in layer.texts:
                painter.setFont(text_item.current_font)
                painter.setPen(text_item.color)
                text_rect = painter.boundingRect(QRectF(text_item.position, QSizeF()), Qt.AlignLeft, text_item.text)
                painter.drawText(text_rect, text_item.text)
                text_item.rect = text_rect
                
                if text_item in self.selected_texts:
                    painter.setPen(QPen(Qt.red, 1, Qt.DashLine))
                    painter.drawRect(text_rect)
        
        if self.temp_line:
            painter.setPen(QPen(self.line_color))
            if len(self.temp_line) == 2:
                painter.drawLine(self.temp_line[0], self.temp_line[1])
            elif len(self.temp_line) == 3:
                painter.drawLine(self.temp_line[0], self.temp_line[1])
                painter.drawLine(self.temp_line[1], self.temp_line[2])
        
        painter.end()
        self.image_label.setPixmap(result)

    def update_cursor(self, pos):
        if self.selected_line:
            if self.is_near_vertex(pos, self.selected_line.start) or \
               self.is_near_vertex(pos, self.selected_line.mid) or \
               self.is_near_vertex(pos, self.selected_line.end):
                self.setCursor(Qt.CrossCursor)
                return
        
        for layer in self.layers:
            for text_item in layer.texts:
                if text_item.rect and text_item.rect.contains(pos):
                    self.setCursor(Qt.SizeAllCursor)
                    return
        
        self.setCursor(Qt.ArrowCursor)

    def is_near_vertex(self, point, vertex, threshold=5):
        return (point - vertex).manhattanLength() < threshold

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageEditor()
    ex.show()
    sys.exit(app.exec_())