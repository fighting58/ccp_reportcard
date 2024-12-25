from PySide6.QtWidgets import * 
from PySide6.QtGui import *
from PySide6.QtCore import *

from ui_splash_screen import Ui_SplashScreen
import sys

splash_timer_value = 0

class CircularProgress(QWidget):
    def __init__(self):
        super().__init__()

        self.value =0
        self.width=200
        self.height=200
        self.progress_width=10
        self.progress_rounded_cap=True
        self.max_value=100
        self.progress_color= 0xff79c9
        self.enable_text=True
        self.font_family='Segoe UI'
        self.font_size=12
        self.suffix='%'
        self.text_color=0xff79c9
        self.enable_bg=True
        self.bg_color=0x44475a
        self.resize(self.width, self.height)
    
    def add_shadow(self, enable):
        if enable:
            self.shadow = QGraphicsDropShadowEffect(self)
            self.shadow.setBlurRadius(10)  
            self.shadow.setXOffset(0)  
            self.shadow.setYOffset(0)  
            self.shadow.setColor(QColor(0, 0, 0, 80))  
            self.setGraphicsEffect(self.shadow)

    def set_value(self, value):
        self.value=value
        self.repaint()  

    def paintEvent(self, e):
        width = self.width - self.progress_width
        height = self.height - self.progress_width
        margin = self.progress_width / 2
        value = self.value * 360 / self.max_value

        paint = QPainter()
        paint.begin(self)
        paint.setRenderHint(QPainter.Antialiasing)  
        paint.setFont(QFont(self.font_family, self.font_size))  

        rect=QRect(0, 0, self.width, self.height)
        paint.setPen(Qt.NoPen)  
        paint.drawRect(rect)  

        pen = QPen()
        pen.setColor(QColor(self.progress_color))
        pen.setWidth(self.progress_width)

        if self.progress_rounded_cap:
            pen.setCapStyle(Qt.RoundCap)

        paint.setPen(pen)  
        paint.drawArc(margin, margin, width, height, -90 * 16, -value * 16)  


        pen.setColor(QColor(self.text_color))  
        paint.setPen(pen)
        paint.drawText(rect, Qt.AlignCenter, f"{self.value}{self.suffix}")  
        
        paint.end()

class Splashscreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_SplashScreen()
        self.ui.setupUi(self)

        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.ui.loading.setStyleSheet("color:#fff")

        self.progress = CircularProgress()
        self.progress.width = 300
        self.progress.height = 300
        self.progress.value=50
        self.progress.font_size =40
        self.progress.setFixedSize(self.progress.width, self.progress.height)

        self.progress.add_shadow(True)
        self.progress.bg_color = QColor(68,71, 90, 140)

        self.progress.setParent(self.ui.centralwidget)
        self.progress.show()
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0,0,0,80))
        self.setGraphicsEffect(self.shadow)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(10)
        self.show()
    
    def update(self):
        global splash_timer_value
        self.progress.set_value(splash_timer_value)
        if splash_timer_value >= 100:
            self.timer.stop()

        splash_timer_value += 1


 
if __name__ == "__main__":
    app=QApplication(sys.argv)
    ex = Splashscreen()
    sys.exit(app.exec())