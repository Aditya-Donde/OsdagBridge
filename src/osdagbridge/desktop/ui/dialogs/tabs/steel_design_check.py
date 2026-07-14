from __future__ import annotations

import logging
import io
import re

def _to_display_style(latex: str) -> str:
    r"""Replace \frac with \dfrac so num/denom render at full glyph size."""
    return latex.replace(r"\frac", r"\dfrac")

import matplotlib
matplotlib.use("Agg")
import matplotlib.figure as mfigure
import matplotlib.mathtext as mathtext

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, QByteArray
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtSvg import QSvgRenderer

from osdagbridge.desktop.ui.utils.styled_scroll_area import StyledScrollArea
from osdagbridge.desktop.ui.utils.custom_widgets import PercentBarWidget
from osdagbridge.core.utils.common import (
    KEY_CHECK_FLEXURE, KEY_CHECK_SHEAR, KEY_CHECK_INTERACTION, KEY_CHECK_LTB,
    KEY_CHECK_SHEAR_LONG_TRANS, KEY_CHECK_FATIGUE, KEY_CHECK_STRESS, KEY_CHECK_DEFLECTION,
    DESIGN_CHECK_ORDER, DESIGN_CHECK_TITLES, DESIGN_CHECK_UNITS,
    DESIGN_CHECK_DEM_PFX, DESIGN_CHECK_CAP_PFX,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DESIGN_CHECKS = [(k, DESIGN_CHECK_TITLES[k]) for k in DESIGN_CHECK_ORDER]

# ---------------------------------------------------------------------------
# LaTeX equation strings and sizing constants
# ---------------------------------------------------------------------------

_LINE_HEIGHT_SIMPLE = 38
_LINE_HEIGHT_FRAC   = 70

_FONTSIZE_SIMPLE = 16
_FONTSIZE_FRAC   = 66
# (check_key) → tuple of (latex_string, display_width_px, is_frac)
# is_frac=True for equations containing \frac or complex \sqrt
_EQ_LATEX: dict[str, tuple[tuple[str, int, bool], ...]] = {
    KEY_CHECK_FLEXURE: (
        (r"$M_d \leq M_r = M_p$",                                   110, False),
        (r"$\mathrm{(IRC\ 22\ Annex\ I,\ Table\ I.1)}$",            220, False),
    ),
    KEY_CHECK_SHEAR: (
        (r"$V_d \leq V_r$",                                          80, False),
        (r"$V_r = \frac{A_v \cdot f_y}{\sqrt{3} \cdot \gamma_{m0}}$", 140, True),
    ),
    KEY_CHECK_INTERACTION: (
        (r"$\frac{M_d}{\beta_b Z_p f_y/\gamma_{m0}} + \frac{V_d}{A_v f_y/(\sqrt{3}\,\gamma_{m0})} \leq 1.0$", 300, True),
    ),
    KEY_CHECK_LTB: (
        (r"$M_d \leq M_{cr}$", 80, False),
        (r"$M_{cr}=\sqrt{\left(\frac{\pi^{2}EI_y}{L_{LT}^{2}}\right)\left(GI_t+\frac{\pi^{2}EI_w}{L_{LT}^{2}}\right)}$", 280, True),
    ),
    KEY_CHECK_SHEAR_LONG_TRANS: (
        (r"$V_L \leq n \cdot Q_u / s$", 100, False),
        (r"$V_L = V_d \cdot A_{ec} \cdot Y / I_c$", 140, False),
        (r"$Q_u=\min\left(\frac{0.8\,f_u\,A}{\gamma_v},\;\frac{0.29\,\alpha\,d^{2}\sqrt{f_{ck}E_{cm}}}{\gamma_v}\right)$", 400, True),
    ),
    KEY_CHECK_FATIGUE: (
        (r"$\Delta\sigma \leq \Delta\sigma_{allowable}$",            160, False),
        (r"$\Delta\sigma_{allowable} = \Delta\sigma_C / \gamma_{mf}$", 180, False),
    ),
    KEY_CHECK_STRESS: (
        (r"$\sigma = M_d / Z$",                                      80, False),
        (r"$\sigma \leq f_y / \gamma_{m0}$",                        100, False),
    ),
    KEY_CHECK_DEFLECTION: (
        (r"$\delta \leq L / x$",                                     80, False),
        (r"$\mathrm{(Default}\ x = 600\mathrm{)}$",                 160, False),
    ),
}
def _get_shear_latex(governing_method: str):
    """
    Return the governing shear equations for the Design Check panel.
    """

    if governing_method == "post_critical":
        return (
            (r"$V_d \leq V_{cr}$", 90, False),
            (r"$V_{cr}=A_v \cdot \tau_b$", 140, False),
        )

    elif governing_method == "tension_field":
        return (
            (r"$V_d \leq V_{tf}$", 90, False),
            (r"$V_n=V_{tf}$", 120, False),
        )

    # Default → Plastic Shear Resistance
    return (
        (r"$V_d \leq V_p$", 90, False),
        (r"$V_p=\frac{A_v \cdot f_y}{\sqrt{3}\,\gamma_{m0}}$", 170, True),
    )

# ---------------------------------------------------------------------------
# Flexure card — Mp equation varies with the position of the Plastic Neutral
# Axis (PNA). Transcribed verbatim from IRC:22-2015 Annexure I, Table I.1
# ("Positive Moment Capacity of Composite Section with full Shear
# Interaction") — the three case rows, using the table's own symbols:
#   As, fy, gamma_m  — steel area / yield stress / material safety factor
#   dc, ds           — centroid-to-centroid distance / slab depth
#   beff, bf, tf, tw — effective slab width / top flange width & thickness /
#                      web thickness ; Af = bf.tf
#   xu, lambda       — PNA depth from top of concrete / stress-block factor
# The "a" coefficient (a = (fy/gamma_m) / [(alpha_cc/gamma_c).eta.lambda.fck],
# Annex eq. I.1) feeds the table's xu column and is omitted from the Mp
# lines below to keep each case to one card-height row, exactly as the Mp
# column of the table itself has no "a" term.
# ---------------------------------------------------------------------------

_EQ_FLEXURE_CASE1_SLAB = (
    r"$M_p=\frac{A_sf_y\left(d_c+0.5d_s-\frac{\lambda x_u}{2}\right)}{\gamma_m},"
    r"\ \ x_u=\frac{aA_s}{b_{eff}}$"
)
_EQ_FLEXURE_CASE2_TOP_FLANGE = (
    r"$M_p=\frac{f_y\left[A_s\{d_c+0.5d_s(1-\lambda)\}"
    r"-b_f(x_u-d_s)\{x_u+(1-\lambda)d_s\}\right]}{\gamma_m}$"
)
_EQ_FLEXURE_CASE3_WEB_ROW1 = (
    r"$M_p=\frac{f_y}{\gamma_m}[A_s\{d_c+0.5d_s(1-\lambda)\}"
    r"-2A_f\{0.5t_f+(1-\lambda/2)d_s\}$"
)
_EQ_FLEXURE_CASE3_WEB_ROW2 = (
    r"$-t_w(x_u-d_s-t_f)\{(x_u-d_s)+(1-\lambda)d_s+t_f\}]$"
)

_PNA_LABEL_LATEX: dict[str, str] = {
    "slab":          r"$\mathrm{Case\ 1:\ PNA\ in\ Slab}$",
    "top_flange":    r"$\mathrm{Case\ 2:\ PNA\ in\ Top\ Flange}$",
    "web":           r"$\mathrm{Case\ 3:\ PNA\ in\ Web}$",
}


def _interaction_eq_lines(check_id: int | None, is_high_shear: bool) -> tuple[tuple[str, int, bool], ...]:
    """Pick the interaction equation matching the check that actually governed.

    Cl.603.3.3.3: the shear term never appears as an additive fraction. Instead,
    when Vu > 0.6Vd, the bending capacity itself is reduced to Mdv before the
    plain M-V (or M-N) check is run; when Vu <= 0.6Vd, no reduction applies and
    Mdv == Md. check_id 4 (M-N) only exists at all when axial force is present.
    """
    if check_id == 4:
        return (
            (r"$\frac{N_u}{N_{Rd}} + \frac{M_u}{M_{dv}} \leq 1.0$", 220, True),
        )
    if is_high_shear:
        return (
            (r"$M_u \leq M_{dv}$", 110, False),
            (r"$M_{dv}=M_d-\beta(M_d-M_{fd})\ \ \mathrm{(Cl.\ 603.3.3.3,\ high\ shear)}$", 360, False),
        )
    return (
        (r"$M_u \leq M_{dv}=M_d\ \ \mathrm{(Cl.\ 603.3.3.3,\ no\ shear\ reduction)}$", 320, False),
    )


def _flexure_eq_lines(pna_location: str) -> tuple[tuple[str, int, bool], ...]:
    """Pick the Mp equation matching the computed PNA location.

    Cases 1-3 map straight onto IRC:22-2015 Annexure I Table I.1. The code's
    "bottom_flange" outcome (PNA below the web) falls outside the table's
    three rows, so it keeps the neutral placeholder rather than guessing an
    unpublished fourth formula.
    """
    check_line = (r"$M_d \leq M_r = M_p$", 110, False)

    if pna_location == "slab":
        lines = [check_line, (_EQ_FLEXURE_CASE1_SLAB, 260, True)]
    elif pna_location == "top_flange":
        lines = [check_line, (_EQ_FLEXURE_CASE2_TOP_FLANGE, 300, False)]
    elif pna_location == "web":
        lines = [
            check_line,
            (_EQ_FLEXURE_CASE3_WEB_ROW1, 300, False),
            (_EQ_FLEXURE_CASE3_WEB_ROW2, 300, False),
        ]
    else:
        return _EQ_LATEX[KEY_CHECK_FLEXURE]

    label = _PNA_LABEL_LATEX.get(pna_location)
    if label:
        lines.append((label, 200, False))
    return tuple(lines)

# ---------------------------------------------------------------------------
# LaTeX → SVG via matplotlib mathtext
# Pure vector paths — no pixels, no temp files, no pdflatex
# ---------------------------------------------------------------------------

_SVG_CACHE: dict[tuple[str, int, int], bytes] = {}  # key is now (latex, display_width, fontsize)

def _latex_to_svg(latex: str, display_width: int = 260, fontsize: int = 14) -> bytes:
    cache_key = (latex, display_width, fontsize)
    if cache_key in _SVG_CACHE:
        return _SVG_CACHE[cache_key]

    svg_bytes = b""
    try:
        dpi  = 150
        pad  = 6
        prop = matplotlib.font_manager.FontProperties(size=fontsize)
        parser = mathtext.MathTextParser("path")

        width_pt, height_pt, *_ = parser.parse(latex, dpi=72, prop=prop)

        fig_w = (width_pt  + pad * 2) / 72
        fig_h = (height_pt + pad * 2) / 72

        fig = mfigure.Figure(figsize=(fig_w, fig_h), dpi=dpi)
        fig.patch.set_visible(False)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()
        ax.set_xlim(0, fig_w * dpi)
        ax.set_ylim(0, fig_h * dpi)
        ax.text(
            fig_w * dpi / 2, fig_h * dpi / 2, latex,
            fontsize=fontsize, color="#1a1a1a",
            ha="center", va="center",
        )

        buf = io.BytesIO()
        fig.savefig(buf, format="svg", transparent=True,
                    bbox_inches="tight", pad_inches=pad / 72)
        matplotlib.pyplot.close(fig)
        svg_bytes = buf.getvalue()

    except Exception:
        logger.exception("mathtext SVG render failed for: %s", latex[:80])
        svg_bytes = b'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="30"></svg>'

    _SVG_CACHE[cache_key] = svg_bytes
    return svg_bytes
# ---------------------------------------------------------------------------
# MathSvgWidget — a QSvgWidget that auto-sizes to its SVG content
# ---------------------------------------------------------------------------

# Single unified line height for ALL equations — frac or not
_LINE_HEIGHT = 84  # px — tall enough for fractions, simple equations scale up to match

class MathSvgWidget(QSvgWidget):
    def __init__(self, svg_bytes: bytes, target_height: int = _LINE_HEIGHT_FRAC, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.load(QByteArray(svg_bytes))

        sz = self.renderer().defaultSize()
        if sz.isValid() and sz.width() > 0 and sz.height() > 0:
            scale = target_height / sz.height()
            w = int(sz.width() * scale)
            h = target_height
        else:
            w, h = 200, target_height
        self.setFixedSize(w, h)
# ---------------------------------------------------------------------------
# LatexEquationView — renders each equation line as an SVG widget
# ---------------------------------------------------------------------------

# Calculate view height for worst-case: 3 lines with mixed types, spacing included
# Worst case is KEY_CHECK_SHEAR_LONG_TRANS with 3 lines (2 simple + 1 frac/complex)
# Height = (2 * _SIMPLE_LINE_HEIGHT + 1 * _FRAC_LINE_HEIGHT) + spacing
_EQ_INTERNAL_PADDING = 8  # total padding (margins + spacing inside LatexEquationView)
# _EQ_VIEW_FIXED_HEIGHT = (2 * _SIMPLE_LINE_HEIGHT + 1 * _FRAC_LINE_HEIGHT) + 2 * _EQ_INTERNAL_PADDING + 6  # +6 for line spacing

_EQ_VIEW_FIXED_HEIGHT = (2 * _LINE_HEIGHT_SIMPLE + _LINE_HEIGHT_FRAC) + 2 * _EQ_INTERNAL_PADDING + 12

class LatexEquationView(QWidget):
    def __init__(self, lines, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(_EQ_VIEW_FIXED_HEIGHT)
        self.setStyleSheet("background: white;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.setAlignment(Qt.AlignVCenter)
        self._outer = outer

        self.set_lines(lines)

    def set_lines(self, lines) -> None:
        """Rebuild the rendered equation rows in place (e.g. flexure card
        swapping its Mp formula to match the computed PNA location)."""
        while self._outer.count():
            item = self._outer.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        if not lines:
            return

        inner = QWidget()
        inner.setStyleSheet("background: white;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(4, 4, 4, 4)
        inner_layout.setSpacing(4)
        inner_layout.setAlignment(Qt.AlignVCenter)

        for latex_line, display_width, is_frac in lines:
            latex     = _to_display_style(latex_line) if is_frac else latex_line
            fontsize  = _FONTSIZE_SIMPLE  # same fontsize for everything now
            target_h  = _LINE_HEIGHT_FRAC if is_frac else _LINE_HEIGHT_SIMPLE
            svg_bytes = _latex_to_svg(latex, display_width, fontsize=fontsize)
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.addStretch()
            row.addWidget(MathSvgWidget(svg_bytes, target_h))
            row.addStretch()
            inner_layout.addLayout(row)

        self._outer.addStretch()
        self._outer.addWidget(inner)
        self._outer.addStretch()
    
# ---------------------------------------------------------------------------
# StatusBadge
# ---------------------------------------------------------------------------

_BADGE_STYLES = {
    "pass":    ("PASS", "#1a7a4a", "#d4edda"),
    "fail":    ("FAIL", "#8b0000", "#f8d7da"),
    "neutral": ("",     "#444444", "#eeeeee"),
}


class StatusBadge(QLabel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(60, 22)
        self.setAlignment(Qt.AlignCenter)
        self.set_neutral()

    def _apply(self, state: str) -> None:
        text, fg, bg = _BADGE_STYLES[state]
        self.setText(text)
        self.setStyleSheet(
            f"color: {fg}; background: {bg};"
            "font-weight: bold; font-size: 10px; border-radius: 6px;"
        )

    def set_pass(self) -> None: self._apply("pass")
    def set_fail(self) -> None: self._apply("fail")
    def set_neutral(self) -> None: self._apply("neutral")


# ---------------------------------------------------------------------------
# SteelDesignCheckTab
# ---------------------------------------------------------------------------

class SteelDesignCheckTab(QWidget):
    """
    Design Check tab for the Steel Design dialog.

    Eight IRC code-compliance check cards in a two-column grid.
    Equations are rendered as pure SVG vector paths via matplotlib mathtext —
    Computer Modern fonts, true fractions and radicals, no pdflatex,
    no PyMuPDF, no QtWebEngine, no pixmaps required.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.check_eq_views   : dict[str, LatexEquationView] = {}
        self.check_val_labels : dict[str, QLabel]            = {}
        self.check_dcr_labels : dict[str, QLabel]            = {}
        self.check_bars       : dict[str, PercentBarWidget]  = {}
        self.check_badges     : dict[str, StatusBadge]       = {}
        self.check_cards      : dict[str, QFrame]            = {}
        self.checks_grid      : QGridLayout | None           = None

        self.summary_passed_label : QLabel | None      = None
        self.summary_failed_label : QLabel | None      = None
        self.summary_badge        : StatusBadge | None = None
        self.design_results       : list[dict]         = []

        self.setStyleSheet("background-color: white;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = StyledScrollArea()
        container   = QWidget()
        container.setStyleSheet("background-color: white;")

        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(18, 6, 18, 12)
        c_layout.setSpacing(16)
        c_layout.addWidget(self._build_summary_bar())
        c_layout.addLayout(self._build_checks_grid())
        c_layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

    def _build_summary_bar(self) -> QFrame:
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

        _S = (
            "font-size: 11px; font-weight: 600; color: #2b2b2b; "
            "background: transparent; border: none;"
        )

        checks_lbl = QLabel(f"Checks: {len(DESIGN_CHECKS)}")
        checks_lbl.setStyleSheet(_S)
        layout.addWidget(checks_lbl)

        self.summary_passed_label = QLabel("Passed: \u2014")
        self.summary_passed_label.setStyleSheet(_S)
        layout.addWidget(self.summary_passed_label)

        self.summary_failed_label = QLabel("Failed: \u2014")
        self.summary_failed_label.setStyleSheet(_S)
        layout.addWidget(self.summary_failed_label)

        layout.addStretch()

        self.summary_badge = StatusBadge()
        layout.addWidget(self.summary_badge)
        return frame

    def _build_checks_grid(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        self.checks_grid = grid
        for idx, (key, title) in enumerate(DESIGN_CHECKS):
            widget = self._build_check_card(key, title)
            grid.addWidget(widget, idx // 2, idx % 2)
            grid.setRowMinimumHeight(idx // 2, 0)   # don't force row height
        return grid

    def _relayout_visible_cards(self) -> None:
        """Re-pack visible cards into contiguous grid cells so hidden cards
        leave no empty gaps. Card order (DESIGN_CHECK_ORDER) is preserved."""
        grid = self.checks_grid
        if grid is None:
            return
        for key in DESIGN_CHECK_ORDER:
            card = self.check_cards.get(key)
            if card is not None:
                grid.removeWidget(card)
        idx = 0
        for key in DESIGN_CHECK_ORDER:
            card = self.check_cards.get(key)
            if card is not None and not card.isHidden():
                grid.addWidget(card, idx // 2, idx % 2)
                idx += 1

    def _build_check_card(self, key: str, title: str) -> QFrame:
        # Calculate total card height: title + eq_view + labels + bar + badge + spacing + margins
        # Title height estimate
        _TITLE_HEIGHT = 20
        # Value label height estimate (when shown)
        _VAL_LABEL_HEIGHT = 32
        # DCR label height estimate (when shown)
        _DCR_LABEL_HEIGHT = 20
        # PercentBarWidget height
        _BAR_HEIGHT = 30
        # StatusBadge height
        _BADGE_HEIGHT = 22
        # Layout margins (top + bottom)
        _CARD_MARGIN_HEIGHT = 24
        # Spacing between 6 widgets = 5 spacings * 8 px each
        _CARD_SPACING_HEIGHT = 40
        
        # Total card height (includes all elements visible and hidden)
        _CARD_FIXED_HEIGHT = (
            _TITLE_HEIGHT + _EQ_VIEW_FIXED_HEIGHT + _VAL_LABEL_HEIGHT +
            _DCR_LABEL_HEIGHT + _BAR_HEIGHT + _BADGE_HEIGHT +
            _CARD_MARGIN_HEIGHT + _CARD_SPACING_HEIGHT
        )
        
        card = QFrame()
        card.setObjectName("checkCard")
        card.setStyleSheet(
            "QFrame#checkCard {"
            "background-color: white;"
            "border: 1px solid #222222;"
            "border-radius: 8px;"
            "}"
        )
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setFixedHeight(_CARD_FIXED_HEIGHT)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #000; "
            "background: transparent; border: none;"
        )
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl)

        lines   = _EQ_LATEX.get(key, ())
        eq_view = LatexEquationView(lines)
        layout.addWidget(eq_view)
        self.check_eq_views[key] = eq_view

        val_lbl = QLabel()
        val_lbl.setTextFormat(Qt.RichText)
        val_lbl.setWordWrap(True)
        val_lbl.setStyleSheet(
            "font-size: 13px; color: #222; "
            "background: transparent; border: none; padding-top: 2px;"
        )
        val_lbl.setVisible(False)
        layout.addWidget(val_lbl)
        self.check_val_labels[key] = val_lbl

        dcr_bar_widget = QWidget()
        dcr_bar_widget.setStyleSheet("background: transparent;")
        dcr_bar_layout = QVBoxLayout(dcr_bar_widget)
        dcr_bar_layout.setContentsMargins(0, 0, 0, 0)
        dcr_bar_layout.setSpacing(2)

        dcr_lbl = QLabel()
        dcr_lbl.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #555; "
            "background: transparent; border: none;"
        )
        dcr_lbl.setToolTip("Utilization Ratio = Demand / Capacity  (UR ≤ 1.0 → PASS)")
        dcr_lbl.setVisible(False)
        dcr_bar_layout.addWidget(dcr_lbl)
        self.check_dcr_labels[key] = dcr_lbl

        bar = PercentBarWidget(label="", value=0.0)
        dcr_bar_layout.addWidget(bar)
        self.check_bars[key] = bar

        layout.addWidget(dcr_bar_widget)

        badge = StatusBadge()
        badge.setVisible(False)
        layout.addWidget(badge, alignment=Qt.AlignRight)
        self.check_badges[key] = badge

        self.check_cards[key] = card
        return card

    def load_data(self, cad_state: dict) -> None:
        pass

    def set_check_result(self, key: str, text: str) -> None:
        lbl = self.check_val_labels.get(key)
        if lbl is not None:
            lbl.setTextFormat(Qt.PlainText)
            lbl.setText(text)

    def clear_results(self) -> None:
        for key in self.check_badges:
            card = self.check_cards.get(key)
            if card:
                card.setVisible(True)
            lbl = self.check_val_labels.get(key)
            if lbl:
                lbl.setText("")
                lbl.setStyleSheet(
                    "font-size: 13px; color: #222; "
                    "background: transparent; border: none; padding-top: 2px;"
                )
                lbl.setVisible(False)
            dcr = self.check_dcr_labels.get(key)
            if dcr:
                dcr.setText("")
                dcr.setVisible(False)
                dcr.setStyleSheet(
                    "font-size: 14px; font-weight: bold; color: #555; "
                    "background: transparent; border: none;"
                )
            bar = self.check_bars.get(key)
            if bar:
                bar.set_value(0)
            badge = self.check_badges.get(key)
            if badge:
                badge.set_neutral()
                badge.setVisible(False)
        eq_view = self.check_eq_views.get(KEY_CHECK_FLEXURE)
        if eq_view is not None:
            eq_view.set_lines(_EQ_LATEX[KEY_CHECK_FLEXURE])
        self.design_results = []
        self._relayout_visible_cards()
        self._refresh_summary()

    def populate_from_results(self, demand, capacity, engine) -> None:
        self.clear_results()

        # Multiple checks share the same check_id (e.g. several checks all have id=5 or id=7).
        # Build a list-of-lists so _worst picks the highest DCR across ALL checks with those IDs.
        from collections import defaultdict
        by_id: dict[int, list] = defaultdict(list)
        for chk in engine.checks:
            by_id[chk.check_id].append(chk)

        def _worst(*ids):
            """Return the check with the highest DCR among all checks with the given IDs."""
            candidates = []
            for i in ids:
                candidates.extend(by_id.get(i, []))
            return max(candidates, key=lambda c: c.dcr) if candidates else None

        mapping = [
            # (ui_key,               check_ids to pick worst from)
            (KEY_CHECK_FLEXURE,          (1,)),
            (KEY_CHECK_SHEAR,            (2,)),
            (KEY_CHECK_INTERACTION,      (3, 4)),  # M-V and M-N interaction
            (KEY_CHECK_LTB,              (5,)),
            (KEY_CHECK_SHEAR_LONG_TRANS, (6, 7)),            # longitudinal stud spacing + detailing
            (KEY_CHECK_FATIGUE,          (8, 9)),           # normal + shear fatigue
            (KEY_CHECK_STRESS,           (11,)),             # steel-equivalent stress (concrete + rebar moved to deck)
            (KEY_CHECK_DEFLECTION,       (13, 14)),          # live + total deflection (crack moved to deck)
        ]

        results_by_key: dict[str, dict] = {}

        for key, ids in mapping:
            try:
                worst = _worst(*ids)
                if worst is None:
                    continue
                entry = {
                    "demand":   worst.demand,
                    "capacity": worst.capacity,
                    "ratio":    worst.dcr,
                    "passed":   worst.status != "FAIL",
                    "governing_method": worst.governing_method,
                }
                if key == KEY_CHECK_FLEXURE:
                    m = re.search(r"PNA in (\w+)", worst.note or "")
                    entry["pna_location"] = m.group(1) if m else ""
                if key == KEY_CHECK_INTERACTION:
                    note = worst.note or ""
                    entry["check_id"] = worst.check_id
                    entry["Mu_kNm"]  = getattr(demand, "Mu_kNm", 0.0)
                    entry["Mdv_kNm"] = getattr(capacity, "Mdv_kNm", 0.0)
                    if worst.check_id == 4:
                        entry["is_high_shear"] = "shear-reduced" in note
                        entry["Nu_kN"]  = getattr(demand, "Nu_kN", 0.0)
                        entry["NRd_kN"] = getattr(capacity, "NRd_kN", 0.0)
                    else:
                        m = re.search(r"beta=([\d.]+)", note)
                        entry["is_high_shear"] = bool(m) and float(m.group(1)) > 0
                results_by_key[key] = entry
            except Exception:
                logger.exception("Failed to load checks %s for key %s", ids, key)

        self.design_results = list(results_by_key.values())
        for key, res in results_by_key.items():
            self._apply_card_result(key, res)
        for key in DESIGN_CHECK_ORDER:
            card = self.check_cards.get(key)
            if card is not None:
                card.setVisible(key in results_by_key)
        self._relayout_visible_cards()
        self._refresh_summary()


    def _apply_card_result(self, key: str, res: dict) -> None:
        if key not in self.check_val_labels:
            return

        demand   = res.get("demand",   0.0)
        capacity = res.get("capacity", 0.0)
        ratio    = res.get("ratio",    0.0)
        passed   = res.get("passed",   False)
        unit_str = f" {DESIGN_CHECK_UNITS[key]}" if DESIGN_CHECK_UNITS.get(key) else ""
        
        if key == KEY_CHECK_FLEXURE:
            eq_view = self.check_eq_views.get(key)
            if eq_view is not None:
                eq_view.set_lines(_flexure_eq_lines(res.get("pna_location", "")))
        if key == KEY_CHECK_SHEAR:
    
            governing_method = res.get("governing_method")

            new_lines = _get_shear_latex(governing_method)

            old_eq = self.check_eq_views.get(key)

            if old_eq is not None:
                card = self.check_cards[key]
                layout = card.layout()

        # Remove the old equation widget
                layout.removeWidget(old_eq)
                old_eq.hide()
                old_eq.setParent(None)
                old_eq.deleteLater()

        # Create the new equation widget
                new_eq = LatexEquationView(new_lines)

        # Insert it back below the title (index 1)
                layout.insertWidget(1, new_eq)

        # Store the new widget
                self.check_eq_views[key] = new_eq
        
        

        if key == KEY_CHECK_INTERACTION:
            old_eq = self.check_eq_views.get(key)
            if old_eq is not None:
                card = self.check_cards[key]
                layout = card.layout()
                
                # Remove old equation widget
                layout.removeWidget(old_eq)
                old_eq.hide()
                old_eq.setParent(None)
                old_eq.deleteLater()
                
                # Create new equation widget
                new_eq = LatexEquationView(
                    _interaction_eq_lines(
                        res.get("check_id"),
                        res.get("is_high_shear", False)
                    )
                )
                # Insert below the title
                layout.insertWidget(1, new_eq)

                # Store new widget
                self.check_eq_views[key] = new_eq

            Mu_kNm  = res.get("Mu_kNm", 0.0)
            Mdv_kNm = res.get("Mdv_kNm", 0.0)
            if res.get("check_id") == 4:
                Nu_kN  = res.get("Nu_kN", 0.0)
                NRd_kN = res.get("NRd_kN", 0.0)
                val_text = (
                    f"<i>N<sub>u</sub></i> = {Nu_kN:.2f} kN, <i>N<sub>Rd</sub></i> = {NRd_kN:.2f} kN<br>"
                    f"<i>M<sub>u</sub></i> = {Mu_kNm:.2f} kNm, <i>M<sub>dv</sub></i> = {Mdv_kNm:.2f} kNm<br>"
                    f"<i>N<sub>u</sub></i>/<i>N<sub>Rd</sub></i> + <i>M<sub>u</sub></i>/<i>M<sub>dv</sub></i> = {ratio:.2f}"
                )
            else:
                val_text = (
                    f"<i>M<sub>u</sub></i> = {Mu_kNm:.2f} kNm, <i>M<sub>dv</sub></i> = {Mdv_kNm:.2f} kNm<br>"
                    f"<i>M<sub>u</sub></i>/<i>M<sub>dv</sub></i> = {ratio:.2f}"
                )
        else:
            dem_pfx = DESIGN_CHECK_DEM_PFX.get(key, "Demand")
            cap_pfx = DESIGN_CHECK_CAP_PFX.get(key, "Capacity")

            if key == KEY_CHECK_SHEAR:
                method = res.get("governing_method")

                if method == "plastic":
                    cap_pfx = "<i>V<sub>p</sub></i>"
                elif method == "post_critical":
                    cap_pfx = "<i>V<sub>cr</sub></i>"
                elif method == "tension_field":
                    cap_pfx = "<i>V<sub>tf</sub></i>"

            val_text = (
                f"{dem_pfx} = {demand:.2f}{unit_str}<br>"
                f"{cap_pfx} = {capacity:.2f}{unit_str}"
            )
        
        dcr_color = "#388E3C" if passed else "#D32F2F"
        val_lbl = self.check_val_labels[key]
        val_lbl.setTextFormat(Qt.RichText)
        val_lbl.setText(val_text)
        val_lbl.setVisible(True)

        dcr_lbl = self.check_dcr_labels.get(key)
        if dcr_lbl:
            dcr_lbl.setText(f"Utilization Ratio = {ratio:.2f}")
            dcr_lbl.setStyleSheet(
                f"font-size: 14px; font-weight: bold; color: {dcr_color}; "
                "background: transparent; border: none;"
            )
            dcr_lbl.setVisible(True)

        bar = self.check_bars.get(key)
        if bar:
            bar.set_value(ratio * 100)
            
        badge = self.check_badges.get(key)
        if badge:
            badge.setVisible(True)
            if passed:
                badge.set_pass()
            else:
                badge.set_fail()

    def _refresh_summary(self) -> None:      
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