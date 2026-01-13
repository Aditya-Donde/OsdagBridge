import sys
import os
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QComboBox, QScrollArea, QLabel, QFormLayout, QLineEdit, QGroupBox, QSizePolicy, QMessageBox, QInputDialog, QDialog, QCheckBox, QFrame,
    QDialogButtonBox, QStackedWidget
)
from PySide6.QtCore import Qt, QRegularExpression, QSize, QTimer, QPoint, QEvent, Signal
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
        grade = material or self._get_parent_grade(member) or (VALUES_MATERIAL[0] if VALUES_MATERIAL else "")
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
        return VALUES_DECK_CONCRETE_GRADE if member == "Deck" else VALUES_MATERIAL

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
    # Signal emitted when any input value changes
    input_value_changed = Signal()
    
    def __init__(self, backend, parent):
        super().__init__()
        self.parent = parent
        self.backend = backend
        self.input_widget = None
        self.structure_type_combo = None
        self.project_location_combo = None
        self.custom_location_input = None
        self.include_median_combo = None
        self.footpath_combo = None
        self.additional_inputs = None
        self.additional_inputs_widget = None
        self.additional_input_values = {}  # Store values from additional inputs dialog
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
    
    def get_all_input_values(self):
        """Collect all input values from the input dock"""
        input_values = {}
        
        # Helper function to safely get numeric value
        def get_numeric_value(widget):
            if isinstance(widget, QLineEdit):
                text = widget.text().strip()
                if text:
                    try:
                        return float(text)
                    except ValueError:
                        pass
            return None
        
        # Collect span
        if hasattr(self, 'span_input'):
            val = get_numeric_value(self.span_input)
            if val is not None:
                input_values[KEY_SPAN] = val
        
        # Collect carriageway width
        if hasattr(self, 'carriageway_input'):
            val = get_numeric_value(self.carriageway_input)
            if val is not None:
                input_values[KEY_CARRIAGEWAY_WIDTH] = val
        
        # Collect skew angle
        if hasattr(self, 'skew_input'):
            val = get_numeric_value(self.skew_input)
            if val is not None:
                input_values[KEY_SKEW_ANGLE] = val
            else:
                input_values[KEY_SKEW_ANGLE] = 0.0  # Default
        
        # Collect footpath
        # Footpath handling (derive numeric values, do NOT store KEY_FOOTPATH)
        if hasattr(self, 'footpath_combo'):
            footpath = self.footpath_combo.currentText()

            if footpath.lower() == "none":
                input_values[KEY_FOOTPATH_WIDTH] = 0.0
                input_values[KEY_FOOTPATH_THICKNESS] = 0.0
            else:
                # Defaults (or override via Additional Inputs)
                input_values.setdefault(KEY_FOOTPATH_WIDTH, 1.5)
                input_values.setdefault(KEY_FOOTPATH_THICKNESS, 200.0)

        
        # Collect median
        if hasattr(self, 'include_median_combo'):
            input_values[KEY_INCLUDE_MEDIAN] = (self.include_median_combo.currentText() == "Yes")
        
        # Add default values for parameters that CAD widget needs
        # These will be overridden by additional inputs if present
        input_values.setdefault(KEY_NO_OF_GIRDERS, 4)
        input_values.setdefault(KEY_GIRDER_SPACING, 2.75)
        input_values.setdefault(KEY_DECK_OVERHANG, 1.0)
        input_values.setdefault(KEY_DECK_THICKNESS, 200)
        input_values.setdefault(KEY_FOOTPATH_WIDTH, 1.5)
        input_values.setdefault(KEY_FOOTPATH_THICKNESS, 200)
        input_values.setdefault(KEY_CROSS_BRACING_SPACING, 3.5)
        input_values.setdefault(KEY_CRASH_BARRIER_WIDTH, 0.5)
        
        # Merge values from Additional Inputs dialog if they exist
        if hasattr(self, 'additional_input_values') and self.additional_input_values:
            input_values.update(self.additional_input_values)
        
        return input_values
    
    def emit_value_changed(self):
        """Emit signal to notify that input values have changed"""
        self.input_value_changed.emit()

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


        # === Type of Structure Box ===
        type_box = QGroupBox("Type of Structure")
        type_box.setStyleSheet("""
            QGroupBox {
                border: 1px solid #90AF13;
                border-radius: 4px;
                background-color: white;
                padding: 8px;
                margin-top: 12px;
                font-size: 10px;
                font-weight: bold;
                color: #333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 8px;
                padding: 0 4px;
                margin-top: 4px;
                background-color: white;
                color: #333;
            }
        """)
        type_box_layout = QVBoxLayout(type_box)
        type_box_layout.setContentsMargins(8, 8, 8, 8)
        type_box_layout.setSpacing(8)
        
        # Type of Structure field
        type_row = QHBoxLayout()
        type_field_label = QLabel("Type of Structure")
        type_field_label.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 12px;
                background: transparent;
            }
        """)
        type_field_label.setMinimumWidth(110)
        
        self.structure_type_combo = NoScrollComboBox()
        self.structure_type_combo.setObjectName(KEY_STRUCTURE_TYPE)
        apply_field_style(self.structure_type_combo)
        self.structure_type_combo.addItems(VALUES_STRUCTURE_TYPE)
        
        type_row.addWidget(type_field_label)
        type_row.addWidget(self.structure_type_combo, 1)
        type_box_layout.addLayout(type_row)

        self.structure_note = QLabel("*Other structures not included")
        self.structure_note.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 12px;
                background: transparent;
            }
        """)
        self.structure_note.setVisible(False)
        type_box_layout.addWidget(self.structure_note)

        self.structure_type_combo.currentTextChanged.connect(self.on_structure_type_changed)
        group_container_layout.addWidget(type_box)
        
        # === Project Location Box ===
        location_box = QGroupBox()
        location_box.setStyleSheet("""
            QGroupBox {
                border: 1px solid #90AF13;
                border-radius: 4px;
                background-color: white;
                padding: 8px;
                margin-top: 12px;
            }
        """)
        location_box_layout = QVBoxLayout(location_box)
        location_box_layout.setContentsMargins(8, 8, 8, 8)
        location_box_layout.setSpacing(8)

        loc_header = QHBoxLayout()
        loc_title = QLabel("Project Location*")
        loc_title.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 12px;
                background: transparent;
            }
        """)
        loc_title.setMinimumWidth(110)
        loc_header.addWidget(loc_title)
        
        add_here_btn = QPushButton("Add Here")
        add_here_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_here_btn.setStyleSheet("""
            QPushButton {
                background-color: #90AF13;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 11px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #7a9a12;
            }
            QPushButton:disabled{
                background: #D0D0D0;
                color: #666;
            }
            
        """)
        add_here_btn.clicked.connect(self.show_project_location_dialog)
        loc_header.addWidget(add_here_btn, 1)
        location_box_layout.addLayout(loc_header)        
        group_container_layout.addWidget(location_box)
        
        # === Superstructure Section (Contains Everything) ===
        structure_group = QGroupBox()
        structure_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #90AF13;
                border-radius: 5px;
                margin-top: 0px;
                padding-top: 5px;
                background-color: white;
            }
        """)
        structure_layout = QVBoxLayout()
        structure_layout.setContentsMargins(10, 10, 10, 10)
        structure_layout.setSpacing(10)
        
        # Header with title and collapse icon
        struct_header = QHBoxLayout()
        struct_title = QLabel("Superstructure")
        struct_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #333;")
        struct_header.addWidget(struct_title)
        struct_header.addStretch()
        
        # Collapse/expand toggle using SVG icon
        toggle_btn = QPushButton()
        toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_btn.setCheckable(True)
        toggle_btn.setChecked(True)
        toggle_btn.setIcon(QIcon(":/vectors/arrow_up_light.svg"))
        toggle_btn.setIconSize(QSize(20, 20))
        toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 2px;
            }
            QPushButton:hover {
                background: transparent;
            }
            QPushButton:pressed {
                background: transparent;
            }
        """)
        struct_header.addWidget(toggle_btn)

        structure_layout.addLayout(struct_header)

        # body widget that contains everything inside the Superstructure and can be hidden
        structure_body = QFrame()
        structure_body.setFrameShape(QFrame.NoFrame)
        structure_body_layout = QVBoxLayout(structure_body)
        structure_body_layout.setContentsMargins(0, 0, 0, 0)
        structure_body_layout.setSpacing(10)
        structure_body.setVisible(True)
        structure_layout.addWidget(structure_body)

        def _toggle_structure(checked):
            # checked True means show body (open)
            structure_body.setVisible(checked)
            toggle_btn.setIcon(QIcon(":/vectors/arrow_up_light.svg" if checked else ":/vectors/arrow_down_light.svg"))

        toggle_btn.toggled.connect(_toggle_structure)
        
        # === Geometric Details Box ===
        geo_box = QGroupBox("Geometric Details")
        geo_box.setStyleSheet("""
            QGroupBox {
                border: 1px solid #90AF13;
                border-radius: 4px;
                background-color: white;
                padding: 8px;
                margin-top: 12px;
                font-size: 10px;
                font-weight: bold;
                color: #333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 8px;
                padding: 0 4px;
                margin-top: 4px;
                background-color: white;
                color: #333;
            }
        """)
        geo_box_layout = QVBoxLayout(geo_box)
        geo_box_layout.setContentsMargins(8, 8, 8, 8)
        geo_box_layout.setSpacing(8)
        
        # Span
        span_row = QHBoxLayout()
        span_label = QLabel("Span*")
        span_label.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 12px;
                background: transparent;
            }
        """)
        span_label.setMinimumWidth(110)
        self.span_input = QLineEdit()
        self.span_input.setObjectName(KEY_SPAN)
        apply_field_style(self.span_input)
        self.span_input.setValidator(QDoubleValidator(SPAN_MIN, SPAN_MAX, 2))
        self.span_input.setPlaceholderText(f"{SPAN_MIN}-{SPAN_MAX} m")
        self.span_input.textChanged.connect(self.emit_value_changed)
        span_row.addWidget(span_label)
        span_row.addWidget(self.span_input, 1)
        geo_box_layout.addLayout(span_row)
        
        # Carriageway Width
        carriageway_row = QHBoxLayout()
        carriageway_label = QLabel("Carriageway Width*")
        carriageway_label.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 12px;
                background: transparent;
            }
        """)
        carriageway_label.setMinimumWidth(110)
        self.carriageway_input = QLineEdit()
        self.carriageway_input.setObjectName(KEY_CARRIAGEWAY_WIDTH)
        apply_field_style(self.carriageway_input)
        self.carriageway_input.setValidator(QDoubleValidator(0.0, 100.0, 2))
        self.carriageway_input.editingFinished.connect(self.validate_carriageway_width)
        self.carriageway_input.textChanged.connect(self.emit_value_changed)
        carriageway_row.addWidget(carriageway_label)
        carriageway_row.addWidget(self.carriageway_input, 1)
        geo_box_layout.addLayout(carriageway_row)

        # Include Median option
        median_row = QHBoxLayout()
        median_row.setContentsMargins(0, 0, 0, 0)
        median_row.setSpacing(8)

        median_label = QLabel("Include Median")
        median_label.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 12px;
                background: transparent;
            }
        """)
        median_label.setMinimumWidth(110)
        median_row.addWidget(median_label)

        self.include_median_combo = NoScrollComboBox()
        self.include_median_combo.addItems(["No", "Yes"])
        self.include_median_combo.setCurrentIndex(0)
        self.include_median_combo.setObjectName(KEY_INCLUDE_MEDIAN)
        apply_field_style(self.include_median_combo)
        #self.include_median_combo.setMaximumWidth(110)
        self.include_median_combo.currentTextChanged.connect(self.on_include_median_changed)
        self.include_median_combo.currentTextChanged.connect(self.emit_value_changed)
        median_row.addWidget(self.include_median_combo, 1)
        median_row.addStretch()
        geo_box_layout.addLayout(median_row)
        self._update_carriageway_placeholder()
        
        # Footpath
        footpath_row = QHBoxLayout()
        footpath_label = QLabel("Footpath")
        footpath_label.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 12px;
                background: transparent;
            }
        """)
        footpath_label.setMinimumWidth(110)
        self.footpath_combo = NoScrollComboBox()
        #self.footpath_combo.setObjectName(KEY_FOOTPATH)
        apply_field_style(self.footpath_combo)
        self.footpath_combo.addItems(VALUES_FOOTPATH)
        self.footpath_combo.setCurrentIndex(0)
        self.footpath_combo.currentTextChanged.connect(self.on_footpath_changed)
        self.footpath_combo.currentTextChanged.connect(self.emit_value_changed)
        footpath_row.addWidget(footpath_label)
        footpath_row.addWidget(self.footpath_combo, 1)
        geo_box_layout.addLayout(footpath_row)
        
        # Skew Angle
        skew_row = QHBoxLayout()
        skew_label = QLabel("Skew Angle")
        skew_label.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 12px;
                background: transparent;
            }
        """)
        skew_label.setMinimumWidth(110)
        self.skew_input = QLineEdit()
        self.skew_input.setObjectName(KEY_SKEW_ANGLE)
        apply_field_style(self.skew_input)
        self.skew_input.setValidator(QDoubleValidator(SKEW_ANGLE_MIN, SKEW_ANGLE_MAX, 1))
        #self.skew_input.setText(f"{str(SKEW_ANGLE_DEFAULT)}°")
        self.skew_input.setPlaceholderText(f"{SKEW_ANGLE_MIN} - {SKEW_ANGLE_MAX}°")
        self.skew_input.textChanged.connect(self.emit_value_changed)
        skew_row.addWidget(skew_label)
        skew_row.addWidget(self.skew_input, 1)
        geo_box_layout.addLayout(skew_row)
        
        # Additional Geometry (inside Geometric Details)
        add_geo_row = QHBoxLayout()
        add_geo_label = QLabel("Additional Geometry")
        add_geo_label.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 12px;
                background: transparent;
            }
        """)
        add_geo_label.setMinimumWidth(110)
        add_geo_row.addWidget(add_geo_label)
        
        modify_geo_btn = QPushButton("Modify Here")
        modify_geo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        modify_geo_btn.setStyleSheet("""
            QPushButton {
                background-color: #90AF13;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 11px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #7a9a12;
            }
            QPushButton:disabled{
                background: #D0D0D0;
                color: #666;
            }
        """)
        modify_geo_btn.clicked.connect(self.show_additional_inputs)
        add_geo_row.addWidget(modify_geo_btn, 1)
        geo_box_layout.addLayout(add_geo_row)
        
        structure_body_layout.addWidget(geo_box)
        
        # === Material Inputs Box ===
        material_box = QGroupBox("Material Inputs")
        material_box.setStyleSheet("""
            QGroupBox {
                border: 1px solid #90AF13;
                border-radius: 4px;
                background-color: white;
                padding: 8px;
                margin-top: 12px;
                font-size: 10px;
                font-weight: bold;
                color: #333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 8px;
                padding: 0 4px;
                margin-top: 4px;
                background-color: white;
                color: #333;
            }
        """)
        material_box_layout = QVBoxLayout(material_box)
        material_box_layout.setContentsMargins(8, 8, 8, 8)
        material_box_layout.setSpacing(8)
        
        # Girder
        girder_row = QHBoxLayout()
        girder_label = QLabel("Girder")
        girder_label.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 12px;
                background: transparent;
            }
        """)
        girder_label.setMinimumWidth(110)
        self.girder_combo = NoScrollComboBox()
        self.girder_combo.setObjectName(KEY_GIRDER)
        apply_field_style(self.girder_combo)
        self.girder_combo.addItems(VALUES_MATERIAL)
        girder_row.addWidget(girder_label)
        girder_row.addWidget(self.girder_combo, 1)
        material_box_layout.addLayout(girder_row)
        
        # Cross Bracing
        cross_bracing_row = QHBoxLayout()
        cross_bracing_label = QLabel("Cross Bracing")
        cross_bracing_label.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 12px;
                background: transparent;
            }
        """)
        cross_bracing_label.setMinimumWidth(110)
        self.cross_bracing_combo = NoScrollComboBox()
        self.cross_bracing_combo.setObjectName(KEY_CROSS_BRACING)
        apply_field_style(self.cross_bracing_combo)
        self.cross_bracing_combo.addItems(VALUES_MATERIAL)
        cross_bracing_row.addWidget(cross_bracing_label)
        cross_bracing_row.addWidget(self.cross_bracing_combo, 1)
        material_box_layout.addLayout(cross_bracing_row)

        # End Diaphragm
        end_diaphragm_row = QHBoxLayout()
        end_diaphragm_label = QLabel("End Diaphragm")
        end_diaphragm_label.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 12px;
                background: transparent;
            }
        """)
        end_diaphragm_label.setMinimumWidth(110)
        self.end_diaphragm_combo = NoScrollComboBox()
        self.end_diaphragm_combo.setObjectName(KEY_END_DIAPHRAGM)
        apply_field_style(self.end_diaphragm_combo)
        self.end_diaphragm_combo.addItems(VALUES_MATERIAL)
        end_diaphragm_row.addWidget(end_diaphragm_label)
        end_diaphragm_row.addWidget(self.end_diaphragm_combo, 1)
        material_box_layout.addLayout(end_diaphragm_row)
        
        # Deck
        deck_row = QHBoxLayout()
        deck_label = QLabel("Deck")
        deck_label.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 12px;
                background: transparent;
            }
        """)
        deck_label.setMinimumWidth(110)
        self.deck_combo = NoScrollComboBox()
        self.deck_combo.setObjectName(KEY_DECK_CONCRETE_GRADE_BASIC)
        apply_field_style(self.deck_combo)
        self.deck_combo.addItems(VALUES_DECK_CONCRETE_GRADE)
        self.deck_combo.setCurrentText("M 25")
        deck_row.addWidget(deck_label)
        deck_row.addWidget(self.deck_combo, 1)
        material_box_layout.addLayout(deck_row)

        # Material Properties header with button
        mat_prop_header = QHBoxLayout()
        mat_prop_title = QLabel("Properties")
        mat_prop_title.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 12px;
                background: transparent;
            }
        """)
        mat_prop_title.setMinimumWidth(110)
        mat_prop_header.addWidget(mat_prop_title)
        
        modify_mat_btn = QPushButton("Modify Here")
        modify_mat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        modify_mat_btn.setStyleSheet("""
            QPushButton {
                background-color: #90AF13;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 11px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #7a9a12;
            }
            QPushButton:disabled{
                background: #f1f1f1;
                color: #666;
            }
        """)
        modify_mat_btn.clicked.connect(self.show_material_properties_dialog)
        mat_prop_header.addWidget(modify_mat_btn, 1)
        material_box_layout.addLayout(mat_prop_header)
        
        structure_body_layout.addWidget(material_box)
        
        # Close the Superstructure section
        structure_group.setLayout(structure_layout)
        group_container_layout.addWidget(structure_group)

        # === Substructure Section (empty body for now) ===
        sub_group = QGroupBox()
        sub_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #90AF13;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 5px;
                background-color: white;
            }
        """)
        sub_layout = QVBoxLayout()
        sub_layout.setContentsMargins(10, 10, 10, 10)
        sub_layout.setSpacing(8)

        # Header with toggle
        sub_header = QHBoxLayout()
        sub_title = QLabel("Substructure")
        sub_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #333;")
        sub_header.addWidget(sub_title)
        sub_header.addStretch()

        sub_toggle = QPushButton()
        sub_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        sub_toggle.setCheckable(True)
        sub_toggle.setChecked(True)
        sub_toggle.setIcon(QIcon(":/vectors/arrow_up_light.svg"))
        sub_toggle.setIconSize(QSize(20, 20))
        sub_toggle.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 2px;
            }
            QPushButton:hover {
                background: transparent;
            }
            QPushButton:pressed {
                background: transparent;
            }
        """)
        sub_header.addWidget(sub_toggle)
        sub_layout.addLayout(sub_header)

        sub_body = QFrame()
        sub_body.setFrameShape(QFrame.NoFrame)
        sub_body_layout = QVBoxLayout(sub_body)
        sub_body_layout.setContentsMargins(0,0,0,0)
        sub_body_layout.setSpacing(6)
        sub_body.setVisible(True)
        sub_layout.addWidget(sub_body)

        def _toggle_sub(checked):
            sub_body.setVisible(checked)
            sub_toggle.setIcon(QIcon(":/vectors/arrow_up_light.svg" if checked else ":/vectors/arrow_down_light.svg"))

        sub_toggle.toggled.connect(_toggle_sub)

        sub_group.setLayout(sub_layout)
        group_container_layout.addWidget(sub_group)

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
        
        self.additional_inputs = AdditionalInputs(footpath_value, carriageway_width)
        
        self.additional_inputs = AdditionalInputs(footpath_value, carriageway_width)

        # CONNECT HERE
        self.additional_inputs.cadDataChanged.connect(self._on_additional_inputs_changed)

        self.additional_inputs.exec()
    
    def _on_additional_inputs_changed(self, cad_data):
        # Store additional input values
        self.additional_input_values = cad_data

        # Notify main window that inputs changed
        self.input_value_changed.emit()

    
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
        self.additional_inputs = None
        self.additional_inputs_widget = None

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