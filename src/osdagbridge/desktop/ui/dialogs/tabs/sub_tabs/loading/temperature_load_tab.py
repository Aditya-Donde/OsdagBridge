from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import TEMPERATURE_LOAD_TAB_SCHEMA


class TemperatureLoadTab(QWidget):
    """Temperature load inputs for evaluation per IRC 6."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self._build_ui()

    def _build_ui(self):
        owner = self.owner
        schema = TEMPERATURE_LOAD_TAB_SCHEMA

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
        left_layout.setSpacing(12)

        label_style = "font-size: 11px; color: #3a3a3a; background: transparent; border: none;"
        heading_style = "font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;"
        field_width = schema.get("field_width", 140)
        label_width = schema.get("label_width", 240)

        readonly_input_style = """
        QLineEdit {
            color: #9e9e9e;
            background-color: #f3f3f3;
            border: 1px solid #3a3a3a;
            border-radius: 4px;
            padding: 4px;
        }
        """

        for section in schema.get("sections", []):
            section_box = QFrame()
            section_box.setStyleSheet(
                "QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }"
            )
            section_layout = QVBoxLayout(section_box)
            section_layout.setContentsMargins(12, 12, 12, 12)
            section_layout.setSpacing(10)

            section_title = QLabel(section.get("title", ""))
            section_title.setStyleSheet(heading_style)
            section_layout.addWidget(section_title)

            grid = QGridLayout()
            grid.setContentsMargins(0, 4, 0, 0)
            grid.setHorizontalSpacing(12)
            grid.setVerticalSpacing(10)
            grid.setColumnMinimumWidth(0, label_width)

            row = 0
            for field in section.get("fields", []):
                lbl = QLabel(field.get("label", ""))
                lbl.setStyleSheet(label_style)
                grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)

                input_widget = QLineEdit()
                input_widget.setFixedWidth(field_width)
                apply_field_style(input_widget)

                if "placeholder" in field:
                    input_widget.setPlaceholderText(field["placeholder"])

                if "default" in field:
                    input_widget.setText(field["default"])

                if "validator" in field:
                    validator_config = field["validator"]
                    if validator_config["type"] == "double_range":
                        validator = QDoubleValidator(
                            validator_config["bottom"],
                            validator_config["top"],
                            validator_config.get("decimals", 2),
                            input_widget
                        )
                        validator.setNotation(QDoubleValidator.StandardNotation)
                        input_widget.setValidator(validator)
                    elif validator_config["type"] == "int_range":
                        validator = QIntValidator(
                            validator_config["bottom"],
                            validator_config["top"],
                            input_widget
                        )
                        input_widget.setValidator(validator)

                if field.get("read_only", False):
                    input_widget.setReadOnly(True)
                    input_widget.setStyleSheet(readonly_input_style)

                bind_name = field.get("bind")
                if bind_name:
                    setattr(owner, bind_name, input_widget)

                grid.addWidget(input_widget, row, 1, Qt.AlignLeft)
                row += 1

            section_layout.addLayout(grid)
            left_layout.addWidget(section_box)

        left_layout.addStretch()

        right_card = owner._create_card()
        right_card.setStyleSheet(
            "QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #d4d4d4; }"
        )
        right_card.setMinimumWidth(230)
        right_card.setMinimumHeight(520)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        desc_title = QLabel("Description Box")
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet(
            "font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;"
        )
        right_layout.addWidget(desc_title)
        right_layout.addStretch()

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 2)

        page_layout.addLayout(content_row)