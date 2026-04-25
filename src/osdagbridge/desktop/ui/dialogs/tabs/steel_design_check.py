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
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage

import io
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

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

# 8 design checks from the screenshot - 2 columns - 4 rows
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

# HTML equation strings for each card (rendered via Qt.RichText)
_RENDER_MAP = {
    "flexure": {
        "eq": (
            "<i>M<sub>d</sub></i> &le; <i>M<sub>r</sub></i><br>"
            "<i>M<sub>r</sub></i> = <i>&beta;<sub>b</sub></i> &middot; "
            "<i>Z<sub>p</sub></i> &middot; <i>f<sub>y</sub></i> / <i>&gamma;<sub>m</sub></i>"
        ),
        "dem_pfx": "<i>M<sub>d</sub></i>",
        "cap_pfx": "<i>M<sub>r</sub></i>",
        "unit": "kNm",
    },
    "shear": {
        "eq": (
            "<i>V<sub>d</sub></i> &le; <i>V<sub>r</sub></i><br>"
            "<i>V<sub>r</sub></i> = <i>A<sub>v</sub></i> &middot; <i>f<sub>y</sub></i> / "
            "(&radic;3 &middot; <i>&gamma;<sub>m</sub></i>)"
        ),
        "dem_pfx": "<i>V<sub>d</sub></i>",
        "cap_pfx": "<i>V<sub>r</sub></i>",
        "unit": "kN",
    },
    "interaction": {
        "eq": (
            "<i>M<sub>d</sub></i> / (<i>&beta;<sub>b</sub></i> &middot; <i>Z<sub>p</sub></i> &middot; "
            "<i>f<sub>y</sub></i> / <i>&gamma;<sub>m</sub></i>) + "
            "<i>V<sub>d</sub></i> / (<i>A<sub>v</sub></i> &middot; <i>f<sub>y</sub></i> / "
            "(&radic;3 &middot; <i>&gamma;<sub>m</sub></i>)) &le; 1.0"
        ),
        "unit": "",
    },
    "ltb": {
        "eq": (
            "<i>M<sub>d</sub></i> &le; <i>M<sub>cr</sub></i><br>"
            "<i>M<sub>cr</sub></i> &approx; (&pi;&sup2; &middot; <i>E</i> &middot; "
            "<i>I<sub>y</sub></i>) / <i>L<sub>LTB</sub></i>&sup2;"
        ),
        "dem_pfx": "<i>M<sub>d</sub></i>",
        "cap_pfx": "<i>M<sub>cr</sub></i>",
        "unit": "kNm",
    },
    "shear_long_trans": {
        # IRC 22:2015 Cl.606.4.1 - Longitudinal shear flow at steel-concrete interface.
        # Demand  : VL (N/mm) - longitudinal shear flow
        # Capacity: n_studs * Qu / spacing (N/mm) - stud resistance per unit length
        "eq": (
            "<i>V<sub>L</sub></i> &le; <i>n</i> &middot; <i>Q<sub>u</sub></i> / <i>s</i><br>"
            "<i>V<sub>L</sub></i> = <i>V<sub>d</sub></i> &middot; <i>A<sub>ec</sub></i>"
            " &middot; <i>Y</i> / <i>I<sub>c</sub></i><br>"
            "<i>Q<sub>u</sub></i> = min(0.8<i>f<sub>u</sub>A</i>, "
            "0.29&alpha;<i>d</i>&sup2;"
            "&radic;(<i>f<sub>ck</sub>E<sub>cm</sub></i>)) / <i>&gamma;<sub>v</sub></i>"
        ),
        "dem_pfx": "<i>V<sub>L</sub></i>",
        "cap_pfx": "<i>nQ<sub>u</sub>/s</i>",
        "unit": "N/mm",
    },
    "fatigue": {
        "eq": (
            "&Delta;<i>&sigma;</i> &le; &Delta;<i>&sigma;<sub>allowable</sub></i><br>"
            "&Delta;<i>&sigma;<sub>allowable</sub></i> = &Delta;<i>&sigma;<sub>c</sub></i> / "
            "<i>&gamma;<sub>mf</sub></i>"
        ),
        "dem_pfx": "&Delta;<i>&sigma;</i>",
        "cap_pfx": "&Delta;<i>&sigma;<sub>allowable</sub></i>",
        "unit": "MPa",
    },
    "stress": {
        "eq": (
            "<i>&sigma;</i> = <i>M<sub>d</sub></i> / <i>Z</i><br>"
            "<i>&sigma;</i> &le; <i>f<sub>y</sub></i> / <i>&gamma;<sub>m</sub></i>"
        ),
        "dem_pfx": "<i>&sigma;</i>",
        "cap_pfx": "<i>f<sub>y</sub> / &gamma;<sub>m</sub></i>",
        "unit": "MPa",
    },
    "deflection": {
        "eq": (
            "<i>&delta;</i> &le; <i>L</i> / <i>x</i><br>"
            "(Default <i>x</i> = 600)"
        ),
        "dem_pfx": "<i>&delta;</i>",
        "cap_pfx": "<i>L / x</i>",
        "unit": "mm",
    },
}


