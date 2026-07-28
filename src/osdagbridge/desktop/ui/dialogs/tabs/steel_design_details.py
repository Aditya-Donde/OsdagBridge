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
from osdagbridge.desktop.ui.dialogs.additional_input.drawings.rolled_section_preview import RolledSectionPreview
from osdagbridge.desktop.ui.dialogs.additional_input.drawings.stiffener_cad_preview import (
    StiffenerCadPreviewWidget,
)
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    STEEL_DESIGN_DETAILS_SCHEMA,
)
from osdagbridge.core.utils.common import (
    KEY_SD_GRADE_OF_MATERIAL,
    KEY_SD_SECTION_TYPE,
    KEY_SD_SECTION_DESIGNATION,
    KEY_SD_SECTION_CLASS,
    KEY_SD_TOTAL_DEPTH,
    KEY_SD_WEB_THICKNESS,
    KEY_SD_TOP_FLANGE_WIDTH,
    KEY_SD_TOP_FLANGE_THICKNESS,
    KEY_SD_BOTTOM_FLANGE_WIDTH,
    KEY_SD_BOTTOM_FLANGE_THICKNESS,
    KEY_SD_TORSIONAL_RESTRAINT,
    KEY_SD_WARPING_RESTRAINT,
    KEY_SD_WEB_TYPE,
    KEY_SD_EFFECTIVE_SLAB_WIDTH,
    KEY_SD_SHEAR_YIELD_STRENGTH,
    KEY_SD_SHEAR_ULTIMATE_STRENGTH,
    KEY_SD_SHEAR_DIAMETER,
    KEY_SD_SHEAR_HEIGHT,
    KEY_SD_SHEAR_TRANSVERSE_SPACING,
    KEY_SD_SHEAR_STUDS_PER_SECTION,
    KEY_SD_SHEAR_LONGITUDINAL_SPACING,
    KEY_MP_GIRDER_MASS,
    KEY_MP_GIRDER_SECTIONAL_AREA,
    KEY_MP_GIRDER_SECTIONAL_IZ,
    KEY_MP_GIRDER_SECTIONAL_IY,
    KEY_MP_GIRDER_RADIUS_GYRATION_Z,
    KEY_MP_GIRDER_RADIUS_GYRATION_Y,
    KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ,
    KEY_MP_GIRDER_ELASTIC_MODULUS_ZY,
    KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ,
    KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY,
    KEY_MP_GIRDER_TORSION_CONSTANT_IT,
    KEY_MP_GIRDER_WARPING_CONSTANT_IW,
    KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
    KEY_MP_STIFFENER_BEARING_THICKNESS,
    KEY_MP_STIFFENER_BEARING_OUTSTAND,
    KEY_MP_STIFFENER_SPACING,
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_LONGITUDINAL,
    KEY_MP_STIFFENER_LONGITUDINAL_THICKNESS,
)

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

    Displays read-only information cards:
      - Dimensional Details: material grade, section type, and full cross-section geometry
      - Shear Connector    : connector material, geometry, and spacing
      - Section Properties : mass, moments of area, moduli, torsion/warping

    Additionally renders a stiffener summary table and two CAD view placeholders
    (populated at runtime when a model is mounted).
    """

    def __init__(self, parent=None):
        # Initialise field dicts before super().__init__ so slots set during
        # construction can reference them safely.
        self._field_groups = {
            "member": {},
            "dim": {},
            "shear": {},
            "section": {},
        }
        self._card_schemas = STEEL_DESIGN_DETAILS_SCHEMA.get("cards", [])
        self._stiffener_schema = STEEL_DESIGN_DETAILS_SCHEMA.get("stiffener", {})
        self._cad_schema = STEEL_DESIGN_DETAILS_SCHEMA.get("cad", {})

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

        # ── TOP ROW ───────────────────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        top_row.setContentsMargins(0, 0, 0, 0)
        
        top_left_col = QVBoxLayout()
        top_left_col.setSpacing(12)
        top_left_col.setContentsMargins(0, 0, 0, 0)
        top_left_col.addWidget(self._build_dimensional_section())
        top_left_col.addWidget(self._build_shear_section())
        top_left_col.addStretch()
        
        top_right_col = QVBoxLayout()
        top_right_col.setSpacing(12)
        top_right_col.setContentsMargins(0, 0, 0, 0)
        top_right_col.addWidget(self._build_top_cad_placeholder())
        top_right_col.addWidget(self._build_section_properties_section())
        top_right_col.addStretch()
        
        top_row.addLayout(top_left_col, 1)
        top_row.addLayout(top_right_col, 1)
        container_layout.addLayout(top_row)

        # ── BOTTOM ROW ────────────────────────────────────────────────
        container_layout.addWidget(self._build_stiffener_section())

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

    def _get_card_schema(self, title):
        for card in self._card_schemas:
            if card.get("title") == title:
                return card
        return {}

    def _build_card_from_schema(self, card_schema):
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        card_layout.addWidget(self._create_label(card_schema.get("title", "")))

        grid = self._make_grid()
        r = 0
        for field_def in card_schema.get("fields", []):
            field = self._readonly_field()
            label = field_def.get("label", "")
            r = self._add_row(grid, r, label, field)

            field_id = field_def.get("id")
            if field_id:
                field.setObjectName(field_id)

            group = field_def.get("group")
            data_key = field_def.get("data_key")
            if group and data_key:
                self._field_groups.setdefault(group, {})[data_key] = field

        card_layout.addLayout(grid)
        return card

    # ─────────────────────────────────────────────────────────────────────────
    # SECTIONS
    # ─────────────────────────────────────────────────────────────────────────

    # _build_member_section removed — Grade & Type are now in Dimensional Details.

    def _build_dimensional_section(self):
        card_schema = self._get_card_schema("Dimensional Details:")
        return self._build_card_from_schema(card_schema)

    def _build_shear_section(self):
        card_schema = self._get_card_schema("Shear Connector Details:")
        return self._build_card_from_schema(card_schema)

    def _build_section_properties_section(self):
        card_schema = self._get_card_schema("Section Properties:")
        return self._build_card_from_schema(card_schema)

    # ─────────────────────────────────────────────────────────────────────────
    # CAD PLACEHOLDERS
    # ─────────────────────────────────────────────────────────────────────────

    def _build_top_cad_placeholder(self):
        card = self._create_card_frame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        self.section_preview = RolledSectionPreview()
        self.section_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.preview_caption = QLabel("Girder preview")
        self.preview_caption.setAlignment(Qt.AlignCenter)
        self.preview_caption.setStyleSheet(
            "QLabel { font-size: 13px; font-weight: 700; color: #1e1e1e; border: none; "
            "padding-top: 6px; font-family: 'Ubuntu Sans', 'Segoe UI', sans-serif; }"
        )

        layout.addWidget(self.section_preview, 1)
        layout.addWidget(self.preview_caption)
        
        return card

    # ─────────────────────────────────────────────────────────────────────────
    # STIFFENER TABLE
    # ─────────────────────────────────────────────────────────────────────────

    def _build_stiffener_section(self) -> QFrame:
        """Build the Stiffener Details card with a styled table.

        The table style mirrors the Inputs table in the Lane Details sub-tab
        of Typical Section Details (Additional Inputs dialog) — same font,
        padding, alternating-row colours, and header treatment.
        """
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(12)

        card_layout.addWidget(self._create_label("Stiffener Details:"))

        # ── Table widget ──────────────────────────────────────────────
        columns = self._stiffener_schema.get("columns", [])
        rows = self._stiffener_schema.get("rows", [])
        self._stiffener_columns = columns
        self._stiffener_rows = rows
        num_rows = len(rows)
        num_cols = len(columns)

        self.stiffener_table = NoScrollTable()
        self.stiffener_table.setRowCount(num_rows)
        self.stiffener_table.setColumnCount(num_cols)
        self.stiffener_table.setHorizontalHeaderLabels(
            [col.get("label", "") for col in columns]
        )

        # Populate rows — all cells are read-only and center-aligned.
        for row, row_def in enumerate(rows):
            type_item = QTableWidgetItem(row_def.get("label", ""))
            type_item.setFlags(Qt.ItemIsEnabled)
            type_item.setTextAlignment(Qt.AlignCenter)
            self.stiffener_table.setItem(row, 0, type_item)

            for col in range(1, num_cols):
                cell = QTableWidgetItem("")
                cell.setFlags(Qt.ItemIsEnabled)
                cell.setTextAlignment(Qt.AlignCenter)
                self.stiffener_table.setItem(row, col, cell)

        # ── Header behaviour ──────────────────────────────────────────
        h_header = self.stiffener_table.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.Stretch)
        h_header.setDefaultAlignment(Qt.AlignCenter)

        v_header = self.stiffener_table.verticalHeader()
        v_header.setVisible(False)
        row_height = self._stiffener_schema.get("row_height", 40)
        v_header.setDefaultSectionSize(row_height)

        # ── General table properties ──────────────────────────────────
        self.stiffener_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.stiffener_table.setSelectionMode(QTableWidget.NoSelection)
        self.stiffener_table.setFocusPolicy(Qt.NoFocus)
        self.stiffener_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.stiffener_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.stiffener_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.stiffener_table.setAlternatingRowColors(True)

        # Fixed height: header (~36 px) + rows * row_height + 2 px border.
        table_height = 36 + num_rows * row_height + 2
        self.stiffener_table.setFixedHeight(table_height)

        # ── Stylesheet — mirrors Lane Details Inputs table ────────────
        self.stiffener_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f9f9f9;
                gridline-color: #e0e0e0;
                border: 1px solid #e0e0e0;
                color: #333333;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
                color: #333333;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #333333;
                padding: 8px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
                font-size: 11px;
            }
        """)

        card_layout.addWidget(self.stiffener_table)

        # Add CAD preview below the table
        self.stiffener_preview = StiffenerCadPreviewWidget()
        self.stiffener_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stiffener_preview.setMinimumHeight(200)

        self.stiffener_caption = QLabel("Stiffener preview")
        self.stiffener_caption.setAlignment(Qt.AlignCenter)
        self.stiffener_caption.setStyleSheet(
            "QLabel { font-size: 13px; font-weight: 700; color: #1e1e1e; border: none; "
            "padding-top: 6px; font-family: 'Ubuntu Sans', 'Segoe UI', sans-serif; background: transparent; }"
        )

        card_layout.addSpacing(10)
        card_layout.addWidget(self.stiffener_preview, 1)
        card_layout.addWidget(self.stiffener_caption)

        return card

    # ─────────────────────────────────────────────────────────────────────────
    # LOAD DATA (unchanged logic)
    # ─────────────────────────────────────────────────────────────────────────

    def load_data(self, output_dict: dict, girder_index: int = 0):
        """Populate all field widgets from an output_dict snapshot for the given girder."""
        if not output_dict:
            return
        self._girder_index = girder_index
        normalized_state = self._normalize_output_dict(output_dict, girder_index)

        for group_fields in self._field_groups.values():
            for key, field in group_fields.items():
                field.setText(str(normalized_state.get(key, "")))

        if hasattr(self, "stiffener_table"):
            columns = self._stiffener_columns
            rows = self._stiffener_rows
            for row_index, row_def in enumerate(rows):
                prefix = row_def.get("data_prefix", "")
                if not prefix:
                    continue
                for col_index, col_def in enumerate(columns[1:], start=1):
                    suffix = col_def.get("suffix", "")
                    if not suffix:
                        continue
                    value_key = f"{prefix}_{suffix}"
                    # Try to get the value from normalized_state, with a sensible default
                    value = normalized_state.get(value_key, "NA")
                    # Avoid displaying "None" or empty strings
                    if not value or value == "None":
                        value = "NA"
                    item = QTableWidgetItem(str(value))
                    item.setFlags(Qt.ItemIsEnabled)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.stiffener_table.setItem(row_index, col_index, item)
                    
        self._update_cad_previews(normalized_state, output_dict)

    def _normalize_output_dict(self, output_dict: dict, girder_index: int = 0) -> dict:
        """
        Build a flat dict keyed by schema data_key strings, suitable for
        field.setText() in load_data().

        Every value is read directly from output_dict, which store_design_results()
        populates after a design run (both Optimized and Custom modes). There are
        no raw-input fallbacks, so the tab stays blank until a design has run.

        The Dimensional card reads the selected girder's per-girder ".G{n}.M1" keys,
        falling back to the flat (controlling-girder) key when a per-girder value is
        absent (e.g. an older snapshot).
        """
        out = {}
        gsuf = f".G{girder_index + 1}.M1"

        # ── Helpers ──────────────────────────────────────────────────────────────
        def _str(val):
            if val is None or val == "":
                return ""
            return str(val)
        def _sd(base_key):
            """Per-girder KEY_SD_* value for the selected girder."""
            return output_dict.get(base_key + gsuf, "")
        
        def _round1(val):
            """Value already in mm → 1 dp string."""
            try:
                return _str(round(float(val), 1))
            except (TypeError, ValueError):
                return _str(val)

        # ─────────────────────────────────────────────────────────────────────────
        # DIMENSIONAL DETAILS — flat KEY_SD_* keys (dimensions already in mm).
        # ─────────────────────────────────────────────────────────────────────────
        out["grade_of_material"]   = _str(_sd(KEY_SD_GRADE_OF_MATERIAL))
        out["section_type"]        = _str(_sd(KEY_SD_SECTION_TYPE))
        out["section_designation"] = _str(_sd(KEY_SD_SECTION_DESIGNATION))
        out["section_class"]       = _str(_sd(KEY_SD_SECTION_CLASS))

        out["total_depth"]             = _round1(_sd(KEY_SD_TOTAL_DEPTH))
        out["web_thickness"]           = _round1(_sd(KEY_SD_WEB_THICKNESS))
        out["top_flange_width"]        = _round1(_sd(KEY_SD_TOP_FLANGE_WIDTH))
        out["top_flange_thickness"]    = _round1(_sd(KEY_SD_TOP_FLANGE_THICKNESS))
        out["bottom_flange_width"]     = _round1(_sd(KEY_SD_BOTTOM_FLANGE_WIDTH))
        out["bottom_flange_thickness"] = _round1(_sd(KEY_SD_BOTTOM_FLANGE_THICKNESS))

        out["torsional_restraint"]  = _str(_sd(KEY_SD_TORSIONAL_RESTRAINT))
        out["warping_restraint"]    = _str(_sd(KEY_SD_WARPING_RESTRAINT))
        out["web_type"]             = _str(_sd(KEY_SD_WEB_TYPE))
        out["effective_slab_width"] = _round1(_sd(KEY_SD_EFFECTIVE_SLAB_WIDTH))

        # ─────────────────────────────────────────────────────────────────────────
        # SHEAR CONNECTOR DETAILS — flat KEY_SD_SHEAR_* keys.
        # ─────────────────────────────────────────────────────────────────────────
        out["shear_material_yield_strength"]    = _str(output_dict.get(KEY_SD_SHEAR_YIELD_STRENGTH))
        out["shear_material_ultimate_strength"] = _str(output_dict.get(KEY_SD_SHEAR_ULTIMATE_STRENGTH))
        out["shear_diameter"]                   = _str(output_dict.get(KEY_SD_SHEAR_DIAMETER))
        out["shear_height"]                     = _str(output_dict.get(KEY_SD_SHEAR_HEIGHT))
        out["shear_transverse_spacing"]         = _str(output_dict.get(KEY_SD_SHEAR_TRANSVERSE_SPACING))
        out["shear_studs_per_section"]          = _str(output_dict.get(KEY_SD_SHEAR_STUDS_PER_SECTION))
        out["shear_longitudinal_spacing"]       = _str(output_dict.get(KEY_SD_SHEAR_LONGITUDINAL_SPACING))

        # ─────────────────────────────────────────────────────────────────────────
        # SECTION PROPERTIES — per-member KEY_MP_GIRDER_* keys (SI units, .2e format).
        # The example key locates the active member's ".G{n}.M{m}" suffix.
        # ─────────────────────────────────────────────────────────────────────────
        def _suffix_for(base: str) -> str:
            """Return the selected girder suffix only."""
            return gsuf if base + gsuf in output_dict else ""

        sec_suf = _suffix_for(KEY_MP_GIRDER_SECTIONAL_AREA)

        def _sec(base_key):
            """Raw SI value in .2e format (matches the Girder Details tab)."""
            v = output_dict.get(base_key + sec_suf)
            if v is None or v == "":
                return ""
            try:
                return f"{float(v):.2e}"
            except (TypeError, ValueError):
                return _str(v)

        out["mass"] = _sec(KEY_MP_GIRDER_MASS)
        out["area"] = _sec(KEY_MP_GIRDER_SECTIONAL_AREA)
        out["iz"]   = _sec(KEY_MP_GIRDER_SECTIONAL_IZ)
        out["iv"]   = _sec(KEY_MP_GIRDER_SECTIONAL_IY)
        out["rz"]   = _sec(KEY_MP_GIRDER_RADIUS_GYRATION_Z)
        out["rv"]   = _sec(KEY_MP_GIRDER_RADIUS_GYRATION_Y)
        out["zz"]   = _sec(KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ)
        out["zv"]   = _sec(KEY_MP_GIRDER_ELASTIC_MODULUS_ZY)
        out["zuz"]  = _sec(KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ)
        out["zuv"]  = _sec(KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY)
        out["it"]   = _sec(KEY_MP_GIRDER_TORSION_CONSTANT_IT)
        out["iw"]   = _sec(KEY_MP_GIRDER_WARPING_CONSTANT_IW)

        # ─────────────────────────────────────────────────────────────────────────
        # STIFFENER DETAILS — per-member member_properties.stiffener_details.* keys.
        # Values are per-girder (".G{n}.M{m}"); _suffix_for picks the active member.
        # Grade is the girder material grade (no per-member grade is stored).
        # ─────────────────────────────────────────────────────────────────────────
        grade = _str(output_dict.get(KEY_SD_GRADE_OF_MATERIAL))
        stiff_suf = _suffix_for(KEY_MP_STIFFENER_BEARING_THICKNESS)

        def _mp_stiff(base_key):
            """Per-member stiffener value from the suffixed key."""
            v = output_dict.get(base_key + stiff_suf)
            return str(v) if v is not None and str(v).strip() not in ("", "None", "NA") else ""

        def _na(value):
            return value if value and str(value).strip() not in ("", "None") else "NA"

        # Bearing (always present); count drives the CAD preview (no table column).
        out["stiff_bearing_grade"]     = _na(grade)
        out["stiff_bearing_thickness"] = _na(_mp_stiff(KEY_MP_STIFFENER_BEARING_THICKNESS))
        out["stiff_bearing_width"]     = _na(_mp_stiff(KEY_MP_STIFFENER_BEARING_OUTSTAND))
        out["stiff_bearing_spacing"]   = _na(_mp_stiff(KEY_MP_STIFFENER_SPACING))
        out["stiff_bearing_count"]     = _na(_mp_stiff(KEY_MP_STIFFENER_NO_BEARING_STIFFENERS))

        # Intermediate (only when enabled).
        int_on = _mp_stiff(KEY_MP_STIFFENER_INTERMEDIATE).strip().lower() in ("yes", "true", "1")
        out["stiff_intermediate_on"] = "Yes" if int_on else "No"
        if int_on:
            out["stiff_intermediate_grade"]     = _na(grade)
            out["stiff_intermediate_thickness"] = _na(_mp_stiff(KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS))
            out["stiff_intermediate_width"]     = _na(_mp_stiff(KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND))
            out["stiff_intermediate_spacing"]   = _na(_mp_stiff(KEY_MP_STIFFENER_INTERMEDIATE_SPACING))
        else:
            out["stiff_intermediate_grade"]     = "NA"
            out["stiff_intermediate_thickness"] = "NA"
            out["stiff_intermediate_width"]     = "NA"
            out["stiff_intermediate_spacing"]   = "NA"

        # Longitudinal (only when enabled; width/spacing not user-defined → NA).
        long_mode = _mp_stiff(KEY_MP_STIFFENER_LONGITUDINAL)
        long_on = bool(long_mode) and long_mode.strip().lower() != "no"
        out["stiff_longitudinal_mode"] = long_mode.strip() if long_on else "No"
        if long_on:
            out["stiff_longitudinal_grade"]     = _na(grade)
            out["stiff_longitudinal_thickness"] = _na(_mp_stiff(KEY_MP_STIFFENER_LONGITUDINAL_THICKNESS))
            out["stiff_longitudinal_width"]     = "NA"
            out["stiff_longitudinal_spacing"]   = "NA"
        else:
            out["stiff_longitudinal_grade"]     = "NA"
            out["stiff_longitudinal_thickness"] = "NA"
            out["stiff_longitudinal_width"]     = "NA"
            out["stiff_longitudinal_spacing"]   = "NA"

        return out

    def _update_cad_previews(self, normalized_state: dict, output_dict: dict = None):
        if not output_dict:
            output_dict = {}

        if hasattr(self, "section_preview"):
            def to_f(v):
                try: return float(v)
                except: return None
                
            depth = to_f(normalized_state.get("total_depth"))
            tf_w = to_f(normalized_state.get("top_flange_width"))
            tf_t = to_f(normalized_state.get("top_flange_thickness"))
            bf_w = to_f(normalized_state.get("bottom_flange_width"))
            bf_t = to_f(normalized_state.get("bottom_flange_thickness"))
            web_t = to_f(normalized_state.get("web_thickness"))
            
            bf_w = bf_w or tf_w
            bf_t = bf_t or tf_t
            
            if all([depth, tf_w, tf_t, web_t]):
                st = normalized_state.get("section_type", "").lower()
                self.section_preview.set_dimensions(
                    depth_mm=depth,
                    flange_width_mm=tf_w,
                    bottom_flange_width_mm=bf_w,
                    web_thickness_mm=web_t,
                    flange_thickness_mm=tf_t,
                    bottom_flange_thickness_mm=bf_t,
                    show_welds=(st == "welded")
                )
            else:
                self.section_preview.clear()
                
        if hasattr(self, "stiffener_preview"):
            # Prepare dummy structure for CAD rendering since output_dict doesn't contain segments
            depth = to_f(normalized_state.get("total_depth")) or 0.0
            tf_t = to_f(normalized_state.get("top_flange_thickness")) or 0.0
            bf_t = to_f(normalized_state.get("bottom_flange_thickness")) or 0.0
            
            length_m = 30.0 # fallback
            try:
                length = output_dict.get("geometry.length")
                if length: length_m = float(length)
            except:
                pass
                
            segments = [{"id": "G1M1", "start": 0.0, "end": length_m, "length": length_m}]

            # Drive the CAD from the same normalized values shown in the table so
            # the preview always matches the displayed stiffener details. The CAD
            # parser only accepts digit strings, so coerce numeric values to ints.
            #converts decimal values to whole values
            def _cad_num(key):
                v = normalized_state.get(key)
                s = str(v).strip() if v is not None else ""
                if s in ("", "NA", "None"):
                    return ""
                try:
                    return str(int(round(float(s))))
                except (TypeError, ValueError):
                    return s

            stiff_state = {
                "bearing_stiffeners_each_end": _cad_num("stiff_bearing_count"),
                "bearing_spacing_mm":          _cad_num("stiff_bearing_spacing"),
                "intermediate_stiffener":      normalized_state.get("stiff_intermediate_on"),
                "intermediate_spacing_mm":     _cad_num("stiff_intermediate_spacing"),
                "longitudinal_stiffener":      normalized_state.get("stiff_longitudinal_mode"),
                KEY_SD_SHEAR_DIAMETER:         normalized_state.get("shear_diameter"),
                KEY_SD_SHEAR_HEIGHT:           normalized_state.get("shear_height"),
                KEY_SD_SHEAR_LONGITUDINAL_SPACING: normalized_state.get("shear_longitudinal_spacing"),
            }

            stiffener_by_member = {"G1M1": stiff_state}
            
            section_dims = {
                "G1M1": {
                    "depth_mm": depth,
                    "top_flange_thickness_mm": tf_t,
                    "bottom_flange_thickness_mm": bf_t
                }
            }
            
            self.stiffener_preview.set_data(
                segments=segments,
                stiffener_by_member=stiffener_by_member,
                active_member_id="G1M1",
                section_dims_by_member=section_dims
            )
