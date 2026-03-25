"""
Combobox UI utilities.

Provides enhanced combobox views with:
- Greyed-out disabled items
- Smart cursor behaviour
- Better UX feedback for selectable vs non-selectable items
"""

from PySide6.QtWidgets import QListView, QStyledItemDelegate
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


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

#----------------------------------------------------------------------------------
#   To create a checkbox with text that supports HTML formatting (e.g. subscripts)
#----------------------------------------------------------------------------------
from PySide6.QtWidgets import QCheckBox, QStyleOptionButton, QStyle, QApplication
from PySide6.QtGui import QPainter, QTextDocument
from PySide6.QtCore import Qt, QSize, QPoint


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