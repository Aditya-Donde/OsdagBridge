from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFrame,
    QLabel,
    QScrollArea,
    QHBoxLayout,
    QGroupBox,
    QCheckBox,
)
from PySide6.QtCore import Qt

from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    DESIGN_OPTIONS_CONT_SCHEMA,
)


class DesignOptionsContTab(QWidget):
    """
    Design Options (Cont.) Tab
    Includes scroll area and limit state checkbox groups
    """

    def __init__(self, parent_dialog):
        super().__init__()
        self.parent_dialog = parent_dialog
        self.init_ui()
    
    def save_values(self):
        """Collect and return all design option (cont.) values."""
        values = {}
        for field_name in dir(self.parent_dialog):
            if field_name.endswith("_combo") or field_name.endswith("_input"):
                widget = getattr(self.parent_dialog, field_name, None)
                if widget:
                    from PySide6.QtWidgets import QLineEdit, QComboBox
                    if isinstance(widget, QLineEdit):
                        values[field_name] = widget.text()
                    elif isinstance(widget, QComboBox):
                        values[field_name] = widget.currentText()
        return values

    def init_ui(self):
        #Changed Bg color
        self.setStyleSheet("background-color: #ffffff;")

        #Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #ffffff;")

        main_layout = QVBoxLayout(scroll_content)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

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

        field_width = 150

        for section in DESIGN_OPTIONS_CONT_SCHEMA.get("sections", []):

            # -------- LIMIT STATES (Checkbox Groups) --------
            if section.get("checkbox_groups"):

                title_lbl = QLabel(section.get("title", ""))
                title_lbl.setStyleSheet("""
                    font-size: 12px;
                    font-weight: 700;
                    color: #000000;
                    margin-left: 4px;
                """)
                main_layout.addWidget(title_lbl, alignment=Qt.AlignLeft)

                groups_layout = QHBoxLayout()
                groups_layout.setSpacing(20)

                for group in section.get("checkbox_groups", []):
                    box = QGroupBox(group.get("title", ""))
                    box.setStyleSheet("""
                        QGroupBox {
                            border: 1px solid #000000;
                            border-radius: 8px;
                            margin-top: 12px;
                            padding: 8px;
                            background-color: #ffffff;
                        }
                        QGroupBox::title {
                            subcontrol-origin: margin;
                            subcontrol-position: top left;
                            left: 12px;
                            padding: 0 6px;
                            background-color: #ffffff;
                            font-weight: 600;
                            font-size: 11px;
                            color: #000000;
                        }
                    """)

                    vbox = QVBoxLayout(box)
                    vbox.setContentsMargins(16, 20, 16, 16)
                    vbox.setSpacing(8)

                    checkboxes = []
                    for text in group.get("items", []):
                        cb = QCheckBox(text)
                        cb.setStyleSheet("""
                            QCheckBox {
                                font-size: 11px;
                                color: #333333;
                                spacing: 6px;
                            }
                        """)
                        vbox.addWidget(cb)
                        checkboxes.append(cb)
                    vbox.addStretch()  
                    # bind to parent dialog
                    setattr(self.parent_dialog, group.get("bind"), checkboxes)

                    groups_layout.addWidget(box)

                main_layout.addLayout(groups_layout)
                continue

            # -------- NORMAL CARD SECTIONS --------
            card = QFrame()
            card.setStyleSheet(card_style)

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 16, 16, 16)
            card_layout.setSpacing(10)

            self.parent_dialog._build_sections_from_schema(
                card_layout,
                [section],
                heading_style,
                label_style,
                field_width,
            )

            main_layout.addWidget(card)

        main_layout.addStretch()

        scroll.setWidget(scroll_content)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)