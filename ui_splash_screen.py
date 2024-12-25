# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'splash_screensDgBZk.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QMainWindow, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_SplashScreen(object):
    def setupUi(self, SplashScreen):
        if not SplashScreen.objectName():
            SplashScreen.setObjectName(u"SplashScreen")
        SplashScreen.resize(300, 300)
        SplashScreen.setMinimumSize(QSize(300, 300))
        SplashScreen.setMaximumSize(QSize(300, 300))
        self.centralwidget = QWidget(SplashScreen)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setStyleSheet("#centralwidget {background-image: url(splash.png);}")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(5, 5, 5, 5)
        self.container = QFrame(self.centralwidget)
        self.container.setObjectName(u"container")
        self.container.setFrameShape(QFrame.Shape.NoFrame)
        # self.container.setFrameShadow(QFrame.Shadow.Raised)
        self.verticallayout_1 = QVBoxLayout(self.container)
        self.verticallayout_1.setSpacing(0)
        self.verticallayout_1.setObjectName(u"verticallayout_1")
        self.verticallayout_1.setContentsMargins(20, 20, 20, 20)
        self.circle_bg = QFrame(self.container)
        self.circle_bg.setObjectName(u"circle_bg")

        self.horizontalLayout_3 = QHBoxLayout(self.circle_bg)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.texts = QFrame(self.circle_bg)
        self.texts.setObjectName(u"texts")
        self.texts.setFixedHeight(230)
        self.texts.setStyleSheet("font-weight: bold;")

        self.texts.setFrameShape(QFrame.Shape.NoFrame)
        self.texts.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.texts)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(5)
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 20, 0, 0)
        self.empty = QFrame(self.texts)
        self.empty.setObjectName(u"empty")
        self.empty.setMinimumSize(QSize(0, 60))
        self.empty.setFrameShape(QFrame.Shape.NoFrame)
        self.empty.setFrameShadow(QFrame.Shadow.Raised)

        self.gridLayout.addWidget(self.empty, 2, 0, 1, 1)

        self.loading = QLabel(self.texts)
        self.loading.setFixedHeight(20)
        self.loading.setObjectName(u"loading")
        self.loading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.loading, 4, 0, 1, 1)

        self.title = QLabel(self.texts)
        self.title.setObjectName(u"title")
        self.title.setMinimumSize(QSize(0, 30))
        self.title.setStyleSheet("""
                                 	color: rgb(248, 248, 242);
	                                font: bold 12pt \"굴림\";
                                 """)

        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.warn_message = QLabel("※ GNSS에 의한 지적측량규정 숙지 ※", self.container)
        self.warn_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.warn_message.setFixedHeight(20)
        self.warn_message.setStyleSheet("""
                                        color: rgb(255, 184, 108);
                                        background-color: none;
                                        font: bold 9pt \"굴림\";
                                       """)

        self.gridLayout.addWidget(self.title, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.warn_message, 1, 0, 1, 1)


        self.frame_2 = QFrame(self.texts)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_2.setFixedHeight(100)
        self.frame_2.setContentsMargins(0, 5, 0,75)

        self.horizontalLayout_4 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(5, 5, 5, 5)

        self.version = QLabel(self.frame_2)        
        self.version.setObjectName(u"version")
        self.version.setFixedSize(130, 20)
        self.version.setStyleSheet("""QLabel {
                                      color: rgb(248, 248, 242);
                                      background-color: rgb(68, 71, 90);
                                      border-radius: 10px;
                                      font: bold 9pt \"Seoge UI\";    
                                      }""")
        self.version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.horizontalLayout_4.addWidget(self.version)

        self.gridLayout.addWidget(self.frame_2, 3, 0, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.horizontalLayout_3.addWidget(self.texts)
        self.verticallayout_1.addWidget(self.circle_bg)

        self.horizontalLayout.addWidget(self.container)
        SplashScreen.setCentralWidget(self.centralwidget)

        self.retranslateUi(SplashScreen)
        QMetaObject.connectSlotsByName(SplashScreen)
    # setupUi

    def retranslateUi(self, SplashScreen):
        SplashScreen.setWindowTitle(QCoreApplication.translate("SplashScreen", u"Loading...", None))
        self.loading.setText(QCoreApplication.translate("SplashScreen", u"Loading...", None))
        self.title.setText(QCoreApplication.translate("SplashScreen", u"지적기준점 성과표", None))
        self.version.setText(QCoreApplication.translate("SplashScreen", u"v1.0.0 - Beta 1", None))
    # retranslateUi

