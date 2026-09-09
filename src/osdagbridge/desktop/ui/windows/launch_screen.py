"""
Launch screen UI for OsdagBridge GUI.
Displays splash screen with animation and logos.
"""
import osdagbridge.desktop.resources.mainPageIcons_rc

from PySide6.QtCore import (QCoreApplication, QMetaObject, QEasingCurve,
                            QRect, QTimer, Qt, QPropertyAnimation)
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QLabel, QWidget)
from PySide6.QtSvgWidgets import QSvgWidget

from osdagbridge import __version__ as VERSION


class OsdagBridgeLaunchScreen(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"SplashScreen_MainWindow")
        MainWindow.resize(610, 400)
        MainWindow.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        MainWindow.setAttribute(Qt.WA_TranslucentBackground)
        MainWindow.setWindowIcon(QIcon(":/vectors/Osdag_logo.svg"))

        def close_on_click(event):
            MainWindow.hide()

        MainWindow.mouseDoubleClickEvent = close_on_click
        MainWindow.setCursor(Qt.CursorShape.ArrowCursor)

        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"SplashScreen_CentralWidget")

        self.AestheticVector = QSvgWidget(self.centralwidget)
        self.AestheticVector.setObjectName(u"SplashScreen_AestheticVector")
        self.AestheticVector.setGeometry(QRect(2, 3, 606, 308))

        self.OsdagLogo = QSvgWidget(self.centralwidget)
        self.OsdagLogo.setObjectName(u"SplashScreen_OsdagLogo")
        self.OsdagLogo.setGeometry(QRect(20, 20, 81, 81))

        # ======== POP-IN ANIMATION ========
        # Set initial small size at the same position
        start_rect = QRect(45, 45, 10, 10)  # Start with a small size
        end_rect = QRect(20, 20, 81, 81)    # End with the desired size

        self.OsdagLogo.setGeometry(start_rect)

        # Create geometry (size and position) animation
        self.logo_pop_anim = QPropertyAnimation(self.OsdagLogo, b"geometry")
        self.logo_pop_anim.setDuration(1000)  # 1 second duration
        self.logo_pop_anim.setStartValue(start_rect)
        self.logo_pop_anim.setEndValue(end_rect)
        self.logo_pop_anim.setEasingCurve(QEasingCurve.OutBack)  # Adds a slight overshoot for a "pop" feel

        # Start animation
        self.logo_pop_anim.start()
        # ======== END OF ANIMATION ========

        self.OsdagLabel = QSvgWidget(self.centralwidget)
        self.OsdagLabel.setObjectName(u"SplashScreen_OsdagLabel")
        self.OsdagLabel.setGeometry(QRect(115, 23, 170, 75))

        self.OsdagTagline = QSvgWidget(self.centralwidget)
        self.OsdagTagline.setObjectName(u"SplashScreen_OsdagTagline")
        self.OsdagTagline.setGeometry(QRect(20, 120, 350, 29))

        self.VersionLabel = QLabel(self.centralwidget)
        self.VersionLabel.setObjectName("splash_version_label")
        self.VersionLabel.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.VersionLabel.setGeometry(QRect(20, 155, 200, 16))

        self.DescriptionLabel = QLabel(self.centralwidget)
        self.DescriptionLabel.setObjectName("splash_description_label")
        self.DescriptionLabel.setGeometry(QRect(20, 190, 360, 112))
        self.DescriptionLabel.setWordWrap(True)
        self.DescriptionLabel.setTextFormat(Qt.TextFormat.RichText)
        self.DescriptionLabel.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )

        self.LoadingLabel = QLabel(self.centralwidget)
        self.LoadingLabel.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.LoadingLabel.setGeometry(QRect(20, 310, 200, 30))
        self.LoadingLabel.setObjectName("splash_loading_label")

        # aligned to the right with margin(top = right = 10 wrt size of MainWindow)
        self.IITBLogo = QSvgWidget(self.centralwidget)
        self.IITBLogo.setObjectName(u"SplashScreen_IITBLogo")
        self.IITBLogo.setGeometry(QRect(508, 10, 92, 90))

        self.FOSSEELogo = QSvgWidget(self.centralwidget)
        self.FOSSEELogo.setObjectName(u"SplashScreen_FOSSEELogo")
        self.FOSSEELogo.setGeometry(QRect(20, 340, 111, 41))

        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

        # To Trigger Updation
        self.show_dot = 0
        self.timer = QTimer(MainWindow)
        self.timer.timeout.connect(self.simulateLoading)
        # Blinking Time
        self.timer.start(1000)

    def simulateLoading(self):
        if self.show_dot == 0:
            self.LoadingLabel.setText(f"Loading application .  ")
            self.show_dot = 1
        elif self.show_dot == 1:
            self.LoadingLabel.setText(f"Loading application .. ")
            self.show_dot = 2
        elif self.show_dot == 2:
            self.LoadingLabel.setText(f"Loading application ...")
            self.show_dot = 3
        elif self.show_dot == 3:
            self.LoadingLabel.setText(f"Loading application    ")
            self.show_dot = 0

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("Splash Screen", u"Splash Screen", None))

        self.AestheticVector.load(":/vectors/contour_lines.svg")

        self.OsdagLogo.load(":/vectors/Osdag_logo.svg")

        self.OsdagLabel.load(":/vectors/OsdagBridge_label_light.svg")

        self.OsdagTagline.load(":/vectors/OsdagBridge_tagline_light.svg")

        self.VersionLabel.setText(f"Version {VERSION}")

        self.DescriptionLabel.setText(
            "<p>OsdagBridge is a cross-platform <b>free and open-source software "
            "for the design (and detailing) of steel bridges</b>, following the "
            "relevant Indian Standards and IRC codes.</p>"
            "<p>OsdagBridge is licensed under LGPL v3. Osdag&reg; and the Osdag "
            "logo are registered trademarks of Indian Institute of Technology "
            "Bombay (IIT Bombay).</p>"
        )

        self.LoadingLabel.setText(f"Loading application    ")

        self.IITBLogo.load(":/vectors/IITB_Launch.svg")

        self.FOSSEELogo.load(":/vectors/FOSSEE_light.svg")
