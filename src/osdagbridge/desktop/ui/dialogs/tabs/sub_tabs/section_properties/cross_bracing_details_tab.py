import sys
import os
import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar, QLabel, QLineEdit,
    QComboBox, QGroupBox, QFormLayout, QPushButton, QScrollArea,
    QCheckBox, QMessageBox, QSizePolicy, QSpacerItem, QStackedWidget,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QDialog, QSizeGrip
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QDoubleValidator, QIntValidator

from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.widgets.section_viewer import SectionPreviewWidget, SectionCatalog
from osdagbridge.desktop.ui.widgets.placeholder_section_preview import PlaceholderSectionPreviewWidget

class CrossBracingDetailsTab(QWidget):
    """Tab for Cross-Bracing Details with visual previews"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.catalog = SectionCatalog()
        self._girder_details_tab = None
        self._global_design_mode = "Optimized"

        # Keep all combo boxes strictly uniform in width.
        self._combo_width = 190

        # Persist UI state per (girder-pair, member-id) so switching selection
        # restores user inputs for that specific member.
        self._state_by_member_key: dict[str, dict] = {}
        self._active_member_key: str | None = None
        self._selection_sync_guard = False
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )
        main_layout.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)

        primary_card = self._create_card_frame()
        card_layout = QHBoxLayout(primary_card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(12)

        # Left column (inputs)
        left_column = QWidget()
        left_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        selection_box = self._create_inner_box()
        selection_layout = QGridLayout(selection_box)
        selection_layout.setContentsMargins(12, 8, 12, 8)
        selection_layout.setHorizontalSpacing(12)
        selection_layout.setVerticalSpacing(8)
        selection_layout.setColumnMinimumWidth(0, 180)
        selection_layout.setColumnStretch(0, 0)
        selection_layout.setColumnStretch(1, 0)

        self.select_girders_combo = QComboBox()
        # Populated from Girder Details when bound.
        self._configure_combo_box(self.select_girders_combo)
        apply_field_style(self.select_girders_combo)
        selection_layout.addWidget(self._create_label("Select Girders:"), 0, 0)
        selection_layout.addWidget(self.select_girders_combo, 0, 1)

        self.member_id_combo = QComboBox()
        # Populated from Girder Details when bound. (No Custom option.)
        self._configure_combo_box(self.member_id_combo)
        # Member IDs are software-generated and must not be typed/edited.
        self.member_id_combo.setEditable(False)
        try:
            self.member_id_combo.setInsertPolicy(QComboBox.NoInsert)
        except Exception:
            pass
        # Hide the dropdown entirely; show a read-only display instead.
        self.member_id_combo.setVisible(False)

        self.member_id_display = QLineEdit()
        self.member_id_display.setReadOnly(True)
        self.member_id_display.setFixedSize(self._combo_width, 28)
        self.member_id_display.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        try:
            self.member_id_display.setFocusPolicy(Qt.NoFocus)
        except Exception:
            pass
        apply_field_style(self.member_id_display)
        selection_layout.addWidget(self._create_label("Member ID:"), 1, 0)
        selection_layout.addWidget(self.member_id_display, 1, 1)

        # Keep the two selectors aligned and persist state per selection.
        self.select_girders_combo.currentIndexChanged.connect(self._on_select_girders_index_changed)

        selection_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        left_layout.addWidget(selection_box)

        inputs_box = self._create_inner_box()
        inputs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        inputs_layout = QVBoxLayout(inputs_box)
        inputs_layout.setContentsMargins(12, 8, 12, 8)
        inputs_layout.setSpacing(6)
        inputs_layout.addWidget(self._create_heading_label("Section Inputs:"))

        inputs_grid = QGridLayout()
        inputs_grid.setContentsMargins(0, 0, 0, 0)
        inputs_grid.setHorizontalSpacing(12)
        inputs_grid.setVerticalSpacing(8)
        inputs_grid.setColumnMinimumWidth(0, 180)
        inputs_grid.setColumnStretch(0, 0)
        inputs_grid.setColumnStretch(1, 0)

        self.design_combo = QComboBox()
        self.design_combo.addItems(["Customized", "Optimized"])
        if self.design_combo.count() > 1:
            self.design_combo.setCurrentIndex(1)  # Default to Optimized
        self._configure_combo_box(self.design_combo)
        apply_field_style(self.design_combo)
        self.design_combo.setVisible(False)
        row = 0

        self.bracing_type_combo = QComboBox()
        self.bracing_type_combo.addItems(["K-Bracing", "X-Bracing"])
        self._configure_combo_box(self.bracing_type_combo)
        apply_field_style(self.bracing_type_combo)
        row = self._add_grid_row(inputs_grid, row, "Type of Bracing:", self.bracing_type_combo)

        section_type_options = [
            "Angle",
            "Double Angle (Long Leg)",
            "Double Angle (Short Leg)",
            "Channel",
            "Double Channel",
        ]

        self.bracing_section_type_combo = QComboBox()
        self.bracing_section_type_combo.addItems(section_type_options)
        self._configure_combo_box(self.bracing_section_type_combo)
        apply_field_style(self.bracing_section_type_combo)
        row = self._add_grid_row(inputs_grid, row, "Bracing Section Type:", self.bracing_section_type_combo)

        self.bracing_section_combo = QComboBox()
        self._configure_combo_box(self.bracing_section_combo)
        apply_field_style(self.bracing_section_combo)
        row = self._add_grid_row(inputs_grid, row, "Bracing Section:", self.bracing_section_combo)

        self.top_bracket_type_combo = QComboBox()
        self.top_bracket_type_combo.addItems(section_type_options)
        self._configure_combo_box(self.top_bracket_type_combo)
        apply_field_style(self.top_bracket_type_combo)
        row = self._add_grid_row(inputs_grid, row, "Top Bracket Section:", self.top_bracket_type_combo)

        self.top_bracket_size_combo = QComboBox()
        self._configure_combo_box(self.top_bracket_size_combo)
        apply_field_style(self.top_bracket_size_combo)
        row = self._add_grid_row(inputs_grid, row, "Top Bracket Size:", self.top_bracket_size_combo)

        self.bottom_bracket_type_combo = QComboBox()
        self.bottom_bracket_type_combo.addItems(section_type_options)
        self._configure_combo_box(self.bottom_bracket_type_combo)
        apply_field_style(self.bottom_bracket_type_combo)
        row = self._add_grid_row(inputs_grid, row, "Bottom Bracket Section:", self.bottom_bracket_type_combo)

        self.bottom_bracket_size_combo = QComboBox()
        self._configure_combo_box(self.bottom_bracket_size_combo)
        apply_field_style(self.bottom_bracket_size_combo)
        row = self._add_grid_row(inputs_grid, row, "Bottom Bracket Size:", self.bottom_bracket_size_combo)

        self.spacing_input = QLineEdit()
        self.spacing_input.setValidator(QDoubleValidator(0, 100000, 2))
        apply_field_style(self.spacing_input)
        self.spacing_input.setFixedSize(self._combo_width, 28)
        self.spacing_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._add_grid_row(inputs_grid, row, "Spacing (m):", self.spacing_input)

        inputs_layout.addLayout(inputs_grid)
        left_layout.addWidget(inputs_box)
        left_layout.addStretch(1)

        card_layout.addWidget(left_column)

        # Right column (previews)
        right_column = QWidget()
        self.right_column = right_column
        right_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Match End Diaphragm cross-bracing view: show a bracing-layout diagram at the top.
        type_box = self._create_inner_box()
        type_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        type_layout = QVBoxLayout(type_box)
        type_layout.setContentsMargins(12, 8, 12, 10)
        type_layout.setSpacing(6)
        type_layout.addWidget(self._create_heading_label("Type of Bracing"))
        type_layout.addWidget(self._create_bracing_layout_placeholder("Bracing Layout", 170))
        right_layout.addWidget(type_box)

        self.bracing_preview_box, self.bracing_preview_label = self._create_preview_box("Bracing")
        right_layout.addWidget(self.bracing_preview_box)

        self.top_bracket_preview_box, self.top_bracket_preview_label = self._create_preview_box("Top Bracket")
        right_layout.addWidget(self.top_bracket_preview_box)

        self.bottom_bracket_preview_box, self.bottom_bracket_preview_label = self._create_preview_box("Bottom Bracket")
        right_layout.addWidget(self.bottom_bracket_preview_box)

        right_layout.addStretch()

        card_layout.addWidget(right_column)
        card_layout.setStretch(0, 3)
        card_layout.setStretch(1, 4)
        container_layout.addWidget(primary_card)
        container_layout.addStretch()

        self.bracing_type_combo.currentTextChanged.connect(self._update_previews)
        self.bracing_section_type_combo.currentTextChanged.connect(self._on_bracing_type_changed)
        self.bracing_section_combo.currentTextChanged.connect(self._update_previews)
        self.top_bracket_type_combo.currentTextChanged.connect(self._on_top_bracket_type_changed)
        self.top_bracket_size_combo.currentTextChanged.connect(self._update_previews)
        self.bottom_bracket_type_combo.currentTextChanged.connect(self._on_bottom_bracket_type_changed)
        self.bottom_bracket_size_combo.currentTextChanged.connect(self._update_previews)
        self.design_combo.currentTextChanged.connect(self._on_design_changed)
        self.spacing_input.textChanged.connect(self._on_span_or_spacing_changed)
        self._populate_designations()
        self._on_design_changed(self._global_design_mode)

        # Seed selection drop-downs with a safe default until Girder Details is bound.
        self.refresh_girder_options()

        # Ensure initial selection loads its saved/default state.
        self._load_state_for_current_member()

    def _on_span_or_spacing_changed(self, *_args) -> None:
        # Member IDs are derived from Span + Spacing (software-driven).
        try:
            self._refresh_member_id_display()
        except Exception:
            pass

    def _current_member_id(self) -> str:
        return f"B{self._pair_index()}M1"

    def _current_member_key(self) -> str:
        pair = (self.select_girders_combo.currentText() or "").strip()
        member = self._current_member_id()
        return f"{pair}::{member}".strip(":")

    @staticmethod
    def _normalize_member_id(text: str, pair_index: int | None = None) -> str:
        """Normalize legacy IDs/ranges to the canonical format B{pair}M{member}.

        Accepts:
        - 'B1M3' (canonical)
        - 'B1-3' (legacy hyphen)
        - 'B1-1 to B1-15' (legacy range; coerces to M1)
        """
        raw = (text or "").strip().replace(" ", "")
        if not raw:
            return ""

        upper = raw.upper()

        # Canonical already.
        if "M" in upper and upper.startswith("B"):
            return upper

        # Legacy range like B1-1toB1-15 -> choose first.
        if upper.startswith("B") and "TO" in upper:
            # Try to keep the pair index if provided.
            if pair_index is not None:
                return f"B{pair_index}M1"
            # Attempt to parse pair number from prefix.
            try:
                after_b = upper[1:]
                pair_num = int("".join(ch for ch in after_b if ch.isdigit()) or 0)
            except Exception:
                pair_num = 0
            return f"B{pair_num}M1" if pair_num > 0 else ""

        # Legacy single member like B1-3.
        if upper.startswith("B") and "-" in upper:
            try:
                b_part, m_part = upper.split("-", 1)
                pair_num = int(b_part[1:])
                mem_num = int("".join(ch for ch in m_part if ch.isdigit()))
                return f"B{pair_num}M{mem_num}"
            except Exception:
                return ""

        # Fallback: if only a member number is present and pair_index is known.
        if pair_index is not None:
            try:
                mem_num = int("".join(ch for ch in upper if ch.isdigit()))
                if mem_num > 0:
                    return f"B{pair_index}M{mem_num}"
            except Exception:
                pass
        return ""

    @staticmethod
    def _member_number(text: str) -> int | None:
        text = (text or "").strip().upper().replace(" ", "")
        if not text:
            return None
        if text.startswith("B") and "M" in text:
            try:
                _b, m = text.split("M", 1)
                return int("".join(ch for ch in m if ch.isdigit()) or 0) or None
            except Exception:
                return None
        if text.startswith("B") and "-" in text:
            try:
                _b, m = text.split("-", 1)
                return int("".join(ch for ch in m if ch.isdigit()) or 0) or None
            except Exception:
                return None
        return None

    def _pair_index(self) -> int:
        return max(0, int(self.select_girders_combo.currentIndex())) + 1

    def _get_total_span_m(self) -> float | None:
        tab = self._girder_details_tab
        if tab is None:
            return None
        getter = getattr(tab, "_get_total_span", None)
        if getter is None or not callable(getter):
            return None
        try:
            span = getter()
        except Exception:
            return None
        try:
            span = float(span)
        except Exception:
            return None
        return span if span > 0 else None

    def _get_cross_bracing_spacing_m(self) -> float | None:
        text = (self.spacing_input.text() or "").strip()
        if not text:
            return None
        try:
            spacing_m = float(text)
        except Exception:
            return None
        if spacing_m <= 0:
            return None
        return spacing_m

    def _cross_bracing_member_count(self) -> int:
        """Compute number of cross bracing members (m) for a pair.

        Based on the provided reference:
            m = Span / CrossBracingSpacing - 1

        Span is read from Girder Details "Total Span (m)".
        Spacing is read from this tab "Spacing (m)".
        """
        span_m = self._get_total_span_m()
        spacing_m = self._get_cross_bracing_spacing_m()
        if not span_m or not spacing_m:
            return 1
        raw = (span_m / spacing_m) - 1.0
        try:
            m = int(math.floor(raw + 1e-9))
        except Exception:
            m = 1
        return max(1, m)

    def _member_ids_for_pair(self, pair_index: int) -> list[str]:
        count = self._cross_bracing_member_count()
        return [f"B{pair_index}M{i}" for i in range(1, count + 1)]

    def _refresh_member_id_display(self) -> None:
        pair_index = self._pair_index()
        count = self._cross_bracing_member_count()
        member_id = f"B{pair_index}M1"
        display_text = member_id if count <= 1 else f"B{pair_index}M1 to B{pair_index}M{count}"
        if hasattr(self, "member_id_display") and self.member_id_display is not None:
            prev = self.member_id_display.blockSignals(True)
            try:
                self.member_id_display.setText(display_text)
            finally:
                self.member_id_display.blockSignals(prev)

        # Keep the hidden combo in sync for any existing code paths.
        block = self.member_id_combo.blockSignals(True)
        try:
            self.member_id_combo.clear()
            self.member_id_combo.addItems([member_id])
            self.member_id_combo.setCurrentIndex(0)
        finally:
            self.member_id_combo.blockSignals(block)

    def _default_member_state(self) -> dict:
        # Use the tab defaults (Optimized + first options) for new members.
        return {
            "design": self._global_design_mode,
            "bracing_type": "K-Bracing",
            "bracing_section_type": "Angle",
            "bracing_section_data": None,
            "bracing_section_text": "",
            "top_bracket_type": "Angle",
            "top_bracket_data": None,
            "top_bracket_text": "",
            "bottom_bracket_type": "Angle",
            "bottom_bracket_data": None,
            "bottom_bracket_text": "",
            "spacing": "3",
        }

    def _snapshot_current_state(self) -> dict:
        return {
            "design": self._global_design_mode,
            "bracing_type": self.bracing_type_combo.currentText(),
            "bracing_section_type": self.bracing_section_type_combo.currentText(),
            "bracing_section_data": self.bracing_section_combo.currentData(),
            "bracing_section_text": self.bracing_section_combo.currentText(),
            "top_bracket_type": self.top_bracket_type_combo.currentText(),
            "top_bracket_data": self.top_bracket_size_combo.currentData(),
            "top_bracket_text": self.top_bracket_size_combo.currentText(),
            "bottom_bracket_type": self.bottom_bracket_type_combo.currentText(),
            "bottom_bracket_data": self.bottom_bracket_size_combo.currentData(),
            "bottom_bracket_text": self.bottom_bracket_size_combo.currentText(),
            "spacing": self.spacing_input.text(),
        }

    def _store_current_member_state(self) -> None:
        if not hasattr(self, "select_girders_combo") or not hasattr(self, "member_id_combo"):
            return
        key = self._active_member_key or self._current_member_key()
        if not key:
            return
        self._state_by_member_key[key] = self._snapshot_current_state()
        self._active_member_key = key

    def _set_combo_to_data_or_text(self, combo: QComboBox, desired_data, desired_text: str) -> None:
        if desired_data is not None:
            idx = combo.findData(desired_data)
            if idx >= 0:
                combo.setCurrentIndex(idx)
                return
        if desired_text:
            idx = combo.findText(desired_text)
            if idx >= 0:
                combo.setCurrentIndex(idx)

    def _apply_state(self, state: dict) -> None:
        # Apply in a safe order: set section types first (to repopulate size combos),
        # then set sizes, then design mode.
        self.design_combo.setCurrentText(self._global_design_mode)
        self.bracing_type_combo.setCurrentText(state.get("bracing_type") or self.bracing_type_combo.currentText())

        self.bracing_section_type_combo.setCurrentText(state.get("bracing_section_type") or self.bracing_section_type_combo.currentText())
        self._update_designations_for(self.bracing_section_combo, self.bracing_section_type_combo.currentText())
        self._set_combo_to_data_or_text(
            self.bracing_section_combo,
            state.get("bracing_section_data"),
            state.get("bracing_section_text") or "",
        )

        self.top_bracket_type_combo.setCurrentText(state.get("top_bracket_type") or self.top_bracket_type_combo.currentText())
        self._update_designations_for(self.top_bracket_size_combo, self.top_bracket_type_combo.currentText())
        self._set_combo_to_data_or_text(
            self.top_bracket_size_combo,
            state.get("top_bracket_data"),
            state.get("top_bracket_text") or "",
        )

        self.bottom_bracket_type_combo.setCurrentText(state.get("bottom_bracket_type") or self.bottom_bracket_type_combo.currentText())
        self._update_designations_for(self.bottom_bracket_size_combo, self.bottom_bracket_type_combo.currentText())
        self._set_combo_to_data_or_text(
            self.bottom_bracket_size_combo,
            state.get("bottom_bracket_data"),
            state.get("bottom_bracket_text") or "",
        )

        self.spacing_input.setText(state.get("spacing") or "")

        # Ensure enable/disable and previews match the restored design state.
        self._on_design_changed(self._global_design_mode)

    def _load_state_for_current_member(self) -> None:
        key = self._current_member_key()
        if not key:
            return
        self._active_member_key = key
        state = self._state_by_member_key.get(key)
        if state is None:
            state = self._default_member_state()
        guard_a = self.design_combo.blockSignals(True)
        guard_b = self.bracing_type_combo.blockSignals(True)
        guard_c = self.bracing_section_type_combo.blockSignals(True)
        guard_d = self.bracing_section_combo.blockSignals(True)
        guard_e = self.top_bracket_type_combo.blockSignals(True)
        guard_f = self.top_bracket_size_combo.blockSignals(True)
        guard_g = self.bottom_bracket_type_combo.blockSignals(True)
        guard_h = self.bottom_bracket_size_combo.blockSignals(True)
        try:
            self._apply_state(state)
        finally:
            self.design_combo.blockSignals(guard_a)
            self.bracing_type_combo.blockSignals(guard_b)
            self.bracing_section_type_combo.blockSignals(guard_c)
            self.bracing_section_combo.blockSignals(guard_d)
            self.top_bracket_type_combo.blockSignals(guard_e)
            self.top_bracket_size_combo.blockSignals(guard_f)
            self.bottom_bracket_type_combo.blockSignals(guard_g)
            self.bottom_bracket_size_combo.blockSignals(guard_h)

        # After restoring, refresh previews explicitly.
        self._update_previews()

    def _on_select_girders_index_changed(self, idx: int) -> None:
        if self._selection_sync_guard:
            return
        self._store_current_member_state()
        self._selection_sync_guard = True
        try:
            self._refresh_member_id_display()
        finally:
            self._selection_sync_guard = False
        self._load_state_for_current_member()

    def bind_girder_details_tab(self, girder_details_tab) -> None:
        """Bind to Girder Details so girder pair options reflect user inputs."""
        self._girder_details_tab = girder_details_tab
        try:
            length_input = getattr(girder_details_tab, "length_input", None)
            if length_input is not None and hasattr(length_input, "textChanged"):
                length_input.textChanged.connect(self._on_span_or_spacing_changed)
        except Exception:
            pass
        self.refresh_girder_options()

    def showEvent(self, event):  # noqa: N802 (Qt naming)
        super().showEvent(event)
        # When the tab becomes visible, refresh in case girder count changed.
        self.refresh_girder_options()

    def _girder_pairs(self) -> list[str]:
        girders = []
        if self._girder_details_tab is not None and hasattr(self._girder_details_tab, "available_girders"):
            try:
                girders = list(getattr(self._girder_details_tab, "available_girders") or [])
            except Exception:
                girders = []

        if not girders:
            girders = ["G1", "G2"]

        pairs = [f"{girders[i]} to {girders[i + 1]}" for i in range(len(girders) - 1)]
        return pairs or ["G1 to G2"]

    def refresh_girder_options(self) -> None:
        """Populate Select Girders + Member ID based on Girder Details."""
        # Save current member state before rebuilding lists.
        try:
            self._store_current_member_state()
        except Exception:
            pass
        pairs = self._girder_pairs()

        prev_pair = self.select_girders_combo.currentText().strip() if hasattr(self, "select_girders_combo") else ""

        block_a = self.select_girders_combo.blockSignals(True)
        try:
            self.select_girders_combo.clear()
            self.select_girders_combo.addItems(pairs)
            if prev_pair in pairs:
                self.select_girders_combo.setCurrentText(prev_pair)
            else:
                self.select_girders_combo.setCurrentIndex(0)
        finally:
            self.select_girders_combo.blockSignals(block_a)

        # Update the (read-only) Member ID display for the selected pair.
        self._refresh_member_id_display()

        # Restore saved/default state for the currently selected member after refresh.
        self._load_state_for_current_member()

    def _create_card_frame(self):
        card = QFrame()
        card.setStyleSheet("QFrame { border: 1px solid #d0d0d0; border-radius: 12px; background-color: #ffffff; }")
        return card

    def _create_inner_box(self):
        box = QFrame()
        box.setStyleSheet(
            "QFrame { border: 1px solid #cfcfcf; border-radius: 8px; background-color: #ffffff; }"
            "QFrame QComboBox, QFrame QLineEdit { border: none; border-bottom: 1px solid #d0d0d0; border-radius: 0px; min-height: 28px; padding: 4px 8px; background-color: #ffffff; }"
            "QFrame QComboBox:hover, QFrame QLineEdit:hover { border-bottom: 1px solid #5d5d5d; }"
            "QFrame QComboBox:focus, QFrame QLineEdit:focus { border-bottom: 1px solid #90AF13; }"
            "QFrame QLabel { border: none; }"
        )
        return box

    def _create_heading_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 12px; font-weight: 700; color: #4b4b4b; border: none;")
        return label

    def _create_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 11px; font-weight: 400; color: #4b4b4b; border: none;")
        return label

    def _add_grid_row(self, layout, row, text, widget):
        label = self._create_label(text)
        layout.addWidget(label, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        # Respect fixed-width widgets (e.g., combo boxes) so all fields remain uniform.
        try:
            fixed_width = widget.minimumWidth() == widget.maximumWidth() and widget.minimumWidth() > 0
        except Exception:
            fixed_width = False
        if fixed_width:
            widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        else:
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Left-align the widget so fixed-width combos line up.
        layout.addWidget(widget, row, 1, Qt.AlignLeft | Qt.AlignVCenter)
        return row + 1

    def _configure_combo_box(self, combo: QComboBox) -> None:
        """Keep combos stable without forcing the right-side diagram to collapse."""
        combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        combo.setMinimumContentsLength(12)
        try:
            combo.setFixedWidth(int(getattr(self, "_combo_width", 190)))
            combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        except Exception:
            pass

    def _create_bracing_layout_placeholder(self, text: str, height: int):
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumHeight(height)
        label.setStyleSheet(
            "QLabel { border: 1px solid #d0d0d0; border-radius: 10px; background-color: #f7f7f7; "
            "font-weight: bold; color: #5b5b5b; }"
        )
        return label

    def _create_preview_box(self, title):
        box = self._create_inner_box()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 12px; font-weight: 700; color: #4b4b4b; border: none;")
        layout.addWidget(heading)
        image = PlaceholderSectionPreviewWidget(title, 110)
        layout.addWidget(image)
        return box, image

    def _update_previews(self):
        if self.design_combo.currentText() != "Customized":
            # Hide geometry when optimization controls the section selection.
            for widget in [
                self.bracing_preview_label,
                self.top_bracket_preview_label,
                self.bottom_bracket_preview_label,
            ]:
                widget.set_section("", "")
            return
        self._set_preview(self.bracing_preview_label, self.bracing_section_type_combo, self.bracing_section_combo)
        self._set_preview(self.top_bracket_preview_label, self.top_bracket_type_combo, self.top_bracket_size_combo)
        self._set_preview(self.bottom_bracket_preview_label, self.bottom_bracket_type_combo, self.bottom_bracket_size_combo)

    def _apply_custom_mode(self, is_custom: bool):
        # Only allow manual section selection in Customized mode.
        # Keep the preview/diagram column visible in Optimized mode (like Girder Details).
        self.right_column.setVisible(True)
        for widget in [
            self.bracing_section_type_combo,
            self.bracing_section_combo,
            self.top_bracket_type_combo,
            self.top_bracket_size_combo,
            self.bottom_bracket_type_combo,
            self.bottom_bracket_size_combo,
        ]:
            widget.setEnabled(is_custom)

    def _on_design_changed(self, label: str):
        is_custom = label == "Customized"
        self._apply_custom_mode(is_custom)
        self._update_previews()

    def set_design_mode(self, mode_str: str) -> None:
        mode = "Customized" if str(mode_str or "").strip().lower() == "customized" else "Optimized"
        self._global_design_mode = mode
        if hasattr(self, "design_combo") and self.design_combo is not None:
            prev = self.design_combo.blockSignals(True)
            try:
                self.design_combo.setCurrentText(mode)
            finally:
                self.design_combo.blockSignals(prev)
        self._on_design_changed(mode)

    # ---- Helpers for section labels -------------------------------------
    def _display_name_for(self, designation: str, section_type: str) -> str:
        name = (designation or "").strip()
        if section_type in ("angle", "double_angle_long", "double_angle_short"):
            name = name.lstrip("∠⌒⟡⟠").strip()
            if not name.upper().startswith("IS"):
                name = f"IS {name}"
        return name

    def _fill_combo(self, combo: QComboBox, items, section_type: str):
        combo.blockSignals(True)
        combo.clear()
        for des in items:
            combo.addItem(self._display_name_for(des, section_type), des)
        combo.blockSignals(False)

    def _set_preview(self, widget: SectionPreviewWidget, type_combo: QComboBox, size_combo: QComboBox):
        stype = self._map_section_type(type_combo.currentText())
        designation = size_combo.currentData() or size_combo.currentText()
        show_double_total = True
        if stype in ("double_angle_long", "double_angle_short"):
            show_double_total = False
        widget.set_section(stype, designation, show_double_total)

    def _populate_designations(self):
        angles = self.catalog.list_angles()

        self._fill_combo(self.bracing_section_combo, angles, "angle")
        self._fill_combo(self.top_bracket_size_combo, angles, "angle")
        self._fill_combo(self.bottom_bracket_size_combo, angles, "angle")

    def _map_section_type(self, label: str) -> str:
        mapping = {
            "Angle": "angle",
            "Double Angle (Long Leg)": "double_angle_long",
            "Double Angle (Short Leg)": "double_angle_short",
            "Channel": "channel",
            "Double Channel": "double_channel",
        }
        return mapping.get(label, "angle")

    def _on_bracing_type_changed(self, label: str):
        self._update_designations_for(self.bracing_section_combo, label)
        self._update_previews()

    def _on_top_bracket_type_changed(self, label: str):
        self._update_designations_for(self.top_bracket_size_combo, label)
        self._update_previews()

    def _on_bottom_bracket_type_changed(self, label: str):
        self._update_designations_for(self.bottom_bracket_size_combo, label)
        self._update_previews()

    def _update_designations_for(self, combo: QComboBox, type_label: str):
        stype = self._map_section_type(type_label)
        if stype in ("angle", "double_angle_long", "double_angle_short"):
            items = self.catalog.list_angles()
        else:
            items = self.catalog.list_channels()
        self._fill_combo(combo, items, stype)

    # ---- External API -----------------------------------------------------
    def reset_defaults(self):
        # Clear per-member persistence so Defaults returns to a clean slate.
        self._state_by_member_key.clear()
        self._active_member_key = None

        # Refresh girder options (may have changed after Girder Defaults).
        try:
            self.refresh_girder_options()
        except Exception:
            pass

        # Drop any state that may have been snapshotted during refresh.
        self._state_by_member_key.clear()
        self._active_member_key = None

        # Reset selection to the first pair/member in a guarded way.
        self._selection_sync_guard = True
        try:
            if self.select_girders_combo.count() > 0:
                self.select_girders_combo.setCurrentIndex(0)
            if self.member_id_combo.count() > 0:
                self.member_id_combo.setCurrentIndex(0)
        finally:
            self._selection_sync_guard = False

        # With no saved state for this member, this applies default UI values
        # (Optimized + first options) and updates enable/disable + previews.
        self._load_state_for_current_member()

    def collect_data(self):
        # Ensure the latest edits are persisted to the active member.
        self._store_current_member_state()

        pairs = self._girder_pairs()

        # For the UI we configure only one member (always M1) per pair.
        # For the solver/export, expand the configured state to all members.
        by_member: dict[str, dict] = {}
        for pair_idx, pair_label in enumerate(pairs, start=1):
            base_member = f"B{pair_idx}M1"
            base_key = f"{pair_label}::{base_member}"
            base_state = self._state_by_member_key.get(base_key)
            if base_state is None:
                base_state = dict(self._default_member_state())
                self._state_by_member_key[base_key] = dict(base_state)

            for member_id in self._member_ids_for_pair(pair_idx):
                payload = dict(base_state or {})
                payload["select_girders"] = pair_label
                payload["member_id"] = member_id
                by_member[member_id] = payload

        # Backward compatible: keep current selection fields at the top-level.
        current_pair = (self.select_girders_combo.currentText() or "").strip()
        current_member = self._current_member_id().strip().upper()
        return {
            "select_girders": current_pair,
            "member_id": current_member,
            "design": self._global_design_mode,
            "bracing_type": self.bracing_type_combo.currentText(),
            "bracing_section_type": self.bracing_section_type_combo.currentText(),
            "bracing_section": self.bracing_section_combo.currentText(),
            "top_bracket_type": self.top_bracket_type_combo.currentText(),
            "top_bracket_size": self.top_bracket_size_combo.currentText(),
            "bottom_bracket_type": self.bottom_bracket_type_combo.currentText(),
            "bottom_bracket_size": self.bottom_bracket_size_combo.currentText(),
            "spacing": self.spacing_input.text(),
            "cross_bracing_by_member": by_member,
        }

    def restore_data(self, data: dict) -> None:
        """Restore previously saved cross bracing inputs."""
        if not isinstance(data, dict):
            return

        restored = data.get("cross_bracing_by_member")
        if isinstance(restored, dict):
            # Prefer restoring from the configured member (always M1) for each pair.
            rebuilt: dict[str, dict] = {}
            for _member_id, payload in restored.items():
                if not isinstance(payload, dict):
                    continue
                pair_label = str(payload.get("select_girders") or "").strip()
                member_id = str(payload.get("member_id") or _member_id or "").strip().upper()
                if not pair_label:
                    continue
                # Only store state for M1 in the UI.
                if not member_id.endswith("M1"):
                    continue
                state = dict(payload)
                state.pop("select_girders", None)
                state.pop("member_id", None)
                rebuilt[f"{pair_label}::{member_id}"] = state
            if rebuilt:
                self._state_by_member_key = rebuilt

        # Refresh dropdowns and try to restore selection.
        try:
            self.refresh_girder_options()
        except Exception:
            pass

        target_pair = str(data.get("select_girders") or "").strip()
        target_member = str(data.get("member_id") or "").strip().upper()
        if target_pair:
            try:
                self.select_girders_combo.setCurrentText(target_pair)
            except Exception:
                pass
        # Member ID is software-driven (always M1) so just refresh the display.
        try:
            self._refresh_member_id_display()
        except Exception:
            pass

        # Ensure UI reflects stored state for restored selection.
        try:
            self._load_state_for_current_member()
        except Exception:
            pass

