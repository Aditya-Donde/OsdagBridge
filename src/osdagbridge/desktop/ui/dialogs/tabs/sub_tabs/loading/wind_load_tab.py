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
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import WIND_LOAD_TAB_SCHEMA

class WindLoadTab(QWidget):
    """Wind Load tab content extracted from LoadingTab."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.schema = WIND_LOAD_TAB_SCHEMA
        self._build_ui()

    def _build_ui(self):
        owner = self.owner
        schema = self.schema
      
        LABEL_MIN_WIDTH = schema.get("label_width", 260)
        FIELD_WIDTH = schema.get("field_width", 140)
        FIELD_HEIGHT = schema.get("field_height", 28)
        COMBO_WIDTH = FIELD_WIDTH  

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
         
            if section_type == "input_group":
                wind_inputs_box = QFrame()
                wind_inputs_box.setStyleSheet("""
                    QFrame {
                        border: 1px solid #9c9c9c;
                        border-radius: 6px;
                        background-color: #ffffff;
                        padding: 0px;
                    }
                """)
                wind_inputs_layout = QVBoxLayout(wind_inputs_box)
                wind_inputs_layout.setContentsMargins(12, 12, 12, 12)
                wind_inputs_layout.setSpacing(14)

                wind_title = QLabel(section.get("title", ""))
                wind_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
                wind_inputs_layout.addWidget(wind_title)

                for field in section.get("fields", []):
                    field_type = field.get("type")
                    field_id = field.get("id")
                    
                    row_layout = QHBoxLayout()
                    row_layout.setSpacing(10)
                    
                    lbl = QLabel(field.get("label", ""))
                    lbl.setStyleSheet(label_style)
                    lbl.setMinimumWidth(LABEL_MIN_WIDTH)
                    row_layout.addWidget(lbl)
              
                    if field_type == "line":
                        widget = QLineEdit()
                        if field.get("default"):
                            widget.setText(field.get("default"))
                        if field.get("placeholder"):
                            widget.setPlaceholderText(field.get("placeholder"))
                        widget.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
                        apply_field_style(widget)
                        
                        bind_name = field.get("bind")
                        if bind_name:
                            setattr(owner, bind_name, widget)

                        if field.get("read_only"):
                            widget.setReadOnly(True)
                            if field_id == "basic_wind_speed":
                                widget.setToolTip("Auto-filled from software output (project location wind speed)")
                                
                        if not field.get("enabled", True):
                            widget.setEnabled(False)
                        
                        row_layout.addWidget(widget)
                    
                    elif field_type == "combo":
                        widget = QComboBox()
                        widget.addItems(field.get("choices", []))
                        if field.get("default"):
                            widget.setCurrentText(field.get("default"))
                        combo_width = COMBO_WIDTH
                        widget.setFixedSize(combo_width, FIELD_HEIGHT)
                        apply_field_style(widget)
                        
                        bind_name = field.get("bind")
                        if bind_name:
                            setattr(owner, bind_name, widget)
                        
                        row_layout.addWidget(widget)
                    
                    elif field_type == "mode_line":
                        mode_combo = QComboBox()
                        mode_combo.addItems(field.get("mode_choices", []))
                        if field.get("default_mode"):
                            mode_combo.setCurrentText(field.get("default_mode"))
                        mode_combo.setFixedSize(COMBO_WIDTH, FIELD_HEIGHT)
                        apply_field_style(mode_combo)
                        
                        mode_bind = field.get("bind_mode")
                        if mode_bind:
                            setattr(owner, mode_bind, mode_combo)
                        
                        row_layout.addWidget(mode_combo)
            
                        value_input = QLineEdit()
                        if field.get("default_value"):
                            value_input.setText(field.get("default_value"))
                        if field.get("placeholder"):
                            value_input.setPlaceholderText(field.get("placeholder"))
                        value_input.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
                        value_input.setEnabled(False)
                        apply_field_style(value_input)
                        
                        value_bind = field.get("bind_value")
                        if value_bind:
                            setattr(owner, value_bind, value_input)
                        
                        row_layout.addWidget(value_input)
                    
                    row_layout.addStretch()
                    wind_inputs_layout.addLayout(row_layout)

                left_layout.addWidget(wind_inputs_box)

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

                owner.wind_computed_fields = {}
                
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
                        owner.wind_computed_fields[bind_name] = computed_field
                    
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

        wind_inputs = next(
            (s for s in schema.get("sections", []) if s.get("id") == "wind_inputs_section"),
            None
        )
        
        if wind_inputs:
            for field in wind_inputs.get("fields", []):
                if field.get("type") == "mode_line":
                    mode_bind = field.get("bind_mode")
                    value_bind = field.get("bind_value")
                    
                    if mode_bind and value_bind and hasattr(owner, mode_bind) and hasattr(owner, value_bind):
                        mode_combo = getattr(owner, mode_bind)
                        value_input = getattr(owner, value_bind)
                      
                        mode_combo.currentTextChanged.connect(
                            lambda text, v=value_input: v.setEnabled(text == "Custom")
                        )
        self.reset_defaults()

    def _block(self, widgets, block=True):
        """Temporarily block signals for a list of widgets"""
        for w in widgets:
            if w is not None:
                w.blockSignals(block)

    def reset_defaults(self):
        """Reset Wind Load inputs to schema default values"""
        wind_inputs = next(
            (s for s in self.schema.get("sections", []) if s.get("id") == "wind_inputs_section"),
            None
        )
        
        if not wind_inputs:
            return
       
        mode_combos = []
        for field in wind_inputs.get("fields", []):
            if field.get("type") == "mode_line":
                mode_bind = field.get("bind_mode")
                if mode_bind and hasattr(self.owner, mode_bind):
                    mode_combos.append(getattr(self.owner, mode_bind))
      
        self._block(mode_combos, True)
        
        for field in wind_inputs.get("fields", []):
            field_type = field.get("type")
            
            if field_type == "line":
                bind_name = field.get("bind")
                if bind_name and hasattr(self.owner, bind_name):
                    widget = getattr(self.owner, bind_name)
                    default_value = field.get("default", "")
                    widget.setText(default_value)
            
            elif field_type == "combo":
                bind_name = field.get("bind")
                if bind_name and hasattr(self.owner, bind_name):
                    widget = getattr(self.owner, bind_name)
                    default_value = field.get("default")
                    if default_value:
                        widget.setCurrentText(default_value)
            
            elif field_type == "mode_line":
                mode_bind = field.get("bind_mode")
                value_bind = field.get("bind_value")
                
                if mode_bind and hasattr(self.owner, mode_bind):
                    mode_combo = getattr(self.owner, mode_bind)
                    default_mode = field.get("default_mode", "Automatic")
                    mode_combo.setCurrentText(default_mode)
                
                if value_bind and hasattr(self.owner, value_bind):
                    value_input = getattr(self.owner, value_bind)
                    default_value = field.get("default_value", "")
                    
                    if default_value:
                        value_input.setText(default_value)
                    else:
                        value_input.clear()
                  
                    value_input.setEnabled(False)
                    
        self._block(mode_combos, False)

    def update_project_location(self, location_data):
        if not location_data:
            return
            
        weather = location_data.get("weather_data")
        if weather:
            wind = weather.get("wind_speed")
            
            if wind is not None and hasattr(self.owner, "basic_wind_speed_input"):
                self.owner.basic_wind_speed_input.setText(str(wind))