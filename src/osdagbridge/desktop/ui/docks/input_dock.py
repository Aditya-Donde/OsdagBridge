import sys
import os
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QComboBox, QScrollArea, QLabel, QFormLayout, QLineEdit, QGroupBox, QSizePolicy, QMessageBox, QInputDialog, QDialog, QCheckBox, QFrame,
    QDialogButtonBox, QStackedWidget
)
from PySide6.QtCore import Qt, QRegularExpression, QSize, QTimer, QPoint, QEvent
from PySide6.QtGui import QPixmap, QDoubleValidator, QRegularExpressionValidator, QIcon
from PySide6.QtSvgWidgets import *
from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.dialogs.additional_inputs import AdditionalInputs
from osdagbridge.desktop.ui.utils.custom_buttons import DockCustomButton
from osdagbridge.desktop.ui.dialogs.project_location import ProjectLocationDialog


STEEL_MEMBER_FIELDS = [
    "Ultimate Tensile Strength, Fu (MPa)",
    "Yield Strength, Fy (MPa)",
    "Modulus of Elasticity, E (GPa)",
    "Modulus of Rigidity, G (GPa)",
    "Poisson's Ratio, ν",
    "Thermal Expansion Coefficient, (×10⁻⁶/°C)",
]

DECK_MEMBER_FIELDS = [
    "Characteristic Compressive (Cube) Strength of Concrete, (fck)cu (MPa)",
    "Mean Tensile Strength of Concrete, fctm (MPa)",
    "Secant Modulus of Elasticity of Concrete, Ecm (GPa)",
    "Ecm Multiplication Factor",
]

STEEL_MODULUS_E_GPA = 200.0
STEEL_MODULUS_G_GPA = 77.0
STEEL_POISSON_RATIO = 0.30
STEEL_THERMAL_COEFF = 11.7

STEEL_GRADE_BASE_VALUES = {
    250: {"Fy": 250, "Fu": 410},
    275: {"Fy": 275, "Fu": 430},
    300: {"Fy": 300, "Fu": 440},
    350: {"Fy": 350, "Fu": 490},
    410: {"Fy": 410, "Fu": 540},
    450: {"Fy": 450, "Fu": 570},
    550: {"Fy": 550, "Fu": 650},
    600: {"Fy": 600, "Fu": 700},
    650: {"Fy": 650, "Fu": 750},
}

ECM_FACTOR_OPTIONS = [
    ("Quartzite/granite aggregates = 1", 1.0),
    ("Limestone aggregates = 0.9", 0.9),
    ("Sandstone aggregates = 0.7", 0.7),
    ("Basalt aggregates = 1.2", 1.2),
    ("Custom", None),
]
ECM_FACTOR_LABELS = [text for text, _ in ECM_FACTOR_OPTIONS]
DEFAULT_ECM_FACTOR_LABEL = ECM_FACTOR_OPTIONS[0][0]
CUSTOM_ECM_FACTOR_LABEL = "Custom"


class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()  # Prevent changing selection on scroll

def apply_field_style(widget):
    widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    widget.setMinimumHeight(28)
    
    if isinstance(widget, QComboBox):
        style = """
            QComboBox{
                padding: 1px 7px;
                border: 1px solid black;
                border-radius: 5px;
                background-color: white;
                color: black;
            }
            QComboBox::drop-down{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                border-left: 0px;
            }
            QComboBox::down-arrow{
                image: url(:/vectors/arrow_down_light.svg);
                width: 20px;
                height: 20px;
                margin-right: 8px;
            }
            QComboBox::down-arrow:on {
                image: url(:/vectors/arrow_up_light.svg);
                width: 20px;
                height: 20px;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView{
                background-color: white;
                border: 1px solid black;
                outline: none;
            }
            QComboBox QAbstractItemView::item{
                color: black;
                background-color: white;
                border: none;
                border: 1px solid white;
                border-radius: 0;
                padding: 2px;
            }
            QComboBox QAbstractItemView::item:hover{
                border: 1px solid #90AF13;
                background-color: #90AF13;
                color: black;
            }
            QComboBox QAbstractItemView::item:selected{
                background-color: #90AF13;
                color: black;
                border: 1px solid #90AF13;
            }
            QComboBox QAbstractItemView::item:selected:hover{
                background-color: #90AF13;
                color: black;
                border: 1px solid #94b816;
            }
            QComboBox:disabled{
                background: #f1f1f1;
                color: #666;
            }
        """
        widget.setStyleSheet(style)
    elif isinstance(widget, QLineEdit):
        widget.setStyleSheet("""
            QLineEdit {
                padding: 1px 7px;
                border: 1px solid #070707;
                border-radius: 6px;
                background-color: white;
                color: #000000;
                font-weight: normal;
            }
            QLineEdit:disabled{
                background: #f1f1f1;
                color: #666;
            }
        """)


