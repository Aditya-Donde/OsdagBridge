from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from pathlib import Path
import sqlite3
import re

from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.desktop.ui.docks.dock_utils import apply_field_style
from osdagbridge.core.utils.common import (
    connectdb, KEY_GIRDER, KEY_CROSS_BRACING, KEY_END_DIAPHRAGM, KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_MATERIAL_GIRDER_FY, KEY_MATERIAL_GIRDER_FU, KEY_MATERIAL_GIRDER_E,
    KEY_MATERIAL_GIRDER_G, KEY_MATERIAL_GIRDER_POISSON, KEY_MATERIAL_GIRDER_THERMAL,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_MATERIAL_DECK_FCK, KEY_MATERIAL_DECK_FCTM, KEY_MATERIAL_DECK_ECM, KEY_MATERIAL_DECK_THERMAL,
    KEY_MATERIAL_DECK_DENSITY,
    DISP_MATERIAL_GIRDER_FY, DISP_MATERIAL_GIRDER_FU, DISP_MATERIAL_GIRDER_E,
    DISP_MATERIAL_GIRDER_G, DISP_MATERIAL_GIRDER_POISSON, DISP_MATERIAL_GIRDER_THERMAL,
    DISP_MATERIAL_GIRDER_DENSITY,
    DISP_MATERIAL_DECK_FCK, DISP_MATERIAL_DECK_FCTM, DISP_MATERIAL_DECK_ECM, DISP_MATERIAL_DECK_THERMAL,
    DISP_MATERIAL_DECK_DENSITY,
)
from osdagbridge.desktop.ui.utils.custom_cursors import pointing_hand_cursor

concrete_properies = connectdb("Concrete_Grade_Properties")

DIALOG_TITLE_MATERIAL_PROPERTIES = "Enter Custom Properties"
CUSTOM_STEEL_PREFIX = "custom_steel_"
CUSTOM_CONCRETE_PREFIX = "custom_concrete_"
DEFAULT_DECK_CUSTOM_GRADE = "M 15"

MATPROP_LABEL_MATERIAL = "Material"

ECM_FACTOR_OPTION_QUARTZITE = "Quartzite/granite aggregates = 1"
ECM_FACTOR_OPTION_LIMESTONE = "Limestone aggregates = 0.9"
ECM_FACTOR_OPTION_SANDSTONE = "Sandstone aggregates = 0.7"
ECM_FACTOR_OPTION_BASALT = "Basalt aggregates = 1.2"
ECM_FACTOR_OPTION_CUSTOM = "Custom"

ECM_FACTOR_OPTIONS = [
    (ECM_FACTOR_OPTION_QUARTZITE, 1.0),
    (ECM_FACTOR_OPTION_LIMESTONE, 0.9),
    (ECM_FACTOR_OPTION_SANDSTONE, 0.7),
    (ECM_FACTOR_OPTION_BASALT, 1.2),
    (ECM_FACTOR_OPTION_CUSTOM, None),
]
DEFAULT_ECM_FACTOR_LABEL = ECM_FACTOR_OPTIONS[0][0]

# HARD CODED VALUES REMOVED AND COMPLETELY SWAPPED OUT
STEEL_THERMAL_COEFF = 11.7      # COEFF is constant regardless, so not removed.

# Weight densities fetched from IRC6:2017 Cl.203 (t/m3) and converted to kN/m3
_dead_load_data = IRC6_2017.cl_203_dead_load()
STEEL_WEIGHT_DENSITY = round(_dead_load_data['steel'] * 9.8, 2)           # 7.8 t/m3 -> kN/m3
CONCRETE_WEIGHT_DENSITY = round(_dead_load_data['concrete_cement_reinforced'] * 9.8, 2)  # 2.5 t/m3 -> kN/m3

def _locate_resource_file(file_name: str) -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "core" / "data" / "ResourceFiles" / file_name
        if candidate.exists():
            return candidate
    return current.parents[3] / "core" / "data" / "ResourceFiles" / file_name


def _execute_resource_query(query: str):
    db_path = _locate_resource_file("Intg_osdag.sqlite")
    if not db_path.exists():
        return None

    connection = sqlite3.connect(str(db_path))
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error:
        return None
    finally:
        connection.close()


