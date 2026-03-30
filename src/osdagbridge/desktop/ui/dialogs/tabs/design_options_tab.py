from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
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
                   "increment": float(bounds.get("increment", 1.0))  # safe default
            }

            STANDARD = [8, 10, 12, 16, 20, 25, 28, 32, 36, 40]

            self._reinforcement_values = [
                s for s in STANDARD
                if self._reinforcement_bounds["lower"] <= s <= self._reinforcement_bounds["upper"]
            ] 
            

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
        # Changed Bg color
        self.setStyleSheet("background-color: #f5f5f5;")

        # Scroll Area Setup
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f5f5f5;
            }
        """)

        # Scroll content container
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #ffffff;")

        main_layout = QVBoxLayout(scroll_content)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

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
            background: transparent;
            border: none;
        """

        label_style = """
            font-size: 11px;
            color: #3a3a3a;
            background: transparent;
            border: none;
        """

        default_field_width = 150

       
        # Built Cards from Schema 
        for card_schema in DESIGN_OPTIONS_SCHEMA.get("cards", []):

            card = QFrame()
            card.setStyleSheet(card_style)

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(10)

            card_title = card_schema.get("title")
            if card_title:
                title_lbl = QLabel(f"{card_title}")
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

            main_layout.addWidget(card)

        # Push everything up
        main_layout.addStretch()

        # Final scroll wiring
        scroll.setWidget(scroll_content)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

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
                result.pop("increment", None)
                self._reinforcement_bounds = result

                STANDARD = [8, 10, 12, 16, 20, 25, 28, 32, 36, 40]

                self._reinforcement_values = [
                    s for s in STANDARD
                    if result["lower"] <= s <= result["upper"]
                ]

                print("Reinforcement:", self._reinforcement_values) 

        


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
        lower = self._parse_positive(self.lower_input.text())
        upper = self._parse_positive(self.upper_input.text())

        if lower is None or upper is None:
            QMessageBox.warning(self, "Invalid Bounds", "Please enter valid numbers.")
            return

        if upper <= lower:
            QMessageBox.warning(self, "Invalid Bounds", "Upper must be greater than lower.")
            return

        self._result = {
            "lower": float(lower),
            "upper": float(upper),
            "increment": None
        }
        self.accept()
   

               