class MaterialPropertiesDialog(QDialog):
    MEMBER_OPTIONS = ["Girder", "Cross Bracing", "End Diaphragm", "Deck"]
    STEEL_MEMBERS = {"Girder", "Cross Bracing", "End Diaphragm"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Material Properties")
        self.setMinimumWidth(580)
        self.setStyleSheet("background-color: white;")

        self.parent_dock = parent
        self._loading = False
        self.current_member = None
        self.member_data = {}

        self.member_combo = NoScrollComboBox()
        self.member_combo.addItems(self.MEMBER_OPTIONS)
        apply_field_style(self.member_combo)

        self.material_combo = NoScrollComboBox()
        apply_field_style(self.material_combo)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)

        # Create a container widget for all form fields
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(10)
        
        # Member row
        member_row = QHBoxLayout()
        member_row.setContentsMargins(0, 0, 0, 0)
        member_row.setSpacing(18)
        member_label = QLabel("Member*:")
        member_label.setStyleSheet("font-size: 12px; color: #2d2d2d;")
        member_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        member_label.setFixedWidth(280)
        self.member_combo.setFixedWidth(242)
        member_row.addWidget(member_label)
        member_row.addWidget(self.member_combo)
        member_row.addStretch()
        form_layout.addLayout(member_row)
        
        # Material row
        material_row = QHBoxLayout()
        material_row.setContentsMargins(0, 0, 0, 0)
        material_row.setSpacing(18)
        material_label = QLabel("Material*:")
        material_label.setStyleSheet("font-size: 12px; color: #2d2d2d;")
        material_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        material_label.setFixedWidth(280)
        self.material_combo.setFixedWidth(242)
        material_row.addWidget(material_label)
        material_row.addWidget(self.material_combo)
        material_row.addStretch()
        form_layout.addLayout(material_row)
        
        main_layout.addWidget(form_container)

        self.stack = QStackedWidget()
        self.stack.setContentsMargins(0, 0, 0, 0)
        self.steel_page = self._build_steel_form()
        self.deck_page = self._build_deck_form()
        self.stack.addWidget(self.steel_page)
        self.stack.addWidget(self.deck_page)
        main_layout.addWidget(self.stack)

        # Updated default row with proper alignment
        default_row = QHBoxLayout()
        default_row.setContentsMargins(0, 0, 0, 0)
        default_row.setSpacing(18)
        default_label = QLabel("Default")
        default_label.setStyleSheet("font-size: 12px; color: #2d2d2d;")
        default_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        default_label.setFixedWidth(280)
        self.default_checkbox = QCheckBox()
        # Create container for checkbox to align it to the left
        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(0)
        checkbox_layout.addWidget(self.default_checkbox)
        checkbox_layout.addStretch()
        
        default_row.addWidget(default_label)
        default_row.addWidget(checkbox_container)
        main_layout.addLayout(default_row)

        self.member_combo.currentTextChanged.connect(self._on_member_changed)
        self.material_combo.currentTextChanged.connect(self._on_material_changed)
        self.default_checkbox.stateChanged.connect(self._on_default_toggled)

        self._initialize_member_data()
        self._on_member_changed(self.member_combo.currentText())

    def closeEvent(self, event):
        self._save_current_member_form()
        super().closeEvent(event)

    def _build_steel_form(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.steel_field_inputs = {}
        for label_text in STEEL_MEMBER_FIELDS:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(18)
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 12px; color: #2d2d2d;")
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label.setFixedWidth(280)
            line_edit = QLineEdit()
            line_edit.setFixedWidth(242)
            apply_field_style(line_edit)
            # Add validator for 1 decimal place
            line_edit.setValidator(QDoubleValidator(0.0, 99999.0, 1))
            line_edit.textEdited.connect(self._handle_user_override)
            self.steel_field_inputs[label_text] = line_edit
            row.addWidget(label)
            row.addWidget(line_edit)
            row.addStretch()
            layout.addLayout(row)
        layout.addStretch()
        return widget

    def _build_deck_form(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        self.deck_field_inputs = {}
        for label_text in DECK_MEMBER_FIELDS:
            row = QHBoxLayout()
            row.setSpacing(18)
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 12px; color: #2d2d2d;")
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label.setFixedWidth(280)
            if label_text == "Ecm Multiplication Factor":
                self.deck_factor_combo = NoScrollComboBox()
                self.deck_factor_combo.addItems(ECM_FACTOR_LABELS)
                self.deck_factor_combo.setFixedWidth(242)
                apply_field_style(self.deck_factor_combo)
                self.deck_factor_combo.currentTextChanged.connect(self._on_factor_changed)

                self.deck_factor_custom_input = QLineEdit()
                apply_field_style(self.deck_factor_custom_input)
                self.deck_factor_custom_input.setPlaceholderText("Custom factor")
                self.deck_factor_custom_input.setFixedWidth(242)
                self.deck_factor_custom_input.setVisible(False)
                self.deck_factor_custom_input.setEnabled(False)
                self.deck_factor_custom_input.setValidator(QDoubleValidator(0.1, 5.0, 1))
                self.deck_factor_custom_input.textEdited.connect(self._handle_user_override)

                row.addWidget(label)
                row.addWidget(self.deck_factor_combo)
                row.addStretch()
                
                # Add custom input row (hidden by default)
                custom_row = QHBoxLayout()
                custom_row.setContentsMargins(0, 0, 0, 0)
                custom_row.setSpacing(18)
                custom_label = QLabel("")  # Empty label for alignment
                custom_label.setFixedWidth(280)
                custom_row.addWidget(custom_label)
                custom_row.addWidget(self.deck_factor_custom_input)
                custom_row.addStretch()
                layout.addLayout(custom_row)
                
                self.deck_field_inputs[label_text] = self.deck_factor_combo
            else:
                line_edit = QLineEdit()
                line_edit.setFixedWidth(242)
                apply_field_style(line_edit)
                # Add validator for 1 decimal place
                line_edit.setValidator(QDoubleValidator(0.0, 99999.0, 1))
                line_edit.textEdited.connect(self._handle_user_override)
                row.addWidget(label)
                row.addWidget(line_edit)
                row.addStretch()
                self.deck_field_inputs[label_text] = line_edit
            layout.addLayout(row)
        layout.addStretch()
        return widget

    def _initialize_member_data(self):
        for member in self.MEMBER_OPTIONS:
            material = self._get_parent_grade(member)
            fields = self._default_fields_for_member(member, material)
            self.member_data[member] = {
                "material": material,
                "fields": fields,
                "is_default": True,
                "factor_label": DEFAULT_ECM_FACTOR_LABEL if member == "Deck" else None,
                "custom_factor": "1.0" if member == "Deck" else None,
            }

    def _default_fields_for_member(self, member, material=None, factor_label=None, custom_factor=None):
        if member == "Deck":
            grade = material or self._get_parent_grade(member) or (VALUES_DECK_CONCRETE_GRADE[0] if VALUES_DECK_CONCRETE_GRADE else "")
            factor_label = factor_label or DEFAULT_ECM_FACTOR_LABEL
            factor_value = self._factor_value_from_label(factor_label, custom_factor)
            return self._deck_defaults(grade, factor_value)
        grade = material or self._get_parent_grade(member)
        if not grade:
            grade = VALUES_MATERIAL[0] if VALUES_MATERIAL else ""
        return self._steel_defaults(grade)

    def _steel_defaults(self, grade):
        grade_value = self._extract_numeric_grade(grade)
        defaults = STEEL_GRADE_BASE_VALUES.get(grade_value, STEEL_GRADE_BASE_VALUES[250])
        return {
            "Ultimate Tensile Strength, Fu (MPa)": "{:.1f}".format(defaults["Fu"]),
            "Yield Strength, Fy (MPa)": "{:.1f}".format(defaults["Fy"]),
            "Modulus of Elasticity, E (GPa)": "{:.1f}".format(STEEL_MODULUS_E_GPA),
            "Modulus of Rigidity, G (GPa)": "{:.1f}".format(STEEL_MODULUS_G_GPA),
            "Poisson's Ratio, ν": "{:.1f}".format(STEEL_POISSON_RATIO),
            "Thermal Expansion Coefficient, (×10⁻⁶/°C)": "{:.1f}".format(STEEL_THERMAL_COEFF),
        }

    def _deck_defaults(self, grade, factor_value):
        strength = self._extract_numeric_grade(grade, default=25)
        fck = float(strength)
        fctm = round(0.7 * math.sqrt(fck), 1)
        ecm = round(5.0 * math.sqrt(fck) * factor_value, 1)
        return {
            "Characteristic Compressive (Cube) Strength of Concrete, (fck)cu (MPa)": "{:.1f}".format(fck),
            "Mean Tensile Strength of Concrete, fctm (MPa)": "{:.1f}".format(fctm),
            "Secant Modulus of Elasticity of Concrete, Ecm (GPa)": "{:.1f}".format(ecm),
            "Ecm Multiplication Factor": "{:.1f}".format(factor_value),
        }

    def _extract_numeric_grade(self, grade, default=250):
        digits = ''.join(ch for ch in grade if ch.isdigit())
        try:
            return int(digits) if digits else default
        except ValueError:
            return default

    def _materials_for_member(self, member):
        if member == "Deck":
            return VALUES_DECK_CONCRETE_GRADE
        return VALUES_MATERIAL

    def _on_member_changed(self, member):
        if self.current_member:
            self._save_current_member_form()

        self.current_member = member
        is_deck = member == "Deck"
        self.stack.setCurrentWidget(self.deck_page if is_deck else self.steel_page)

        data = self.member_data.get(member)
        if not data:
            self.member_data[member] = self._create_default_entry(member)
            data = self.member_data[member]

        if data.get("is_default"):
            self._apply_defaults_for_member(member, update_ui=False)

        materials = self._materials_for_member(member)
        self._loading = True
        self.material_combo.clear()
        self.material_combo.addItems(materials)
        if data["material"] in materials:
            self.material_combo.setCurrentText(data["material"])
        elif materials:
            self.material_combo.setCurrentIndex(0)
            data["material"] = self.material_combo.currentText()

        self.default_checkbox.setChecked(data.get("is_default", False))
        if is_deck:
            self._populate_deck_fields(data)
        else:
            self._populate_steel_fields(data)
        self._loading = False

    def _populate_steel_fields(self, data):
        for label, widget in self.steel_field_inputs.items():
            value = data["fields"].get(label, "")
            # Format to 1 decimal place
            try:
                formatted_value = "{:.1f}".format(float(value))
                widget.setText(formatted_value)
            except (ValueError, TypeError):
                widget.setText(value)

    def _populate_deck_fields(self, data):
        for label, widget in self.deck_field_inputs.items():
            if label == "Ecm Multiplication Factor":
                factor_label = data.get("factor_label", DEFAULT_ECM_FACTOR_LABEL)
                if factor_label not in ECM_FACTOR_LABELS:
                    factor_label = DEFAULT_ECM_FACTOR_LABEL
                self.deck_factor_combo.blockSignals(True)
                self.deck_factor_combo.setCurrentText(factor_label)
                self.deck_factor_combo.blockSignals(False)
                self._update_custom_factor_visibility(factor_label)
                self.deck_factor_custom_input.blockSignals(True)
                custom_val = data.get("custom_factor", "1.0")
                try:
                    formatted_custom = "{:.1f}".format(float(custom_val))
                    self.deck_factor_custom_input.setText(formatted_custom)
                except (ValueError, TypeError):
                    self.deck_factor_custom_input.setText(custom_val)
                self.deck_factor_custom_input.blockSignals(False)
            else:
                value = data["fields"].get(label, "")
                # Format to 1 decimal place
                try:
                    formatted_value = "{:.1f}".format(float(value))
                    widget.setText(formatted_value)
                except (ValueError, TypeError):
                    widget.setText(value)

    def _save_current_member_form(self):
        if not self.current_member:
            return
        data = self.member_data.setdefault(self.current_member, self._create_default_entry(self.current_member))
        data["material"] = self.material_combo.currentText()
        if self.current_member == "Deck":
            for label, widget in self.deck_field_inputs.items():
                if label == "Ecm Multiplication Factor":
                    data["factor_label"] = self.deck_factor_combo.currentText()
                    data["custom_factor"] = self.deck_factor_custom_input.text() or "1.0"
                else:
                    data["fields"][label] = widget.text()
            factor_value = self._factor_value_from_label(data["factor_label"], data.get("custom_factor"))
            data["fields"]["Ecm Multiplication Factor"] = "{:.1f}".format(factor_value)
        else:
            for label, widget in self.steel_field_inputs.items():
                data["fields"][label] = widget.text()
        data["is_default"] = self.default_checkbox.isChecked()

    def _create_default_entry(self, member):
        material = self._get_parent_grade(member)
        return {
            "material": material,
            "fields": self._default_fields_for_member(member, material),
            "is_default": True,
            "factor_label": DEFAULT_ECM_FACTOR_LABEL if member == "Deck" else None,
            "custom_factor": "1.0" if member == "Deck" else None,
        }

    def _apply_defaults_for_member(self, member, update_ui=True):
        data = self.member_data.setdefault(member, self._create_default_entry(member))
        grade = self._get_parent_grade(member) or data.get("material")
        materials = self._materials_for_member(member)
        if grade not in materials and materials:
            grade = materials[0]
        data["material"] = grade
        if member == "Deck":
            data["factor_label"] = DEFAULT_ECM_FACTOR_LABEL
            data["custom_factor"] = "1.0"
            factor_value = self._factor_value_from_label(DEFAULT_ECM_FACTOR_LABEL)
            data["fields"] = self._deck_defaults(grade, factor_value)
        else:
            data["fields"] = self._steel_defaults(grade)
        data["is_default"] = True

        if update_ui and member == self.current_member:
            self._loading = True
            self.material_combo.setCurrentText(grade)
            if member == "Deck":
                self._populate_deck_fields(data)
            else:
                self._populate_steel_fields(data)
            self.default_checkbox.setChecked(True)
            self._loading = False

    def _factor_value_from_label(self, label, custom_factor=None):
        for text, value in ECM_FACTOR_OPTIONS:
            if text == label:
                if value is None:
                    try:
                        return float(custom_factor) if custom_factor else 1.0
                    except ValueError:
                        return 1.0
                return value
        return 1.0

    def _reset_current_member_to_defaults(self):
        if not self.current_member:
            return

        self._apply_defaults_for_member(self.current_member, update_ui=False)
        data = self.member_data.get(self.current_member)
        if not data:
            return

        target_material = data.get("material", "")
        self._loading = True
        if target_material:
            index = self.material_combo.findText(target_material)
            if index >= 0:
                self.material_combo.setCurrentIndex(index)
            elif self.material_combo.count() > 0:
                self.material_combo.setCurrentIndex(0)
                data["material"] = self.material_combo.currentText()
        if self.current_member == "Deck":
            self._populate_deck_fields(data)
        else:
            self._populate_steel_fields(data)
        self._loading = False

        self.default_checkbox.blockSignals(True)
        self.default_checkbox.setChecked(True)
        self.default_checkbox.blockSignals(False)
        self._save_current_member_form()

    def _update_custom_factor_visibility(self, label):
        is_custom = label == CUSTOM_ECM_FACTOR_LABEL
        self.deck_factor_custom_input.setVisible(is_custom)
        self.deck_factor_custom_input.setEnabled(is_custom)
        self.deck_factor_combo.setVisible(not is_custom)

    def _on_material_changed(self, material):
        if self._loading:
            return
        data = self.member_data.get(self.current_member)
        if data:
            data["material"] = material
        self._handle_user_override()

    def _on_default_toggled(self, state):
        if self._loading:
            return
        try:
            check_state = Qt.CheckState(state)
        except ValueError:
            check_state = Qt.CheckState.Checked if bool(state) else Qt.CheckState.Unchecked
        if check_state == Qt.CheckState.Checked:
            self._reset_current_member_to_defaults()
        else:
            data = self.member_data.get(self.current_member)
            if data:
                data["is_default"] = False

    def _on_factor_changed(self, label):
        self._update_custom_factor_visibility(label)
        self._handle_user_override()

    def _handle_user_override(self):
        if self._loading:
            return
        if self.default_checkbox.isChecked():
            self._loading = True
            self.default_checkbox.setChecked(False)
            self._loading = False
        data = self.member_data.get(self.current_member)
        if data:
            data["is_default"] = False
        self._save_current_member_form()

    def _get_parent_grade(self, member):
        parent = self.parent_dock
        if not parent:
            return ""
        mapping = {
            "Girder": getattr(parent, "girder_combo", None),
            "Cross Bracing": getattr(parent, "cross_bracing_combo", None),
            "End Diaphragm": getattr(parent, "end_diaphragm_combo", None),
            "Deck": getattr(parent, "deck_combo", None),
        }
        combo = mapping.get(member)
        return combo.currentText() if combo else ""

    def set_member(self, member):
        index = self.member_combo.findText(member)
        if index >= 0:
            self.member_combo.setCurrentIndex(index)

    def sync_with_parent_defaults(self):
        for member, data in self.member_data.items():
            if data.get("is_default"):
                self._apply_defaults_for_member(member, update_ui=(member == self.current_member))


class InputDock(QWidget):
    def __init__(self, backend, parent):
        super().__init__()
        self.parent = parent
        self.backend = backend
        self.input_widget = None
        self.structure_type_combo = None
        self.structure_note = None
        self.project_location_combo = None
        self.custom_location_input = None
        self.include_median_combo = None
        self.footpath_combo = None
        self.additional_inputs = None
        self.additional_inputs_widget = None
        self.material_dialog = None
        self.additional_inputs_btn = None
        self.lock_btn = None
        self.scroll_area = None
        self.is_locked = False

        self.setStyleSheet("background: transparent;")
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.left_container = QWidget()

        # Get input fields from backend
        input_field_list = self.backend.input_values()

        self.build_left_panel(input_field_list)
        self.main_layout.addWidget(self.left_container)

        # Toggle strip
        self.toggle_strip = QWidget()
        self.toggle_strip.setStyleSheet("background-color: #90AF13;")
        self.toggle_strip.setFixedWidth(6)
        toggle_layout = QVBoxLayout(self.toggle_strip)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setSpacing(0)
        toggle_layout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.toggle_btn = QPushButton("❮")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedSize(6, 60)
        self.toggle_btn.setToolTip("Hide panel")
        self.toggle_btn.clicked.connect(self.toggle_input_dock)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c8408;
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5e7407;
            }
        """)
        toggle_layout.addStretch()
        toggle_layout.addWidget(self.toggle_btn)
        toggle_layout.addStretch()
        self.main_layout.addWidget(self.toggle_strip)

    def get_validator(self, validator):
        if validator == 'Int Validator':
            return QRegularExpressionValidator(QRegularExpression("^(0|[1-9]\\d*)(\\.\\d+)?$"))
        elif validator == 'Double Validator':
            return QDoubleValidator()
        else:
            return None
    
    def on_structure_type_changed(self, text):
        """Handle structure type combo box changes"""
        if text == "Other":
            if hasattr(self, 'structure_note'):
                self.structure_note.setVisible(True)
        else:
            if hasattr(self, 'structure_note'):
                self.structure_note.setVisible(False)
 
    def show_project_location_dialog(self):
        """Show Project Location selection dialog"""
        dialog = ProjectLocationDialog()
        
        if dialog.exec() == QDialog.Accepted:
            location_data = dialog.get_selected_location()
            
            # Process the location data as needed
            if location_data['method'] == 'coordinates':
                lat = location_data['data']['latitude']
                lon = location_data['data']['longitude']
                print(f"Selected coordinates: {lat}, {lon}")
                
            elif location_data['method'] == 'location_name':
                state = location_data['data']['state']
                district = location_data['data']['district']
                print(f"Selected location: {district}, {state}")
                
            elif location_data['method'] == 'map':
                print("Map selection (to be implemented)")
            
            if location_data['custom_params']:
                print("Custom loading parameters requested")

    # Lock-Tooltip-Events-Starts-------------------------------------------------------------------------
    def eventFilter(self, obj, event):
        # Check if it's the scroll area and it's a mouse press
        if obj == self.scroll_area and event.type() == QEvent.MouseButtonPress:
            if self.is_locked:
                self.show_lock_tooltip()
            return True  # Block the event
        return super().eventFilter(obj, event)
    
    def clear_force_hover(self):
        if self.lock_btn:
            self.lock_btn.setProperty("forceHover", False)
            self.lock_btn.style().polish(self.lock_btn)
            self.lock_btn.update()

    def show_lock_tooltip(self):
        # Stop any existing timer first
        if hasattr(self, 'tooltip_timer') and self.tooltip_timer.isActive():
            self.tooltip_timer.stop()
        
        # Position tooltip to the right of the lock button
        lock_global_pos = self.lock_btn.mapToGlobal(self.lock_btn.rect().topRight())
        tooltip_pos = lock_global_pos + QPoint(5, 0)
        self.lock_btn.setProperty("forceHover", True)
        self.lock_btn.style().polish(self.lock_btn)
        self.lock_btn.update()
                
        # Adjust size and position
        self.lock_btn_tooltip.adjustSize()
        self.lock_btn_tooltip.move(tooltip_pos)
        self.lock_btn_tooltip.show()
        self.lock_btn_tooltip.raise_()
        
        # Hide after 3 seconds
        if not hasattr(self, 'tooltip_timer'):
            self.tooltip_timer = QTimer()
            self.tooltip_timer.setSingleShot(True)
            self.tooltip_timer.timeout.connect(self.lock_btn_tooltip.hide)
            self.tooltip_timer.timeout.connect(self.clear_force_hover)
        
        self.tooltip_timer.start(3000)
    
    def toggle_lock(self):            
        self.is_locked = not self.is_locked
        self.lock_btn.setChecked(self.is_locked)
        self.scroll_area.setDisabled(self.is_locked)
        self.update_lock_icon()

    def update_lock_icon(self):
        if self.lock_btn:
            if self.is_locked:
                self.lock_btn.setIcon(QIcon(":/vectors/lock_close.svg"))
            else:
                self.lock_btn.setIcon(QIcon(":/vectors/lock_open.svg"))
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Checking hasattr is only meant to prevent errors,
        # while standalone testing of this widget
        if self.parent:
            if self.width() == 0:
                if hasattr(self.parent, 'update_docking_icons'):
                    self.parent.update_docking_icons(input_is_active=False)
            elif self.width() > 0:
                if hasattr(self.parent, 'update_docking_icons'):
                    self.parent.update_docking_icons(input_is_active=True)


    def paintEvent(self, event):
        self.update_lock_icon()
        return super().paintEvent(event)

    def toggle_input_dock(self):
        parent = self.parent
        if hasattr(parent, 'toggle_animate'):
            is_collapsing = self.width() > 0
            parent.toggle_animate(show=not is_collapsing, dock='input')
        
        self.toggle_btn.setText("❯" if is_collapsing else "❮")
        self.toggle_btn.setToolTip("Show panel" if is_collapsing else "Hide panel")

    
    # Lock-Tooltip-Events-Ends-------------------------------------------------------------------------

    def build_left_panel(self, field_list):
        left_layout = QVBoxLayout(self.left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.left_panel = QWidget()
        self.left_panel.setStyleSheet("background-color: white;")
        panel_layout = QVBoxLayout(self.left_panel)
        panel_layout.setContentsMargins(15, 10, 15, 10)
        panel_layout.setSpacing(0)

        # Top Bar with buttons
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)
        top_bar.setContentsMargins(0, 0, 0, 15)
        
        input_dock_btn = QPushButton("Basic Inputs")
        input_dock_btn.setStyleSheet("""
            QPushButton {
                background-color: #90AF13;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                padding: 7px 20px;
                min-width: 80px;
            }
        """)
        input_dock_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top_bar.addWidget(input_dock_btn)
        
        self.additional_inputs_btn = QPushButton("Additional Inputs")
        self.additional_inputs_btn.setCursor(Qt.CursorShape.PointingHandCursor)        
        self.additional_inputs_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: black;
                font-weight: bold;
                font-size: 13px;
                border-radius: 5px;
                border: 1px solid black;
                padding: 7px 20px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #90AF13;
                border: 1px solid #90AF13;
                color: white;
            }
            QPushButton:pressed {
                color: black;
                background-color: white;
                border: 1px solid black;
            }
        """)
        self.additional_inputs_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.additional_inputs_btn.clicked.connect(self.show_additional_inputs)
        top_bar.addWidget(self.additional_inputs_btn)           

        # Lock button
        self.lock_btn = QPushButton()
        self.lock_btn.setStyleSheet("""
            QPushButton {
                background-color: #f4f4f4;
                border: none;
                padding: 7px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:checked {
                background-color: #FFA500;
            }
            QPushButton:unchecked {
                background-color: #f4f4f4;
            }
            QPushButton:unchecked:hover {
                background-color: #e0e0e0;
            }
            QPushButton:checked:hover {
                background-color: #fa7a02;
            }
        """)
        self.lock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lock_btn.setObjectName("lock_btn")
        self.lock_btn.setCheckable(True)
        self.lock_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lock_btn.clicked.connect(self.toggle_lock)
        top_bar.addWidget(self.lock_btn)
        panel_layout.addLayout(top_bar)

        #-Lock-ToolTip--------------------------------------
        self.lock_btn_tooltip = QLabel("Unlock to Edit")
        self.lock_btn_tooltip.setStyleSheet("""
            QLabel{
                background-color: #f1f1f1;
                color: #000000;
                border: 1px solid #90AF13;
                padding: 4px;
                font-size: 15px;
                border-radius: 0px;
                qproperty-alignment: AlignVCenter;
            }
        """)
        self.lock_btn_tooltip.setObjectName("lock_btn_tooltip")
        self.lock_btn_tooltip.setWindowFlags(Qt.ToolTip)
        self.lock_btn_tooltip.hide()
        #--------------------------------------------------

        # Scroll area
        scroll_area = QScrollArea()
        self.scroll_area = scroll_area
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll_area.installEventFilter(self)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                padding: 0px 5px;
                border-top: 1px solid #909090;
                border-bottom: 1px solid #909090;
            }

            QScrollArea QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                margin-left: 2px;
            }

            QScrollArea QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
            }

            QScrollArea QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }

            QScrollArea QScrollBar::handle:vertical:pressed {
                background: #808080;
            }

            QScrollArea QScrollBar::add-line:vertical,
            QScrollArea QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }

            QScrollArea QScrollBar::add-page:vertical,
            QScrollArea QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        group_container = QWidget()
        self.input_widget = group_container
        group_container_layout = QVBoxLayout(group_container)
        group_container_layout.setContentsMargins(0, 0, 0, 0)
        group_container_layout.setSpacing(12)
        
        self.section_contexts = {}
        self.container_layouts = {}

        self._build_basic_inputs(field_list, group_container_layout)

        group_container_layout.addStretch()
        scroll_area.setWidget(group_container)

        self.data = {}
        panel_layout.addWidget(scroll_area)

        # Bottom buttons
        btn_button_layout = QHBoxLayout()
        btn_button_layout.setContentsMargins(0, 15, 0, 0)
        btn_button_layout.setSpacing(10)

        save_input_btn = DockCustomButton("Save Input", ":/vectors/save.svg")
        save_input_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_button_layout.addWidget(save_input_btn)

        design_btn = DockCustomButton("Design", ":/vectors/design.svg")
        design_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_button_layout.addWidget(design_btn)

        panel_layout.addLayout(btn_button_layout)

        # Horizontal scroll area
        h_scroll_area = QScrollArea()
        h_scroll_area.setWidgetResizable(True)
        h_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        h_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        h_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        h_scroll_area.setStyleSheet("""
            QScrollArea{
                background: transparent;
            }
            QScrollBar:horizontal{
                background: #E0E0E0;
                height: 8px;
                margin: 3px 0px 0px 0px;
                border-radius: 2px;
            }
            QScrollBar::handle:horizontal{
                background: #A0A0A0;
                min-width: 30px;
                border-radius: 2px;
            }
            QScrollBar::handle:horizontal:hover{
                background: #707070;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal{
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal{
                background: none;
            }
        """)
        h_scroll_area.setWidget(self.left_panel)

        left_layout.addWidget(h_scroll_area)
        self._apply_lock_state()
    
    def show_additional_inputs(self):
        """Show Additional Inputs dialog"""
        footpath_value = self.footpath_combo.currentText() if self.footpath_combo else "None"
        
        carriageway_width = self._get_effective_carriageway_width()

        # Lazily create the in-session storage for Additional Inputs.
        if not hasattr(self, "_additional_inputs_saved_data"):
            self._additional_inputs_saved_data = {}

        self.additional_inputs = AdditionalInputs(footpath_value, carriageway_width)
        self.additional_inputs_widget = self.additional_inputs

        # Restore previously saved dialog state (includes stiffener details).
        if isinstance(getattr(self, "_additional_inputs_saved_data", None), dict) and self._additional_inputs_saved_data:
            try:
                self.additional_inputs.set_properties_data(self._additional_inputs_saved_data)
            except Exception:
                pass

        # Capture state when dialog closes.
        try:
            self.additional_inputs.finished.connect(self._handle_additional_inputs_closed)
        except Exception:
            pass

        self.additional_inputs.show()
    
    def _apply_lock_state(self):
        self.update_lock_icon()

        enabled = not self.is_locked
        if self.scroll_area:
            self.scroll_area.setEnabled(enabled)
        if self.input_widget:
            self.input_widget.setEnabled(enabled)
        self._set_additional_inputs_enabled(enabled)

        if self.material_dialog:
            self.material_dialog.setEnabled(enabled)

    def _set_additional_inputs_enabled(self, enabled):
        if self.additional_inputs_widget:
            self.additional_inputs_widget.setEnabled(enabled)

    def _handle_additional_inputs_closed(self):
        # Persist the last saved Additional Inputs data for the session.
        try:
            if self.additional_inputs is not None and hasattr(self.additional_inputs, "get_saved_data"):
                saved = self.additional_inputs.get_saved_data()
                if isinstance(saved, dict) and saved:
                    self._additional_inputs_saved_data = saved
        except Exception:
            pass
        self.additional_inputs = None
        self.additional_inputs_widget = None

    def _build_basic_inputs(self, field_definitions, root_layout):
        current_section_id = None
        for definition in field_definitions:
            key, label, field_type, values, required, validator, metadata = self._normalize_definition(definition)
            if field_type == TYPE_MODULE:
                continue
            if field_type == TYPE_TITLE:
                section_id = key or label
                section_context = self._create_section_context(section_id, label, metadata, root_layout)
                current_section_id = section_context["id"]
                continue
            if current_section_id is None:
                continue
            section_context = self.section_contexts.get(current_section_id)
            if not section_context:
                continue
            self._create_field_row(section_context, key, label, field_type, values, validator, metadata)

        self._finalize_section_contexts()
        self._update_carriageway_placeholder()

    def _normalize_definition(self, definition):
        if len(definition) == 6:
            return (*definition, {})
        return definition

    def _create_section_context(self, section_id, title, metadata, root_layout):
        container_key = (metadata or {}).get("container", "main")
        parent_layout = self._get_container_layout(container_key, root_layout, metadata)

        show_title = metadata.get("show_group_title", True) if metadata else True
        group_title = title if show_title and title else ""
        group_box = QGroupBox(group_title) if group_title else QGroupBox()
        group_box.setStyleSheet(self._section_groupbox_style())

        layout = QVBoxLayout(group_box)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        if metadata and metadata.get("custom_content") == "project_location":
            self._add_project_location_controls(layout, metadata)

        parent_layout.addWidget(group_box)
        context = {
            "id": section_id,
            "layout": layout,
            "metadata": metadata or {},
            "group_box": group_box,
        }
        self.section_contexts[section_id] = context
        return context

    def _section_groupbox_style(self):
        return (
            "QGroupBox {\n"
            "    border: 1px solid #90AF13;\n"
            "    border-radius: 4px;\n"
            "    background-color: white;\n"
            "    padding: 8px;\n"
            "    margin-top: 12px;\n"
            "    font-size: 10px;\n"
            "    font-weight: bold;\n"
            "    color: #333;\n"
            "}\n"
            "QGroupBox::title {\n"
            "    subcontrol-origin: margin;\n"
            "    subcontrol-position: top left;\n"
            "    left: 8px;\n"
            "    padding: 0 4px;\n"
            "    margin-top: 4px;\n"
            "    background-color: white;\n"
            "    color: #333;\n"
            "}"
        )

    def _get_container_layout(self, container_key, root_layout, metadata=None):
        if not container_key or container_key == "main":
            return root_layout
        if container_key in self.container_layouts:
            return self.container_layouts[container_key]
        body_layout = self._create_container_group(container_key, root_layout, metadata)
        self.container_layouts[container_key] = body_layout
        return body_layout

    def _container_display_name(self, container_key, metadata):
        if metadata:
            custom = metadata.get("container_label") or metadata.get("container_title")
            if custom:
                return custom
        fallback = container_key or "Section"
        return fallback.replace("_", " ").title()

    def _create_container_group(self, container_key, root_layout, metadata=None):
        display_name = self._container_display_name(container_key, metadata or {})
        group = QGroupBox()
        group.setStyleSheet(
            "QGroupBox {\n"
            "    border: 1px solid #90AF13;\n"
            "    border-radius: 5px;\n"
            "    margin-top: 0px;\n"
            "    padding-top: 5px;\n"
            "    background-color: white;\n"
            "}\n"
        )
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(10)

        header = QHBoxLayout()
        title_label = QLabel(display_name)
        title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #333;")
        header.addWidget(title_label)
        header.addStretch()

        toggle_btn = QPushButton()
        toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_btn.setCheckable(True)
        toggle_btn.setChecked(True)
        toggle_btn.setIcon(QIcon(":/vectors/arrow_up_light.svg"))
        toggle_btn.setIconSize(QSize(20, 20))
        toggle_btn.setStyleSheet(
            "QPushButton {\n"
            "    background: transparent;\n"
            "    border: none;\n"
            "    padding: 2px;\n"
            "}\n"
            "QPushButton:hover {\n"
            "    background: transparent;\n"
            "}\n"
            "QPushButton:pressed {\n"
            "    background: transparent;\n"
            "}"
        )
        header.addWidget(toggle_btn)
        container_layout.addLayout(header)

        container_body = QFrame()
        container_body.setFrameShape(QFrame.NoFrame)
        body_layout = QVBoxLayout(container_body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(10)
        container_body.setVisible(True)
        container_layout.addWidget(container_body)

        def _toggle(checked):
            container_body.setVisible(checked)
            icon = ":/vectors/arrow_up_light.svg" if checked else ":/vectors/arrow_down_light.svg"
            toggle_btn.setIcon(QIcon(icon))

        toggle_btn.toggled.connect(_toggle)

        group.setLayout(container_layout)
        root_layout.addWidget(group)
        return body_layout

    def _add_project_location_controls(self, layout, metadata):
        label_text = metadata.get("header_label") or "Project Location*"
        button_rows = metadata.get("button_rows")
        if button_rows:
            for row_entry in button_rows:
                row_config = self._prepare_button_row_config(row_entry, {"label": label_text})
                if row_config:
                    self._add_button_row(layout, row_config)
            return

        fallback_row = self._prepare_button_row_config("project_location", {"label": label_text})
        self._add_button_row(layout, fallback_row)

    def _section_label_style(self):
        return (
            "QLabel {\n"
            "    color: #000000;\n"
            "    font-size: 12px;\n"
            "    background: transparent;\n"
            "}"
        )

    def _default_action_button_style(self):
        return (
            "QPushButton {\n"
            "    background-color: #90AF13;\n"
            "    color: white;\n"
            "    font-weight: bold;\n"
            "    border: none;\n"
            "    border-radius: 4px;\n"
            "    padding: 8px 20px;\n"
            "    font-size: 11px;\n"
            "    min-width: 80px;\n"
            "}\n"
            "QPushButton:hover {\n"
            "    background-color: #7a9a12;\n"
            "}\n"
            "QPushButton:disabled{\n"
            "    background: #D0D0D0;\n"
            "    color: #666;\n"
            "}"
        )

    def _default_row_config(self, row_type):
        mapping = {
            "project_location": {
                "label": "Project Location*",
                "buttons": [
                    {"text": "Add Here", "action": "show_project_location_dialog"},
                ],
            },
            "additional_geometry": {
                "label": "Additional Geometry",
                "buttons": [
                    {"text": "Modify Here", "action": "show_additional_inputs"},
                ],
            },
            "material_properties": {
                "label": "Properties",
                "buttons": [
                    {"text": "Modify Here", "action": "show_material_properties_dialog"},
                ],
            },
        }
        return mapping.get(row_type, {})

    def _prepare_button_row_config(self, config_entry, fallback_defaults=None):
        fallback_defaults = fallback_defaults or {}
        if isinstance(config_entry, str):
            config = {"type": config_entry}
        else:
            config = dict(config_entry or {})

        row_type = config.get("type")
        defaults = self._default_row_config(row_type)

        resolved = {}
        resolved.update(defaults)
        resolved.update(fallback_defaults)
        resolved.update(config)

        if not resolved.get("buttons"):
            extra_defaults = self._default_row_config(resolved.get("type"))
            if extra_defaults:
                resolved.setdefault("buttons", extra_defaults.get("buttons"))
                resolved.setdefault("label", extra_defaults.get("label"))

        return resolved if resolved.get("buttons") else None

    def _add_button_row(self, layout, config):
        if not config:
            return

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        label_text = config.get("label")
        if label_text:
            field_label = QLabel(label_text)
            field_label.setStyleSheet(self._section_label_style())
            field_label.setMinimumWidth(config.get("label_min_width", 110))
            row.addWidget(field_label)

        buttons = config.get("buttons", [])
        for button_config in buttons:
            button = self._create_action_button(button_config)
            stretch = button_config.get("stretch", 1 if len(buttons) == 1 else 0)
            row.addWidget(button, stretch)

        if config.get("add_stretch", True):
            row.addStretch()

        layout.addLayout(row)

    def _create_action_button(self, config):
        button = QPushButton(config.get("text", "Action"))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        if config.get("size_policy") == "fixed":
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        else:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        icon_path = config.get("icon")
        if icon_path:
            button.setIcon(QIcon(icon_path))
            icon_size = config.get("icon_size")
            if isinstance(icon_size, (list, tuple)) and len(icon_size) == 2:
                button.setIconSize(QSize(icon_size[0], icon_size[1]))

        style = config.get("style") or self._default_action_button_style()
        button.setStyleSheet(style)

        tooltip = config.get("tooltip")
        if tooltip:
            button.setToolTip(tooltip)

        action_name = config.get("action")
        callback = getattr(self, action_name, None) if action_name else None
        if callable(callback):
            button.clicked.connect(callback)
        else:
            button.setEnabled(False)

        return button

    def _create_field_row(self, section_context, key, label, field_type, values, validator, metadata):
        widget = self._create_input_widget(key, field_type, values, validator, metadata)
        if widget is None:
            return
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        display_label = (metadata or {}).get("label") if metadata else None
        field_label = QLabel(display_label or label)
        field_label.setStyleSheet(self._section_label_style())
        field_label.setMinimumWidth(110)
        row.addWidget(field_label)
        row.addWidget(widget, 1)
        if metadata.get("add_stretch"):
            row.addStretch()
        section_context["layout"].addLayout(row)

    def _create_input_widget(self, key, field_type, values, validator, metadata):
        if field_type == TYPE_COMBOBOX:
            widget = NoScrollComboBox()
            apply_field_style(widget)
            if values:
                widget.addItems(values)
            default_value = (metadata or {}).get("default")
            if default_value:
                idx = widget.findText(default_value)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
        elif field_type == TYPE_TEXTBOX:
            widget = QLineEdit()
            apply_field_style(widget)
            validator_instance = self.get_validator(validator)
            if validator_instance:
                widget.setValidator(validator_instance)
        else:
            return None

        key_name = key if isinstance(key, str) else None
        if key_name:
            widget.setObjectName(key_name)
        self._register_input_widget(key_name, widget)
        self._apply_field_specific_config(key_name, widget, metadata or {})
        return widget

    def _register_input_widget(self, key, widget):
        if key == KEY_STRUCTURE_TYPE:
            self.structure_type_combo = widget
        elif key == KEY_SPAN:
            self.span_input = widget
        elif key == KEY_CARRIAGEWAY_WIDTH:
            self.carriageway_input = widget
        elif key == KEY_INCLUDE_MEDIAN:
            self.include_median_combo = widget
        elif key == KEY_FOOTPATH:
            self.footpath_combo = widget
        elif key == KEY_SKEW_ANGLE:
            self.skew_input = widget
        elif key == KEY_GIRDER:
            self.girder_combo = widget
        elif key == KEY_CROSS_BRACING:
            self.cross_bracing_combo = widget
        elif key == KEY_END_DIAPHRAGM:
            self.end_diaphragm_combo = widget
        elif key == KEY_DECK_CONCRETE_GRADE_BASIC:
            self.deck_combo = widget

    def _apply_field_specific_config(self, key, widget, metadata):
        if not key or widget is None:
            return
        if key == KEY_STRUCTURE_TYPE and hasattr(widget, "currentTextChanged"):
            widget.currentTextChanged.connect(self.on_structure_type_changed)
        elif key == KEY_SPAN and isinstance(widget, QLineEdit):
            widget.setValidator(QDoubleValidator(SPAN_MIN, SPAN_MAX, 2))
            widget.setPlaceholderText(f"{SPAN_MIN}-{SPAN_MAX} m")
        elif key == KEY_CARRIAGEWAY_WIDTH and isinstance(widget, QLineEdit):
            widget.setValidator(QDoubleValidator(0.0, 100.0, 2))
            widget.editingFinished.connect(self.validate_carriageway_width)
        elif key == KEY_INCLUDE_MEDIAN and hasattr(widget, "currentTextChanged"):
            widget.currentTextChanged.connect(self.on_include_median_changed)
            default_value = metadata.get("default")
            if default_value:
                idx = widget.findText(default_value)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
        elif key == KEY_FOOTPATH and hasattr(widget, "currentTextChanged"):
            widget.currentTextChanged.connect(self.on_footpath_changed)
            default_value = metadata.get("default")
            if default_value:
                idx = widget.findText(default_value)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
        elif key == KEY_SKEW_ANGLE and isinstance(widget, QLineEdit):
            widget.setValidator(QDoubleValidator(SKEW_ANGLE_MIN, SKEW_ANGLE_MAX, 1))
            widget.setPlaceholderText(f"{SKEW_ANGLE_MIN} - {SKEW_ANGLE_MAX}°")
        elif key == KEY_DECK_CONCRETE_GRADE_BASIC and hasattr(widget, "findText"):
            default_value = metadata.get("default")
            if default_value:
                idx = widget.findText(default_value)
                if idx >= 0:
                    widget.setCurrentIndex(idx)

    def _finalize_section_contexts(self):
        for context in self.section_contexts.values():
            metadata = context.get("metadata", {})
            note_config = metadata.get("post_note")
            if note_config:
                self._add_section_note(context, note_config)

            for row_entry in metadata.get("post_rows", []):
                row_config = self._prepare_button_row_config(row_entry)
                if row_config:
                    self._add_button_row(context["layout"], row_config)

    def _add_section_note(self, context, note_config):
        note_label = QLabel(note_config.get("text", ""))
        note_label.setStyleSheet(self._section_label_style())
        note_label.setVisible(False)
        context["layout"].addWidget(note_label)
        attr_name = note_config.get("attr")
        if attr_name:
            setattr(self, attr_name, note_label)

    def on_footpath_changed(self, footpath_value):
        """Update additional inputs when footpath changes"""
        if self.additional_inputs and self.additional_inputs.isVisible():
            if hasattr(self, 'additional_inputs_widget'):
                self.additional_inputs_widget.update_footpath_value(footpath_value)

    def on_include_median_changed(self, _value):
        self._update_carriageway_placeholder()
        # Re-validate silently so previously entered values honor the new limits
        self.validate_carriageway_width(show_message=False)

    def _carriageway_limits(self):
        include_median = self._is_median_included()
        min_width = CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN if include_median else CARRIAGEWAY_WIDTH_MIN
        return min_width, CARRIAGEWAY_WIDTH_MAX_LIMIT

    def _update_carriageway_placeholder(self):
        if not hasattr(self, "carriageway_input") or self.carriageway_input is None:
            return
        min_width, max_width = self._carriageway_limits()
        suffix = " per side" if self._is_median_included() else ""
        self.carriageway_input.setPlaceholderText(f"{min_width:.2f} - {max_width:.1f} m{suffix}")

    def validate_carriageway_width(self, show_message=True):
        if not self.carriageway_input:
            return
        text = self.carriageway_input.text().strip()
        if not text:
            return
        try:
            value = float(text)
        except ValueError:
            self.carriageway_input.clear()
            if show_message:
                QMessageBox.warning(self, "Carriageway Width", "Please enter a numeric carriageway width.")
            return

        min_width, max_width = self._carriageway_limits()
        include_median = self._is_median_included()
        message = None

        if value < min_width:
            if include_median:
                message = "IRC 5 Clause 104.3.1 requires minimum carriageway width on both sides of the median to be at least 7.5 m."
            else:
                message = "IRC 5 Clause 104.3.1 requires minimum carriageway width of 4.25 m."
            value = min_width
        elif value > max_width:
            message = "Software limits carriageway width upto 23.6 m"
            value = max_width

        self.carriageway_input.setText(f"{value:.2f}")
        if message and show_message:
            QMessageBox.warning(self, "Carriageway Width", message)

    def _get_effective_carriageway_width(self):
        min_width, max_width = self._carriageway_limits()
        width = min_width
        if self.carriageway_input and self.carriageway_input.text():
            try:
                width = float(self.carriageway_input.text())
            except ValueError:
                width = min_width
        width = max(min_width, min(width, max_width))
        if self._is_median_included():
            return width * 2.0  # Two carriageways, one on each side of the median
        return width

    def _is_median_included(self):
        if not self.include_median_combo:
            return False
        return self.include_median_combo.currentText().lower() == "yes"

    def show_material_properties_dialog(self):
        """Open the material properties dialog with the relevant member selected."""
        if self.material_dialog is None:
            self.material_dialog = MaterialPropertiesDialog(self)

        member = "Girder"
        focus_widget = QApplication.focusWidget()
        focus_map = {
            getattr(self, 'girder_combo', None): "Girder",
            getattr(self, 'deck_combo', None): "Deck",
            getattr(self, 'cross_bracing_combo', None): "Cross Bracing",
            getattr(self, 'end_diaphragm_combo', None): "End Diaphragm",
        }
        for widget, name in focus_map.items():
            if widget is not None and widget is focus_widget:
                member = name
                break

        self.material_dialog.sync_with_parent_defaults()
        self.material_dialog.set_member(member)
        self.material_dialog.show()
        self.material_dialog.raise_()
        self.material_dialog.activateWindow()