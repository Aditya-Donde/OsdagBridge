from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import SUPPORT_CONDITIONS_SCHEMA


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
    
    def reset_defaults(self):
        """Reset to default values."""
        if hasattr(self.parent_dialog, "left_support_combo"):
            self.parent_dialog.left_support_combo.setCurrentText("Pinned")
        if hasattr(self.parent_dialog, "right_support_combo"):
            self.parent_dialog.right_support_combo.setCurrentText("Roller")
        if hasattr(self.parent_dialog, "bearing_length_input"):
            self.parent_dialog.bearing_length_input.setText("400")

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

        
        self.parent_dialog._build_sections_from_schema(
            card_layout,
            SUPPORT_CONDITIONS_SCHEMA["sections"],
            "font-size: 12px; font-weight: 700; color: #2b2b2b;",
            "font-size: 11px; color: #3a3a3a;",
            160,
        )

        main_layout.addWidget(card)
        main_layout.addStretch()