def _load_concrete_grade_values_from_db():
    rows = _execute_resource_query(
        """
        SELECT Grade, fck, fctm, Ecm
        FROM Concrete_Grade_Properties
        """
    )

    values = {}
    if rows is not None:
        for grade, fck, fctm, ecm in rows:
            key = str(grade).strip().upper()
            values[key] = {
                "fck": float(fck),
                "fctm": float(fctm),
                "Ecm": float(ecm),
            }

    return values


def _normalize_steel_material_name(name: str) -> str:
    return "".join(str(name or "").upper().split())


def _load_steel_material_values_from_db():
        values = {}
        rows = _execute_resource_query(
                """
                SELECT Grade, [Yield Strength], [Ultimate Tensile Strength], [Modulus of Elasticity], [Poisson's Ratio]
                FROM Steel_Grade_Properties
                """
            )
        if rows is None:
            return {}

        try:
            for grade, fy, fu, e, poisson in rows:
                key = _normalize_steel_material_name(grade)
                if not key:
                    continue

                e_value = float(e)
                poisson_value = float(poisson)
                values[key] = {
                    "Fy": float(fy),
                    "Fu": float(fu),
                    "E": e_value,
                    "Poisson": poisson_value,
                    "G": round(e_value / (2 * (1 + poisson_value)), 1),
                }

            return values
        except (TypeError, ValueError):
            return {}

    
STEEL_MATERIAL_BASE_VALUES = _load_steel_material_values_from_db()
CONCRETE_GRADE_BASE_VALUES = _load_concrete_grade_values_from_db()


TYPE_TEXTBOX = 'textbox'

def steel_material_properties_values():
    return [
        (KEY_MATERIAL_GIRDER_DENSITY, DISP_MATERIAL_GIRDER_DENSITY, TYPE_TEXTBOX, None, True, 'Double Validator'),
        (KEY_MATERIAL_GIRDER_FY, DISP_MATERIAL_GIRDER_FY, TYPE_TEXTBOX, None, True, 'Double Validator'),
        (KEY_MATERIAL_GIRDER_FU, DISP_MATERIAL_GIRDER_FU, TYPE_TEXTBOX, None, True, 'Double Validator'),
        (KEY_MATERIAL_GIRDER_E, DISP_MATERIAL_GIRDER_E, TYPE_TEXTBOX, None, True, 'Double Validator'),
        (KEY_MATERIAL_GIRDER_G, DISP_MATERIAL_GIRDER_G, TYPE_TEXTBOX, None, True, 'Double Validator'),
        (KEY_MATERIAL_GIRDER_POISSON, DISP_MATERIAL_GIRDER_POISSON, TYPE_TEXTBOX, None, True, 'Double Validator'),
        (KEY_MATERIAL_GIRDER_THERMAL, DISP_MATERIAL_GIRDER_THERMAL, TYPE_TEXTBOX, None, True, 'Double Validator'),
    ]

def deck_material_properties_values():
    return [
        (KEY_MATERIAL_DECK_DENSITY, DISP_MATERIAL_DECK_DENSITY, TYPE_TEXTBOX, None, True, 'Double Validator'),
        (KEY_MATERIAL_DECK_FCK, DISP_MATERIAL_DECK_FCK, TYPE_TEXTBOX, None, True, 'Double Validator'),
        (KEY_MATERIAL_DECK_FCTM, DISP_MATERIAL_DECK_FCTM, TYPE_TEXTBOX, None, True, 'Double Validator'),
        (KEY_MATERIAL_DECK_ECM, DISP_MATERIAL_DECK_ECM, TYPE_TEXTBOX, None, True, 'Double Validator'),
        (KEY_MATERIAL_DECK_THERMAL, DISP_MATERIAL_DECK_THERMAL, TYPE_TEXTBOX, None, True, 'Double Validator'),
    ]

