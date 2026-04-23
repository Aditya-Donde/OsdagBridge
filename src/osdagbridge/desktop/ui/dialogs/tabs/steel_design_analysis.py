from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QFrame,
    QSizePolicy,
    QGroupBox,
)
from PySide6.QtCore import Qt

from osdagbridge.desktop.ui.docks.output_dock import (
    NoScrollComboBox,
)
from osdagbridge.desktop.ui.utils.styled_scroll_area import StyledScrollArea

# Fallback load combination labels used to pre-populate the dropdown before
# live load cases are discovered from the analyser results.
LOAD_COMBINATIONS = [
    "Envelope",
    "DL + LL",
    "1.35 DL + 1.5 LL",
    "DL", "SIDL", "LL",
    "WL", "EL", "IMF", "TL",
]

# Greyed-out read-only style for combos mirroring the Output Dock selection.
# Drop-down arrow is hidden to make clear the field is not interactive.
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

#  Design tokens — copied verbatim from output_dock.apply_field_style()
#  so every control matches the rest of the OsdagBridge application.

# Read-only result fields (grey background, black border like main app)
_FIELD_STYLE = """
    QLineEdit {
        padding: 1px 7px;
        border: 1px solid black;
        border-radius: 5px;
        background-color: #f4f4f4;
        color: #000000;
        font-size: 11px;
        font-weight: normal;
    }
"""

# Interactive field — e.g. the x-position field (white, editable)
_FIELD_STYLE_WHITE = """
    QLineEdit {
        padding: 1px 7px;
        border: 1px solid black;
        border-radius: 5px;
        background-color: white;
        color: #000000;
        font-size: 11px;
        font-weight: normal;
    }
"""

# Combo box — exact match for output_dock.apply_field_style(QComboBox)
_COMBO_STYLE = """
    QComboBox {
        padding: 1px 7px;
        border: 1px solid black;
        border-radius: 5px;
        background-color: white;
        color: black;
        font-size: 11px;
        min-height: 28px;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        border-left: 0px;
    }
    QComboBox::down-arrow {
        image: url(:/vectors/arrow_down_light.svg);
        width: 20px;
        height: 20px;
        margin-right: 8px;
    }
    QComboBox::down-arrow:on {
        image: url(:/vectors/arrow_up_light.svg);
        width: 20px;
        height: 20px;
        margin-right: 8px;
    }
    QComboBox QAbstractItemView {
        background-color: white;
        border: 1px solid black;
        outline: none;
    }
    QComboBox QAbstractItemView::item {
        color: black;
        background-color: white;
        border: 1px solid white;
        border-radius: 0;
        padding: 2px;
    }
    QComboBox QAbstractItemView::item:hover {
        border: 1px solid #90AF13;
        background-color: #90AF13;
        color: black;
    }
    QComboBox QAbstractItemView::item:selected {
        background-color: #90AF13;
        color: black;
        border: 1px solid #90AF13;
    }
"""

# Outer panel/card borders — same grey as input/output docks
_CARD_STYLE = (
    "QFrame#girderCard { "
    "background-color: white; "
    "border: 1px solid #b0b0b0; "
    "border-radius: 6px; "
    "}"
)

# Inner QGroupBox (Support Reactions / Maximum Values) — matches _analysis_group_style
_GROUP_STYLE = """
    QGroupBox {
        font-weight: bold;
        font-size: 11px;
        color: #000000;
        border: 1px solid #b0b0b0;
        border-radius: 6px;
        margin-top: 8px;
        padding-top: 14px;
        background-color: white;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 8px;
        padding: 0 4px;
        background-color: #f5f5f5;
    }
"""

# Fixed width for form-row labels — keeps all input fields left-aligned at the same x offset.
_LABEL_MIN_W = 130


