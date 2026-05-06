"""End Diaphragm Details tab.

This tab handles inputs for end diaphragm members, supporting Cross Bracing,
Rolled Beam, and Welded Beam views.
"""

from __future__ import annotations

import re
from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLineEdit,
    QWidget,
)

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import END_DIAPHRAGM_DETAILS_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.builder import UIBuilder
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab
from osdagbridge.desktop.ui.widgets.section_viewer import SectionCatalog


class EndDiaphragmDetailsTab(SchemaTab):
    """Tab for End Diaphragm Details with visual previews and stacked views."""
    schema = END_DIAPHRAGM_DETAILS_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self.catalog = SectionCatalog()
        self._girder_details_tab = None
        self._girder_state: Dict[str, object] = {}
        self._global_design_mode = "Optimized"
        
        # State persistence per (view_type, girder-pair)
        # Note: End Diaphragm inputs apply to both ends, so we only store per pair.
        self._state_by_key: Dict[str, dict] = {}
        self._active_key: Optional[str] = None
        self._selection_sync_guard = False
        self._updating_chord_rules = False

        # Signals
        self.type_selector_combo.currentTextChanged.connect(self._on_view_type_changed)
        self.cross_bracing_type_combo.currentTextChanged.connect(self._on_cross_layout_changed)
        self.cross_bracing_section_type_combo.currentTextChanged.connect(self._on_cross_type_changed)
        self.cross_top_chord_checkbox.toggled.connect(self._on_cross_layout_changed)
        self.cross_top_chord_type_combo.currentTextChanged.connect(self._on_cross_top_type_changed)
        self.cross_bottom_chord_checkbox.toggled.connect(self._on_cross_layout_changed)
        self.cross_bottom_chord_type_combo.currentTextChanged.connect(self._on_cross_bottom_type_changed)
        
        # Common design changed signals
        for combo in [self.cross_design_combo, self.rolled_design_combo, self.welded_design_combo]:
            combo.currentTextChanged.connect(self._on_design_changed)

        self.refresh_girder_options()

    def _on_view_type_changed(self, *_args):
        self._load_state_for_current_selection()

    def _on_girder_pair_changed(self, *_args):
        if self._selection_sync_guard: return
        self._store_current_state()
        self._load_state_for_current_selection()

    def _current_key(self) -> str:
        view = self.type_selector_combo.currentText()
        pair = self.select_girders_combo.currentText()
        return f"{view}::{pair}"

    def _store_current_state(self) -> None:
        key = self._active_key or self._current_key()
        if not key: return
        state = schema_io.collect_values(self, END_DIAPHRAGM_DETAILS_SCHEMA)
        # Store extra combo data
        state["cross_bracing_section_data"] = self.cross_bracing_section_combo.currentData()
        state["cross_top_chord_size_data"] = self.cross_top_chord_size_combo.currentData()
        state["cross_bottom_chord_size_data"] = self.cross_bottom_chord_size_combo.currentData()
        state["rolled_is_section_data"] = self.rolled_is_section_combo.currentData()
        self._state_by_key[key] = state
        self._active_key = key

    def _load_state_for_current_selection(self) -> None:
        key = self._current_key()
        if not key: return
        self._active_key = key
        state = self._state_by_key.get(key) or self._get_default_state()
        
        widgets = self.findChildren(QComboBox) + self.findChildren(QCheckBox) + self.findChildren(QLineEdit)
        blocked = [w.blockSignals(True) for w in widgets]
        try:
            schema_io.restore_values(self, END_DIAPHRAGM_DETAILS_SCHEMA, state)
            # Update dynamic designations
            self._update_cross_designations()
            # Restore combo data
            self._set_combo_to_data(self.cross_bracing_section_combo, state.get("cross_bracing_section_data"))
            self._set_combo_to_data(self.cross_top_chord_size_combo, state.get("cross_top_chord_size_data"))
            self._set_combo_to_data(self.cross_bottom_chord_size_combo, state.get("cross_bottom_chord_size_data"))
            self._set_combo_to_data(self.rolled_is_section_combo, state.get("rolled_is_section_data"))
        finally:
            for w, prev in zip(widgets, blocked):
                w.blockSignals(prev)
        
        self._on_cross_layout_changed()
        self._refresh_enabled_states()

    def _get_default_state(self) -> dict:
        schema_io.reset_defaults(self, END_DIAPHRAGM_DETAILS_SCHEMA)
        return schema_io.collect_values(self, END_DIAPHRAGM_DETAILS_SCHEMA)

    def _set_combo_to_data(self, combo: QComboBox, data):
        if data is not None:
            idx = combo.findData(data)
            if idx >= 0: combo.setCurrentIndex(idx)

    def bind_girder_details_tab(self, girder_details_tab) -> None:
        self._girder_details_tab = girder_details_tab
        export_state = getattr(girder_details_tab, "export_dependency_state", None)
        if callable(export_state):
            try:
                self._girder_state = dict(export_state() or {})
            except Exception:
                self._girder_state = {}
        self.refresh_girder_options()

    def refresh_from_girder_state(self, state: dict) -> None:
        self._girder_state = dict(state or {})
        self.refresh_girder_options()

    def refresh_girder_options(self) -> None:
        self._store_current_state()
        pairs = self._girder_pairs()
        prev = self.select_girders_combo.currentText()
        
        b = self.select_girders_combo.blockSignals(True)
        self.select_girders_combo.clear()
        self.select_girders_combo.addItems(pairs)
        if prev in pairs: self.select_girders_combo.setCurrentText(prev)
        self.select_girders_combo.blockSignals(b)
        
        self._load_state_for_current_selection()

    def _girder_pairs(self) -> list[str]:
        girders = ["G1", "G2"]
        if isinstance(self._girder_state.get("available_girders"), list):
            girders = list(self._girder_state.get("available_girders") or girders)
        elif self._girder_details_tab:
            getter = getattr(self._girder_details_tab, "list_available_girders", None)
            if callable(getter):
                try:
                    girders = list(getter() or girders)
                except Exception:
                    girders = girders
        return [f"{girders[i]} to {girders[i+1]}" for i in range(len(girders)-1)] or ["G1 to G2"]

    def _on_design_changed(self, label: str):
        self._global_design_mode = "Custom" if str(label or "").strip() == "Custom" else "Optimized"
        self._refresh_enabled_states()

    def set_design_mode(self, mode_str: str) -> None:
        mode = "Custom" if str(mode_str or "").strip().lower() in {"custom", "customized"} else "Optimized"
        self._global_design_mode = mode
        for combo in (
            getattr(self, "cross_design_combo", None),
            getattr(self, "rolled_design_combo", None),
            getattr(self, "welded_design_combo", None),
        ):
            if isinstance(combo, QComboBox):
                previous = combo.blockSignals(True)
                try:
                    combo.setCurrentText(mode)
                finally:
                    combo.blockSignals(previous)
        self._refresh_enabled_states()

    def _refresh_enabled_states(self):
        view = self.type_selector_combo.currentText()
        if view == "Cross Bracing":
            is_custom = self.cross_design_combo.currentText() == "Custom"
            for w in [self.cross_bracing_section_type_combo, self.cross_bracing_section_combo,
                      self.cross_top_chord_type_combo, self.cross_top_chord_size_combo,
                      self.cross_bottom_chord_type_combo, self.cross_bottom_chord_size_combo]:
                w.setEnabled(is_custom)
        elif view == "Rolled Beam":
            self.rolled_is_section_combo.setEnabled(self.rolled_design_combo.currentText() == "Custom")
        elif view == "Welded Beam":
            self.welded_symmetry_combo.setEnabled(self.welded_design_combo.currentText() == "Custom")

    def _on_cross_layout_changed(self, *_args):
        if self._updating_chord_rules: return
        self._updating_chord_rules = True
        try:
            bracing = self.cross_bracing_type_combo.currentText()
            if bracing == "K-Bracing":
                self.cross_bottom_chord_checkbox.setChecked(True)
            
            if hasattr(self, "cross_bracing_cad_preview"):
                self.cross_bracing_cad_preview.set_layout(
                    bracing, self.cross_top_chord_checkbox.isChecked(),
                    self.cross_bottom_chord_checkbox.isChecked(),
                    "", self.select_girders_combo.currentText()
                )
        finally:
            self._updating_chord_rules = False

    def _update_cross_designations(self):
        self._update_combo_from_catalog(self.cross_bracing_section_combo, self.cross_bracing_section_type_combo.currentText())
        self._update_combo_from_catalog(self.cross_top_chord_size_combo, self.cross_top_chord_type_combo.currentText())
        self._update_combo_from_catalog(self.cross_bottom_chord_size_combo, self.cross_bottom_chord_type_combo.currentText())

    def _update_combo_from_catalog(self, combo: QComboBox, type_label: str):
        stype = {
            "Angle": "angle", "Double Angle (Long Leg)": "double_angle_long",
            "Double Angle (Short Leg)": "double_angle_short", "Channel": "channel",
            "Double Channel": "double_channel"
        }.get(type_label, "angle")
        items = self.catalog.list_angles() if "angle" in stype else self.catalog.list_channels()
        b = combo.blockSignals(True)
        combo.clear()
        for des in items:
            disp = des if des.startswith("IS") else f"IS {des}"
            combo.addItem(disp, des)
        combo.blockSignals(b)

    def _on_cross_type_changed(self, label: str): self._update_combo_from_catalog(self.cross_bracing_section_combo, label)
    def _on_cross_top_type_changed(self, label: str): self._update_combo_from_catalog(self.cross_top_chord_size_combo, label)
    def _on_cross_bottom_type_changed(self, label: str): self._update_combo_from_catalog(self.cross_bottom_chord_size_combo, label)

    def reset_defaults(self):
        self._state_by_key.clear()
        self._active_key = None
        self.refresh_girder_options()

    def collect_data(self):
        self._store_current_state()
        pairs = self._girder_pairs()
        by_member = {}
        for idx, pair in enumerate(pairs, 1):
            # Create two members per pair: E{idx}M1 and E{idx}M2
            for m_idx in [1, 2]:
                mid = f"E{idx}M{m_idx}"
                # For simplicity, we use same state for all view types in collect, but 
                # practically only one view type is active.
                view = self.type_selector_combo.currentText()
                state = self._state_by_key.get(f"{view}::{pair}") or self._get_default_state()
                by_member[mid] = dict(state)
                by_member[mid]["select_girders"] = pair
                by_member[mid]["member_id"] = mid
        
        data = schema_io.collect_values(self, END_DIAPHRAGM_DETAILS_SCHEMA)
        data.update({"end_diaphragm_by_member": by_member})
        return data

    def restore_data(self, data: dict):
        if not isinstance(data, dict): return
        widgets = self.findChildren(QComboBox) + self.findChildren(QCheckBox) + self.findChildren(QLineEdit)
        blocked = [widget.blockSignals(True) for widget in widgets]
        try:
            schema_io.restore_values(self, END_DIAPHRAGM_DETAILS_SCHEMA, data)
        finally:
            for widget, previous in zip(widgets, blocked):
                widget.blockSignals(previous)
        restored = data.get("end_diaphragm_by_member", {})
        rebuilt = {}
        for mid, payload in restored.items():
            if mid.endswith("M1"): # Only need one per pair
                view = payload.get("type_selector") or "Cross Bracing"
                pair = payload.get("select_girders")
                if pair: rebuilt[f"{view}::{pair}"] = payload
        if rebuilt:
            self._state_by_key = rebuilt
        else:
            key = self._current_key()
            if key:
                self._state_by_key = {
                    key: schema_io.collect_values(self, END_DIAPHRAGM_DETAILS_SCHEMA)
                }
        self.refresh_girder_options()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self.refresh_girder_options()
