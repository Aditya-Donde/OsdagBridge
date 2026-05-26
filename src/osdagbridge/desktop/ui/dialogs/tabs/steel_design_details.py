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
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    STEEL_DESIGN_DETAILS_SCHEMA,
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

        # ── TOP ROW: CAD placeholder (right only; Member Info removed) 
        container_layout.addWidget(self._build_top_cad_placeholder())

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
        cad_schema = self._cad_schema.get("top", {})
        self.cad_placeholder = QLabel()
        min_height = cad_schema.get("min_height", 160)
        self.cad_placeholder.setMinimumHeight(min_height)
        self.cad_placeholder.setAlignment(Qt.AlignCenter)
        self.cad_placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        cad_id = cad_schema.get("id")
        if cad_id:
            self.cad_placeholder.setObjectName(cad_id)
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
        cad_schema = self._cad_schema.get("bottom", {})
        bottom_cad = QLabel()
        width = cad_schema.get("width", 400)
        height = cad_schema.get("height", 200)
        bottom_cad.setFixedSize(width, height)
        bottom_cad.setAlignment(Qt.AlignCenter)
        bottom_cad.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        cad_id = cad_schema.get("id")
        if cad_id:
            bottom_cad.setObjectName(cad_id)
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
        return card

    # ─────────────────────────────────────────────────────────────────────────
    # LOAD DATA (unchanged logic)
    # ─────────────────────────────────────────────────────────────────────────

    def load_data(self, cad_state: dict):
        """Populate all field widgets from a cad_state snapshot; silently ignores missing or invalid keys."""
        if not cad_state:
            return

        for group_fields in self._field_groups.values():
            for key, field in group_fields.items():
                field.setText(str(cad_state.get(key, "")))

        if hasattr(self, "stiffener_table"):
            columns = self._stiffener_columns
            rows = self._stiffener_rows
            for row_index, row_def in enumerate(rows):
                prefix = row_def.get("data_prefix", "")
                for col_index, col_def in enumerate(columns[1:], start=1):
                    suffix = col_def.get("suffix", "")
                    value_key = f"{prefix}_{suffix}" if prefix and suffix else ""
                    value = cad_state.get(value_key, "") if value_key else ""
                    item = QTableWidgetItem(str(value))
                    item.setFlags(Qt.ItemIsEnabled)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.stiffener_table.setItem(row_index, col_index, item)
