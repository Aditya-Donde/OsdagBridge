from PySide6.QtWidgets import (
    QDialog,
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
    QTextEdit,
    QSizeGrip,
)
from PySide6.QtCore import Qt

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.utils.styled_scroll_area import StyledScrollArea
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar


class NoScrollTable(QTableWidget):
    """Passes wheel events to parent scroll area — table never scrolls."""
    def wheelEvent(self, event):
        event.ignore()


# =============================================================================
#   DIALOG: Deck Design
# =============================================================================

class DeckDesign(QDialog):
    """
    Deck Design dialog — displays deck properties, reinforcement details,
    and design check results.

    Styling mirrors the Steel Design dialog's Details tab for visual
    consistency across the application.
    """

    # Reinforcement table constants — matches Stiffener Details table styling.
    _REBAR_ROW_HEIGHT = 50
    _REBAR_HEADERS = [
        "Position",
        "Material Yield\nStrength (MPa)",
        "Diameter (mm)",
        "Spacing (mm)",
        "Clear Cover from\nTop (mm)",
        "Area (mm\u00b2)",
    ]
    _REBAR_TYPES = ["Top Layer", "Bottom Layer"]

    # =========================================================================
    #   UI INITIALISATION
    # =========================================================================

    def __init__(self, parent=None):
        super().__init__(None)
        self._main_window = parent
        self.setObjectName("DeckDesign")
        self.resize(1024, 720)
        self.setMinimumSize(900, 520)
        self.init_ui()

        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #90AF13;
            }
        """)

    # =========================================================================
    #   WINDOW WRAPPER — frameless with custom title bar + resize grip
    # =========================================================================

    def setupWrapper(self):
        """
        Configure a frameless window with a custom title bar and a resize grip.
        The content_widget acts as the root container for the dialog layout.
        """
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.Window
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar()
        self.title_bar.setTitle("Deck Design")
        main_layout.addWidget(self.title_bar)

        self.content_widget = QWidget(self)
        main_layout.addWidget(self.content_widget, 1)

        size_grip = QSizeGrip(self)
        size_grip.setFixedSize(16, 16)

        overlay = QHBoxLayout()
        overlay.setContentsMargins(0, 0, 4, 4)
        overlay.addStretch(1)
        overlay.addWidget(size_grip, 0, Qt.AlignBottom | Qt.AlignRight)
        main_layout.addLayout(overlay)

    def init_ui(self):
        """Build the top-level layout: scroll area containing the three sections."""
        self.setupWrapper()

        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)

        # ── SCROLL AREA ───────────────────────────────────────────────────────
        scroll_area = StyledScrollArea()

        container = QWidget()
        container.setStyleSheet("background-color: white;")

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(12)

        # Deck Properties: constrain to ~50% width (left half), matching
        # the Steel Design Details tab's side-by-side card layout.
        props_row = QHBoxLayout()
        props_row.setContentsMargins(0, 0, 0, 0)
        props_row.setSpacing(0)
        props_row.addWidget(self._build_properties_section(), 1)
        props_row.addStretch(1)  # empty right half
        container_layout.addLayout(props_row)

        container_layout.addWidget(self._build_reinforcement_section())
        container_layout.addWidget(self._build_design_check_section())
        container_layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

    # =========================================================================
    #   HELPERS — mirrors steel_design_details.py card / label / grid patterns
    # =========================================================================

    def _create_card_frame(self) -> QFrame:
        """Outer card — same as SteelDesignDetailsTab._create_card_frame."""
        frame = QFrame()
        frame.setObjectName("girderCard")
        frame.setStyleSheet(
            "QFrame#girderCard {"
            "  background-color: white;"
            "  border: 1px solid #b0b0b0;"
            "  border-radius: 6px;"
            "}"
        )
        return frame

    def _create_label(self, text: str) -> QLabel:
        """Section title label — 13 px bold, matching Steel Design."""
        label = QLabel(text)
        label.setStyleSheet(
            "font-size: 13px; color: #2B2B2B; font-weight: bold;"
            " background: transparent; border: none;"
        )
        label.setAutoFillBackground(False)
        return label

    def _create_small_label(self, text: str) -> QLabel:
        """Row field label — 11 px, supports HTML rich text."""
        label = QLabel(text)
        label.setTextFormat(Qt.RichText)
        label.setStyleSheet(
            "font-size: 11px; color: #333333;"
            " background: transparent; border: none;"
        )
        label.setAutoFillBackground(False)
        return label

    def _readonly_field(self) -> QLineEdit:
        """Readonly output field — expands to fill its grid column."""
        field = QLineEdit()
        field.setReadOnly(True)
        field.setMinimumWidth(80)
        field.setMinimumHeight(28)
        field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        apply_field_style(field)
        return field

    def _make_grid(self) -> QGridLayout:
        """Grid matching Steel Design Details grid spacing."""
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)
        grid.setColumnMinimumWidth(0, 230)
        grid.setColumnStretch(0, 0)   # label: fits content, doesn't stretch
        grid.setColumnStretch(1, 1)   # field: fills all remaining width
        return grid

    def _add_row(self, grid, row, text, widget):
        grid.addWidget(
            self._create_small_label(text), row, 0,
            Qt.AlignLeft | Qt.AlignVCenter,
        )
        grid.addWidget(widget, row, 1)
        return row + 1

    # =========================================================================
    #   SECTIONS
    # =========================================================================

    def _build_properties_section(self) -> QFrame:
        """Build the Deck Properties card with grade and thickness fields."""
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        card_layout.addWidget(self._create_label("Deck Properties:"))

        grid = self._make_grid()
        self.grade_field     = self._readonly_field()
        self.thickness_field = self._readonly_field()

        r = 0
        r = self._add_row(grid, r, "Grade of Material:", self.grade_field)
        r = self._add_row(grid, r, "Thickness (mm):",    self.thickness_field)

        card_layout.addLayout(grid)
        return card

    def _build_reinforcement_section(self) -> QFrame:
        """Build the Reinforcement Details card with a styled table.

        The table style mirrors the Stiffener Details table in the Steel
        Design Details tab — same font, padding, alternating-row colours,
        center alignment, and header treatment.
        """
        card = self._create_card_frame()
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(12)
        card_layout.addWidget(self._create_label("Reinforcement Details:"))

        # ── Table widget ──────────────────────────────────────────────
        num_rows = len(self._REBAR_TYPES)
        num_cols = len(self._REBAR_HEADERS)

        self.rebar_table = NoScrollTable()
        self.rebar_table.setRowCount(num_rows)
        self.rebar_table.setColumnCount(num_cols)
        self.rebar_table.setHorizontalHeaderLabels(self._REBAR_HEADERS)

        # Populate rows — all cells are read-only and center-aligned.
        for row, type_name in enumerate(self._REBAR_TYPES):
            type_item = QTableWidgetItem(type_name)
            type_item.setFlags(Qt.ItemIsEnabled)
            type_item.setTextAlignment(Qt.AlignCenter)
            self.rebar_table.setItem(row, 0, type_item)

            for col in range(1, num_cols):
                cell = QTableWidgetItem("")
                cell.setFlags(Qt.ItemIsEnabled)
                cell.setTextAlignment(Qt.AlignCenter)
                self.rebar_table.setItem(row, col, cell)

        # ── Header behaviour ──────────────────────────────────────────
        h_header = self.rebar_table.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.Stretch)
        h_header.setDefaultAlignment(Qt.AlignCenter)

        v_header = self.rebar_table.verticalHeader()
        v_header.setVisible(False)
        v_header.setDefaultSectionSize(self._REBAR_ROW_HEIGHT)
        v_header.setSectionResizeMode(QHeaderView.Stretch)

        # ── General table properties ──────────────────────────────────
        self.rebar_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rebar_table.setSelectionMode(QTableWidget.NoSelection)
        self.rebar_table.setFocusPolicy(Qt.NoFocus)
        self.rebar_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.rebar_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.rebar_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.rebar_table.setAlternatingRowColors(True)

        # Height: multi-line headers need ~48 px, each data row is
        # _REBAR_ROW_HEIGHT (40 px), plus 2 px for the border.
        header_height = 48
        table_height = header_height + num_rows * self._REBAR_ROW_HEIGHT + 2
        self.rebar_table.setFixedHeight(table_height)

        # ── Stylesheet — mirrors Stiffener / Lane Details table ───────
        self.rebar_table.setStyleSheet("""
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

        card_layout.addWidget(self.rebar_table)
        return card

    def _build_design_check_section(self) -> QFrame:
        """Build the Design Check card with a read-only text area."""
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        card_layout.addWidget(self._create_label("Design Check:"))

        self.design_check_text = QTextEdit()
        self.design_check_text.setReadOnly(True)
        self.design_check_text.setMinimumHeight(200)
        self.design_check_text.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding,
        )
        self.design_check_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: none;
                font-size: 11px;
                color: #333333;
            }
        """)
        card_layout.addWidget(self.design_check_text)
        return card

    # =========================================================================
    #   PUBLIC API
    # =========================================================================

    def load_data(self, cad_state: dict) -> None:
        """Populate all field widgets from a cad_state snapshot.

        Silently ignores missing or invalid keys.
        """
        if not cad_state:
            return

        self.grade_field.setText(str(cad_state.get("deck_grade", "")))
        self.thickness_field.setText(str(cad_state.get("deck_thickness", "")))

        rebar_map = {0: "top", 1: "bottom"}
        for row, prefix in rebar_map.items():
            for col, suffix in enumerate(
                ["yield", "dia", "spacing", "cover", "area"], start=1,
            ):
                value = cad_state.get(f"rebar_{prefix}_{suffix}", "")
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemIsEnabled)
                item.setTextAlignment(Qt.AlignCenter)
                self.rebar_table.setItem(row, col, item)

        self.design_check_text.setPlainText(
            str(cad_state.get("deck_design_check", ""))
        )