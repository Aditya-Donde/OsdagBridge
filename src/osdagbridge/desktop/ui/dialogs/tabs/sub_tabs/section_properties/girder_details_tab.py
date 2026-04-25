"""Girder Details tab.

This tab handles the master configuration of girders and their segments.
It manages geometry (span, segments), design mode, and section properties.
"""

from __future__ import annotations

import copy
import math
import re
from typing import Dict, List, Optional, Set, Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QStyledItemDelegate,
    QDialog,
)
from PySide6.QtGui import QDoubleValidator

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import GIRDER_DETAILS_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab
from osdagbridge.desktop.ui.widgets.section_viewer import SectionCatalog
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.girder_helpers import BoundsDialog, ThicknessSelectionDialog


class _ReadOnlyCellDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index): return None

class _EndDistanceDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QDoubleValidator(0.0, 1000.0, 3, editor))
        return editor

class GirderDetailsTab(SchemaTab):
    """Tab for Girder Details - Geometry and Section Properties."""
    schema = GIRDER_DETAILS_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self.catalog = SectionCatalog()

        self._thickness_values = GIRDER_DETAILS_SCHEMA.get("thickness_values_mm", [])
        
        # Geometry state
        self.available_girders: List[str] = ["G1"]
        self.segment_chain: Dict[str, List[dict]] = {}
        self._current_girder: str = "G1"
        self._current_segment_index: int = 0
        
        # Property state (nested: girder -> member_id -> {inputs, bounds})
        self._member_state: Dict[str, Dict[str, dict]] = {}
        self._dirty_members: Set[str] = set()
        
        # Defaults
        cfg = GIRDER_DETAILS_SCHEMA.get("defaults", {})
        self._default_member_length_m = float(cfg.get("member_length_m", 30.0))
        self._default_distance_start_m = float(cfg.get("distance_start_m", 0.0))
        self._max_girder_count = int(cfg.get("max_girder_count", 20))
        self._dimension_bounds = self._default_dimension_bounds()

        # Flags
        self._suppress_member_state_updates = False
        self._suppress_distance_updates = False
        self._suppress_member_switch_prompt = False

        # Manual segment table construction (too custom for current UIBuilder)
        self._setup_segment_table()
        
        # Signals
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self.is_section_combo.currentTextChanged.connect(self._on_rolled_section_changed)
        self.span_combo.currentTextChanged.connect(self._on_span_changed)
        
        # Wire thickness mode changes
        self.web_thickness_combo.currentTextChanged.connect(lambda t: self._on_thickness_mode_changed("web_thickness", t))
        self.top_thickness_combo.currentTextChanged.connect(lambda t: self._on_thickness_mode_changed("top_thickness", t))
        self.bottom_thickness_combo.currentTextChanged.connect(lambda t: self._on_thickness_mode_changed("bottom_thickness", t))

        self.reset_defaults()

    def _setup_segment_table(self):
        # We find where to put the table. In GIRDER_DETAILS_SCHEMA overview, it's a gap.
        # Actually, let's just create it and add to a known layout if possible, 
        # or find it if UIBuilder created a placeholder.
        pass

    def _on_girder_dropdown_changed(self, text: str):
        girder = self.girder_dropdown.currentData() or str(text).replace("Girder ", "G")
        self._on_girder_changed(girder)

    def _on_cross_view_clicked(self):
        if hasattr(self, "girder_cad_view"):
            self.girder_cad_view.set_view_mode("cross")

    def _on_side_view_clicked(self):
        if hasattr(self, "girder_cad_view"):
            self.girder_cad_view.set_view_mode("side")

    def _on_bounds_clicked(self, key: str):
        bounds = self._dimension_bounds.get(key, {})
        title = f"Edit Bounds: {key.replace('_', ' ').title()}"
        dlg = BoundsDialog(title, bounds, self)
        if dlg.exec():
            res = dlg.result_bounds()
            if res:
                self._dimension_bounds[key] = res
                self._mark_current_member_dirty()

    def _default_dimension_bounds(self) -> dict:
        return {
            "total_depth": {"lower": 200.0, "upper": 2000.0, "increment": 25.0},
            "top_width": {"lower": 100.0, "upper": 1000.0, "increment": 10.0},
            "bottom_width": {"lower": 100.0, "upper": 1000.0, "increment": 10.0},
        }

    def _on_type_changed(self, text: str):
        is_rolled = (text == "Rolled Beam")
        # In schema-driven, we use conditions or manual toggles if complex
        self._refresh_visibility()

    def _refresh_visibility(self):
        is_rolled = (self.type_combo.currentText() == "Rolled Beam")
        # Find which widgets belong to which view
        pass

    def _on_rolled_section_changed(self, *_args):
        pass

    def _on_span_changed(self, text: str):
        self.length_input.setReadOnly(text != "Custom")

    def _on_girder_changed(self, girder: str):
        if self._is_current_member_dirty():
            self._commit_current_member_state()
        self._current_girder = girder
        self._refresh_segment_list(girder)
        self._select_segment_index(0)

    def _is_current_member_dirty(self) -> bool:
        _, mid = self._current_member_key()
        return mid in self._dirty_members

    def _mark_current_member_dirty(self):
        _, mid = self._current_member_key()
        if mid: self._dirty_members.add(mid)

    def _current_member_key(self) -> tuple[str, str]:
        segments = self.segment_chain.get(self._current_girder, [])
        if not segments: return self._current_girder, ""
        idx = max(0, min(self._current_segment_index, len(segments)-1))
        return self._current_girder, segments[idx]["id"]

    def _commit_current_member_state(self):
        girder, mid = self._current_member_key()
        if not mid: return
        state = {
            "inputs": schema_io.collect_values(self, GIRDER_DETAILS_SCHEMA),
            "bounds": copy.deepcopy(self._dimension_bounds)
        }
        self._member_state.setdefault(girder, {})[mid] = state
        self._dirty_members.discard(mid)

    def _refresh_segment_list(self, girder: str):
        # Implementation omitted for brevity in this step, but would populate table
        pass

    def _select_segment_index(self, index: int):
        self._current_segment_index = index
        # Load state for this segment
        girder, mid = self._current_member_key()
        stored = self._member_state.get(girder, {}).get(mid)
        if stored:
            self._suppress_member_state_updates = True
            try:
                schema_io.restore_values(self, GIRDER_DETAILS_SCHEMA, stored.get("inputs", {}))
                self._dimension_bounds = copy.deepcopy(stored.get("bounds", self._default_dimension_bounds()))
            finally:
                self._suppress_member_state_updates = False
        else:
            schema_io.reset_defaults(self, GIRDER_DETAILS_SCHEMA)

    def reset_defaults(self):
        self._member_state.clear()
        self._dirty_members.clear()
        self.segment_chain.clear()
        schema_io.reset_defaults(self, GIRDER_DETAILS_SCHEMA)
        self._dimension_bounds = self._default_dimension_bounds()
        
        self.available_girders = ["G1"]
        self.segment_chain["G1"] = [{"id": "G1M1", "start": 0.0, "end": 30.0}]
        self._refresh_girder_dropdown()
        self._on_girder_changed("G1")

    def collect_data(self) -> dict:
        self._commit_current_member_state()
        data = super().collect_data()
        data.update({
            "available_girders": self.available_girders,
            "segment_chain": self.segment_chain,
            "member_state": self._member_state,
        })
        return data

    def restore_data(self, data: dict):
        if not data: return
        super().restore_data(data)
        self.available_girders = data.get("available_girders", ["G1"])
        self.segment_chain = data.get("segment_chain", {})
        self._member_state = data.get("member_state", {})
        self._refresh_girder_dropdown()
        self._on_girder_changed(self.available_girders[0])

    def _on_thickness_mode_changed(self, field_key: str, text: str):
        if text == "Custom":
            # Open dialog
            pass

    def _wire_dirty_tracking(self):
        from PySide6.QtWidgets import QComboBox, QLineEdit, QCheckBox
        for w in self.findChildren(QComboBox) + self.findChildren(QLineEdit) + self.findChildren(QCheckBox):
            if isinstance(w, QComboBox): w.currentTextChanged.connect(self._mark_current_member_dirty)
            elif isinstance(w, QLineEdit): w.textChanged.connect(self._mark_current_member_dirty)
            elif isinstance(w, QCheckBox): w.toggled.connect(self._mark_current_member_dirty)

    def _on_apply_exterior_clicked(self): pass
    def _on_apply_interior_clicked(self): pass
    def _make_segment_id(self, girder: str, index: int) -> str: return f"{girder}M{index}"

    def _refresh_girder_dropdown(self) -> None:
        combo = getattr(self, "girder_dropdown", None)
        if combo is None:
            return
        current = combo.currentData() or combo.currentText() or self._current_girder
        previous = combo.blockSignals(True)
        try:
            combo.clear()
            for girder in self.available_girders:
                combo.addItem(girder.replace("G", "Girder "), girder)
            index = combo.findData(current)
            if index < 0 and self.available_girders:
                index = combo.findData(self.available_girders[0])
            if index >= 0:
                combo.setCurrentIndex(index)
        finally:
            combo.blockSignals(previous)

    def _ensure_girder_segments(self, girder: str) -> list[dict]:
        segments = self.segment_chain.get(girder)
        if isinstance(segments, list) and segments:
            return segments
        default_length = float(self._default_member_length_m)
        segments = [{"id": f"{girder}M1", "start": 0.0, "end": default_length}]
        self.segment_chain[girder] = segments
        return segments

    def list_all_member_ids(self) -> list[str]:
        member_ids: list[str] = []
        for girder in self.available_girders:
            for segment in self._ensure_girder_segments(girder):
                member_id = str(segment.get("id") or "").strip()
                if member_id:
                    member_ids.append(member_id)
        return member_ids

    def _member_inputs(self, member_id: str) -> dict:
        current_girder, current_member = self._current_member_key()
        if member_id == current_member:
            return schema_io.collect_values(self, GIRDER_DETAILS_SCHEMA)

        girder = str(member_id).split("M", 1)[0]
        state = self._member_state.get(girder, {}).get(member_id, {})
        inputs = state.get("inputs", {}) if isinstance(state, dict) else {}
        return dict(inputs) if isinstance(inputs, dict) else {}

    @staticmethod
    def _as_float(value, default=0.0) -> float:
        try:
            text = str(value).strip()
            return float(text) if text else float(default)
        except Exception:
            return float(default)

    def get_member_section_dimensions(self, member_id: str) -> dict:
        inputs = self._member_inputs(member_id)
        top_width = self._as_float(inputs.get("top_width_input"), 0.0)
        bottom_width = self._as_float(inputs.get("bottom_width_input"), 0.0)
        web_thickness = self._as_float(inputs.get("web_thickness_value_input"), 0.0)
        total_depth = self._as_float(inputs.get("total_depth_input"), 0.0)
        return {
            "top_flange_width_mm": top_width,
            "bottom_flange_width_mm": bottom_width,
            "web_thickness_mm": web_thickness,
            "total_depth_mm": total_depth,
        }

    def is_member_optimized(self, member_id: str) -> bool:
        inputs = self._member_inputs(member_id)
        return str(inputs.get("design_combo", self.design_combo.currentText() if hasattr(self, "design_combo") else "")).strip() == "Optimized"

    def _get_total_span(self) -> float:
        segments = self._ensure_girder_segments(self._current_girder or self.available_girders[0])
        if not segments:
            return float(self._default_member_length_m)
        start = self._as_float(segments[0].get("start"), 0.0)
        end = self._as_float(segments[-1].get("end"), self._default_member_length_m)
        return max(0.0, end - start)

    def export_dependency_state(self) -> dict:
        self._commit_current_member_state()
        member_ids = self.list_all_member_ids()
        return {
            "available_girders": list(self.available_girders),
            "segment_chain": copy.deepcopy(self.segment_chain),
            "member_ids": member_ids,
            "optimized_members": {member_id for member_id in member_ids if self.is_member_optimized(member_id)},
            "section_dimensions_by_member": {
                member_id: self.get_member_section_dimensions(member_id)
                for member_id in member_ids
            },
            "total_span_m": self._get_total_span(),
        }

    def set_girder_count(self, count):
        try:
            requested = max(1, min(int(count), self._max_girder_count))
        except Exception:
            requested = 1
        self.available_girders = [f"G{i}" for i in range(1, requested + 1)]
        for girder in list(self.segment_chain):
            if girder not in self.available_girders:
                self.segment_chain.pop(girder, None)
        for girder in self.available_girders:
            self._ensure_girder_segments(girder)
        self._current_girder = self.available_girders[0]
        self._refresh_girder_dropdown()
        self._on_girder_changed(self._current_girder)

    def has_unsaved_changes(self) -> bool:
        return bool(self._dirty_members)
