from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel


class PermanentLoadTab(QWidget):
    """Permanent Load tab content extracted from LoadingTab."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self._build_ui()

    def _build_ui(self):
        owner = self.owner

        self.setStyleSheet("background-color: #f5f5f5;")
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(12)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(16)

        left_card = owner._create_card()
        left_card.setStyleSheet(
            "QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }"
        )
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(16)

        owner._add_load_section(left_layout, "Dead Load (DL):", [
            ("Include Member Self Weight:", owner._create_yes_no_combo()),
            ("Self-weight factor:", owner._create_line_edit()),
            ("Include Concrete Deck Weight:", owner._create_yes_no_combo()),
        ])

        owner._add_load_section(left_layout, "Dead Load for Surfacing (DW):", [
            ("Include Load from Wearing Course:", owner._create_yes_no_combo()),
        ])

        owner._add_load_section(left_layout, "Super-Imposed Dead Load (SIDL):", [
            ("Include Load from Crash Barrier:", owner._create_yes_no_combo()),
            ("Include Load from Median:", owner._create_yes_no_combo()),
            ("Include Load from Railing:", owner._create_yes_no_combo()),
        ])

        left_layout.addStretch()

        right_card = owner._create_card()
        right_card.setStyleSheet(
            "QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #c8c8c8; }"
        )
        right_card.setMinimumWidth(270)
        right_card.setMinimumHeight(360)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(12)
        description_label = QLabel("Description Box")
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #000000;")
        description_label.setMinimumHeight(320)
        right_layout.addWidget(description_label)

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 2)

        page_layout.addLayout(content_row)
