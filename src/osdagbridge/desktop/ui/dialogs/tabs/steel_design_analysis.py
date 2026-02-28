from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QFrame,
    QSizePolicy,
    QSpacerItem,
)
from PySide6.QtCore import Qt

from osdagbridge.desktop.ui.docks.output_dock import (
    NoScrollComboBox,
)
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.utils.styled_scroll_area import StyledScrollArea

# From load_combination_tab.py defaults + output_dock
LOAD_COMBINATIONS = [
    "Envelope",
    "DL + LL",
    "1.35 DL + 1.5 LL",
    "DL", "SIDL", "LL",
    "WL", "EL", "IMF", "TL",
]


class SteelDesignAnalysisTab(QWidget):

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

        # Same margins/spacing as girder_details_tab content_layout
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(12)

        # ── MAIN ROW ─────────────────────────────────────────────────────────
        main_row = QHBoxLayout()
        main_row.setSpacing(12)
        main_row.setContentsMargins(0, 0, 0, 0)

        main_row.addWidget(self._build_left_panel(), 0)
        main_row.addWidget(self._build_diagram_section(), 1)

        container_layout.addLayout(main_row)
        container_layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

    # ── HELPERS — exact girder_details_tab pattern ───────────────────────────

    def _create_card_frame(self):
        """Outer card — same as GirderDetailsTab._create_card_frame."""
        frame = QFrame()
        frame.setObjectName("girderCard")
        frame.setStyleSheet(
            "QFrame#girderCard { background-color: white; border: 1px solid #cfcfcf; border-radius: 10px; }"
        )
        return frame

    def _create_label(self, text):
        """Section title — same as GirderDetailsTab._create_label."""
        label = QLabel(text)
        label.setStyleSheet(
            "font-size: 12px; color: #2f2f2f; font-weight: 600; background: transparent;"
        )
        label.setAutoFillBackground(False)
        return label

    def _create_small_label(self, text):
        """Row label — same as GirderDetailsTab._create_small_label."""
        label = QLabel(text)
        label.setTextFormat(Qt.RichText)
        label.setStyleSheet("font-size: 10px; color: #5a5a5a; background: transparent;")
        label.setAutoFillBackground(False)
        return label

    def _side_label(self, text):
        """Short label beside diagram fields."""
        lbl = QLabel(text)
        lbl.setTextFormat(Qt.RichText)
        lbl.setStyleSheet("font-size: 10px; color: #5a5a5a; background: transparent;")
        lbl.setFixedWidth(40)
        return lbl

    def _make_grid(self):
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)
        grid.setColumnMinimumWidth(0, 180)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 1)
        return grid

    def _readonly_field(self):
        field = QLineEdit()
        field.setReadOnly(True)
        field.setFixedWidth(150)
        field.setMinimumHeight(28)
        field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        apply_field_style(field)
        return field

    def _side_field(self):
        field = QLineEdit()
        field.setReadOnly(True)
        field.setFixedWidth(120)
        field.setMinimumHeight(28)
        field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        apply_field_style(field)
        return field

    def _add_row(self, grid, row, text, widget):
        grid.addWidget(self._create_small_label(text), row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        grid.addWidget(widget,                         row, 1, Qt.AlignLeft | Qt.AlignVCenter)
        return row + 1

    # ── LEFT PANEL ────────────────────────────────────────────────────────────

    def _build_left_panel(self):
        panel = QWidget()
        panel.setStyleSheet("background-color: transparent;")
        panel.setFixedWidth(360)
        panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # ── Selection card ────────────────────────────────────────────────────
        sel_card = self._create_card_frame()
        sel_layout = QVBoxLayout(sel_card)
        sel_layout.setContentsMargins(18, 16, 18, 16)
        sel_layout.setSpacing(10)
        sel_layout.addWidget(self._create_label("Selection:"))

        sel_grid = self._make_grid()

        self.member_combo = NoScrollComboBox()
        apply_field_style(self.member_combo)
        self.member_combo.setFixedWidth(150)
        self.member_combo.setMinimumHeight(28)
        self.member_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.member_combo.addItems(["All", "Girder 1", "Girder 2"])

        self.load_combo = NoScrollComboBox()
        apply_field_style(self.load_combo)
        self.load_combo.setFixedWidth(150)
        self.load_combo.setMinimumHeight(28)
        self.load_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.load_combo.addItems(LOAD_COMBINATIONS)

        r = 0
        r = self._add_row(sel_grid, r, "Member ID:",        self.member_combo)
        r = self._add_row(sel_grid, r, "Load Combination:", self.load_combo)
        sel_layout.addLayout(sel_grid)
        layout.addWidget(sel_card)

        # ── Results card ──────────────────────────────────────────────────────
        res_card = self._create_card_frame()
        res_layout = QVBoxLayout(res_card)
        res_layout.setContentsMargins(18, 16, 18, 16)
        res_layout.setSpacing(10)
        res_layout.addWidget(self._create_label("Results:"))

        res_grid = self._make_grid()
        r = 0
        for key, label in [
            ("R_A",   "R<sub>A</sub>"),
            ("R_B",   "R<sub>B</sub>"),
            ("M_max", "M<sub>max</sub>"),
            ("V_max", "V<sub>max</sub>"),
            ("D_max", "D<sub>max</sub>"),
        ]:
            field = self._readonly_field()
            r = self._add_row(res_grid, r, label, field)
            self.result_fields[key] = field

        res_layout.addLayout(res_grid)
        layout.addWidget(res_card)
        layout.addStretch()

        return panel

    # ── DIAGRAM SECTION ───────────────────────────────────────────────────────

    def _build_diagram_section(self):
        """
        Diagram and right-side fields sit side-by-side with NO outer card —
        the diagram placeholder itself is the visual element.
        """
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        inner_row = QHBoxLayout(wrapper)
        inner_row.setSpacing(12)
        inner_row.setContentsMargins(0, 0, 0, 0)

        # Diagram placeholder — standalone, no card around it
        self.diagram_placeholder = QLabel()
        self.diagram_placeholder.setMinimumSize(260, 440)
        self.diagram_placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.diagram_placeholder.setAlignment(Qt.AlignCenter)
        self.diagram_placeholder.setText("[BMD / SFD / Deflection Diagram]")
        self.diagram_placeholder.setStyleSheet("""
            QLabel {
                border: 1px solid #cfcfcf;
                background-color: #F5F5F5;
                color: #9a9a9a;
                font-size: 10px;
                border-radius: 10px;
            }
        """)
        inner_row.addWidget(self.diagram_placeholder, 1)

        # Right column: x input + M_x / V_x / D_x spaced to diagram zones
        right_col = QWidget()
        right_col.setStyleSheet("background: transparent;")
        right_col.setFixedWidth(170)
        right_col.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.x_input = QLineEdit()
        self.x_input.setFixedWidth(120)
        self.x_input.setMinimumHeight(28)
        self.x_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        apply_field_style(self.x_input)
        right_layout.addLayout(self._side_row("x", self.x_input))

        right_layout.addSpacerItem(QSpacerItem(0, 100, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.mx_field = self._side_field()
        right_layout.addLayout(self._side_row("M<sub>x</sub>", self.mx_field))

        right_layout.addSpacerItem(QSpacerItem(0, 100, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.vx_field = self._side_field()
        right_layout.addLayout(self._side_row("V<sub>x</sub>", self.vx_field))

        right_layout.addSpacerItem(QSpacerItem(0, 100, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.dx_field = self._side_field()
        right_layout.addLayout(self._side_row("D<sub>x</sub>", self.dx_field))

        right_layout.addStretch()

        self.x_fields["M_x"] = self.mx_field
        self.x_fields["V_x"] = self.vx_field
        self.x_fields["D_x"] = self.dx_field

        inner_row.addWidget(right_col, 0)
        return wrapper

    def _side_row(self, label_text, widget):
        row = QHBoxLayout()
        row.setSpacing(6)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self._side_label(label_text))
        row.addWidget(widget)
        row.addStretch()
        return row

    # ── PUBLIC API ────────────────────────────────────────────────────────────

    def set_girder_count(self, count):
        """Mirrors GirderDetailsTab.set_girder_count — no hardcoding."""
        self.member_combo.clear()
        self.member_combo.addItems(["All"] + [f"Girder {i}" for i in range(1, count + 1)])

    def load_data(self, cad_state: dict):
        if not cad_state:
            return
        try:
            self.set_girder_count(int(cad_state.get("no_of_girders", 2)))
        except (ValueError, TypeError):
            pass
        for key, field in self.result_fields.items():
            field.setText(str(cad_state.get(key, "")))
        for key, field in self.x_fields.items():
            field.setText(str(cad_state.get(key, "")))