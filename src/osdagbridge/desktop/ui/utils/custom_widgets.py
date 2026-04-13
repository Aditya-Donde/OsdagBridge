"""
Combobox UI utilities.

Provides enhanced combobox views with:
- Greyed-out disabled items
- Smart cursor behaviour
- Better UX feedback for selectable vs non-selectable items
"""

from PySide6.QtWidgets import QListView, QStyledItemDelegate, QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainterPath

# =================================================================================
#   ITEM DELEGATE FOR DISABLED ITEMS
# =================================================================================

class ComboBoxItemDelegate(QStyledItemDelegate):
    """
    Custom delegate to render disabled combobox items in grey.

    This improves UX by visually distinguishing disabled options
    from selectable ones in dropdown lists.
    """

    def paint(self, painter, option, index):
        model = index.model()
        item = model.item(index.row()) if hasattr(model, "item") else None

        if item and not item.isEnabled():
            # Draw background normally
            painter.fillRect(option.rect, option.palette.base())

            # Draw disabled text in grey
            painter.setPen(QColor(120, 120, 120))
            text = index.data()
            painter.drawText(
                option.rect,
                Qt.AlignLeft | Qt.AlignVCenter,
                f"  {text}",
            )
        else:
            super().paint(painter, option, index)


# =================================================================================
#   SMART COMBOBOX VIEW
# =================================================================================

class SmartCursorComboBoxView(QListView):
    """
    Custom QListView used inside QComboBox.

    Features:
    - Shows pointing hand cursor for enabled items
    - Shows forbidden cursor for disabled items
    - Uses ComboBoxItemDelegate for grey rendering
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Apply custom delegate
        self.setItemDelegate(ComboBoxItemDelegate())

    def mouseMoveEvent(self, event):
        """
        Update cursor depending on whether hovered item is enabled.
        """
        index = self.indexAt(event.pos())

        if index.isValid():
            model = index.model()
            item = model.item(index.row()) if hasattr(model, "item") else None

            if item and not item.isEnabled():
                self.setCursor(Qt.ForbiddenCursor)
            else:
                self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.PointingHandCursor)

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        """
        Reset cursor when leaving the dropdown.
        """
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)

from PySide6.QtWidgets import QCheckBox, QLabel, QHBoxLayout
from PySide6.QtWidgets import QCheckBox, QStyleOptionButton, QStyle, QApplication
from PySide6.QtGui import QPainter, QTextDocument
from PySide6.QtCore import Qt, QSize, QPoint

#----------------------------------------------------------------------------------
#   To create a checkbox with text that supports HTML formatting (e.g. subscripts)
#----------------------------------------------------------------------------------
class RichCheckBox(QCheckBox):
    def __init__(self, text="", parent=None):
        super().__init__("", parent)  # Keep native text empty
        self._rich_text = text

    def setText(self, text: str):
        self._rich_text = text
        self.updateGeometry()
        self.update()

    def text(self) -> str:
        return self._rich_text

    def _doc(self) -> QTextDocument:
        """Build a QTextDocument from the rich text."""
        doc = QTextDocument()
        doc.setDefaultFont(self.font())
        doc.setHtml(self._rich_text)
        return doc

    def sizeHint(self) -> QSize:
        doc = self._doc()
        # Ideal (unconstrained) size of the HTML content
        doc.setTextWidth(-1)
        text_size = doc.size()

        opt = QStyleOptionButton()
        self.initStyleOption(opt)

        # Width of the native checkbox indicator
        indicator_w = self.style().pixelMetric(
            QStyle.PM_IndicatorWidth, opt, self
        )
        spacing = self.style().pixelMetric(
            QStyle.PM_CheckBoxLabelSpacing, opt, self
        )

        w = indicator_w + spacing + int(text_size.width())
        h = max(
            self.style().pixelMetric(QStyle.PM_IndicatorHeight, opt, self),
            int(text_size.height()),
        )
        return QSize(w + 4, h + 4)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        opt = QStyleOptionButton()
        self.initStyleOption(opt)

        # --- 1. Draw ONLY the checkbox indicator (no text) ---
        opt.text = ""
        indicator_rect = self.style().subElementRect(
            QStyle.SE_CheckBoxIndicator, opt, self
        )
        opt.rect = indicator_rect
        self.style().drawControl(QStyle.CE_CheckBox, opt, painter, self)

        # --- 2. Draw rich text with QTextDocument ---
        indicator_w = self.style().pixelMetric(QStyle.PM_IndicatorWidth, opt, self)
        spacing = self.style().pixelMetric(QStyle.PM_CheckBoxLabelSpacing, opt, self)

        text_x = indicator_w + spacing
        text_y = (self.height() - int(self._doc().size().height())) // 2

        painter.save()
        painter.translate(QPoint(text_x, text_y))

        doc = self._doc()
        doc.setTextWidth(self.width() - text_x)
        doc.drawContents(painter)

        painter.restore()

#=================Percentage-bar widget (for OutputDock)==============================================
"""
Usage
    bar = PercentBarWidget(label="Strength Limit State (Flexure)", value=80)
    bar = PercentBarWidget(label="Strength Limit State (Shear)",   value=120)

    # Update at runtime:
    bar.set_value(95)

