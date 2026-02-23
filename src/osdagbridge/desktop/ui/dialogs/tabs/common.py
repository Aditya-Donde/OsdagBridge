"""Shared helpers for the Additional Inputs dialog and its tabs."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QFrame,
    QSizePolicy,
    QPushButton,
    QHBoxLayout,
)


class CheckableComboBox(QComboBox):
    """Multi-select combo with All/individual toggle behavior."""

    checkedItemsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        model = QStandardItemModel(self)
        self.setModel(model)
        self._updating_selection = False
        model.itemChanged.connect(self._handle_item_changed)

    def addItem(self, text, userData=None):  # noqa: N802 (Qt naming)
        super().addItem(text, userData)
        self._initialize_item(self.count() - 1)

    def addItems(self, texts):  # noqa: N802 (Qt naming)
        for text in texts:
            self.addItem(text)

    def _initialize_item(self, index):
        item = self.model().item(index)
        if not item:
            return
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        item.setData(
            Qt.Checked if item.text().strip().lower() == "all" else Qt.Unchecked,
            Qt.CheckStateRole,
        )

    def _handle_item_changed(self, item):
        if self._updating_selection or item is None:
            return
        self._updating_selection = True
        try:
            if item.text().strip().lower() == "all":
                if item.checkState() == Qt.Checked:
                    self._uncheck_non_all_items()
            else:
                if item.checkState() == Qt.Checked:
                    self._uncheck_all_item()
        finally:
            self._updating_selection = False
        self.checkedItemsChanged.emit()

    def _uncheck_non_all_items(self):
        for row in range(self.model().rowCount()):
            item = self.model().item(row)
            if item and item.text().strip().lower() != "all":
                item.setCheckState(Qt.Unchecked)

    def _uncheck_all_item(self):
        for row in range(self.model().rowCount()):
            item = self.model().item(row)
            if item and item.text().strip().lower() == "all":
                item.setCheckState(Qt.Unchecked)
                break

    def checked_items(self, include_all: bool = False):
        selected, all_checked = [], False
        for row in range(self.model().rowCount()):
            item = self.model().item(row)
            if not item or item.checkState() != Qt.Checked:
                continue
            text = item.text()
            if text.strip().lower() == "all":
                all_checked = True
                if include_all:
                    selected.append(text)
            else:
                selected.append(text)
        if all_checked and not include_all:
            return []
        return selected



def get_combobox_style():
    """Return the common stylesheet for dropdowns with the SVG icon from resources."""
    return """
        QComboBox{
            padding: 1px 7px;
            border: 1px solid black;
            border-radius: 5px;
            background-color: white;
            color: black;
        }
        QComboBox::drop-down{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            border-left: 0px;
        }
        QComboBox::down-arrow{
            image: url(:/vectors/arrow_down_light.svg);
            width: 20px;
            height: 20px;
            margin-right: 8px;
        }
        QComboBox::down-arrow:on {
            image: url(:/vectors/arrow_up_light.svg);
            width: 20px;
            height: 20px;
            margin-right: 8px;
        }
        QComboBox QAbstractItemView{
            background-color: white;
            border: 1px solid black;
            outline: none;
        }
        QComboBox QAbstractItemView::item{
            color: black;
            background-color: white;
            border: none;
            border: 1px solid white;
            border-radius: 0;
            padding: 2px;
        }
        QComboBox QAbstractItemView::item:hover{
            border: 1px solid #90AF13;
            background-color: #90AF13;
            color: black;
        }
        QComboBox QAbstractItemView::item:selected{
            background-color: #90AF13;
            color: black;
            border: 1px solid #90AF13;
        }
        QComboBox QAbstractItemView::item:selected:hover{
            background-color: #90AF13;
            color: black;
            border: 1px solid #94b816;
        }
        QComboBox:disabled{
            background: #f1f1f1;
            color: #666;
        }
    """


def get_lineedit_style():
    """Return the shared stylesheet for line edits in the section inputs."""
    return """
        QLineEdit {
            padding: 1px 7px;
            border: 1px solid #070707;
            border-radius: 6px;
            background-color: white;
            color: #000000;
            font-weight: normal;
        }
        QLineEdit:disabled{
            background: #f1f1f1;
            color: #666;
        }
        QLineEdit:read-only{
            background: #f6f6f6;
            color: #555555;
        }
        QLineEdit:hover {
            border: 1px solid #5d5d5d;
        }
    """


def apply_field_style(widget):
    """Apply the appropriate style to combo boxes and line edits."""
    widget.setMinimumHeight(28)
    if isinstance(widget, QComboBox):
        widget.setStyleSheet(get_combobox_style())
    elif isinstance(widget, QLineEdit):
        widget.setStyleSheet(get_lineedit_style())


SECTION_NAV_BUTTON_STYLE = """
    QPushButton {
        background-color: #f4f4f4;
        border: 2px solid #d2d2d2;
        border-radius: 12px;
        padding: 20px 16px;
        text-align: left;
        font-weight: bold;
        font-size: 12px;
        color: #333333;
    }
    QPushButton:hover {
        border-color: #b5b5b5;
    }
    QPushButton:checked {
        background-color: #9ecb3d;
        border-color: #7da523;
        color: #ffffff;
    }
"""


def create_action_button_bar(parent=None):
    """Create a standardized Defaults/Save bar with gray backing."""
    frame = QFrame(parent)
    frame.setObjectName("actionButtonBar")
    frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    frame.setStyleSheet("""
        QFrame#actionButtonBar {
            background-color: #ededed;
            border: 1px solid #c8c8c8;
            border-radius: 6px;
        }
        QFrame#actionButtonBar QPushButton {
            background-color: #ffffff;
            color: #2f2f2f;
            font-weight: 600;
            border: 1px solid #8c8c8c;
            border-radius: 4px;
            padding: 6px 24px;
            min-width: 120px;
        }
        QFrame#actionButtonBar QPushButton:hover {
            background-color: #f6f6f6;
        }
        QFrame#actionButtonBar QPushButton:pressed {
            background-color: #e0e0e0;
        }
    """)

    layout = QHBoxLayout(frame)
    layout.setContentsMargins(22, 10, 22, 10)
    layout.setSpacing(12)
    layout.addStretch()

    defaults_button = QPushButton("Defaults", frame)
    save_button = QPushButton("Save", frame)
    layout.addWidget(defaults_button)
    layout.addWidget(save_button)
    layout.addStretch()

    return frame, defaults_button, save_button
