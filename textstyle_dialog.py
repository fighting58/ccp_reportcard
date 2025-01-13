

from PySide6.QtWidgets import (QDialog, QFrame, QLabel, QHBoxLayout,QGridLayout, QColorDialog, QPushButton, 
                               QFormLayout, QComboBox, QSpinBox, QDialogButtonBox, QCheckBox)
from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QColor, QFont, QPen, QPixmap, QPainter, QFontDatabase
from environment_manage import EnvironmentManager

class TextStyleDialog(QDialog):

    values_summited = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("textStyleDialog")
        self.setWindowTitle("Text Style")
        self.resize(300, 260)

        self.text_font = QFont()
        self.text_font_style = "Normal"

        self.font_color = QColor('#0000ff')
        self.envrioment_manager = EnvironmentManager('image_editor.ini')        
        self.read_environment('SubTitle-Style')

        self.init_ui()
        self.apply_widget_color()
        self.update_label()
        self.setStyleSheet("""* {color: black;}""")


    def init_ui(self):

        layout = QGridLayout()
        vlayout = QHBoxLayout()
        
        form_layout = QFormLayout()

        self.text_type_combo = QComboBox(self)
        self.text_type_combo.addItems(["제목", "항목"])
        self.text_type_combo.setCurrentText("항목")

        self.divide_line= QFrame(self)
        self.divide_line.setFrameShape(QFrame.Shape.HLine)
        self.divide_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.font_family_combo = QComboBox(self)
        self.font_family_combo.addItems(self.get_korean_fonts())
        
        self.font_color_btn = QPushButton("Font Color", self)
        
        self.font_size_spin = QSpinBox(self)
        self.font_size_spin.setRange(8, 50)        
        self.font_style_combo = QComboBox(self)
        self.font_style_combo.addItems(["Normal", "Bold", "Italic", "Underline", 'Bold italic', 'Bold underline', 'Italic underline', 'Bold italic underline'])

        self.rect_color_btn = QPushButton("Boundary Color", self)        
        
        self.rect_line_width_spin = QSpinBox(self)
        self.rect_line_width_spin.setRange(0, 5)        

        self.rect_line_style_combo = QComboBox(self)
        self.rect_line_style_combo.addItems(["Solid", "Dashed"])
        self.rect_fill_btn = QPushButton("Fill Color", self)
        

        form_layout.addRow("Text Type", self.text_type_combo)
        form_layout.addRow(self.divide_line)
        form_layout.addRow("Font Family", self.font_family_combo)
        form_layout.addRow("Font Color", self.font_color_btn)
        form_layout.addRow("Font Size", self.font_size_spin)  
        form_layout.addRow("Font Style", self.font_style_combo)
        
        form_layout.addRow("Boundary Color", self.rect_color_btn)
        form_layout.addRow("Boundary Line Width", self.rect_line_width_spin)
        form_layout.addRow("Boundary Line Style", self.rect_line_style_combo)
        form_layout.addRow("Fill Color", self.rect_fill_btn)

        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        vlayout.addLayout(form_layout)
        
        self.label = QLabel(self)
        self.label.setFixedSize(350, 240)
        self.label.setAlignment(Qt.AlignCenter)
        self.save_settings = QCheckBox("이 설정을 저장합니다.", self)
        vlayout.addWidget(self.label)

        layout.addLayout(vlayout, 0, 0, 1, 2)
        layout.addWidget(self.save_settings, 1, 0, 1, 1)
        layout.addWidget(self.buttonBox, 1, 1, 1, 1)

        self.update_dialog()
        self.setLayout(layout)
    
        self.text_type_combo.currentTextChanged.connect(self.on_text_type_changed)
        self.font_family_combo.currentTextChanged.connect(self.apply_font)
        self.font_size_spin.valueChanged.connect(self.apply_font)
        self.font_style_combo.currentTextChanged.connect(self.apply_font)
        self.font_color_btn.clicked.connect(self.apply_font_color)
        self.rect_line_width_spin.valueChanged.connect(self.apply_rect_line_width)
        self.rect_line_style_combo.currentTextChanged.connect(self.apply_rect_line_style)
        self.rect_color_btn.clicked.connect(self.apply_rect_line_color)
        self.rect_fill_btn.clicked.connect(self.apply_rect_fill_color)
        self.buttonBox.accepted.connect(self.on_accept)
        self.buttonBox.rejected.connect(self.reject)

    def on_accept(self):
        values = {"font": self.text_font,
                  "font_color": self.font_color,
                  "rect_line_width": self.rect_line_width_spin.value(),
                  "rect_line_style": self.rect_line_style_combo.currentText(),
                  "rect_line_color": self.rect_line_color,
                  "rect_fill_color": self.rect_fill_color
                 }
        if self.save_settings.isChecked():
            if self.text_type_combo.currentText() == "제목":
                section_name = "Title-Style"
            else:
                section_name = "SubTitle-Style"
            
            config_dict = { 'font-family': self.font_family_combo.currentText(),
                            'font-size': str(self.font_size_spin.value()),
                            'font-style': self.font_style_combo.currentText(),
                            'font-color': self.font_color.name(),
                            'rect-line-width': str(self.rect_line_width_spin.value()),
                            'rect-line-style': self.rect_line_style_combo.currentText(),
                            'rect-line-color': self.rect_line_color.name(),
                            'rect-fill-color': self.rect_fill_color.name()                            

            }
            self.envrioment_manager.add_section(section_name, config_dict)

        self.values_summited.emit(values)
        self.accept()

    def on_text_type_changed(self):
        if self.text_type_combo.currentText() == "제목":
            section_name = "Title-Style"
        else:
            section_name = "SubTitle-Style"
        self.read_environment(section_name)
        self.update_dialog()
        self.apply_widget_color()

    def update_dialog(self):
        self.font_family_combo.setCurrentText(self.text_font.family())
        self.font_size_spin.setValue(self.text_font.pointSize())
        self.font_style_combo.setCurrentText(self.text_font_style)
        self.font_color_btn.setText(self.font_color.name())
        self.rect_line_width_spin.setValue(self.rect_line_width)
        self.rect_color_btn.setText(self.rect_line_color.name())
        self.rect_fill_btn.setText(self.rect_fill_color.name())
    
    def apply_widget_color(self):
        luminance = 0.2126 * self.font_color.red() + 0.7152 * self.font_color.green() + 0.0722 * self.font_color.blue()
        self.font_color_btn.setStyleSheet(f"color: black; background-color: {self.font_color.name()};") if luminance > 128 else self.font_color_btn.setStyleSheet(f"color: white; background-color: {self.font_color.name()};")
        luminance = 0.2126 * self.rect_line_color.red() + 0.7152 * self.rect_line_color.green() + 0.0722 * self.rect_line_color.blue()
        self.rect_color_btn.setStyleSheet(f"color: black; background-color: {self.rect_line_color.name()};") if luminance > 128 else self.rect_color_btn.setStyleSheet(f"color: white; background-color: {self.rect_line_color.name()};")
        luminance = 0.2126 * self.rect_fill_color.red() + 0.7152 * self.rect_fill_color.green() + 0.0722 * self.rect_fill_color.blue()
        self.rect_fill_btn.setStyleSheet(f"color: black; background-color: {self.rect_fill_color.name()};") if luminance > 128 else self.rect_fill_btn.setStyleSheet(f"color: white; background-color: {self.rect_fill_color.name()};")
        
        
    def read_environment(self, text_type):
        config_dict = self.envrioment_manager.get_section(text_type)
        self.text_font.setFamily(config_dict.get('font-family', '굴림'))
        self.text_font.setPointSize(int(config_dict.get('font-size', 26)))
        self.text_font.setBold(True) if 'bold' in config_dict.get('font-style', 'normal').lower() else self.text_font.setBold(False)
        self.text_font.setItalic(True) if 'italic' in config_dict.get('font-style', 'normal').lower() else self.text_font.setItalic(False)  
        self.text_font.setUnderline(True) if 'underline' in config_dict.get('font-style', 'normal').lower() else self.text_font.setUnderline(False)  
        self.text_font_style = config_dict.get('font-style', 'normal')
        self.font_color =  QColor(config_dict.get('font-color', '#0000ff'))
        self.rect_line_width = int(config_dict.get('rect-line-width', 2))
        self.rect_line_style = config_dict.get('rect-line-style', 'Solid')
        self.rect_line_color = QColor(config_dict.get('rect-line-color', '#000000'))
        self.rect_fill_color = QColor(config_dict.get('rect-fill-color', '#ffffff'))


    def boundary_pen(self):
        pen = QPen()
        pen.setColor(self.rect_line_color)
        pen.setWidth(self.rect_line_width)
        if self.rect_line_style == "Dashed":
            pen.setStyle(Qt.DashLine)
        else:
            pen.setStyle(Qt.SolidLine)
        return pen

    def apply_font(self):
        self.text_font.setFamily(self.font_family_combo.currentText())
        self.text_font.setPointSize(self.font_size_spin.value())
        styles = self.font_style_combo.currentText().lower()
        self.text_font.setBold(True) if "bold" in styles else self.text_font.setBold(False)
        self.text_font.setItalic(True) if "italic" in styles else self.text_font.setItalic(False)
        self.text_font.setUnderline(True) if "underline" in styles else self.text_font.setUnderline(False)
        self.update_label()

    def apply_font_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.font_color = color
            self.font_color_btn.setText(self.font_color.name())
            self.apply_widget_color()
            self.update_label()

    def apply_rect_line_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.rect_line_color = color
            self.rect_color_btn.setText(self.rect_line_color.name())
            self.apply_widget_color()
            self.update_label() 

    def apply_rect_line_width(self): 
        self.rect_line_width = self.rect_line_width_spin.value()
        self.update_label() 

    def apply_rect_line_style(self): 
        self.rect_line_style = self.rect_line_style_combo.currentText()
        self.update_label()

    def apply_rect_fill_color(self): 
        color = QColorDialog.getColor()
        if color.isValid():
            self.rect_fill_color = color
            self.rect_fill_btn.setText(self.rect_fill_color.name())
            self.apply_widget_color()
            self.update_label()

    def get_korean_fonts(self):
        korean_fonts= []
        fonts = QFontDatabase.families()
        for font in fonts:
            writing_systems = QFontDatabase.writingSystems(font)
            for ws in writing_systems:
                if ws == QFontDatabase.Korean:
                    korean_fonts.append(font)
        return korean_fonts

    def initialize_pixmap(self):
        result = QPixmap(350,240)
        result.fill(Qt.white)
        self.label.setPixmap(result)        

    def update_label(self):
        self.initialize_pixmap()
        pixmap = self.label.pixmap()
        painter = QPainter(pixmap)
        pen = self.boundary_pen()
        painter.setPen(pen)
        painter.setFont(self.text_font)
        rect = painter.boundingRect(QRect(10, 10, 330, 220), Qt.AlignCenter, "Aa가나123")
        rect = rect.adjusted(-5, -2, 5, 2)
        painter.drawRect(rect)  # Adjust the rectangle size and position as needed
        painter.fillRect(rect, self.rect_fill_color)
        painter.setPen(self.font_color)
        painter.drawText(10, 10, 330, 220, Qt.AlignCenter, "Aa가나123")
        painter.end()
        self.label.setPixmap(pixmap)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = TextStyleDialog()
    dialog.show()
    sys.exit(app.exec())

