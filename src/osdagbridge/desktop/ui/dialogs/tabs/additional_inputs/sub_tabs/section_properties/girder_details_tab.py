"""Girder Details tab.

This tab handles the master configuration of girders and their segments.
It manages geometry (span, segments), design mode, and section properties.
"""

from __future__ import annotations

import copy
import math
import re
from typing import Dict, List, Optional, Set, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QStyledItemDelegate,
)
from PySide6.QtGui import QDoubleValidator

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import GIRDER_DETAILS_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab
from osdagbridge.desktop.ui.widgets.section_viewer import SectionCatalog
from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.sub_tabs.section_properties.girder_helpers import BoundsDialog, ThicknessSelectionDialog


class _ReadOnlyCellDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index): return None

class _EndDistanceDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QDoubleValidator(0.0, 1000.0, 3, editor))
        return editor


ROLLED_ONLY_BINDS = ("is_section_combo",)
WELDED_ONLY_BINDS = (
    "design_combo",
    "symmetry_combo",
    "total_depth_widget",
    "top_width_widget",
    "top_thickness_combo",
    "top_thickness_value_input",
    "bottom_width_widget",
    "bottom_thickness_combo",
    "bottom_thickness_value_input",
    "support_type_combo",
    "support_width_input",
    "web_thickness_combo",
    "web_thickness_value_input",
    "web_type_combo",
)


