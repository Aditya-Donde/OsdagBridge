from PySide6.QtCore import Qt, QLocale
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox, QLineEdit
from PySide6.QtGui import QDoubleValidator

from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import PERMANENT_LOAD_TAB_SCHEMA

LABEL_MIN_WIDTH = 220
FIELD_WIDTH = 180
FIELD_HEIGHT = 28


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
        left_card_layout = QVBoxLayout(left_card)
        left_card_layout.setContentsMargins(0, 0, 0, 0)
        left_card_layout.setSpacing(0)

        content_wrapper = QWidget()
        content_wrapper.setStyleSheet("background-color: #ffffff;")
        left_layout = QVBoxLayout(content_wrapper)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(12)

        schema = PERMANENT_LOAD_TAB_SCHEMA
        label_width = schema.get("label_width", LABEL_MIN_WIDTH)

        for section in schema.get("sections", []):
            section_box = self._create_section_box(section, label_width)
            left_layout.addWidget(section_box)

        left_layout.addStretch()
        left_card_layout.addWidget(content_wrapper)

        right_card = owner._create_card()
        right_card.setStyleSheet(
            "QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #d4d4d4; }"
        )
        right_card.setMinimumWidth(260)
        right_card.setMinimumHeight(420)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        description = schema.get("description", {})
        
        desc_title = QLabel(description.get("title", "Description Box"))
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #000000; background: transparent; border: none;")
        right_layout.addWidget(desc_title)

        desc_text = QLabel(description.get("text", ""))
        desc_text.setWordWrap(True)
        desc_text.setStyleSheet("font-size: 11px; color: #4b4b4b; background: transparent; border: none;")
        right_layout.addWidget(desc_text)
        right_layout.addStretch()

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 2)

        page_layout.addLayout(content_row)

    def _create_section_box(self, section, label_width):
        """Create a grouped section box from schema definition"""
        section_box = QFrame()
        section_box.setStyleSheet("""
            QFrame {
                border: 1px solid #9c9c9c;
                border-radius: 6px;
                background-color: #ffffff;
                padding: 0px;
            }
        """)
        section_box_layout = QVBoxLayout(section_box)
        section_box_layout.setContentsMargins(12, 12, 12, 12)
        section_box_layout.setSpacing(14)

        if "title" in section:
            title_label = QLabel(section["title"])
            title_label.setStyleSheet("font-size: 11px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
            section_box_layout.addWidget(title_label)

        label_style = "font-size: 11px; font-weight: 600; color: #3a3a3a; background: transparent; border: none;"
        
        for field_def in section.get("fields", []):
            row = QHBoxLayout()
            row.setSpacing(10)

            label = QLabel(field_def["label"])
            label.setStyleSheet(label_style)
            label.setMinimumWidth(label_width)
            row.addWidget(label)

            widget = self._create_field_widget(field_def)
            widget.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
            row.addWidget(widget)
            
            row.addStretch()
            section_box_layout.addLayout(row)

        return section_box

    def _create_field_widget(self, field_def):
        """Create widget from field definition and bind it"""
        field_type = field_def.get("type")
        bind_name = field_def.get("bind")

        if field_type == "combo":
            widget = self.owner._create_yes_no_combo() if field_def.get("choices") == ["Yes", "No"] else QComboBox()
            
            if field_def.get("choices") != ["Yes", "No"]:
                choices = field_def.get("choices", [])
                widget.addItems(choices)
            
            default = field_def.get("default")
            if default:
                widget.setCurrentText(default)
                
        elif field_type == "line":
            widget = self.owner._create_line_edit()
        
            default = field_def.get("default")
            if default:
                widget.setText(default)
            
            validator_def = field_def.get("validator")
            if validator_def and validator_def.get("type") == "double_range":
                validator = QDoubleValidator(
                    validator_def.get("bottom", 0.0),
                    validator_def.get("top", 999999.0),
                    validator_def.get("decimals", 2),
                    widget
                )
                validator.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
                validator.setNotation(QDoubleValidator.StandardNotation)
                widget.setValidator(validator)
        else:
            widget = self.owner._create_line_edit()

        if bind_name:
            setattr(self, bind_name, widget)

        return widget

    def update_dependency_states(self, has_median: bool, has_footpath: bool):
        """
        Enable/disable load options based on basic inputs
        """
        # Median dependency
        if hasattr(self, 'include_median_combo'):
            self.include_median_combo.setEnabled(has_median)
            if not has_median:
                self.include_median_combo.setCurrentText("No")

        # Railing dependency
        if hasattr(self, 'include_railing_combo'):
            self.include_railing_combo.setEnabled(has_footpath)
            if not has_footpath:
                self.include_railing_combo.setCurrentText("No")
    
    def reset_defaults(self):
        """Reset Permanent Load inputs to default values"""
        schema = PERMANENT_LOAD_TAB_SCHEMA
        
        for section in schema.get("sections", []):
            for field_def in section.get("fields", []):
                bind_name = field_def.get("bind")
                default = field_def.get("default")
                
                if bind_name and default and hasattr(self, bind_name):
                    widget = getattr(self, bind_name)
                    
                    if isinstance(widget, QComboBox):
                        widget.setCurrentText(default)
                    elif isinstance(widget, QLineEdit):
                        widget.setText(default)