Visual behaviour
----------------
  value < 100  →  green fill, proportional width, "XX%" text to the right
  value >= 100 →  red   fill, full  width,         "XX%" text to the right
"""

# ── Colours ───────────────────────────────────────────────────────────────────
COLOR_GREEN      = QColor("#90AF13")   # matches dock accent
COLOR_RED        = QColor("#CC2222")
COLOR_TRACK      = QColor("#D8D8D8")   # unfilled portion

BAR_HEIGHT       = 6           # px — height of the progress track
PCT_LABEL_WIDTH  = 46          # px — fixed width reserved for "120%" text
LABEL_STYLE      = "QLabel { font-size:13px; color:#222; background:transparent; }"
PCT_LABEL_STYLE  = "QLabel { font-size:12px; font-weight:bold; color:#444; background:transparent; }"


# ── Inner bar widget ──────────────────────────────────────────────────────────

class _BarPainter(QWidget):
    """Custom-painted progress track."""

    def __init__(self, value: float, parent=None):
        super().__init__(parent)
        self._value = max(0.0, float(value))
        self.setFixedHeight(BAR_HEIGHT)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_value(self, value: float):
        self._value = max(0.0, float(value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        radius = h / 2.0

        exceeded   = self._value >= 100.0
        fill_ratio = 1.0 if exceeded else self._value / 100.0
        fill_w     = w * fill_ratio

        painter.setPen(Qt.NoPen)

        # ── Full rounded track pill ───────────────────────────────────────────
        track_path = QPainterPath()
        track_path.addRoundedRect(QRectF(0, 0, w, h), radius, radius)
        painter.setBrush(COLOR_TRACK)
        painter.drawPath(track_path)

        # ── Fill clipped to track shape ───────────────────────────────────────
        if fill_w > 0:
            fill_color = COLOR_RED if exceeded else COLOR_GREEN
            fill_rect_path = QPainterPath()
            fill_rect_path.addRect(QRectF(0, 0, fill_w, h))
            clipped = track_path.intersected(fill_rect_path)
            painter.setBrush(fill_color)
            painter.drawPath(clipped)

        painter.end()


# ── Public widget ─────────────────────────────────────────────────────────────

class PercentBarWidget(QWidget):
    """
    [Label (wraps, constrained to bar width)]
    [bar ────────────────────────────────── ] XX%
    """

    def __init__(self, label: str = "", value: float = 0.0, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 5, 0, 0)
        root.setSpacing(4)

        # ── Label — max-width kept in sync with bar via resizeEvent ───────────
        lbl = QLabel(label)
        lbl.setStyleSheet(LABEL_STYLE)
        lbl.setTextFormat(Qt.RichText)
        lbl.setWordWrap(True)
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._lbl = lbl
        root.addWidget(lbl)

        # ── Bar row ───────────────────────────────────────────────────────────
        bar_row = QHBoxLayout()
        bar_row.setContentsMargins(0, 0, 0, 0)
        bar_row.setSpacing(8)

        self._bar = _BarPainter(value)
        bar_row.addWidget(self._bar, 1)

        self._pct_label = QLabel(self._fmt(value))
        self._pct_label.setStyleSheet(PCT_LABEL_STYLE)
        self._pct_label.setFixedWidth(PCT_LABEL_WIDTH)
        self._pct_label.setAlignment(Qt.AlignCenter)
        bar_row.addWidget(self._pct_label)

        root.addLayout(bar_row)

    def resizeEvent(self, event):
        """Keep label max-width aligned to the bar column (excludes pct label)."""
        super().resizeEvent(event)
        bar_w = self.width() - PCT_LABEL_WIDTH - 8  # 8 = bar_row spacing
        if bar_w > 0:
            self._lbl.setMaximumWidth(bar_w)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_value(self, value: float):
        self._bar.set_value(value)
        self._pct_label.setText(self._fmt(value))

    @staticmethod
    def _fmt(value: float) -> str:
        return f"{int(round(value))}%"
    

#---------Standalone-Testing------------------------------------
import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
 
if __name__ == "__main__":
    app = QApplication(sys.argv)
 
    win = QWidget()
    win.setWindowTitle("PercentBar Test")
    win.setMinimumWidth(480)
    win.setStyleSheet("background-color: white;")
 
    layout = QVBoxLayout(win)
    layout.setContentsMargins(24, 24, 24, 24)
    layout.setSpacing(16)
 
    layout.addWidget(PercentBarWidget("Strength Limit State (Flexure)", 80))
    layout.addWidget(PercentBarWidget(
        "Strength Limit State (Shear) — Very Long Label That Should Wrap Here", 120
    )),
    layout.addWidget(PercentBarWidget(
        "Strength Limit State (Shear) — Very Long Label That Should Wrap Here", 100
    )),
    layout.addWidget(PercentBarWidget("Strength Limit State (Flexure)", 99.9))
    layout.addWidget(PercentBarWidget("Strength Limit State (Flexure)", 99.4))
    layout.addStretch()
 
    win.show()
    sys.exit(app.exec())

#-------------