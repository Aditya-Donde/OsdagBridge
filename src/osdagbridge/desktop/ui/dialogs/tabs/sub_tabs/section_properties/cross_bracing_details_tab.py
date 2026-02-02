import sys
import os
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

class CrossBracingDetailsTab(QWidget):
    """Tab for Cross-Bracing Details with visual previews"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.catalog = SectionCatalog()
        self._girder_details_tab = None

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
        selection_layout.setContentsMargins(8, 4, 8, 4)
        selection_layout.setHorizontalSpacing(6)
        selection_layout.setVerticalSpacing(2)
        selection_layout.setColumnMinimumWidth(0, 130)
        selection_layout.setColumnStretch(1, 1)

        self.select_girders_combo = QComboBox()
        # Populated from Girder Details when bound.
        self._configure_combo_box(self.select_girders_combo)
        apply_field_style(self.select_girders_combo)
        selection_layout.addWidget(self._create_label("Select Girders:"), 0, 0)
        selection_layout.addWidget(self.select_girders_combo, 0, 1)

        self.member_id_combo = QComboBox()
        # Populated from Girder Details when bound. (No Custom option.)
        self._configure_combo_box(self.member_id_combo)
        apply_field_style(self.member_id_combo)
        selection_layout.addWidget(self._create_label("Member ID:"), 1, 0)
        selection_layout.addWidget(self.member_id_combo, 1, 1)

        # Keep the two selectors aligned and persist state per selection.
        self.select_girders_combo.currentIndexChanged.connect(self._on_select_girders_index_changed)
        self.member_id_combo.currentIndexChanged.connect(self._on_member_id_index_changed)

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
        inputs_grid.setColumnMinimumWidth(0, 130)
        inputs_grid.setColumnStretch(0, 0)
        inputs_grid.setColumnStretch(1, 1)

        self.design_combo = QComboBox()
        self.design_combo.addItems(["Customized", "Optimized"])
        if self.design_combo.count() > 1:
            self.design_combo.setCurrentIndex(1)  # Default to Optimized
        self._configure_combo_box(self.design_combo)
        apply_field_style(self.design_combo)
        row = self._add_grid_row(inputs_grid, 0, "Design:", self.design_combo)

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
        self.spacing_input.setPlaceholderText("Spacing (mm)")
        self.spacing_input.setValidator(QDoubleValidator(0, 100000, 2))
        apply_field_style(self.spacing_input)
        self._add_grid_row(inputs_grid, row, "Spacing:", self.spacing_input)

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
        type_layout.addWidget(self._create_image_placeholder(170))
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
        self._populate_designations()
        self._on_design_changed(self.design_combo.currentText())

        # Seed selection drop-downs with a safe default until Girder Details is bound.
        self.refresh_girder_options()

        # Ensure initial selection loads its saved/default state.
        self._load_state_for_current_member()

    def _current_member_key(self) -> str:
        pair = (self.select_girders_combo.currentText() or "").strip()
        member = (self.member_id_combo.currentText() or "").strip()
        return f"{pair}::{member}".strip(":")

    def _default_member_state(self) -> dict:
        # Use the tab defaults (Optimized + first options) for new members.
        return {
            "design": "Optimized",
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
            "spacing": "",
        }

    def _snapshot_current_state(self) -> dict:
        return {
            "design": self.design_combo.currentText(),
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
        self.design_combo.setCurrentText(state.get("design") or self.design_combo.currentText())
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
        self._on_design_changed(self.design_combo.currentText())

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
            if self.member_id_combo.count() > 0:
                self.member_id_combo.setCurrentIndex(min(max(idx, 0), self.member_id_combo.count() - 1))
        finally:
            self._selection_sync_guard = False
        self._load_state_for_current_member()

    def _on_member_id_index_changed(self, idx: int) -> None:
        if self._selection_sync_guard:
            return
        self._store_current_member_state()
        self._selection_sync_guard = True
        try:
            if self.select_girders_combo.count() > 0:
                self.select_girders_combo.setCurrentIndex(min(max(idx, 0), self.select_girders_combo.count() - 1))
        finally:
            self._selection_sync_guard = False
        self._load_state_for_current_member()

    def bind_girder_details_tab(self, girder_details_tab) -> None:
        """Bind to Girder Details so girder pair options reflect user inputs."""
        self._girder_details_tab = girder_details_tab
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
        prev_member = self.member_id_combo.currentText().strip() if hasattr(self, "member_id_combo") else ""

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

        # Member IDs follow pair index: B1..Bn (no Custom)
        member_items = [f"B{i}-1 to B{i}-15" for i in range(1, len(pairs) + 1)]
        block_b = self.member_id_combo.blockSignals(True)
        try:
            self.member_id_combo.clear()
            self.member_id_combo.addItems(member_items)
            if prev_member in member_items:
                self.member_id_combo.setCurrentText(prev_member)
            else:
                # Keep member aligned with selected pair (1-based)
                idx = max(0, self.select_girders_combo.currentIndex())
                self.member_id_combo.setCurrentIndex(min(idx, len(member_items) - 1))
        finally:
            self.member_id_combo.blockSignals(block_b)

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
        label.setStyleSheet("font-size: 12px; font-weight: 600; color: #4b4b4b; border: none;")
        return label

    def _create_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 11px; color: #4b4b4b; border: none;")
        return label

    def _add_grid_row(self, layout, row, text, widget):
        label = self._create_label(text)
        layout.addWidget(label, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(widget, row, 1)
        return row + 1

    def _configure_combo_box(self, combo: QComboBox) -> None:
        """Keep combos stable without forcing the right-side diagram to collapse."""
        combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        combo.setMinimumContentsLength(12)

    def _create_image_placeholder(self, height):
        widget = SectionPreviewWidget()
        widget.setMinimumHeight(height)
        widget.setStyleSheet("QWidget { border: 1px solid #d0d0d0; border-radius: 10px; background-color: #ffffff; }")
        return widget

    def _create_preview_box(self, title):
        box = self._create_inner_box()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 12px; font-weight: 700; color: #4b4b4b; border: none;")
        layout.addWidget(heading)
        image = self._create_image_placeholder(110)
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
        # Reset types to single angle and reload designations
        for combo in [self.bracing_section_type_combo, self.top_bracket_type_combo, self.bottom_bracket_type_combo]:
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
        self._populate_designations()
        # Select first designation for each
        for combo in [self.bracing_section_combo, self.top_bracket_size_combo, self.bottom_bracket_size_combo]:
            combo.setCurrentIndex(0 if combo.count() > 0 else -1)
        self._update_previews()

    def collect_data(self):
        # Ensure the latest edits are persisted to the active member.
        self._store_current_member_state()
        return {
            "select_girders": self.select_girders_combo.currentText(),
            "member_id": self.member_id_combo.currentText(),
            "design": self.design_combo.currentText(),
            "bracing_type": self.bracing_type_combo.currentText(),
            "bracing_section_type": self.bracing_section_type_combo.currentText(),
            "bracing_section": self.bracing_section_combo.currentText(),
            "top_bracket_type": self.top_bracket_type_combo.currentText(),
            "top_bracket_size": self.top_bracket_size_combo.currentText(),
            "bottom_bracket_type": self.bottom_bracket_type_combo.currentText(),
            "bottom_bracket_size": self.bottom_bracket_size_combo.currentText(),
            "spacing": self.spacing_input.text(),
        }