# ---------------------------------------------------------------------------
# Matplotlib mathtext strings — one list per check key.
# Each string in the list becomes one rendered line in the equation box.
# Syntax: matplotlib mathtext (large subset of AMS LaTeX).
# ---------------------------------------------------------------------------
_MATHTEXT_MAP: dict[str, list[str]] = {
    "flexure": [
        r"$M_d \leq M_r$",
        r"$M_r = \beta_b \cdot Z_p \cdot f_y \;/\; \gamma_m$",
    ],
    "shear": [
        r"$V_d \leq V_r$",
        r"$V_r = \dfrac{A_v \cdot f_y}{\sqrt{3} \cdot \gamma_m}$",
    ],
    "interaction": [
        r"$\dfrac{M_d}{\beta_b Z_p f_y / \gamma_m}"
        r" + \dfrac{V_d}{A_v f_y / (\sqrt{3}\,\gamma_m)} \leq 1.0$",
    ],
    "ltb": [
        r"$M_d \leq M_{cr}$",
        r"$M_{cr} \approx \dfrac{\pi^2 E \, I_y}{L_{LTB}^{\,2}}$",
    ],
    "shear_long_trans": [
        r"$V_L \leq n \cdot Q_u \;/\; s$",
        r"$V_L = V_d \cdot A_{ec} \cdot Y \;/\; I_c$",
        r"$Q_u = \min\!\left(0.8\,f_u A,\;"
        r"0.29\,\alpha\,d^2\sqrt{f_{ck}\,E_{cm}}\right)/\gamma_v$",
    ],
    "fatigue": [
        r"$\Delta\sigma \leq \Delta\sigma_{allowable}$",
        r"$\Delta\sigma_{allowable} = \Delta\sigma_C \;/\; \gamma_{mf}$",
    ],
    "stress": [
        r"$\sigma = M_d \;/\; Z$",
        r"$\sigma \leq f_y \;/\; \gamma_m$",
    ],
    "deflection": [
        r"$\delta \leq L \;/\; x$",
        r"$(\mathrm{Default}\; x = 600)$",
    ],
}

