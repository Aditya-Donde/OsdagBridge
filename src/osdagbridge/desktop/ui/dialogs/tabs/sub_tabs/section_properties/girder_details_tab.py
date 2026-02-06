"""Schema-driven Girder Details tab for member properties."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QScrollArea, QSizePolicy, QFrame, QGridLayout
)
from PySide6.QtCore import Qt

from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import GIRDER_DETAILS_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style


class GirderDetailsTab(QWidget):
    """Tab for Girder Details using the schema definition."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.welded_rows = []
        self.rolled_rows = []
        self.section_property_inputs = {}
        self.girder_count = 2
        self.widgets = {}
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        main_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        content.setStyleSheet("background-color: white;")

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 0, 10, 10)
        content_layout.setSpacing(12)

        content_layout.addWidget(self._build_overview_card())
        content_layout.addWidget(self._build_section_card())
        content_layout.addStretch()

    def _build_overview_card(self):
        card = self._create_card_frame()
        layout = QGridLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(12)

        row = 0
        for field_def in GIRDER_DETAILS_SCHEMA["overview"]:
            label = self._create_label(field_def["label"])
            widget = self._create_field(field_def)
            if field_def.get("id") == "span":
                layout.addWidget(label, row, 2)
                layout.addWidget(widget, row, 3)
            else:
                layout.addWidget(label, row, 0)
                layout.addWidget(widget, row, 1)
            row += 1

        self.member_id_input = QLineEdit("G1-1")
        apply_field_style(self.member_id_input)
        self._set_field_width(self.member_id_input)

        self.length_input = QLineEdit("30")
        apply_field_style(self.length_input)
        self._set_field_width(self.length_input)

        layout.addWidget(self._create_label("Member ID:"), row, 0)
        layout.addWidget(self.member_id_input, row, 1)
        layout.addWidget(self._create_label("Length (m):"), row, 2)
        layout.addWidget(self.length_input, row, 3)
        row += 1

        self.distance_start_input = QLineEdit("0")
        self.distance_end_input = QLineEdit("30")
        apply_field_style(self.distance_start_input)
        apply_field_style(self.distance_end_input)
        self._set_field_width(self.distance_start_input, 80)
        self._set_field_width(self.distance_end_input, 80)

        layout.addWidget(self._create_label("Distance from left edge (m):"), row, 0)
        layout.addLayout(self._build_distance_row(), row, 1)

        layout.addWidget(self._create_label("Member:"), row, 2)
        member_combo = self._create_member_combo()
        layout.addWidget(member_combo, row, 3)

        return card

    def _build_distance_row(self):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(self._create_small_label("Start"))
        row.addWidget(self.distance_start_input)
        row.addWidget(self._create_small_label("End"))
        row.addWidget(self.distance_end_input)
        return row

    def _build_section_card(self):
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)

        left_column = QWidget()
        left_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_column_layout = QVBoxLayout(left_column)
        left_column_layout.setContentsMargins(0, 0, 0, 0)
        left_column_layout.setSpacing(12)

        section_inputs_box = self._create_inner_box()
        section_inputs_layout = QVBoxLayout(section_inputs_box)
        section_inputs_layout.setContentsMargins(12, 8, 12, 12)
        section_inputs_layout.setSpacing(8)

        section_inputs_title = self._create_label("Section Inputs:")
        section_inputs_layout.addWidget(section_inputs_title)

        inputs_grid = QGridLayout()
        inputs_grid.setContentsMargins(0, 0, 0, 0)
        inputs_grid.setHorizontalSpacing(16)
        inputs_grid.setVerticalSpacing(12)
        inputs_grid.setColumnMinimumWidth(0, 150)
        inputs_grid.setColumnStretch(0, 0)
        inputs_grid.setColumnStretch(1, 1)

        row = 0
        for field_def in GIRDER_DETAILS_SCHEMA["section_inputs"]:
            if field_def.get("id") in {"torsional_restraint", "warping_restraint", "web_type"}:
                continue
            row = self._add_schema_row(inputs_grid, row, field_def)

        section_inputs_layout.addLayout(inputs_grid)
        left_column_layout.addWidget(section_inputs_box)

        restraint_box = self._create_inner_box()
        restraint_layout = QVBoxLayout(restraint_box)
        restraint_layout.setContentsMargins(12, 8, 12, 12)
        restraint_layout.setSpacing(8)

        restraint_title = self._create_label("Restraint & Web Details:")
        restraint_layout.addWidget(restraint_title)

        restraint_grid = QGridLayout()
        restraint_grid.setContentsMargins(0, 0, 0, 0)
        restraint_grid.setHorizontalSpacing(16)
        restraint_grid.setVerticalSpacing(12)
        restraint_grid.setColumnMinimumWidth(0, 150)
        restraint_grid.setColumnStretch(0, 0)
        restraint_grid.setColumnStretch(1, 1)

        rrow = 0
        for field_def in GIRDER_DETAILS_SCHEMA["section_inputs"]:
            if field_def.get("id") in {"torsional_restraint", "warping_restraint", "web_type"}:
                rrow = self._add_schema_row(restraint_grid, rrow, field_def)

        restraint_layout.addLayout(restraint_grid)
        left_column_layout.addWidget(restraint_box)

        main_layout.addWidget(left_column)

        right_column = QWidget()
        right_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_column_layout = QVBoxLayout(right_column)
        right_column_layout.setContentsMargins(0, 0, 0, 0)
        right_column_layout.setSpacing(12)

        image_box = self._create_inner_box()
        image_layout = QVBoxLayout(image_box)
        image_layout.setContentsMargins(10, 10, 10, 10)
        image_layout.setSpacing(5)

        self.dynamic_image_label = QLabel("Welded Girder")
        self.dynamic_image_label.setAlignment(Qt.AlignCenter)
        self.dynamic_image_label.setMinimumSize(240, 140)
        self.dynamic_image_label.setStyleSheet("QLabel { border: 1px solid #d0d0d0; border-radius: 4px; background-color: #fafafa; font-weight: bold; color: #5b5b5b; }")
        image_layout.addWidget(self.dynamic_image_label)

        right_column_layout.addWidget(image_box)

        props_box = self._create_inner_box()
        props_layout = QVBoxLayout(props_box)
        props_layout.setContentsMargins(12, 10, 12, 10)
        props_layout.setSpacing(10)

        props_title = self._create_label("Section Properties:")
        props_layout.addWidget(props_title)

        properties_grid = QGridLayout()
        properties_grid.setContentsMargins(0, 0, 0, 0)
        properties_grid.setHorizontalSpacing(12)
        properties_grid.setVerticalSpacing(10)
        properties_grid.setColumnMinimumWidth(0, 140)
        properties_grid.setColumnStretch(0, 0)
        properties_grid.setColumnStretch(1, 1)

        property_fields = [
            "Mass, M (Kg/m)",
            "Sectional Area, a (cm2)",
            "2nd Moment of Area, Iz (cm4)",
            "2nd Moment of Area, Iy (cm4)",
            "Radius of Gyration, rz (cm)",
            "Radius of Gyration, ry (cm)",
            "Elastic Modulus, Zz (cm3)",
            "Elastic Modulus, Zy (cm3)",
            "Plastic Modulus, Zuz (cm3)",
            "Plastic Modulus, Zuy (cm3)",
            "Torsion Constant, It (cm4)",
            "Warping Constant, Iw (cm6)",
        ]

        for index, text in enumerate(property_fields):
            label = self._create_small_label(text)
            line_edit = self._create_line_edit()
            properties_grid.addWidget(label, index, 0)
            properties_grid.addWidget(line_edit, index, 1)
            self.section_property_inputs[text] = line_edit

        props_layout.addLayout(properties_grid)
        right_column_layout.addWidget(props_box)

        main_layout.addWidget(right_column)

        if hasattr(self, "type_combo"):
            self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self._apply_mode_states()
        if hasattr(self, "type_combo"):
            self._on_type_changed(self.type_combo.currentText())

        return container

    def _create_card_frame(self):
        frame = QFrame()
        frame.setObjectName("girderCard")
        frame.setStyleSheet("QFrame#girderCard { background-color: white; border: 1px solid #cfcfcf; border-radius: 10px; }")
        return frame

    def _create_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 12px; color: #2f2f2f; font-weight: 600; background: transparent;")
        label.setAutoFillBackground(False)
        return label

    def _create_small_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 10px; color: #5a5a5a; background: transparent;")
        label.setAutoFillBackground(False)
        return label

    def _create_line_edit(self):
        line_edit = QLineEdit()
        apply_field_style(line_edit)
        return line_edit

    def _create_member_combo(self):
        combo = QComboBox()
        apply_field_style(combo)
        self._set_field_width(combo)
        self.widgets["member_select_combo"] = combo
        self._populate_member_list()
        return combo

    def _create_field(self, field_def):
        field_type = field_def.get("type")
        bind_name = field_def.get("bind")

        if field_type == "combo_dynamic":
            combo = QComboBox()
            apply_field_style(combo)
            self._set_field_width(combo)
            if bind_name:
                self.widgets[bind_name] = combo
            self._populate_girder_lists()
            return combo

        if field_type == "combo":
            combo = QComboBox()
            combo.addItems(field_def.get("choices", []))
            apply_field_style(combo)
            self._set_field_width(combo)
            if bind_name:
                self.widgets[bind_name] = combo
            return combo

        line_edit = QLineEdit()
        apply_field_style(line_edit)
        if bind_name:
            self.widgets[bind_name] = line_edit
        return line_edit

    def _add_schema_row(self, layout, row, field_def):
        visible_for = field_def.get("visible_for")
        tracker = None
        if visible_for:
            if "welded" in visible_for:
                tracker = self.welded_rows
            elif "rolled" in visible_for:
                tracker = self.rolled_rows

        if field_def.get("type") == "mode_line":
            mode_combo = QComboBox()
            mode_combo.addItems(field_def.get("mode_choices", []))
            if field_def.get("default_mode"):
                mode_combo.setCurrentText(field_def["default_mode"])
            apply_field_style(mode_combo)
            self._set_field_width(mode_combo, 130)

            value_field = self._create_line_edit()
            self._set_field_width(value_field)

            bind_mode = field_def.get("bind_mode")
            bind_value = field_def.get("bind_value")
            if bind_mode:
                self.widgets[bind_mode] = mode_combo
            if bind_value:
                self.widgets[bind_value] = value_field

            row = self._add_mode_row(layout, row, field_def["label"], mode_combo, value_field, tracker)
            mode_combo.currentTextChanged.connect(self._apply_mode_states)
            return row

        if field_def.get("type") == "combo":
            combo = QComboBox()
            combo.addItems(field_def.get("choices", []))
            apply_field_style(combo)
            self._set_field_width(combo)
            bind_name = field_def.get("bind")
            if bind_name:
                self.widgets[bind_name] = combo
            return self._add_box_row(layout, row, field_def["label"], combo, tracker)

        widget = self._create_field(field_def)
        return self._add_box_row(layout, row, field_def["label"], widget, tracker)

    def _add_box_row(self, layout, row, label_text, widget, visibility_list=None):
        label = self._create_small_label(label_text)
        layout.addWidget(label, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(widget, row, 1)
        if visibility_list is not None:
            visibility_list.append((label, widget))
        return row + 1

    def _add_mode_row(self, layout, row, label_text, mode_combo, value_field, visibility_list=None):
        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.setSpacing(8)
        wrapper.addWidget(mode_combo)
        wrapper.addWidget(value_field)
        wrapper.addStretch()

        label = self._create_small_label(label_text)
        layout.addWidget(label, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        layout.addLayout(wrapper, row, 1)
        if visibility_list is not None:
            visibility_list.append((label, mode_combo))
            visibility_list.append((None, value_field))
        return row + 1

    def _set_field_width(self, widget, width=230):
        widget.setMaximumWidth(width)
        widget.setMinimumWidth(min(width, 160))

    def _on_type_changed(self, text):
        is_welded = text.lower() == "welded"
        self._set_row_visibility(self.welded_rows, is_welded)
        self._set_row_visibility(self.rolled_rows, not is_welded)
        self.dynamic_image_label.setText("Welded Girder" if is_welded else "Rolled Section")
        self._apply_mode_states()

    def _create_inner_box(self):
        box = QFrame()
        box.setStyleSheet(
            """
            QFrame {
               border: 1px solid #b0b0b0;
               border-radius: 6px;
               background-color: #ffffff;
            }
            QFrame QComboBox, QFrame QLineEdit {
               border: none;
               border-bottom: 1px solid #d0d0d0;
               border-radius: 0px;
               min-height: 28px;
               padding: 4px 8px;
               background-color: #ffffff;
            }
            QFrame QComboBox:hover, QFrame QLineEdit:hover {
               border-bottom: 1px solid #5d5d5d;
            }
            QFrame QComboBox:focus, QFrame QLineEdit:focus {
               border-bottom: 1px solid #90AF13;
            }
            QFrame QLabel {
               border: none;
               padding: 0px;
               margin: 0px;
            }
            """
        )
        return box

    def _set_row_visibility(self, rows, visible):
        for label, widget in rows:
            if label is not None:
                label.setVisible(visible)
            widget.setVisible(visible)

    def _sync_mode_field(self, mode_combo, value_field, optimized_placeholder=None, custom_label=None):
        mode_text = mode_combo.currentText()
        is_optimized = mode_text.lower().startswith("opt") or mode_text.lower() == "all"
        is_custom = mode_text.lower().startswith("custom")
        if is_optimized and optimized_placeholder is not None:
            value_field.setReadOnly(True)
            value_field.setPlaceholderText(optimized_placeholder)
            value_field.clear()
        elif is_custom:
            value_field.setReadOnly(False)
            if custom_label:
                value_field.setPlaceholderText(custom_label)
        else:
            value_field.setReadOnly(False)
        value_field.setEnabled(True)

    def _populate_girder_lists(self):
        combo = self.widgets.get("select_girder_combo")
        if not combo:
            return
        items = [f"Girder {i}" for i in range(1, self.girder_count + 1)] + ["All"]
        combo.clear()
        combo.addItems(items)

    def _populate_member_list(self):
        combo = self.widgets.get("member_select_combo")
        if not combo:
            return
        items = [f"Girder {i}" for i in range(1, self.girder_count + 1)]
        combo.clear()
        combo.addItems(items)

    def set_girder_count(self, count):
        try:
            count_int = int(max(1, count))
        except Exception:
            count_int = 1
        self.girder_count = count_int
        self._populate_girder_lists()
        self._populate_member_list()

    def _apply_mode_states(self):
        def sync_pair(mode_name, value_name, opt_placeholder=None, custom_label=None):
            mode_widget = self.widgets.get(mode_name)
            value_widget = self.widgets.get(value_name)
            if mode_widget and value_widget:
                self._sync_mode_field(mode_widget, value_widget, optimized_placeholder=opt_placeholder, custom_label=custom_label)

        sync_pair("depth_mode_combo", "depth_input", opt_placeholder="Auto")
        sync_pair("top_width_mode_combo", "top_width_input", opt_placeholder="Auto")
        sync_pair("bottom_width_mode_combo", "bottom_width_input", opt_placeholder="Auto")
        sync_pair("top_thickness_mode_combo", "top_thickness_input", custom_label="Custom")
        sync_pair("bottom_thickness_mode_combo", "bottom_thickness_input", custom_label="Custom")
        sync_pair("web_thickness_mode_combo", "web_thickness_input", custom_label="Custom")
