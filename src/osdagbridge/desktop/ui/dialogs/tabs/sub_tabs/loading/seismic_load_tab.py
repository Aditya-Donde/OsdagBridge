from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QFrame,
    QScrollArea,
)

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import SEISMIC_LOAD_TAB_SCHEMA

class SeismicLoadTab(QWidget):
    """Seismic/Earthquake Load tab content extracted from LoadingTab."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.schema = SEISMIC_LOAD_TAB_SCHEMA
        self._build_ui()

    def _build_ui(self):
        owner = self.owner
        schema = self.schema

        LABEL_MIN_WIDTH = schema.get("label_width", 220)
        FIELD_WIDTH = schema.get("field_width", 180)
        FIELD_HEIGHT = schema.get("field_height", 28)

        self.setStyleSheet("background-color: #f5f5f5;")
     
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background-color: #f5f5f5; border: none; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #f5f5f5;")
        page_layout = QVBoxLayout(scroll_content)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(12)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(16)

        left_card = owner._create_card()
        left_card.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }")
        left_card_layout = QVBoxLayout(left_card)
        left_card_layout.setContentsMargins(0, 0, 0, 0)
        left_card_layout.setSpacing(0)

        content_wrapper = QWidget()
        content_wrapper.setStyleSheet("background-color: #ffffff;")
        left_layout = QVBoxLayout(content_wrapper)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(12)

        label_style = "font-size: 11px; font-weight: 600; color: #3a3a3a; background: transparent; border: none;"

        for section in schema.get("sections", []):
            section_type = section.get("type")
            section_id = section.get("id")
         
            if section_type == "input_group" and section_id == "seismic_inputs_section":
                seismic_inputs_box = QFrame()
                seismic_inputs_box.setStyleSheet("""
                    QFrame {
                        border: 1px solid #9c9c9c;
                        border-radius: 6px;
                        background-color: #ffffff;
                        padding: 0px;
                    }
                """)
                seismic_inputs_box_layout = QVBoxLayout(seismic_inputs_box)
                seismic_inputs_box_layout.setContentsMargins(12, 12, 12, 12)
                seismic_inputs_box_layout.setSpacing(14)

                seismic_title = QLabel(section.get("title", ""))
                seismic_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
                seismic_inputs_box_layout.addWidget(seismic_title)

                for field in section.get("fields", []):
                    field_type = field.get("type")
                    
                    row_layout = QHBoxLayout()
                    row_layout.setSpacing(10)
                    
                    lbl = QLabel(field.get("label", ""))
                    lbl.setStyleSheet(label_style)
                    lbl.setMinimumWidth(LABEL_MIN_WIDTH)
                    row_layout.addWidget(lbl)
    
                    if field_type == "combo":
                        widget = QComboBox()
                        widget.addItems(field.get("choices", []))
                        if field.get("default"):
                            widget.setCurrentText(field.get("default"))
                        widget.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
                        apply_field_style(widget)
                        
                        bind_name = field.get("bind")
                        if bind_name:
                            setattr(self, bind_name, widget)

                        # Seismic zone combo (if configured as combo) is derived from project location output.
                        row_layout.addWidget(widget)
                    
                    elif field_type == "line":
                        widget = QLineEdit()
                        if field.get("default"):
                            widget.setText(field.get("default"))
                        widget.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
                        apply_field_style(widget)
                        
                        bind_name = field.get("bind")
                        if bind_name:
                            setattr(self, bind_name, widget)

                        if field.get("id") == "seismic_zone":
                            widget.setReadOnly(True)
                            widget.setToolTip("Auto-filled from software output (project location seismic zone)")
                            
                        if not field.get("enabled", True):
                            widget.setEnabled(False)
                        
                        row_layout.addWidget(widget)
                    
                    elif field_type == "mode_line":
                        mode_combo = QComboBox()
                        mode_combo.addItems(field.get("mode_choices", []))
                        if field.get("default_mode"):
                            mode_combo.setCurrentText(field.get("default_mode"))
                        mode_combo.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
                        apply_field_style(mode_combo)
                        
                        mode_bind = field.get("bind_mode")
                        if mode_bind:
                            setattr(self, mode_bind, mode_combo)
                        
                        row_layout.addWidget(mode_combo)
                        
                        value_input = QLineEdit()
                        value_input.setPlaceholderText(field.get("placeholder", ""))
                        value_input.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
                        value_input.setEnabled(False)
                        apply_field_style(value_input)
                        
                        value_bind = field.get("bind_value")
                        if value_bind:
                            setattr(self, value_bind, value_input)
                        
                        row_layout.addWidget(value_input)
                    
                    row_layout.addStretch()
                    seismic_inputs_box_layout.addLayout(row_layout)

                left_layout.addWidget(seismic_inputs_box)
         
            elif section_type == "computed_group" and section_id == "computed_values_section":
                computed_box = QFrame()
                computed_box.setStyleSheet("""
                    QFrame {
                        border: 1px solid #9c9c9c;
                        border-radius: 6px;
                        background-color: #ffffff;
                        padding: 0px;
                    }
                """)
                computed_box_layout = QVBoxLayout(computed_box)
                computed_box_layout.setContentsMargins(12, 12, 12, 12)
                computed_box_layout.setSpacing(14)

                computed_title = QLabel(section.get("title", ""))
                computed_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
                computed_box_layout.addWidget(computed_title)

                self.seismic_computed_fields = {}
                
                for field in section.get("fields", []):
                    row_layout = QHBoxLayout()
                    row_layout.setSpacing(10)
                    
                    lbl = QLabel(field.get("label", ""))
                    lbl.setStyleSheet(label_style)
                    lbl.setMinimumWidth(LABEL_MIN_WIDTH)
                    
                    computed_field = QLineEdit()
                    computed_field.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
                    computed_field.setReadOnly(True)
                    computed_field.setStyleSheet("""
                        QLineEdit {
                            background-color: #f0f0f0;
                            border: 1px solid #8a8a8a;
                            border-radius: 5px;
                            padding: 5px 8px;
                            color: #5a5a5a;
                            font-size: 11px;
                        }
                    """)
                    
                    bind_name = field.get("bind")
                    if bind_name:
                        self.seismic_computed_fields[bind_name] = computed_field
                    
                    row_layout.addWidget(lbl)
                    row_layout.addWidget(computed_field)
                    row_layout.addStretch()
                    
                    computed_box_layout.addLayout(row_layout)

                left_layout.addWidget(computed_box)

        left_layout.addStretch()
        left_card_layout.addWidget(content_wrapper)

        right_card = owner._create_card()
        right_card.setStyleSheet("QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #d4d4d4; }")
        right_card.setMinimumWidth(260)
        right_card.setMinimumHeight(420)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        description = schema.get("description", {})
        desc_title = QLabel(description.get("title", ""))
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

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        seismic_inputs = next(
            (s for s in schema.get("sections", []) if s.get("id") == "seismic_inputs_section"),
            None
        )
        
        if seismic_inputs:
            for field in seismic_inputs.get("fields", []):
                on_mode_change = field.get("on_mode_change")
                if on_mode_change:
                    mode_bind = field.get("bind_mode")
                    if mode_bind and hasattr(self, mode_bind):
                        combo = getattr(self, mode_bind)
                        combo.currentTextChanged.connect(lambda _: self._toggle_seismic_custom_inputs())
      
        self._apply_seismic_defaults()
        self._toggle_seismic_custom_inputs()
    
        if hasattr(self.owner, "project_seismic_zone") and hasattr(self, "seismic_zone_combo"):
            zone_val = str(self.owner.project_seismic_zone)
            if isinstance(self.seismic_zone_combo, QComboBox):
                self.seismic_zone_combo.setCurrentText(zone_val)
            elif isinstance(self.seismic_zone_combo, QLineEdit):
                self.seismic_zone_combo.setText(zone_val)

    def _apply_seismic_defaults(self):
        """Apply default values from schema"""
        seismic_inputs = next(
            (s for s in self.schema.get("sections", []) if s.get("id") == "seismic_inputs_section"),
            None
        )
        
        if not seismic_inputs:
            return
        
        for field in seismic_inputs.get("fields", []):
            bind_name = field.get("bind") or field.get("bind_mode")
            if not bind_name or not hasattr(self, bind_name):
                continue
            
            widget = getattr(self, bind_name)
            default_value = field.get("default") or field.get("default_mode")
            
            if default_value:
                if isinstance(widget, QComboBox):
                    widget.setCurrentText(default_value)
                elif isinstance(widget, QLineEdit):
                    widget.setText(default_value)

    def _toggle_seismic_custom_inputs(self):
        """Enable/disable custom inputs based on mode selection"""
        if hasattr(self, 'dead_load_seismic_combo') and hasattr(self, 'dead_load_custom_input'):
            dead_is_custom = self.dead_load_seismic_combo.currentText() == "Custom"
            self.dead_load_custom_input.setEnabled(dead_is_custom)

        if hasattr(self, 'live_load_seismic_combo') and hasattr(self, 'live_load_custom_input'):
            live_is_custom = self.live_load_seismic_combo.currentText() == "Custom"
            self.live_load_custom_input.setEnabled(live_is_custom)

    def reset_defaults(self):
        """Reset Seismic Load inputs to schema default values"""
        self._apply_seismic_defaults()
        self._toggle_seismic_custom_inputs()
        
    def update_project_location(self, location_data):
        if not location_data:
            return
            
        weather = location_data.get("weather_data")
        if weather:
            zone = weather.get("zone")
            z_val = weather.get("z_value")
            
            if zone is not None and hasattr(self, "seismic_zone_combo"):
                if isinstance(self.seismic_zone_combo, QComboBox):
                    # Check if 'zone' text exists in choices, avoiding errors
                    idx = self.seismic_zone_combo.findText(str(zone))
                    if idx >= 0:
                        self.seismic_zone_combo.setCurrentIndex(idx)
                elif isinstance(self.seismic_zone_combo, QLineEdit):
                    self.seismic_zone_combo.setText(str(zone))
                    
            if z_val is not None and "zone_factor" in getattr(self, "seismic_computed_fields", {}):
                self.seismic_computed_fields["zone_factor"].setText(str(z_val))