from __future__ import annotations

import math
import copy
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QColor, QPalette, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QListWidget,
    QScrollArea,
    QSizePolicy,
    QStyledItemDelegate,
    QStyle,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from osdagbridge.core.utils.common import (
    VALUES_GIRDER_DESIGN_MODE,
    VALUES_GIRDER_SPAN_MODE,
    VALUES_GIRDER_SYMMETRY,
    VALUES_GIRDER_SUPPORT_TYPE,
    VALUES_GIRDER_TYPE,
    VALUES_PROFILE_SCOPE,
    VALUES_TORSIONAL_RESTRAINT,
    VALUES_WARPING_RESTRAINT,
    VALUES_WEB_TYPE,
)
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.utils.rolled_section_preview import RolledSectionPreview
from osdagbridge.core.utils.resource_db import ensure_resource_database


DEFAULT_MEMBER_LENGTH_M = 30.0
DEFAULT_DISTANCE_START_M = 0.0
# Upper bound for girder-specific UI controls (dropdowns/tables).
# This is a UI safety cap; actual girder count is driven by the "No. of Girders" input.
MAX_GIRDER_COUNT = 20

SAIL_APPROVED_THICKNESS_VALUES = [
    "8", "10", "12", "14", "16", "18", "20", "22", "25", "28", "32", "36",
    "40", "45", "50", "56", "63", "75", "80", "90", "100", "110", "120",
]
def _locate_database() -> Path:
    return ensure_resource_database(Path(__file__).resolve())


DB_PATH = _locate_database()


@dataclass(frozen=True)
class BeamSection:
    """Data container for rolled beam properties."""

    designation: str
    type_name: str
    mass_per_meter_kg: float
    area_cm2: float
    depth_mm: float
    flange_width_mm: float
    web_thickness_mm: float
    flange_thickness_mm: float
    root_radius_mm: float
    toe_radius_mm: float
    moment_of_inertia_zz_cm4: float
    moment_of_inertia_yy_cm4: float
    radius_of_gyration_z_cm: float
    radius_of_gyration_y_cm: float
    elastic_section_modulus_z_cm3: float
    elastic_section_modulus_y_cm3: float
    plastic_section_modulus_z_cm3: float
    plastic_section_modulus_y_cm3: float
    torsion_constant_cm4: float
    warping_constant_cm6: float


class GirderSectionCatalog:
    """Loads rolled girder information from the bundled SQLite database."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self._sections: Dict[str, BeamSection] = {}
        self._outlines: Dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not self.db_path.exists():
            return
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    Designation, Type, Mass, Area, D, B, tw, T,
                    R1, R2, Iz, Iy, rz, ry, Zz, Zy, Zpz, Zpy, It, Iw
                FROM Beams
                """
            )
            for row in cursor.fetchall():
                (
                    designation,
                    type_name,
                    mass,
                    area,
                    depth,
                    flange_width,
                    web_thickness,
                    flange_thickness,
                    r1,
                    r2,
                    iz,
                    iy,
                    rz,
                    ry,
                    zz,
                    zy,
                    zpz,
                    zpy,
                    it,
                    iw,
                ) = row
                section = BeamSection(
                    designation=str(designation).strip(),
                    type_name=str(type_name or "").strip(),
                    mass_per_meter_kg=float(mass or 0.0),
                    area_cm2=float(area or 0.0),
                    depth_mm=float(depth or 0.0),
                    flange_width_mm=float(flange_width or 0.0),
                    web_thickness_mm=float(web_thickness or 0.0),
                    flange_thickness_mm=float(flange_thickness or 0.0),
                    root_radius_mm=float(r1 or 0.0),
                    toe_radius_mm=float(r2 or 0.0),
                    moment_of_inertia_zz_cm4=float(iz or 0.0),
                    moment_of_inertia_yy_cm4=float(iy or 0.0),
                    radius_of_gyration_z_cm=float(rz or 0.0),
                    radius_of_gyration_y_cm=float(ry or 0.0),
                    elastic_section_modulus_z_cm3=float(zz or 0.0),
                    elastic_section_modulus_y_cm3=float(zy or 0.0),
                    plastic_section_modulus_z_cm3=float(zpz or 0.0),
                    plastic_section_modulus_y_cm3=float(zpy or 0.0),
                    torsion_constant_cm4=float(it or 0.0),
                    warping_constant_cm6=float(iw or 0.0),
                )
                self._sections[section.designation] = section
                self._outlines[section.designation] = {
                    "designation": section.designation,
                    "depth_mm": section.depth_mm,
                    "top_flange_width_mm": section.flange_width_mm,
                    "bottom_flange_width_mm": section.flange_width_mm,
                    "web_thickness_mm": section.web_thickness_mm,
                    "top_flange_thickness_mm": section.flange_thickness_mm,
                    "bottom_flange_thickness_mm": section.flange_thickness_mm,
                }
        finally:
            connection.close()

    def list_available_sections(self) -> Dict[str, BeamSection]:
        return dict(self._sections)

    def get_beam_profile(self, designation: str) -> Optional[BeamSection]:
        if not designation:
            return None
        return self._sections.get(designation.strip())

    def get_rolled_section(self, designation: str) -> Optional[dict]:
        if not designation:
            return None
        return self._outlines.get(designation.strip())


girder_properties = GirderSectionCatalog()


class _ReadOnlyCellDelegate(QStyledItemDelegate):
    """Render read-only table cells in a muted gray, regardless of selection."""

    _bg = QColor("#fafafa")
    _text = QColor("#666666")

    def paint(self, painter, option, index):  # noqa: N802 (Qt naming)
        opt = QStyleOptionViewItem(option)
        # Keep read-only cells gray even when the row is selected.
        if opt.state & QStyle.State_Selected:
            opt.state &= ~QStyle.State_Selected
        opt.backgroundBrush = self._bg
        opt.palette.setColor(QPalette.Base, self._bg)
        opt.palette.setColor(QPalette.Text, self._text)
        super().paint(painter, opt, index)


class _EndDistanceDelegate(QStyledItemDelegate):
    """Make the End column feel editable (white) with a visible edit affordance."""

    _bg = QColor("#ffffff")
    _border = QColor("#c0c0c0")

    def paint(self, painter, option, index):  # noqa: N802 (Qt naming)
        # Keep End cells white even when the row is selected.
        opt = QStyleOptionViewItem(option)
        if opt.state & QStyle.State_Selected:
            opt.state &= ~QStyle.State_Selected

        opt.backgroundBrush = self._bg
        opt.palette.setColor(QPalette.Base, self._bg)

        super().paint(painter, opt, index)

        # Border indicates "editable".
        painter.save()
        pen = QPen(self._border)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRoundedRect(opt.rect.adjusted(3, 3, -3, -3), 4, 4)
        painter.restore()

    def createEditor(self, parent, option, index):  # noqa: N802 (Qt naming)
        editor = QLineEdit(parent)
        editor.setAlignment(Qt.AlignCenter)
        editor.setValidator(QDoubleValidator(0.0, 1e12, 3, editor))
        editor.setStyleSheet(
            "QLineEdit { padding: 0px 4px; border: 2px solid #90AF13; border-radius: 4px; "
            "background: #ffffff; color: #000000; selection-background-color: #90AF13; selection-color: #ffffff; }"
        )
        return editor

    def setEditorData(self, editor, index):  # noqa: N802 (Qt naming)
        value = index.data() or ""
        editor.setText(str(value))
        editor.selectAll()

    def setModelData(self, editor, model, index):  # noqa: N802 (Qt naming)
        model.setData(index, editor.text())


class _BoundsDialog(QDialog):
    def __init__(self, title: str, bounds: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setStyleSheet("QDialog { background: #ffffff; border: 1px solid #90AF13; }")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(1, 1, 1, 1)
        root_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(parent=self)
        self.title_bar.setTitle(title)
        root_layout.addWidget(self.title_bar)

        content = QWidget(self)
        content.setStyleSheet("background: #f3f3f3;")
        root_layout.addWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(22, 16, 22, 16)
        layout.setSpacing(12)

        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(14)
        form_grid.setVerticalSpacing(10)

        lower = float(bounds.get("lower", 0.0))
        upper = float(bounds.get("upper", 0.0))
        increment = float(bounds.get("increment", 0.0))

        self.lower_input = QLineEdit(f"{lower:.2f}")
        self.upper_input = QLineEdit(f"{upper:.2f}")
        self.increment_input = QLineEdit(f"{increment:.2f}")

        for line_edit in (self.lower_input, self.upper_input, self.increment_input):
            line_edit.setValidator(QDoubleValidator(0.0, 1e12, 3, line_edit))
            line_edit.setMinimumHeight(34)
            line_edit.setStyleSheet(
                "QLineEdit {"
                " border: 1px solid #c8c8c8; border-radius: 8px;"
                " background: #ffffff; color: #111111; padding: 6px 10px; font-size: 13px;"
                "}"
            )

        labels = (
            ("Lower Bound:", self.lower_input),
            ("Upper Bound:", self.upper_input),
            ("Increment:", self.increment_input),
        )
        for row, (text, widget) in enumerate(labels):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-size: 12px; color: #202020; background: transparent;")
            form_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
            form_grid.addWidget(widget, row, 1)

        layout.addLayout(form_grid)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 4, 0, 0)
        button_row.setSpacing(10)
        button_row.addStretch(1)

        cancel_btn = QPushButton("Cancel")
        ok_btn = QPushButton("OK")
        for button in (cancel_btn, ok_btn):
            button.setMinimumHeight(34)
            button.setStyleSheet(
                "QPushButton {"
                " background: #ffffff; color: #111111;"
                " border: 1px solid #1f1f1f; border-radius: 10px;"
                " min-width: 86px;"
                " font-size: 12px; font-weight: 700;"
                "}"
                "QPushButton:hover { background: #f3f3f3; }"
                "QPushButton:pressed { background: #e9e9e9; }"
            )

        cancel_btn.clicked.connect(self.reject)
        ok_btn.clicked.connect(self._on_accept)
        button_row.addWidget(cancel_btn)
        button_row.addWidget(ok_btn)
        layout.addLayout(button_row)

        self._result = None

    def _on_accept(self) -> None:
        lower = self._parse_positive(self.lower_input.text())
        upper = self._parse_positive(self.upper_input.text())
        increment = self._parse_positive(self.increment_input.text())

        if lower is None or upper is None or increment is None:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Warning)
            box.setWindowTitle("Invalid Bounds")
            box.setText("Please enter valid positive numeric values.")
            box.setStandardButtons(QMessageBox.Ok)
            box.exec()
            return
        if upper <= lower:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Warning)
            box.setWindowTitle("Invalid Bounds")
            box.setText("Upper bound must be greater than lower bound.")
            box.setStandardButtons(QMessageBox.Ok)
            box.exec()
            return
        if increment <= 0.0:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Warning)
            box.setWindowTitle("Invalid Bounds")
            box.setText("Increment must be greater than zero.")
            box.setStandardButtons(QMessageBox.Ok)
            box.exec()
            return

        self._result = {
            "lower": float(lower),
            "upper": float(upper),
            "increment": float(increment),
        }
        self.accept()

    @staticmethod
    def _parse_positive(text: str) -> Optional[float]:
        try:
            return float(str(text).strip())
        except Exception:
            return None

    def result_bounds(self) -> Optional[dict]:
        return self._result