def _render_mathtext_pixmap(
    lines: list[str],
    *,
    font_size: float = 9,
    dpi: int = 110,
    text_color: str = "#2E3B4E",
    bg_color: str = "#F8F9FA",
    h_pad_in: float = 0.12,
    v_pad_in: float = 0.10,
    line_gap_in: float = 0.32,
) -> QPixmap:
    """
    Render a list of matplotlib mathtext strings into a single QPixmap.

    Lines are stacked vertically with even spacing. The figure is sized to
    fit the content tightly; the caller is responsible for placing the pixmap
    inside a QLabel that provides the grey background frame.

    Parameters
    ----------
    lines       : list of mathtext strings, each wrapped in ``$...$``
    font_size   : points; 11.5 matches the surrounding 13 px UI font at 96 dpi
    dpi         : dots per inch for rasterisation
    text_color  : hex colour string matching the existing equation box style
    bg_color    : figure background; should match the QLabel background colour
    h_pad_in    : left/right margin in inches
    v_pad_in    : top/bottom margin in inches
    line_gap_in : vertical gap between lines in inches

    Returns
    -------
    QPixmap — transparent if rendering fails (caller falls back to HTML).

    Raises
    ------
    Never raises. Returns an empty QPixmap on any error.
    """
    if not lines:
        return QPixmap()

    n = len(lines)
    # Estimate figure height: n lines + (n-1) gaps + top/bottom padding
    fig_h = n * line_gap_in + (n - 1) * (line_gap_in * 0.15) + 2 * v_pad_in
    # Width will be determined by bbox_inches="tight"; start with a sensible default
    fig_w = 4.8

    fig = Figure(figsize=(fig_w, fig_h), dpi=dpi, facecolor=bg_color)
    fig.patch.set_facecolor(bg_color)

    try:
        for i, expr in enumerate(lines):
            # y position: distribute evenly from top (1.0) to bottom (0.0)
            y = 1.0 - (i + 0.5) / n
            fig.text(
                0.5, y,
                expr,
                ha="center",
                va="center",
                fontsize=font_size,
                color=text_color,
                usetex=False,          # matplotlib mathtext, NOT system LaTeX
            )

        canvas = FigureCanvasAgg(fig)
        canvas.draw()

        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            dpi=dpi,
            bbox_inches="tight",
            facecolor=bg_color,
            pad_inches=v_pad_in,
        )
        buf.seek(0)
        data = buf.read()

    except Exception:
        return QPixmap()
    finally:
        import matplotlib.pyplot as _plt
        _plt.close(fig)       # prevent memory accumulation across 8 cards

    pixmap = QPixmap()
    if not pixmap.loadFromData(data, "PNG"):
        return QPixmap()
    return pixmap


# ---------------------------------------------------------------------------
# Badge style definitions
# ---------------------------------------------------------------------------

_BADGE_STYLES = {
    "pass":    ("PASS", "#1a7a4a", "#d4edda"),
    "fail":    ("FAIL", "#8b0000", "#f8d7da"),
    "neutral": ("",     "#444444", "#eeeeee"),
}


# ---------------------------------------------------------------------------
# Inline widgets - UtilizationBar and StatusBadge
# ---------------------------------------------------------------------------

class UtilizationBar(QWidget):
    """Horizontal fill-bar showing demand/capacity ratio (0-1+)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(10)
        self.setStyleSheet("background: #e0e0e0; border-radius: 5px;")
        self._fill = QWidget(self)
        self._fill.setFixedHeight(10)
        self._ratio = 0.0
        self._fill.resize(0, 10)
        self._update()

    def set_ratio(self, ratio: float):
        self._ratio = ratio
        self._update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update()

    def _update(self):
        fill_w = int(min(self._ratio, 1.0) * self.width())
        color = "#28a745" if self._ratio <= 1.0 else "#dc3545"
        self._fill.setFixedWidth(max(0, fill_w))
        self._fill.setStyleSheet(f"background: {color}; border-radius: 5px;")


class StatusBadge(QLabel):
    """Small PASS / FAIL label badge with coloured background."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 22)
        self.setAlignment(Qt.AlignCenter)
        self.set_neutral()

    def _apply(self, state):
        text, fg, bg = _BADGE_STYLES[state]
        self.setText(text)
        self.setStyleSheet(
            f"color: {fg}; background: {bg};"
            "font-weight: bold; font-size: 10px; border-radius: 6px;"
        )

    def set_pass(self):
        self._apply("pass")

    def set_fail(self):
        self._apply("fail")

    def set_neutral(self):
        self._apply("neutral")


# ---------------------------------------------------------------------------
# Main tab widget
# ---------------------------------------------------------------------------

