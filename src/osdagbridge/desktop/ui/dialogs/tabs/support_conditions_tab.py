from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QHBoxLayout, QSizePolicy
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import SUPPORT_CONDITIONS_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.drawings.support_conditions_cad import SupportCADWidget
from osdagbridge.desktop.ui.dialogs.tabs.drawings.support_detail_cad import SupportDetailCADWidget

class SupportConditionsTab(QWidget):

    def __init__(self, parent_dialog):
        super().__init__()
        self.setObjectName("support_tab_widget")
        self.parent_dialog = parent_dialog
        self.init_ui()

    def save_values(self):
        """Save support conditions values."""
        values = {}
        if hasattr(self.parent_dialog, "left_support_combo"):
            values["left_support"] = self.parent_dialog.left_support_combo.currentText()
        if hasattr(self.parent_dialog, "right_support_combo"):
            values["right_support"] = self.parent_dialog.right_support_combo.currentText()
        if hasattr(self.parent_dialog, "bearing_length_input"):
            values["bearing_length"] = self.parent_dialog.bearing_length_input.text()
        return values

    def validate_tab(self):
        errors = []

        if hasattr(self.parent_dialog, "bearing_length_input"):
            widget = self.parent_dialog.bearing_length_input
            text = widget.text().strip()

            if not text:
                errors.append("Bearing Length cannot be empty.")
            else:
                try:
                    value = float(text)
                    if value <= 0:
                        errors.append("Bearing Length must be greater than 0.")
                    elif value > 600:
                        errors.append("Bearing Length should not be greater than 600.")    
                except ValueError:
                    errors.append("Bearing Length must be a valid number.")

        return errors

    def init_ui(self):
        
        self.setStyleSheet("""
    

        #support_tab_widget QLabel {
            border: none;
            background: transparent;
            padding: 0;
            border-radius: 0;                
        }
        #support_tab_widget {
            background-color: #f5f5f5;
        }                   

    """)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # create a separate card for each section defined in the schema
        for section in SUPPORT_CONDITIONS_SCHEMA["sections"]:
            card = QFrame()
            card.setObjectName("support_card")
            card.setStyleSheet("""
                QFrame#support_card {
                    border: 1px solid #b2b2b2;
                    border-radius: 8px;
                    background-color: #ffffff;
                }
                /* this selector is even more specific than the app stylesheet */
                QFrame#support_card QLabel {
                    background: transparent;
                    border: none;
                    border-radius: 0;
                    padding: 0;
                }
            """)

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 16, 16, 16)
            card_layout.setSpacing(12)

            # build only the current section inside its own frame
            self.parent_dialog._build_sections_from_schema(
                card_layout,
                [section],
                "font-size: 12px; font-weight: 700; color: #2b2b2b;",
                "font-size: 11px; color: #3a3a3a;",
                160,
            )

            main_layout.addWidget(card)


        cad_card = QFrame()
        cad_card.setObjectName("support_card")
        cad_card.setStyleSheet("""
            QFrame#support_card {
                border: 1px solid #b2b2b2;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)

        cad_layout = QVBoxLayout(cad_card)
        cad_layout.setContentsMargins(10, 10, 10, 10)

        cad_row = QHBoxLayout()
        cad_row.setSpacing(12)

        self.left_cad = SupportCADWidget()
        self.left_cad.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.left_cad.setMinimumSize(300, 250)
        cad_row.addWidget(self.left_cad, 1)

        self.right_cad = SupportDetailCADWidget()
        self.right_cad.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.right_cad.setMinimumSize(150, 200)
        cad_row.addWidget(self.right_cad, 1)

        if hasattr(self.parent_dialog, "bearing_length_input"):
            self.parent_dialog.bearing_length_input.textChanged.connect(
                self.update_cad
            )

        cad_layout.addLayout(cad_row)

        main_layout.addWidget(cad_card)
        
        main_layout.addStretch()

    def reset_defaults(self):
        """Reset support conditions to default values."""
        if hasattr(self.parent_dialog, "left_support_combo"):
            self.parent_dialog.left_support_combo.setCurrentText("Pinned")

        if hasattr(self.parent_dialog, "right_support_combo"):
            self.parent_dialog.right_support_combo.setCurrentText("Roller")

        if hasattr(self.parent_dialog, "bearing_length_input"):
            self.parent_dialog.bearing_length_input.setText("400")


    def update_cad(self):
        if hasattr(self.parent_dialog, "bearing_length_input"):
            text = self.parent_dialog.bearing_length_input.text()

            try:
                value = float(text)
            except:
                value = 400

            if hasattr(self, "right_cad"):
                self.right_cad.update_params({
                    "bearing_length": value
                })   
                
    
                     
