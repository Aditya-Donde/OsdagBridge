"""Lane Details sub-tab for Typical Section Details."""
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QComboBox,
    QTableWidget,
    QHeaderView,
    QHBoxLayout,
)
from PySide6.QtCore import Qt


class LaneDetailsTab(QWidget):
    """Constructs the Lane Details tab UI and binds fields to the owner."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setStyleSheet("background-color: white;")
        self._build_ui()

    def _build_ui(self):
        owner = self.owner

        lane_layout = QVBoxLayout(self)
        lane_layout.setContentsMargins(18, 6, 18, 12)
        lane_layout.setSpacing(0)

        card, card_layout = owner._create_section_card("Inputs:")

        selector_layout = QHBoxLayout()
        selector_layout.setContentsMargins(0, 0, 0, 0)
        selector_layout.setSpacing(12)

        lanes_label = QLabel("No. of Traffic Lanes:")
        lanes_label.setStyleSheet("font-size: 11px; color: #000;")
        selector_layout.addWidget(lanes_label)

        owner.lane_count_combo = QComboBox()
        owner.lane_count_combo.addItems([str(i) for i in range(1, 7)])
        owner.style_input_field(owner.lane_count_combo)
        owner.lane_count_combo.currentTextChanged.connect(owner.on_lane_count_changed)
        selector_layout.addWidget(owner.lane_count_combo)
        selector_layout.addStretch()

        card_layout.addLayout(selector_layout)

        owner.lane_table = QTableWidget()
        owner.lane_table.setColumnCount(3)
        owner.lane_table.setHorizontalHeaderLabels([
            "Traffic Lane Number",
            "Distance from inner edge of crash barrier to left edge of lane (m)",
            "Lane Width (m)",
        ])
        header = owner.lane_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        owner.lane_table.verticalHeader().setVisible(False)
        owner.lane_table.setAlternatingRowColors(True)
        owner.lane_table.setStyleSheet(
            """
            QTableWidget { 
                background-color: #ffffff;
                alternate-background-color: #f9f9f9;
                gridline-color: #e0e0e0;
                border: 1px solid #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableWidget::item:hover {
                background-color: #e8f4f8;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #333;
                padding: 8px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
                font-size: 11px;
            }
            """
        )

        card_layout.addWidget(owner.lane_table)
        lane_layout.addWidget(card)
        lane_layout.addStretch()

        owner._update_lane_details_rows(owner.lane_count_combo.currentText())

