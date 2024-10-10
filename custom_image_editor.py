
#==========================================
import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFileDialog, QPushButton, QInputDialog, QSlider,
                                QToolBar, QComboBox, QMenu, QLabel, QColorDialog, QVBoxLayout, QHBoxLayout)
from PySide6.QtCore import Qt, Signal,Slot, QSize, QRectF, QSizeF, QPointF
from PySide6.QtGui import QKeySequence, QPainter, QPen, QColor, QIcon, QAction, QPixmap, QFont, QKeyEvent, QFontDatabase, QMouseEvent, QCursor

class CustomCursor(QCursor):
    def __init__(self):
        super().__init__()
        self.pen_cursor = QCursor(QPixmap('images/pen_cursor.svg'), hotX=0, hotY=20)
        self.text_cursor = QCursor(QPixmap('images/text_cursor.svg'), hotX=0, hotY=0)

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
    def __init__(self, start, end, mid, color, is_dashed, width=1):
        self.start = start
        self.mid = mid
        self.end = end
        self.color = color
        self.width = width
        self.is_dashed = is_dashed
        self.is_selected = False

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


class ImageEditor(QMainWindow):
    table_update_request = Signal(int, str, str)
    
    def __init__(self, parent=None):
        super().__init__()
        self.layers = []
        self.current_layer = None
        self.current_image = None
        self.drawing = False
        self.adding_text = False
        self.moving_text = False
        self.doing_resize = False
        self.selected_text = None
        self.selected_texts = set()
        self.selected_line = None
        self.moving_vertex = None
        self.points = []
        self.temp_line = None
        self.line_color = QColor(Qt.red)
        self.line_width = 2
        self.current_font_color = QColor(Qt.blue)
        self.current_font = QFont("굴림", pointSize=24, weight=1)
        self.IMAGE_SIZE = (400, 300)
        self.table_row = None
        self.custom_cursor = CustomCursor()
        self.initUI()
        self.setGeometry(100, 100, 800, 600)

    def initUI(self):       
        self.add_toolbar("Main Toolbar")

        # image canvas
        self.image_label = QLabel(self)
        self.image_label.setObjectName("image_label")
        self.image_label.setMaximumSize(*self.IMAGE_SIZE)
        self.image_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)    
        self.image_label.setStyleSheet("border: 1px solid black;")
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self.mousePressEvent
        self.image_label.mouseMoveEvent = self.mouseMoveEvent 
        self.image_label.mouseDoubleClickEvent = self.mouseDoubleClickEvent
        self.image_label.mouseReleaseEvent = self.mouseReleaseEvent

        self.main_widget = QWidget(self)
        layout = QHBoxLayout(self.main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        layout.addWidget(self.image_label)

        self.setCentralWidget(self.main_widget)        

        # 키 이벤트를 처리하기 위해 포커스 정책 설정
        self.setFocusPolicy(Qt.StrongFocus)

    def add_toolbar(self, name='Toolbar'):
        self.toolbar = QToolBar(name)
        self.toolbar.setFixedHeight(30)
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
        self.font_color_btn.setStyleSheet(f"color: {self.current_font_color.name()}; border: none;")
        self.font_color_btn.clicked.connect(self.change_font_color)
        self.toolbar.addWidget(self.font_color_btn)

        self.toolbar.addSeparator()

        # 라인 종류 설정
        self.line_type_combo = QComboBox(self)
        self.line_type_combo.addItems(["────", "─ ─ ─"])
        self.line_type_combo.setCurrentText("─ ─ ─")
        self.line_type_combo.currentIndexChanged.connect(self.change_line_type)
        self.toolbar.addWidget(self.line_type_combo)

        # 라인 두께 설정
        line_width_setting = QWidget(self)
        line_width_setting.setMaximumWidth(70)
        line_width_setting.setToolTip('선두께')
        line_width_setting_layout = QHBoxLayout(line_width_setting)
        line_width_setting_layout.setContentsMargins(0,0,0,0)
        line_width_setting_layout.setSpacing(0)
        
        self.h_slider = QSlider(line_width_setting)
        self.h_slider.setFixedSize(40, 10)
        self.h_slider.setMinimum(1)
        self.h_slider.setMaximum(50)
        self.h_slider.setValue(self.line_width)
        self.h_slider.setOrientation(Qt.Horizontal)
        self.h_slider.valueChanged.connect(self.change_line_width)
        self.line_width_label = QLabel(line_width_setting)
        self.line_width_label.setFixedWidth(15)
        self.line_width_label.setNum(self.line_width)
        self.line_width_label.setAlignment(Qt.AlignCenter)
        line_width_setting_layout.addWidget(self.h_slider)
        line_width_setting_layout.addWidget(self.line_width_label)
        self.toolbar.addWidget(line_width_setting)

        # 라인 색상 설정
        self.line_color_menubtn = QPushButton("L")
        self.line_color_menubtn.setFixedSize(QSize(24, 24))
        self.line_color_menubtn.setFont(QFont("Courier", 18, weight=QFont.Bold))
        self.line_color_menubtn.setToolTip('라인 색상')
        self.line_color_menubtn.setStyleSheet(f"color: {self.line_color.name()}; border: none;")
        self.line_color_menubtn.clicked.connect(self.change_line_color)
        self.toolbar.addWidget(self.line_color_menubtn)

        self.toolbar.addSeparator()

        # 거리 입력 버튼
        line_drawing_action = QAction(QIcon(':/icons/pen-2-svgrepo-com.svg'), '거리 입력', self)
        line_drawing_action.setShortcut(QKeySequence("Ctrl+L"))
        line_drawing_action.triggered.connect(self.start_drawing_line)
        self.toolbar.addAction(line_drawing_action)        

        # 텍스트 입력 버튼
        adding_text_action = QAction(QIcon(':/icons/text-selection-svgrepo-com.svg'), '텍스트 입력', self)
        adding_text_action.setShortcut(QKeySequence("Ctrl+T"))
        adding_text_action.triggered.connect(self.start_adding_text)
        self.toolbar.addAction(adding_text_action)   

        # Toolbar2
        self.toolbar2 = QToolBar("Apply Image Toolbar")
        self.addToolBar(Qt.TopToolBarArea, self.toolbar2)

        self.image_apply_button = QPushButton("Save && apply", self.toolbar2)
        self.image_apply_button.setShortcut(QKeySequence("Ctrl+Return"))
        self.image_apply_button.clicked.connect(self.on_request_update)
        self.toolbar2.addWidget(self.image_apply_button)

    # 새로운 메서드들
    def new_document(self):
        self.layers = []
        self.current_layer = None
        self.current_image = None
        self.table_row = None
        self.update_image()

    def on_request_update(self):
        if not self.table_row is None:
            # self.target_image가 None이면 self.current_image를 사용
            if self.target_image is None:
                path = self.current_image
            # target_image가 파일형식인 경우 디렉토리 경로만 사용, 아니면 전체를 경로로 사용
            path = self.target_image if os.path.isdir(self.target_image) else os.path.split(self.target_image)[0]
            # 새로운 경로 지정
            new_path = path if path.endswith('_거리입력_') else path + '/_거리입력_'
            new_filename = f"{self.table_row[1]}_edit.png"   # 파일명을 "{도근번호}_edit"으로 설정하고 png형식으로 저장
            if not os.path.exists(new_path):
                os.mkdir(new_path)        # 거리입력 디렉토리 생성
            # 이미지 저장
            self.save_image(filename=os.path.join(new_path, new_filename), quality=100, size=QSize(800, 600))
            self.table_update_request.emit(self.table_row[0], new_path, new_filename)

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
        self.update_selected_text_style()

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
            self.current_image = file_name
            pixmap = QPixmap(self.current_image)
            scaled_pixmap = self.scale_pixmap(pixmap)
            self.add_layer(scaled_pixmap)        
            self.resize_pixmap()

    def open_image_from(self, file_name):
        self.layers=[]
        self.target_image = file_name
        if os.path.exists(file_name) and os.path.isfile(file_name):
            pixmap = QPixmap(file_name)
        else:
            pixmap = QPixmap(*self.IMAGE_SIZE)
            pixmap.fill(Qt.white)
        scaled_pixmap = self.scale_pixmap(pixmap)
        self.add_layer(scaled_pixmap)
    
    def save_image(self, filename=None, quality=50, size: QSize=None):
        if not self.layers:
            return
        self.unselect()
        self.update_image()
        if filename is None:
            filename, _ = QFileDialog.getSaveFileName(self, "이미지 저장", "", "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)")
        
        if size is not None:
            pixmap = self.image_label.pixmap().scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pixmap = self.image_label.pixmap()

        if filename:
            pixmap.save(filename, quality=quality)

    def scale_pixmap(self, pixmap, size=None):
        if size is None:
            return pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def get_korean_fonts(self):
        korean_fonts= []
        fonts = QFontDatabase.families()
        for font in fonts:
            writing_systems = QFontDatabase.writingSystems(font)
            for ws in writing_systems:
                if ws == QFontDatabase.Korean:
                    korean_fonts.append(font)
        return korean_fonts

    def add_layer(self, pixmap=None):
        if pixmap is None:
            pixmap = QPixmap(*self.IMAGE_SIZE)
            pixmap.fill(Qt.transparent)
        layer = Layer(pixmap=pixmap)
        self.layers.append(layer)
        self.current_layer = layer
        self.update_image()

    def start_drawing_line(self):
        self.drawing = True
        self.adding_text = False
        self.points = []
        self.temp_line = None
        
    def start_adding_text(self):
        self.adding_text = True
        self.drawing = False
    
    def change_font_color(self):
        color = QColorDialog.getColor(initial=self.line_color)
        if color.isValid():
            self.current_font_color = color
            self.font_color_btn.setStyleSheet(f"color: {color.name()}; border: none;")
        self.update_selected_text_style()

    def change_line_color(self):
        color = QColorDialog.getColor(initial=self.line_color)
        if color.isValid():
            self.line_color = color
            self.line_color_menubtn.setStyleSheet(f"color: {color.name()}; border: none;")
        if self.selected_line:
            self.selected_line.color = color

    def change_line_width(self):
        thickness = self.h_slider.value()
        self.line_width_label.setNum(thickness)
        self.line_width = thickness
        if self.selected_line:
            self.selected_line.width = thickness

    def change_line_type(self):
        is_dashed = self.line_type_combo.currentText() == "─ ─ ─"
        if self.selected_line:
            self.selected_line.is_dashed = is_dashed

    def update_items(self, from_index, to_index):
        if from_index == -1:  # 새 아이템 추가
            self.add_layer()
        elif to_index == -1:  # 아이템 제거
            del self.layers[from_index]
        else:  # 아이템 이동
            item = self.layers.pop(from_index)
            self.layers.insert(to_index, item)

    def resize_pixmap(self):
        main_widget_size = self.main_widget.size()
        # 가로 크기에 따라 세로 크기를 4:3 비율로 설정
        new_width = main_widget_size.width() 
        new_height = int(new_width * 3 / 4)

        # 부모 위젯의 세로 크기보다 계산된 세로 크기가 클 경우
        if new_height > main_widget_size.height():
            new_height = main_widget_size.height()
            new_width = int(new_height * 4 / 3)
        # 레이블 크기 재조정        
        self.IMAGE_SIZE = (int(new_width * 0.98), int(new_height * 0.98))
        self.image_label.setFixedSize(*self.IMAGE_SIZE)

        if self.layers:
            self.open_image_from(self.current_image) 

    def resizeEvent(self, event):
        self.resize_pixmap()
        super().resizeEvent(event)  

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Delete:
            self.delete_selected_items()

    def mousePressEvent(self, event: QMouseEvent):
        if self.drawing:
            self.points.append(event.position())
            if len(self.points) == 3:
                text, ok = QInputDialog.getText(self, "텍스트 입력", "텍스트:")
                if ok:
                    line_type = self.line_type_combo.currentText()
                    new_line = LineItem(self.points[0], self.points[1], self.points[2], QColor(self.line_color), line_type=="─ ─ ─", width=self.line_width)
                    self.current_layer.lines.append(new_line)
                    self.current_layer.texts.append(TextItem(text, self.points[2], QFont(self.current_font), QColor(self.current_font_color)))
                    self.update_image()
                self.drawing = False

                self.points = []
                self.temp_line = None
                self.update_image()
        elif self.adding_text:
            text, ok = QInputDialog.getText(self, "텍스트 입력", "텍스트:")           
            if ok and text:
                self.current_layer.texts.append(TextItem(text, event.position(), QFont(self.current_font), QColor(self.current_font_color)))
                self.update_image()
            self.unselect()
            self.adding_text = False

        else:
            # 선 선택 로직
            for layer in self.layers:
                for line in layer.lines:
                    if self.is_near_line(event.position(), line):
                        self.unselect()  # 기존 선택 해제
                        self.selected_line = line
                        self.selected_line.is_selected = True
                        self.moving_vertex = self.get_nearest_vertex(event.position(), line)
                        self.update_image()
                        return
            
            # 텍스트 선택 로직
            for layer in self.layers:
                for text_item in layer.texts:
                    if text_item.rect and text_item.rect.contains(event.position()):
                        if not (event.modifiers() & Qt.ControlModifier):
                            self.unselect()  # Ctrl 키가 눌리지 않았다면 기존 선택 해제
                        self.selected_text = text_item
                        self.add_selected_text(text_item)
                        self.moving_text = True
                        self.offset = event.position() - text_item.position
                        self.update_image()
                        return            
            self.unselect()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.drawing:
            if len(self.points) == 1:
                self.temp_line = (self.points[0], event.position())
            elif len(self.points) == 2:
                self.temp_line = (self.points[0], event.position(), self.points[1])
        elif self.moving_text and self.selected_text:
            new_pos = event.position() - self.offset
            self.selected_text.position = new_pos
        elif self.selected_line and self.moving_vertex:
            new_pos = event.position()
            if self.moving_vertex == 'start':
                self.selected_line.start = new_pos
            elif self.moving_vertex == 'mid':
                self.selected_line.mid = new_pos
            elif self.moving_vertex == 'end':
                self.selected_line.end = new_pos
        else:
            pass
        self.update_image()        
        self.update_cursor(event.position())

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.moving_text:
            self.moving_text = False
        if self.selected_line:
            self.moving_vertex = None        
        self.update_image()
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        for layer in self.layers:
            for text_item in layer.texts:
                if text_item.rect and text_item.rect.contains(event.position()):
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

    def initialize_pixmap(self):
        result = QPixmap(400,300)
        result.fill(Qt.transparent)
        self.image_label.setPixmap(result)
        # self.resize_pixmap()

    def update_image(self):
        result = QPixmap(*self.IMAGE_SIZE)
        result.fill(Qt.transparent)
        if not self.layers:
            self.image_label.setPixmap(result)
            return
        painter = QPainter(result)
        
        for layer in self.layers[::-1]:
            # painter.setOpacity(0.8)
            painter.drawPixmap(0, 0, layer.pixmap)            
            
            for line in layer.lines:
                pen = QPen(line.color)
                pen.setWidth(line.width)
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
        if self.drawing:
            self.image_label.setCursor(self.custom_cursor.pen_cursor)
        elif self.adding_text:
            self.image_label.setCursor(self.custom_cursor.text_cursor)
        else:
            self.image_label.setCursor(Qt.ArrowCursor)

        if self.selected_line:
            if self.is_near_vertex(pos, self.selected_line.start) or \
               self.is_near_vertex(pos, self.selected_line.mid) or \
               self.is_near_vertex(pos, self.selected_line.end):
                self.image_label.setCursor(Qt.CrossCursor)
                return
        
        for layer in self.layers:
            for text_item in layer.texts:
                if text_item.rect and text_item.rect.contains(pos):
                    self.image_label.setCursor(Qt.SizeAllCursor)
                    return

    def is_near_vertex(self, point, vertex, threshold=5):
        return (point - vertex).manhattanLength() < threshold

class TestManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUI()
        self.resize(800, 700)
        self.show()

    def setupUI(self):
        # 중앙 위젯 생성
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 레이아웃 설정
        layout = QVBoxLayout(central_widget)

        # ImageEditor 생성
        self.image_editor = ImageEditor(self)
        self.image_editor.setStyleSheet("QLabel { margin: 3px;}")

        layout.addWidget(self.image_editor)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = TestManager()
    sys.exit(app.exec())