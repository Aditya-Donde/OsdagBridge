from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QScrollArea,
    QLineEdit,
    QMessageBox,
    QGridLayout,
    QLineEdit,
    QComboBox

)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    DESIGN_OPTIONS_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.girder_details_tab import _BoundsDialog
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType

class DesignOptionsTab(QWidget):
    """
    Design Options Tab
    Schema-driven UI matching Osdag card layout
    Now includes vertical scroll support
    """

    def __init__(self, parent_dialog):
        super().__init__()
        self.parent_dialog = parent_dialog
        self._reinforcement_bounds = {
            "lower": 8.0,
            "upper": 40.0,
            "increment": 1.0
        }
        self._reinforcement_values = [8, 10, 12, 16, 20, 25, 28, 32, 36, 40]
        self.init_ui()
    
    def save_values(self):
        """Collect and return all design option values."""
        values = {}
        for field_name in dir(self.parent_dialog):
            if field_name.endswith("_combo") or field_name.endswith("_input"):
                widget = getattr(self.parent_dialog, field_name, None)
                if widget:
                    if isinstance(widget, QLineEdit):
                        values[field_name] = widget.text()
                    elif isinstance(widget, QComboBox):
                        values[field_name] = widget.currentText()

        values["reinforcement_bounds"] = self._reinforcement_bounds

        return values

    def restore_properties(self, data: dict):
        bounds = data.get("reinforcement_bounds")

        if bounds:
            self._reinforcement_bounds = {
                   "lower": float(bounds.get("lower", 8.0)),
                   "upper": float(bounds.get("upper", 40.0)),
                   "increment": float(bounds.get("increment", 1.0))
            }

            STANDARD = [8, 10, 12, 16, 20, 25, 28, 32, 36, 40]

            self._reinforcement_values = [
                s for s in STANDARD
                if self._reinforcement_bounds["lower"] <= s <= self._reinforcement_bounds["upper"]
            ] 

        combo = getattr(self.parent_dialog, "reinforcement_size_combo", None)
        if combo:
            combo.clear()
            for val in self._reinforcement_values:
                combo.addItem(f"{val} mm")    
            

    def reset_defaults(self):
        """Reset Design Options fields to schema defaults."""
        for card in DESIGN_OPTIONS_SCHEMA.get("cards", []):
            for section in card.get("sections", []):
                for field in section.get("fields", []):
                    bind_name = field.get("bind")
                    default_value = field.get("default")

                    if bind_name and default_value is not None and hasattr(self.parent_dialog, bind_name):
                        widget = getattr(self.parent_dialog, bind_name)

                        from PySide6.QtWidgets import QLineEdit, QComboBox

                        if isinstance(widget, QLineEdit):
                            widget.setText(str(default_value))
                        elif isinstance(widget, QComboBox):
                            widget.setCurrentText(str(default_value))

        self._reinforcement_bounds = {
            "lower": 8.0,
            "upper": 40.0,
            "increment": 1.0
        }

        self._reinforcement_values = [8, 10, 12, 16, 20, 25, 28, 32, 36, 40]                 

    def validate_tab(self):
        errors = []

        widgets = self.findChildren(QLineEdit)

        for widget in widgets:

            if not widget.isVisible():
                continue

            text = widget.text().strip()
            field_name = widget.objectName().replace("_", " ").title()

            if not text:
                errors.append(f"{field_name} cannot be empty.")
                continue

            validator = widget.validator()

            try:
                value = float(text)
            except ValueError:
                errors.append(f"{field_name} must be a valid number.")
                continue

            if isinstance(validator, (QDoubleValidator, QIntValidator)):
                if value < validator.bottom() or value > validator.top():
                    errors.append(
                        f"{field_name} must be between {validator.bottom()} and {validator.top()}."
                    )

        if hasattr(self.parent_dialog, "shear_stud_diameter_combo") and hasattr(self.parent_dialog, "shear_stud_spacing_input"):

            try:
                diameter = float(self.parent_dialog.shear_stud_diameter_combo.currentText())
                spacing = float(self.parent_dialog.shear_stud_spacing_input.text())

                if spacing < 4 * diameter:
                    errors.append(
                        f"Shear Stud Spacing must be at least {4*diameter:.2f} mm for diameter {diameter:.2f} mm."
                    )

            except ValueError:
                pass

        return list(set(errors))

    def init_ui(self):
        self.setStyleSheet("background-color: #f5f5f5;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

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
        content_row.setSpacing(16)

        left_card = QFrame()
        left_card.setStyleSheet("""
            QFrame {
                border: 1px solid #b2b2b2;
                border-radius: 10px;
                background-color: #ffffff;
            }
        """)

        left_card_layout = QVBoxLayout(left_card)
        left_card_layout.setContentsMargins(0, 0, 0, 0)

        content_wrapper = QWidget()
        content_wrapper.setStyleSheet("background-color: #ffffff;")

        left_layout = QVBoxLayout(content_wrapper)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(12)

        card_style = """
            QFrame {
                border: 1px solid #b2b2b2;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """

        heading_style = """
            font-size: 12px;
            font-weight: 700;
            color: #2b2b2b;
            border: none;
        """

        label_style = """
            font-size: 11px;
            color: #3a3a3a;
            border: none;
        """

        default_field_width = 150

        for card_schema in DESIGN_OPTIONS_SCHEMA.get("cards", []):

            card = QFrame()
            card.setStyleSheet(card_style)

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(10)

            card_title = card_schema.get("title")
            if card_title:
                title_lbl = QLabel(card_title)
                title_lbl.setStyleSheet(heading_style)
                card_layout.addWidget(title_lbl)

            # Reuse parent dialog schema renderer
            self.parent_dialog._build_sections_from_schema(
                card_layout,
                card_schema.get("sections", []),
                heading_style,
                label_style,
                card_schema.get("field_width", default_field_width),
            )

            left_layout.addWidget(card)

        left_layout.addStretch()
        left_card_layout.addWidget(content_wrapper)

        right_card = QFrame()
        right_card.setStyleSheet("""
            QFrame {
                border: 1px solid #9c9c9c;
                border-radius: 10px;
                background-color: #d4d4d4;
            }
        """)
        right_card.setMinimumWidth(260)

        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        desc = DESIGN_OPTIONS_SCHEMA.get("description", {})

        desc_title = QLabel(desc.get("title", "Description Box"))
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet("""
            font-size: 12px;
            font-weight: 700;
            color: #000;
            border: none;
        """)

        desc_text = QLabel(desc.get("text", " "))
        desc_text.setWordWrap(True)
        desc_text.setStyleSheet("""
            font-size: 11px;
            color: #4b4b4b;
            border: none;
        """)

        right_layout.addWidget(desc_title)
        right_layout.addWidget(desc_text)
        right_layout.addStretch()

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 2)

        page_layout.addLayout(content_row)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        if hasattr(self.parent_dialog, "reinforcement_bounds_btn"):
            self.parent_dialog.reinforcement_bounds_btn.clicked.connect(
                self._open_reinforcement_bounds
            )

        self._connect_validations()

    def _connect_validations(self):

        if hasattr(self.parent_dialog, "shear_stud_diameter") and hasattr(self.parent_dialog, "shear_stud_spacing_input"):

            self.parent_dialog.shear_stud_diameter.currentTextChanged.connect(
                self.validate_shear_stud_spacing
            ) 

    def validate_shear_stud_spacing(self):
        spacing_widget = getattr(self.parent_dialog, "shear_stud_spacing_input", None)

        if not spacing_widget:
            return

        text = spacing_widget.text().strip()

        if not text:
            return

        try:
            spacing = float(text)
        except ValueError:
            return

        validator = spacing_widget.validator()

        if validator:
            bottom = validator.bottom()
            top = validator.top()

            if spacing < bottom or spacing > top:

                from PySide6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self,
                    "Invalid Shear Stud Spacing",
                    f"Shear Stud Spacing must be between {bottom} and {top}.",
                )   

    def _open_reinforcement_bounds(self):

        dialog = BoundsDialogNoIncrement(
            "Reinforcement Size",
            self._reinforcement_bounds,
            self
        )

        if dialog.exec():
            result = dialog.result_bounds()
            if result:
                self._reinforcement_bounds = {
                    "lower": result["lower"],
                    "upper": result["upper"],
                    "increment": 1.0
                }

                STANDARD = [8, 10, 12, 16, 20, 25, 28, 32, 36, 40]

                self._reinforcement_values = [
                    s for s in STANDARD
                    if result["lower"] <= s <= result["upper"]
                ]

                combo = getattr(self.parent_dialog, "reinforcement_size_combo", None)
                if combo:
                    combo.clear()
                    for val in self._reinforcement_values:
                        combo.addItem(f"{val} mm")

        


class BoundsDialogNoIncrement(_BoundsDialog):
    def __init__(self, title, bounds, parent=None):
        super().__init__(title, bounds, parent)

        self.increment_input.hide()

        layout = self.findChild(QGridLayout)
        if layout:
            item = layout.itemAtPosition(2, 0)
            if item and item.widget():
                item.widget().hide()

    def _on_accept(self):
        errors = []

        lower = self._parse_positive(self.lower_input.text())
        upper = self._parse_positive(self.upper_input.text())

        if lower is None or upper is None:
            errors.append("Please enter valid numeric values.")

        else:
            if lower < 8:
                errors.append("Lower bound cannot be less than 8 mm.")

            if upper > 40:
                errors.append("Upper bound cannot be greater than 40 mm.")

            if upper <= lower:
                errors.append("Upper bound must be greater than lower bound.")

        if errors:
            message = "\n\n".join(f"• {err}" for err in errors)

            CustomMessageBox(
                title="Validation Errors",
                text=message,
                buttons=["OK"],
                dialogType=MessageBoxType.Warning,
            ).exec()
            return

        self._result = {
            "lower": float(lower),
            "upper": float(upper),
            "increment": 1.0
        }

        self.accept()
   

               

