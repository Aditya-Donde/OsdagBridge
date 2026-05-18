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
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_check import UtilizationBar, StatusBadge


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
    utilization ratios, and design check results.

    Styling mirrors the Steel Design dialog's Details tab for visual
    consistency across the application.
    """

    _REBAR_ROW_HEIGHT  = 50
    _REBAR_HEADER_HEIGHT = 48
    _REBAR_HEADERS = [
        "Position",
        "Material Yield\nStrength (MPa)",
        "Diameter (mm)",
        "Spacing (mm)",
        "Clear Cover\n(mm)",
        "Area (mm²)",
    ]
    _REBAR_TYPES = ["Top Layer", "Bottom Layer", "Overhang"]

    # (dict key, display label, is_overhang_row)
    _UR_CHECKS = [
        ("ur_bot_uls",   "ULS – Bottom (Sagging)",         False),
        ("ur_top_uls",   "ULS – Top (Hogging)",            False),
        ("ur_oh_uls",    "ULS – Overhang",                 True),
        ("ur_bot_sls_c", "SLS – Bottom Concrete Stress",   False),
        ("ur_bot_sls_s", "SLS – Bottom Steel Stress",      False),
        ("ur_top_sls_c", "SLS – Top Concrete Stress",      False),
        ("ur_top_sls_s", "SLS – Top Steel Stress",         False),
        ("ur_bot_crack", "SLS – Bottom Crack Width",       False),
        ("ur_top_crack", "SLS – Top Crack Width",          False),
        ("ur_oh_sls_c",  "SLS – Overhang Concrete Stress", True),
        ("ur_oh_sls_s",  "SLS – Overhang Steel Stress",    True),
        ("ur_oh_crack",  "SLS – Overhang Crack Width",     True),
    ]

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

        if self._main_window.output_dict:
            self.load_data(self._main_window.output_dict)

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
        """Build the top-level layout: scroll area containing all sections."""
        self.setupWrapper()

        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)

        scroll_area = StyledScrollArea()

        container = QWidget()
        container.setStyleSheet("background-color: white;")

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(12)

        # Deck Properties — left half only (mirrors Steel Design Details layout)
        props_row = QHBoxLayout()
        props_row.setContentsMargins(0, 0, 0, 0)
        props_row.setSpacing(0)
        props_row.addWidget(self._build_properties_section(), 1)
        props_row.addStretch(1)
        container_layout.addLayout(props_row)

        container_layout.addWidget(self._build_reinforcement_section())
        container_layout.addWidget(self._build_utilization_section())
        container_layout.addWidget(self._build_design_check_section())
        container_layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

        # Only run deck design if the main design has already been executed
        # (sizing_result is None until the Design button is clicked).
        backend = getattr(self._main_window, "backend", None)
        if backend is not None and getattr(backend, "sizing_result", None) is not None:
            try:
                from osdagbridge.core.bridge_types.plate_girder.deckdesign import design_deck_slab
                result = design_deck_slab(backend)
                self.load_data(result)
            except Exception:
                self.design_check_text.setHtml(
                    "<p style='color:#c0392b;font-size:11px;padding:12px;'>"
                    "Deck design could not be computed. Check inputs and try again."
                    "</p>"
                )
        else:
            self.design_check_text.setHtml(
                "<p style='color:#888888;font-size:11px;padding:16px;'>"
                "Click <b>Design</b> in the Input panel to run the analysis, "
                "then re-open this dialog to see deck design results."
                "</p>"
            )

    # =========================================================================
    #   HELPERS — mirrors steel_design_details.py card / label / grid patterns
    # =========================================================================

    def _create_card_frame(self) -> QFrame:
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
        label = QLabel(text)
        label.setStyleSheet(
            "font-size: 13px; color: #2B2B2B; font-weight: bold;"
            " background: transparent; border: none;"
        )
        label.setAutoFillBackground(False)
        return label

    def _create_small_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setTextFormat(Qt.RichText)
        label.setStyleSheet(
            "font-size: 11px; color: #333333;"
            " background: transparent; border: none;"
        )
        label.setAutoFillBackground(False)
        return label

    def _readonly_field(self) -> QLineEdit:
        field = QLineEdit()
        field.setReadOnly(True)
        field.setMinimumWidth(80)
        field.setMinimumHeight(28)
        field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        apply_field_style(field)
        return field

    def _make_grid(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)
        grid.setColumnMinimumWidth(0, 230)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
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
        """Deck Properties card: grade, thickness, and overhang."""
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        card_layout.addWidget(self._create_label("Deck Properties:"))

        grid = self._make_grid()
        self.grade_field    = self._readonly_field()
        self.thickness_field = self._readonly_field()
        self.overhang_field  = self._readonly_field()

        r = 0
        r = self._add_row(grid, r, "Grade of Material:",   self.grade_field)
        r = self._add_row(grid, r, "Thickness (mm):",      self.thickness_field)
        r = self._add_row(grid, r, "Deck Overhang (mm):",  self.overhang_field)

        card_layout.addLayout(grid)
        return card

    def _build_reinforcement_section(self) -> QFrame:
        """Reinforcement Details card with a table for top, bottom, and overhang."""
        card = self._create_card_frame()
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(12)
        card_layout.addWidget(self._create_label("Reinforcement Details:"))

        num_rows = len(self._REBAR_TYPES)
        num_cols = len(self._REBAR_HEADERS)

        self.rebar_table = NoScrollTable()
        self.rebar_table.setRowCount(num_rows)
        self.rebar_table.setColumnCount(num_cols)
        self.rebar_table.setHorizontalHeaderLabels(self._REBAR_HEADERS)

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

        # Hide overhang row (row 2) until load_data() reveals it
        self.rebar_table.setRowHidden(2, True)

        h_header = self.rebar_table.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.Stretch)
        h_header.setDefaultAlignment(Qt.AlignCenter)

        v_header = self.rebar_table.verticalHeader()
        v_header.setVisible(False)
        v_header.setDefaultSectionSize(self._REBAR_ROW_HEIGHT)
        v_header.setSectionResizeMode(QHeaderView.Stretch)

        self.rebar_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rebar_table.setSelectionMode(QTableWidget.NoSelection)
        self.rebar_table.setFocusPolicy(Qt.NoFocus)
        self.rebar_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.rebar_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.rebar_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.rebar_table.setAlternatingRowColors(True)

        # Initial height for 2 visible rows (overhang hidden)
        self.rebar_table.setFixedHeight(
            self._REBAR_HEADER_HEIGHT + 2 * self._REBAR_ROW_HEIGHT + 2
        )

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

    def _build_utilization_section(self) -> QFrame:
        """Utilization Summary card with demand/capacity bars for all ULS and SLS checks."""
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(6)
        card_layout.addWidget(self._create_label("Utilization Summary:"))

        # Column header
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 2, 0, 4)
        hdr_lbl = QLabel("Check")
        hdr_lbl.setStyleSheet("font-size: 10px; color: #888; font-weight: bold;")
        hdr_lbl.setFixedWidth(230)
        hdr.addWidget(hdr_lbl)
        hdr.addStretch(1)
        for txt in ("UR", "Status"):
            w = QLabel(txt)
            w.setStyleSheet("font-size: 10px; color: #888; font-weight: bold;")
            w.setFixedWidth(52 if txt == "UR" else 64)
            w.setAlignment(Qt.AlignCenter)
            hdr.addWidget(w)
        card_layout.addLayout(hdr)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e0e0e0;")
        card_layout.addWidget(sep)

        self._ur_widgets: dict = {}

        for key, label, is_overhang in self._UR_CHECKS:
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(0, 3, 0, 3)
            row_l.setSpacing(8)

            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 11px; color: #333333;")
            lbl.setFixedWidth(230)
            row_l.addWidget(lbl)

            bar = UtilizationBar()
            bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            row_l.addWidget(bar, 1)

            val = QLabel("–")
            val.setFixedWidth(52)
            val.setAlignment(Qt.AlignCenter)
            val.setStyleSheet("font-size: 11px; color: #333333; font-weight: bold;")
            row_l.addWidget(val)

            badge = StatusBadge()
            row_l.addWidget(badge)

            # Hide overhang rows until overhang data is present
            row_w.setVisible(not is_overhang)
            card_layout.addWidget(row_w)

            self._ur_widgets[key] = {
                "row":   row_w,
                "bar":   bar,
                "val":   val,
                "badge": badge,
                "is_overhang": is_overhang,
            }

        return card

    def _build_design_check_section(self) -> QFrame:
        """Design Check card with a read-only HTML text area."""
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
    #   HELPERS
    # =========================================================================

    @staticmethod
    def _text_to_html(text: str) -> str:
        """Convert the plain-text design report to HTML with PASS/FAIL colouring."""
        lines = []
        for line in text.split("\n"):
            esc = (line
                   .replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;"))
            esc = esc.replace(
                "PASS",
                '<span style="color:#1a7a4a;font-weight:bold">PASS</span>',
            )
            esc = esc.replace(
                "FAIL",
                '<span style="color:#8b0000;font-weight:bold">FAIL</span>',
            )
            lines.append(esc)
        return (
            "<pre style='font-family:monospace;font-size:11px;"
            "color:#333333;line-height:1.55;margin:0;'>"
            + "<br>".join(lines)
            + "</pre>"
        )

    # =========================================================================
    #   PUBLIC API
    # =========================================================================

    def load_data(self, cad_state: dict) -> None:
        """Populate all widgets from a deck-design result dict.

        Silently ignores missing or invalid keys — safe to call with partial data.
        """
        if not cad_state:
            return

        # ── Properties ───────────────────────────────────────────────────────
        self.grade_field.setText(str(cad_state.get("deck_grade", "")))
        self.thickness_field.setText(str(cad_state.get("deck_thickness", "")))
        self.overhang_field.setText(str(cad_state.get("deck_overhang", "")))

        # ── Reinforcement table ───────────────────────────────────────────────
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

        # Show overhang row only when overhang reinforcement data is present
        has_overhang = bool(cad_state.get("rebar_overhang_dia", ""))
        self.rebar_table.setRowHidden(2, not has_overhang)
        if has_overhang:
            for col, suffix in enumerate(
                ["yield", "dia", "spacing", "cover", "area"], start=1,
            ):
                value = cad_state.get(f"rebar_overhang_{suffix}", "")
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemIsEnabled)
                item.setTextAlignment(Qt.AlignCenter)
                self.rebar_table.setItem(2, col, item)

        n_visible = 2 + (1 if has_overhang else 0)
        self.rebar_table.setFixedHeight(
            self._REBAR_HEADER_HEIGHT + n_visible * self._REBAR_ROW_HEIGHT + 2
        )

        # ── Utilization bars ──────────────────────────────────────────────────
        for key, widgets in self._ur_widgets.items():
            if widgets["is_overhang"]:
                widgets["row"].setVisible(has_overhang)

            raw = cad_state.get(key)
            if raw is None:
                widgets["val"].setText("–")
                widgets["bar"].set_ratio(0.0)
                widgets["badge"].set_neutral()
            else:
                ratio = float(raw)
                widgets["val"].setText(f"{ratio:.3f}")
                widgets["bar"].set_ratio(ratio)
                if ratio <= 1.0:
                    widgets["badge"].set_pass()
                else:
                    widgets["badge"].set_fail()

        # ── Design check text ─────────────────────────────────────────────────
        raw_text = str(cad_state.get("deck_design_check", ""))
        if raw_text:
            self.design_check_text.setHtml(self._text_to_html(raw_text))
        else:
            self.design_check_text.clear()