class GirderDetailsTab(SchemaTab):
    """Tab for Girder Details - Geometry and Section Properties."""
    schema = GIRDER_DETAILS_SCHEMA
    dependency_state_changed = Signal(dict)

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

        self._wire_dirty_tracking()
        self.reset_defaults()

    def _setup_segment_table(self):
        headers = GIRDER_DETAILS_SCHEMA.get("segment_manager", {}).get(
            "table_headers",
            ["Member ID", "Start (m)", "End (m)", "Length (m)", "Action"],
        )
        table = QTableWidget(self)
        table.setObjectName("girder_segment_table")
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        if table.columnCount() > 4:
            table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table.setItemDelegateForColumn(0, _ReadOnlyCellDelegate(table))
        table.setItemDelegateForColumn(1, _ReadOnlyCellDelegate(table))
        table.setItemDelegateForColumn(2, _ReadOnlyCellDelegate(table))
        table.setItemDelegateForColumn(3, _ReadOnlyCellDelegate(table))
        table.itemSelectionChanged.connect(self._on_segment_selection_changed)
        self.segment_table = table

        page_layout = getattr(self.builder, "page_layout", None)
        if page_layout is not None:
            page_layout.addWidget(table)

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
                self._sync_cad_view()

    def _default_dimension_bounds(self) -> dict:
        return {
            "total_depth": {"lower": 200.0, "upper": 2000.0, "increment": 25.0},
            "top_width": {"lower": 100.0, "upper": 1000.0, "increment": 10.0},
            "bottom_width": {"lower": 100.0, "upper": 1000.0, "increment": 10.0},
        }

    def _on_type_changed(self, text: str):
        self._refresh_visibility()
        self._mark_current_member_dirty()
        self._sync_cad_view()

    def _refresh_visibility(self):
        is_rolled = (self.type_combo.currentText() == "Rolled Beam")
        self._set_widgets_active(ROLLED_ONLY_BINDS, is_rolled)
        self._set_widgets_active(WELDED_ONLY_BINDS, not is_rolled)

    def _on_rolled_section_changed(self, *_args):
        self._mark_current_member_dirty()
        self._sync_cad_view()

    def _on_span_changed(self, text: str):
        self.length_input.setReadOnly(text != "Custom")

    def _on_girder_changed(self, girder: str):
        if self._is_current_member_dirty():
            self.commit_active_state()
        self._current_girder = girder
        self._refresh_segment_list(girder)
        self._select_segment_index(0)
        self._sync_length_field()

    def _is_current_member_dirty(self) -> bool:
        _, mid = self._current_member_key()
        return mid in self._dirty_members

    def _mark_current_member_dirty(self):
        if self._suppress_member_state_updates:
            return
        _, mid = self._current_member_key()
        if mid: self._dirty_members.add(mid)

    def _current_member_key(self) -> tuple[str, str]:
        segments = self.segment_chain.get(self._current_girder, [])
        if not segments:
            return self._current_girder, ""
        idx = max(0, min(self._current_segment_index, len(segments) - 1))
        return self._current_girder, segments[idx]["id"]

    def _current_member_id(self) -> str:
        return self._current_member_key()[1]

    def _current_segment(self) -> Optional[dict]:
        segments = self.segment_chain.get(self._current_girder, [])
        if not segments:
            return None
        index = max(0, min(self._current_segment_index, len(segments) - 1))
        return segments[index]

    def _member_state_for(self, girder: str, member_id: str) -> dict:
        state = self._member_state.get(girder, {}).get(member_id, {})
        return state if isinstance(state, dict) else {}

    def _member_input_values(self, member_id: str) -> dict:
        current_girder, current_member = self._current_member_key()
        if member_id == current_member:
            return schema_io.collect_values(self, GIRDER_DETAILS_SCHEMA)

        girder = str(member_id).split("M", 1)[0]
        state = self._member_state_for(girder, member_id)
        inputs = state.get("inputs", {})
        return dict(inputs) if isinstance(inputs, dict) else {}

    def _commit_current_member_state(self):
        girder, member_id = self._current_member_key()
        if not member_id:
            return
        self._member_state.setdefault(girder, {})[member_id] = self._current_member_state_snapshot()
        self._dirty_members.discard(member_id)

    def commit_active_state(self, *, emit_signal: bool = True) -> dict:
        self._commit_current_member_state()
        state = self._dependency_state_snapshot()
        if emit_signal:
            self.dependency_state_changed.emit(copy.deepcopy(state))
        return state

    def _refresh_segment_list(self, girder: str):
        table = getattr(self, "segment_table", None)
        if table is None:
            return
        segments = self._ensure_girder_segments(girder)
        previous = table.blockSignals(True)
        try:
            table.setRowCount(len(segments))
            for row, segment in enumerate(segments):
                start = self._as_float(segment.get("start"), 0.0)
                end = self._as_float(segment.get("end"), self._default_member_length_m)
                length = max(0.0, end - start)
                values = (
                    str(segment.get("id", self._make_segment_id(girder, row + 1))),
                    f"{start:.2f}",
                    f"{end:.2f}",
                    f"{length:.2f}",
                    "Configured",
                )
                for column, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    table.setItem(row, column, item)
            if segments:
                row = max(0, min(self._current_segment_index, len(segments) - 1))
                table.selectRow(row)
        finally:
            table.blockSignals(previous)
        self._sync_cad_view()

    def _select_segment_index(self, index: int):
        self._current_segment_index = index
        girder, member_id = self._current_member_key()
        self._restore_member_state(self._member_state_for(girder, member_id))
        self._sync_length_field()
        self._sync_cad_view()

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
        self._sync_cad_view()
        self.commit_active_state()

    def collect_data(self) -> dict:
        self.commit_active_state(emit_signal=False)
        data = super().collect_data()
        data.update({
            "available_girders": list(self.available_girders),
            "segment_chain": copy.deepcopy(self.segment_chain),
            "member_state": copy.deepcopy(self._member_state),
        })
        return data

    def restore_data(self, data: dict):
        if not data: return
        self._suppress_member_state_updates = True
        try:
            super().restore_data(data)
        finally:
            self._suppress_member_state_updates = False
        self.available_girders = list(data.get("available_girders", ["G1"]) or ["G1"])
        self.segment_chain = copy.deepcopy(data.get("segment_chain", {}) or {})
        self._member_state = copy.deepcopy(data.get("member_state", {}) or {})
        self._dirty_members.clear()
        target_girder = self.available_girders[0]
        self._current_girder = target_girder
        self._refresh_girder_dropdown()
        combo = getattr(self, "girder_dropdown", None)
        if combo is not None:
            blocked = combo.blockSignals(True)
            try:
                index = combo.findData(target_girder)
                if index >= 0:
                    combo.setCurrentIndex(index)
            finally:
                combo.blockSignals(blocked)
        self._on_girder_changed(target_girder)
        self._sync_cad_view()
        self.commit_active_state()

    def _on_thickness_mode_changed(self, field_key: str, text: str):
        if text == "Custom":
            bind_map = {
                "web_thickness": "web_thickness_value_input",
                "top_thickness": "top_thickness_value_input",
                "bottom_thickness": "bottom_thickness_value_input",
            }
            value_widget = getattr(self, bind_map.get(field_key, ""), None)
            current = self._as_float(value_widget.text() if value_widget is not None else "", 0.0)
            dialog = ThicknessSelectionDialog(
                f"Select {field_key.replace('_', ' ').title()}",
                list(self._thickness_values),
                current,
                self,
            )
            if dialog.exec():
                selected = dialog.selected_value()
                if selected is not None and value_widget is not None:
                    value_widget.setText(f"{selected:.1f}".rstrip("0").rstrip("."))
        self._mark_current_member_dirty()
        self._sync_cad_view()

    def _wire_dirty_tracking(self):
        from PySide6.QtWidgets import QComboBox, QLineEdit, QCheckBox
        for w in self.findChildren(QComboBox) + self.findChildren(QLineEdit) + self.findChildren(QCheckBox):
            if isinstance(w, QComboBox):
                w.currentTextChanged.connect(self._mark_current_member_dirty)
                w.currentTextChanged.connect(lambda *_args: self._sync_cad_view())
            elif isinstance(w, QLineEdit):
                w.textChanged.connect(self._mark_current_member_dirty)
                w.textChanged.connect(lambda *_args: self._sync_cad_view())
            elif isinstance(w, QCheckBox):
                w.toggled.connect(self._mark_current_member_dirty)
                w.toggled.connect(lambda *_args: self._sync_cad_view())

    def _on_apply_exterior_clicked(self):
        self._apply_current_state_to_girders(exterior_only=True)

    def _on_apply_interior_clicked(self):
        self._apply_current_state_to_girders(exterior_only=False)
    def _make_segment_id(self, girder: str, index: int) -> str: return f"{girder}M{index}"

    def _on_segment_selection_changed(self) -> None:
        table = getattr(self, "segment_table", None)
        if table is None:
            return
        row = table.currentRow()
        if row >= 0:
            if row != self._current_segment_index and self._is_current_member_dirty():
                self.commit_active_state()
            self._select_segment_index(row)

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

    def _sync_length_field(self) -> None:
        widget = getattr(self, "length_input", None)
        if widget is None:
            return
        if self.widget_current_text("span_combo") == "Custom":
            widget.setReadOnly(False)
            return
        widget.setReadOnly(True)
        widget.setText(f"{self._get_total_span():.2f}".rstrip("0").rstrip("."))

    def _current_member_state_snapshot(self) -> dict:
        return {
            "inputs": self._member_input_values(self._current_member_id()),
            "bounds": copy.deepcopy(self._dimension_bounds),
        }

    def _restore_member_state(self, stored: Optional[dict]) -> None:
        self._suppress_member_state_updates = True
        widgets = self.findChildren(QComboBox) + self.findChildren(QLineEdit)
        blocked = [widget.blockSignals(True) for widget in widgets]
        try:
            if stored:
                schema_io.restore_values(self, GIRDER_DETAILS_SCHEMA, stored.get("inputs", {}))
                self._dimension_bounds = copy.deepcopy(stored.get("bounds", self._default_dimension_bounds()))
            else:
                schema_io.reset_defaults(self, GIRDER_DETAILS_SCHEMA)
                self._dimension_bounds = self._default_dimension_bounds()
        finally:
            for widget, previous in zip(widgets, blocked):
                widget.blockSignals(previous)
            self._suppress_member_state_updates = False
        self._refresh_visibility()

    def _set_widgets_active(self, bind_names, enabled: bool) -> None:
        for name in bind_names:
            widget = getattr(self, name, None)
            if widget is not None:
                widget.setVisible(enabled)
                widget.setEnabled(enabled)

    def _current_member_dimensions(self) -> dict:
        return {
            "top_flange_width_mm": self._as_float(self.widget_text("top_width_input"), 0.0),
            "bottom_flange_width_mm": self._as_float(self.widget_text("bottom_width_input"), 0.0),
            "web_thickness_mm": self._as_float(self.widget_text("web_thickness_value_input"), 0.0),
            "total_depth_mm": self._as_float(self.widget_text("total_depth_input"), 0.0),
        }

    def _sync_cad_view(self) -> None:
        if getattr(self, "_syncing_cad_view", False):
            return
        cad = getattr(self, "girder_cad_view", None)
        if cad is None:
            return
        self._syncing_cad_view = True
        try:
            dims = self._current_member_dimensions()
            flange_thickness = max(
                10.0,
                self._as_float(self.widget_text("top_thickness_value_input"), 0.0) or 0.0,
                self._as_float(self.widget_text("bottom_thickness_value_input"), 0.0) or 0.0,
                dims.get("web_thickness_mm") or 15.0,
            )
            cad.set_segments(self._ensure_girder_segments(self._current_girder))
            cad.set_selected_member(self._current_member_id())
            cad._flange_thickness = flange_thickness
            cad.update()
        finally:
            self._syncing_cad_view = False

    def list_available_girders(self) -> list[str]:
        return list(self.available_girders)

    def list_all_member_ids(self) -> list[str]:
        member_ids: list[str] = []
        for girder in self.available_girders:
            for segment in self._ensure_girder_segments(girder):
                member_id = str(segment.get("id") or "").strip()
                if member_id:
                    member_ids.append(member_id)
        return member_ids

    def _member_inputs(self, member_id: str) -> dict:
        return self._member_input_values(member_id)

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

    def get_total_span(self) -> float:
        return self._get_total_span()

    def segments_for_girder(self, girder: str) -> list[dict]:
        return copy.deepcopy(self._ensure_girder_segments(girder))

    def _get_total_span(self) -> float:
        current_girder = self._current_girder or self.available_girders[0]
        segments = self._ensure_girder_segments(current_girder)
        if not segments:
            return float(self._default_member_length_m)
        start = self._as_float(segments[0].get("start"), 0.0)
        end = self._as_float(segments[-1].get("end"), self._default_member_length_m)
        return max(0.0, end - start)

    def _dependency_state_snapshot(self) -> dict:
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

    def export_dependency_state(self) -> dict:
        return self.commit_active_state(emit_signal=False)

    def set_design_mode(self, mode_str: str) -> None:
        mode = "Custom" if str(mode_str or "").strip().lower() in {"custom", "customized"} else "Optimized"
        combo = getattr(self, "design_combo", None)
        if isinstance(combo, QComboBox):
            combo.setCurrentText(mode)
        self.commit_active_state()

    def set_girder_count(self, count):
        self.commit_active_state(emit_signal=False)
        try:
            requested = max(1, min(int(count), self._max_girder_count))
        except Exception:
            requested = 1
        next_girders = [f"G{i}" for i in range(1, requested + 1)]
        for girder in list(self.segment_chain):
            if girder not in next_girders:
                self.segment_chain.pop(girder, None)
                self._member_state.pop(girder, None)
        self.available_girders = next_girders
        valid_member_ids = {
            str(segment.get("id") or "")
            for girder in self.available_girders
            for segment in self._ensure_girder_segments(girder)
        }
        self._dirty_members.intersection_update({member_id for member_id in valid_member_ids if member_id})
        for girder in self.available_girders:
            self._ensure_girder_segments(girder)
        self._current_girder = self.available_girders[0]
        self._refresh_girder_dropdown()
        self._on_girder_changed(self._current_girder)
        self.commit_active_state()

    def has_unsaved_changes(self) -> bool:
        return bool(self._dirty_members)

    def _apply_current_state_to_girders(self, *, exterior_only: bool) -> None:
        self.commit_active_state(emit_signal=False)
        source_girder, source_member = self._current_member_key()
        source_state = copy.deepcopy(self._member_state_for(source_girder, source_member))
        if not source_state:
            return

        if exterior_only:
            targets = {self.available_girders[0], self.available_girders[-1]}
        else:
            targets = set(self.available_girders[1:-1]) or set(self.available_girders)

        for girder in targets:
            for segment in self._ensure_girder_segments(girder):
                member_id = str(segment.get("id") or "")
                if not member_id or member_id == source_member:
                    continue
                self._member_state.setdefault(girder, {})[member_id] = copy.deepcopy(source_state)

        self._refresh_segment_list(self._current_girder)
        self.commit_active_state()