class SteelDesignAnalysisTab(QWidget):
    """
    Analysis Results tab for the Steel Design dialog.

    Layout
    ──────
    QScrollArea
    └── container (QVBoxLayout)
        └── main_row (QHBoxLayout)
            ├── left_panel  (fixed 350 px)
            │   ├── Selection card  [Member ID | Load Combination]
            │   └── Results card    [Support Reactions | Maximum Values]
            └── diagram_card  (expanding)
                ├── controls_row   [Component card | Display Location card]
                ├── separator
                └── inner_row
                    ├── diagram_placeholder  (FigureCanvas injected at runtime)
                    └── right_col  [x_input | M_z | V_y | D_y]
    """

    def __init__(self, parent=None):
        self.result_fields = {}
        self.x_fields      = {}

        super().__init__(parent)
        self.setStyleSheet("background-color: white;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = StyledScrollArea()

        container = QWidget()
        container.setStyleSheet("background-color: white;")

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(6)

        main_row = QHBoxLayout()
        main_row.setSpacing(10)
        main_row.setContentsMargins(0, 0, 0, 0)

        main_row.addWidget(self._build_left_panel(), 0)
        main_row.addWidget(self._build_diagram_section(), 1)

        container_layout.addLayout(main_row)
        container_layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

    # ─────────────────────────────────────────────────────────────────────────
    # WIDGET FACTORY HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _card_frame(self):
        """Outer panel card — consistent grey rounded border."""
        frame = QFrame()
        frame.setObjectName("girderCard")
        frame.setStyleSheet(_CARD_STYLE)
        return frame

    def _section_title(self, text):
        """Bold section header — matches label style in other docks."""
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 13px; color: #2B2B2B; font-weight: bold; background: transparent; border: none;"
        )
        return lbl

    def _row_label(self, text):
        """Left-column label for a form row."""
        lbl = QLabel(text)
        lbl.setTextFormat(Qt.RichText)
        lbl.setStyleSheet("font-size: 11px; color: #333333; background: transparent;")
        lbl.setFixedWidth(_LABEL_MIN_W)
        lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        return lbl

    def _side_label(self, text):
        """Label shown beside RHS diagram value fields."""
        lbl = QLabel(text)
        lbl.setTextFormat(Qt.RichText)
        lbl.setStyleSheet(
            "font-size: 11px; color: #333333; background: transparent;"
        )
        lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return lbl

    def _readonly_field(self):
        """Read-only result field — fixed 28×160 px to match every other form field."""
        field = QLineEdit()
        field.setReadOnly(True)
        field.setFixedHeight(28)
        field.setFixedWidth(160)
        field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        field.setStyleSheet(_FIELD_STYLE)
        field.setAlignment(Qt.AlignCenter)
        return field

    def _side_field(self):
        """Compact read-only field displayed beside the plots."""
        field = QLineEdit()
        field.setReadOnly(True)
        field.setFixedHeight(28)
        field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        field.setAlignment(Qt.AlignCenter)
        field.setStyleSheet(_FIELD_STYLE)
        return field

    def _styled_combo(self, width=160):
        """Combo box styled identically to output_dock.apply_field_style."""
        combo = NoScrollComboBox()
        if width > 0:
            combo.setFixedWidth(width)
        combo.setFixedHeight(28)
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        combo.setStyleSheet(_COMBO_STYLE)
        return combo

    def _form_row(self, label_text, widget, layout):
        """
        Append a (label, widget) row to *layout* as a QHBoxLayout.
        Fixed-width label ensures all field widgets start at the same x offset.
        """
        row = QHBoxLayout()
        row.setSpacing(8)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self._row_label(label_text))
        row.addWidget(widget)
        row.addStretch()
        layout.addLayout(row)

    def _diagram_side_row(self, label_widget, field_widget):
        """Return a QHBoxLayout with a fixed-width right-aligned label + field."""
        row = QHBoxLayout()
        row.setSpacing(4)
        row.setContentsMargins(0, 2, 0, 2)
        row.addWidget(label_widget, 0)         # label: fixed to its natural size
        row.addWidget(field_widget, 1)         # widget: takes all remaining width
        return row

    # ─────────────────────────────────────────────────────────────────────────
    # LEFT PANEL
    # ─────────────────────────────────────────────────────────────────────────

    def _build_left_panel(self):
        """Build the fixed-width left panel containing the selection and results cards."""
        panel = QWidget()
        panel.setStyleSheet("background-color: transparent;")
        # Width = 350: leaves 350-26(card margins)-22(groupbox border+margins)=302px
        # for 130(label)+8(spacing)+160(field)=298px — 4px breathing room each side
        panel.setFixedWidth(350)
        panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # ── Selection card ────────────────────────────────────────────
        sel_card = self._card_frame()
        sel_layout = QVBoxLayout(sel_card)
        # Left margin = 23 to match effective indent of Results group box fields:
        # Results: card_L(12) + groupbox_border(1) + groupbox_margin_L(10) = 23px
        sel_layout.setContentsMargins(23, 10, 14, 12)
        sel_layout.setSpacing(8)
        sel_layout.addWidget(self._section_title("Select Member"))

        self.member_combo = self._styled_combo()
        self.member_combo.addItems(["All", "Girder 1", "Girder 2"])
        self.member_combo.setEnabled(False)
        self.member_combo.setStyleSheet(_DISABLED_COMBO_STYLE)
        self.member_combo.setToolTip(
            "Change the member in the Output Dock \u2014 this field mirrors that selection."
        )

        self.load_combo = self._styled_combo()
        self.load_combo.addItems(LOAD_COMBINATIONS)
        self.load_combo.setEnabled(False)
        self.load_combo.setStyleSheet(_DISABLED_COMBO_STYLE)
        self.load_combo.setToolTip(
            "Change the load combination in the Output Dock \u2014 this field mirrors that selection."
        )

        self._form_row("Member ID:", self.member_combo, sel_layout)
        self._form_row("Load Combination:", self.load_combo, sel_layout)

        layout.addWidget(sel_card)

        # ── Results card ──────────────────────────────────────────────
        res_card = self._card_frame()
        res_layout = QVBoxLayout(res_card)
        res_layout.setContentsMargins(12, 10, 14, 12)
        res_layout.setSpacing(8)
        res_layout.addWidget(self._section_title("Results"))

        # Support Reactions sub-group
        reac_group = QGroupBox("Support Reactions")
        reac_group.setStyleSheet(_GROUP_STYLE)
        reac_inner = QVBoxLayout(reac_group)
        reac_inner.setContentsMargins(10, 8, 10, 10)
        reac_inner.setSpacing(8)
        for key, label in [
            ("R_A", "R<sub>A</sub> (kN)"),
            ("R_B", "R<sub>B</sub> (kN)"),
        ]:
            field = self._readonly_field()
            self.result_fields[key] = field
            # Build the row manually so we can force font-weight: normal
            # on the label, overriding QGroupBox bold cascade.
            row_lbl = self._row_label(label)
            row_lbl.setStyleSheet(
                "font-size: 11px; font-weight: normal; "
                "color: #333333; background: transparent;"
            )
            row = QHBoxLayout()
            row.setSpacing(8)
            row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(row_lbl)
            row.addWidget(field)
            row.addStretch()
            reac_inner.addLayout(row)

        # Maximum Values sub-group
        max_group = QGroupBox("Maximum Values")
        max_group.setStyleSheet(_GROUP_STYLE)
        max_inner = QVBoxLayout(max_group)
        max_inner.setContentsMargins(8, 8, 8, 10)
        max_inner.setSpacing(8)
        for key, label in [
            ("T_x", "T<sub>x</sub> (kNm)"),
            ("M_y", "M<sub>y</sub> (kNm)"),
            ("M_z", "M<sub>z</sub> (kNm)"),
            ("F_x", "F<sub>x</sub> (kN)"),
            ("V_y", "V<sub>y</sub> (kN)"),
            ("V_z", "V<sub>z</sub> (kN)"),
            ("D_x", "D<sub>x</sub> (mm)"),
            ("D_y", "D<sub>y</sub> (mm)"),
            ("D_z", "D<sub>z</sub> (mm)"),
        ]:
            field = self._readonly_field()
            self.result_fields[key] = field
            self._form_row(label, field, max_inner)

        res_layout.addWidget(reac_group)
        res_layout.addWidget(max_group)
        layout.addWidget(res_card)
        layout.addStretch()

        return panel

    # ─────────────────────────────────────────────────────────────────────────
    # DIAGRAM SECTION
    # ─────────────────────────────────────────────────────────────────────────

    def _build_diagram_section(self):
        """
        Right-hand panel containing:
          1. top_bar  — Component combo + Display Location group, both centered
          2. separator
          3. inner_row — FigureCanvas placeholder + RHS value column
        """
        card = self._card_frame()
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 24, 12) # 24px right margin keeps all content off the scrollbar
        card_layout.setSpacing(6)

        # ── Component titled card ─────────────────────────────────────
        comp_card = QFrame()
        comp_card.setObjectName("controlCard")
        comp_card.setStyleSheet("""
            QFrame#controlCard {
                background-color : white;
                border           : 1px solid #b0b0b0;
                border-radius    : 6px;
            }
            QLabel {
                border     : none;
                background : transparent;
            }
        """)
        comp_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # Height is allowed to adapt; QHBoxLayout will ensure disp_card matches

        comp_card_layout = QVBoxLayout(comp_card)
        comp_card_layout.setContentsMargins(23, 10, 14, 12)
        comp_card_layout.setSpacing(4)

        comp_title = QLabel("Component")
        comp_title.setStyleSheet(
            "font-size: 13px; color: #2B2B2B; font-weight: bold;"
            " background: transparent; border: none;"
        )
        comp_card_layout.addWidget(comp_title)

        self.component_combo = NoScrollComboBox()
        self.component_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.component_combo.setStyleSheet(_COMBO_STYLE)
        self.component_combo.addItems([
            "Major (Mz, Vy, Dy)",
            "Minor (My, Vz, Dz)",
            "Axial (Tx, Fx, Dx)",
        ])
        comp_card_layout.addWidget(self.component_combo)

        # ── Display Location titled card placeholder ──────────────────
        # SteelDesign._setup_analysis_plots() will build and inject this card.
        # We store a reference point so SteelDesign knows where to insert it.
        self.disp_card_placeholder = None   # filled at runtime

        # ── Controls row: two equal cards side by side ────────────────
        self.controls_row = QHBoxLayout()
        self.controls_row.setContentsMargins(0, 0, 0, 0)
        self.controls_row.setSpacing(24)  # Generous gap to prevent border merge
        self.controls_row.addWidget(comp_card, 1)   # stretch=1
        # SteelDesign appends the Display Location card with stretch=1

        card_layout.addLayout(self.controls_row)

        # Create fixed-width labels for RHS diagram value column.
        # These are initialised here so update_rhs_labels() can update them
        # before the inner_row builds the right_col widget.
        self.lbl_x = self._side_label("x (m)")
        self.lbl_m = self._side_label("M<sub>z</sub> (kNm)")
        self.lbl_v = self._side_label("V<sub>y</sub> (kN)")
        self.lbl_d = self._side_label("D<sub>y</sub> (mm)")

        for lbl in (self.lbl_x, self.lbl_m, self.lbl_v, self.lbl_d):
            lbl.setFixedWidth(70)
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("border: none; border-top: 1px solid #e0e0e0;")
        sep.setMaximumHeight(1)
        card_layout.addWidget(sep)

        # ── Inner row: plots + RHS value column ───────────────────────
        inner_row = QHBoxLayout()
        inner_row.setSpacing(10)
        inner_row.setContentsMargins(0, 0, 0, 0)

        # Diagram placeholder — replaced at runtime with FigureCanvas
        self.diagram_placeholder = QLabel()
        self.diagram_placeholder.setMinimumSize(260, 300)
        self.diagram_placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.diagram_placeholder.setAlignment(Qt.AlignCenter)
        self.diagram_placeholder.setText("[BMD / SFD / Deflection Diagram]")
        self.diagram_placeholder.setStyleSheet("""
            QLabel {
                border: 1px dashed #b0b0b0;
                background-color: #fafafa;
                color: #999999;
                font-size: 10px;
                border-radius: 6px;
            }
        """)
        inner_row.addWidget(self.diagram_placeholder, 1)

        # ── Right column: x(position) at top; M_z/V_y/D_y vertically centred 
        #    with the 3 subplots via fixed pixel spacers.
        right_col = QWidget()
        right_col.setStyleSheet("background: transparent;")
        right_col.setMinimumWidth(180)
        right_col.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)

        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(6, 0, 6, 0)   # 6px padding each side
        right_layout.setSpacing(0)

        # x-position (interactive, white background)
        self.x_input = QLineEdit()
        self.x_input.setPlaceholderText("click plot…")
        self.x_input.setFixedHeight(28)
        self.x_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.x_input.setStyleSheet(_FIELD_STYLE_WHITE)
        self.x_input.setAlignment(Qt.AlignCenter)  # P3: centre-align position readout
        right_layout.addSpacing(35)
        right_layout.addLayout(self._diagram_side_row(self.lbl_x, self.x_input))

        # Fixed spacers derived from gridspec maths so each label's vertical
        # centre aligns with the midpoint of its corresponding subplot band.
        #
        # Gridspec: height_ratios=[0.45, 1, 1, 1], hspace=0.32
        # subplots_adjust: top=0.94, bottom=0.12  → usable height ≈ 475 px (at 580 px canvas)
        #
        # Subplot vertical centres from canvas top (px, ~580 px canvas):
        #   ax_scheme centre ≈  50 px   (x_input top-pad = 35 gets mid at ~49 px)
        #   ax_bmd    centre ≈ 154 px   → gap after x_input row ≈ 74 px
        #   ax_sfd    centre ≈ 303 px   → gap after M_z row     ≈ 119 px
        #   ax_defl   centre ≈ 451 px   → gap after V_y row     ≈ 119 px
        #   bottom pad                  ≈ 114 px
        right_layout.addSpacing(74)
        self.mx_field = self._side_field()
        right_layout.addLayout(self._diagram_side_row(self.lbl_m, self.mx_field))

        right_layout.addSpacing(119)
        self.vx_field = self._side_field()
        right_layout.addLayout(self._diagram_side_row(self.lbl_v, self.vx_field))

        right_layout.addSpacing(119)
        self.dx_field = self._side_field()
        right_layout.addLayout(self._diagram_side_row(self.lbl_d, self.dx_field))
        right_layout.addSpacing(114)   # bottom pad

        self.x_fields["M_z"] = self.mx_field
        self.x_fields["V_y"] = self.vx_field
        self.x_fields["D_y"] = self.dx_field

        inner_row.addWidget(right_col, 0)
        card_layout.addLayout(inner_row, 1)

        return card

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────

    def update_rhs_labels(self, component_index):
        """
        Update right-hand panel labels for major (0), minor (1), or axial (2) components.
        """
        if component_index == 0:  # Major
            self.lbl_m.setText("M<sub>z</sub> (kNm)")
            self.lbl_v.setText("V<sub>y</sub> (kN)")
            self.lbl_d.setText("D<sub>y</sub> (mm)")
        elif component_index == 1:  # Minor
            self.lbl_m.setText("M<sub>y</sub> (kNm)")
            self.lbl_v.setText("V<sub>z</sub> (kN)")
            self.lbl_d.setText("D<sub>z</sub> (mm)")
        elif component_index == 2:  # Axial
            self.lbl_m.setText("M<sub>x</sub> (kNm)")
            self.lbl_v.setText("F<sub>x</sub> (kN)")
            self.lbl_d.setText("D<sub>x</sub> (mm)")

    def set_girder_count(self, count):
        """Repopulate member_combo with 'Girder 1' … 'Girder N' entries."""
        self.member_combo.clear()
        self.member_combo.addItems(["All"] + [f"Girder {i}" for i in range(1, count + 1)])

    def load_data(self, cad_state: dict):
        """
        Pre-fill fields from a cad_state snapshot (e.g. on dialog open).
        Silently ignores missing or invalid entries.
        """
        if not cad_state:
            return
        try:
            self.set_girder_count(int(cad_state.get("no_of_girders", 2)))
        except (ValueError, TypeError):
            pass
        for key, field in self.result_fields.items():
            field.setText(str(cad_state.get(key, "")))
        for key, field in self.x_fields.items():
            if hasattr(field, "setText"):
                field.setText(str(cad_state.get(key, "")))
