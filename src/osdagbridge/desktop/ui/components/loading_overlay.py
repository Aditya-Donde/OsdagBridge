"""
Loading overlay for OsdagBridge GUI.

Covers the active tab body with a spinner while a module is being built, so
the app never looks frozen during the slow parts of opening a module.

The spinner repaints on a QTimer, which only fires when the GUI thread gets to
process events. Long synchronous builds should therefore call pump()
periodically - see UIBuilder.__init__ and AdditionalInputs.init_ui.
"""
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QElapsedTimer, QEvent, QEventLoop, QRectF, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen

# Brand green, matching the rest of the shell
SPINNER_COLOR = QColor("#90AF13")
TRACK_COLOR = QColor("#E2E2E2")
TEXT_COLOR = QColor("#3A3A3A")
VEIL_COLOR = QColor(255, 255, 255, 235)

SPINNER_RADIUS = 26
SPINNER_THICKNESS = 4
ARC_LENGTH = 100

# One full turn per second, derived from elapsed time rather than tick count so
# the arc is in the right place even when repaints are sparse.
DEGREES_PER_SECOND = 360
FRAME_INTERVAL_MS = 16

# How many overlays are currently running. pump() is a no-op unless one is.
_active_overlays = 0


def pump():
    """Let a running loading overlay repaint during long GUI-thread work.

    User input stays excluded, so a half-built widget tree cannot be re-entered
    by a stray click. Does nothing when no overlay is on screen, which keeps
    the widget builders behaving exactly as before outside a module open.
    """
    if _active_overlays:
        QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)


class LoadingOverlay(QWidget):
    """Translucent veil with a spinner and a message."""

    def __init__(self, parent, message="Loading..."):
        super().__init__(parent)
        self.message = message
        self.uptime = QElapsedTimer()

        # Sitting on top of the page is enough to swallow clicks aimed at the
        # widgets underneath, so no explicit mouse grab is needed.
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setCursor(Qt.CursorShape.BusyCursor)
        self.setGeometry(parent.rect())
        parent.installEventFilter(self)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)

    # ── Lifecycle ────────────────────────────────────────────────────────────
    def start(self):
        global _active_overlays
        _active_overlays += 1
        self.uptime.start()
        self.setGeometry(self.parentWidget().rect())
        self.show()
        self.raise_()
        self.timer.start(FRAME_INTERVAL_MS)

    def stop(self):
        global _active_overlays
        _active_overlays = max(0, _active_overlays - 1)
        self.timer.stop()
        parent = self.parentWidget()
        if parent is not None:
            parent.removeEventFilter(self)
        self.hide()
        self.deleteLater()

    def set_message(self, message):
        self.message = message
        self.update()

    # ── Painting ─────────────────────────────────────────────────────────────
    def eventFilter(self, obj, event):
        # Keep covering the whole page when the window is resized
        if obj is self.parentWidget() and event.type() == QEvent.Resize:
            self.setGeometry(self.parentWidget().rect())
        return super().eventFilter(obj, event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), VEIL_COLOR)

        centre = self.rect().center()
        box = QRectF(
            centre.x() - SPINNER_RADIUS,
            centre.y() - SPINNER_RADIUS - 20,
            SPINNER_RADIUS * 2,
            SPINNER_RADIUS * 2,
        )

        # Full ring behind the moving arc, so the gap reads as motion
        pen = QPen(TRACK_COLOR, SPINNER_THICKNESS, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(box, 0, 360 * 16)

        # Qt angles are in 1/16th of a degree, counter-clockwise from 3 o'clock
        pen.setColor(SPINNER_COLOR)
        painter.setPen(pen)
        angle = (self.uptime.elapsed() * DEGREES_PER_SECOND / 1000.0) % 360
        painter.drawArc(box, int(-angle * 16), -ARC_LENGTH * 16)

        painter.setPen(TEXT_COLOR)
        font = QFont(self.font())
        font.setPointSize(11)
        painter.setFont(font)
        text_box = self.rect().adjusted(0, int(SPINNER_RADIUS * 2) + 10, 0, 0)
        painter.drawText(text_box, Qt.AlignHCenter | Qt.AlignVCenter, self.message)
