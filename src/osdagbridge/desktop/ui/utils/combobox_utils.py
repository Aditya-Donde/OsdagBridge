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