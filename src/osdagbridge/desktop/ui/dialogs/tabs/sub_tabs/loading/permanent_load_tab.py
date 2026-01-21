from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame

PERMANENT_LOAD_DEFAULTS = {
    "include_self_weight": "Yes",
    "self_weight_factor": "1.00",
    "include_deck_weight": "Yes",
    "include_wearing_course": "Yes",
    "include_crash_barrier": "Yes",
    "include_median": "Yes",
    "include_railing": "Yes",
}

# Match Seismic Load tab dimensions
LABEL_MIN_WIDTH = 220
FIELD_WIDTH = 180
FIELD_HEIGHT = 28


class PermanentLoadTab(QWidget):
    """Permanent Load tab content extracted from LoadingTab."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self._build_ui()

    def _build_ui(self):
        owner = self.owner

        self.setStyleSheet("background-color: #f5f5f5;")
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(12)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(16)

        # ============ LEFT CARD ============
        left_card = owner._create_card()
        left_card.setStyleSheet(
            "QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }"
        )
        left_card_layout = QVBoxLayout(left_card)
        left_card_layout.setContentsMargins(0, 0, 0, 0)
        left_card_layout.setSpacing(0)

        content_wrapper = QWidget()
        content_wrapper.setStyleSheet("background-color: #ffffff;")
        left_layout = QVBoxLayout(content_wrapper)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(12)


        label_style = "font-size: 11px; font-weight: 600; color: #3a3a3a; background: transparent; border: none;"

        # ============ DEAD LOAD BOX ============
        dead_load_box = QFrame()
        dead_load_box.setStyleSheet("""
            QFrame {
                border: 1px solid #9c9c9c;
                border-radius: 6px;
                background-color: #ffffff;
                padding: 0px;
            }
        """)
        dead_load_box_layout = QVBoxLayout(dead_load_box)
        dead_load_box_layout.setContentsMargins(12, 12, 12, 12)
        dead_load_box_layout.setSpacing(14)

        # Dead Load section title
        dl_title = QLabel("Dead Load (DL):")
        dl_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
        dead_load_box_layout.addWidget(dl_title)

        # Include Member Self Weight
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        lbl1 = QLabel("Include Member Self Weight:")
        lbl1.setStyleSheet(label_style)
        lbl1.setMinimumWidth(LABEL_MIN_WIDTH)
        self.include_self_weight_combo = owner._create_yes_no_combo()
        self.include_self_weight_combo.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
        row1.addWidget(lbl1)
        row1.addWidget(self.include_self_weight_combo)
        row1.addStretch()
        dead_load_box_layout.addLayout(row1)

        # Self-weight factor
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        lbl2 = QLabel("Self-weight factor:")
        lbl2.setStyleSheet(label_style)
        lbl2.setMinimumWidth(LABEL_MIN_WIDTH)
        self.self_weight_factor_input = owner._create_line_edit()
        self.self_weight_factor_input.setText(PERMANENT_LOAD_DEFAULTS["self_weight_factor"])
        self.self_weight_factor_input.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
        row2.addWidget(lbl2)
        row2.addWidget(self.self_weight_factor_input)
        row2.addStretch()
        dead_load_box_layout.addLayout(row2)

        # Include Concrete Deck Weight
        row3 = QHBoxLayout()
        row3.setSpacing(10)
        lbl3 = QLabel("Include Concrete Deck Weight:")
        lbl3.setStyleSheet(label_style)
        lbl3.setMinimumWidth(LABEL_MIN_WIDTH)
        self.include_deck_weight_combo = owner._create_yes_no_combo()
        self.include_deck_weight_combo.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
        row3.addWidget(lbl3)
        row3.addWidget(self.include_deck_weight_combo)
        row3.addStretch()
        dead_load_box_layout.addLayout(row3)

        left_layout.addWidget(dead_load_box)

        # ============ DEAD LOAD FOR SURFACING BOX ============
        surfacing_box = QFrame()
        surfacing_box.setStyleSheet("""
            QFrame {
                border: 1px solid #9c9c9c;
                border-radius: 6px;
                background-color: #ffffff;
                padding: 0px;
            }
        """)
        surfacing_box_layout = QVBoxLayout(surfacing_box)
        surfacing_box_layout.setContentsMargins(12, 12, 12, 12)
        surfacing_box_layout.setSpacing(14)

        # Surfacing section title
        surf_title = QLabel("Dead Load for Surfacing (DW):")
        surf_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
        surfacing_box_layout.addWidget(surf_title)

        # Include Load from Wearing Course
        row4 = QHBoxLayout()
        row4.setSpacing(10)
        lbl4 = QLabel("Include Load from Wearing Course:")
        lbl4.setStyleSheet(label_style)
        lbl4.setMinimumWidth(LABEL_MIN_WIDTH)
        self.include_wearing_course_combo = owner._create_yes_no_combo()
        self.include_wearing_course_combo.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
        row4.addWidget(lbl4)
        row4.addWidget(self.include_wearing_course_combo)
        row4.addStretch()
        surfacing_box_layout.addLayout(row4)

        left_layout.addWidget(surfacing_box)

        # ============ SUPER-IMPOSED DEAD LOAD BOX ============
        sidl_box = QFrame()
        sidl_box.setStyleSheet("""
            QFrame {
                border: 1px solid #9c9c9c;
                border-radius: 6px;
                background-color: #ffffff;
                padding: 0px;
            }
        """)
        sidl_box_layout = QVBoxLayout(sidl_box)
        sidl_box_layout.setContentsMargins(12, 12, 12, 12)
        sidl_box_layout.setSpacing(14)

        # SIDL section title
        sidl_title = QLabel("Super-Imposed Dead Load (SIDL):")
        sidl_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
        sidl_box_layout.addWidget(sidl_title)

        # Include Load from Crash Barrier
        row5 = QHBoxLayout()
        row5.setSpacing(10)
        lbl5 = QLabel("Include Load from Crash Barrier:")
        lbl5.setStyleSheet(label_style)
        lbl5.setMinimumWidth(LABEL_MIN_WIDTH)
        self.include_crash_barrier_combo = owner._create_yes_no_combo()
        self.include_crash_barrier_combo.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
        row5.addWidget(lbl5)
        row5.addWidget(self.include_crash_barrier_combo)
        row5.addStretch()
        sidl_box_layout.addLayout(row5)

        # Include Load from Median
        row6 = QHBoxLayout()
        row6.setSpacing(10)
        lbl6 = QLabel("Include Load from Median:")
        lbl6.setStyleSheet(label_style)
        lbl6.setMinimumWidth(LABEL_MIN_WIDTH)
        self.include_median_combo = owner._create_yes_no_combo()
        self.include_median_combo.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
        row6.addWidget(lbl6)
        row6.addWidget(self.include_median_combo)
        row6.addStretch()
        sidl_box_layout.addLayout(row6)

        # Include Load from Railing
        row7 = QHBoxLayout()
        row7.setSpacing(10)
        lbl7 = QLabel("Include Load from Railing:")
        lbl7.setStyleSheet(label_style)
        lbl7.setMinimumWidth(LABEL_MIN_WIDTH)
        self.include_railing_combo = owner._create_yes_no_combo()
        self.include_railing_combo.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
        row7.addWidget(lbl7)
        row7.addWidget(self.include_railing_combo)
        row7.addStretch()
        sidl_box_layout.addLayout(row7)

        left_layout.addWidget(sidl_box)

        left_layout.addStretch()
        left_card_layout.addWidget(content_wrapper)

        # ============ RIGHT CARD - Description Box ============
        right_card = owner._create_card()
        right_card.setStyleSheet(
            "QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #d4d4d4; }"
        )
        right_card.setMinimumWidth(260)
        right_card.setMinimumHeight(420)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        desc_title = QLabel("Description Box")
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #000000; background: transparent; border: none;")
        right_layout.addWidget(desc_title)

        desc_text = QLabel(
            "Configure permanent loads including dead loads, wearing course, and super-imposed dead loads.\n\n"
            "Self-weight is automatically calculated based on member properties.\n\n"
            "Include appropriate factors for specific load components."
        )
        desc_text.setWordWrap(True)
        desc_text.setStyleSheet("font-size: 11px; color: #4b4b4b; background: transparent; border: none;")
        right_layout.addWidget(desc_text)
        right_layout.addStretch()

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 2)

        page_layout.addLayout(content_row)

    def update_dependency_states(self, has_median: bool, has_footpath: bool):
        """
        Enable/disable load options based on basic inputs
        """
        # Median dependency
        self.include_median_combo.setEnabled(has_median)
        if not has_median:
            self.include_median_combo.setCurrentText("No")

        # Railing dependency
        self.include_railing_combo.setEnabled(has_footpath)
        if not has_footpath:
            self.include_railing_combo.setCurrentText("No")
    
    def reset_defaults(self):
        """Reset Permanent Load inputs to default values"""
        self.include_self_weight_combo.setCurrentText(
            PERMANENT_LOAD_DEFAULTS["include_self_weight"]
        )
        self.self_weight_factor_input.setText(
            PERMANENT_LOAD_DEFAULTS["self_weight_factor"]
        )
        self.include_deck_weight_combo.setCurrentText(
            PERMANENT_LOAD_DEFAULTS["include_deck_weight"]
        )
        self.include_wearing_course_combo.setCurrentText(
            PERMANENT_LOAD_DEFAULTS["include_wearing_course"]
        )
        self.include_crash_barrier_combo.setCurrentText(
            PERMANENT_LOAD_DEFAULTS["include_crash_barrier"]
        )
        self.include_median_combo.setCurrentText(
            PERMANENT_LOAD_DEFAULTS["include_median"]
        )
        self.include_railing_combo.setCurrentText(
            PERMANENT_LOAD_DEFAULTS["include_railing"]
        )