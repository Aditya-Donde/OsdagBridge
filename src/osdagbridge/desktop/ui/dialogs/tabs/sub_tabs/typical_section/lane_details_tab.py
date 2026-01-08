"""Lane Details sub-tab for Typical Section Details (schema-driven header)."""
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QTableWidget,
    QHeaderView,
    QHBoxLayout,
)
from PySide6.QtCore import Qt

from osdagbridge.core.bridge_types.plate_girder.typical_section_schema import LANE_DETAILS_TAB_SCHEMA


class LaneDetailsTab(QWidget):
    """Constructs the Lane Details tab UI and binds fields to the owner."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setStyleSheet("background-color: white;")
        self._build_ui()

    def _create_field(self, field_def):
        owner = self.owner
        ftype = field_def.get("type")
        if ftype == "combo":
            field = QComboBox()
            field.addItems(field_def.get("choices") or [])
        else:
            return None

        field.setObjectName(field_def.get("id", ""))
        owner.style_input_field(field)

        # Make the lane count combo wider for readability
        bind_name = field_def.get("bind")
        if field_def.get("id") == "lane_count" or bind_name == "lane_count_combo":
            try:
                field.setFixedWidth(180)
            except Exception:
                pass

        bind_name = field_def.get("bind")
        if bind_name:
            setattr(owner, bind_name, field)

        on_change = field_def.get("on_change")
        if on_change and hasattr(owner, on_change):
            field.currentTextChanged.connect(getattr(owner, on_change))

        return field

    def _build_ui(self):
        owner = self.owner

        lane_layout = QVBoxLayout(self)
        lane_layout.setContentsMargins(18, 6, 18, 12)
        lane_layout.setSpacing(0)

        card, card_layout = owner._create_section_card("Inputs:")

        selector_layout = QHBoxLayout()
        selector_layout.setContentsMargins(0, 0, 0, 0)
        selector_layout.setSpacing(12)

        for row in LANE_DETAILS_TAB_SCHEMA.get("rows", []):
            for field_def in row.get("fields", []):
                label = QLabel(field_def.get("label", ""))
                label.setStyleSheet("font-size: 11px; color: #000;")
                selector_layout.addWidget(label)

                field = self._create_field(field_def)
                if field:
                    selector_layout.addWidget(field)

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
                color: #333333;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
                color: #333333;
            }
            QTableWidget::item:hover {
                background-color: #e8f4f8;
                color: #333333;
            }
            QTableWidget::item:selected {
                background-color: #d0e8f0;
                color: #333333;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #333333;
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
        # Note: Lane table population is handled by owner._initialize_lane_defaults()

