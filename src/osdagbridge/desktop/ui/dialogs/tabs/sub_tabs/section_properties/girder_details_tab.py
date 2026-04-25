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
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder
from osdagbridge.desktop.ui.widgets.section_viewer import SectionCatalog
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.girder_helpers import BoundsDialog, ThicknessSelectionDialog


class _ReadOnlyCellDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index): return None

class _EndDistanceDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QDoubleValidator(0.0, 1000.0, 3, editor))
        return editor

class GirderDetailsTab(QWidget):
    """Tab for Girder Details - Geometry and Section Properties."""

    def __init__(self, parent=None):
        super().__init__(parent)
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

        # Build UI from schema
        UIBuilder(owner=self, schema=GIRDER_DETAILS_SCHEMA).build_tab(self)
        
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
        
        self._on_girder_changed("G1")

    def collect_data(self) -> dict:
        self._commit_current_member_state()
        return {
            "available_girders": self.available_girders,
            "segment_chain": self.segment_chain,
            "member_state": self._member_state,
        }

    def restore_data(self, data: dict):
        if not data: return
        self.available_girders = data.get("available_girders", ["G1"])
        self.segment_chain = data.get("segment_chain", {})
        self._member_state = data.get("member_state", {})
        self._on_girder_changed(self.available_girders[0])

    def _on_thickness_mode_changed(self, field_key: str, text: str):
        if text == "Custom":
            # Open dialog
            pass

    def _wire_dirty_tracking(self):
        from PySide6.QtWidgets import QComboBox, QLineEdit, QCheckBox
        for w in self.findChildren((QComboBox, QLineEdit, QCheckBox)):
            if isinstance(w, QComboBox): w.currentTextChanged.connect(self._mark_current_member_dirty)
            elif isinstance(w, QLineEdit): w.textChanged.connect(self._mark_current_member_dirty)
            elif isinstance(w, QCheckBox): w.toggled.connect(self._mark_current_member_dirty)

    def _on_apply_exterior_clicked(self): pass
    def _on_apply_interior_clicked(self): pass
    def _make_segment_id(self, girder: str, index: int) -> str: return f"{girder}M{index}"
