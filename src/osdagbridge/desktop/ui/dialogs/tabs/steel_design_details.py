from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QFrame,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PySide6.QtCore import Qt

from osdagbridge.desktop.ui.docks.output_dock import (
    NoScrollComboBox,
)

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style


from osdagbridge.desktop.ui.utils.styled_scroll_area import StyledScrollArea


class NoScrollTable(QTableWidget):
    """QTableWidget that passes wheel events up to the parent scroll area."""
    def wheelEvent(self, event):
        event.ignore()


class SteelDesignDetailsTab(QWidget):

    def __init__(self, parent=None):
        self.member_fields    = {}
        self.dim_fields       = {}
        self.shear_fields     = {}
        self.section_fields   = {}
        self.stiffener_fields = {}

        super().__init__(parent)

        self.setStyleSheet("background-color: white;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = StyledScrollArea()

        container = QWidget()
        container.setStyleSheet("background-color: white;")

        # Same outer margins/spacing as girder_details_tab content_layout
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(12)

        # ── TOP ROW: Member Info card (left) + CAD placeholder (right) ───────
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.addWidget(self._build_member_section(), 2)
        top_row.addWidget(self._build_top_cad_placeholder(), 0)
        container_layout.addLayout(top_row)

        # ── BODY: Dimensional + Shear (left) | Section Properties (right) ────
        body_row = QHBoxLayout()
        body_row.setSpacing(12)
        body_row.setContentsMargins(0, 0, 0, 0)

        left_col = QVBoxLayout()
        left_col.setSpacing(12)
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.addWidget(self._build_dimensional_section())
        left_col.addWidget(self._build_shear_section())
        left_col.addStretch()

        right_col = QVBoxLayout()
        right_col.setSpacing(12)
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.addWidget(self._build_section_properties_section())
        right_col.addStretch()

        body_row.addLayout(left_col, 2)
        body_row.addLayout(right_col, 1)
        container_layout.addLayout(body_row)

        # ── STIFFENER TABLE ───────────────────────────────────────────────────
        container_layout.addWidget(self._build_stiffener_section())

        # ── BOTTOM CAD placeholder ────────────────────────────────────────────
        container_layout.addWidget(self._build_bottom_cad_section())

        container_layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

    # ── HELPERS: exact girder_details_tab pattern ─────────────────────────────

    def _create_card_frame(self):
        """Outer card — same as GirderDetailsTab._create_card_frame."""
        frame = QFrame()
        frame.setObjectName("girderCard")
        frame.setStyleSheet(
            "QFrame#girderCard { background-color: white; border: 1px solid #cfcfcf; border-radius: 10px; }"
        )
        return frame

    def _create_label(self, text):
        """Section title label — same as GirderDetailsTab._create_label."""
        label = QLabel(text)
        label.setStyleSheet(
            "font-size: 12px; color: #2f2f2f; font-weight: 600; background: transparent;"
        )
        label.setAutoFillBackground(False)
        return label

    def _create_small_label(self, text):
        """Row field label — same as GirderDetailsTab._create_small_label."""
        label = QLabel(text)
        label.setStyleSheet("font-size: 10px; color: #5a5a5a; background: transparent;")
        label.setAutoFillBackground(False)
        return label

    def _readonly_field(self):
        """Readonly output field matching inner_box min-height."""
        field = QLineEdit()
        field.setReadOnly(True)
        field.setFixedWidth(150)
        field.setMinimumHeight(28)
        field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        apply_field_style(field)
        return field

    def _make_grid(self):
        """Grid matching girder_details_tab inputs_grid spacing."""
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)
        grid.setColumnMinimumWidth(0, 180)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 1)
        return grid

    def _add_row(self, grid, row, text, widget):
        grid.addWidget(self._create_small_label(text), row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        grid.addWidget(widget,                         row, 1, Qt.AlignLeft | Qt.AlignVCenter)
        return row + 1

    # ── SECTIONS ──────────────────────────────────────────────────────────────

    def _build_member_section(self):
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        card_layout.addWidget(self._create_label("Member Info:"))

        grid = self._make_grid()

        self.member_combo = NoScrollComboBox()
        apply_field_style(self.member_combo)
        self.member_combo.setFixedWidth(150)
        self.member_combo.setMinimumHeight(28)
        self.member_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.grade_field = self._readonly_field()
        self.type_field  = self._readonly_field()

        r = 0
        r = self._add_row(grid, r, "Member ID:",         self.member_combo)
        r = self._add_row(grid, r, "Grade of Material:", self.grade_field)
        r = self._add_row(grid, r, "Type:",              self.type_field)

        card_layout.addLayout(grid)

        self.member_fields["member_id"]         = self.member_combo
        self.member_fields["grade_of_material"] = self.grade_field
        self.member_fields["section_type"]      = self.type_field

        return card

    def _build_dimensional_section(self):
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        card_layout.addWidget(self._create_label("Dimensional Details:"))

        grid = self._make_grid()
        labels = {
            "section_designation":     "Section Designation",
            "section_class":           "Section Class",
            "total_depth":             "Total Depth (mm)",
            "web_thickness":           "Web Thickness (mm)",
            "top_flange_width":        "Top Flange Width (mm)",
            "top_flange_thickness":    "Top Flange Thickness (mm)",
            "bottom_flange_width":     "Bottom Flange Width (mm)",
            "bottom_flange_thickness": "Bottom Flange Thickness (mm)",
            "torsional_restraint":     "Torsional Restraint",
            "warping_restraint":       "Warping Restraint",
            "web_type":                "Web Type",
            "effective_slab_width":    "Effective Width of Slab (mm)",
        }
        r = 0
        for key, text in labels.items():
            field = self._readonly_field()
            r = self._add_row(grid, r, text, field)
            self.dim_fields[key] = field

        card_layout.addLayout(grid)
        return card

    def _build_shear_section(self):
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        card_layout.addWidget(self._create_label("Shear Connector Details:"))

        grid = self._make_grid()
        labels = {
            "shear_material":             "Material",
            "shear_diameter":             "Diameter (mm)",
            "shear_height":               "Height (mm)",
            "shear_transverse_spacing":   "Transverse Spacing (mm)",
            "shear_studs_per_section":    "No. of Shear Studs per Section",
            "shear_longitudinal_spacing": "Average Longitudinal Spacing (mm)",
        }
        r = 0
        for key, text in labels.items():
            field = self._readonly_field()
            r = self._add_row(grid, r, text, field)
            self.shear_fields[key] = field

        card_layout.addLayout(grid)
        return card

    def _build_section_properties_section(self):
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        card_layout.addWidget(self._create_label("Section Properties:"))

        grid = self._make_grid()
        labels = {
            "mass":  "Mass, M (Kg/m)",
            "area":  "Sectional Area (cm\u00b2)",
            "iz":    "2nd Moment of Area, Iz (cm\u2074)",
            "iv":    "2nd Moment of Area, Iv (cm\u2074)",
            "rz":    "Radius of Gyration, rz (cm)",
            "rv":    "Radius of Gyration, rv (cm)",
            "zz":    "Elastic Modulus, Zz (cm\u00b3)",
            "zv":    "Elastic Modulus, Zv (cm\u00b3)",
            "zuz":   "Plastic Modulus, Zuz (cm\u00b3)",
            "zuv":   "Plastic Modulus, Zuv (cm\u00b3)",
            "it":    "Torsion Constant, It (cm\u2074)",
            "iw":    "Warping Constant, Iw (cm\u2076)",
        }
        r = 0
        for key, text in labels.items():
            field = self._readonly_field()
            r = self._add_row(grid, r, text, field)
            self.section_fields[key] = field

        card_layout.addLayout(grid)
        return card

    # ── CAD PLACEHOLDERS ──────────────────────────────────────────────────────

    def _build_top_cad_placeholder(self):
        self.cad_placeholder = QLabel()
        self.cad_placeholder.setFixedSize(385, 160)
        self.cad_placeholder.setAlignment(Qt.AlignCenter)
        self.cad_placeholder.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.cad_placeholder.setStyleSheet("""
            QLabel {
                border: 1px solid #cfcfcf;
                background-color: #F5F5F5;
                border-radius: 10px;
            }
        """)
        return self.cad_placeholder

    def _build_bottom_cad_section(self):
        card = self._create_card_frame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)

        bottom_cad = QLabel()
        bottom_cad.setFixedSize(400, 200)
        bottom_cad.setAlignment(Qt.AlignCenter)
        bottom_cad.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        bottom_cad.setStyleSheet("""
            QLabel {
                border: 1px solid #cfcfcf;
                background-color: #F5F5F5;
                border-radius: 6px;
            }
        """)
        layout.addWidget(bottom_cad, alignment=Qt.AlignCenter)
        return card

    # ── STIFFENER TABLE ───────────────────────────────────────────────────────

    def _build_stiffener_section(self):
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)

        card_layout.addWidget(self._create_label("Stiffener Details:"))

        # ── Wrap table in a QFrame so the border is drawn by the frame,
        # not QAbstractScrollArea's viewport (which clips the left edge).
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #b0b0b0;
                border-radius: 0px;
                background: white;
            }
        """)
        table_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        table_frame_layout = QVBoxLayout(table_frame)
        # right margin -1 pulls table 1px under the frame border, hiding the last gridline
        table_frame_layout.setContentsMargins(0, 0, 0, 0)
        table_frame_layout.setSpacing(0)

        self.stiffener_table = NoScrollTable()
        self.stiffener_table.setRowCount(3)
        self.stiffener_table.setColumnCount(5)
        self.stiffener_table.setHorizontalHeaderLabels([
            "Type", "Grade of Material", "Thickness (mm)", "Width (mm)", "Spacing (mm)"
        ])

        for row, name in enumerate(["Intermediate", "Longitudinal", "Bearing"]):
            item = QTableWidgetItem(name)
            item.setFlags(Qt.ItemIsEnabled)
            self.stiffener_table.setItem(row, 0, item)
            for col in range(1, 5):
                empty = QTableWidgetItem("")
                empty.setFlags(Qt.ItemIsEnabled)
                self.stiffener_table.setItem(row, col, empty)

        self.stiffener_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stiffener_table.verticalHeader().setVisible(False)
        self.stiffener_table.verticalHeader().setDefaultSectionSize(26)
        self.stiffener_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.stiffener_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.stiffener_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.stiffener_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Use sizeHint-based height after headers/rows are configured
        # header ~30px + 3 rows * 26px + 1px bottom = 109px; frame adds 2px
        self.stiffener_table.setMinimumHeight(109)
        self.stiffener_table.setMaximumHeight(109)

        self.stiffener_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #cfcfcf;
                color: black;
                font-size: 10px;
                border: none;
            }
            QHeaderView::section {
                background-color: #EAEAEA;
                color: black;
                font-weight: bold;
                border: none;
                border-right: 1px solid #cfcfcf;
                border-bottom: 1px solid #cfcfcf;
                padding: 3px;
                font-size: 10px;
            }
            QHeaderView::section:last {
                border-right: none;
            }
            QTableWidget::item {
                color: black;
            }
        """)

        # Pull right edge of viewport 1px left so last gridline sits under frame border
        self.stiffener_table.setViewportMargins(0, 0, -1, 0)
        table_frame_layout.addWidget(self.stiffener_table)
        table_frame.setMinimumHeight(111)
        table_frame.setMaximumHeight(111)
        card_layout.addWidget(table_frame)
        return card

    # ── LOAD DATA (unchanged logic) ───────────────────────────────────────────

    def load_data(self, cad_state: dict):
        if not cad_state:
            return

        for key, field in self.member_fields.items():
            value = cad_state.get(key, "")
            if isinstance(field, NoScrollComboBox):
                field.clear()
                field.addItem(str(value))
            else:
                field.setText(str(value))

        for key, field in self.dim_fields.items():
            field.setText(str(cad_state.get(key, "")))

        for key, field in self.shear_fields.items():
            field.setText(str(cad_state.get(key, "")))

        for key, field in self.section_fields.items():
            field.setText(str(cad_state.get(key, "")))

        if hasattr(self, "stiffener_table"):
            stiffener_map = {0: "intermediate", 1: "longitudinal", 2: "bearing"}
            for row, prefix in stiffener_map.items():
                grade     = cad_state.get(f"stiff_{prefix}_grade",     "")
                thickness = cad_state.get(f"stiff_{prefix}_thickness", "")
                width     = cad_state.get(f"stiff_{prefix}_width",     "")
                spacing   = cad_state.get(f"stiff_{prefix}_spacing",   "")

                self.stiffener_table.setItem(row, 1, QTableWidgetItem(str(grade)))
                self.stiffener_table.setItem(row, 2, QTableWidgetItem(str(thickness)))
                self.stiffener_table.setItem(row, 3, QTableWidgetItem(str(width)))
                self.stiffener_table.setItem(row, 4, QTableWidgetItem(str(spacing)))