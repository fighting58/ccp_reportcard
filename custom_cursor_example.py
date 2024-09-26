import sys
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QCursor, QPixmap

class CustomCursorWidget(QWidget):
    def __init__(self):
        super().__init__()

        # 커스텀 커서 이미지 로드
        cursor_pixmap = QPixmap('images/text.png')  # 커서 이미지 파일 경로

        # 핫스팟 위치 (x, y)를 지정하여 커스텀 커서 생성 (이미지에서 마우스 클릭 지점)
        hotspot_x = 0  # 예: 이미지의 x 좌표
        hotspot_y = 32  # 예: 이미지의 y 좌표
        custom_cursor = QCursor(cursor_pixmap, hotspot_x, hotspot_y)

        # 커서 설정
        self.setCursor(custom_cursor)

        # 기본적인 창 설정
        self.setWindowTitle("Custom Cursor with Hotspot Example")
        self.setGeometry(100, 100, 400, 300)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = CustomCursorWidget()
    window.show()

    sys.exit(app.exec())
