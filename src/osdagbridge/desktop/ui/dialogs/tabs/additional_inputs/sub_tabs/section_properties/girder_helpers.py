from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QWidget,
)

from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style


class BoundsDialog(QDialog):
    def __init__(self, title: str, bounds: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setStyleSheet("QDialog { background: #ffffff; border: 1px solid #90AF13; }")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(1, 1, 1, 1)
        root_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(parent=self)
        self.title_bar.setTitle(title)
        root_layout.addWidget(self.title_bar)

        content = QWidget(self)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 24, 20, 20)
        layout.setSpacing(18)

        # Inputs
        form = QHBoxLayout()
        form.setSpacing(16)

        def add_input(label: str, value: float):
            col = QVBoxLayout()
            col.setSpacing(6)
            col.addWidget(QLabel(label))
            edit = QLineEdit(str(value))
            apply_field_style(edit)
            col.addWidget(edit)
            form.addLayout(col)
            return edit

        self.lower_input = add_input("Lower Bound:", bounds.get("lower", 0.0))
        self.upper_input = add_input("Upper Bound:", bounds.get("upper", 1000.0))
        self.increment_input = add_input("Increment:", bounds.get("increment", 1.0))

        layout.addLayout(form)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch(1)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 32)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setFixedSize(100, 32)
        save_btn.setStyleSheet("background: #90AF13; color: white; font-weight: bold; border-radius: 4px;")
        save_btn.clicked.connect(self._on_accept)
        btns.addWidget(save_btn)

        layout.addLayout(btns)
        root_layout.addWidget(content)

        self._result = None

    def _on_accept(self) -> None:
        lower = self._parse_positive(self.lower_input.text())
        upper = self._parse_positive(self.upper_input.text())
        increment = self._parse_positive(self.increment_input.text())

        if lower is None or upper is None or increment is None:
            QMessageBox.warning(self, "Invalid Bounds", "Please enter valid positive numeric values.")
            return
        if upper <= lower:
            QMessageBox.warning(self, "Invalid Bounds", "Upper bound must be greater than lower bound.")
            return
        if increment <= 0.0:
            QMessageBox.warning(self, "Invalid Bounds", "Increment must be greater than zero.")
            return

        self._result = {
            "lower": float(lower),
            "upper": float(upper),
            "increment": float(increment),
        }
        self.accept()

    @staticmethod
    def _parse_positive(text: str) -> Optional[float]:
        try:
            return float(str(text).strip())
        except Exception:
            return None

    def result_bounds(self) -> Optional[dict]:
        return self._result


class ThicknessSelectionDialog(QDialog):
    def __init__(self, title: str, values: list[float], current: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setMinimumWidth(320)
        self.setStyleSheet("QDialog { background: white; border: 1px solid #90AF13; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)

        self.title_bar = CustomTitleBar(parent=self)
        self.title_bar.setTitle(title)
        root.addWidget(self.title_bar)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        
        from PySide6.QtWidgets import QListWidget
        self.list_widget = QListWidget()
        for v in values:
            self.list_widget.addItem(f"{v:.1f}")
        
        # Select current
        try:
            items = self.list_widget.findItems(f"{float(current):.1f}", Qt.MatchExactly)
            if items:
                self.list_widget.setCurrentItem(items[0])
        except Exception:
            pass
            
        layout.addWidget(self.list_widget)

        btns = QHBoxLayout()
        btns.addStretch(1)
        cbtn = QPushButton("Cancel")
        cbtn.clicked.connect(self.reject)
        btns.addWidget(cbtn)
        sbtn = QPushButton("Select")
        sbtn.setStyleSheet("background: #90AF13; color: white;")
        sbtn.clicked.connect(self.accept)
        btns.addWidget(sbtn)
        layout.addLayout(btns)
        root.addWidget(content)

    def selected_value(self) -> Optional[float]:
        item = self.list_widget.currentItem()
        if not item: return None
        try:
            return float(item.text())
        except Exception:
            return None