class SteelDesignCheckTab(QWidget):
    """
    Design Check tab for the Steel Design dialog.

    Displays eight IRC code compliance check cards in a two-column grid.
    Each card shows: bold title, styled equation box, computed demand/capacity
    values, coloured DCR label, utilization progress bar, and PASS/FAIL badge.

    A summary bar at the top shows aggregate pass/fail counts.

    Public API
    ----------
    populate_from_results(demand, capacity, engine)
        Populate all 8 cards from the IRC 22:2015 pipeline output.
    set_check_result(key, text)
        Write a result string into the named check card.
    clear_results()
        Clear all check output areas.
    set_girder_count(count)
        Repopulate the Member ID combo.
    load_data(cad_state)
        Restore check results from a cad_state snapshot.
    """

    def __init__(self, parent=None):
        # Widget tracking dicts - one entry per card key
        self.check_eq_labels  = {}   # key - equation QLabel
        self.check_val_labels = {}   # key - demand/capacity QLabel
        self.check_dcr_labels = {}   # key - DCR QLabel
        self.check_bars       = {}   # key - UtilizationBar
        self.check_badges     = {}   # key - StatusBadge

        self.summary_passed_label = None
        self.summary_failed_label = None
        self.summary_badge        = None
        self.design_results       = []

        super().__init__(parent)

        # White background - consistent with other tabs.
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

        # - TOP BAR: Member ID + Load Combination in a bordered card -
        container_layout.addWidget(self._build_top_bar())

        # - SUMMARY BAR: pass/fail counts + overall badge -
        container_layout.addWidget(self._build_summary_bar())

        # - CHECK CARDS GRID: 2 columns -
        container_layout.addLayout(self._build_checks_grid())

        container_layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

    # ---------------------------------------------------------------------------
    # SUMMARY BAR
    # ---------------------------------------------------------------------------
    def _build_summary_bar(self):
        """Build the Checks / Passed / Failed summary row with an overall badge."""
        frame = QFrame()
        frame.setObjectName("summaryFrame")
        frame.setStyleSheet(
            "QFrame#summaryFrame {"
            "background: #f0f4e8; border: 1px solid #90AF13;"
            "border-radius: 6px; padding: 4px;"
            "}"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(16)

        _SUMMARY_STYLE = (
            "font-size: 11px; font-weight: 600; color: #2b2b2b; "
            "background: transparent; border: none;"
        )

        label = QLabel("Checks: 8")
        label.setStyleSheet(_SUMMARY_STYLE)
        layout.addWidget(label)

        self.summary_passed_label = QLabel("Passed: \u2014")
        self.summary_passed_label.setStyleSheet(_SUMMARY_STYLE)
        layout.addWidget(self.summary_passed_label)

        self.summary_failed_label = QLabel("Failed: \u2014")
        self.summary_failed_label.setStyleSheet(_SUMMARY_STYLE)
        layout.addWidget(self.summary_failed_label)

        layout.addStretch()

        self.summary_badge = StatusBadge()
        layout.addWidget(self.summary_badge)

        return frame

# ---------------------------------------------------------------------------
    # HELPERS - exact copy from steel_design_details.py
# ---------------------------------------------------------------------------

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

    def _build_top_bar(self):
        """
        Build the Member ID and Load Combination read-only mirror row.

        Returns a transparent container widget holding two equal-width individual
        card frames - one per combo - matching the 'Component' / 'Display Location'
        card layout used in the Analysis Results tab:
          - each card: white bg, 1 px solid #b0b0b0, border-radius 6 px
          - bold section title at the top, combo below
          - equal horizontal stretch so both cards share the full width

        The combos are intentionally disabled. The Output Dock is the only place
        where the user changes member / load combination; sync_from_output_dock()
        writes new selections in here programmatically.
        """
        # Shared card stylesheet - identical to comp_card / disp_card in Analysis tab.
        _CARD_STYLE = (
            "QFrame#controlCard {"
            "  background-color: white;"
            "  border: 1px solid #b0b0b0;"
            "  border-radius: 6px;"
            "}"
            "QLabel {"
            "  border: none;"
            "  background: transparent;"
            "}"
        )
        _TITLE_STYLE = (
            "font-size: 13px; color: #2B2B2B; font-weight: bold;"
            " background: transparent; border: none;"
        )

        # Disabled combo: black border / #f4f4f4 bg, no arrow - non-interactive read-only.
        self._DISABLED_COMBO_STYLE = (
            "QComboBox {"
            "  padding: 1px 7px;"
            "  border: 1px solid black;"
            "  border-radius: 5px;"
            "  background-color: #f4f4f4;"
            "  color: #555555;"
            "  font-size: 11px;"
            "  min-height: 28px;"
            "}"
            "QComboBox::drop-down { border: none; width: 0px; }"
            "QComboBox::down-arrow { width: 0px; height: 0px; image: none; }"
        )

        # Transparent row container - no border of its own.
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(16)   # gap between the two cards (matches controls_row spacing)

        # - Member ID card -
        member_card = QFrame()
        member_card.setObjectName("controlCard")
        member_card.setStyleSheet(_CARD_STYLE)
        member_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        mc_layout = QVBoxLayout(member_card)
        mc_layout.setContentsMargins(23, 10, 14, 12)
        mc_layout.setSpacing(4)

        member_title = QLabel("Member ID")
        member_title.setStyleSheet(_TITLE_STYLE)
        mc_layout.addWidget(member_title)

        self.member_combo = NoScrollComboBox()
        self.member_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.member_combo.setFixedHeight(28)
        self.member_combo.addItems(["All", "Girder 1", "Girder 2"])
        self.member_combo.setEnabled(False)
        self.member_combo.setStyleSheet(self._DISABLED_COMBO_STYLE)
        self.member_combo.setToolTip(
            "Change the member in the Output Dock \u2014 this field mirrors that selection."
        )
        mc_layout.addWidget(self.member_combo)

        # - Load Combination card -
        load_card = QFrame()
        load_card.setObjectName("controlCard")
        load_card.setStyleSheet(_CARD_STYLE)
        load_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lc_layout = QVBoxLayout(load_card)
        lc_layout.setContentsMargins(23, 10, 14, 12)
        lc_layout.setSpacing(4)

        load_title = QLabel("Load Combination")
        load_title.setStyleSheet(_TITLE_STYLE)
        lc_layout.addWidget(load_title)

        self.load_combo = NoScrollComboBox()
        self.load_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.load_combo.setFixedHeight(28)
        self.load_combo.addItems(LOAD_COMBINATIONS)
        self.load_combo.setEnabled(False)
        self.load_combo.setStyleSheet(self._DISABLED_COMBO_STYLE)
        self.load_combo.setToolTip(
            "Change the load combination in the Output Dock \u2014 this field mirrors that selection."
        )
        lc_layout.addWidget(self.load_combo)

        row.addWidget(member_card, 1)   # stretch=1: both cards share width equally
        row.addWidget(load_card,   1)

        return container

    # ---------------------------------------------------------------------------
    # CHECK CARDS GRID
    # ---------------------------------------------------------------------------
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

    def _build_check_card(self, key: str, title: str) -> QFrame:
        """
        Single check card with five layers:
          1. Bold title
          2. Styled equation box (HTML rich text)
          3. Computed demand / capacity value lines
          4. Coloured DCR label + utilization progress bar
          5. PASS / FAIL status badge
        """
        card = QFrame()
        card.setObjectName("checkCard")
        card.setStyleSheet("""
            QFrame#checkCard {
                background-color: white;
                border: 1px solid #CFCFCF;
                border-radius: 8px;
            }
        """)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(8)

        # - 1. Title -
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #000; "
            "background: transparent; border: none;"
        )
        title_lbl.setWordWrap(True)
        card_layout.addWidget(title_lbl)

        # - 2. Equation box (mathtext pixmap or HTML fallback) -
        eq_lbl = QLabel()
        eq_lbl.setAlignment(Qt.AlignCenter)
        eq_lbl.setStyleSheet(
            "background-color: #F8F9FA; border: 1px solid #E4E7EB; "
            "border-radius: 4px; padding: 6px;"
        )

        math_lines = _MATHTEXT_MAP.get(key, [])
        _pixmap_set = False

        if math_lines:
            try:
                pixmap = _render_mathtext_pixmap(math_lines)
                if not pixmap.isNull():
                    eq_lbl.setPixmap(pixmap)
                    _pixmap_set = True
            except Exception:
                pass

        if not _pixmap_set:
            # Graceful fallback: render using original HTML if mathtext fails
            eq_lbl.setTextFormat(Qt.RichText)
            eq_lbl.setWordWrap(True)
            eq_lbl.setStyleSheet(
                "font-family: 'Cambria Math', 'Times New Roman', serif; "
                "font-size: 13px; color: #2E3B4E; "
                "background-color: #F8F9FA; border: 1px solid #E4E7EB; "
                "border-radius: 4px; padding: 6px;"
            )
            eq_text = _RENDER_MAP.get(key, {}).get("eq", "")
            eq_lbl.setText(eq_text)

        card_layout.addWidget(eq_lbl)
        self.check_eq_labels[key] = eq_lbl

        # - 3. Value lines (demand / capacity) -
        val_lbl = QLabel()
        val_lbl.setTextFormat(Qt.RichText)
        val_lbl.setWordWrap(True)
        val_lbl.setStyleSheet(
            "font-size: 13px; color: #222; "
            "background: transparent; border: none; padding-top: 2px;"
        )
        card_layout.addWidget(val_lbl)
        self.check_val_labels[key] = val_lbl

        # - 4. DCR label -
        dcr_lbl = QLabel()
        dcr_lbl.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #555; "
            "background: transparent; border: none;"
        )
        dcr_lbl.setToolTip("Utilization Ratio = Demand / Capacity  (UR < 1.0 - PASS)")
        card_layout.addWidget(dcr_lbl)
        self.check_dcr_labels[key] = dcr_lbl

        # - 5. Utilization bar -
        bar = UtilizationBar()
        card_layout.addWidget(bar)
        self.check_bars[key] = bar

        # - 6. Status badge -
        badge = StatusBadge()
        card_layout.addWidget(badge, alignment=Qt.AlignLeft)
        self.check_badges[key] = badge

        return card

    # ---------------------------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------------------------
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

    def set_check_result(self, key: str, text: str) -> None:
        """Write plain-text result into the value label of the named card."""
        lbl = self.check_val_labels.get(key)
        if lbl is not None:
            lbl.setTextFormat(Qt.PlainText)
            lbl.setText(text)

    def clear_results(self) -> None:
        """Reset all eight cards to their initial empty state."""
        for key in self.check_badges:
            lbl = self.check_val_labels.get(key)
            if lbl:
                lbl.setText("")
            dcr = self.check_dcr_labels.get(key)
            if dcr:
                dcr.setText("")
                dcr.setStyleSheet(
                    "font-size: 14px; font-weight: bold; color: #555; "
                    "background: transparent; border: none;"
                )
            bar = self.check_bars.get(key)
            if bar:
                bar.set_ratio(0)
            badge = self.check_badges.get(key)
            if badge:
                badge.set_neutral()
        self.design_results = []
        self._refresh_summary()

    def populate_from_results(
        self,
        demand: object,
        capacity: object,
        engine: object,
    ) -> None:
        """
        Populate all 8 design-check cards from IRC 22:2015 pipeline output.

        Called by steel_design.py ``_run_design_checks()``.
        Each card is populated independently - a failure in one card never
        prevents the others from rendering.

        Parameters
        ----------
        demand   : DemandEnvelope
        capacity : CapacityResults  (from IRC22CapacityCalculator.compute_all())
        engine   : DCREngine        (run_all_checks() already called)
        """
        self.clear_results()

        by_id: dict[int, object] = {chk.check_id: chk for chk in engine.checks}

        def _classify(dcr: float) -> bool:
            return dcr < 1.0

        # Build a result dict for each card via the DCREngine checks
        results_by_key: dict[str, dict] = {}

        # - 1. Flexure (check_id=1) -
        try:
            c = by_id[1]
            results_by_key["flexure"] = {
                "demand": c.demand, "capacity": c.capacity,
                "ratio": c.dcr, "passed": c.status != "FAIL",
            }
        except Exception:
            pass

        # - 2. Shear (check_id=2) -
        try:
            c = by_id[2]
            results_by_key["shear"] = {
                "demand": c.demand, "capacity": c.capacity,
                "ratio": c.dcr, "passed": c.status != "FAIL",
            }
        except Exception:
            pass

        # - 3. Interaction (check_id=3) -
        try:
            c = by_id[3]
            results_by_key["interaction"] = {
                "demand": c.demand, "capacity": c.capacity,
                "ratio": c.dcr, "passed": c.status != "FAIL",
            }
        except Exception:
            pass

        # - 4. LTB (check_id=4) -
        try:
            c = by_id[4]
            results_by_key["ltb"] = {
                "demand": c.demand, "capacity": c.capacity,
                "ratio": c.dcr, "passed": c.status != "FAIL",
            }
        except Exception:
            pass

        # - 5. Deflection - worst of Live (id=5) and Total (id=6) -
        try:
            worst = None
            for cid in (5, 6):
                c = by_id.get(cid)
                if c and (worst is None or c.dcr > worst.dcr):
                    worst = c
            if worst:
                results_by_key["deflection"] = {
                    "demand": worst.demand, "capacity": worst.capacity,
                    "ratio": worst.dcr, "passed": worst.status != "FAIL",
                }
        except Exception:
            pass

        # - 6. Fatigue - worst of Normal (id=7) and Shear (id=8) -
        try:
            worst = None
            for cid in (7, 8):
                c = by_id.get(cid)
                if c and (worst is None or c.dcr > worst.dcr):
                    worst = c
            if worst:
                results_by_key["fatigue"] = {
                    "demand": worst.demand, "capacity": worst.capacity,
                    "ratio": worst.dcr, "passed": worst.status != "FAIL",
                }
        except Exception:
            pass

        # - 7. Stress Limitation (Cl.604.3.1) -
        # - 8. Resistance to Longitudinal and Transverse Shear (Cl.606.4.1) -
        #
        # Neither check has a corresponding check_id in DCREngine (only IDs
        # 1-8 are emitted).  These cards intentionally remain blank - showing
        # their governing equation only - until the engine adds the checks.
        # This matches the Output Dock which shows 0 % for both.

        # - Apply results to card widgets -
        self.design_results = list(results_by_key.values())

        for key, res in results_by_key.items():
            self._apply_card_result(key, res)

        self._refresh_summary()

    # ---------------------------------------------------------------------------
    # CARD RENDERING HELPERS
    # ---------------------------------------------------------------------------
    def _apply_card_result(self, key: str, res: dict) -> None:
        """Populate a single card's value/DCR/bar/badge widgets from a result dict."""
        if key not in self.check_val_labels:
            return

        demand   = res.get("demand",   0.0)
        capacity = res.get("capacity", 0.0)
        ratio    = res.get("ratio",    0.0)
        passed   = res.get("passed",   False)

        rm       = _RENDER_MAP.get(key, {})
        unit     = rm.get("unit", "")
        unit_str = f" {unit}" if unit else ""

        # Build value text (demand / capacity lines)
        if key == "interaction":
            val_text = (
                f"<i>M<sub>d</sub></i> / <i>M<sub>r</sub></i> + "
                f"<i>V<sub>d</sub></i> / <i>V<sub>r</sub></i> = {demand:.2f}"
            )
        else:
            dem_pfx = rm.get("dem_pfx", "Demand")
            cap_pfx = rm.get("cap_pfx", "Capacity")
            val_text = (
                f"{dem_pfx} = {demand:.2f}{unit_str}<br>"
                f"{cap_pfx} = {capacity:.2f}{unit_str}"
            )

        dcr_text  = f"Utilization Ratio = {ratio:.2f}"
        dcr_color = "#388E3C" if passed else "#D32F2F"

        # Set value label
        val_lbl = self.check_val_labels[key]
        val_lbl.setTextFormat(Qt.RichText)
        val_lbl.setText(val_text)

        # Set DCR label
        dcr_lbl = self.check_dcr_labels.get(key)
        if dcr_lbl:
            dcr_lbl.setText(dcr_text)
            dcr_lbl.setStyleSheet(
                f"font-size: 14px; font-weight: bold; color: {dcr_color}; "
                "background: transparent; border: none;"
            )

        # Set utilization bar
        bar = self.check_bars.get(key)
        if bar:
            bar.set_ratio(ratio)

        # Set badge
        badge = self.check_badges.get(key)
        if badge:
            badge.set_pass() if passed else badge.set_fail()

    def _refresh_summary(self) -> None:
        """Update the summary bar pass/fail counts and overall badge."""
        passed = sum(1 for r in self.design_results if r.get("passed"))
        failed = len(self.design_results) - passed
        if self.summary_passed_label:
            self.summary_passed_label.setText(f"Passed: {passed}")
        if self.summary_failed_label:
            self.summary_failed_label.setText(f"Failed: {failed}")
        if self.summary_badge:
            if not self.design_results:
                self.summary_badge.set_neutral()
            elif failed == 0:
                self.summary_badge.set_pass()
            else:
                self.summary_badge.set_fail()
