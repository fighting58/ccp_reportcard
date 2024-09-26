import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QCursor, QPixmap

app = QApplication(sys.argv)
pen_cursor = QCursor(QPixmap('images/pen_cursor.png'), hotX=0, hotY=32)
text_cursor = QCursor(QPixmap('images/text_cursor.png'))