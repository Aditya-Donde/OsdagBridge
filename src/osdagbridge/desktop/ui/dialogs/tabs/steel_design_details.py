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
from osdagbridge.desktop.ui.utils.rolled_section_preview import RolledSectionPreview
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.stiffener_details_tab import (
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
    KEY_SD_SECTION_PROP_MASS,
    KEY_SD_SECTION_PROP_AREA,
    KEY_SD_SECTION_PROP_IZ,
    KEY_SD_SECTION_PROP_IV,
    KEY_SD_SECTION_PROP_RZ,
    KEY_SD_SECTION_PROP_RV,
    KEY_SD_SECTION_PROP_ZZ,
    KEY_SD_SECTION_PROP_ZV,
    KEY_SD_SECTION_PROP_ZUZ,
    KEY_SD_SECTION_PROP_ZUV,
    KEY_SD_SECTION_PROP_IT,
    KEY_SD_SECTION_PROP_IW,
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

    def load_data(self, output_dict: dict):
        """Populate all field widgets from an output_dict snapshot; normalizes schema keys to flat dict."""
        if not output_dict:
            return
            
        normalized_state = self._normalize_output_dict(output_dict)

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

    def _normalize_output_dict(self, output_dict: dict) -> dict:
        """
        Build a flat dict keyed by schema data_key strings, suitable for
        field.setText() in load_data().

        Priority: read KEY_SD_* values written by store_design_results() first
        (present after a full design run), then fall back to raw input_dict keys
        (present when the dialog is opened before design has run).
        """
        out = {}

        # ── Helpers ──────────────────────────────────────────────────────────────
        def _str(val):
            if val is None or val == "":
                return ""
            return str(val)

        def _mm(val):
            """SI metres → mm string, 1 dp."""
            try:
                return f"{float(val) * 1000:.1f}"
            except (TypeError, ValueError):
                return _str(val)

        def _get(key, fallback_key=None, fallback_val=""):
            """Read key; if missing or empty try fallback_key; else fallback_val."""
            v = output_dict.get(key)
            if v is not None and v != "":
                return v
            if fallback_key is not None:
                v2 = output_dict.get(fallback_key)
                if v2 is not None and v2 != "":
                    return v2
            return fallback_val

        # ─────────────────────────────────────────────────────────────────────────
        # DIMENSIONAL DETAILS
        # Prefer KEY_SD_* (post-design); fall back to raw input_dict keys (pre-design).
        # ─────────────────────────────────────────────────────────────────────────

        # Grade of Material
        out["grade_of_material"] = _str(_get(
            KEY_SD_GRADE_OF_MATERIAL,               # "steeldesign.details.grade_of_material"
            "material.girder",                       # raw fallback
        ))

        # Section Type — KEY_SD_SECTION_TYPE written as "Welded"/"Rolled" by store_design_results.
        # Raw fallback: derive from design_mode ("Optimized" → "Welded").
        sd_type = _get(KEY_SD_SECTION_TYPE)
        if not sd_type:
            mode = _str(output_dict.get("geometry.design_mode", ""))
            sd_type = "Welded" if "Optimized" in mode else "Rolled"
        out["section_type"] = _str(sd_type)

        # Section Designation — "D × bf_top × tf_top × bf_bot × tf_bot" built by store_design_results.
        # Raw fallback: rolled IS section name.
        out["section_designation"] = _str(_get(
            KEY_SD_SECTION_DESIGNATION,
            "member_properties.girder_details.section_input.is_section",
        ))

        # Section Class — only available post-design (no raw fallback).
        out["section_class"] = _str(_get(KEY_SD_SECTION_CLASS))

        # Plate dimensions — KEY_SD_* are already in mm (post-design).
        # Raw fallback keys are SI (m) → convert with _mm().
        def _dim(sd_key, raw_key):
            v = output_dict.get(sd_key)
            if v is not None and v != "":
                return _str(round(float(v), 1))      # already mm
            raw = output_dict.get(raw_key)
            if raw is not None and raw != "":
                return _mm(raw)                       # SI → mm
            return ""

        out["total_depth"] = _dim(
            KEY_SD_TOTAL_DEPTH,
            "member_properties.girder_details.section_input.depth",
        )
        out["web_thickness"] = _dim(
            KEY_SD_WEB_THICKNESS,
            "member_properties.girder_details.section_input.web_thickness",
        )
        out["top_flange_width"] = _dim(
            KEY_SD_TOP_FLANGE_WIDTH,
            "member_properties.girder_details.section_input.top_flange_width",
        )
        out["top_flange_thickness"] = _dim(
            KEY_SD_TOP_FLANGE_THICKNESS,
            "member_properties.girder_details.section_input.top_flange_thickness",
        )
        out["bottom_flange_width"] = _dim(
            KEY_SD_BOTTOM_FLANGE_WIDTH,
            "member_properties.girder_details.section_input.bottom_flange_width",
        )
        out["bottom_flange_thickness"] = _dim(
            KEY_SD_BOTTOM_FLANGE_THICKNESS,
            "member_properties.girder_details.section_input.bottom_flange_thickness",
        )

        # Torsional / Warping Restraint — string labels from Additional Inputs.
        # store_design_results writes the label string; no meaningful raw fallback.
        out["torsional_restraint"] = _str(_get(KEY_SD_TORSIONAL_RESTRAINT))
        out["warping_restraint"]   = _str(_get(KEY_SD_WARPING_RESTRAINT))

        # Web Type — string label from Additional Inputs.
        out["web_type"] = _str(_get(KEY_SD_WEB_TYPE))

        # Effective Slab Width — mm, only available post-design.
        eff = output_dict.get(KEY_SD_EFFECTIVE_SLAB_WIDTH)
        out["effective_slab_width"] = _str(round(float(eff), 1)) if eff not in (None, "") else ""

        # ─────────────────────────────────────────────────────────────────────────
        # SHEAR CONNECTOR DETAILS
        # ─────────────────────────────────────────────────────────────────────────

        out["shear_material_yield_strength"] = _str(_get(
            KEY_SD_SHEAR_YIELD_STRENGTH,
            "design_options.shear_studs.yield_strength",
        ))
        out["shear_material_ultimate_strength"] = _str(_get(
            KEY_SD_SHEAR_ULTIMATE_STRENGTH,
            "design_options.shear_studs.ultimate_strength",
        ))
        out["shear_diameter"] = _str(_get(
            KEY_SD_SHEAR_DIAMETER,
            "design_options.shear_studs.diameter",
        ))
        out["shear_height"] = _str(_get(
            KEY_SD_SHEAR_HEIGHT,
            "design_options.shear_studs.height",
        ))
        out["shear_transverse_spacing"] = _str(_get(
            KEY_SD_SHEAR_TRANSVERSE_SPACING,
            "design_options.shear_studs.transverse_spacing",
        ))
        out["shear_studs_per_section"] = _str(_get(
            KEY_SD_SHEAR_STUDS_PER_SECTION,
            "design_options.shear_studs.count",
        ))
        # Longitudinal spacing — only available post-design (computed by IRC 22 pipeline).
        out["shear_longitudinal_spacing"] = _str(_get(KEY_SD_SHEAR_LONGITUDINAL_SPACING))

        # ─────────────────────────────────────────────────────────────────────────
        # SECTION PROPERTIES
        # Display units: cm², cm⁴, cm, cm³, cm⁶  (matches girder_details_tab convention)
        # KEY_SD_SECTION_PROP_* store SI values (m², m⁴ …) from input_dict.
        # ─────────────────────────────────────────────────────────────────────────

        def _si(sd_key, raw_key, conv_fn):
            """Read sd_key or raw_key; apply conv_fn to convert SI → display unit."""
            v = output_dict.get(sd_key)
            if v is None or v == "":
                v = output_dict.get(raw_key)
            if v is None or v == "":
                return ""
            try:
                return f"{conv_fn(float(v)):.2f}"
            except (TypeError, ValueError):
                return _str(v)

        m2_to_cm2  = lambda v: v * 1e4
        m4_to_cm4  = lambda v: v * 1e8
        m_to_cm    = lambda v: v * 1e2
        m3_to_cm3  = lambda v: v * 1e6
        m6_to_cm6  = lambda v: v * 1e12

        out["mass"] = _str(_get(
            KEY_SD_SECTION_PROP_MASS,
            "member_properties.girder_details.section_properties.mass",
        ))
        out["area"] = _si(
            KEY_SD_SECTION_PROP_AREA,
            "member_properties.girder_details.section_properties.area",
            m2_to_cm2,
        )
        out["iz"] = _si(
            KEY_SD_SECTION_PROP_IZ,
            "member_properties.girder_details.section_properties.iz",
            m4_to_cm4,
        )
        out["iv"] = _si(
            KEY_SD_SECTION_PROP_IV,
            "member_properties.girder_details.section_properties.iy",
            m4_to_cm4,
        )
        out["rz"] = _si(
            KEY_SD_SECTION_PROP_RZ,
            "member_properties.girder_details.section_properties.radius_gyration_z",
            m_to_cm,
        )
        out["rv"] = _si(
            KEY_SD_SECTION_PROP_RV,
            "member_properties.girder_details.section_properties.radius_gyration_y",
            m_to_cm,
        )
        out["zz"] = _si(
            KEY_SD_SECTION_PROP_ZZ,
            "member_properties.girder_details.material_properties.modulus_of_elasticity_zz",
            m3_to_cm3,
        )
        out["zv"] = _si(
            KEY_SD_SECTION_PROP_ZV,
            "member_properties.girder_details.material_properties.modulus_of_elasticity_zy",
            m3_to_cm3,
        )
        out["zuz"] = _si(
            KEY_SD_SECTION_PROP_ZUZ,
            "member_properties.girder_details.material_properties.plastic_modulus_zuz",
            m3_to_cm3,
        )
        out["zuv"] = _si(
            KEY_SD_SECTION_PROP_ZUV,
            "member_properties.girder_details.material_properties.plastic_modulus_zuy",
            m3_to_cm3,
        )
        out["it"] = _si(
            KEY_SD_SECTION_PROP_IT,
            "member_properties.girder_details.section_properties.torsion_constant_it",
            m4_to_cm4,
        )
        out["iw"] = _si(
            KEY_SD_SECTION_PROP_IW,
            "member_properties.girder_details.section_properties.warping_constant_iw",
            m6_to_cm6,
        )
        out["torsional_restraint"] = _str(
            _get(KEY_SD_TORSIONAL_RESTRAINT) or "Fully Restrained"
        )
        out["warping_restraint"] = _str(
            _get(KEY_SD_WARPING_RESTRAINT) or "Both Flanges Restrained"
        )
        out["web_type"] = _str(
            _get(KEY_SD_WEB_TYPE) or "Thin Web with ITS"
        )

        grade = out.get("grade_of_material", "")   # already resolved above

        # StiffenerDetailsTab.collect_data() saves values nested under
        # stiffener_by_member[member_id]. Read from the first member's state
        # as the pre-design fallback; post-design flat keys take priority.
        stiffener_data = output_dict.get("stiffener_by_member") or {}
        first_member_state = {}
        if stiffener_data:
            first_key = next(iter(stiffener_data), None)
            if first_key:
                first_member_state = stiffener_data[first_key] or {}

        def _stiff_val(flat_key, nested_key=None):
            """Read post-design flat key first; fall back to nested member state."""
            if flat_key:
                v = output_dict.get(flat_key)
                if v is not None and str(v).strip() not in ("", "None"):
                    return str(v)
            if nested_key:
                v2 = first_member_state.get(nested_key)
                if v2 is not None and str(v2).strip() not in ("", "None"):
                    return str(v2)
            return ""

        # ── Bearing (always populated) ────────────────────────────────────────────
        out["stiff_bearing_grade"]     = _stiff_val("stiff_bearing_grade") or grade
        out["stiff_bearing_thickness"] = _stiff_val("stiff_bearing_thickness", "bearing_thickness_value")
        out["stiff_bearing_width"]     = _stiff_val("stiff_bearing_width",     "bearing_outstand_mm")
        out["stiff_bearing_spacing"]   = _stiff_val("stiff_bearing_spacing",   "bearing_spacing_mm")
        for key in ("stiff_bearing_grade", "stiff_bearing_thickness", "stiff_bearing_width", "stiff_bearing_spacing"):
            if not out[key] or str(out[key]).strip() in ("", "None"):
                out[key] = "NA"

        # ── Intermediate ──────────────────────────────────────────────────────────
        int_from_store = output_dict.get("stiff_intermediate_grade")
        int_flag_raw = str(
            first_member_state.get("intermediate_stiffener")
            or output_dict.get("intermediate_stiffener", "No")
        ).strip()

        if int_from_store is not None:
            out["stiff_intermediate_grade"]     = _stiff_val("stiff_intermediate_grade")
            out["stiff_intermediate_thickness"] = _stiff_val("stiff_intermediate_thickness")
            out["stiff_intermediate_width"]     = _stiff_val("stiff_intermediate_width")
            out["stiff_intermediate_spacing"]   = _stiff_val("stiff_intermediate_spacing")
        elif int_flag_raw == "Yes":
            out["stiff_intermediate_grade"]     = grade
            out["stiff_intermediate_thickness"] = _stiff_val("", "intermediate_thickness_value")
            out["stiff_intermediate_width"]     = _stiff_val("", "intermediate_outstand_mm")
            out["stiff_intermediate_spacing"]   = _stiff_val("", "intermediate_spacing_mm")
        else:
            out["stiff_intermediate_grade"]     = "NA"
            out["stiff_intermediate_thickness"] = "NA"
            out["stiff_intermediate_width"]     = "NA"
            out["stiff_intermediate_spacing"]   = "NA"
        for key in ("stiff_intermediate_grade", "stiff_intermediate_thickness", "stiff_intermediate_width", "stiff_intermediate_spacing"):
            if not out[key] or str(out[key]).strip() in ("", "None"):
                out[key] = "NA"

        # ── Longitudinal ──────────────────────────────────────────────────────────
        long_from_store = output_dict.get("stiff_longitudinal_grade")
        long_flag_raw = str(
            first_member_state.get("longitudinal_stiffener")
            or output_dict.get("longitudinal_stiffener", "No")
        ).strip()

        if long_from_store is not None:
            out["stiff_longitudinal_grade"]     = _stiff_val("stiff_longitudinal_grade")
            out["stiff_longitudinal_thickness"] = _stiff_val("stiff_longitudinal_thickness")
            out["stiff_longitudinal_width"]     = _stiff_val("stiff_longitudinal_width")
            out["stiff_longitudinal_spacing"]   = _stiff_val("stiff_longitudinal_spacing")
        elif long_flag_raw != "No":
            out["stiff_longitudinal_grade"]     = grade
            out["stiff_longitudinal_thickness"] = _stiff_val("", "longitudinal_thickness_value")
            out["stiff_longitudinal_width"]     = "NA"
            out["stiff_longitudinal_spacing"]   = "NA"
        else:
            out["stiff_longitudinal_grade"]     = "NA"
            out["stiff_longitudinal_thickness"] = "NA"
            out["stiff_longitudinal_width"]     = "NA"
            out["stiff_longitudinal_spacing"]   = "NA"
        for key in ("stiff_longitudinal_grade", "stiff_longitudinal_thickness", "stiff_longitudinal_width", "stiff_longitudinal_spacing"):
            if not out[key] or str(out[key]).strip() in ("", "None"):
                out[key] = "NA"

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
            
            stiff_state = {
                "bearing_stiffeners_each_end": str(output_dict.get("bearing_stiffeners_each_end", "2")),
                "bearing_spacing_mm":          str(output_dict.get("bearing_spacing_mm", "")),
                "intermediate_stiffener":      str(output_dict.get("intermediate_stiffener", "No")),
                "intermediate_spacing_mm":     str(output_dict.get("intermediate_spacing_mm", "NA")),
                "longitudinal_stiffener":      str(output_dict.get("longitudinal_stiffener", "No")),
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
