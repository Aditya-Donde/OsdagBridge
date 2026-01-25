"""Stiffener Details tab.

This tab is part of Member Properties (Section Properties) and stores inputs per girder member.
"""

from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from osdagbridge.core.utils.common import VALUES_YES_NO, VALUES_STIFFENER_DESIGN
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style

class StiffenerDetailsTab(QWidget):
    """Tab for Stiffener Details with compact layout"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._girder_details_tab = None
        self._state_by_member: Dict[str, dict] = {}
        self._active_member_id: Optional[str] = None
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
        container.setStyleSheet("background-color: #f4f4f4;")

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(4)

        # Combined card for inputs and description
        card_frame = self._create_card_frame()
        card_layout = QHBoxLayout(card_frame)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(18)

        # Left column - inputs
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        girder_row = QHBoxLayout()
        girder_row.setContentsMargins(0, 0, 0, 0)
        girder_row.setSpacing(10)

        girder_label = QLabel("Select Girder Member:")
        girder_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #3a3a3a; border: none;")
        girder_row.addWidget(girder_label)

        self.girder_member_combo = QComboBox()
        apply_field_style(self.girder_member_combo)
        self.girder_member_combo.setFixedWidth(190)
        self.girder_member_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        girder_row.addWidget(self.girder_member_combo, 1)

        left_layout.addLayout(girder_row)

        stiffener_heading = QLabel("Stiffener Inputs")
        stiffener_heading.setStyleSheet("font-size: 11px; font-weight: 700; color: #000000; border: none; margin-top: 4px;")
        left_layout.addWidget(stiffener_heading)

        inputs_grid = QGridLayout()
        inputs_grid.setContentsMargins(0, 0, 0, 0)
        inputs_grid.setHorizontalSpacing(12)
        inputs_grid.setVerticalSpacing(10)
        inputs_grid.setColumnMinimumWidth(0, 180)
        inputs_grid.setColumnStretch(0, 0)
        inputs_grid.setColumnStretch(1, 1)

        self.intermediate_combo = QComboBox()
        self.intermediate_combo.addItems(VALUES_YES_NO)
        apply_field_style(self.intermediate_combo)
        row = self._add_form_row(inputs_grid, 0, "Intermediate Stiffener:", self.intermediate_combo)

        self.intermediate_spacing_input = QLineEdit()
        self.intermediate_spacing_input.setValidator(QIntValidator(1, 10**9, self.intermediate_spacing_input))
        apply_field_style(self.intermediate_spacing_input)
        self.intermediate_spacing_input.setPlaceholderText("NA")
        row = self._add_form_row(inputs_grid, row, "Intermediate Stiffener Spacing (mm):", self.intermediate_spacing_input)

        self.longitudinal_combo = QComboBox()
        self.longitudinal_combo.addItems(VALUES_YES_NO)
        apply_field_style(self.longitudinal_combo)
        row = self._add_form_row(inputs_grid, row, "Longitudinal Stiffener:", self.longitudinal_combo)

        self.intermediate_thick_combo = QComboBox()
        self.intermediate_thick_combo.addItems(["All", "Customized"])
        apply_field_style(self.intermediate_thick_combo)
        row = self._add_form_row(inputs_grid, row, "Intermediate Stiffener Thickness (mm):", self.intermediate_thick_combo)

        self.long_thick_combo = QComboBox()
        self.long_thick_combo.addItems(["All", "Customized"])
        apply_field_style(self.long_thick_combo)
        row = self._add_form_row(inputs_grid, row, "Longitudinal Stiffener Thickness (mm):", self.long_thick_combo)

        left_layout.addLayout(inputs_grid)

        buckling_heading = QLabel("Web Buckling Details")
        buckling_heading.setStyleSheet("font-size: 11px; font-weight: 700; color: #000000; border: none; margin-top: 4px;")
        left_layout.addWidget(buckling_heading)

        buckling_grid = QGridLayout()
        buckling_grid.setContentsMargins(0, 0, 0, 0)
        buckling_grid.setHorizontalSpacing(12)
        buckling_grid.setVerticalSpacing(10)
        buckling_grid.setColumnMinimumWidth(0, 180)

        self.method_combo = QComboBox()
        self.method_combo.addItems(VALUES_STIFFENER_DESIGN)
        apply_field_style(self.method_combo)
        self._add_form_row(buckling_grid, 0, "Shear Buckling Design Method:", self.method_combo)

        left_layout.addLayout(buckling_grid)

        card_layout.addWidget(left_column, 2)

        # Right column - description
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        desc_heading = QLabel("Description")
        desc_heading.setStyleSheet("font-size: 11px; font-weight: 700; color: #000000; border: none;")
        right_layout.addWidget(desc_heading)

        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setPlaceholderText("Describe stiffener assumptions or notes here.")
        self.description_text.setMinimumHeight(210)
        self.description_text.setStyleSheet(
            "QTextEdit { border: 1px solid #d0d0d0; border-radius: 6px; background: #ffffff; color: #3a3a3a; font-size: 11px; }"
        )
        right_layout.addWidget(self.description_text, 1)

        card_layout.addWidget(right_column, 3)

        container_layout.addWidget(card_frame)

        # Dynamic image box
        image_box = self._create_card_frame()
        image_layout = QVBoxLayout(image_box)
        image_layout.setContentsMargins(16, 16, 16, 16)
        image_layout.setSpacing(8)

        self.dynamic_image_label = QLabel("Dynamic Image")
        self.dynamic_image_label.setAlignment(Qt.AlignCenter)
        self.dynamic_image_label.setMinimumHeight(140)
        self.dynamic_image_label.setStyleSheet(
            "QLabel { border: 1px solid #d8d8d8; border-radius: 8px; background-color: #f8f8f8; "
            "font-weight: 600; color: #5b5b5b; font-size: 11px; }"
        )
        image_layout.addWidget(self.dynamic_image_label)
        container_layout.addWidget(image_box)


        # Signals
        self.girder_member_combo.currentTextChanged.connect(self._on_member_changed)
        self.intermediate_combo.currentTextChanged.connect(self._on_intermediate_changed)
        self.longitudinal_combo.currentTextChanged.connect(self._on_longitudinal_changed)

        # Defaults
        self._on_intermediate_changed(self.intermediate_combo.currentText())
        self._on_longitudinal_changed(self.longitudinal_combo.currentText())
        self.refresh_girder_members()

    def _create_card_frame(self):
        card = QFrame()
        card.setStyleSheet(
            "QFrame { border: 1px solid #d6d6d6; border-radius: 8px; background-color: #f7f7f7; }"
        )
        return card

    def _create_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 11px; color: #3a3a3a; border: none;")
        return label

    def _add_form_row(self, layout, row, text, widget):
        label = self._create_label(text)
        layout.addWidget(label, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(widget, row, 1)
        return row + 1

    def bind_girder_details_tab(self, girder_details_tab) -> None:
        """Bind to the Girder Details tab to populate members and detect optimized members."""
        self._girder_details_tab = girder_details_tab
        self.refresh_girder_members()

    def refresh_girder_members(self) -> None:
        """Refresh the Select Girder Member dropdown from Girder Details segment chains."""
        members = []
        if self._girder_details_tab is not None and hasattr(self._girder_details_tab, "list_all_member_ids"):
            try:
                members = list(self._girder_details_tab.list_all_member_ids() or [])
            except Exception:
                members = []

        # Fall back to a sane default when Girder Details is not bound yet.
        if not members:
            members = ["G1-1"]

        previous = self.girder_member_combo.blockSignals(True)
        try:
            current = self.girder_member_combo.currentText().strip()
            self.girder_member_combo.clear()
            for member_id in members:
                self.girder_member_combo.addItem(str(member_id), str(member_id))
            # Default should show the very first girder member.
            target = current if current in members else members[0]
            self.girder_member_combo.setCurrentText(target)
        finally:
            self.girder_member_combo.blockSignals(previous)

        # Ensure state exists and UI is synced to the active selection.
        self._on_member_changed(self.girder_member_combo.currentText())

    def validate(self) -> None:
        """Validate current stored inputs before saving the dialog."""
        self._store_current_member_state()
        for member_id, state in self._state_by_member.items():
            if self._is_member_optimized(member_id):
                continue
            if state.get("intermediate_stiffener") == "Yes":
                spacing = str(state.get("intermediate_spacing_mm") or "").strip()
                if not spacing.isdigit() or int(spacing) <= 0:
                    raise ValueError(
                        f"Intermediate Stiffener Spacing (mm) is required for {member_id} when Intermediate Stiffener is Yes."
                    )

    def collect_data(self) -> dict:
        self._store_current_member_state()
        return {
            "stiffener_by_member": dict(self._state_by_member),
        }

    def restore_data(self, data: dict) -> None:
        """Restore previously saved stiffener inputs.

        Args:
            data: Dict as returned by collect_data() (or compatible).
        """
        if not isinstance(data, dict):
            return
        restored = data.get("stiffener_by_member", {})
        if not isinstance(restored, dict):
            restored = {}
        # Replace the per-member state and refresh UI.
        self._state_by_member = dict(restored)
        try:
            self.refresh_girder_members()
        except Exception:
            pass

    def showEvent(self, event):  # noqa: N802 (Qt naming)
        super().showEvent(event)
        # When the tab becomes visible, refresh member list in case girder segments changed.
        self.refresh_girder_members()

    def _default_member_state(self) -> dict:
        return {
            "intermediate_stiffener": "No",
            "intermediate_spacing_mm": "NA",
            "longitudinal_stiffener": "No",
            "intermediate_thickness_mode": "All",
            "longitudinal_thickness_mode": "All",
            "shear_buckling_method": VALUES_STIFFENER_DESIGN[0] if VALUES_STIFFENER_DESIGN else "",
        }

    def _store_current_member_state(self) -> None:
        if not self._active_member_id:
            return
        self._state_by_member[self._active_member_id] = {
            "intermediate_stiffener": self.intermediate_combo.currentText(),
            "intermediate_spacing_mm": self.intermediate_spacing_input.text().strip(),
            "longitudinal_stiffener": self.longitudinal_combo.currentText(),
            "intermediate_thickness_mode": self.intermediate_thick_combo.currentText(),
            "longitudinal_thickness_mode": self.long_thick_combo.currentText(),
            "shear_buckling_method": self.method_combo.currentText(),
        }

    def _load_member_state(self, member_id: str) -> None:
        state = self._state_by_member.get(member_id) or self._default_member_state()

        block_a = self.intermediate_combo.blockSignals(True)
        block_b = self.longitudinal_combo.blockSignals(True)
        block_c = self.method_combo.blockSignals(True)
        try:
            self.intermediate_combo.setCurrentText(state.get("intermediate_stiffener", "No"))
            self.longitudinal_combo.setCurrentText(state.get("longitudinal_stiffener", "No"))
            self.intermediate_thick_combo.setCurrentText(state.get("intermediate_thickness_mode", "All"))
            self.long_thick_combo.setCurrentText(state.get("longitudinal_thickness_mode", "All"))
            self.method_combo.setCurrentText(state.get("shear_buckling_method", self.method_combo.itemText(0)))

            # spacing text is managed by _on_intermediate_changed
            self.intermediate_spacing_input.setText(str(state.get("intermediate_spacing_mm", "NA")))
        finally:
            self.intermediate_combo.blockSignals(block_a)
            self.longitudinal_combo.blockSignals(block_b)
            self.method_combo.blockSignals(block_c)

        self._on_intermediate_changed(self.intermediate_combo.currentText())
        self._on_longitudinal_changed(self.longitudinal_combo.currentText())
        self._update_enabled_state(member_id)

    def _on_member_changed(self, member_id: str) -> None:
        member_id = str(member_id or "").strip()
        if not member_id:
            return

        if self._active_member_id and self._active_member_id != member_id:
            self._store_current_member_state()

        self._active_member_id = member_id
        self._load_member_state(member_id)

    def _on_intermediate_changed(self, text: str) -> None:
        is_yes = str(text).strip() == "Yes"
        if not is_yes:
            prev = self.intermediate_spacing_input.blockSignals(True)
            try:
                self.intermediate_spacing_input.setText("NA")
            finally:
                self.intermediate_spacing_input.blockSignals(prev)
            self.intermediate_spacing_input.setEnabled(False)
        else:
            if self.intermediate_spacing_input.text().strip().upper() == "NA":
                self.intermediate_spacing_input.clear()
            self.intermediate_spacing_input.setEnabled(True)

    def _on_longitudinal_changed(self, text: str) -> None:
        is_yes = str(text).strip() == "Yes"
        self.long_thick_combo.setEnabled(is_yes)

    def _is_member_optimized(self, member_id: str) -> bool:
        if self._girder_details_tab is None:
            return False
        if hasattr(self._girder_details_tab, "is_member_optimized"):
            try:
                return bool(self._girder_details_tab.is_member_optimized(member_id))
            except Exception:
                return False
        return False

    def _update_enabled_state(self, member_id: str) -> None:
        optimized = self._is_member_optimized(member_id)
        
        # Disable all inputs when member is optimized
        for widget in (
            self.intermediate_combo,
            self.longitudinal_combo,
            self.intermediate_thick_combo,
            self.long_thick_combo,
            self.method_combo,
        ):
            widget.setEnabled(not optimized)
        
        # Handle spacing input based on both optimized state and intermediate stiffener selection
        if optimized:
            self.intermediate_spacing_input.setEnabled(False)
        else:
            is_yes = self.intermediate_combo.currentText().strip() == "Yes"
            self.intermediate_spacing_input.setEnabled(is_yes)



