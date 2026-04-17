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
    QTextEdit,
)
from PySide6.QtCore import Qt

from osdagbridge.desktop.ui.docks.output_dock import (
    NoScrollComboBox,
)
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.utils.styled_scroll_area import StyledScrollArea

_UI_FONT = "font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px;"

# From load_combination_tab.py defaults + output_dock
LOAD_COMBINATIONS = [
    "Envelope",
    "DL + LL",
    "1.35 DL + 1.5 LL",
    "DL", "SIDL", "LL",
    "WL", "EL", "IMF", "TL",
]

# 8 design checks from the screenshot — 2 columns ├ù 4 rows
DESIGN_CHECKS = [
    ("flexure",          "Strength Limit State (Flexure)"),
    ("shear_long_trans", "Resistance to Longitudinal and Transverse Shear"),
    ("shear",            "Strength Limit State (Shear)"),
    ("fatigue",          "Resistance to Fatigue"),
    ("interaction",      "Interaction"),
    ("stress",           "Stress Limitation"),
    ("ltb",              "Lateral Torsional Buckling"),
    ("deflection",       "Deflection and Crack Control"),
]


class SteelDesignCheckTab(QWidget):
    """
    Design Check tab for the Steel Design dialog.

    Displays eight IRC code compliance check cards in a two-column grid.
    Each card shows a check title and a read-only output area that is
    populated at runtime when design results are available.

    Public API
    ----------
    set_check_result(key, text)
        Write a result string into the named check card output area.
    clear_results()
        Clear all check output areas.
    set_girder_count(count)
        Repopulate the Member ID combo with the correct girder count.
    load_data(cad_state)
        Restore check results from a cad_state snapshot.

    Check keys (used by set_check_result / load_data)
    --------------------------------------------------
    ``flexure``, ``shear_long_trans``, ``shear``, ``fatigue``,
    ``interaction``, ``stress``, ``ltb``, ``deflection``
    """

    def __init__(self, parent=None):
        self.check_outputs = {}   # key → QTextEdit

        super().__init__(parent)

        # White background — consistent with SteelDesignDetailsTab and SteelDesignAnalysisTab.
        self.setStyleSheet("background-color: white;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = StyledScrollArea()

        container = QWidget()
        container.setStyleSheet("background-color: white;")

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(18, 6, 18, 12)
        container_layout.setSpacing(16)

        # ── TOP BAR: Member ID (left) + Load Combination (right) ──────
        container_layout.addLayout(self._build_top_bar())

        # ── CHECK CARDS GRID: 2 columns ───────────────────────────────
        container_layout.addLayout(self._build_checks_grid())

        container_layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS — exact copy from steel_design_details.py
    # ─────────────────────────────────────────────────────────────────────────

    def _section_card(self, title):
        """Return a borderless card QFrame with a bold title label and a QVBoxLayout."""
        card = QFrame()
        card.setObjectName("sectionCard")
        card.setStyleSheet("""
            QFrame#sectionCard {
                background-color: white;
                border: none;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #000;")
        card_layout.addWidget(title_label)

        return card, card_layout

    def _row_label(self, text):
        """Return a left-aligned row label with minimum width 180 px."""
        lbl = QLabel(text)
        lbl.setStyleSheet(f"{_UI_FONT} color: #333333;")
        lbl.setMinimumWidth(180)
        return lbl

    def _make_grid(self):
        """Return a three-column QGridLayout: label | field | stretch."""
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 1)
        return grid

    def _readonly_field(self):
        """Return a fixed 150×22 px read-only QLineEdit."""
        field = QLineEdit()
        field.setReadOnly(True)
        field.setFixedWidth(150)
        field.setFixedHeight(22)
        field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        apply_field_style(field)
        return field

    def _add_row(self, grid, row, text, widget):
        """Append a (label, widget) row to grid at the given row index; return the next row index."""
        grid.addWidget(self._row_label(text), row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        grid.addWidget(widget,                row, 1, Qt.AlignLeft | Qt.AlignVCenter)
        return row + 1

    # ─────────────────────────────────────────────────────────────────────────
    # TOP BAR
    # ─────────────────────────────────────────────────────────────────────────

    def _build_top_bar(self):
        """Build the Member ID and Load Combination selector row."""
        bar = QHBoxLayout()
        bar.setSpacing(24)
        bar.setContentsMargins(0, 0, 0, 0)

        # Member ID
        member_lbl = QLabel("Member ID")
        member_lbl.setStyleSheet(f"{_UI_FONT} color: #000;")

        self.member_combo = NoScrollComboBox()
        apply_field_style(self.member_combo)
        self.member_combo.setFixedWidth(150)
        self.member_combo.setFixedHeight(22)
        self.member_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.member_combo.addItems(["All", "Girder 1", "Girder 2"])

        bar.addWidget(member_lbl)
        bar.addWidget(self.member_combo)

        bar.addSpacing(40)

        # Load Combination
        load_lbl = QLabel("Load Combination:")
        load_lbl.setStyleSheet(f"{_UI_FONT} color: #000;")

        self.load_combo = NoScrollComboBox()
        apply_field_style(self.load_combo)
        self.load_combo.setFixedWidth(150)
        self.load_combo.setFixedHeight(22)
        self.load_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.load_combo.addItems(LOAD_COMBINATIONS)

        bar.addWidget(load_lbl)
        bar.addWidget(self.load_combo)
        bar.addStretch()

        return bar

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK CARDS GRID
    # ─────────────────────────────────────────────────────────────────────────

    def _build_checks_grid(self):
        """
        2-column grid of check cards.
        Left column: flexure, shear, interaction, LTB
        Right column: longitudinal/transverse shear, fatigue, stress, deflection
        """
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        for idx, (key, title) in enumerate(DESIGN_CHECKS):
            col = idx % 2
            row = idx // 2
            card = self._build_check_card(key, title)
            grid.addWidget(card, row, col)

        return grid

    def _build_check_card(self, key, title):
        """
        Single check card:
          - Rounded border matching the screenshot style
          - Bold title at top
          - Expanding QTextEdit output area below (readonly)
        """
        card = QFrame()
        card.setObjectName("checkCard")
        card.setStyleSheet("""
            QFrame#checkCard {
                background-color: white;
                border: 1px solid #b0b0b0;
                border-radius: 6px;
            }
        """)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(8)

        # Title
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"{_UI_FONT.replace('11px','12px')} font-weight: bold; color: #2B2B2B; background: transparent; border: none;")
        title_lbl.setWordWrap(True)
        card_layout.addWidget(title_lbl)

        # Output area — readonly, expandable, shows check results
        output = QTextEdit()
        output.setReadOnly(True)
        output.setFixedHeight(60)
        output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        output.setStyleSheet(f"""
            QTextEdit {{
                background-color: white;
                border: none;
                {_UI_FONT}
                color: #333;
            }}
        """)
        card_layout.addWidget(output)

        self.check_outputs[key] = output
        return card

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────

    def set_girder_count(self, count):
        """Repopulate the Member ID combo with 'All' plus one entry per girder."""
        self.member_combo.clear()
        self.member_combo.addItems(["All"] + [f"Girder {i}" for i in range(1, count + 1)])

    def load_data(self, cad_state: dict):
        """Populate check output areas and member combo from a cad_state snapshot."""
        if not cad_state:
            return
        try:
            self.set_girder_count(int(cad_state.get("no_of_girders", 2)))
        except (ValueError, TypeError):
            pass

        # Populate check output areas if results are in cad_state
        for key, output in self.check_outputs.items():
            result = cad_state.get(f"check_{key}", "")
            output.setPlainText(str(result) if result else "")

    def set_check_result(self, key: str, text: str):
        """Write result text into the named check card output area; silently ignores unknown keys."""
        if key in self.check_outputs:
            self.check_outputs[key].setPlainText(text)

    def clear_results(self):
        """Clear all eight check output areas."""
        for output in self.check_outputs.values():
            output.clear()
