from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QFrame,


    QGridLayout,

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


        self.setStyleSheet("background-color: #f5f5f5;")
        page_layout = QVBoxLayout(self)

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
         
            if section_type == "input_group" and section_id == "wind_inputs_section":
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
                        
                        row_layout.addWidget(widget)
                    
                    elif field_type == "combo":
                        widget = QComboBox()
                        widget.addItems(field.get("choices", []))
                        if field.get("default"):
                            widget.setCurrentText(field.get("default"))
                        widget.setFixedSize(COMBO_WIDTH, FIELD_HEIGHT)
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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: #ffffff;")
        left_layout = QVBoxLayout(scroll_content)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        label_style = "font-size: 11px; color: #3a3a3a; background: transparent; border: none;"
        field_width = 120

        wind_inputs_box = QFrame()
        wind_inputs_box.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }")
        wind_inputs_layout = QVBoxLayout(wind_inputs_box)
        wind_inputs_layout.setContentsMargins(12, 12, 12, 12)
        wind_inputs_layout.setSpacing(10)

        wind_title = QLabel("Wind Load (WL) Inputs for Evaluation per IRC6")
        wind_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;")
        wind_inputs_layout.addWidget(wind_title)

        wind_grid = QGridLayout()
        wind_grid.setContentsMargins(0, 4, 0, 0)
        wind_grid.setHorizontalSpacing(12)
        wind_grid.setVerticalSpacing(8)
        wind_grid.setColumnMinimumWidth(0, 220)

        row = 0

        def add_line(label_text, attr_name, is_combo=False, items=None, placeholder=None, enable_on_custom=False):
            nonlocal row
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            widget = QComboBox() if is_combo else QLineEdit()
            if is_combo and items:
                widget.addItems(items)
            if placeholder and not is_combo:
                widget.setPlaceholderText(placeholder)
            widget.setFixedWidth(field_width)
            apply_field_style(widget)
            wind_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
            wind_grid.addWidget(widget, row, 1, Qt.AlignLeft)
            setattr(owner, attr_name, widget)
            row += 1
            return widget

        add_line("Basic Wind Speed (m/s):", "basic_wind_speed_input")
        add_line("Average Exposed Height (m):", "avg_exposed_height_input")
        add_line("Type of Terrain:", "terrain_type_combo", is_combo=True, items=["Plain", "Hilly", "Coastal"])
        add_line("Site Topography:", "site_topography_combo", is_combo=True, items=["Flat", "Hilly", "Ridge", "Valley"])
        owner.gust_factor_combo = add_line("Gust Factor, G:", "gust_factor_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.gust_factor_value = add_line("", "gust_factor_value", placeholder="Value")
        owner.gust_factor_value.setEnabled(False)
        owner.drag_coeff_combo = add_line("Drag Coefficient, CD:", "drag_coeff_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.drag_coeff_value = add_line("", "drag_coeff_value", placeholder="Custom Value")
        owner.drag_coeff_value.setEnabled(False)
        owner.drag_coeff_ll_combo = add_line("Drag Coefficient against Live Load, CDLL:", "drag_coeff_ll_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.drag_coeff_ll_value = add_line("", "drag_coeff_ll_value", placeholder="Value")
        owner.drag_coeff_ll_value.setEnabled(False)
        owner.lift_coeff_combo = add_line("Lift Coefficient, CL:", "lift_coeff_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.lift_coeff_value = add_line("", "lift_coeff_value", placeholder="Value")
        owner.lift_coeff_value.setEnabled(False)
        owner.super_area_elev_combo = add_line("Superstructure Area in Elevation (m2):", "super_area_elev_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.super_area_elev_value = add_line("", "super_area_elev_value", placeholder="Custom Value")
        owner.super_area_elev_value.setEnabled(False)
        owner.super_area_plain_combo = add_line("Superstructure Area in Plain (m2):", "super_area_plain_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.super_area_plain_value = add_line("", "super_area_plain_value", placeholder="Custom Value")
        owner.super_area_plain_value.setEnabled(False)
        owner.exposed_frontal_area_combo = add_line("Exposed Frontal Area of Live Load (m2):", "exposed_frontal_area_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.exposed_frontal_area_value = add_line("", "exposed_frontal_area_value", placeholder="Custom Value")
        owner.exposed_frontal_area_value.setEnabled(False)
        owner.wind_ecc_deck_combo = add_line("Wind Load Eccentricity from Top of Deck\n(m): Negative for below deck", "wind_ecc_deck_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.wind_ecc_deck_value = add_line("", "wind_ecc_deck_value", placeholder="Value")
        owner.wind_ecc_deck_value.setEnabled(False)
        owner.wind_ll_ecc_combo = add_line("Wind on Live Load Eccentricity from Top\nof Deck (m):", "wind_ll_ecc_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.wind_ll_ecc_value = add_line("", "wind_ll_ecc_value", placeholder="Value")
        owner.wind_ll_ecc_value.setEnabled(False)

        wind_inputs_layout.addLayout(wind_grid)
        left_layout.addWidget(wind_inputs_box)

        computed_box = QFrame()
        computed_box.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }")
        computed_layout = QGridLayout(computed_box)
        computed_layout.setContentsMargins(12, 12, 12, 12)
        computed_layout.setHorizontalSpacing(12)
        computed_layout.setVerticalSpacing(8)
        computed_layout.setColumnMinimumWidth(0, 220)

        computed_fields = [
            ("Hourly Mean Wind Speed (m/s):", "hourly_mean_wind"),
            ("Hourly Wind Pressure in N/m2:", "hourly_wind_pressure"),
            ("Transverse Wind Force in N:", "transverse_wind_force"),
            ("Longitudinal Wind Force in N:", "longitudinal_wind_force"),
            ("Vertical Wind Force in N:", "vertical_wind_force"),
            ("Transverse Wind Force on Live\nLoad in N:", "transverse_wind_ll"),
            ("Longitudinal Wind Force on Live\nLoad in N:", "longitudinal_wind_ll"),
        ]

        owner.wind_computed_fields = {}
        for idx, (label_text, field_name) in enumerate(computed_fields):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            field = QLineEdit()
            field.setFixedWidth(field_width)
            field.setReadOnly(True)
            apply_field_style(field)
            computed_layout.addWidget(lbl, idx, 0, Qt.AlignLeft | Qt.AlignVCenter)
            computed_layout.addWidget(field, idx, 1, Qt.AlignLeft)
            owner.wind_computed_fields[field_name] = field

        left_layout.addWidget(computed_box)
        left_layout.addStretch()

        scroll.setWidget(scroll_content)
        left_card_layout.addWidget(scroll)

        right_card = owner._create_card()
        right_card.setStyleSheet("QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #d4d4d4; }")
        right_card.setMinimumWidth(150)
        right_card.setMaximumWidth(200)

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

        desc_title = QLabel("Description\nBox")
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;")
        right_layout.addWidget(desc_title)
        right_layout.addStretch()

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 1)

        page_layout.addLayout(content_row)

        owner.gust_factor_combo.currentTextChanged.connect(lambda t: owner.gust_factor_value.setEnabled(t == "Custom"))
        owner.drag_coeff_combo.currentTextChanged.connect(lambda t: owner.drag_coeff_value.setEnabled(t == "Custom"))
        owner.drag_coeff_ll_combo.currentTextChanged.connect(lambda t: owner.drag_coeff_ll_value.setEnabled(t == "Custom"))
        owner.lift_coeff_combo.currentTextChanged.connect(lambda t: owner.lift_coeff_value.setEnabled(t == "Custom"))
        owner.super_area_elev_combo.currentTextChanged.connect(lambda t: owner.super_area_elev_value.setEnabled(t == "Custom"))
        owner.super_area_plain_combo.currentTextChanged.connect(lambda t: owner.super_area_plain_value.setEnabled(t == "Custom"))
        owner.exposed_frontal_area_combo.currentTextChanged.connect(lambda t: owner.exposed_frontal_area_value.setEnabled(t == "Custom"))
        owner.wind_ecc_deck_combo.currentTextChanged.connect(lambda t: owner.wind_ecc_deck_value.setEnabled(t == "Custom"))
        owner.wind_ll_ecc_combo.currentTextChanged.connect(lambda t: owner.wind_ll_ecc_value.setEnabled(t == "Custom"))

