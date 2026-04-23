from __future__ import annotations
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

# Greyed-out read-only style for combos mirroring the Output Dock selection.
_DISABLED_COMBO_STYLE = (
    "QComboBox {"
    "  background-color: #f0f0f0;"
    "  color: #888888;"
    "  border: 1px solid #cccccc;"
    "  border-radius: 5px;"
    "  padding: 1px 7px;"
    "  font-size: 11px;"
    "  min-height: 28px;"
    "}"
    "QComboBox::drop-down { border: none; width: 0px; }"
    "QComboBox::down-arrow { width: 0px; height: 0px; }"
)


class NoScrollTable(QTableWidget):
    """QTableWidget that passes wheel events up to the parent scroll area."""
    def wheelEvent(self, event):
        event.ignore()


class SteelDesignDetailsTab(QWidget):
    """
    Scrollable details tab for the Steel Design dialog.

    Displays four read-only information cards:
      - Member Info        : member ID combo, material grade, section type
      - Dimensional Details: full cross-section geometry
      - Shear Connector    : connector material, geometry, and spacing
      - Section Properties : mass, moments of area, moduli, torsion/warping

    Additionally renders a stiffener summary table and two CAD view placeholders
    (populated at runtime when a model is mounted).
    """

    def __init__(self, parent=None):
        # Initialise field dicts before super().__init__ so slots set during
        # construction can reference them safely.
        self.member_fields  = {}
        self.dim_fields     = {}
        self.shear_fields   = {}
        self.section_fields = {}

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

        # ── TOP ROW: Member Info card (left) + CAD placeholder (right) 
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.addWidget(self._build_member_section(), 1)
        top_row.addWidget(self._build_top_cad_placeholder(), 1)
        container_layout.addLayout(top_row)

        # ── BODY: Dimensional + Shear (left) | Section Properties (right) 
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

        body_row.addLayout(left_col, 1)
        body_row.addLayout(right_col, 1)
        container_layout.addLayout(body_row)

        # ── STIFFENER TABLE ───────────────────────────────────────────
        container_layout.addWidget(self._build_stiffener_section())

        # ── BOTTOM CAD placeholder ────────────────────────────────────
        container_layout.addWidget(self._build_bottom_cad_section())

        container_layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS: exact girder_details_tab pattern
    # ─────────────────────────────────────────────────────────────────────────

    def _create_card_frame(self):
        """Outer card — same as GirderDetailsTab._create_card_frame."""
        frame = QFrame()
        frame.setObjectName("girderCard")
        frame.setStyleSheet(
            "QFrame#girderCard { background-color: white; border: 1px solid #b0b0b0; border-radius: 6px; }"
        )
        return frame

    def _create_label(self, text):
        """Section title label — same as GirderDetailsTab._create_label."""
        label = QLabel(text)
        label.setStyleSheet(
            "font-size: 13px; color: #2B2B2B; font-weight: bold; background: transparent; border: none;"
        )
        label.setAutoFillBackground(False)
        return label

    def _create_small_label(self, text):
        """Row field label — supports HTML rich text for subscripts/superscripts."""
        label = QLabel(text)
        label.setTextFormat(Qt.RichText)
        label.setStyleSheet("font-size: 11px; color: #333333; background: transparent;")
        label.setAutoFillBackground(False)
        return label

    def _readonly_field(self):
        """Readonly output field — expands to fill its grid column."""
        field = QLineEdit()
        field.setReadOnly(True)
        field.setMinimumWidth(80)
        field.setMinimumHeight(28)
        field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        apply_field_style(field)
        return field

    def _make_grid(self):
        """Grid matching girder_details_tab inputs_grid spacing."""
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)
        grid.setColumnMinimumWidth(0, 230)
        grid.setColumnStretch(0, 0)   # label: fits content, doesn't stretch
        grid.setColumnStretch(1, 1)   # field: fills all remaining width
        return grid

    def _add_row(self, grid, row, text, widget):
        grid.addWidget(self._create_small_label(text), row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        grid.addWidget(widget,                         row, 1)
        return row + 1

    # ─────────────────────────────────────────────────────────────────────────
    # SECTIONS
    # ─────────────────────────────────────────────────────────────────────────

    def _build_member_section(self):
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        card_layout.addWidget(self._create_label("Member Info:"))

        grid = self._make_grid()

        self.member_combo = NoScrollComboBox()
        self.member_combo.setMinimumWidth(80)
        self.member_combo.setMinimumHeight(28)
        self.member_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.member_combo.setEnabled(False)
        self.member_combo.setStyleSheet(_DISABLED_COMBO_STYLE)
        self.member_combo.setToolTip(
            "Change the member in the Output Dock \u2014 this field mirrors that selection."
        )

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

        # Reuse the shared grid + row helper so fields behave identically
        # to Dimensional Details (left-aligned, same width, no fill-column expansion).
        grid = self._make_grid()
        section_prop_labels = [
            ("mass",  "Mass, M (Kg/m)"),
            ("area",  "Sectional Area, a (cm<sup>2</sup>)"),
            ("iz",    "2nd Moment of Area, I<sub>z</sub> (cm<sup>4</sup>)"),
            ("iv",    "2nd Moment of Area, I<sub>y</sub> (cm<sup>4</sup>)"),
            ("rz",    "Radius of Gyration, r<sub>z</sub> (cm)"),
            ("rv",    "Radius of Gyration, r<sub>y</sub> (cm)"),
            ("zz",    "Elastic Modulus, Z<sub>z</sub> (cm<sup>3</sup>)"),
            ("zv",    "Elastic Modulus, Z<sub>y</sub> (cm<sup>3</sup>)"),
            ("zuz",   "Plastic Modulus, Z<sub>pz</sub> (cm<sup>3</sup>)"),
            ("zuv",   "Plastic Modulus, Z<sub>py</sub> (cm<sup>3</sup>)"),
            ("it",    "Torsion Constant, I<sub>t</sub> (cm<sup>4</sup>)"),
            ("iw",    "Warping Constant, I<sub>w</sub> (cm<sup>6</sup>)"),
        ]
        r = 0
        for key, html_label in section_prop_labels:
            field = self._readonly_field()
            # _add_row creates labels with Qt.RichText enabled (via _create_small_label)
            # and adds the field left-aligned — consistent with Dimensional Details.
            r = self._add_row(grid, r, html_label, field)
            self.section_fields[key] = field

        card_layout.addLayout(grid)
        return card

    # ─────────────────────────────────────────────────────────────────────────
    # CAD PLACEHOLDERS
    # ─────────────────────────────────────────────────────────────────────────

    def _build_top_cad_placeholder(self):
        self.cad_placeholder = QLabel()
        self.cad_placeholder.setMinimumHeight(160)
        self.cad_placeholder.setAlignment(Qt.AlignCenter)
        self.cad_placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.cad_placeholder.setStyleSheet("""
            QLabel {
                border: 1px solid #b0b0b0;
                background-color: #F5F5F5;
                border-radius: 6px;
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
                border: 1px solid #b0b0b0;
                background-color: #F5F5F5;
                border-radius: 6px;
            }
        """)
        layout.addWidget(bottom_cad, alignment=Qt.AlignCenter)
        return card

    # ─────────────────────────────────────────────────────────────────────────
    # STIFFENER TABLE
    # ─────────────────────────────────────────────────────────────────────────

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
        # header ~30px + 3 rows * 26px + 1px bottom = 109px; frame adds 2px. Plus OS scaling safety margin
        self.stiffener_table.setMinimumHeight(120)
        self.stiffener_table.setMaximumHeight(120)

        self.stiffener_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #e0e0e0;
                color: black;
                font-size: 10px;
                border: none;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: black;
                font-weight: bold;
                border: none;
                border-right: 1px solid #b0b0b0;
                border-bottom: 1px solid #b0b0b0;
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
        table_frame.setMinimumHeight(122)
        table_frame.setMaximumHeight(122)
        card_layout.addWidget(table_frame)
        return card

    # ─────────────────────────────────────────────────────────────────────────
    # LOAD DATA (unchanged logic)
    # ─────────────────────────────────────────────────────────────────────────

    def load_data(self, cad_state: dict):
        """Populate all field widgets from a cad_state snapshot; silently ignores missing or invalid keys."""
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