class MaterialPropertiesDialog(QDialog):
    def __init__(self, parent=None, read_only=False, selected_material=None, member=None, custom_fields=None):
        super().__init__(parent)
        self.read_only = read_only
        self.selected_material = selected_material or ""
        self.member = member
        self.custom_fields = custom_fields
        self.is_deck_material = (self.member == "Deck") or self._is_deck_material(self.selected_material)
        self.setWindowTitle(DIALOG_TITLE_MATERIAL_PROPERTIES)
        self.setObjectName("material_properties_dialog")
        self.setMinimumWidth(580)
        self.setStyleSheet("""
        QDialog#material_properties_dialog {
            background-color: white;
            border: 1px solid #90AF13;
        }
        QPushButton#primary {
            background-color: #ffffff;
            color: #1f1f1f;
            border-radius: 6px;
            padding: 8px 18px;
            font-weight: 600;
        }
        QPushButton#primary:hover { background-color: #90AF13; }
        QPushButton#primary:pressed { background-color: #64850c; }
        QPushButton#ghost {
            background-color: #ffffff;
            color: #1d1d1d;
            border-radius: 6px;
            padding: 8px 14px;
            font-weight: 600;
        }
        QPushButton#ghost:hover { background-color: #90AF13; }
        QPushButton#ghost:pressed { background-color: #d9d9d9; }
    """)

        self.fields = deck_material_properties_values() if self.is_deck_material else steel_material_properties_values()
        self._loading = False
        self._suppress_auto_update = False
        default_prefix = CUSTOM_CONCRETE_PREFIX if self.is_deck_material else CUSTOM_STEEL_PREFIX
        initial_material = self.selected_material.strip() if self.read_only else default_prefix
        self.form_data = {
            "material": initial_material or default_prefix,
            "fields": self._defaults_for_material(initial_material or default_prefix),
        }

        self.material_input = QLineEdit(self.form_data["material"])
        self.material_input.setReadOnly(True)
        self.material_input.setFixedWidth(242)
        self.material_input.setMinimumHeight(28)
        self.material_input.setStyleSheet("""
            QLineEdit {
                padding: 1px 7px;
                border: 1px solid #a8a8a8;
                border-radius: 6px;
                background-color: #f1f1f1;
                color: #555555;
            }
        """)
        self.setupWrapper()
        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setContentsMargins(20, 16, 20, 16)

        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(12)
        
        material_row = QHBoxLayout()
        material_row.setContentsMargins(0, 0, 0, 0)
        material_row.setSpacing(18)
        material_label = QLabel(MATPROP_LABEL_MATERIAL)
        material_label.setStyleSheet("font-size: 12px; color: #2d2d2d;")
        material_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        material_label.setFixedWidth(280)
        material_row.addWidget(material_label)
        material_row.addWidget(self.material_input)
        material_row.addStretch()
        form_layout.addLayout(material_row)
        
        main_layout.addWidget(form_container)

        self.fields_page = self._build_fields_form()
        main_layout.addWidget(self.fields_page)

        self._add_footer_buttons(main_layout)

        if self.read_only:
            self._load_material_info_for_view(self.selected_material)
            self._set_read_only_fields(True)
            self.setWindowTitle("Material Information")
            self.title_bar.setTitle("Material Information")
            
        else:
            self._populate_fields()
            self._update_custom_material_name()
        self.setFixedSize(self.sizeHint())

    def setupWrapper(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.Dialog)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        
        self.title_bar = CustomTitleBar(parent=self)
        self.title_bar.setTitle(DIALOG_TITLE_MATERIAL_PROPERTIES)
        main_layout.addWidget(self.title_bar)
        
        self.content_widget = QWidget(self)
        main_layout.addWidget(self.content_widget, 1)

    def closeEvent(self, event):
        super().closeEvent(event)

    def _add_footer_buttons(self, layout):
        footer = QHBoxLayout()
        footer.addStretch()

        if self.read_only:
            ok_btn = QPushButton("OK")
            ok_btn.setObjectName("primary")
            ok_btn.setCursor(pointing_hand_cursor())
            ok_btn.setMinimumWidth(90)
            ok_btn.setAutoDefault(False)
            ok_btn.clicked.connect(self.accept)
            footer.addWidget(ok_btn)
        else:
            add_btn = QPushButton("Add")
            add_btn.setObjectName("primary")
            add_btn.setCursor(pointing_hand_cursor())
            add_btn.setMinimumWidth(90)
            add_btn.setAutoDefault(False)
            add_btn.clicked.connect(self._validate_and_save)
            footer.addWidget(add_btn)

            cancel_btn = QPushButton("Cancel")
            cancel_btn.setObjectName("ghost")
            cancel_btn.setCursor(pointing_hand_cursor())
            cancel_btn.setMinimumWidth(90)
            cancel_btn.setAutoDefault(False)
            cancel_btn.clicked.connect(self.reject)
            footer.addWidget(cancel_btn)

        layout.addLayout(footer)

    def _validate_and_save(self):
        # Create a mapping from key to display label for better error messages
        key_to_label = {f[0]: f[1] for f in self.fields}
        
        for key, widget in self.field_inputs.items():
            text = widget.text().strip()
            display_name = key_to_label.get(key, key)
            
            if not text:
                CustomMessageBox(
                    title="Validation Error",
                    text=f"Please enter a value for {display_name}.",
                    dialogType=MessageBoxType.Critical,
                ).exec()
                return
                
            try:
                val = float(text)
                if val <= 0.0:
                    CustomMessageBox(
                        title="Validation Error",
                        text=f"{display_name} must be greater than 0.",
                        dialogType=MessageBoxType.Critical,
                    ).exec()
                    return
            except ValueError:
                CustomMessageBox(
                    title="Validation Error",
                    text=f"Please enter a valid number for {display_name}.",
                    dialogType=MessageBoxType.Critical,
                ).exec()
                return
                
        self._save_form()
        self.accept()

    def _build_fields_form(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.field_inputs = {}
        
        for field_tuple in self.fields:
            key, display_label, _, _, _, _ = field_tuple
            
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(18)
            
            label = QLabel(display_label)
            label.setTextFormat(Qt.RichText)
            label.setStyleSheet("font-size: 12px; color: #2d2d2d;")
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label.setFixedWidth(280)
            label.setWordWrap(True)
            
            line_edit = QLineEdit()
            line_edit.setFixedWidth(242)
            apply_field_style(line_edit)
            line_edit.setValidator(QDoubleValidator(0.0, 99999.0, 1))
            line_edit.textEdited.connect(self._handle_user_override)
            if self.is_deck_material and key in (KEY_MATERIAL_DECK_FCK, KEY_MATERIAL_DECK_FCTM):
                line_edit.textEdited.connect(self._update_custom_material_name)
            elif (not self.is_deck_material) and key in (KEY_MATERIAL_GIRDER_FU, KEY_MATERIAL_GIRDER_FY):
                line_edit.textEdited.connect(self._update_custom_material_name)
            self.field_inputs[key] = line_edit
            
            row.addWidget(label)
            row.addWidget(line_edit)
            row.addStretch()
            layout.addLayout(row)
            
        layout.addStretch()
        return widget

    def _is_deck_material(self, material_name: str) -> bool:
        normalized = (material_name or "").strip()
        return (normalized in concrete_properies or 
                normalized.lower().startswith(CUSTOM_CONCRETE_PREFIX))

    def _defaults_for_material(self, material_name):
        if self.is_deck_material:
            grade = (material_name or "").strip()
            if self._get_concrete_from_code(grade) is None:
                grade = DEFAULT_DECK_CUSTOM_GRADE
            return self._deck_defaults(grade, self._factor_value_from_label(DEFAULT_ECM_FACTOR_LABEL))
        return self._steel_defaults(material_name)

    def _steel_defaults(self, grade):
        normalized_name = _normalize_steel_material_name(grade)
        defaults = STEEL_MATERIAL_BASE_VALUES.get(normalized_name) or {}

        if not defaults:
            # Backward fallback for custom/older naming patterns.
            grade_value = self._extract_numeric_grade(grade)
            prefix = f"E{grade_value}"
            for key, values in STEEL_MATERIAL_BASE_VALUES.items():
                if key.startswith(prefix):
                    defaults = values
                    break
        
        result = {}
        for field_tuple in steel_material_properties_values():
            key = field_tuple[0]
            if key == KEY_MATERIAL_GIRDER_DENSITY:
                result[key] = "{:.1f}".format(STEEL_WEIGHT_DENSITY)
            elif key == KEY_MATERIAL_GIRDER_FU:
                result[key] = "{:.1f}".format(defaults.get("Fu", 0.0))
            elif key == KEY_MATERIAL_GIRDER_FY:
                result[key] = "{:.1f}".format(defaults.get("Fy", 0.0))
            elif key == KEY_MATERIAL_GIRDER_E:
                result[key] = "{:.1f}".format(defaults.get("E", 0.0))
            elif key == KEY_MATERIAL_GIRDER_G:
                result[key] = "{:.1f}".format(defaults.get("G", 0.0))
            elif key == KEY_MATERIAL_GIRDER_POISSON:
                result[key] = "{:.2f}".format(defaults.get("Poisson", 0.0))
            elif key == KEY_MATERIAL_GIRDER_THERMAL:
                # DB does not include thermal expansion; use constant default for DB grades
                result[key] = "{:.1f}".format(STEEL_THERMAL_COEFF)
        return result

    def _get_concrete_from_code(self, grade):
        normalized = (grade or "").replace(" ", "").upper()
        return CONCRETE_GRADE_BASE_VALUES.get(normalized)

    def _deck_defaults(self, grade, factor_value):
        data = self._get_concrete_from_code(grade)
        if not data:
            return {
                KEY_MATERIAL_DECK_DENSITY: "{:.1f}".format(CONCRETE_WEIGHT_DENSITY),
                KEY_MATERIAL_DECK_FCK: "",
                KEY_MATERIAL_DECK_FCTM: "",
                KEY_MATERIAL_DECK_ECM: "",
                KEY_MATERIAL_DECK_THERMAL: "{:.1f}".format(STEEL_THERMAL_COEFF),
            }

        ecm = round(data["Ecm"] * factor_value, 1)
        return {
            KEY_MATERIAL_DECK_DENSITY: "{:.1f}".format(CONCRETE_WEIGHT_DENSITY),
            KEY_MATERIAL_DECK_FCK: "{:.1f}".format(data["fck"]),
            KEY_MATERIAL_DECK_FCTM: "{:.1f}".format(data["fctm"]),
            KEY_MATERIAL_DECK_ECM: "{:.1f}".format(ecm),
            KEY_MATERIAL_DECK_THERMAL: "{:.1f}".format(STEEL_THERMAL_COEFF),
        }

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
    
    def _extract_numeric_grade(self, grade, default=250):
        text = (grade or "").upper().replace(" ", "")

        # Primary path: extract the base 3-digit steel grade from codes like
        # E350B0, E350BR, E 250A, etc.
        match = re.search(r"E?(250|275|300|350|410|450|550|600|650)", text)
        if match:
            return int(match.group(1))

        digits = ''.join(ch for ch in text if ch.isdigit())
        if not digits:
            return default

        # Fallback path: if extra suffix digits exist, try first 3 digits.
        if len(digits) >= 3:
            first_three = int(digits[:3])
            if any(key.startswith(f"E{first_three}") for key in STEEL_MATERIAL_BASE_VALUES):
                return first_three

        try:
            parsed = int(digits)
            return parsed if any(key.startswith(f"E{parsed}") for key in STEEL_MATERIAL_BASE_VALUES) else default
        except ValueError:
            return default

    def _populate_fields(self):
        for label, widget in self.field_inputs.items():
            value = self.form_data["fields"].get(label, "")
            try:
                formatted_value = "{:.1f}".format(float(value))
                widget.setText(formatted_value)
            except (ValueError, TypeError):
                widget.setText(value)

    def _save_form(self):
        default_prefix = CUSTOM_CONCRETE_PREFIX if self.is_deck_material else CUSTOM_STEEL_PREFIX
        self.form_data["material"] = self.material_input.text().strip() or default_prefix
        for label, widget in self.field_inputs.items():
            self.form_data["fields"][label] = widget.text()

    def _member_prefix(self):
        """Return the member-specific material prefix, e.g. 'material.girder' or 'material.cross_bracing' or 'material.end_diaphragm' or 'material.deck'."""
        # Accept a variety of member identifiers: input keys (e.g. KEY_GIRDER),
        # schema member_type strings (e.g. "Girder"/"Deck"), or raw keys.
        try:
            m = str(self.member or "").strip()
            if not m:
                return "material.girder"
            # Deck checks
            if m == KEY_DECK_CONCRETE_GRADE_BASIC:
                return "material.deck"
            # Cross bracing checks
            if m == KEY_CROSS_BRACING:
                return "material.cross_bracing"
            # End diaphragm checks
            if m == KEY_END_DIAPHRAGM:
                return "material.end_diaphragm"
        except Exception:
            pass
        # Default to girder
        return "material.girder"

    def get_export_fields(self):
        """Return a copy of form_data['fields'] remapped to member-prefixed canonical keys.

        Internal form_data stores template keys (KEY_STEEL_*, KEY_CONCRETE_*). This method
        translates steel template keys (which are based on girder) to the correct member
        prefix (cross_bracing, end_diaphragm, or girder). Concrete keys are left as-is.
        """
        export = {}
        prefix = self._member_prefix()
        for k, v in self.form_data.get("fields", {}).items():
            if k.startswith("material.girder"):
                new_k = k.replace("material.girder", prefix)
                export[new_k] = v
            else:
                # concrete keys / already-correct keys
                export[k] = v
        return export

    def _handle_user_override(self):
        # Called on textEdited for field widgets. Auto-update related fields
        # (E, G, Poisson) while avoiding recursion using a suppression flag.
        if self._loading or self._suppress_auto_update:
            return
        sender = self.sender()
        if not sender:
            return
        # Find which key this sender corresponds to
        changed_key = None
        for k, w in self.field_inputs.items():
            if w is sender:
                changed_key = k
                break
        if not changed_key:
            return

        # Helper to parse float safely
        def _try_float(txt):
            try:
                return float(txt)
            except Exception:
                return None

        # Only apply auto-updates for steel properties (E, G, Poisson)
        if changed_key in (KEY_MATERIAL_GIRDER_E, KEY_MATERIAL_GIRDER_G, KEY_MATERIAL_GIRDER_POISSON):
            e_widget = self.field_inputs.get(KEY_MATERIAL_GIRDER_E)
            g_widget = self.field_inputs.get(KEY_MATERIAL_GIRDER_G)
            nu_widget = self.field_inputs.get(KEY_MATERIAL_GIRDER_POISSON)

            e_val = _try_float(e_widget.text() if e_widget else "")
            g_val = _try_float(g_widget.text() if g_widget else "")
            nu_val = _try_float(nu_widget.text() if nu_widget else "")

            try:
                self._suppress_auto_update = True
                # If E changed and Poisson available, update G
                if changed_key == KEY_MATERIAL_GIRDER_E and e_val is not None and nu_val is not None:
                    # G = E / (2*(1+nu))
                    g_calc = e_val / (2.0 * (1.0 + nu_val))
                    if g_widget:
                        g_widget.setText("{:.1f}".format(g_calc))

                # If G changed and Poisson available, update E
                elif changed_key == KEY_MATERIAL_GIRDER_G and g_val is not None and nu_val is not None:
                    # E = 2*G*(1+nu)
                    e_calc = 2.0 * g_val * (1.0 + nu_val)
                    if e_widget:
                        e_widget.setText("{:.1f}".format(e_calc))

                # If Poisson changed, prefer to use existing E to compute G, else use G to compute E
                elif changed_key == KEY_MATERIAL_GIRDER_POISSON and nu_val is not None:
                    if e_val is not None:
                        g_calc = e_val / (2.0 * (1.0 + nu_val))
                        if g_widget:
                            g_widget.setText("{:.1f}".format(g_calc))
                    elif g_val is not None:
                        e_calc = 2.0 * g_val * (1.0 + nu_val)
                        if e_widget:
                            e_widget.setText("{:.1f}".format(e_calc))
            finally:
                self._suppress_auto_update = False
        # End of _handle_user_override

    def _normalize_material_token(self, text):
        value = (text or "").strip()
        if not value:
            return ""
        try:
            num = float(value)
            if num.is_integer():
                return str(int(num))
            return f"{num:g}"
        except ValueError:
            return value

    def _update_custom_material_name(self, *_):
        if self.read_only:
            return
            
        if self.is_deck_material:
            fck_input = self.field_inputs.get(KEY_MATERIAL_DECK_FCK)
            fctm_input = self.field_inputs.get(KEY_MATERIAL_DECK_FCTM)
            val1 = self._normalize_material_token(fck_input.text() if fck_input else "")
            val2 = self._normalize_material_token(fctm_input.text() if fctm_input else "")
        else:
            fy_input = self.field_inputs.get(KEY_MATERIAL_GIRDER_FY)
            fu_input = self.field_inputs.get(KEY_MATERIAL_GIRDER_FU)
            val1 = self._normalize_material_token(fy_input.text() if fy_input else "")
            val2 = self._normalize_material_token(fu_input.text() if fu_input else "")

        parts = [part for part in (val1, val2) if part]
        prefix = CUSTOM_CONCRETE_PREFIX if self.is_deck_material else CUSTOM_STEEL_PREFIX
        material_name = prefix + "_".join(parts) if parts else prefix
        self.material_input.setText(material_name)

    def _set_read_only_fields(self, enabled: bool):
        for widget in self.field_inputs.values():
            widget.setReadOnly(enabled)
            widget.setEnabled(not enabled)
            if enabled:
                widget.setStyleSheet("""
                    QLineEdit {
                        padding: 1px 7px;
                        border: 1px solid #a8a8a8;
                        border-radius: 6px;
                        background-color: #f1f1f1;
                        color: #555555;
                    }
                """)

    def _load_material_info_for_view(self, material_name: str):
        name = (material_name or "").strip()
        if not name:
            name = CUSTOM_CONCRETE_PREFIX if self.is_deck_material else CUSTOM_STEEL_PREFIX

        self.form_data["material"] = name
        
        if self.custom_fields:
            self.form_data["fields"] = self.custom_fields.copy()
        else:
            if self.is_deck_material:
                factor = self._factor_value_from_label(DEFAULT_ECM_FACTOR_LABEL)
                self.form_data["fields"] = self._deck_defaults(name, factor)
            else:
                fy_value = ""
                fu_value = ""

                custom_match = re.match(
                    r"^(?:Cus_|custom_steel_)([0-9]+(?:\.[0-9]+)?)_([0-9]+(?:\.[0-9]+)?)$",
                    name,
                    re.IGNORECASE,
                )
                if custom_match:
                    fy_value = custom_match.group(1)
                    fu_value = custom_match.group(2)
                else:
                    defaults = STEEL_MATERIAL_BASE_VALUES.get(_normalize_steel_material_name(name))
                    if not defaults:
                        grade_value = self._extract_numeric_grade(name, default=None)
                        defaults = None
                        if grade_value is not None:
                            prefix = f"E{grade_value}"
                            for key, values in STEEL_MATERIAL_BASE_VALUES.items():
                                if key.startswith(prefix):
                                    defaults = values
                                    break
                    if defaults:
                        fy_value = "{:.1f}".format(defaults["Fy"])
                        fu_value = "{:.1f}".format(defaults["Fu"])

                self.form_data["fields"] = {
                    KEY_MATERIAL_GIRDER_DENSITY: "{:.1f}".format(STEEL_WEIGHT_DENSITY),
                    KEY_MATERIAL_GIRDER_FY: fy_value,
                    KEY_MATERIAL_GIRDER_FU: fu_value,
                    KEY_MATERIAL_GIRDER_E: "{:.1f}".format(defaults.get("E", 0.0)) if defaults else "",
                    KEY_MATERIAL_GIRDER_G: "{:.1f}".format(defaults.get("G", 0.0)) if defaults else "",
                    KEY_MATERIAL_GIRDER_POISSON: "{:.2f}".format(defaults.get("Poisson", 0.0)) if defaults else "",
                    KEY_MATERIAL_GIRDER_THERMAL: "{:.1f}".format(STEEL_THERMAL_COEFF),
                }

        self.material_input.setText(name)
        self._populate_fields()

    def set_member(self, member):
        _ = member

def sync_custom_materials_across_steel_members(combo_map, ensure_option_callback, material_name=None):
    steel_keys = [KEY_GIRDER, KEY_CROSS_BRACING, KEY_END_DIAPHRAGM]
    custom_materials = set()
    
    if material_name:
        if str(material_name).lower().startswith(CUSTOM_STEEL_PREFIX):
            custom_materials.add(material_name)
    else:
        for key in steel_keys:
            if key in combo_map:
                combo = combo_map[key]
                for i in range(combo.count()):
                    text = combo.itemText(i)
                    if str(text).lower().startswith(CUSTOM_STEEL_PREFIX):
                        custom_materials.add(text)
                        
    for key in steel_keys:
        if key in combo_map:
            combo = combo_map[key]
            for mat in custom_materials:
                ensure_option_callback(combo, mat)