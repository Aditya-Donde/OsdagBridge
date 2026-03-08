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
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from osdagbridge.core.utils.common import VALUES_NO_YES, VALUES_STIFFENER_DESIGN
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style

OUTSTAND_DEFAULT_TEXT = "NA"
VALUES_BEARING_STIFFENER_COUNT = ["1", "2", "3", "4"]
VALUES_STIFFENER_THICKNESS_MODE = ["All", "Customized"]
VALUES_LONGITUDINAL_STIFFENER = ["No", "Yes and 1 stiffener", "Yes and 2 stiffeners"]

class StiffenerDetailsTab(QWidget):
    """Tab for Stiffener Details with compact layout"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._girder_details_tab = None
        self._state_by_member: Dict[str, dict] = {}
        self._active_member_id: Optional[str] = None
        self._is_loading_ui: bool = False
        self.init_ui()

    def init_ui(self):
        combo_width = 190  # keep all combo boxes strictly same width
        self._form_label_width = 245

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

        girder_label = QLabel("Select Member ID:")
        girder_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #3a3a3a; border: none;")
        girder_row.addWidget(girder_label)

        self.girder_member_combo = QComboBox()
        apply_field_style(self.girder_member_combo)
        self.girder_member_combo.setFixedWidth(combo_width)
        self.girder_member_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        girder_row.addWidget(self.girder_member_combo, 1)

        left_layout.addLayout(girder_row)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(8)
        self.apply_to_all_btn = QPushButton("Apply changes to all custom")
        self.apply_to_all_btn.setFixedHeight(26)
        self.apply_to_all_btn.setStyleSheet(
            "QPushButton { background: #ffffff; border: 1px solid #cfcfcf; border-radius: 6px; "
            "padding: 4px 10px; font-size: 11px; color: #2b2b2b; }"
            "QPushButton:hover { border-color: #90AF13; }"
            "QPushButton:pressed { background: #f0f0f0; }"
            "QPushButton:disabled { color: #8a8a8a; }"
        )
        action_row.addStretch(1)
        action_row.addWidget(self.apply_to_all_btn)
        left_layout.addLayout(action_row)

        stiffener_heading = QLabel("Stiffener Inputs")
        stiffener_heading.setStyleSheet("font-size: 11px; font-weight: 700; color: #000000; border: none; margin-top: 4px;")
        left_layout.addWidget(stiffener_heading)

        inputs_grid = QGridLayout()
        inputs_grid.setContentsMargins(0, 0, 0, 0)
        inputs_grid.setHorizontalSpacing(12)
        inputs_grid.setVerticalSpacing(10)
        inputs_grid.setColumnMinimumWidth(0, self._form_label_width)
        inputs_grid.setColumnStretch(0, 0)
        inputs_grid.setColumnStretch(1, 1)

        self.bearing_count_combo = QComboBox()
        self.bearing_count_combo.addItems(VALUES_BEARING_STIFFENER_COUNT)
        apply_field_style(self.bearing_count_combo)
        self.bearing_count_combo.setFixedWidth(combo_width)
        self.bearing_count_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row = self._add_form_row(
            inputs_grid,
            0,
            "No. of Bearing Stiffeners at each end\n(on one side only):",
            self.bearing_count_combo,
        )

        self.bearing_thick_combo = QComboBox()
        self.bearing_thick_combo.addItems(VALUES_STIFFENER_THICKNESS_MODE)
        apply_field_style(self.bearing_thick_combo)
        self.bearing_thick_combo.setFixedWidth(combo_width)
        self.bearing_thick_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row = self._add_form_row(inputs_grid, row, "Bearing Stiffener Thickness (mm):", self.bearing_thick_combo)

        self.bearing_outstand_input = QTextEdit()
        self.bearing_outstand_input.setReadOnly(True)
        self.bearing_outstand_input.setText(OUTSTAND_DEFAULT_TEXT)
        self.bearing_outstand_input.setFixedHeight(28)
        self.bearing_outstand_input.setFixedWidth(combo_width)
        self.bearing_outstand_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bearing_outstand_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bearing_outstand_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.bearing_outstand_input.setStyleSheet(
            "QTextEdit { border: 1px solid #d0d0d0; border-radius: 6px; background: #ffffff; "
            "color: #5b5b5b; font-size: 11px; }"
        )
        row = self._add_form_row(inputs_grid, row, "Outstand of Bearing Stiffener (mm):", self.bearing_outstand_input)

        self.intermediate_combo = QComboBox()
        self.intermediate_combo.addItems(VALUES_NO_YES)
        apply_field_style(self.intermediate_combo)
        self.intermediate_combo.setFixedWidth(combo_width)
        self.intermediate_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row = self._add_form_row(inputs_grid, row, "Intermediate Stiffener:", self.intermediate_combo)

        self.intermediate_spacing_input = QLineEdit()
        self.intermediate_spacing_input.setValidator(QIntValidator(1, 10**9, self.intermediate_spacing_input))
        apply_field_style(self.intermediate_spacing_input)
        self.intermediate_spacing_input.setPlaceholderText("NA")
        self.intermediate_spacing_input.setFixedWidth(combo_width)
        self.intermediate_spacing_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row = self._add_form_row(inputs_grid, row, "Intermediate Stiffener Spacing:", self.intermediate_spacing_input)

        self.intermediate_thick_combo = QComboBox()
        self.intermediate_thick_combo.addItems(VALUES_STIFFENER_THICKNESS_MODE)
        apply_field_style(self.intermediate_thick_combo)
        self.intermediate_thick_combo.setFixedWidth(combo_width)
        self.intermediate_thick_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row = self._add_form_row(inputs_grid, row, "Intermediate Stiffener Thickness (mm):", self.intermediate_thick_combo)

        self.intermediate_outstand_input = QTextEdit()
        self.intermediate_outstand_input.setReadOnly(True)
        self.intermediate_outstand_input.setText(OUTSTAND_DEFAULT_TEXT)
        self.intermediate_outstand_input.setFixedHeight(28)
        self.intermediate_outstand_input.setFixedWidth(combo_width)
        self.intermediate_outstand_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.intermediate_outstand_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.intermediate_outstand_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.intermediate_outstand_input.setStyleSheet(
            "QTextEdit { border: 1px solid #d0d0d0; border-radius: 6px; background: #ffffff; "
            "color: #5b5b5b; font-size: 11px; }"
        )
        row = self._add_form_row(inputs_grid, row, "Outstand of Intermediate Stiffener (mm):", self.intermediate_outstand_input)

        self.longitudinal_combo = QComboBox()
        self.longitudinal_combo.addItems(VALUES_LONGITUDINAL_STIFFENER)
        apply_field_style(self.longitudinal_combo)
        self.longitudinal_combo.setFixedWidth(combo_width)
        self.longitudinal_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row = self._add_form_row(inputs_grid, row, "Longitudinal Stiffener:", self.longitudinal_combo)

        self.long_thick_combo = QComboBox()
        self.long_thick_combo.addItems(VALUES_STIFFENER_THICKNESS_MODE)
        apply_field_style(self.long_thick_combo)
        self.long_thick_combo.setFixedWidth(combo_width)
        self.long_thick_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row = self._add_form_row(inputs_grid, row, "Longitudinal Stiffener Thickness (mm):", self.long_thick_combo)

        left_layout.addLayout(inputs_grid)

        buckling_heading = QLabel("Web Buckling Details")
        buckling_heading.setStyleSheet("font-size: 11px; font-weight: 700; color: #000000; border: none; margin-top: 4px;")
        left_layout.addWidget(buckling_heading)

        buckling_grid = QGridLayout()
        buckling_grid.setContentsMargins(0, 0, 0, 0)
        buckling_grid.setHorizontalSpacing(12)
        buckling_grid.setVerticalSpacing(10)
        buckling_grid.setColumnMinimumWidth(0, self._form_label_width)

        self.method_combo = QComboBox()
        self.method_combo.addItems(VALUES_STIFFENER_DESIGN)
        apply_field_style(self.method_combo)
        self.method_combo.setFixedWidth(combo_width)
        self.method_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
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
        self.bearing_count_combo.currentTextChanged.connect(self._on_any_input_changed)
        self.bearing_thick_combo.currentTextChanged.connect(self._on_any_input_changed)
        self.intermediate_combo.currentTextChanged.connect(self._on_intermediate_changed)
        self.longitudinal_combo.currentTextChanged.connect(self._on_longitudinal_changed)
        self.intermediate_spacing_input.textChanged.connect(self._on_any_input_changed)
        self.intermediate_thick_combo.currentTextChanged.connect(self._on_any_input_changed)
        self.long_thick_combo.currentTextChanged.connect(self._on_any_input_changed)
        self.method_combo.currentTextChanged.connect(self._on_any_input_changed)
        self.apply_to_all_btn.clicked.connect(self._apply_current_to_all_members)

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
        label.setWordWrap(True)
        label_width = int(getattr(self, "_form_label_width", 245) or 245)
        label.setMinimumWidth(label_width)
        label.setMaximumWidth(label_width)
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        return label

    def _add_form_row(self, layout, row, text, widget):
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
        layout.addWidget(widget, row, 1)
        return row + 1

    def bind_girder_details_tab(self, girder_details_tab) -> None:
        """Bind to the Girder Details tab to populate members and detect optimized members."""
        self._girder_details_tab = girder_details_tab
        self.refresh_girder_members()

    def refresh_girder_members(self) -> None:
        """Refresh the Select Girder Member dropdown from Girder Details segment chains."""
        # Persist any in-progress edits before rebuilding the member list.
        self._store_current_member_state()

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
                    # Guide the user to the offending member + field.
                    try:
                        self.girder_member_combo.setCurrentText(str(member_id))
                    except Exception:
                        pass
                    try:
                        self.intermediate_spacing_input.setFocus()
                        self.intermediate_spacing_input.selectAll()
                    except Exception:
                        pass
                    raise ValueError(
                        f"Intermediate Stiffener Spacing (mm) is required for member '{member_id}' when Intermediate Stiffener is Yes."
                    )

    def collect_data(self) -> dict:
        self._store_current_member_state()
        # Ensure all current members get a state entry so save/restore is consistent.
        for member_id in self._list_current_member_ids():
            if member_id not in self._state_by_member:
                self._state_by_member[member_id] = dict(self._default_member_state())
        return {
            "stiffener_by_member": dict(self._state_by_member),
        }

    def reset_defaults(self) -> None:
        """Reset UI + per-member stored values to the initial defaults."""
        self._state_by_member.clear()
        self._active_member_id = None

        # Refresh members first (depends on Girder Details).
        try:
            self.refresh_girder_members()
        except Exception:
            pass

        # Force UI to default member state for current selection.
        member_id = (self.girder_member_combo.currentText() or "").strip()
        if member_id:
            self._active_member_id = member_id
            self._load_member_state(member_id)

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
            "bearing_stiffeners_each_end": "2",
            "bearing_thickness_mode": "All",
            "bearing_outstand_mm": OUTSTAND_DEFAULT_TEXT,
            "intermediate_stiffener": "No",
            "intermediate_spacing_mm": "NA",
            "intermediate_outstand_mm": OUTSTAND_DEFAULT_TEXT,
            "longitudinal_stiffener": "Yes and 1 stiffener",
            "intermediate_thickness_mode": "All",
            "longitudinal_thickness_mode": "All",
            "shear_buckling_method": VALUES_STIFFENER_DESIGN[0] if VALUES_STIFFENER_DESIGN else "",
        }

    def _store_current_member_state(self) -> None:
        if self._is_loading_ui:
            return
        if not self._active_member_id:
            return
        self._state_by_member[self._active_member_id] = {
            "bearing_stiffeners_each_end": self.bearing_count_combo.currentText(),
            "bearing_thickness_mode": self.bearing_thick_combo.currentText(),
            "bearing_outstand_mm": self.bearing_outstand_input.toPlainText().strip(),
            "intermediate_stiffener": self.intermediate_combo.currentText(),
            "intermediate_spacing_mm": self.intermediate_spacing_input.text().strip(),
            "intermediate_outstand_mm": self.intermediate_outstand_input.toPlainText().strip(),
            "longitudinal_stiffener": self.longitudinal_combo.currentText(),
            "intermediate_thickness_mode": self.intermediate_thick_combo.currentText(),
            "longitudinal_thickness_mode": self.long_thick_combo.currentText(),
            "shear_buckling_method": self.method_combo.currentText(),
        }

    def _load_member_state(self, member_id: str) -> None:
        # Ensure every member has a state entry.
        if member_id not in self._state_by_member:
            self._state_by_member[member_id] = dict(self._default_member_state())
        state = dict(self._state_by_member.get(member_id) or self._default_member_state())

        self._is_loading_ui = True

        block_a = self.intermediate_combo.blockSignals(True)
        block_b = self.longitudinal_combo.blockSignals(True)
        block_c = self.method_combo.blockSignals(True)
        try:
            self.intermediate_combo.setCurrentText(state.get("intermediate_stiffener", "No"))
            self.longitudinal_combo.setCurrentText(state.get("longitudinal_stiffener", "Yes and 1 stiffener"))
            self.intermediate_thick_combo.setCurrentText(state.get("intermediate_thickness_mode", "All"))
            self.long_thick_combo.setCurrentText(state.get("longitudinal_thickness_mode", "All"))
            self.method_combo.setCurrentText(state.get("shear_buckling_method", self.method_combo.itemText(0)))

            self.bearing_count_combo.setCurrentText(state.get("bearing_stiffeners_each_end", "2"))
            self.bearing_thick_combo.setCurrentText(state.get("bearing_thickness_mode", "All"))
            self.bearing_outstand_input.setText(state.get("bearing_outstand_mm", OUTSTAND_DEFAULT_TEXT))
            self.intermediate_outstand_input.setText(state.get("intermediate_outstand_mm", OUTSTAND_DEFAULT_TEXT))

            # spacing text is managed by _on_intermediate_changed
            self.intermediate_spacing_input.setText(str(state.get("intermediate_spacing_mm", "NA")))
        finally:
            self.intermediate_combo.blockSignals(block_a)
            self.longitudinal_combo.blockSignals(block_b)
            self.method_combo.blockSignals(block_c)
            self._is_loading_ui = False

        self._on_intermediate_changed(self.intermediate_combo.currentText())
        self._on_longitudinal_changed(self.longitudinal_combo.currentText())
        self._update_outstand_fields(member_id)
        self._refresh_enabled_state(member_id)
        # Keep in-memory state synced even when user only edits a single member.
        self._store_current_member_state()

    def _on_member_changed(self, member_id: str) -> None:
        member_id = str(member_id or "").strip()
        if not member_id:
            return

        if self._active_member_id and self._active_member_id != member_id:
            self._store_current_member_state()

        self._active_member_id = member_id
        self._load_member_state(member_id)

    def _on_any_input_changed(self, *_args) -> None:
        """Persist UI edits into per-member state as the user types/selects."""
        self._store_current_member_state()

    def _update_outstand_fields(self, member_id: str) -> None:
        computed = self._compute_outstand_value(member_id)
        value = computed if computed is not None else OUTSTAND_DEFAULT_TEXT
        prev_a = self.bearing_outstand_input.blockSignals(True)
        prev_b = self.intermediate_outstand_input.blockSignals(True)
        try:
            self.bearing_outstand_input.setText(value)
            self.intermediate_outstand_input.setText(value)
        finally:
            self.bearing_outstand_input.blockSignals(prev_a)
            self.intermediate_outstand_input.blockSignals(prev_b)

    def _compute_outstand_value(self, member_id: str) -> Optional[str]:
        if self._girder_details_tab is None:
            return None
        if not hasattr(self._girder_details_tab, "get_member_section_dimensions"):
            return None

        dims = None
        try:
            dims = self._girder_details_tab.get_member_section_dimensions(member_id)
        except Exception:
            dims = None

        if not isinstance(dims, dict):
            return None

        try:
            top_width = float(dims.get("top_flange_width_mm") or 0.0)
            bottom_width = float(dims.get("bottom_flange_width_mm") or 0.0)
            web_thickness = float(dims.get("web_thickness_mm") or 0.0)
        except (TypeError, ValueError):
            return None

        if top_width <= 0 or bottom_width <= 0 or web_thickness <= 0:
            return None

        outstand = (min(top_width, bottom_width) - web_thickness) / 2.0
        if outstand <= 0:
            return None

        text = f"{outstand:.3f}".rstrip("0").rstrip(".")
        return text or None

    def _on_intermediate_changed(self, text: str) -> None:
        is_yes = str(text).strip().startswith("Yes")
        if not is_yes:
            prev = self.intermediate_spacing_input.blockSignals(True)
            try:
                self.intermediate_spacing_input.setText("NA")
            finally:
                self.intermediate_spacing_input.blockSignals(prev)
            # Reset dependent selections when not applicable.
            prev_mode = self.intermediate_thick_combo.blockSignals(True)
            try:
                self.intermediate_thick_combo.setCurrentText("All")
            finally:
                self.intermediate_thick_combo.blockSignals(prev_mode)
        else:
            if self.intermediate_spacing_input.text().strip().upper() == "NA":
                self.intermediate_spacing_input.clear()
        self._refresh_enabled_state(self._active_member_id or "")
        self._store_current_member_state()

    def _on_longitudinal_changed(self, text: str) -> None:
        is_yes = str(text).strip() == "Yes"
        if not is_yes:
            prev_mode = self.long_thick_combo.blockSignals(True)
            try:
                self.long_thick_combo.setCurrentText("All")
            finally:
                self.long_thick_combo.blockSignals(prev_mode)
        self._refresh_enabled_state(self._active_member_id or "")
        self._store_current_member_state()

    def _is_member_optimized(self, member_id: str) -> bool:
        if self._girder_details_tab is None:
            return False
        if hasattr(self._girder_details_tab, "is_member_optimized"):
            try:
                return bool(self._girder_details_tab.is_member_optimized(member_id))
            except Exception:
                return False
        return False

    def _refresh_enabled_state(self, member_id: str) -> None:
        member_id = str(member_id or self._active_member_id or "").strip()
        optimized = self._is_member_optimized(member_id) if member_id else False

        base_enabled = not optimized
        self.bearing_count_combo.setEnabled(base_enabled)
        self.bearing_thick_combo.setEnabled(base_enabled)
        self.bearing_outstand_input.setEnabled(base_enabled)
        self.intermediate_outstand_input.setEnabled(base_enabled)
        self.intermediate_combo.setEnabled(base_enabled)
        self.longitudinal_combo.setEnabled(base_enabled)
        self.method_combo.setEnabled(base_enabled)

        intermediate_yes = self.intermediate_combo.currentText().strip() == "Yes"
        longitudinal_yes = self.longitudinal_combo.currentText().strip().startswith("Yes")

        self.intermediate_spacing_input.setEnabled(base_enabled and intermediate_yes)
        self.intermediate_thick_combo.setEnabled(base_enabled and intermediate_yes)
        self.long_thick_combo.setEnabled(base_enabled and longitudinal_yes)

        # If optimized, applying changes makes no sense.
        self.apply_to_all_btn.setEnabled(base_enabled)

    def _list_current_member_ids(self) -> list[str]:
        members: list[str] = []
        for i in range(self.girder_member_combo.count()):
            try:
                members.append(str(self.girder_member_combo.itemText(i)).strip())
            except Exception:
                continue
        return [m for m in members if m]

    def _apply_current_to_all_members(self) -> None:
        """Copy the currently selected member's inputs to all members."""
        self._store_current_member_state()
        if not self._active_member_id:
            return

        template = dict(self._state_by_member.get(self._active_member_id) or self._default_member_state())
        for member_id in self._list_current_member_ids():
            if self._is_member_optimized(member_id):
                continue
            self._state_by_member[member_id] = dict(template)

        # Re-load to ensure the UI reflects the stored state for the active member.
        self._load_member_state(self._active_member_id)