class _ThicknessSelectionDialog(QDialog):
    def __init__(self, title: str, selected_values: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.setModal(True)
        self.setMinimumSize(620, 520)
        self.setStyleSheet("QDialog { background: #ffffff; border: 1px solid #90AF13; }")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(1, 1, 1, 1)
        root_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(parent=self)
        self.title_bar.setTitle(title)
        root_layout.addWidget(self.title_bar)

        content = QWidget(self)
        content.setStyleSheet("background: #f3f3f3;")
        root_layout.addWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(14)

        top_row = QHBoxLayout()
        top_row.setSpacing(18)

        left_col = QVBoxLayout()
        left_col.setSpacing(8)
        left_lbl = QLabel("Available:")
        left_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #1f1f1f;")
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.available_list.setStyleSheet(
            "QListWidget { background: #ffffff; border: 1px solid #c8c8c8; border-radius: 10px;"
            " font-size: 14px; color: #1f1f1f; padding: 4px; }"
        )
        left_col.addWidget(left_lbl)
        left_col.addWidget(self.available_list, 1)

        buttons_col = QVBoxLayout()
        buttons_col.setSpacing(10)
        buttons_col.addStretch(1)
        self.move_all_right_btn = self._move_btn(">>", True)
        self.move_right_btn = self._move_btn(">", False)
        self.move_left_btn = self._move_btn("<", False)
        self.move_all_left_btn = self._move_btn("<<", True)
        buttons_col.addWidget(self.move_all_right_btn)
        buttons_col.addWidget(self.move_right_btn)
        buttons_col.addWidget(self.move_left_btn)
        buttons_col.addWidget(self.move_all_left_btn)
        buttons_col.addStretch(1)

        right_col = QVBoxLayout()
        right_col.setSpacing(8)
        right_lbl = QLabel("Selected:")
        right_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #1f1f1f;")
        self.selected_list = QListWidget()
        self.selected_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.selected_list.setStyleSheet(
            "QListWidget { background: #ffffff; border: 1px solid #c8c8c8; border-radius: 10px;"
            " font-size: 14px; color: #1f1f1f; padding: 4px; }"
        )
        right_col.addWidget(right_lbl)
        right_col.addWidget(self.selected_list, 1)

        top_row.addLayout(left_col, 1)
        top_row.addLayout(buttons_col)
        top_row.addLayout(right_col, 1)
        layout.addLayout(top_row, 1)

        submit_row = QHBoxLayout()
        submit_row.addStretch(1)
        submit_btn = QPushButton("Submit")
        submit_btn.setMinimumHeight(40)
        submit_btn.setMinimumWidth(220)
        submit_btn.setStyleSheet(
            "QPushButton {"
            " background: #90AF13; color: #ffffff;"
            " border: 1px solid #90AF13; border-radius: 10px;"
            " font-size: 14px; font-weight: 700;"
            "}"
            "QPushButton:hover { background: #7f9d11; }"
            "QPushButton:pressed { background: #6f8b0f; }"
        )
        submit_btn.clicked.connect(self.accept)
        submit_row.addWidget(submit_btn)
        submit_row.addStretch(1)
        layout.addLayout(submit_row)

        selected = [v for v in selected_values if v in SAIL_APPROVED_THICKNESS_VALUES]
        if not selected:
            selected = list(SAIL_APPROVED_THICKNESS_VALUES)
        available = [v for v in SAIL_APPROVED_THICKNESS_VALUES if v not in selected]

        self.available_list.addItems(available)
        self.selected_list.addItems(selected)

        self.move_all_right_btn.clicked.connect(self._move_all_right)
        self.move_right_btn.clicked.connect(self._move_selected_right)
        self.move_left_btn.clicked.connect(self._move_selected_left)
        self.move_all_left_btn.clicked.connect(self._move_all_left)

        self._refresh_button_states()
        self.available_list.itemSelectionChanged.connect(self._refresh_button_states)
        self.selected_list.itemSelectionChanged.connect(self._refresh_button_states)

    def _move_btn(self, text: str, primary: bool) -> QPushButton:
        button = QPushButton(text)
        button.setMinimumSize(84, 48)
        if primary:
            button.setStyleSheet(
                "QPushButton { background: #90AF13; color: #ffffff; border: 1px solid #90AF13;"
                " border-radius: 10px; font-size: 18px; font-weight: 800; }"
                "QPushButton:hover { background: #7f9d11; }"
                "QPushButton:pressed { background: #6f8b0f; }"
                "QPushButton:disabled { background: #d2d2d2; color: #8a8a8a; border-color: #d2d2d2; }"
            )
        else:
            button.setStyleSheet(
                "QPushButton { background: #cfcfcf; color: #6b6b6b; border: 1px solid #cfcfcf;"
                " border-radius: 10px; font-size: 18px; font-weight: 800; }"
                "QPushButton:disabled { background: #dcdcdc; color: #9a9a9a; border-color: #dcdcdc; }"
            )
        return button

    def _move_selected_right(self) -> None:
        self._move_items(self.available_list, self.selected_list, selected_only=True)

    def _move_selected_left(self) -> None:
        self._move_items(self.selected_list, self.available_list, selected_only=True)

    def _move_all_right(self) -> None:
        self._move_items(self.available_list, self.selected_list, selected_only=False)

    def _move_all_left(self) -> None:
        self._move_items(self.selected_list, self.available_list, selected_only=False)

    def _move_items(self, source: QListWidget, target: QListWidget, selected_only: bool) -> None:
        rows = []
        if selected_only:
            rows = sorted([source.row(item) for item in source.selectedItems()], reverse=True)
        else:
            rows = list(range(source.count() - 1, -1, -1))

        moved = []
        for row in rows:
            item = source.takeItem(row)
            if item is not None:
                moved.append(item.text())
        for text in moved:
            target.addItem(text)

        self._sort_list(self.available_list)
        self._sort_list(self.selected_list)
        self._refresh_button_states()

    def _sort_list(self, widget: QListWidget) -> None:
        values = []
        for i in range(widget.count()):
            values.append(widget.item(i).text())
        values = sorted(values, key=lambda v: SAIL_APPROVED_THICKNESS_VALUES.index(v) if v in SAIL_APPROVED_THICKNESS_VALUES else 9999)
        widget.clear()
        widget.addItems(values)

    def _refresh_button_states(self) -> None:
        self.move_right_btn.setEnabled(bool(self.available_list.selectedItems()))
        self.move_left_btn.setEnabled(bool(self.selected_list.selectedItems()))
        self.move_all_right_btn.setEnabled(self.available_list.count() > 0)
        self.move_all_left_btn.setEnabled(self.selected_list.count() > 0)

    def selected_values(self) -> List[str]:
        return [self.selected_list.item(i).text() for i in range(self.selected_list.count())]


class GirderDetailsTab(QWidget):
    """Tab for Girder Details styled to match the provided reference."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.welded_rows = []
        self.rolled_rows = []
        self.symmetry_row = []
        self.web_type_row = []
        self.section_property_inputs = {}
        # Segment chain is stored per girder:
        # { 'G1': [ {'id': 'G1M1', 'start': 0.0, 'end': 30.0}, ... ], 'G2': [...] }
        self.segment_chain: Dict[str, List[Dict[str, float]]] = {}
        self._suppress_distance_updates = False
        self._suppress_member_state_updates = False
        # Always expose up to MAX_GIRDER_COUNT main girders in the UI.
        self.available_girders = [f"G{i}" for i in range(1, MAX_GIRDER_COUNT + 1)]
        self._girder_combo_connected = False

        # Master-Detail UI state
        self._current_girder: str = self.available_girders[0] if self.available_girders else "G1"
        self._current_segment_index: int = 0

        # Per-member (Member ID) persistence + dirty tracking.
        # {"G1": {"G1M1": {"inputs": {...}}}}
        self._member_state: Dict[str, Dict[str, dict]] = {}
        self._dirty_members: set[tuple[str, str]] = set()
        self._last_member_combo_index: int = 0
        self._suppress_member_switch_prompt: bool = True
        # Template state used when a member is first visited.
        self._default_member_state: Optional[dict] = None
        # Section Inputs widgets are built later than the overview card. Avoid
        # applying/storing per-member UI state before they exist.
        self._section_inputs_built: bool = False

        # Segment Manager widgets (right column)
        self.girder_dropdown: Optional[QComboBox] = None
        self.segment_table: Optional[QTableWidget] = None
        self.split_add_button: Optional[QPushButton] = None
        self.split_remove_button: Optional[QPushButton] = None

        # Segment Details widgets (left column)
        self.segment_length_input: Optional[QLineEdit] = None

        # Section Inputs widgets
        self.member_id_combo: Optional[QComboBox] = None
        self._dimension_bounds = {
            "total_depth": {"lower": 200.0, "upper": 2000.0, "increment": 25.0},
            "top_width": {"lower": 100.0, "upper": 1000.0, "increment": 10.0},
            "bottom_width": {"lower": 100.0, "upper": 1000.0, "increment": 10.0},
        }
        self.init_ui()

    def set_design_mode(self, mode_str: str):
        if hasattr(self, "design_combo"):
             self.design_combo.setCurrentText(mode_str)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        main_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        content.setStyleSheet("background-color: white;")

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 0, 10, 10)
        content_layout.setSpacing(12)

        content_layout.addWidget(self._build_overview_card())
        # content_layout.addWidget(self._build_section_card())
        content_layout.addStretch()

    def _build_overview_card(self):
        card = self._create_card_frame()
        outer = QGridLayout(card)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setHorizontalSpacing(16)
        outer.setVerticalSpacing(16)

        def _cad_placeholder(label: str) -> QFrame:
            frame = QFrame()
            frame.setFixedHeight(160)
            frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            frame.setStyleSheet(
                "QFrame { border: 2px dashed #b7b7b7; border-radius: 8px; background: #ffffff; }"
            )
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(0)
            text = QLabel(label)
            text.setAlignment(Qt.AlignCenter)
            text.setStyleSheet("font-size: 12px; font-weight: 700; color: #6f6f6f;")
            layout.addWidget(text)
            return frame

        # LEFT: Select Girder + Total Span (matches reference layout)
        left_panel = self._create_inner_box()
        left_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 10, 12, 10)
        left_layout.setSpacing(10)

        # Placeholder area for CAD diagram (left)
        left_layout.addWidget(_cad_placeholder("CAD Diagram Placeholder"))

        details_box = QWidget()
        details_layout = QGridLayout(details_box)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setHorizontalSpacing(16)
        details_layout.setVerticalSpacing(10)
        details_layout.setColumnMinimumWidth(0, 160)
        details_layout.setColumnStretch(0, 0)
        details_layout.setColumnStretch(1, 1)

        # Keep span mode internally (for existing behavior) but hide it to match the reference UI.
        self.span_combo = QComboBox()
        self.span_combo.addItems(VALUES_GIRDER_SPAN_MODE)
        apply_field_style(self.span_combo)
        self._set_field_width(self.span_combo)
        self.span_combo.currentTextChanged.connect(self._on_span_changed)
        span_label = self._create_label("Span:")
        span_label.setVisible(False)
        self.span_combo.setVisible(False)
        details_layout.addWidget(span_label, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        details_layout.addWidget(self.span_combo, 0, 1)

        details_layout.addWidget(self._create_label("Select Girder:"), 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.girder_dropdown = QComboBox()
        # Display-friendly names while keeping stable internal IDs.
        for girder in self.available_girders:
            label = f"Girder {girder[1:]}" if girder.startswith("G") and girder[1:].isdigit() else girder
            self.girder_dropdown.addItem(label, girder)
        apply_field_style(self.girder_dropdown)
        self._set_field_width(self.girder_dropdown)
        self.girder_dropdown.currentIndexChanged.connect(lambda _idx: self._on_girder_changed(self.girder_dropdown.currentData()))
        details_layout.addWidget(self.girder_dropdown, 1, 1)

        self.length_input = QLineEdit("30")
        apply_field_style(self.length_input)
        self._set_field_width(self.length_input)
        self.length_input.setReadOnly(True)
        self.length_input.setToolTip("Total Span is auto-controlled and cannot be edited here")
        self.length_input.textChanged.connect(self._on_length_changed)
        details_layout.addWidget(self._create_label("Total Span (m):"), 2, 0, Qt.AlignLeft | Qt.AlignVCenter)
        details_layout.addWidget(self.length_input, 2, 1)

        # Exterior/Interior copy buttons layout (Row 3, spans 2 columns)
        copy_buttons_layout = QHBoxLayout()
        copy_buttons_layout.setContentsMargins(0, 0, 0, 0)
        copy_buttons_layout.setSpacing(10)

        self.apply_exterior_button = QPushButton("Apply changes to exterior girders")
        self.apply_exterior_button.setFixedHeight(26)
        self.apply_exterior_button.setStyleSheet(
            "QPushButton { background: #f0f0f0; border: 1px solid #b5b5b5; border-radius: 2px; "
            "padding: 4px 10px; font-size: 11px; color: #000000; font-weight: 400; }"
            "QPushButton:hover { background: #f0f0f0; border: 1px solid #b5b5b5; color: #000000; }"
            "QPushButton:pressed { background: #f0f0f0; border: 1px solid #b5b5b5; color: #000000; }"
            "QPushButton:disabled { color: #8a8a8a; border: 1px solid #cfcfcf; }"
        )
        self.apply_exterior_button.setToolTip("Apply changes to exterior girders (first and last)")
        self.apply_exterior_button.clicked.connect(self._on_apply_exterior_clicked)

        self.apply_interior_button = QPushButton("Apply changes to interior girder")
        self.apply_interior_button.setFixedHeight(26)
        self.apply_interior_button.setStyleSheet(
            "QPushButton { background: #f0f0f0; border: 1px solid #b5b5b5; border-radius: 2px; "
            "padding: 4px 10px; font-size: 11px; color: #000000; font-weight: 400; }"
            "QPushButton:hover { background: #f0f0f0; border: 1px solid #b5b5b5; color: #000000; }"
            "QPushButton:pressed { background: #f0f0f0; border: 1px solid #b5b5b5; color: #000000; }"
            "QPushButton:disabled { color: #8a8a8a; border: 1px solid #cfcfcf; }"
        )
        self.apply_interior_button.setToolTip("Apply changes to interior girder(s)")
        self.apply_interior_button.clicked.connect(self._on_apply_interior_clicked)
        
        copy_buttons_layout.addWidget(self.apply_exterior_button)
        copy_buttons_layout.addWidget(self.apply_interior_button)
        
        details_layout.addLayout(copy_buttons_layout, 3, 0, 1, 2)

        # Hidden legacy fields: still used by existing split/ripple logic.
        self.member_id_input = QLineEdit()
        apply_field_style(self.member_id_input)
        self.member_id_input.setReadOnly(True)
        self.member_id_input.setVisible(False)

        self.distance_start_input = QLineEdit("0")
        apply_field_style(self.distance_start_input)
        self.distance_start_input.setReadOnly(True)
        self.distance_start_input.setVisible(False)

        self.distance_end_input = QLineEdit("30")
        apply_field_style(self.distance_end_input)
        self.distance_end_input.editingFinished.connect(self._on_distance_end_changed)
        self.distance_end_input.setVisible(False)

        self.segment_length_input = QLineEdit("30")
        apply_field_style(self.segment_length_input)
        self.segment_length_input.setReadOnly(True)
        self.segment_length_input.setVisible(False)

        details_layout.addWidget(self.member_id_input, 4, 0, 1, 2)
        details_layout.addWidget(self.distance_start_input, 5, 0, 1, 2)
        details_layout.addWidget(self.distance_end_input, 6, 0, 1, 2)
        details_layout.addWidget(self.segment_length_input, 7, 0, 1, 2)

        left_layout.addWidget(details_box)
        left_layout.addStretch(1)

        # RIGHT: Member segments table with per-row actions
        manager_box = self._create_inner_box()
        manager_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        manager_layout = QVBoxLayout(manager_box)
        manager_layout.setContentsMargins(12, 10, 12, 10)
        manager_layout.setSpacing(10)

        # Placeholder area for CAD diagram (right)
        manager_layout.addWidget(_cad_placeholder("CAD Diagram Placeholder"))

        table_row = QWidget()
        table_row_layout = QHBoxLayout(table_row)
        table_row_layout.setContentsMargins(0, 0, 0, 0)
        table_row_layout.setSpacing(0)

        self.segment_table = QTableWidget(0, 5)
        self.segment_table.setHorizontalHeaderLabels(["Member ID", "Start (m)", "End (m)", "Length (m)", "Action"])
        self.segment_table.horizontalHeader().setVisible(True)
        self.segment_table.verticalHeader().setVisible(False)
        self.segment_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.segment_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.segment_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.segment_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.segment_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.segment_table.setColumnWidth(4, 132)
        self.segment_table.horizontalHeader().setMinimumHeight(34)
        self.segment_table.verticalHeader().setDefaultSectionSize(38)
        self.segment_table.verticalHeader().setMinimumSectionSize(34)
        self.segment_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.segment_table.setShowGrid(True)
        self.segment_table.setGridStyle(Qt.SolidLine)
        self.segment_table.setAlternatingRowColors(True)
        self.segment_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.segment_table.setSelectionMode(QTableWidget.SingleSelection)
        # Allow editing End values (used for split/ripple), other columns remain read-only by item flags.
        self.segment_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked | QTableWidget.EditKeyPressed)
        # Show only ~2 rows; scroll for additional rows.
        _row_h = int(self.segment_table.verticalHeader().defaultSectionSize() or 34)
        _hdr_h = 34
        self.segment_table.setFixedHeight(_hdr_h + (2 * _row_h) + 10)
        self.segment_table.setStyleSheet(
            "QTableWidget { background: #ffffff; border: 1px solid #d6d6d6; border-radius: 6px; gridline-color: #d0d0d0; }"
            "QTableWidget::item { color: #1f1f1f; padding: 4px 6px; }"
            "QTableWidget::item:selected { background: #e8f0c9; color: #1a1a1a; }"
            "QTableWidget::item:focus { outline: none; }"
            "QTableWidget QLineEdit { background: #ffffff; color: #000000; }"
            "QHeaderView::section { background: #f3f3f3; color: #2b2b2b; font-weight: 700; border: 1px solid #d0d0d0; padding: 6px; }"
            "QTableCornerButton::section { background: #f3f3f3; border: 1px solid #d0d0d0; }"
        )
        ro_delegate = _ReadOnlyCellDelegate(self.segment_table)
        self.segment_table.setItemDelegateForColumn(0, ro_delegate)
        self.segment_table.setItemDelegateForColumn(1, ro_delegate)
        self.segment_table.setItemDelegateForColumn(3, ro_delegate)
        self.segment_table.setItemDelegateForColumn(2, _EndDistanceDelegate(self.segment_table))
        self.segment_table.currentCellChanged.connect(self._on_segment_row_changed)
        # Single-click editing for End column (better UX) while keeping row selection.
        self.segment_table.cellClicked.connect(self._on_segment_cell_clicked)
        self.segment_table.itemChanged.connect(self._on_segment_table_item_changed)
        table_row_layout.addWidget(self.segment_table, 1)

        manager_layout.addWidget(table_row)

        # Remove local add to layout, we will build the grid at the end
        # outer.addWidget(left_panel, 1)
        # outer.addWidget(manager_box, 1)

        # Initialize segment chain and UI selections
        self._initialize_segment_chain_if_needed()
        # Default to an editable span (Custom) while keeping legacy span-mode support.
        if self.span_combo.findText("Custom") >= 0:
            self.span_combo.setCurrentText("Custom")
        self._on_span_changed(self.span_combo.currentText())
        self._on_girder_changed(self._current_girder)

        outer.addWidget(left_panel, 0, 0)
        outer.addWidget(manager_box, 0, 1)

        # Build Section Properties (Inputs + Preview) inline with the grid layout
        # for perfect vertical alignment of left/right columns.
        section_container = self._build_section_card()
        # Extract the two main widgets from the section container to place them directly
        # into the main grid layout so they align with the columns above.
        
        # NOTE: _build_section_card returns a container with a QHBoxLayout containing
        # left_column and right_column widgets. We extract them here.
        section_layout = section_container.layout()
        if section_layout and section_layout.count() >= 2:
            left_col_widget = section_layout.itemAt(0).widget()
            right_col_widget = section_layout.itemAt(1).widget()
            
            # Re-parent them to the main card just in case, though adding to layout handles it.
            outer.addWidget(left_col_widget, 1, 0)
            outer.addWidget(right_col_widget, 1, 1)

        # Set column stretch to match left/right panels (equal width usually)
        outer.setColumnStretch(0, 1)
        outer.setColumnStretch(1, 1)

        return card

    # ===== Master-Detail / Segment Chain helpers =====

    @staticmethod
    def _make_segment_id(girder: str, index: int) -> str:
        """Format a segment/member ID as G1M1, G1M2, ..."""
        return f"{girder}M{int(index)}"

    def _migrate_member_state_key(self, girder: str, old_id: str, new_id: str) -> None:
        if not old_id or not new_id or old_id == new_id:
            return
        if girder in self._member_state and old_id in self._member_state[girder] and new_id not in self._member_state[girder]:
            self._member_state[girder][new_id] = self._member_state[girder].pop(old_id)
        if (girder, old_id) in self._dirty_members and (girder, new_id) not in self._dirty_members:
            self._dirty_members.discard((girder, old_id))
            self._dirty_members.add((girder, new_id))

    def _initialize_segment_chain_if_needed(self) -> None:
        """Ensure each available girder has at least one segment spanning the total span."""
        total_span = self._get_total_span() or DEFAULT_MEMBER_LENGTH_M
        if not self.segment_chain:
            for girder in self.available_girders:
                self.segment_chain[girder] = [
                    {"id": self._make_segment_id(girder, 1), "start": 0.0, "end": float(total_span)},
                ]

    def _ensure_girder_segments(self, girder: str) -> List[Dict[str, float]]:
        total_span = self._get_total_span() or DEFAULT_MEMBER_LENGTH_M
        segments = self.segment_chain.get(girder)
        if not segments:
            segments = [{"id": self._make_segment_id(girder, 1), "start": 0.0, "end": float(total_span)}]
            self.segment_chain[girder] = segments

        # Normalize ids to the requested GxMy format, migrating any stored member-state.
        for i, seg in enumerate(segments, start=1):
            desired = self._make_segment_id(girder, i)
            existing = str(seg.get("id") or "").strip()
            if not existing:
                seg["id"] = desired
                continue
            # Migrate legacy pattern like "G1-2" -> "G1M2".
            base, idx = self._split_member_id(existing)
            if base == girder and isinstance(idx, int) and idx >= 1:
                new_id = self._make_segment_id(girder, idx)
                if existing != new_id:
                    self._migrate_member_state_key(girder, existing, new_id)
                    seg["id"] = new_id
            else:
                # Invalid/legacy ID: force canonical sequence and migrate state key.
                self._migrate_member_state_key(girder, existing, desired)
                seg["id"] = desired

        # Keep explicit user-entered starts/ends as-is; only fill missing values.
        if "start" not in segments[0] or segments[0]["start"] is None:
            segments[0]["start"] = 0.0
        for i in range(1, len(segments)):
            if "start" not in segments[i] or segments[i]["start"] is None:
                segments[i]["start"] = float(segments[i - 1].get("end", 0.0))
        if "end" not in segments[-1] or segments[-1]["end"] is None:
            segments[-1]["end"] = float(total_span)
        return segments

    @staticmethod
    def _fmt_m(value: float) -> str:
        text = f"{value:.3f}".rstrip("0").rstrip(".")
        return text if text else "0"

    def _refresh_segment_list(self, girder: str) -> None:
        if not self.segment_table:
            return
        segments = self._ensure_girder_segments(girder)
        self.segment_table.blockSignals(True)
        try:
            # Hard reset row widgets/items each refresh to avoid stale cell-widgets
            # being painted in wrong columns after repeated split/remove updates.
            self.segment_table.clearContents()
            self.segment_table.setRowCount(0)
            self.segment_table.setRowCount(len(segments))
            for row, seg in enumerate(segments):
                # Defensive cleanup: ensure no stale widgets leak into data columns.
                for col in (0, 1, 2, 3):
                    if self.segment_table.cellWidget(row, col) is not None:
                        self.segment_table.removeCellWidget(row, col)

                # Enforce canonical member id at render-time.
                desired_id = self._make_segment_id(girder, row + 1)
                seg_id = str(seg.get("id") or "").strip()
                base, index = self._split_member_id(seg_id)
                if not (base == girder and isinstance(index, int) and index == (row + 1)):
                    if seg_id and seg_id != desired_id:
                        self._migrate_member_state_key(girder, seg_id, desired_id)
                    seg_id = desired_id
                    seg["id"] = seg_id

                start = float(seg.get("start", 0.0))
                end = float(seg.get("end", 0.0))
                length = max(0.0, end - start)

                # Member ID
                id_item = QTableWidgetItem(seg_id)
                id_item.setTextAlignment(Qt.AlignCenter)
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
                id_item.setToolTip("Read-only")
                self.segment_table.setItem(row, 0, id_item)

                start_item = QTableWidgetItem(self._fmt_m(start))
                start_item.setTextAlignment(Qt.AlignCenter)
                start_item.setFlags(start_item.flags() & ~Qt.ItemIsEditable)
                start_item.setToolTip("Read-only")
                self.segment_table.setItem(row, 1, start_item)

                end_item = QTableWidgetItem(self._fmt_m(end))
                end_item.setTextAlignment(Qt.AlignCenter)
                end_item.setToolTip("Editable")
                self.segment_table.setItem(row, 2, end_item)

                length_item = QTableWidgetItem(self._fmt_m(length))
                length_item.setTextAlignment(Qt.AlignCenter)
                length_item.setFlags(length_item.flags() & ~Qt.ItemIsEditable)
                length_item.setToolTip("Read-only")
                self.segment_table.setItem(row, 3, length_item)

                action_widget = self._create_segment_action_widget(row, can_remove=(len(segments) > 1))
                self.segment_table.setCellWidget(row, 4, action_widget)
        finally:
            self.segment_table.blockSignals(False)

        self._sync_remove_button_visibility()
        self._update_segment_action_row_highlight(self._current_segment_index)

    def _sync_remove_button_visibility(self) -> None:
        """Keep per-row remove action disabled when only one segment exists."""
        segments = self._ensure_girder_segments(self._current_girder)
        can_remove = len(segments) > 1

        if self.segment_table is not None:
            for row in range(self.segment_table.rowCount()):
                action_widget = self.segment_table.cellWidget(row, 4)
                if action_widget is None:
                    continue
                remove_btn = action_widget.findChild(QPushButton, "segmentRemoveBtn")
                if remove_btn is not None:
                    remove_btn.setEnabled(can_remove)
                    remove_btn.setToolTip("Remove this segment" if can_remove else "At least one segment is required")

        self._refresh_member_id_combo()

    def _update_segment_action_row_highlight(self, current_row: int | None = None) -> None:
        if self.segment_table is None:
            return
        selected_row = self.segment_table.currentRow() if current_row is None else int(current_row)
        for row in range(self.segment_table.rowCount()):
            action_widget = self.segment_table.cellWidget(row, 4)
            if action_widget is None:
                continue
            bg = "#e8f0c9" if row == selected_row else "transparent"
            action_widget.setStyleSheet(
                "QWidget#segmentActionCell {"
                f" background: {bg};"
                " border: none;"
                "}"
            )

    def _create_segment_action_widget(self, row: int, can_remove: bool) -> QWidget:
        container = QWidget()
        container.setObjectName("segmentActionCell")
        container.setFixedWidth(118)
        container.setMinimumHeight(28)
        container.setMaximumHeight(34)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)
        container.setStyleSheet("QWidget#segmentActionCell { background: transparent; border: none; }")

        add_btn = QPushButton("+")
        add_btn.setObjectName("segmentAddBtn")
        add_btn.setFixedSize(34, 24)
        add_btn.setFocusPolicy(Qt.NoFocus)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setToolTip("Split/Add segment")
        add_btn.setStyleSheet(
            "QPushButton { background-color: #90AF13; color: #111111; border: 1px solid #6f850f; border-radius: 7px; font-weight: 900; font-size: 17px; }"
            "QPushButton:hover { background-color: #7a9410; }"
            "QPushButton:pressed { background-color: #6a840d; }"
        )
        add_btn.clicked.connect(lambda _checked=False, r=row: self._on_add_segment_for_row(r))

        remove_btn = QPushButton("−")
        remove_btn.setObjectName("segmentRemoveBtn")
        remove_btn.setFixedSize(34, 24)
        remove_btn.setFocusPolicy(Qt.NoFocus)
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.setEnabled(can_remove)
        remove_btn.setToolTip("Remove this segment" if can_remove else "At least one segment is required")
        remove_btn.setStyleSheet(
            "QPushButton { background-color: #c72626; color: #ffffff; border: 1px solid #8f1c1c; border-radius: 7px; font-weight: 900; font-size: 17px; }"
            "QPushButton:hover { background-color: #ae1f1f; }"
            "QPushButton:pressed { background-color: #991a1a; }"
            "QPushButton:disabled { background-color: #d6d6d6; color: #8c8c8c; border-color: #d6d6d6; }"
        )
        remove_btn.clicked.connect(lambda _checked=False, r=row: self._on_remove_segment_for_row(r))

        layout.addStretch(1)
        layout.addWidget(add_btn)
        if can_remove:
            layout.addWidget(remove_btn)
        layout.addStretch(1)
        return container

    def _on_add_segment_for_row(self, row: int) -> None:
        if self.segment_table is None:
            return
        row = max(0, min(int(row), self.segment_table.rowCount() - 1))
        self.segment_table.setCurrentCell(row, 2)
        self._current_segment_index = row
        self._on_split_add_clicked()

    def _on_remove_segment_for_row(self, row: int) -> None:
        if self.segment_table is None:
            return
        row = max(0, min(int(row), self.segment_table.rowCount() - 1))
        self.segment_table.setCurrentCell(row, 2)
        self._current_segment_index = row
        self._on_remove_segment_clicked()

    # ===== Member (Member ID) state + dirty tracking =====

    def _current_member_key(self) -> tuple[str, str]:
        segments = self._ensure_girder_segments(self._current_girder)
        if not segments:
            return (self._current_girder, f"{self._current_girder}-1")
        idx = max(0, min(self._current_segment_index, len(segments) - 1))
        seg_id = str(segments[idx].get("id", f"{self._current_girder}-{idx + 1}"))
        return (self._current_girder, seg_id)

    def _ensure_member_state_initialized(self) -> None:
        """Ensure current member has an initial stored state."""
        girder, member_id = self._current_member_key()
        if girder not in self._member_state:
            self._member_state[girder] = {}
        if member_id not in self._member_state[girder]:
            # IMPORTANT: don't capture the *current* UI here because it may still
            # reflect the previously selected member. Use a stable template.
            if self._default_member_state is not None:
                self._member_state[girder][member_id] = copy.deepcopy(self._default_member_state)
            else:
                self._member_state[girder][member_id] = self._capture_member_state()

    def _mark_current_member_dirty(self) -> None:
        if self._suppress_member_state_updates:
            return
        girder, member_id = self._current_member_key()
        self._dirty_members.add((girder, member_id))

    def _is_current_member_dirty(self) -> bool:
        return self._current_member_key() in self._dirty_members

    def has_unsaved_changes(self) -> bool:
        # Show unsaved-warning popups only for the active member the user is
        # currently editing. Other member-level dirty flags are handled when
        # switching member/girder and should not block unrelated tab switches.
        return self._is_current_member_dirty()

    def _commit_current_member_state(self) -> None:
        girder, member_id = self._current_member_key()
        if girder not in self._member_state:
            self._member_state[girder] = {}
        self._member_state[girder][member_id] = self._capture_member_state()
        self._dirty_members.discard((girder, member_id))

    def _capture_member_state(self) -> dict:
        """Capture Section Inputs for the current member (properties are derived)."""
        return {
            "inputs": {
                "design": self.design_combo.currentText() if hasattr(self, "design_combo") else "",
                "type": self.type_combo.currentText() if hasattr(self, "type_combo") else "",
                "support_type": self.support_type_combo.currentText() if hasattr(self, "support_type_combo") else "",
                "symmetry": self.symmetry_combo.currentText() if hasattr(self, "symmetry_combo") else "",
                "total_depth": self.total_depth_input.text() if hasattr(self, "total_depth_input") else "",
                "top_width": self.top_width_input.text() if hasattr(self, "top_width_input") else "",
                "bottom_width": self.bottom_width_input.text() if hasattr(self, "bottom_width_input") else "",
                "total_depth_bounds": dict(self._dimension_bounds.get("total_depth") or {}),
                "top_width_bounds": dict(self._dimension_bounds.get("top_width") or {}),
                "bottom_width_bounds": dict(self._dimension_bounds.get("bottom_width") or {}),
                "web_thickness": self.web_thickness_combo.currentText() if hasattr(self, "web_thickness_combo") else "",
                "top_thickness": self.top_thickness_combo.currentText() if hasattr(self, "top_thickness_combo") else "",
                "bottom_thickness": self.bottom_thickness_combo.currentText() if hasattr(self, "bottom_thickness_combo") else "",
                "web_thickness_value": self.web_thickness_value_input.text() if hasattr(self, "web_thickness_value_input") else "",
                "top_thickness_value": self.top_thickness_value_input.text() if hasattr(self, "top_thickness_value_input") else "",
                "bottom_thickness_value": self.bottom_thickness_value_input.text() if hasattr(self, "bottom_thickness_value_input") else "",
                "support_width": self.support_width_input.text() if hasattr(self, "support_width_input") else "",
                "is_section": self.is_section_combo.currentText() if hasattr(self, "is_section_combo") else "",
                "torsion": self.torsion_combo.currentText() if hasattr(self, "torsion_combo") else "",
                "warping": self.warping_combo.currentText() if hasattr(self, "warping_combo") else "",
                "web_type": self.web_type_combo.currentText() if hasattr(self, "web_type_combo") else "",
            }
        }

    def _apply_member_state(self, state: dict) -> None:
        # During early init, the overview card triggers segment selection before
        # Section Inputs widgets are created.
        if not getattr(self, "_section_inputs_built", False):
            return
        inputs = (state or {}).get("inputs", {})
        self._suppress_member_state_updates = True
        try:
            if inputs.get("design"):
                self.design_combo.setCurrentText(inputs["design"])
            if inputs.get("type"):
                self.type_combo.setCurrentText(inputs["type"])
            if inputs.get("support_type"):
                self.support_type_combo.setCurrentText(inputs["support_type"])
            if inputs.get("symmetry"):
                self.symmetry_combo.setCurrentText(inputs["symmetry"])

            self.total_depth_input.setText(inputs.get("total_depth", ""))
            self.top_width_input.setText(inputs.get("top_width", ""))
            self.bottom_width_input.setText(inputs.get("bottom_width", ""))

            total_depth_bounds = inputs.get("total_depth_bounds")
            if isinstance(total_depth_bounds, dict):
                self._dimension_bounds["total_depth"] = {
                    "lower": float(total_depth_bounds.get("lower", 200.0)),
                    "upper": float(total_depth_bounds.get("upper", 2000.0)),
                    "increment": float(total_depth_bounds.get("increment", 25.0)),
                }

            top_width_bounds = inputs.get("top_width_bounds")
            if isinstance(top_width_bounds, dict):
                self._dimension_bounds["top_width"] = {
                    "lower": float(top_width_bounds.get("lower", 100.0)),
                    "upper": float(top_width_bounds.get("upper", 1000.0)),
                    "increment": float(top_width_bounds.get("increment", 10.0)),
                }

            bottom_width_bounds = inputs.get("bottom_width_bounds")
            if isinstance(bottom_width_bounds, dict):
                self._dimension_bounds["bottom_width"] = {
                    "lower": float(bottom_width_bounds.get("lower", 100.0)),
                    "upper": float(bottom_width_bounds.get("upper", 1000.0)),
                    "increment": float(bottom_width_bounds.get("increment", 10.0)),
                }

            if inputs.get("web_thickness"):
                self.web_thickness_combo.setCurrentText(inputs["web_thickness"])
            if inputs.get("top_thickness"):
                self.top_thickness_combo.setCurrentText(inputs["top_thickness"])
            if inputs.get("bottom_thickness"):
                self.bottom_thickness_combo.setCurrentText(inputs["bottom_thickness"])

            self.web_thickness_value_input.setText(inputs.get("web_thickness_value", ""))
            self.top_thickness_value_input.setText(inputs.get("top_thickness_value", ""))
            self.bottom_thickness_value_input.setText(inputs.get("bottom_thickness_value", ""))
            self.support_width_input.setText(inputs.get("support_width", ""))

            if inputs.get("is_section"):
                self.is_section_combo.setCurrentText(inputs["is_section"])
            if inputs.get("torsion"):
                self.torsion_combo.setCurrentText(inputs["torsion"])
            if inputs.get("warping"):
                self.warping_combo.setCurrentText(inputs["warping"])
            if inputs.get("web_type"):
                self.web_type_combo.setCurrentText(inputs["web_type"])
        finally:
            self._suppress_member_state_updates = False

        self._update_thickness_value_enabled_state()
        self._update_dimension_field_mode()
        self._refresh_bounds_tooltips()
        self._update_preview()

    def _wire_member_dirty_tracking(self) -> None:
        """Mark current member dirty when Section Inputs change."""
        def connect_combo(combo: QComboBox) -> None:
            combo.currentTextChanged.connect(lambda _t: self._mark_current_member_dirty())

        def connect_line(line: QLineEdit) -> None:
            line.textChanged.connect(lambda _t: self._mark_current_member_dirty())

        connect_combo(self.design_combo)
        connect_combo(self.type_combo)
        connect_combo(self.support_type_combo)
        connect_combo(self.symmetry_combo)
        connect_combo(self.web_thickness_combo)
        connect_combo(self.top_thickness_combo)
        connect_combo(self.bottom_thickness_combo)
        connect_combo(self.is_section_combo)
        connect_combo(self.torsion_combo)
        connect_combo(self.warping_combo)
        connect_combo(self.web_type_combo)

        connect_line(self.total_depth_input)
        connect_line(self.top_width_input)
        connect_line(self.bottom_width_input)
        connect_line(self.web_thickness_value_input)
        connect_line(self.top_thickness_value_input)
        connect_line(self.bottom_thickness_value_input)
        connect_line(self.support_width_input)

    def _confirm_switch_if_dirty(self) -> str:
        """Return 'save'|'discard'|'cancel' before switching member."""
        if not self._is_current_member_dirty():
            return "discard"
        _, member_id = self._current_member_key()
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Unsaved Changes")
        box.setText(f"You have unsaved changes for {member_id}. Save before switching?")
        box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        box.setDefaultButton(QMessageBox.Save)
        result = box.exec()
        if result == QMessageBox.Save:
            return "save"
        if result == QMessageBox.Discard:
            self._dirty_members.discard(self._current_member_key())
            return "discard"
        return "cancel"

    def _refresh_member_id_combo(self) -> None:
        """Keep the Member ID dropdown in sync with the current girder's segments."""
        if not self.member_id_combo:
            return
        segments = self._ensure_girder_segments(self._current_girder)
        block = self.member_id_combo.blockSignals(True)
        try:
            current_index = self._current_segment_index
            self.member_id_combo.clear()
            for seg in segments:
                seg_id = str(seg.get("id", ""))
                self.member_id_combo.addItem(seg_id, seg_id)
            if self.member_id_combo.count():
                self.member_id_combo.setCurrentIndex(max(0, min(current_index, self.member_id_combo.count() - 1)))
                self._last_member_combo_index = self.member_id_combo.currentIndex()
        finally:
            self.member_id_combo.blockSignals(block)

    def _on_member_id_combo_changed(self, index: int) -> None:
        if index is None or index < 0:
            return
        if self._suppress_member_switch_prompt:
            self._select_segment_index(int(index))
            self._last_member_combo_index = int(index)
            return
        # Prompt if user is leaving a dirty member without saving.
        if int(index) != int(self._current_segment_index):
            decision = self._confirm_switch_if_dirty()
            if decision == "cancel":
                prev = self.member_id_combo.blockSignals(True)
                try:
                    self.member_id_combo.setCurrentIndex(self._last_member_combo_index)
                finally:
                    self.member_id_combo.blockSignals(prev)
                return
            if decision == "save":
                self._commit_current_member_state()
                # Confirm member-level save immediately (requested UX).
                try:
                    box = QMessageBox(self)
                    box.setIcon(QMessageBox.Information)
                    box.setWindowTitle("Saved")
                    box.setText("Member inputs saved successfully.")
                    box.setStandardButtons(QMessageBox.Ok)
                    box.exec()
                except Exception:
                    pass

        self._select_segment_index(int(index))
        self._last_member_combo_index = int(index)

    def _on_segment_table_item_changed(self, item: QTableWidgetItem) -> None:
        """Bridge UI edits (End column) into the existing split/ripple logic."""
        if not item or self._suppress_distance_updates:
            return
        # Only respond to End column edits.
        if item.column() != 2:
            return

        row = item.row()
        if row is None or row < 0:
            return

        # Select row so downstream logic uses correct current segment index.
        self._current_segment_index = int(row)
        if self.distance_end_input is None:
            return

        self.distance_end_input.setText(item.text())
        self._on_distance_end_changed()

    def _on_segment_cell_clicked(self, row: int, column: int) -> None:
        """Start editing End (m) on single click."""
        if not self.segment_table:
            return
        if row is None or row < 0:
            return
        if column != 2:
            return
        item = self.segment_table.item(row, column)
        if item is None:
            return
        # Ensure the correct row is selected and open the editor immediately.
        self.segment_table.setCurrentCell(row, column)
        self.segment_table.editItem(item)

    def _on_remove_segment_clicked(self) -> None:
        """Remove the selected segment (keeps at least one segment)."""
        girder = self._current_girder
        segments = self._ensure_girder_segments(girder)
        if not segments:
            return
        if len(segments) == 1:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Warning)
            box.setWindowTitle("Cannot Remove")
            box.setText("At least one member segment is required.")
            box.setStandardButtons(QMessageBox.Ok)
            box.exec()
            return

        idx = self._current_segment_index
        idx = max(0, min(int(idx), len(segments) - 1))
        segments.pop(idx)

        # Renormalize starts, enforce last end == total span, and re-id sequentially.
        total_span = float(self._get_total_span() or DEFAULT_MEMBER_LENGTH_M)
        segments[0]["start"] = 0.0
        for i in range(1, len(segments)):
            segments[i]["start"] = float(segments[i - 1].get("end", 0.0))
        segments[-1]["end"] = float(total_span)
        for i, seg in enumerate(segments, start=1):
            old_id = str(seg.get("id") or "").strip()
            new_id = self._make_segment_id(girder, i)
            if old_id and old_id != new_id:
                self._migrate_member_state_key(girder, old_id, new_id)
            seg["id"] = new_id
        self.segment_chain[girder] = segments

        self._refresh_segment_list(girder)
        self._select_segment_index(min(idx, len(segments) - 1))
        self._mark_current_member_dirty()

    def _select_segment_index(self, index: int) -> None:
        segments = self._ensure_girder_segments(self._current_girder)
        if not segments:
            return
        index = max(0, min(index, len(segments) - 1))
        self._current_segment_index = index
        if self.segment_table and self.segment_table.rowCount() > index:
            self.segment_table.blockSignals(True)
            try:
                self.segment_table.setCurrentCell(index, 0)
            finally:
                self.segment_table.blockSignals(False)
        self._load_segment_details(self._current_girder, index)

        # Keep Member ID combo selection aligned without triggering confirmation loops.
        if self.member_id_combo and self.member_id_combo.currentIndex() != index:
            prev = self.member_id_combo.blockSignals(True)
            try:
                self.member_id_combo.setCurrentIndex(index)
            finally:
                self.member_id_combo.blockSignals(prev)
            self._last_member_combo_index = index

        # Load per-member Section Inputs for the selected Member ID.
        if getattr(self, "_section_inputs_built", False):
            self._ensure_member_state_initialized()
            girder, member_id = self._current_member_key()
            stored = self._member_state.get(girder, {}).get(member_id)
            if stored:
                self._apply_member_state(stored)

    def _copy_girder_settings(self, source_girder: str, target_girders: List[str]) -> None:
        """Copy all segments and their properties from source to target girders."""
        if not source_girder or not target_girders:
            return

        # 1. Commit current state to ensure source is up-to-date
        self._commit_current_member_state() # Always capture current UI state first

        # 2. Get the full detailed structure of the source girder
        # source_segments has IDs like G1M1, G1M2...
        source_segments = self._ensure_girder_segments(source_girder)
        
        # We need to map G1My -> GxMy for each target Gx.
        
        successful_targets = []

        for target in target_girders:
            if target == source_girder:
                continue
                
            # Create a FRESH segment list for target based on source geometry
            new_target_segments = []
            
            # Wipe old state for this target to prevent ghost data
            if target in self._member_state:
                self._member_state[target] = {} # Clear properties
            else:
                self._member_state[target] = {}

            for idx, src_seg in enumerate(source_segments):
                # 1. Geometry copy
                # Create a new segment dict with target ID
                target_id = self._make_segment_id(target, idx + 1)
                new_seg = copy.deepcopy(src_seg)
                new_seg["id"] = target_id
                new_target_segments.append(new_seg)

                # 2. Property state copy
                src_id = str(src_seg.get("id"))
                if source_girder in self._member_state and src_id in self._member_state[source_girder]:
                    # Clone the property dict
                    props = copy.deepcopy(self._member_state[source_girder][src_id])
                    self._member_state[target][target_id] = props
            
            # Commit the new geometry chain
            self.segment_chain[target] = new_target_segments
            successful_targets.append(target)
            
        if successful_targets:
            # If target includes *current* girder (unlikely due to check above, but safe), refresh UI
            if self._current_girder in successful_targets:
                 self._refresh_segment_list(self._current_girder)
                 self._select_segment_index(0)

            QMessageBox.information(
                self, 
                "Applied Changes", 
                f"Configuration applied to: {', '.join(successful_targets)}"
            )

    def _on_apply_exterior_clicked(self) -> None:
        """Apply current girder configuration to First and Last girders."""
        if not self.available_girders:
            return
            
        first = self.available_girders[0]
        last = self.available_girders[-1]
        
        # Unique targets, excluding self is handled inside _copy_girder_settings
        targets = sorted(list(set([first, last])))
        
        self._copy_girder_settings(self._current_girder, targets)

    def _on_apply_interior_clicked(self) -> None:
        """Apply current girder configuration to all Interior girders (G2 to Gn-1)."""
        if len(self.available_girders) <= 2:
            QMessageBox.information(self, "Info", "No interior girders available (Total girders < 3).")
            return
            
        targets = self.available_girders[1:-1]
        self._copy_girder_settings(self._current_girder, targets)

    def _load_segment_details(self, girder: str, index: int) -> None:
        segments = self._ensure_girder_segments(girder)
        if not segments:
            return
        index = max(0, min(index, len(segments) - 1))
        seg = segments[index]
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", 0.0))
        length = max(0.0, end - start)

        self._suppress_distance_updates = True
        try:
            self.member_id_input.setText(seg["id"])
            self.distance_start_input.setText(self._fmt_m(start))
            self.distance_end_input.setText(self._fmt_m(end))
            if self.segment_length_input:
                self.segment_length_input.setText(self._fmt_m(length))
        finally:
            self._suppress_distance_updates = False

    def _on_girder_changed(self, girder: str) -> None:
        if not girder:
            return

        girder = str(girder).strip()
        if not girder or girder == getattr(self, "_current_girder", ""):
            return

        # If user is leaving a dirty member, confirm save/discard/cancel.
        # This mirrors Member ID switching behavior and ensures dependent tabs
        # (e.g., Stiffener Details) see the correct per-member design mode.
        if self._is_current_member_dirty():
            decision = self._confirm_switch_if_dirty()
            if decision == "cancel":
                # Revert the dropdown selection back to the previous girder.
                try:
                    if self.girder_dropdown is not None:
                        prev = self.girder_dropdown.blockSignals(True)
                        try:
                            old = getattr(self, "_current_girder", "")
                            idx = self.girder_dropdown.findData(old)
                            if idx >= 0:
                                self.girder_dropdown.setCurrentIndex(idx)
                        finally:
                            self.girder_dropdown.blockSignals(prev)
                except Exception:
                    pass
                return
            if decision == "save":
                self._commit_current_member_state()
                try:
                    box = QMessageBox(self)
                    box.setIcon(QMessageBox.Information)
                    box.setWindowTitle("Saved")
                    box.setText("Member inputs saved successfully.")
                    box.setStandardButtons(QMessageBox.Ok)
                    box.exec()
                except Exception:
                    pass

        self._current_girder = girder
        self._refresh_segment_list(girder)
        self._select_segment_index(0)
        self._sync_remove_button_visibility()

    def _on_segment_row_changed(self, current_row: int, _current_column: int, _previous_row: int, _previous_column: int) -> None:
        if current_row is None or current_row < 0:
            return
        self._update_segment_action_row_highlight(current_row)
        self._select_segment_index(int(current_row))

    def _on_split_add_clicked(self) -> None:
        """Split the selected segment into two equal halves."""
        girder = self._current_girder
        segments = self._ensure_girder_segments(girder)
        if not segments:
            return

        # Get the selected segment index.
        idx = self.segment_table.currentRow()
        if idx < 0:
            idx = len(segments) - 1
            
        current = segments[idx]
        start = float(current.get("start", 0.0))
        end = float(current.get("end", 0.0))
        length = end - start
        
        if length <= 0.01:
            # Too small to split sensibly
            return

        midpoint = start + (length / 2.0)

        # Update current segment end to midpoint
        current["end"] = midpoint
        
        # Insert new segment from midpoint to original end
        new_segment = {"id": "", "start": midpoint, "end": end}
        segments.insert(idx + 1, new_segment)
        
        # 1. Capture existing states mapped to their original indices
        # We need to map the new segment list back to the old states carefully.
        # The new list has one extra element at idx+1.
        
        reordered_states = []
        
        for i in range(len(segments)):
            if i == idx + 1:
                # This is the newly inserted segment.
                # It should inherit properties from the segment it was split from (idx).
                original_index = idx
            elif i <= idx:
                # These segments haven't moved.
                original_index = i
            else:
                # These segments are shifted by 1.
                original_index = i - 1
                
            original_id = self._make_segment_id(girder, original_index + 1)
            
            state = None
            if girder in self._member_state and original_id in self._member_state[girder]:
                state = self._member_state[girder][original_id]
            
            # If duplicating state for the new segment, ensure deep copy
            if i == idx + 1 and state:
                state = copy.deepcopy(state)
                
            reordered_states.append(state)

        # 2. Clear old state for this girder completely
        if girder in self._member_state:
            self._member_state[girder] = {}
            
        # 3. Re-assign IDs and restore states to the new IDs
        for i, seg in enumerate(segments):
            new_id = self._make_segment_id(girder, i + 1)
            seg["id"] = new_id
            
            state_to_restore = reordered_states[i]
            if state_to_restore:
                if girder not in self._member_state:
                    self._member_state[girder] = {}
                self._member_state[girder][new_id] = state_to_restore

        self.segment_chain[girder] = segments

        self._refresh_segment_list(girder)
        # Select the new segment (second half)
        self._select_segment_index(idx + 1)
        self._mark_current_member_dirty()

    # ===== Span/Length + Auto-split handlers =====

    def _on_span_changed(self, span_text):
        """Toggle total span editability.

        - Custom: user can edit total span.
        - Full Length: total span is locked (read-only).
        """
        self.length_input.setReadOnly(True)

        self._initialize_segment_chain_if_needed()
        self._refresh_segment_list(self._current_girder)
        self._select_segment_index(self._current_segment_index)

    def _on_length_changed(self, _):
        """When total span changes, update the chain so the final segment ends at the new span."""
        total_span = self._get_total_span()
        if total_span is None:
            return

        for girder in self.available_girders:
            segments = self._ensure_girder_segments(girder)
            if not segments:
                continue

            # Clamp and remove segments beyond new span.
            pruned: List[Dict[str, float]] = []
            for seg in segments:
                start = float(seg.get("start", 0.0))
                end = float(seg.get("end", 0.0))
                if start >= total_span:
                    break
                seg["end"] = min(end, float(total_span))
                pruned.append(seg)

            if not pruned:
                pruned = [{"id": self._make_segment_id(girder, 1), "start": 0.0, "end": float(total_span)}]

            # Renormalize starts and ids (keep ids stable if possible).
            pruned[0]["start"] = 0.0
            for i in range(1, len(pruned)):
                pruned[i]["start"] = float(pruned[i - 1].get("end", 0.0))
            pruned[-1]["end"] = float(total_span)
            self.segment_chain[girder] = pruned

        self._refresh_segment_list(self._current_girder)
        self._select_segment_index(min(self._current_segment_index, len(self._ensure_girder_segments(self._current_girder)) - 1))

    def _on_distance_end_changed(self):
        """Auto-split algorithm + ripple edit.

        - If user shortens the current *last* segment, a new fill segment is created.
        - If user edits an intermediate segment, the next segment start is updated.
        """
        if self._suppress_distance_updates:
            return
        if not self.distance_end_input:
            return

        girder = self._current_girder
        segments = self._ensure_girder_segments(girder)
        if not segments:
            return

        idx = max(0, min(self._current_segment_index, len(segments) - 1))
        current = segments[idx]

        new_end = self._parse_float(self.distance_end_input.text())
        if new_end is None:
            # Revert to current stored end
            self._load_segment_details(girder, idx)
            return

        total_span = float(self._get_total_span() or DEFAULT_MEMBER_LENGTH_M)
        start = float(current.get("start", 0.0))
        old_end = float(current.get("end", start))

        # Clamp instead of warning popups.
        if new_end < start:
            new_end = start

        is_last = idx == (len(segments) - 1)
        if is_last:
            if new_end > total_span:
                new_end = total_span
        else:
            next_seg = segments[idx + 1]
            next_end = float(next_seg.get("end", total_span))
            if new_end > next_end:
                new_end = next_end

        # Apply edit
        current["end"] = float(new_end)

        if not is_last:
            # Ripple: set the next start = new end
            segments[idx + 1]["start"] = float(new_end)
        else:
            # Split trigger: if user shortens the last segment, create fill segment
            if new_end < old_end and new_end < total_span:
                next_id = self._make_segment_id(girder, len(segments) + 1)
                segments.append({"id": next_id, "start": float(new_end), "end": float(total_span)})
            elif new_end > total_span:
                current["end"] = float(total_span)

        # Renormalize starts for all subsequent segments
        segments[0]["start"] = 0.0
        for i in range(1, len(segments)):
            segments[i]["start"] = float(segments[i - 1].get("end", 0.0))

        # Always enforce last end == total span after edits
        segments[-1]["end"] = float(total_span)
        self.segment_chain[girder] = segments

        # Refresh master list + keep selection
        self._refresh_segment_list(girder)
        self._select_segment_index(idx)
        self._mark_current_member_dirty()

    def _build_section_card(self):
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)

        # Left side - single bordered box (Section Inputs + restraint fields)
        left_column = QWidget()
        left_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_column_layout = QVBoxLayout(left_column)
        left_column_layout.setContentsMargins(0, 0, 0, 0)
        left_column_layout.setSpacing(0)
        left_column_layout.setAlignment(Qt.AlignTop)

        # Section Inputs box (single frame containing all fields)
        section_inputs_box = self._create_inner_box()
        section_inputs_layout = QVBoxLayout(section_inputs_box)
        section_inputs_layout.setContentsMargins(12, 8, 12, 12)
        section_inputs_layout.setSpacing(8)
        section_inputs_layout.setAlignment(Qt.AlignTop)

        section_inputs_title = self._create_label("Section Inputs:")
        section_inputs_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #4b4b4b; border: none;")
        section_inputs_layout.addWidget(section_inputs_title)

        inputs_grid = QGridLayout()
        inputs_grid.setContentsMargins(0, 0, 0, 0)
        inputs_grid.setHorizontalSpacing(16)
        inputs_grid.setVerticalSpacing(10)
        # Match the reference UI's aligned label column.
        inputs_grid.setColumnMinimumWidth(0, 160)
        inputs_grid.setColumnStretch(0, 0)
        inputs_grid.setColumnStretch(1, 1)

        # Member ID (segment selector) - mirrors reference UI.
        self.member_id_combo = QComboBox()
        apply_field_style(self.member_id_combo)
        self._set_field_width(self.member_id_combo)
        self.member_id_combo.currentIndexChanged.connect(self._on_member_id_combo_changed)
        row = self._add_box_row(inputs_grid, 0, "Member ID:", self.member_id_combo)

        # Hidden design combo to maintain compatibility with existing logic
        self.design_combo = QComboBox()
        self.design_combo.addItems(VALUES_GIRDER_DESIGN_MODE)
        self.design_combo.hide()
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(VALUES_GIRDER_TYPE)
        apply_field_style(self.type_combo)
        self._set_field_width(self.type_combo)
        row = self._add_box_row(inputs_grid, row, "Type:", self.type_combo)

        self.symmetry_combo = QComboBox()
        self.symmetry_combo.addItems(VALUES_GIRDER_SYMMETRY)
        apply_field_style(self.symmetry_combo)
        self._set_field_width(self.symmetry_combo)
        row = self._add_box_row(inputs_grid, row, "Symmetry:", self.symmetry_combo, self.symmetry_row)

        self.support_type_combo = QComboBox()
        self.support_type_combo.addItems(VALUES_GIRDER_SUPPORT_TYPE)
        apply_field_style(self.support_type_combo)
        self._set_field_width(self.support_type_combo)

        self.total_depth_widget, self.total_depth_input, self.total_depth_bounds_button = self._create_dimension_input_widget("total_depth")
        row = self._add_box_row(
            inputs_grid,
            row,
            "Total Depth (d, mm):",
            self.total_depth_widget,
            self.welded_rows,
        )

        self.web_thickness_combo = QComboBox()
        self.web_thickness_combo.addItems(VALUES_PROFILE_SCOPE)
        apply_field_style(self.web_thickness_combo)
        self._set_field_width(self.web_thickness_combo, 180)

        self.web_thickness_value_input = self._create_line_edit()
        self._set_field_width(self.web_thickness_value_input, 78)
        self.web_thickness_value_input.setValidator(QDoubleValidator(0.0, 1e12, 3, self.web_thickness_value_input))

        self.web_thickness_widget = self._create_mode_value_widget(self.web_thickness_combo, self.web_thickness_value_input)
        self.web_thickness_value_combo = self._attach_thickness_value_dropdown(
            self.web_thickness_widget,
            self.web_thickness_value_input,
            "web_thickness",
        )
        row = self._add_box_row(
            inputs_grid,
            row,
            "Web Thickness (w<sub>t</sub>, mm):",
            self.web_thickness_widget,
            self.welded_rows,
        )

        self.top_width_widget, self.top_width_input, self.top_width_bounds_button = self._create_dimension_input_widget("top_width")
        row = self._add_box_row(
            inputs_grid,
            row,
            "Width of Top Flange (t<sub>fw</sub>, mm):",
            self.top_width_widget,
            self.welded_rows,
        )

        self.top_thickness_combo = QComboBox()
        self.top_thickness_combo.addItems(VALUES_PROFILE_SCOPE)
        apply_field_style(self.top_thickness_combo)
        self._set_field_width(self.top_thickness_combo, 180)

        self.top_thickness_value_input = self._create_line_edit()
        self._set_field_width(self.top_thickness_value_input, 78)
        self.top_thickness_value_input.setValidator(QDoubleValidator(0.0, 1e12, 3, self.top_thickness_value_input))

        self.top_thickness_widget = self._create_mode_value_widget(self.top_thickness_combo, self.top_thickness_value_input)
        self.top_thickness_value_combo = self._attach_thickness_value_dropdown(
            self.top_thickness_widget,
            self.top_thickness_value_input,
            "top_thickness",
        )
        row = self._add_box_row(
            inputs_grid,
            row,
            "Top Flange Thickness (t<sub>ft</sub>, mm):",
            self.top_thickness_widget,
            self.welded_rows,
        )

        self.bottom_width_widget, self.bottom_width_input, self.bottom_width_bounds_button = self._create_dimension_input_widget("bottom_width")
        row = self._add_box_row(
            inputs_grid,
            row,
            "Width of Bottom Flange (b<sub>fw</sub>, mm):",
            self.bottom_width_widget,
            self.welded_rows,
        )

        self.bottom_thickness_combo = QComboBox()
        self.bottom_thickness_combo.addItems(VALUES_PROFILE_SCOPE)
        apply_field_style(self.bottom_thickness_combo)
        self._set_field_width(self.bottom_thickness_combo, 180)

        self.bottom_thickness_value_input = self._create_line_edit()
        self._set_field_width(self.bottom_thickness_value_input, 78)
        self.bottom_thickness_value_input.setValidator(QDoubleValidator(0.0, 1e12, 3, self.bottom_thickness_value_input))

        self.bottom_thickness_widget = self._create_mode_value_widget(self.bottom_thickness_combo, self.bottom_thickness_value_input)
        self.bottom_thickness_value_combo = self._attach_thickness_value_dropdown(
            self.bottom_thickness_widget,
            self.bottom_thickness_value_input,
            "bottom_thickness",
        )
        row = self._add_box_row(
            inputs_grid,
            row,
            "Bottom Flange Thickness (b<sub>ft</sub>, mm):",
            self.bottom_thickness_widget,
            self.welded_rows,
        )

        self.support_width_input = self._create_line_edit()
        self.support_width_input.setValidator(QDoubleValidator(0.0, 1e12, 3, self.support_width_input))
        row = self._add_box_row(
            inputs_grid,
            row,
            "Support Type:",
            self.support_type_combo,
            self.welded_rows,
        )
        row = self._add_box_row(
            inputs_grid,
            row,
            "Support Width (mm):",
            self.support_width_input,
            self.welded_rows,
        )

        self.is_section_combo = QComboBox()
        self._populate_rolled_section_combo()
        apply_field_style(self.is_section_combo)
        self._set_field_width(self.is_section_combo)
        self._add_box_row(inputs_grid, row, "IS Section:", self.is_section_combo, self.rolled_rows)

        # Append restraint/web fields into the same Section Inputs box (no extra frame / spacing).
        self.torsion_combo = QComboBox()
        apply_field_style(self.torsion_combo)
        self._set_field_width(self.torsion_combo)
        row = self._add_box_row(inputs_grid, row + 1, "Torsional Restraint:", self.torsion_combo)

        self.warping_combo = QComboBox()
        apply_field_style(self.warping_combo)
        self._set_field_width(self.warping_combo)
        row = self._add_box_row(inputs_grid, row, "Warping Restraint:", self.warping_combo)

        self.web_type_combo = QComboBox()
        apply_field_style(self.web_type_combo)
        self._set_field_width(self.web_type_combo)
        self._add_box_row(inputs_grid, row, "Web Type*:", self.web_type_combo, self.web_type_row)

        section_inputs_layout.addLayout(inputs_grid)
        # Prevent the grid rows from stretching vertically (which creates large blank bands
        # above the first input when the right column is taller). Extra height goes below.
        section_inputs_layout.addStretch(1)
        left_column_layout.addWidget(section_inputs_box)
        self._configure_restraint_fields()

        main_layout.addWidget(left_column)

        # Right side - image + section properties box
        right_column = QWidget()
        right_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_column_layout = QVBoxLayout(right_column)
        right_column_layout.setContentsMargins(0, 0, 0, 0)
        right_column_layout.setSpacing(10)

        # Dynamic image box
        image_box = self._create_inner_box()
        image_layout = QVBoxLayout(image_box)
        image_layout.setContentsMargins(10, 10, 10, 10)
        image_layout.setSpacing(5)

        self.section_preview = RolledSectionPreview()
        image_layout.addWidget(self.section_preview, 1)

        self.preview_caption = QLabel("Provide girder inputs to preview")
        self.preview_caption.setAlignment(Qt.AlignCenter)
        self.preview_caption.setStyleSheet(
            "QLabel { font-size: 13px; font-weight: 700; color: #1e1e1e; border: none; padding-top: 6px; font-family: 'Ubuntu Sans', 'Segoe UI', sans-serif; }"
        )
        image_layout.addWidget(self.preview_caption)

        right_column_layout.addWidget(image_box)

        # Section Properties box
        props_box = self._create_inner_box()
        props_layout = QVBoxLayout(props_box)
        props_layout.setContentsMargins(12, 10, 12, 10)
        props_layout.setSpacing(10)

        props_title = self._create_label("Section Properties:")
        props_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #4b4b4b; border: none;")
        props_layout.addWidget(props_title)

        properties_grid = QGridLayout()
        properties_grid.setContentsMargins(0, 0, 0, 0)
        properties_grid.setHorizontalSpacing(16)
        properties_grid.setVerticalSpacing(10)
        properties_grid.setColumnMinimumWidth(0, 160)
        properties_grid.setColumnStretch(0, 0)
        properties_grid.setColumnStretch(1, 1)

        property_fields = [
            ("Mass, M (Kg/m)", "Mass, M (Kg/m)"),
            ("Sectional Area, a (cm2)", "Sectional Area, a (cm<sup>2</sup>)"),
            ("2nd Moment of Area, Iz (cm4)", "2nd Moment of Area, I<sub>z</sub> (cm<sup>4</sup>)"),
            ("2nd Moment of Area, Iy (cm4)", "2nd Moment of Area, I<sub>y</sub> (cm<sup>4</sup>)"),
            ("Radius of Gyration, rz (cm)", "Radius of Gyration, r<sub>z</sub> (cm)"),
            ("Radius of Gyration, ry (cm)", "Radius of Gyration, r<sub>y</sub> (cm)"),
            ("Elastic Modulus, Zz (cm3)", "Elastic Modulus, Z<sub>z</sub> (cm<sup>3</sup>)"),
            ("Elastic Modulus, Zy (cm3)", "Elastic Modulus, Z<sub>y</sub> (cm<sup>3</sup>)"),
            ("Plastic Modulus, Zuz (cm3)", "Plastic Modulus, Z<sub>uz</sub> (cm<sup>3</sup>)"),
            ("Plastic Modulus, Zuy (cm3)", "Plastic Modulus, Z<sub>uy</sub> (cm<sup>3</sup>)"),
            ("Torsion Constant, It (cm4)", "Torsion Constant, I<sub>t</sub> (cm<sup>4</sup>)"),
            ("Warping Constant, Iw (cm6)", "Warping Constant, I<sub>w</sub> (cm<sup>6</sup>)"),
        ]

        for index, (key, label_text) in enumerate(property_fields):
            label = self._create_small_label(label_text)
            line_edit = self._create_line_edit()
            line_edit.setPlaceholderText("")
            properties_grid.addWidget(label, index, 0)
            properties_grid.addWidget(line_edit, index, 1)
            self.section_property_inputs[key] = line_edit

        props_layout.addLayout(properties_grid)
        right_column_layout.addWidget(props_box)

        main_layout.addWidget(right_column)

        self.design_combo.currentTextChanged.connect(self._on_design_changed)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self.support_type_combo.currentTextChanged.connect(self._on_support_type_changed)
        self.is_section_combo.currentTextChanged.connect(self._update_preview)
        for watcher in (self.total_depth_input, self.top_width_input, self.bottom_width_input):
            watcher.textChanged.connect(self._update_preview)
        self.web_thickness_combo.currentTextChanged.connect(
            lambda text: self._on_thickness_mode_changed("web_thickness", text)
        )
        self.top_thickness_combo.currentTextChanged.connect(
            lambda text: self._on_thickness_mode_changed("top_thickness", text)
        )
        self.bottom_thickness_combo.currentTextChanged.connect(
            lambda text: self._on_thickness_mode_changed("bottom_thickness", text)
        )
        for watcher in (self.web_thickness_value_input, self.top_thickness_value_input, self.bottom_thickness_value_input):
            watcher.textChanged.connect(self._update_preview)
        self._on_design_changed(self.design_combo.currentText())
        self._on_type_changed(self.type_combo.currentText())
        self._on_support_type_changed(self.support_type_combo.currentText())
        self._update_thickness_value_enabled_state()
        self._update_dimension_field_mode()
        self._refresh_bounds_tooltips()

        # Capture a stable template state for new members.
        self._default_member_state = self._capture_member_state()

        # Track per-member edits and ensure current member has a baseline saved state.
        self._wire_member_dirty_tracking()
        self._section_inputs_built = True
        self._refresh_member_id_combo()
        # Now that Section Inputs exist, sync UI state to current segment and seed
        # per-member state from the visible defaults.
        self._select_segment_index(self._current_segment_index)
        self._suppress_member_switch_prompt = False

        return container

    def _create_card_frame(self):
        frame = QFrame()
        frame.setObjectName("girderCard")
        frame.setStyleSheet("QFrame#girderCard { background-color: white; border: 1px solid #cfcfcf; border-radius: 10px; }")
        return frame

    def _create_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 12px; color: #2f2f2f; font-weight: 600; background: transparent;")
        label.setAutoFillBackground(False)
        return label

    def _create_small_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 10px; color: #5a5a5a; background: transparent;")
        label.setAutoFillBackground(False)
        return label

    def _create_line_edit(self):
        line_edit = QLineEdit()
        apply_field_style(line_edit)
        self._set_field_width(line_edit)
        return line_edit

    def _create_mode_value_widget(self, mode_combo: QComboBox, value_input: QLineEdit) -> QWidget:
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._set_field_width(widget, 180)

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(mode_combo)
        layout.addWidget(value_input)
        return widget

    def _attach_thickness_value_dropdown(self, wrapper: QWidget, value_input: QLineEdit, field_key: str) -> QComboBox:
        combo = QComboBox()
        combo.addItems(SAIL_APPROVED_THICKNESS_VALUES)
        apply_field_style(combo)
        combo.setVisible(False)
        self._set_field_width(combo, 180)

        combo.currentTextChanged.connect(lambda text, inp=value_input: inp.setText(str(text or "")))
        combo.currentTextChanged.connect(lambda _text: self._mark_current_member_dirty())
        combo.currentTextChanged.connect(lambda _text: self._update_preview())

        layout = wrapper.layout()
        if layout is not None:
            layout.addWidget(combo)
        return combo

    def _sync_thickness_value_dropdown(self, field_key: str) -> None:
        value_input = getattr(self, f"{field_key}_value_input", None)
        value_combo = getattr(self, f"{field_key}_value_combo", None)
        if value_input is None or value_combo is None:
            return
        first = ""
        selected = self._parse_selected_thickness_values(value_input.text())
        if selected:
            first = selected[0]
        else:
            parsed = str(value_input.text() or "").strip()
            if parsed in SAIL_APPROVED_THICKNESS_VALUES:
                first = parsed
        if not first:
            first = SAIL_APPROVED_THICKNESS_VALUES[0]
            value_input.setText(first)

        prev = value_combo.blockSignals(True)
        try:
            idx = value_combo.findText(first, Qt.MatchFixedString)
            value_combo.setCurrentIndex(idx if idx >= 0 else 0)
        finally:
            value_combo.blockSignals(prev)

    def _parse_selected_thickness_values(self, text: str) -> List[str]:
        chunks = [c.strip() for c in str(text or "").split(",") if str(c).strip()]
        return [v for v in chunks if v in SAIL_APPROVED_THICKNESS_VALUES]

    def _on_thickness_mode_changed(self, field_key: str, _text: str) -> None:
        self._update_thickness_value_enabled_state()
        self._update_preview()

        # Avoid auto-popup during restore/init signal cascades.
        if self._suppress_member_state_updates or not getattr(self, "_section_inputs_built", False):
            return

        combo = getattr(self, f"{field_key}_combo", None)
        if combo is None:
            return
        if not self._is_custom_thickness_mode(combo):
            return

        is_welded = (self.type_combo.currentText() or "").strip().lower() == "welded"
        is_custom_design = (self.design_combo.currentText() or "").strip().lower() == "customized"
        if is_welded and (not is_custom_design):
            self._open_thickness_values_dialog(field_key)

    def _open_thickness_values_dialog(self, field_key: str) -> None:
        value_input = getattr(self, f"{field_key}_value_input", None)
        if value_input is None:
            return

        selected = self._parse_selected_thickness_values(value_input.text())
        titles = {
            "web_thickness": "Select Values: Web Thickness",
            "top_thickness": "Select Values: Top Flange Thickness",
            "bottom_thickness": "Select Values: Bottom Flange Thickness",
        }
        dialog = _ThicknessSelectionDialog(titles.get(field_key, "Select Values"), selected, self)
        if dialog.exec() != QDialog.Accepted:
            return

        chosen = dialog.selected_values()
        value_input.setText(", ".join(chosen))
        self._sync_thickness_value_dropdown(field_key)
        self._mark_current_member_dirty()
        self._update_preview()

    def _create_dimension_input_widget(self, field_key: str):
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._set_field_width(widget, 180)

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        value_input = self._create_line_edit()
        value_input.setValidator(QDoubleValidator(0.0, 1e12, 3, value_input))

        bounds_button = QPushButton("Set Bounds")
        bounds_button.setCursor(Qt.PointingHandCursor)
        bounds_button.setMinimumHeight(28)
        bounds_button.setStyleSheet(
            "QPushButton {"
            " border: 1px solid #2f2f2f; border-radius: 8px;"
            " background: #ffffff; color: #111111; font-size: 12px; font-weight: 700;"
            " padding: 4px 10px;"
            "}"
            "QPushButton:hover { background: #f2f2f2; }"
            "QPushButton:pressed { background: #e9e9e9; }"
        )
        bounds_button.clicked.connect(lambda _checked=False, key=field_key: self._open_bounds_dialog(key))

        layout.addWidget(value_input)
        layout.addWidget(bounds_button)
        return widget, value_input, bounds_button

    def _update_dimension_field_mode(self) -> None:
        is_custom = (self.design_combo.currentText() or "").strip().lower() == "customized"
        is_welded = (self.type_combo.currentText() or "").strip().lower() == "welded"

        for field_key in ("total_depth", "top_width", "bottom_width"):
            value_input = getattr(self, f"{field_key}_input", None)
            bounds_button = getattr(self, f"{field_key}_bounds_button", None)
            if value_input is None or bounds_button is None:
                continue

            show_line_edit = bool(is_custom and is_welded)
            value_input.setVisible(show_line_edit)
            value_input.setEnabled(show_line_edit)
            bounds_button.setVisible((not show_line_edit) and is_welded)
            bounds_button.setEnabled((not show_line_edit) and is_welded)

    def _default_dimension_bounds(self, field_key: str) -> dict:
        defaults = {
            "total_depth": {"lower": 200.0, "upper": 2000.0, "increment": 25.0},
            "top_width": {"lower": 100.0, "upper": 1000.0, "increment": 10.0},
            "bottom_width": {"lower": 100.0, "upper": 1000.0, "increment": 10.0},
        }
        return dict(defaults.get(field_key, {"lower": 0.0, "upper": 0.0, "increment": 0.0}))

    def _normalized_dimension_bounds(self, field_key: str) -> dict:
        defaults = self._default_dimension_bounds(field_key)
        current = self._dimension_bounds.get(field_key) or {}
        out = {}
        for key in ("lower", "upper", "increment"):
            try:
                out[key] = float(current.get(key, defaults[key]))
            except Exception:
                out[key] = float(defaults[key])
        return out

    def _format_bounds_tooltip(self, field_key: str) -> str:
        bounds = self._normalized_dimension_bounds(field_key)
        try:
            lower = float(bounds.get("lower", 0.0))
            upper = float(bounds.get("upper", 0.0))
            increment = float(bounds.get("increment", 0.0))
        except Exception:
            lower, upper, increment = 0.0, 0.0, 0.0
        return (
            f"Lower Bound: {lower:.2f}\n"
            f"Upper Bound: {upper:.2f}\n"
            f"Increment: {increment:.2f}"
        )

    def _refresh_bounds_tooltips(self) -> None:
        for field_key in ("total_depth", "top_width", "bottom_width"):
            bounds_button = getattr(self, f"{field_key}_bounds_button", None)
            if bounds_button is not None:
                bounds_button.setToolTip(self._format_bounds_tooltip(field_key))

    def _open_bounds_dialog(self, field_key: str) -> None:
        current = self._normalized_dimension_bounds(field_key)
        titles = {
            "total_depth": "Select Bound: Total Depth",
            "top_width": "Select Bound: Topflange Width",
            "bottom_width": "Select Bound: Bottomflange Width",
        }
        dialog = _BoundsDialog(titles.get(field_key, "Select Bound"), current, self)
        if dialog.exec() != QDialog.Accepted:
            return

        result = dialog.result_bounds()
        if not isinstance(result, dict):
            return

        self._dimension_bounds[field_key] = {
            "lower": float(result.get("lower", 0.0)),
            "upper": float(result.get("upper", 0.0)),
            "increment": float(result.get("increment", 0.0)),
        }
        self._refresh_bounds_tooltips()
        self._mark_current_member_dirty()

    def _is_custom_thickness_mode(self, combo: QComboBox) -> bool:
        return (combo.currentText() or "").strip().lower() == "custom"

    def _update_thickness_value_enabled_state(self) -> None:
        is_welded = self.type_combo.currentText().lower() == "welded"
        is_custom_design = self.design_combo.currentText().lower() == "customized"
        allow_inputs = is_welded and is_custom_design

        for field_key, mode_combo, value_input, value_combo, wrapper in (
            (
                "web_thickness",
                getattr(self, "web_thickness_combo", None),
                getattr(self, "web_thickness_value_input", None),
                getattr(self, "web_thickness_value_combo", None),
                getattr(self, "web_thickness_widget", None),
            ),
            (
                "top_thickness",
                getattr(self, "top_thickness_combo", None),
                getattr(self, "top_thickness_value_input", None),
                getattr(self, "top_thickness_value_combo", None),
                getattr(self, "top_thickness_widget", None),
            ),
            (
                "bottom_thickness",
                getattr(self, "bottom_thickness_combo", None),
                getattr(self, "bottom_thickness_value_input", None),
                getattr(self, "bottom_thickness_value_combo", None),
                getattr(self, "bottom_thickness_widget", None),
            ),
        ):
            if not mode_combo or not value_input:
                continue

            is_custom_mode = self._is_custom_thickness_mode(mode_combo)

            # Customized mode: one-box dropdown only (SAIL values).
            if allow_inputs:
                if mode_combo.currentText().strip().lower() != "custom":
                    prev = mode_combo.blockSignals(True)
                    mode_combo.setCurrentText("Custom")
                    mode_combo.blockSignals(prev)

                mode_combo.setVisible(False)
                mode_combo.setEnabled(False)

                value_input.setVisible(False)
                value_input.setEnabled(False)
                value_input.setReadOnly(True)

                if value_combo is not None:
                    value_combo.setVisible(True)
                    value_combo.setEnabled(True)
                    self._sync_thickness_value_dropdown(field_key)

                if wrapper is not None:
                    self._set_field_width(wrapper, 180)
                continue

            # Optimized mode: mode combo only; custom opens popup directly.
            mode_combo.setVisible(is_welded)
            mode_combo.setEnabled(is_welded)

            value_input.setVisible(False)
            value_input.setEnabled(False)
            value_input.setReadOnly(True)

            if value_combo is not None:
                value_combo.setVisible(False)
                value_combo.setEnabled(False)

            if wrapper is not None:
                self._set_field_width(wrapper, 180)
            self._set_field_width(mode_combo, 180)

    def _add_section_row(self, layout, row, text, widget, tracker=None):
        label = self._create_label(text)
        widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._set_field_width(widget)
        layout.addWidget(label, row, 0)
        layout.addWidget(widget, row, 1)
        if tracker is not None:
            tracker.append((label, widget))
        return row + 1

    def _set_field_width(self, widget, width=180):
        widget.setMaximumWidth(width)
        widget.setMinimumWidth(min(width, 140))
        widget.setMinimumHeight(28)
        widget.setMaximumHeight(40)

    def _setup_girder_selector(self):
        if not hasattr(self, "select_girder_combo"):
            return
        if not self._girder_combo_connected:
            if hasattr(self.select_girder_combo, "checkedItemsChanged"):
                self.select_girder_combo.checkedItemsChanged.connect(self._on_girders_selection_changed)
            else:
                self.select_girder_combo.currentTextChanged.connect(self._on_girders_selection_changed)
            self._girder_combo_connected = True
        self._on_girders_selection_changed()

    def _refresh_girder_combo_items(self, preferred_selection: Optional[List[str]] = None) -> None:
        if not hasattr(self, "select_girder_combo"):
            return
        if hasattr(self.select_girder_combo, "checked_items"):
            # Preserve multi-selection if possible.
            current_selection = preferred_selection or self.select_girder_combo.checked_items() or []
            desired = [g for g in current_selection if g in self.available_girders]

            block = self.select_girder_combo.blockSignals(True)
            try:
                # Temporarily suppress the internal toggle handler while rebuilding.
                if hasattr(self.select_girder_combo, "_updating_selection"):
                    self.select_girder_combo._updating_selection = True  # type: ignore[attr-defined]
                self.select_girder_combo.clear()
                self.select_girder_combo.addItems(["All"] + self.available_girders)

                if desired:
                    # Uncheck 'All', then check desired girders.
                    for row in range(self.select_girder_combo.model().rowCount()):
                        item = self.select_girder_combo.model().item(row)
                        if not item:
                            continue
                        if item.text().strip().lower() == "all":
                            item.setCheckState(Qt.Unchecked)
                        elif item.text() in desired:
                            item.setCheckState(Qt.Checked)
                        else:
                            item.setCheckState(Qt.Unchecked)
            finally:
                if hasattr(self.select_girder_combo, "_updating_selection"):
                    self.select_girder_combo._updating_selection = False  # type: ignore[attr-defined]
                self.select_girder_combo.blockSignals(block)
        else:
            current_text = self.select_girder_combo.currentText().strip()
            current_selection = preferred_selection or []
            candidate = next((girder for girder in current_selection if girder in self.available_girders), None)
            if not candidate and current_text in self.available_girders:
                candidate = current_text

            block = self.select_girder_combo.blockSignals(True)
            self.select_girder_combo.clear()
            self.select_girder_combo.addItems(["All"] + self.available_girders)
            if candidate:
                index = self.select_girder_combo.findText(candidate, Qt.MatchFixedString)
                self.select_girder_combo.setCurrentIndex(index if index != -1 else 0)
            else:
                self.select_girder_combo.setCurrentIndex(0)
            self.select_girder_combo.blockSignals(block)

    def _on_girders_selection_changed(self, *args):
        if self.span_combo.currentText() == "Full Length":
            self._update_member_id_edit_state()
            return
        current_text = self.member_id_input.text().strip()
        if not self._is_valid_segment_id(current_text):
            default_id = self._default_member_segment_id()
            self._set_member_id_text(default_id)
        self._update_member_id_edit_state()

    def _get_selected_girders(self):
        if not hasattr(self, "select_girder_combo"):
            return self.available_girders.copy()
        if hasattr(self.select_girder_combo, "checked_items"):
            # In this widget, checked_items() returns [] when "All" is selected.
            checked = [g for g in self.select_girder_combo.checked_items() if g in self.available_girders]
            return checked or self.available_girders.copy()

        current = self.select_girder_combo.currentText().strip()
        if not current or current.lower() == "all":
            return self.available_girders.copy()
        if current in self.available_girders:
            return [current]
        return self.available_girders.copy()

    def _default_member_segment_id(self, girders=None):
        girders = girders or self._get_selected_girders()
        base = girders[0] if girders else "G1"
        return self._make_segment_id(base, 1)

    def _set_member_id_text(self, value, block_signals=False):
        if block_signals:
            previous = self.member_id_input.blockSignals(True)
            self.member_id_input.setText(value)
            self.member_id_input.blockSignals(previous)
        else:
            self.member_id_input.setText(value)

    def _is_valid_segment_id(self, member_id):
        member_id = str(member_id or "").strip()
        if not member_id:
            return False
        base, index = self._split_member_id(member_id)
        return bool(base and base in self.available_girders and isinstance(index, int) and index >= 1)

    def _update_member_id_edit_state(self):
        is_full_span = self.span_combo.currentText() == "Full Length"
        self.member_id_input.setReadOnly(is_full_span)
        if is_full_span:
            girders = self._get_selected_girders()
            display = ", ".join(girders) if girders else "G1"
            self._set_member_id_text(display, block_signals=True)
        else:
            current_text = self.member_id_input.text().strip()
            if not self._is_valid_segment_id(current_text):
                default_id = self._default_member_segment_id()
                self._set_member_id_text(default_id)
        self._update_distance_field_states()

    def _on_design_changed(self, text):
        is_custom = text.lower() == "customized"
        toggle_targets = (
            self.type_combo,
            self.symmetry_combo,
        )
        for widget in toggle_targets:
            widget.setEnabled(is_custom)
        if not is_custom:
            self._lock_type_to_welded()
            self._reset_section_state()
        self._update_dimension_field_mode()
        self._apply_type_state()

    def _on_type_changed(self, text):
        self._apply_type_state()
        self._update_preview()

    def _on_support_type_changed(self, support_type: str) -> None:
        """Handle Support Type change."""
        self._mark_current_member_dirty()

    def _apply_type_state(self):
        is_welded = self.type_combo.currentText().lower() == "welded"
        is_custom = self.design_combo.currentText().lower() == "customized"

        self._set_row_visibility(self.welded_rows, is_welded)
        self._set_row_visibility(self.rolled_rows, not is_welded)

        for label, widget in self.symmetry_row:
            label.setVisible(is_welded)
            widget.setVisible(is_welded)
        self.symmetry_combo.setEnabled(is_welded and is_custom)

        # Dimension rows remain enabled in Optimized mode so "Set Bounds" stays clickable.
        for widget in (self.total_depth_widget, self.top_width_widget, self.bottom_width_widget):
            widget.setVisible(is_welded)
            widget.setEnabled(is_welded)

        plate_widgets = (
            self.web_thickness_widget,
            self.top_thickness_widget,
            self.bottom_thickness_widget,
        )
        for widget in plate_widgets:
            widget.setEnabled(is_welded)
            widget.setVisible(is_welded)

        for label, widget in self.web_type_row:
            label.setVisible(is_welded)
            widget.setVisible(is_welded)
            widget.setEnabled(is_welded and is_custom)

        self.is_section_combo.setVisible(not is_welded)
        self.is_section_combo.setEnabled(not is_welded)
        self._update_thickness_value_enabled_state()
        self._update_dimension_field_mode()

    def _lock_type_to_welded(self):
        welded_index = self.type_combo.findText("Welded", Qt.MatchFixedString)
        if welded_index != -1 and self.type_combo.currentIndex() != welded_index:
            previous = self.type_combo.blockSignals(True)
            self.type_combo.setCurrentIndex(welded_index)
            self.type_combo.blockSignals(previous)

    def _reset_section_state(self):
        for widget in (self.total_depth_input, self.top_width_input, self.bottom_width_input):
            previous = widget.blockSignals(True)
            widget.clear()
            widget.blockSignals(previous)
        for widget in (self.web_thickness_value_input, self.top_thickness_value_input, self.bottom_thickness_value_input):
            previous = widget.blockSignals(True)
            widget.clear()
            widget.blockSignals(previous)
        self._update_preview()

    def _update_distance_field_states(self):
        # Master-Detail spec:
        # - Member ID: read-only
        # - Start distance: read-only
        # - End distance: editable
        self.member_id_input.setReadOnly(True)
        self.distance_start_input.setReadOnly(True)
        self.distance_end_input.setReadOnly(False)
        if self.segment_length_input:
            self.segment_length_input.setReadOnly(True)

    def _on_span_changed(self, span_text):
        # Preserve legacy span-mode behavior for total span editability.
        self.length_input.setReadOnly(True)

        self._initialize_segment_chain_if_needed()
        self._refresh_segment_list(self._current_girder)
        self._select_segment_index(self._current_segment_index)
        self._update_distance_field_states()

    def _on_length_changed(self, _):
        # Total span changes affect all girders, regardless of mode.
        total_span = self._get_total_span()
        if total_span is None:
            return

        for girder in self.available_girders:
            segments = self._ensure_girder_segments(girder)
            if not segments:
                self.segment_chain[girder] = [{"id": self._make_segment_id(girder, 1), "start": 0.0, "end": float(total_span)}]
                continue

            # If any segment ends beyond the new span, clamp and drop trailing.
            pruned: List[Dict[str, float]] = []
            for seg in segments:
                start = float(seg.get("start", 0.0))
                if start >= total_span:
                    break
                end = float(seg.get("end", 0.0))
                seg["end"] = min(end, float(total_span))
                pruned.append(seg)
            if not pruned:
                pruned = [{"id": self._make_segment_id(girder, 1), "start": 0.0, "end": float(total_span)}]
            pruned[0]["start"] = 0.0
            for i in range(1, len(pruned)):
                pruned[i]["start"] = float(pruned[i - 1].get("end", 0.0))
            pruned[-1]["end"] = float(total_span)
            self.segment_chain[girder] = pruned

        self._refresh_segment_list(self._current_girder)
        self._select_segment_index(self._current_segment_index)

    def _get_total_span(self):
        text = (self.length_input.text() or "").strip()
        if not text:
            return None
        return self._parse_float(text)

    def _split_member_id(self, member_id):
        member_id = str(member_id or "").strip()
        if not member_id:
            return "", None

        # Preferred format: G1M2
        if "M" in member_id:
            base, index = member_id.rsplit("M", 1)
            if base and index.isdigit():
                return base, int(index)

        # Backward compatible: G1-2
        if "-" in member_id:
            base, index = member_id.rsplit("-", 1)
            if index.isdigit():
                return base, int(index)
            return base, None

        return member_id, None

    def _set_line_edit_value(self, line_edit, value):
        if value is None:
            return
        text = f"{value:.3f}".rstrip("0").rstrip(".")
        if not text:
            text = "0"
        previous_state = line_edit.blockSignals(True)
        line_edit.setText(text)
        line_edit.blockSignals(previous_state)

    def validate_member_properties(self) -> bool:
        if self.design_combo.currentText() != "Customized":
            return True
        required_fields = [
            (self.total_depth_input, "Total Depth (d, mm)"),
            (self.top_width_input, "Width of Top Flange (t_fw, mm)"),
            (self.bottom_width_input, "Width of Bottom Flange (b_fw, mm)"),
        ]
        if self._is_custom_thickness_mode(self.web_thickness_combo):
            required_fields.append((self.web_thickness_value_input, "Web Thickness (w_t, mm)"))
        if self._is_custom_thickness_mode(self.top_thickness_combo):
            required_fields.append((self.top_thickness_value_input, "Top Flange Thickness (t_ft, mm)"))
        if self._is_custom_thickness_mode(self.bottom_thickness_combo):
            required_fields.append((self.bottom_thickness_value_input, "Bottom Flange Thickness (b_ft, mm)"))
        missing = []
        for field, label in required_fields:
            value = self._parse_float(field.text())
            if value is None or value <= 0:
                missing.append(label)
        if missing:
            QMessageBox.critical(
                self,
                "Incomplete Girder Inputs",
                f"Please provide valid values for: {', '.join(missing)}.",
            )
            return False
        return True

    def _create_inner_box(self):
        """Create a bordered box for grouped controls"""
        box = QFrame()
        box.setStyleSheet("""
            QFrame {
               border: 1px solid #b0b0b0;
               border-radius: 6px;
               background-color: #ffffff;
            }
            QFrame QComboBox, QFrame QLineEdit {
               border: none;
               border-bottom: 1px solid #d0d0d0;
               border-radius: 0px;
               min-height: 28px;
               padding: 4px 8px;
               background-color: #ffffff;
            }
            QFrame QComboBox:hover, QFrame QLineEdit:hover {
               border-bottom: 1px solid #5d5d5d;
            }
            QFrame QComboBox:focus, QFrame QLineEdit:focus {
               border-bottom: 1px solid #90AF13;
            }
            QFrame QLabel {
               border: none;
               padding: 0px;
               margin: 0px;
            }
        """)
        return box

    def _create_small_label(self, text):
        """Create a smaller label for compact layouts"""
        label = QLabel(text)
        label.setTextFormat(Qt.RichText)
        label.setStyleSheet("""
            QLabel {
               color: #2b2b2b;
               font-size: 11px;
               font-weight: 500;
               background: transparent;
               border: none;
               padding: 0px;
               margin: 0px;
            }
        """)
        label.setAutoFillBackground(False)
        return label

    def _add_box_row(self, layout, row, label_text, widget, visibility_list=None):
        """Add a row to a box grid layout"""
        label = self._create_small_label(label_text)
        layout.addWidget(label, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(widget, row, 1)
        if visibility_list is not None:
            visibility_list.append((label, widget))
        return row + 1

    def _set_row_visibility(self, rows, visible):
        for label, widget in rows:
            label.setVisible(visible)
            widget.setVisible(visible)

    def _populate_rolled_section_combo(self):
        designations = sorted(girder_properties.list_available_sections().keys())
        if not designations:
            designations = [
                "ISMB 500", "ISMB 550", "ISMB 600",
                "ISWB 500", "ISWB 550", "ISWB 600",
            ]
        self.is_section_combo.clear()
        self.is_section_combo.addItems(designations)

    def _configure_restraint_fields(self):
        torsion_items = self._constant_items("VALUES_TORSIONAL_RESTRAINT")
        warping_items = self._constant_items("VALUES_WARPING_RESTRAINT")
        web_type_items = self._constant_items("VALUES_WEB_TYPE")

        self._reload_combo_items(self.torsion_combo, torsion_items)
        self._reload_combo_items(self.warping_combo, warping_items)
        self._reload_combo_items(self.web_type_combo, web_type_items)

    @staticmethod
    def _reload_combo_items(combo, items):
        block = combo.blockSignals(True)
        combo.clear()
        combo.addItems(items)
        combo.setCurrentIndex(0 if items else -1)
        combo.blockSignals(block)

    @staticmethod
    def _constant_items(constant_name):
        return list(globals().get(constant_name, []))

    def _update_preview(self):
        if not hasattr(self, "section_preview"):
            return

        is_welded = self.type_combo.currentText().lower() == "welded"
        if is_welded:
            dims = self._gather_welded_dimensions()
            caption = "Welded girder preview" if dims else "Enter depth and flange widths"
            if dims:
                self.section_preview.set_dimensions(
                    depth_mm=dims["depth_mm"],
                    flange_width_mm=dims["top_flange_width_mm"],
                    bottom_flange_width_mm=dims["bottom_flange_width_mm"],
                    web_thickness_mm=dims["web_thickness_mm"],
                    flange_thickness_mm=dims["top_flange_thickness_mm"],
                    bottom_flange_thickness_mm=dims["bottom_flange_thickness_mm"],
                    show_welds=True,
                )
            else:
                self.section_preview.clear()
        else:
            designation = self.is_section_combo.currentText()
            beam = girder_properties.get_beam_profile(designation)
            outline = girder_properties.get_rolled_section(designation) if beam is None else None
            has_data = bool(beam or outline)
            caption = f"Rolled section • {designation}" if has_data else "Rolled section unavailable"
            if beam:
                self.section_preview.set_section(beam)
            elif outline:
                self.section_preview.set_dimensions(
                    depth_mm=outline["depth_mm"],
                    flange_width_mm=outline["top_flange_width_mm"],
                    bottom_flange_width_mm=outline["bottom_flange_width_mm"],
                    web_thickness_mm=outline["web_thickness_mm"],
                    flange_thickness_mm=outline["top_flange_thickness_mm"],
                    bottom_flange_thickness_mm=outline["bottom_flange_thickness_mm"],
                )
            else:
                self.section_preview.clear()

        if hasattr(self, "preview_caption"):
            self.preview_caption.setText(caption)
        self._update_section_properties()

    def _gather_welded_dimensions(self):
        depth = self._parse_float(self.total_depth_input.text())
        top_width = self._parse_float(self.top_width_input.text())
        bottom_width = self._parse_float(self.bottom_width_input.text()) or top_width

        if not depth or not top_width or not bottom_width:
            return None

        web_default = max(8.0, depth * 0.02)
        flange_default = max(10.0, depth * 0.03)

        web_thickness = web_default
        if self._is_custom_thickness_mode(self.web_thickness_combo):
            web_thickness = self._parse_float(self.web_thickness_value_input.text()) or web_default

        top_thickness = flange_default
        if self._is_custom_thickness_mode(self.top_thickness_combo):
            top_thickness = self._parse_float(self.top_thickness_value_input.text()) or flange_default

        bottom_thickness = flange_default
        if self._is_custom_thickness_mode(self.bottom_thickness_combo):
            bottom_thickness = self._parse_float(self.bottom_thickness_value_input.text()) or flange_default

        return {
            "designation": "Custom Welded Girder",
            "section_type": "welded",
            "depth_mm": depth,
            "top_flange_width_mm": top_width,
            "bottom_flange_width_mm": bottom_width,
            "web_thickness_mm": web_thickness,
            "top_flange_thickness_mm": top_thickness,
            "bottom_flange_thickness_mm": bottom_thickness,
            "support_width_mm": self._parse_float(self.support_width_input.text()) or 0.0,
        }

    def _update_section_properties(self):
        if not self.section_property_inputs:
            return
        values = None
        if self.type_combo.currentText().lower() == "welded":
            dims = self._gather_welded_dimensions()
            if dims:
                values = self._compute_welded_properties(dims)
        else:
            designation = self.is_section_combo.currentText()
            values = self._fetch_rolled_properties(designation)
        if values:
            self._apply_section_properties(values)
        else:
            self._clear_section_properties()

    def _fetch_rolled_properties(self, designation):
        if not designation:
            return None
        beam = girder_properties.get_beam_profile(designation)
        if not beam:
            return None
        values = {
            "Mass, M (Kg/m)": beam.mass_per_meter_kg,
            "Sectional Area, a (cm2)": beam.area_cm2,
            "2nd Moment of Area, Iz (cm4)": beam.moment_of_inertia_zz_cm4,
            "2nd Moment of Area, Iy (cm4)": beam.moment_of_inertia_yy_cm4,
            "Radius of Gyration, rz (cm)": beam.radius_of_gyration_z_cm,
            "Radius of Gyration, ry (cm)": beam.radius_of_gyration_y_cm,
            "Elastic Modulus, Zz (cm3)": beam.elastic_section_modulus_z_cm3,
            "Elastic Modulus, Zy (cm3)": beam.elastic_section_modulus_y_cm3,
            "Plastic Modulus, Zuz (cm3)": beam.plastic_section_modulus_z_cm3,
            "Plastic Modulus, Zuy (cm3)": beam.plastic_section_modulus_y_cm3,
            "Torsion Constant, It (cm4)": beam.torsion_constant_cm4,
            "Warping Constant, Iw (cm6)": beam.warping_constant_cm6,
        }
        area = values.get("Sectional Area, a (cm2)")
        iz = values.get("2nd Moment of Area, Iz (cm4)")
        iy = values.get("2nd Moment of Area, Iy (cm4)")
        if values.get("Radius of Gyration, rz (cm)") is None and area and iz:
            values["Radius of Gyration, rz (cm)"] = math.sqrt(iz / area)
        if values.get("Radius of Gyration, ry (cm)") is None and area and iy:
            values["Radius of Gyration, ry (cm)"] = math.sqrt(iy / area)
        return values

    def _compute_welded_properties(self, dims):
        depth = dims["depth_mm"]
        top_width = dims["top_flange_width_mm"]
        bottom_width = dims["bottom_flange_width_mm"]
        web_thickness = dims["web_thickness_mm"]
        top_thickness = dims["top_flange_thickness_mm"]
        bottom_thickness = dims["bottom_flange_thickness_mm"]

        h_web = max(depth - top_thickness - bottom_thickness, 1.0)
        area_top = top_width * top_thickness
        area_bottom = bottom_width * bottom_thickness
        area_web = web_thickness * h_web
        area_total_mm2 = area_top + area_bottom + area_web
        area_cm2 = area_total_mm2 / 100.0
        mass_kg_per_m = (area_total_mm2 / 1_000_000.0) * 7850.0

        iz_web = (web_thickness * h_web ** 3) / 12.0
        iz_top = (top_width * top_thickness ** 3) / 12.0
        iz_bottom = (bottom_width * bottom_thickness ** 3) / 12.0
        distance_top = h_web / 2.0 + top_thickness / 2.0
        distance_bottom = h_web / 2.0 + bottom_thickness / 2.0
        iz_top += area_top * distance_top ** 2
        iz_bottom += area_bottom * distance_bottom ** 2
        iz_cm4 = (iz_web + iz_top + iz_bottom) / 10000.0

        iy_web = (h_web * web_thickness ** 3) / 12.0
        iy_top = (top_thickness * top_width ** 3) / 12.0
        iy_bottom = (bottom_thickness * bottom_width ** 3) / 12.0
        iy_cm4 = (iy_web + iy_top + iy_bottom) / 10000.0

        rz_cm = math.sqrt(iz_cm4 / area_cm2) if area_cm2 > 0 else None
        ry_cm = math.sqrt(iy_cm4 / area_cm2) if area_cm2 > 0 else None

        depth_cm = depth / 10.0
        width_cm = max(top_width, bottom_width) / 10.0
        zz_cm3 = iz_cm4 / (depth_cm / 2.0) if depth_cm > 0 else None
        zy_cm3 = iy_cm4 / (width_cm / 2.0) if width_cm > 0 else None

        zpl_major = (
            area_top * distance_top +
            area_bottom * distance_bottom +
            (web_thickness * h_web ** 2) / 4.0
        ) / 1000.0
        zpl_minor = (
            (top_thickness * top_width ** 2) / 4.0 +
            (bottom_thickness * bottom_width ** 2) / 4.0 +
            (h_web * web_thickness ** 2) / 4.0
        ) / 1000.0

        torsion_constant_cm4 = (
            (top_width * top_thickness ** 3) / 3.0 +
            (bottom_width * bottom_thickness ** 3) / 3.0 +
            (h_web * web_thickness ** 3) / 3.0
        ) / 10000.0

        warping_constant_cm6 = (
            ((top_width * top_thickness ** 3) + (bottom_width * bottom_thickness ** 3)) * h_web ** 2 / 24.0
        ) / 1_000_000.0

        return {
            "Mass, M (Kg/m)": mass_kg_per_m,
            "Sectional Area, a (cm2)": area_cm2,
            "2nd Moment of Area, Iz (cm4)": iz_cm4,
            "2nd Moment of Area, Iy (cm4)": iy_cm4,
            "Radius of Gyration, rz (cm)": rz_cm,
            "Radius of Gyration, ry (cm)": ry_cm,
            "Elastic Modulus, Zz (cm3)": zz_cm3,
            "Elastic Modulus, Zy (cm3)": zy_cm3,
            "Plastic Modulus, Zuz (cm3)": zpl_major,
            "Plastic Modulus, Zuy (cm3)": zpl_minor,
            "Torsion Constant, It (cm4)": torsion_constant_cm4,
            "Warping Constant, Iw (cm6)": warping_constant_cm6,
        }

    def _apply_section_properties(self, values):
        for label, widget in self.section_property_inputs.items():
            display = self._format_property_value(values.get(label))
            previous = widget.blockSignals(True)
            widget.setText(display)
            widget.blockSignals(previous)

    def _clear_section_properties(self):
        for widget in self.section_property_inputs.values():
            previous = widget.blockSignals(True)
            widget.clear()
            widget.blockSignals(previous)

    @staticmethod
    def _format_property_value(value):
        if value is None:
            return ""
        if isinstance(value, (int, float)):
            return f"{value:.2f}"
        return str(value)

    @staticmethod
    def _parse_float(text):
        try:
            return float(text)
        except (TypeError, ValueError):
            return None

    def set_girder_count(self, count: Optional[int]) -> None:
        try:
            total = int(count) if count is not None else len(self.available_girders)
        except (TypeError, ValueError):
            total = len(self.available_girders)
        total = max(1, min(MAX_GIRDER_COUNT, total))
        self.available_girders = [f"G{i}" for i in range(1, total + 1)]

        # Prune segment chains for removed girders and initialize new ones.
        self.segment_chain = {g: segs for g, segs in self.segment_chain.items() if g in self.available_girders}
        total_span = float(self._get_total_span() or DEFAULT_MEMBER_LENGTH_M)
        for girder in self.available_girders:
            if girder not in self.segment_chain:
                self.segment_chain[girder] = [{"id": self._make_segment_id(girder, 1), "start": 0.0, "end": total_span}]

        # Refresh dropdown
        if self.girder_dropdown:
            prev = self.girder_dropdown.blockSignals(True)
            self.girder_dropdown.clear()
            for girder in self.available_girders:
                label = f"Girder {girder[1:]}" if girder.startswith("G") and girder[1:].isdigit() else girder
                self.girder_dropdown.addItem(label, girder)
            self.girder_dropdown.setCurrentIndex(0)
            self.girder_dropdown.blockSignals(prev)

        self._current_girder = self.available_girders[0] if self.available_girders else "G1"
        self._on_girder_changed(self._current_girder)

    def reset_defaults(self, preserve_selection: bool = False, preserve_segments: bool = False) -> None:
        """Reset UI + stored values to initial defaults.

        Args:
            preserve_selection: When True, keep the currently selected girder in
                the girder selector.
            preserve_segments: When True, keep the Member ID / Start / End
                segment table (segment_chain) intact.
        """

        selected_girder = None
        selected_segment_index = None
        if preserve_selection:
            try:
                selected_girder = self._current_girder
            except Exception:
                selected_girder = None
            try:
                selected_segment_index = int(getattr(self, "_current_segment_index", 0))
            except Exception:
                selected_segment_index = 0

        preserved_segment_chain = None
        if preserve_segments:
            try:
                preserved_segment_chain = {g: [dict(seg) for seg in segs] for g, segs in self.segment_chain.items()}
            except Exception:
                preserved_segment_chain = None

        # Clear per-member persistence so Defaults truly returns to a clean slate.
        try:
            self._member_state.clear()
        except Exception:
            self._member_state = {}
        try:
            self._dirty_members.clear()
        except Exception:
            self._dirty_members = set()
        self._last_member_combo_index = 0

        if not preserve_segments:
            self.segment_chain.clear()

        def _reset_combo(combo: QComboBox, index: int = 0):
            previous = combo.blockSignals(True)
            combo.setCurrentIndex(index if combo.count() > index >= 0 else 0)
            combo.blockSignals(previous)

        for combo in (
            self.span_combo,
            self.design_combo,
            self.type_combo,
            self.support_type_combo,
            self.symmetry_combo,
            self.web_thickness_combo,
            self.top_thickness_combo,
            self.bottom_thickness_combo,
            self.torsion_combo,
            self.warping_combo,
            self.web_type_combo,
        ):
            _reset_combo(combo)

        if self.is_section_combo.count() > 0:
            _reset_combo(self.is_section_combo)

        # Total span default
        self._set_line_edit_value(self.length_input, DEFAULT_MEMBER_LENGTH_M)

        # Segment chain defaults: one segment per girder spanning the full span
        # (only when not preserving segments, or if preserving but chain is empty).
        if (not preserve_segments) or (not getattr(self, "segment_chain", None)):
            total_span = float(self._get_total_span() or DEFAULT_MEMBER_LENGTH_M)
            for girder in self.available_girders:
                self.segment_chain[girder] = [{"id": self._make_segment_id(girder, 1), "start": 0.0, "end": total_span}]
        elif preserved_segment_chain:
            # Restore preserved segments after any internal recomputation.
            self.segment_chain = preserved_segment_chain

        for field in (
            self.total_depth_input,
            self.top_width_input,
            self.bottom_width_input,
            self.web_thickness_value_input,
            self.top_thickness_value_input,
            self.bottom_thickness_value_input,
            self.support_width_input,
        ):
            previous = field.blockSignals(True)
            field.clear()
            field.blockSignals(previous)

        self._dimension_bounds = {
            "total_depth": {"lower": 200.0, "upper": 2000.0, "increment": 25.0},
            "top_width": {"lower": 100.0, "upper": 1000.0, "increment": 10.0},
            "bottom_width": {"lower": 100.0, "upper": 1000.0, "increment": 10.0},
        }
        self._refresh_bounds_tooltips()

        self._on_design_changed(self.design_combo.currentText())
        self._on_type_changed(self.type_combo.currentText())
        self._update_preview()
        self._update_section_properties()

        # Capture the default template used when new members are first visited.
        try:
            self._default_member_state = self._capture_member_state()
        except Exception:
            self._default_member_state = None

        # Refresh master-detail UI
        if self.girder_dropdown:
            prev = self.girder_dropdown.blockSignals(True)
            self.girder_dropdown.clear()

            # Keep display-friendly labels while preserving stable internal IDs via userData.
            for girder in self.available_girders:
                label = f"Girder {girder[1:]}" if girder.startswith("G") and girder[1:].isdigit() else girder
                self.girder_dropdown.addItem(label, girder)

            # Preserve selection when requested (match by userData, not label).
            if preserve_selection and selected_girder and selected_girder in self.available_girders:
                idx = self.girder_dropdown.findData(selected_girder)
                self.girder_dropdown.setCurrentIndex(idx if idx != -1 else 0)
            else:
                self.girder_dropdown.setCurrentIndex(0)

            self.girder_dropdown.blockSignals(prev)

        if preserve_selection and selected_girder and selected_girder in self.available_girders:
            self._current_girder = selected_girder
        else:
            self._current_girder = self.available_girders[0] if self.available_girders else "G1"

        self._refresh_segment_list(self._current_girder)
        if preserve_segments and selected_segment_index is not None:
            self._select_segment_index(max(0, selected_segment_index))
        else:
            self._select_segment_index(0)
        self._update_distance_field_states()

    def collect_data(self) -> dict:
        # Treat the dialog-level Save as committing the current Member ID.
        if self._is_current_member_dirty():
            self._commit_current_member_state()
        # Save action marks member edits clean for this session.
        self._dirty_members.clear()

        welded_inputs = {
            "total_depth_mm": self.total_depth_input.text().strip(),
            "top_flange_width_mm": self.top_width_input.text().strip(),
            "bottom_flange_width_mm": self.bottom_width_input.text().strip(),
            "total_depth_bounds": dict(self._dimension_bounds.get("total_depth") or {}),
            "top_flange_width_bounds": dict(self._dimension_bounds.get("top_width") or {}),
            "bottom_flange_width_bounds": dict(self._dimension_bounds.get("bottom_width") or {}),
            "web_thickness_mode": self.web_thickness_combo.currentText(),
            "top_thickness_mode": self.top_thickness_combo.currentText(),
            "bottom_thickness_mode": self.bottom_thickness_combo.currentText(),
            "web_thickness_value_mm": self.web_thickness_value_input.text().strip(),
            "top_thickness_value_mm": self.top_thickness_value_input.text().strip(),
            "bottom_thickness_value_mm": self.bottom_thickness_value_input.text().strip(),
            "support_width_mm": self.support_width_input.text().strip(),
        }
        properties_snapshot = {
            label: field.text().strip()
            for label, field in self.section_property_inputs.items()
        }
        current_segments = self._ensure_girder_segments(self._current_girder)
        current_segment = None
        if current_segments:
            idx = max(0, min(self._current_segment_index, len(current_segments) - 1))
            current_segment = dict(current_segments[idx])
        return {
            "selected_girders": [self._current_girder],
            "selected_girder": self._current_girder,
            "span_mode": self.span_combo.currentText(),
            "member_id": self.member_id_input.text().strip(),
            "distance_start_m": self._parse_float(self.distance_start_input.text()),
            "distance_end_m": self._parse_float(self.distance_end_input.text()),
            "total_span_m": self._parse_float(self.length_input.text()),
            "current_segment": current_segment,
            "design_mode": self.design_combo.currentText(),
            "girder_type": self.type_combo.currentText(),
            "symmetry": self.symmetry_combo.currentText(),
            "torsional_restraint": self.torsion_combo.currentText(),
            "warping_restraint": self.warping_combo.currentText(),
            "web_type": self.web_type_combo.currentText(),
            "rolled_section": self.is_section_combo.currentText(),
            "welded_inputs": welded_inputs,
            "segment_chain": {
                girder: [
                    {"id": seg.get("id"), "start": seg.get("start"), "end": seg.get("end")}
                    for seg in segments
                ]
                for girder, segments in self.segment_chain.items()
            },
            # Per-member saved Section Inputs keyed by girder/member_id.
            "member_states": self._member_state,
            "section_properties": properties_snapshot,
        }

    def restore_data(self, data: dict) -> None:
        """Restore previously saved girder details.

        This is used by the Additional Inputs dialog to persist Member Properties
        (including segment chains) across dialog reopen.

        Args:
            data: Dict as returned by collect_data() (or compatible).
        """
        if not isinstance(data, dict):
            return

        # Restore total span early so segment normalization uses the right length.
        total_span = data.get("total_span_m")
        if total_span is not None and hasattr(self, "length_input") and self.length_input is not None:
            try:
                self._set_line_edit_value(self.length_input, float(total_span))
            except Exception:
                # Some callers may store this as an empty string.
                try:
                    text = str(total_span).strip()
                    if text:
                        self.length_input.setText(text)
                except Exception:
                    pass

        segment_chain = data.get("segment_chain")
        if isinstance(segment_chain, dict) and segment_chain:
            # Normalize segment records to {id,start,end}.
            normalized = {}
            for girder, segments in segment_chain.items():
                if not isinstance(segments, list):
                    continue
                seg_list = []
                for seg in segments:
                    if not isinstance(seg, dict):
                        continue
                    seg_list.append(
                        {
                            "id": str(seg.get("id") or "").strip() or None,
                            "start": float(seg.get("start") or 0.0),
                            "end": float(seg.get("end") or 0.0),
                        }
                    )
                if seg_list:
                    normalized[str(girder)] = seg_list
            if normalized:
                self.segment_chain = normalized

        member_states = data.get("member_states")
        if isinstance(member_states, dict):
            self._member_state = member_states

        # Restore current girder + current segment, then refresh dependent UI.
        selected_girder = str(data.get("selected_girder") or data.get("selected_girders", [""])[0] or "").strip()
        if selected_girder and selected_girder in self.available_girders:
            self._current_girder = selected_girder

        # Update dropdown and segment list.
        if self.girder_dropdown is not None:
            prev = self.girder_dropdown.blockSignals(True)
            try:
                if self.girder_dropdown.findText(self._current_girder) >= 0:
                    self.girder_dropdown.setCurrentText(self._current_girder)
            finally:
                self.girder_dropdown.blockSignals(prev)

        self._refresh_segment_list(self._current_girder)
        self._refresh_member_id_combo()

        # Try to restore the previously active segment.
        target_index = 0
        current_segment = data.get("current_segment")
        if isinstance(current_segment, dict):
            target_id = str(current_segment.get("id") or "").strip()
            if target_id:
                segments = self._ensure_girder_segments(self._current_girder)
                for idx, seg in enumerate(segments):
                    if str(seg.get("id") or "").strip() == target_id:
                        target_index = idx
                        break
        self._select_segment_index(int(target_index))

    # ===== Public helpers for other Member Properties tabs =====

    def list_all_member_ids(self) -> List[str]:
        """Return all current member IDs (segments) across all available girders."""
        member_ids: List[str] = []
        for girder in self.available_girders:
            segments = self._ensure_girder_segments(girder)
            for seg in segments:
                seg_id = str(seg.get("id") or "").strip()
                if seg_id:
                    member_ids.append(seg_id)
        return member_ids

    def is_member_optimized(self, member_id: str) -> bool:
        """True if the given member is set to Optimized design in Girder Details."""
        member_id = str(member_id or "").strip()
        if not member_id:
            return False

        girder, _idx = self._split_member_id(member_id)

        # If the requested member is currently active, reflect the live UI.
        try:
            current_girder, current_member_id = self._current_member_key()
            if current_girder == girder and current_member_id == member_id:
                return (self.design_combo.currentText() if hasattr(self, "design_combo") else "") == "Optimized"
        except Exception:
            pass

        stored = (self._member_state.get(girder) or {}).get(member_id) or {}
        design = ((stored.get("inputs") or {}).get("design") or "").strip()
        if design:
            return design == "Optimized"

    def get_member_section_dimensions(self, member_id: str) -> Optional[dict]:
        """Return basic section dimensions for the given member.

        Output keys: top_flange_width_mm, bottom_flange_width_mm, web_thickness_mm.
        """
        member_id = str(member_id or "").strip()
        if not member_id:
            return None

        girder, _idx = self._split_member_id(member_id)

        inputs = None
        try:
            current_girder, current_member_id = self._current_member_key()
            if current_girder == girder and current_member_id == member_id:
                inputs = (self._capture_member_state() or {}).get("inputs")
        except Exception:
            inputs = None

        if inputs is None:
            stored = (self._member_state.get(girder) or {}).get(member_id) or {}
            inputs = (stored.get("inputs") or {})

        return self._compute_section_dimensions_from_inputs(inputs)

    def _compute_section_dimensions_from_inputs(self, inputs: dict) -> Optional[dict]:
        if not isinstance(inputs, dict):
            return None

        section_type = str(inputs.get("type") or "").strip().lower()
        if section_type == "welded":
            depth = self._parse_float(inputs.get("total_depth"))
            top_width = self._parse_float(inputs.get("top_width"))
            bottom_width = self._parse_float(inputs.get("bottom_width")) or top_width

            if not depth or not top_width or not bottom_width:
                return None

            web_thickness = None
            if str(inputs.get("web_thickness") or "").strip().lower() == "custom":
                web_thickness = self._parse_float(inputs.get("web_thickness_value"))

            if not web_thickness:
                web_thickness = max(8.0, depth * 0.02)

            return {
                "top_flange_width_mm": top_width,
                "bottom_flange_width_mm": bottom_width,
                "web_thickness_mm": web_thickness,
            }

        designation = str(inputs.get("is_section") or "").strip()
        if not designation:
            return None

        beam = girder_properties.get_beam_profile(designation)
        outline = girder_properties.get_rolled_section(designation) if beam is None else None
        if beam:
            return {
                "top_flange_width_mm": float(beam.flange_width_mm),
                "bottom_flange_width_mm": float(beam.flange_width_mm),
                "web_thickness_mm": float(beam.web_thickness_mm),
            }
        if outline:
            return {
                "top_flange_width_mm": float(outline.get("top_flange_width_mm") or 0.0),
                "bottom_flange_width_mm": float(outline.get("bottom_flange_width_mm") or 0.0),
                "web_thickness_mm": float(outline.get("web_thickness_mm") or 0.0),
            }
        return None

        # Fallback: if the member hasn't been visited/saved yet, do NOT inherit
        # whatever the currently active member is set to. New/unvisited members
        # should behave like the UI default (Optimized) until explicitly changed.
        try:
            template = getattr(self, "_default_member_state", None) or {}
            default_design = str(((template.get("inputs") or {}).get("design") or "")).strip()
            if default_design:
                return default_design == "Optimized"
        except Exception:
            pass
        return True
