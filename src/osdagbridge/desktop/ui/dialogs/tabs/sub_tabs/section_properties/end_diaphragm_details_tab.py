"""End diaphragm section-properties UI.

This tab supports Cross Bracing, Rolled Beam and Welded Beam views.
Rolled/Welded views render a live section preview and auto-fill section
properties, matching the behavior used in the Girder tab.
"""

import math
import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar, QLabel, QLineEdit,
    QComboBox, QGroupBox, QFormLayout, QPushButton, QScrollArea,
    QCheckBox, QMessageBox, QSizePolicy, QSpacerItem, QStackedWidget,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QDialog, QSizePolicy, QSizeGrip
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QDoubleValidator, QIntValidator

from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.utils.rolled_section_preview import RolledSectionPreview
from osdagbridge.desktop.ui.widgets.section_viewer import SectionCatalog, SectionPreviewWidget
from osdagbridge.desktop.ui.widgets.placeholder_section_preview import PlaceholderSectionPreviewWidget
from .cross_bracing_details_tab import BracingLayoutCadWidget
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import END_DIAPHRAGM_DETAILS_SCHEMA

# Reuse the same rolled section catalog that backs the Girder tab.
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.girder_details_tab import (  # noqa: E501
    _BoundsDialog,
    _ThicknessSelectionDialog,
    girder_properties,
)

from osdagbridge.core.utils.common import SAIL_APPROVED_THICKNESS_VALUES


def _choice_value(options: list[str], preferred: str, fallback_index: int = 0) -> str:
    """Resolve canonical labels by value first, then safe positional fallback."""
    values = [str(value) for value in (options or [])]
    if preferred in values:
        return preferred
    if 0 <= fallback_index < len(values):
        return values[fallback_index]
    return preferred


VIEW_CROSS_BRACING = _choice_value(list(VALUES_END_DIAPHRAGM_TYPE), "Cross Bracing", 0)
VIEW_ROLLED_BEAM = _choice_value(list(VALUES_END_DIAPHRAGM_TYPE), "Rolled Beam", 1)
VIEW_WELDED_BEAM = _choice_value(list(VALUES_END_DIAPHRAGM_TYPE), "Welded Beam", 2)
DESIGN_OPTIMIZED = _choice_value(list(VALUES_GIRDER_DESIGN_MODE), "Optimized", 0)
DESIGN_CUSTOM = _choice_value(list(VALUES_GIRDER_DESIGN_MODE), "Custom", 1)

class EndDiaphragmDetailsTab(QWidget):
    """Tab for End Diaphragm Details with type-specific layouts"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._girder_details_tab = None
        self._global_design_mode = DESIGN_OPTIMIZED
        self._dimension_bounds = {
            "total_depth": {"lower": 200.0, "upper": 2000.0, "increment": 25.0},
            "top_width": {"lower": 100.0, "upper": 1000.0, "increment": 10.0},
            "bottom_width": {"lower": 100.0, "upper": 1000.0, "increment": 10.0},
        }
        self._select_girders_combos = []
        self._member_id_combos = []
        # Member ID is software-generated (E{pair}M1 / E{pair}M2).
        # Show both IDs as a read-only display; inputs apply to both ends.
        self._member_id_display_by_view: dict[str, QLineEdit] = {}

        # Keep all combo boxes strictly uniform in width.
        self._combo_width = 190
        self._label_col_width = 260

        # Persist UI state per (view_type, girder-pair, member-id).
        # Also sync selection (girder/member index) across all three views.
        self._selection_by_view: dict[str, tuple[QComboBox, QComboBox]] = {}
        self._state_by_view_member_key: dict[str, dict] = {}
        self._active_key_by_view: dict[str, str] = {}
        self._block_selection_sync = False
        # Cross bracing uses angle/channel section previews backed by the Osdag DB.
        self._cross_catalog = SectionCatalog()
        self._cross_previews = {}
        self._cross_preview_boxes = {}
        self._updating_cross_chord_rules = False
        self.cross_right_column = None
        self.cross_design_combo = None
        self.cross_bracing_section_type_combo = None
        self.cross_bracing_section_combo = None
        self.cross_top_chord_checkbox = None
        self.cross_top_chord_type_combo = None
        self.cross_top_chord_size_combo = None
        self.cross_bottom_chord_checkbox = None
        self.cross_bottom_chord_type_combo = None
        self.cross_bottom_chord_size_combo = None
        self.cross_bracing_type_combo = None
        self.cross_bracing_layout_widget = None

        self._rolled_property_inputs = {}
        self._welded_property_inputs = {}
        self._rolled_preview = None
        self._welded_preview = None
        self._rolled_caption = None
        self._welded_caption = None
        self._welded_right_column = None
        self._welded_view_layout = None

        self.rolled_design_combo = None
        self.welded_design_combo = None
        self._rolled_inputs = []
        self._welded_inputs = []
        self._suppress_welded_thickness_popup = False
        self.init_ui()

    def bind_girder_details_tab(self, girder_details_tab) -> None:
        """Bind to Girder Details so Select Girders reflects user inputs."""
        self._girder_details_tab = girder_details_tab
        self.refresh_girder_options()

    def showEvent(self, event):  # noqa: N802 (Qt naming)
        super().showEvent(event)
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
        """Populate all view selection combos based on Girder Details."""
        # Save current states before rebuilding options.
        try:
            self._store_all_view_states()
        except Exception:
            pass

        pairs = self._girder_pairs()

        for combo in list(self._select_girders_combos):
            if combo is None:
                continue
            prev = combo.currentText().strip()
            block = combo.blockSignals(True)
            try:
                combo.clear()
                combo.addItems(pairs)
                combo.setCurrentText(prev if prev in pairs else pairs[0])
            finally:
                combo.blockSignals(block)

        # Member IDs are generated per girder-pair selection.
        # End diaphragm uses 2 members per pair: E{pair}M1, E{pair}M2.
        for view_key, (girders_combo, member_combo) in (self._selection_by_view or {}).items():
            if girders_combo is None or member_combo is None:
                continue
            self._rebuild_member_ids_for_view(view_key, previous_member=(member_combo.currentText() or "").strip())
            try:
                self._refresh_member_id_display(view_key)
            except Exception:
                pass

        # After refresh, ensure state is restored for current selection.
        self._restore_all_views_for_current_selection()

    @staticmethod
    def _member_number(text: str) -> int | None:
        raw = (text or "").strip().upper().replace(" ", "")
        if not raw:
            return None
        if "M" in raw:
            try:
                _p, m = raw.split("M", 1)
                return int("".join(ch for ch in m if ch.isdigit()) or 0) or None
            except Exception:
                return None
        if "-" in raw:
            try:
                _p, m = raw.split("-", 1)
                return int("".join(ch for ch in m if ch.isdigit()) or 0) or None
            except Exception:
                return None
        return None

    def _pair_index_for_combo(self, girders_combo: QComboBox | None) -> int:
        return max(0, int(girders_combo.currentIndex() if girders_combo is not None else 0)) + 1

    def _member_ids_for_pair(self, pair_index: int) -> list[str]:
        return [f"E{pair_index}M1", f"E{pair_index}M2"]

    def _refresh_member_id_display(self, view_key: str) -> None:
        combos = self._selection_by_view.get(view_key)
        display = self._member_id_display_by_view.get(view_key)
        if not combos or display is None:
            return
        girders_combo, _member_combo = combos
        pair_index = self._pair_index_for_combo(girders_combo)
        members = self._member_ids_for_pair(pair_index)
        text = " / ".join(members)
        prev = display.blockSignals(True)
        try:
            display.setText(text)
        finally:
            display.blockSignals(prev)

        if view_key == VIEW_CROSS_BRACING:
            try:
                self._on_cross_bracing_layout_changed()
            except Exception:
                pass

    def _rebuild_member_ids_for_view(self, view_key: str, previous_member: str = "") -> None:
        combos = self._selection_by_view.get(view_key)
        if not combos:
            return
        girders_combo, member_combo = combos
        if member_combo is None:
            return
        pair_index = self._pair_index_for_combo(girders_combo)
        items = self._member_ids_for_pair(pair_index)

        block = member_combo.blockSignals(True)
        try:
            member_combo.clear()
            member_combo.addItems(items)
            desired = (previous_member or "").strip().upper()
            if desired and desired in [i.upper() for i in items]:
                member_combo.setCurrentText(desired)
            else:
                member_combo.setCurrentText(f"E{pair_index}M1")
                member_combo.setCurrentIndex(0)
        finally:
            member_combo.blockSignals(block)

        try:
            self._refresh_member_id_display(view_key)
        except Exception:
            pass

    def _selection_key(self, view_key: str) -> str:
        combos = self._selection_by_view.get(view_key)
        if not combos:
            return ""
        girders_combo, member_combo = combos
        pair = (girders_combo.currentText() or "").strip()
        member = (member_combo.currentText() or "").strip()
        return f"{view_key}::{pair}::{member}".strip(":")

    def _default_state_for_view(self, view_key: str) -> dict:
        key = (view_key or "").strip()
        if key == VIEW_CROSS_BRACING:
            angles = []
            try:
                angles = list(self._cross_catalog.list_angles() or [])
            except Exception:
                angles = []
            first_angle = angles[0] if angles else ""
            state = self._schema_default_state_for_view(VIEW_CROSS_BRACING)

            state.update({
                "bracing_section_data": first_angle,
                "bracing_section_text": "",
                "top_chord_data": first_angle,
                "top_chord_text": "",
                "bottom_chord_data": first_angle,
                "bottom_chord_text": "",
            })
            return state
        if key == VIEW_ROLLED_BEAM:
            state = self._schema_default_state_for_view(VIEW_ROLLED_BEAM)
            first = ""
            if self.rolled_is_section_combo is not None and self.rolled_is_section_combo.count() > 0:
                first = self.rolled_is_section_combo.itemText(0)
            state["is_section"] = state.get("is_section") or first
            return state
        if key == VIEW_WELDED_BEAM:
            state = self._schema_default_state_for_view(VIEW_WELDED_BEAM)
            state.update({
                "welded_values": ["" for _ in (self._welded_inputs or [])],
                "total_depth_bounds": dict(self._dimension_bounds.get("total_depth") or {}),
                "top_width_bounds": dict(self._dimension_bounds.get("top_width") or {}),
                "bottom_width_bounds": dict(self._dimension_bounds.get("bottom_width") or {}),
            })
            return state
        return {"design": self._global_design_mode}

    def _snapshot_view_state(self, view_key: str) -> dict:
        key = (view_key or "").strip()
        if key == VIEW_CROSS_BRACING:
            state = self._snapshot_schema_state_for_view(VIEW_CROSS_BRACING)

            state.update({
                "bracing_section_data": self.cross_bracing_section_combo.currentData() if self.cross_bracing_section_combo is not None else None,
                "bracing_section_text": self.cross_bracing_section_combo.currentText() if self.cross_bracing_section_combo is not None else "",
                "top_chord_data": self.cross_top_chord_size_combo.currentData() if self.cross_top_chord_size_combo is not None else None,
                "top_chord_text": self.cross_top_chord_size_combo.currentText() if self.cross_top_chord_size_combo is not None else "",
                "bottom_chord_data": self.cross_bottom_chord_size_combo.currentData() if self.cross_bottom_chord_size_combo is not None else None,
                "bottom_chord_text": self.cross_bottom_chord_size_combo.currentText() if self.cross_bottom_chord_size_combo is not None else "",
            })
            return state
        if key == VIEW_ROLLED_BEAM:
            return self._snapshot_schema_state_for_view(VIEW_ROLLED_BEAM)
        if key == VIEW_WELDED_BEAM:
            state = self._snapshot_schema_state_for_view(VIEW_WELDED_BEAM)
            values = []
            for widget in (self._welded_inputs or []):
                if isinstance(widget, QComboBox):
                    values.append(widget.currentText())
                elif isinstance(widget, QLineEdit):
                    values.append(widget.text())
                else:
                    values.append("")
            state.update({
                "welded_values": values,
                "total_depth_bounds": dict(self._dimension_bounds.get("total_depth") or {}),
                "top_width_bounds": dict(self._dimension_bounds.get("top_width") or {}),
                "bottom_width_bounds": dict(self._dimension_bounds.get("bottom_width") or {}),
            })
            return state
        return {"design": ""}

    def _set_combo_to_data_or_text(self, combo: QComboBox, desired_data, desired_text: str) -> None:
        if combo is None:
            return
        if desired_data is not None:
            idx = combo.findData(desired_data)
            if idx >= 0:
                combo.setCurrentIndex(idx)
                return
        if desired_text:
            idx = combo.findText(desired_text)
            if idx >= 0:
                combo.setCurrentIndex(idx)

    @staticmethod
    def _is_custom_design_label(label: str | None) -> bool:
        text = str(label or "").strip().lower()
        return text in {DESIGN_CUSTOM.lower(), "customized"}

    def _normalize_bracing_type(self, desired: str) -> str:
        text = str(desired or "").strip()
        if text in {"Diagonal", "Horizontal"}:
            # Backward compatibility for older payload values.
            return "X-Bracing"
        return text

    def _apply_cross_bracing_view_state(self, state: dict) -> None:
        self._apply_schema_state_for_view(
            VIEW_CROSS_BRACING,
            state,
            skip_ids={"bracing_section", "top_chord_size", "bottom_chord_size", "bracing_type"},
        )
        if self.cross_bracing_type_combo is not None:
            desired = self._normalize_bracing_type(state.get("bracing_type") or "")
            if desired and self.cross_bracing_type_combo.findText(desired) >= 0:
                self.cross_bracing_type_combo.setCurrentText(desired)

        if self.cross_bracing_section_type_combo is not None:
            self.cross_bracing_section_type_combo.setCurrentText(
                state.get("bracing_section_type")
                or self._end_schema_default(VIEW_CROSS_BRACING, "bracing_section_type", self.cross_bracing_section_type_combo.currentText())
            )
            self._cross_update_designations_for(self.cross_bracing_section_combo, self.cross_bracing_section_type_combo.currentText())
            self._set_combo_to_data_or_text(
                self.cross_bracing_section_combo,
                state.get("bracing_section_data"),
                state.get("bracing_section_text") or "",
            )

        if self.cross_top_chord_type_combo is not None:
            self.cross_top_chord_type_combo.setCurrentText(state.get("top_chord_type") or self.cross_top_chord_type_combo.currentText())
            self._cross_update_designations_for(self.cross_top_chord_size_combo, self.cross_top_chord_type_combo.currentText())
            self._set_combo_to_data_or_text(
                self.cross_top_chord_size_combo,
                state.get("top_chord_data"),
                state.get("top_chord_text") or "",
            )

        if self.cross_bottom_chord_type_combo is not None:
            self.cross_bottom_chord_type_combo.setCurrentText(state.get("bottom_chord_type") or self.cross_bottom_chord_type_combo.currentText())
            self._cross_update_designations_for(self.cross_bottom_chord_size_combo, self.cross_bottom_chord_type_combo.currentText())
            self._set_combo_to_data_or_text(
                self.cross_bottom_chord_size_combo,
                state.get("bottom_chord_data"),
                state.get("bottom_chord_text") or "",
            )

        self._on_cross_design_changed(self._global_design_mode)
        self._on_cross_bracing_layout_changed()
        self._update_cross_previews()

    def _apply_rolled_view_state(self, state: dict) -> None:
        self._apply_schema_state_for_view(VIEW_ROLLED_BEAM, state)
        if self.rolled_is_section_combo is not None:
            desired = state.get("is_section") or ""
            if desired:
                self.rolled_is_section_combo.setCurrentText(desired)
            elif self.rolled_is_section_combo.count() > 0:
                self.rolled_is_section_combo.setCurrentIndex(0)
        self._on_rolled_design_changed(self._global_design_mode)
        self._update_rolled_preview_and_props()

    def _apply_welded_view_state(self, state: dict) -> None:
        self._suppress_welded_thickness_popup = True
        try:
            self._apply_schema_state_for_view(VIEW_WELDED_BEAM, state)

            total_depth_bounds = state.get("total_depth_bounds")
            if isinstance(total_depth_bounds, dict):
                self._dimension_bounds["total_depth"] = {
                    "lower": float(total_depth_bounds.get("lower", 200.0)),
                    "upper": float(total_depth_bounds.get("upper", 2000.0)),
                    "increment": float(total_depth_bounds.get("increment", 25.0)),
                }

            top_width_bounds = state.get("top_width_bounds")
            if isinstance(top_width_bounds, dict):
                self._dimension_bounds["top_width"] = {
                    "lower": float(top_width_bounds.get("lower", 100.0)),
                    "upper": float(top_width_bounds.get("upper", 1000.0)),
                    "increment": float(top_width_bounds.get("increment", 10.0)),
                }

            bottom_width_bounds = state.get("bottom_width_bounds")
            if isinstance(bottom_width_bounds, dict):
                self._dimension_bounds["bottom_width"] = {
                    "lower": float(bottom_width_bounds.get("lower", 100.0)),
                    "upper": float(bottom_width_bounds.get("upper", 1000.0)),
                    "increment": float(bottom_width_bounds.get("increment", 10.0)),
                }

            self._refresh_bounds_tooltips()
            values = list(state.get("welded_values") or [])
            for i, widget in enumerate(self._welded_inputs or []):
                val = values[i] if i < len(values) else ""
                if isinstance(widget, QComboBox):
                    if val:
                        widget.setCurrentText(val)
                    elif widget.count() > 0:
                        widget.setCurrentIndex(0)
                elif isinstance(widget, QLineEdit):
                    widget.setText(val or "")
            self._on_welded_design_changed(self._global_design_mode)
            self._update_welded_preview_and_props()
        finally:
            self._suppress_welded_thickness_popup = False

    def _view_state_apply_handlers(self) -> dict[str, callable]:
        return {
            VIEW_CROSS_BRACING: self._apply_cross_bracing_view_state,
            VIEW_ROLLED_BEAM: self._apply_rolled_view_state,
            VIEW_WELDED_BEAM: self._apply_welded_view_state,
        }

    def _apply_view_state(self, view_key: str, state: dict) -> None:
        key = (view_key or "").strip()
        handler = self._view_state_apply_handlers().get(key)
        if handler is not None:
            handler(state)

    def set_design_mode(self, mode_str: str) -> None:
        mode = DESIGN_CUSTOM if str(mode_str or "").strip().lower() in {"custom", "customized"} else DESIGN_OPTIMIZED
        self._global_design_mode = mode

        for combo in (self.cross_design_combo, self.rolled_design_combo, self.welded_design_combo):
            if combo is None:
                continue
            prev = combo.blockSignals(True)
            try:
                combo.setCurrentText(mode)
            finally:
                combo.blockSignals(prev)

        self._on_cross_design_changed(mode)
        self._on_rolled_design_changed(mode)
        self._on_welded_design_changed(mode)
        self._refresh_type_selector_options()
        self._restore_all_views_for_current_selection()

    def _allowed_end_diaphragm_types(self) -> list[str]:
        options = self._end_schema_choices(VIEW_CROSS_BRACING, "type_selector", list(VALUES_END_DIAPHRAGM_TYPE))
        if self._global_design_mode == DESIGN_OPTIMIZED:
            options = [value for value in options if value != VIEW_ROLLED_BEAM]
        return options

    def _refresh_type_selector_options(self) -> None:
        allowed_types = self._allowed_end_diaphragm_types()
        if not allowed_types:
            return

        desired_type = self.current_type if self.current_type in allowed_types else allowed_types[0]

        self.block_type_sync = True
        try:
            for selector in list(self.type_selectors or []):
                if selector is None:
                    continue
                previous_value = (selector.currentText() or "").strip()
                block = selector.blockSignals(True)
                try:
                    selector.clear()
                    selector.addItems(allowed_types)
                    fallback_value = desired_type if desired_type in allowed_types else allowed_types[0]
                    selector.setCurrentText(previous_value if previous_value in allowed_types else fallback_value)
                finally:
                    selector.blockSignals(block)
        finally:
            self.block_type_sync = False

        if desired_type != self.current_type:
            self._set_current_type(desired_type)

    def _store_view_state(self, view_key: str) -> None:
        selection_key = self._selection_key(view_key)
        if not selection_key:
            return
        self._state_by_view_member_key[selection_key] = self._snapshot_view_state(view_key)
        self._active_key_by_view[view_key] = selection_key

    def _load_view_state(self, view_key: str) -> None:
        selection_key = self._selection_key(view_key)
        if not selection_key:
            return
        self._active_key_by_view[view_key] = selection_key
        state = self._state_by_view_member_key.get(selection_key)
        if state is None:
            state = self._default_state_for_view(view_key)
        self._apply_view_state(view_key, state)

    def _store_all_view_states(self) -> None:
        for view_key in list(self._selection_by_view.keys()):
            self._store_view_state(view_key)

    def _restore_all_views_for_current_selection(self) -> None:
        for view_key in list(self._selection_by_view.keys()):
            self._load_view_state(view_key)

    def _sync_selection_index_to_all_views(self, idx: int) -> None:
        # Backward compatibility: treat this as girder-pair sync only.
        self._sync_girder_index_to_all_views(idx)

    def _sync_girder_index_to_all_views(self, idx: int) -> None:
        if self._block_selection_sync:
            return
        self._store_all_view_states()
        self._block_selection_sync = True
        try:
            for view_key, (girders_combo, member_combo) in self._selection_by_view.items():
                if girders_combo is not None and girders_combo.count() > 0:
                    girders_combo.setCurrentIndex(min(max(idx, 0), girders_combo.count() - 1))
                # Rebuild member IDs to match the newly selected pair while
                # preserving the M# selection when possible.
                if member_combo is not None:
                    self._rebuild_member_ids_for_view(view_key, previous_member=(member_combo.currentText() or "").strip())
                    try:
                        self._refresh_member_id_display(view_key)
                    except Exception:
                        pass
        finally:
            self._block_selection_sync = False
        self._restore_all_views_for_current_selection()

    def _sync_member_index_to_all_views(self, member_idx: int) -> None:
        if self._block_selection_sync:
            return
        self._store_all_view_states()
        self._block_selection_sync = True
        try:
            for _view_key, (_girders_combo, member_combo) in self._selection_by_view.items():
                if member_combo is not None and member_combo.count() > 0:
                    member_combo.setCurrentIndex(min(max(member_idx, 0), member_combo.count() - 1))
        finally:
            self._block_selection_sync = False
        self._restore_all_views_for_current_selection()

    def _is_optimized(self, combo: QComboBox | None) -> bool:
        if combo is None:
            return False
        return (combo.currentText() or "").strip() == DESIGN_OPTIMIZED

    def _design_combo_for_type(self, view_type: str | None) -> QComboBox | None:
        key = (view_type or "").strip()
        if key == VIEW_CROSS_BRACING:
            return self.cross_design_combo
        if key == VIEW_ROLLED_BEAM:
            return self.rolled_design_combo
        if key == VIEW_WELDED_BEAM:
            return self.welded_design_combo
        return None

    def _apply_rolled_custom_mode(self, is_custom: bool) -> None:
        for widget in self._rolled_inputs:
            if widget is not None:
                widget.setEnabled(is_custom)

    def _on_rolled_design_changed(self, label: str) -> None:
        is_custom = self._is_custom_design_label(label)
        self._apply_rolled_custom_mode(is_custom)

    def _apply_welded_custom_mode(self, is_custom: bool) -> None:
        for widget in self._welded_inputs:
            if widget is not None:
                widget.setEnabled(is_custom)

        if self._welded_right_column is not None:
            self._welded_right_column.setVisible(is_custom)
        if self._welded_view_layout is not None:
            self._welded_view_layout.setStretch(0, 1)
            self._welded_view_layout.setStretch(1, 1 if is_custom else 0)

        self._update_welded_thickness_value_enabled_state()

    def _on_welded_design_changed(self, label: str) -> None:
        is_custom = self._is_custom_design_label(label)
        self._apply_welded_custom_mode(is_custom)
        self._update_welded_dimension_field_mode()
        self._update_welded_preview_and_props()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        main_layout.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)

        self.type_stack = QStackedWidget()
        self.type_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        container_layout.addWidget(self.type_stack)
        container_layout.addStretch(1)

        self.views = {}
        self.view_order = []
        self.type_selector_map = {}
        self.type_selectors = []
        self.current_type = None
        self.block_type_sync = False

        cross_view, cross_selector = self._build_cross_bracing_view()
        self._add_type_view(VIEW_CROSS_BRACING, cross_view, cross_selector)
        rolled_view, rolled_selector = self._build_rolled_view()
        self._add_type_view(VIEW_ROLLED_BEAM, rolled_view, rolled_selector)
        welded_view, welded_selector = self._build_welded_view()
        self._add_type_view(VIEW_WELDED_BEAM, welded_view, welded_selector)

        self._refresh_type_selector_options()

        self._set_current_type(VIEW_CROSS_BRACING)

        # Now that all views/widgets exist, restore saved/default state for the
        # current (girder, member) selection across all views.
        self._restore_all_views_for_current_selection()

    def _add_type_view(self, key, widget, type_selector):
        widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.views[key] = widget
        self.view_order.append(key)
        self.type_stack.addWidget(widget)
        self.type_selector_map[key] = type_selector
        self.type_selectors.append(type_selector)
        type_selector.currentTextChanged.connect(self._handle_type_selection)

    # ---- Shared helpers ----
    def _create_card_frame(self):
        card = QFrame()
        card.setStyleSheet("QFrame { border: 1px solid #d0d0d0; border-radius: 12px; background-color: #ffffff; }")
        return card

    def _create_inner_box(self):
        box = QFrame()
        box.setStyleSheet(
            "QFrame { border: 1px solid #cfcfcf; border-radius: 8px; background-color: #ffffff; padding: 0px; margin: 0px; }"
            "QFrame QComboBox, QFrame QLineEdit { border: none; border-bottom: 1px solid #d0d0d0; border-radius: 0px; min-height: 28px; padding: 4px 8px; background-color: #ffffff; }"
            "QFrame QComboBox:hover, QFrame QLineEdit:hover { border-bottom: 1px solid #5d5d5d; }"
            "QFrame QComboBox:focus, QFrame QLineEdit:focus { border-bottom: 1px solid #90AF13; }"
            "QFrame QLabel { border: none; padding: 0px; margin: 0px; }"
        )
        return box

    def _normalize_label_text(self, text: str) -> str:
        return str(text or "").rstrip(": ")

    def _create_heading_label(self, text):
        label = QLabel(self._normalize_label_text(text))
        label.setTextFormat(Qt.RichText)
        label.setStyleSheet("font-size: 12px; font-weight: 700; color: #4b4b4b; border: none; padding: 0px; margin: 0px;")
        return label

    def _create_label(self, text):
        label = QLabel(self._normalize_label_text(text))
        label.setTextFormat(Qt.RichText)
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

    def _create_image_placeholder(self, text, min_height=140):
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumHeight(min_height)
        label.setStyleSheet("QLabel { border: 1px solid #d0d0d0; border-radius: 10px; background-color: #f7f7f7; font-weight: bold; color: #5b5b5b; }")
        return label

    def _create_line_edit(self, placeholder=""):
        line_edit = QLineEdit()
        if placeholder:
            line_edit.setPlaceholderText(placeholder)
        apply_field_style(line_edit)
        return line_edit

    def _end_schema_field(self, view_key: str, field_id: str) -> dict:
        """Return a field definition for a given view and field id.

        Looks up both `overview` and `section_inputs` blocks and returns the
        first matching schema field dict. Returns an empty dict when no match
        exists or the input id is blank.
        """
        views = END_DIAPHRAGM_DETAILS_SCHEMA.get("views", {})
        view_schema = views.get(str(view_key or ""), {}) if isinstance(views, dict) else {}
        target = str(field_id or "").strip()
        if not target:
            return {}

        for section_name in ("overview", "section_inputs"):
            fields = view_schema.get(section_name, [])
            for field in fields:
                if not isinstance(field, dict):
                    continue
                if str(field.get("id") or "").strip() == target:
                    return field
        return {}

    def _end_schema_choices(self, view_key: str, field_id: str, fallback: list[str]) -> list[str]:
        """Resolve choices for a schema field with a safe fallback list.

        Returns normalized string values from schema `choices` when available;
        otherwise returns the provided fallback values.
        """
        field = self._end_schema_field(view_key, field_id)
        choices = field.get("choices") or fallback
        return [str(value) for value in choices]

    def _end_schema_default(self, view_key: str, field_id: str, fallback: str) -> str:
        """Resolve a schema default as a string for UI controls.

        Uses the field `default` when present; otherwise returns the supplied
        fallback string.
        """
        field = self._end_schema_field(view_key, field_id)
        value = field.get("default", fallback)
        return str(value)

    def _end_schema_default_value(self, view_key: str, field_id: str, fallback):
        """Resolve a schema default preserving the original value type.

        Unlike `_end_schema_default`, this helper does not cast to string.
        """
        field = self._end_schema_field(view_key, field_id)
        return field.get("default", fallback)

    def _bind_end_schema_widget(self, view_key: str, field_id: str, widget: QWidget) -> None:
        """Bind a runtime widget to the schema-declared attribute name.

        If the field provides a `bind` key, this sets `self.<bind>` to the
        supplied widget so later state snapshot/apply routines can access it.
        """
        field = self._end_schema_field(view_key, field_id)
        bind_name = str(field.get("bind") or "").strip()
        if bind_name:
            setattr(self, bind_name, widget)

    def _end_schema_section_inputs(self, view_key: str) -> list[dict]:
        """Return normalized `section_inputs` fields for one view.

        Filters out non-dict entries and returns shallow copies for safe local
        use.
        """
        views = END_DIAPHRAGM_DETAILS_SCHEMA.get("views", {})
        view_schema = views.get(str(view_key or ""), {}) if isinstance(views, dict) else {}
        fields = view_schema.get("section_inputs", [])
        return [dict(field) for field in fields if isinstance(field, dict)]

    def _schema_default_state_for_view(self, view_key: str) -> dict:
        """Build default state payload for all schema fields in a view.

        Rules:
        - `design` always follows the current global design mode.
        - explicit schema defaults are used first.
        - combo fields fall back to first choice.
        - checkbox fields default to False.
        - other fields default to empty string.
        """
        state: dict[str, object] = {}
        for field in self._end_schema_section_inputs(view_key):
            field_id = str(field.get("id") or "").strip()
            if not field_id:
                continue

            field_type = str(field.get("type") or "").strip().lower()
            if field_id == "design":
                state[field_id] = self._global_design_mode
                continue

            if "default" in field:
                state[field_id] = field.get("default")
            elif field_type in {"combo", "combo_dynamic"}:
                choices = field.get("choices") or []
                state[field_id] = str(choices[0]) if choices else ""
            elif field_type == "checkbox":
                state[field_id] = False
            else:
                state[field_id] = ""

        return state

    def _snapshot_schema_state_for_view(self, view_key: str) -> dict:
        """Capture current widget values for schema-bound fields in a view.

        Reads values from widgets referenced by each field's `bind` key and
        stores them in a plain state dict keyed by schema field id.
        """
        state: dict[str, object] = {}
        for field in self._end_schema_section_inputs(view_key):
            field_id = str(field.get("id") or "").strip()
            bind_name = str(field.get("bind") or "").strip()
            if not field_id or not bind_name:
                continue

            widget = getattr(self, bind_name, None)
            if isinstance(widget, QComboBox):
                state[field_id] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                state[field_id] = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                state[field_id] = widget.text()

        return state

    def _apply_schema_state_for_view(self, view_key: str, state: dict, skip_ids: set[str] | None = None) -> None:
        """Apply a state payload into schema-bound widgets for one view.

        For each schema field with a `bind` target:
        - skip fields listed in `skip_ids`
        - read desired value from `state` or schema default
        - force `design` to current global design mode
        - write value to the bound widget based on widget type
        """
        skip = set(skip_ids or set())
        for field in self._end_schema_section_inputs(view_key):
            field_id = str(field.get("id") or "").strip()
            bind_name = str(field.get("bind") or "").strip()
            if not field_id or not bind_name or field_id in skip:
                continue

            widget = getattr(self, bind_name, None)
            desired = state.get(field_id, self._end_schema_default_value(view_key, field_id, ""))
            if field_id == "design":
                desired = self._global_design_mode

            if isinstance(widget, QComboBox):
                widget.setCurrentText(str(desired or ""))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(desired))
            elif isinstance(widget, QLineEdit):
                widget.setText(str(desired or ""))

    def _create_mode_value_widget(self, mode_combo: QComboBox, value_input: QLineEdit) -> QWidget:
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        try:
            widget.setFixedWidth(int(getattr(self, "_combo_width", 190)))
        except Exception:
            pass
        widget.setMinimumHeight(28)

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(mode_combo)
        layout.addWidget(value_input)
        return widget

    def _create_dimension_input_widget(self, field_key: str):
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        try:
            widget.setFixedWidth(int(getattr(self, "_combo_width", 190)))
        except Exception:
            pass

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
            bounds_button = getattr(self, f"welded_{field_key}_bounds_button", None)
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
        self._update_welded_preview_and_props()

    def _update_welded_dimension_field_mode(self) -> None:
        is_custom_design = self._is_custom_design_label(
            self.welded_design_combo.currentText() if self.welded_design_combo else ""
        )

        for field_key in ("total_depth", "top_width", "bottom_width"):
            value_input = getattr(self, f"welded_{field_key}", None)
            bounds_button = getattr(self, f"welded_{field_key}_bounds_button", None)
            if value_input is None or bounds_button is None:
                continue

            show_line_edit = bool(is_custom_design)
            value_input.setVisible(show_line_edit)
            value_input.setEnabled(show_line_edit)
            bounds_button.setVisible(not show_line_edit)
            bounds_button.setEnabled(not show_line_edit)

    def _attach_thickness_value_dropdown(self, wrapper: QWidget, value_input: QLineEdit) -> QComboBox:
        combo = QComboBox()
        combo.addItems(SAIL_APPROVED_THICKNESS_VALUES)
        apply_field_style(combo)
        combo.setVisible(False)
        self._configure_combo_box(combo)

        combo.currentTextChanged.connect(lambda text, inp=value_input: inp.setText(str(text or "")))
        combo.currentTextChanged.connect(self._update_welded_preview_and_props)

        layout = wrapper.layout()
        if layout is not None:
            layout.addWidget(combo)
        return combo

    def _sync_thickness_value_dropdown(self, mode_combo: QComboBox | None, value_input: QLineEdit | None, value_combo: QComboBox | None) -> None:
        if mode_combo is None or value_input is None or value_combo is None:
            return
        if not self._is_custom_thickness_mode(mode_combo):
            return

        first = ""
        selected = self._parse_selected_thickness_values(value_input.text())
        if selected:
            first = selected[0]
        else:
            current_text = str(value_input.text() or "").strip()
            if current_text in SAIL_APPROVED_THICKNESS_VALUES:
                first = current_text

        if not first:
            first = SAIL_APPROVED_THICKNESS_VALUES[0]
            value_input.setText(first)

        prev = value_combo.blockSignals(True)
        try:
            idx = value_combo.findText(first, Qt.MatchFixedString)
            value_combo.setCurrentIndex(idx if idx >= 0 else 0)
        finally:
            value_combo.blockSignals(prev)

    @staticmethod
    def _parse_selected_thickness_values(text: str) -> list[str]:
        chunks = [c.strip() for c in str(text or "").split(",") if str(c).strip()]
        return [v for v in chunks if v in SAIL_APPROVED_THICKNESS_VALUES]

    def _on_welded_thickness_mode_changed(self, field_key: str, _text: str) -> None:
        self._update_welded_thickness_value_enabled_state()
        self._update_welded_preview_and_props()

        if self._suppress_welded_thickness_popup:
            return

        is_custom_design = self._is_custom_design_label(
            self.welded_design_combo.currentText() if self.welded_design_combo else ""
        )
        if is_custom_design:
            return

        mode_combo = getattr(self, f"{field_key}_combo", None)
        if mode_combo is None or not self._is_custom_thickness_mode(mode_combo):
            return

        self._open_welded_thickness_values_dialog(field_key)

    def _open_welded_thickness_values_dialog(self, field_key: str) -> None:
        value_input = getattr(self, f"{field_key}_value", None)
        mode_combo = getattr(self, f"{field_key}_combo", None)
        value_combo = getattr(self, f"{field_key}_value_combo", None)
        if value_input is None or mode_combo is None:
            return

        selected = self._parse_selected_thickness_values(value_input.text())
        titles = {
            "welded_web_thickness": "Select Values: Web Thickness",
            "welded_top_thickness": "Select Values: Top Flange Thickness",
            "welded_bottom_thickness": "Select Values: Bottom Flange Thickness",
        }
        dialog = _ThicknessSelectionDialog(titles.get(field_key, "Select Values"), selected, self)
        if dialog.exec() != QDialog.Accepted:
            return

        chosen = dialog.selected_values()
        value_input.setText(", ".join(chosen))
        self._sync_thickness_value_dropdown(mode_combo, value_input, value_combo)
        self._update_welded_preview_and_props()

    def _is_custom_thickness_mode(self, combo: QComboBox | None) -> bool:
        if combo is None:
            return False
        return (combo.currentText() or "").strip().lower() == DESIGN_CUSTOM.lower()

    def _update_welded_thickness_value_enabled_state(self) -> None:
        is_custom_design = self._is_custom_design_label(
            self.welded_design_combo.currentText() if self.welded_design_combo else ""
        )

        for mode_combo, value_input, value_combo, wrapper in (
            (
                getattr(self, "welded_web_thickness_combo", None),
                getattr(self, "welded_web_thickness_value", None),
                getattr(self, "welded_web_thickness_value_combo", None),
                getattr(self, "welded_web_thickness_widget", None),
            ),
            (
                getattr(self, "welded_top_thickness_combo", None),
                getattr(self, "welded_top_thickness_value", None),
                getattr(self, "welded_top_thickness_value_combo", None),
                getattr(self, "welded_top_thickness_widget", None),
            ),
            (
                getattr(self, "welded_bottom_thickness_combo", None),
                getattr(self, "welded_bottom_thickness_value", None),
                getattr(self, "welded_bottom_thickness_value_combo", None),
                getattr(self, "welded_bottom_thickness_widget", None),
            ),
        ):
            if mode_combo is None or value_input is None:
                continue

            # Match Girder welded behavior:
            # Custom -> force Custom mode and show SAIL-value dropdown only.
            if is_custom_design:
                if mode_combo.currentText().strip().lower() != DESIGN_CUSTOM.lower():
                    prev = mode_combo.blockSignals(True)
                    mode_combo.setCurrentText(DESIGN_CUSTOM)
                    mode_combo.blockSignals(prev)

                mode_combo.setVisible(False)
                mode_combo.setEnabled(False)

                value_input.setVisible(False)
                value_input.setEnabled(False)
                value_input.setReadOnly(True)

                if value_combo is not None:
                    value_combo.setVisible(True)
                    value_combo.setEnabled(True)
                    self._sync_thickness_value_dropdown(mode_combo, value_input, value_combo)

                if wrapper is not None:
                    try:
                        wrapper.setFixedWidth(int(getattr(self, "_combo_width", 190)))
                    except Exception:
                        pass
                continue

            # Optimized -> show only mode combo; keep value controls hidden.
            mode_combo.setVisible(True)
            mode_combo.setEnabled(True)

            value_input.setVisible(False)
            value_input.setEnabled(False)
            value_input.setReadOnly(True)

            if value_combo is not None:
                value_combo.setVisible(False)
                value_combo.setEnabled(False)

            if wrapper is not None:
                try:
                    wrapper.setFixedWidth(int(getattr(self, "_combo_width", 190)))
                except Exception:
                    pass

    def _create_selection_box(self, view_key: str):
        box = self._create_inner_box()
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QGridLayout(box)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(8)
        layout.setColumnMinimumWidth(0, int(getattr(self, "_label_col_width", 260)))
        layout.setColumnMinimumWidth(1, int(getattr(self, "_combo_width", 190)))
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)

        girders_combo = QComboBox()
        # Populated from Girder Details when bound. (No All option.)
        self._configure_combo_box(girders_combo)
        apply_field_style(girders_combo)
        girders_combo.setFixedHeight(28)
        girders_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self._create_label("Select Girders:"), 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(girders_combo, 0, 1, Qt.AlignLeft | Qt.AlignVCenter)

        self._select_girders_combos.append(girders_combo)

        member_combo = QComboBox()
        # Populated from Girder Details when bound. (No Custom option.)
        self._configure_combo_box(member_combo)
        # Member IDs are software-generated and should not be edited.
        # Keep an internal (hidden) combo for state keys; display both ends.
        member_combo.setEditable(False)
        member_combo.setEnabled(False)
        member_combo.setVisible(False)
        try:
            member_combo.setInsertPolicy(QComboBox.NoInsert)
        except Exception:
            pass
        apply_field_style(member_combo)

        member_display = QLineEdit()
        member_display.setReadOnly(True)
        apply_field_style(member_display)
        member_display.setFixedSize(int(getattr(self, "_combo_width", 190)), 28)
        member_display.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        try:
            member_display.setFocusPolicy(Qt.NoFocus)
        except Exception:
            pass
        layout.addWidget(self._create_label("Member ID:"), 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(member_display, 1, 1, Qt.AlignLeft | Qt.AlignVCenter)

        self._member_id_combos.append(member_combo)

        # Register selection widgets for state persistence.
        self._selection_by_view[view_key] = (girders_combo, member_combo)
        self._member_id_display_by_view[view_key] = member_display

        # Keep selection synced across views.
        girders_combo.currentIndexChanged.connect(lambda idx, _k=view_key: self._sync_girder_index_to_all_views(idx))

        # Seed with safe defaults so the UI isn't empty before binding.
        try:
            self.refresh_girder_options()
        except Exception:
            pass

        try:
            self._refresh_member_id_display(view_key)
        except Exception:
            pass

        return box

    def collect_data(self) -> dict:
        """Serialize End Diaphragm inputs for all views/pairs/members."""
        # Persist any in-flight edits first.
        try:
            self._store_all_view_states()
        except Exception:
            pass

        pairs = self._girder_pairs()
        view_keys = list(self._selection_by_view.keys())

        # Serialize End Diaphragm inputs for both ends (M1/M2) for each girder-pair.
        # Inputs are shared: M1 is treated as source-of-truth and duplicated to M2.
        by_view: dict[str, dict] = {}
        for view_key in view_keys:
            by_view.setdefault(view_key, {})
            default_state = self._default_state_for_view(view_key)
            for pair_idx, pair_label in enumerate(pairs, start=1):
                source_key = f"{view_key}::{pair_label}::E{pair_idx}M1"
                state = self._state_by_view_member_key.get(source_key)
                if state is None:
                    # Backward compatibility: if an older save had only M2, use it.
                    state = self._state_by_view_member_key.get(f"{view_key}::{pair_label}::E{pair_idx}M2")
                if state is None:
                    state = dict(default_state)
                # Normalize back into M1 so internal state remains stable.
                self._state_by_view_member_key[source_key] = dict(state)

                for member_id in self._member_ids_for_pair(pair_idx):
                    member_id = (member_id or "").strip().upper()
                    payload = dict(state or {})
                    payload["select_girders"] = pair_label
                    payload["member_id"] = member_id
                    by_view[view_key][payload["member_id"]] = payload

        # Current selection (for convenience/backward compatibility).
        current_view = str(self.current_type or "").strip() or VIEW_CROSS_BRACING
        current_pair = ""
        current_member = ""
        combos = self._selection_by_view.get(current_view)
        if combos:
            girders_combo, member_combo = combos
            current_pair = (girders_combo.currentText() or "").strip() if girders_combo is not None else ""
            current_member = (member_combo.currentText() or "").strip().upper() if member_combo is not None else ""

        return {
            "type": current_view,
            "select_girders": current_pair,
            "member_id": current_member,
            "end_diaphragm_by_view": by_view,
        }

    def restore_data(self, data: dict) -> None:
        """Restore previously saved End Diaphragm inputs."""
        if not isinstance(data, dict):
            return

        restored = data.get("end_diaphragm_by_view")
        if isinstance(restored, dict):
            rebuilt: dict[str, dict] = {}
            # Rebuild internal selection-key map.
            for view_key, members in restored.items():
                if not isinstance(members, dict):
                    continue
                for member_id, payload in members.items():
                    if not isinstance(payload, dict):
                        continue
                    pair_label = str(payload.get("select_girders") or "").strip()
                    canonical_member = str(payload.get("member_id") or member_id or "").strip().upper()
                    # Inputs apply to both ends; normalize any M2 state into M1.
                    if canonical_member.endswith("M2"):
                        canonical_member = canonical_member[:-1] + "1"
                    if not view_key or not pair_label or not canonical_member:
                        continue
                    state = dict(payload)
                    state.pop("select_girders", None)
                    state.pop("member_id", None)
                    rebuilt[f"{view_key}::{pair_label}::{canonical_member}"] = state
            self._state_by_view_member_key = rebuilt

        # Refresh combos and restore selection/type where possible.
        try:
            self.refresh_girder_options()
        except Exception:
            pass

        target_type = str(data.get("type") or "").strip()
        if target_type:
            try:
                self._set_current_type(target_type)
            except Exception:
                pass

        target_pair = str(data.get("select_girders") or "").strip()
        target_member = str(data.get("member_id") or "").strip().upper()
        combos = self._selection_by_view.get(str(self.current_type or VIEW_CROSS_BRACING))
        if combos:
            girders_combo, member_combo = combos
            try:
                if target_pair and girders_combo is not None:
                    girders_combo.setCurrentText(target_pair)
            except Exception:
                pass
            try:
                if member_combo is not None:
                    # Ensure items match selected pair, then set member.
                    self._rebuild_member_ids_for_view(str(self.current_type or VIEW_CROSS_BRACING), previous_member=target_member)
                    try:
                        self._refresh_member_id_display(str(self.current_type or VIEW_CROSS_BRACING))
                    except Exception:
                        pass
            except Exception:
                pass

        try:
            self._restore_all_views_for_current_selection()
        except Exception:
            pass

    def _create_section_properties_box(self, title):
        box = self._create_inner_box()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        layout.addWidget(self._create_heading_label(title))

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 150)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        properties = [
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
        ]

        inputs = {}
        for row, (key, label_text) in enumerate(properties):
            label = self._create_label(label_text)
            label.setTextFormat(Qt.RichText)
            field = self._create_line_edit()
            field.setReadOnly(True)
            grid.addWidget(label, row, 0)
            grid.addWidget(field, row, 1)
            inputs[key] = field

        layout.addLayout(grid)
        return box, inputs

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

    def _apply_section_properties(self, inputs, values):
        for key, widget in inputs.items():
            previous = widget.blockSignals(True)
            widget.setText(self._format_property_value(values.get(key)))
            widget.blockSignals(previous)

    def _clear_section_properties(self, inputs):
        for widget in inputs.values():
            previous = widget.blockSignals(True)
            widget.clear()
            widget.blockSignals(previous)

    def _populate_rolled_sections(self, combo: QComboBox) -> None:
        designations = sorted(girder_properties.list_available_sections().keys())
        if not designations:
            designations = [
                "ISMB 500",
                "ISMB 550",
                "ISMB 600",
                "ISWB 500",
                "ISWB 550",
                "ISWB 600",
            ]
        block = combo.blockSignals(True)
        combo.clear()
        combo.addItems(designations)
        combo.setCurrentIndex(0 if designations else -1)
        combo.blockSignals(block)

    def _fetch_rolled_properties(self, designation: str):
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
        }

        area = values.get("Sectional Area, a (cm2)")
        iz = values.get("2nd Moment of Area, Iz (cm4)")
        iy = values.get("2nd Moment of Area, Iy (cm4)")
        if values.get("Radius of Gyration, rz (cm)") is None and area and iz:
            values["Radius of Gyration, rz (cm)"] = math.sqrt(iz / area)
        if values.get("Radius of Gyration, ry (cm)") is None and area and iy:
            values["Radius of Gyration, ry (cm)"] = math.sqrt(iy / area)
        return values

    def _gather_welded_dimensions(self):
        depth = self._parse_float(getattr(self, "welded_total_depth", QLineEdit()).text())
        top_width = self._parse_float(getattr(self, "welded_top_width", QLineEdit()).text())
        bottom_width = self._parse_float(getattr(self, "welded_bottom_width", QLineEdit()).text()) or top_width

        if not depth or not top_width or not bottom_width:
            return None

        # Match Girder welded behavior: infer thicknesses unless Custom value is provided.
        web_default = max(8.0, depth * 0.02)
        flange_default = max(10.0, depth * 0.03)

        web_thickness = web_default
        web_mode = getattr(self, "welded_web_thickness_combo", None)
        web_value = getattr(self, "welded_web_thickness_value", None)
        if self._is_custom_thickness_mode(web_mode):
            web_thickness = self._parse_float(web_value.text() if web_value is not None else "") or web_default

        top_thickness = flange_default
        top_mode = getattr(self, "welded_top_thickness_combo", None)
        top_value = getattr(self, "welded_top_thickness_value", None)
        if self._is_custom_thickness_mode(top_mode):
            top_thickness = self._parse_float(top_value.text() if top_value is not None else "") or flange_default

        bottom_thickness = flange_default
        bottom_mode = getattr(self, "welded_bottom_thickness_combo", None)
        bottom_value = getattr(self, "welded_bottom_thickness_value", None)
        if self._is_custom_thickness_mode(bottom_mode):
            bottom_thickness = self._parse_float(bottom_value.text() if bottom_value is not None else "") or flange_default

        return {
            "designation": "Custom Welded End Diaphragm",
            "section_type": "welded",
            "depth_mm": depth,
            "top_flange_width_mm": top_width,
            "bottom_flange_width_mm": bottom_width,
            "web_thickness_mm": web_thickness,
            "top_flange_thickness_mm": top_thickness,
            "bottom_flange_thickness_mm": bottom_thickness,
        }

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

        iz_web = (web_thickness * h_web**3) / 12.0
        iz_top = (top_width * top_thickness**3) / 12.0
        iz_bottom = (bottom_width * bottom_thickness**3) / 12.0
        distance_top = h_web / 2.0 + top_thickness / 2.0
        distance_bottom = h_web / 2.0 + bottom_thickness / 2.0
        iz_top += area_top * distance_top**2
        iz_bottom += area_bottom * distance_bottom**2
        iz_cm4 = (iz_web + iz_top + iz_bottom) / 10000.0

        iy_web = (h_web * web_thickness**3) / 12.0
        iy_top = (top_thickness * top_width**3) / 12.0
        iy_bottom = (bottom_thickness * bottom_width**3) / 12.0
        iy_cm4 = (iy_web + iy_top + iy_bottom) / 10000.0

        rz_cm = math.sqrt(iz_cm4 / area_cm2) if area_cm2 > 0 else None
        ry_cm = math.sqrt(iy_cm4 / area_cm2) if area_cm2 > 0 else None

        depth_cm = depth / 10.0
        width_cm = max(top_width, bottom_width) / 10.0
        zz_cm3 = iz_cm4 / (depth_cm / 2.0) if depth_cm > 0 else None
        zy_cm3 = iy_cm4 / (width_cm / 2.0) if width_cm > 0 else None

        zpl_major = (
            area_top * distance_top + area_bottom * distance_bottom + (web_thickness * h_web**2) / 4.0
        ) / 1000.0
        zpl_minor = (
            (top_thickness * top_width**2) / 4.0
            + (bottom_thickness * bottom_width**2) / 4.0
            + (h_web * web_thickness**2) / 4.0
        ) / 1000.0

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
        }

    def _update_rolled_preview_and_props(self):
        if not self._rolled_preview:
            return

        designation = getattr(self, "rolled_is_section_combo", QComboBox()).currentText()
        beam = girder_properties.get_beam_profile(designation)
        outline = girder_properties.get_rolled_section(designation) if beam is None else None
        has_data = bool(beam or outline)
        caption = f"Rolled section • {designation}" if has_data else "Rolled section unavailable"

        if beam:
            self._rolled_preview.set_section(beam)
        elif outline:
            self._rolled_preview.set_dimensions(
                depth_mm=outline["depth_mm"],
                flange_width_mm=outline["top_flange_width_mm"],
                bottom_flange_width_mm=outline["bottom_flange_width_mm"],
                web_thickness_mm=outline["web_thickness_mm"],
                flange_thickness_mm=outline["top_flange_thickness_mm"],
                bottom_flange_thickness_mm=outline["bottom_flange_thickness_mm"],
            )
        else:
            self._rolled_preview.clear()

        if self._rolled_caption:
            self._rolled_caption.setText(caption)

        values = self._fetch_rolled_properties(designation)
        if values:
            self._apply_section_properties(self._rolled_property_inputs, values)
        else:
            self._clear_section_properties(self._rolled_property_inputs)

    def _update_welded_preview_and_props(self):
        if not self._welded_preview:
            return
        dims = self._gather_welded_dimensions()
        caption = "Welded section preview" if dims else "Enter depth and flange widths"

        if dims:
            self._welded_preview.set_dimensions(
                depth_mm=dims["depth_mm"],
                flange_width_mm=dims["top_flange_width_mm"],
                bottom_flange_width_mm=dims["bottom_flange_width_mm"],
                web_thickness_mm=dims["web_thickness_mm"],
                flange_thickness_mm=dims["top_flange_thickness_mm"],
                bottom_flange_thickness_mm=dims["bottom_flange_thickness_mm"],
                show_welds=True,
            )
            values = self._compute_welded_properties(dims)
            self._apply_section_properties(self._welded_property_inputs, values)
        else:
            self._welded_preview.clear()
            self._clear_section_properties(self._welded_property_inputs)

        if self._welded_caption:
            self._welded_caption.setText(caption)

    # ---- Cross bracing helpers (angle/channel previews) -----------------
    def _cross_map_section_type(self, label: str) -> str:
        mapping = {
            "Angle": "angle",
            "Double Angle (Long Leg)": "double_angle_long",
            "Double Angle (Short Leg)": "double_angle_short",
            "Channel": "channel",
            "Double Channel": "double_channel",
        }
        return mapping.get((label or "").strip(), "angle")

    def _cross_display_name_for(self, designation: str, section_type: str) -> str:
        name = (designation or "").strip()
        if section_type in ("angle", "double_angle_long", "double_angle_short"):
            name = name.lstrip("∠⌒⟡⟠").strip()
            if name and not name.upper().startswith("IS"):
                name = f"IS {name}"
        return name

    def _cross_fill_combo(self, combo: QComboBox, items, section_type: str) -> None:
        if combo is None:
            return
        block = combo.blockSignals(True)
        combo.clear()
        for des in items:
            combo.addItem(self._cross_display_name_for(des, section_type), des)
        combo.setCurrentIndex(0 if combo.count() > 0 else -1)
        combo.blockSignals(block)

    def _cross_update_designations_for(self, combo: QComboBox, type_label: str) -> None:
        stype = self._cross_map_section_type(type_label)
        if stype in ("angle", "double_angle_long", "double_angle_short"):
            items = self._cross_catalog.list_angles()
        else:
            items = self._cross_catalog.list_channels()
        self._cross_fill_combo(combo, items, stype)

    def _cross_populate_designations(self) -> None:
        angles = self._cross_catalog.list_angles()
        self._cross_fill_combo(self.cross_bracing_section_combo, angles, "angle")
        self._cross_fill_combo(self.cross_top_chord_size_combo, angles, "angle")
        self._cross_fill_combo(self.cross_bottom_chord_size_combo, angles, "angle")

    def _cross_set_preview(self, key: str, type_combo: QComboBox, size_combo: QComboBox) -> None:
        widget = self._cross_previews.get(key)
        if not widget:
            return
        stype = self._cross_map_section_type(type_combo.currentText())
        designation = size_combo.currentData() or size_combo.currentText()
        # Match CrossBracingDetailsTab behavior: for double angles, don't show total envelope.
        show_double_total = stype not in ("double_angle_long", "double_angle_short")
        widget.set_section(stype, designation, show_double_total)

    def _update_cross_previews(self) -> None:
        if not self.cross_design_combo:
            return

        is_custom = self.cross_design_combo.currentText() == DESIGN_CUSTOM
        if not is_custom:
            for widget in self._cross_previews.values():
                widget.set_section("", "")
            return

        self._cross_set_preview(
            "bracing",
            self.cross_bracing_section_type_combo,
            self.cross_bracing_section_combo,
        )
        top_on = bool(self.cross_top_chord_checkbox is not None and self.cross_top_chord_checkbox.isChecked())
        bottom_on = bool(self.cross_bottom_chord_checkbox is not None and self.cross_bottom_chord_checkbox.isChecked())
        bracing = (self.cross_bracing_type_combo.currentText() if self.cross_bracing_type_combo is not None else "").strip()

        if top_on:
            self._cross_set_preview(
                "top",
                self.cross_top_chord_type_combo,
                self.cross_top_chord_size_combo,
            )
        else:
            top_widget = self._cross_previews.get("top")
            if top_widget is not None:
                top_widget.set_section("", "")

        show_bottom = bottom_on or bracing == "K-Bracing"
        if show_bottom:
            self._cross_set_preview(
                "bottom",
                self.cross_bottom_chord_type_combo,
                self.cross_bottom_chord_size_combo,
            )
        else:
            bottom_widget = self._cross_previews.get("bottom")
            if bottom_widget is not None:
                bottom_widget.set_section("", "")

    def _on_cross_bracing_layout_changed(self, *_args) -> None:
        if self._updating_cross_chord_rules:
            return

        self._updating_cross_chord_rules = True
        try:
            bracing = (self.cross_bracing_type_combo.currentText() if self.cross_bracing_type_combo is not None else "").strip()
            is_custom = bool(self.cross_design_combo is not None and self.cross_design_combo.currentText() == DESIGN_CUSTOM)

            if bracing == "K-Bracing" and self.cross_bottom_chord_checkbox is not None:
                self.cross_bottom_chord_checkbox.setChecked(True)

            top_checked = bool(self.cross_top_chord_checkbox is not None and self.cross_top_chord_checkbox.isChecked())
            bottom_checked = bool(self.cross_bottom_chord_checkbox is not None and self.cross_bottom_chord_checkbox.isChecked())

            if self.cross_top_chord_type_combo is not None:
                self.cross_top_chord_type_combo.setEnabled(is_custom and top_checked)
            if self.cross_top_chord_size_combo is not None:
                self.cross_top_chord_size_combo.setEnabled(is_custom and top_checked)
            if self.cross_bottom_chord_type_combo is not None:
                self.cross_bottom_chord_type_combo.setEnabled(is_custom and bottom_checked)
            if self.cross_bottom_chord_size_combo is not None:
                self.cross_bottom_chord_size_combo.setEnabled(is_custom and bottom_checked)

            top_box = self._cross_preview_boxes.get("top")
            if top_box is not None:
                top_box.setVisible(top_checked)

            show_bottom = bottom_checked or bracing == "K-Bracing"
            bottom_box = self._cross_preview_boxes.get("bottom")
            if bottom_box is not None:
                bottom_box.setVisible(show_bottom)

            if self.cross_bracing_layout_widget is not None:
                display = self._member_id_display_by_view.get(VIEW_CROSS_BRACING)
                member_text = display.text() if display is not None else ""
                pair_text = ""
                combos = self._selection_by_view.get(VIEW_CROSS_BRACING)
                if combos and combos[0] is not None:
                    pair_text = combos[0].currentText() or ""
                self.cross_bracing_layout_widget.set_layout(
                    bracing,
                    top_checked,
                    bottom_checked,
                    member_text,
                    pair_text,
                )
        finally:
            self._updating_cross_chord_rules = False

        self._adjust_type_stack()
        self._update_cross_previews()

    def _apply_cross_custom_mode(self, is_custom: bool) -> None:
        # Keep preview/diagram column visible even in Optimized mode.
        if self.cross_right_column is not None:
            self.cross_right_column.setVisible(True)
        for widget in (
            self.cross_bracing_section_type_combo,
            self.cross_bracing_section_combo,
        ):
            if widget is not None:
                widget.setEnabled(is_custom)

        for checkbox in (self.cross_top_chord_checkbox, self.cross_bottom_chord_checkbox):
            if checkbox is not None:
                checkbox.setEnabled(True)

        self._on_cross_bracing_layout_changed()

    def _on_cross_design_changed(self, label: str) -> None:
        is_custom = (label or "").strip() == DESIGN_CUSTOM
        self._apply_cross_custom_mode(is_custom)

    # ---- View builders ----
    def _build_cross_bracing_view(self):
        view = self._create_card_frame()
        layout = QHBoxLayout(view)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        left_column = QWidget()
        left_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)
        left_layout.addWidget(self._create_selection_box(VIEW_CROSS_BRACING))

        inputs_box = self._create_inner_box()
        inputs_layout = QVBoxLayout(inputs_box)
        inputs_layout.setContentsMargins(12, 8, 12, 8)
        inputs_layout.setSpacing(6)
        inputs_layout.addWidget(self._create_heading_label("Section Inputs:"))

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnMinimumWidth(0, int(getattr(self, "_label_col_width", 260)))
        grid.setColumnMinimumWidth(1, int(getattr(self, "_combo_width", 190)))
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        design_combo = QComboBox()
        design_combo.addItems(self._end_schema_choices(VIEW_CROSS_BRACING, "design", list(VALUES_GIRDER_DESIGN_MODE)))
        design_combo.setCurrentText(self._end_schema_default(VIEW_CROSS_BRACING, "design", DESIGN_OPTIMIZED))
        self._configure_combo_box(design_combo)
        apply_field_style(design_combo)
        design_combo.setVisible(False)
        row = 0
        self.cross_design_combo = design_combo
        self._bind_end_schema_widget(VIEW_CROSS_BRACING, "design", design_combo)

        type_selector = QComboBox()
        type_selector.addItems(self._end_schema_choices(VIEW_CROSS_BRACING, "type_selector", list(VALUES_END_DIAPHRAGM_TYPE)))
        type_selector.setCurrentText(self._end_schema_default(VIEW_CROSS_BRACING, "type_selector", VIEW_CROSS_BRACING))
        self._configure_combo_box(type_selector)
        apply_field_style(type_selector)
        row = self._add_grid_row(grid, row, "Type:", type_selector)

        bracing_combo = QComboBox()
        bracing_combo.addItems(self._end_schema_choices(VIEW_CROSS_BRACING, "bracing_type", ["K-Bracing", "X-Bracing"]))
        self._configure_combo_box(bracing_combo)
        apply_field_style(bracing_combo)
        row = self._add_grid_row(grid, row, "Type of Bracing:", bracing_combo)
        self.cross_bracing_type_combo = bracing_combo
        self._bind_end_schema_widget(VIEW_CROSS_BRACING, "bracing_type", bracing_combo)

        section_type_options = self._end_schema_choices(
            VIEW_CROSS_BRACING,
            "bracing_section_type",
            [
                "Angle",
                "Double Angle (Long Leg)",
                "Double Angle (Short Leg)",
                "Channel",
                "Double Channel",
            ],
        )

        bracing_section_type = QComboBox()
        bracing_section_type.addItems(section_type_options)
        self._configure_combo_box(bracing_section_type)
        apply_field_style(bracing_section_type)
        row = self._add_grid_row(grid, row, "Bracing Section Type:", bracing_section_type)
        self.cross_bracing_section_type_combo = bracing_section_type
        self._bind_end_schema_widget(VIEW_CROSS_BRACING, "bracing_section_type", bracing_section_type)

        bracing_section_size = QComboBox()
        self._configure_combo_box(bracing_section_size)
        apply_field_style(bracing_section_size)
        row = self._add_grid_row(grid, row, "Bracing Section Designation:", bracing_section_size)
        self.cross_bracing_section_combo = bracing_section_size

        self.cross_top_chord_checkbox = QCheckBox()
        self.cross_top_chord_checkbox.setFixedHeight(28)
        self.cross_top_chord_checkbox.setStyleSheet("margin-left: 2px;")
        self.cross_top_chord_checkbox.setChecked(self._end_schema_default(VIEW_CROSS_BRACING, "top_chord_enabled", "False").lower() == "true")
        row = self._add_grid_row(grid, row, "Top Chord:", self.cross_top_chord_checkbox)
        self._bind_end_schema_widget(VIEW_CROSS_BRACING, "top_chord_enabled", self.cross_top_chord_checkbox)

        top_chord_type = QComboBox()
        top_chord_type.addItems(section_type_options)
        self._configure_combo_box(top_chord_type)
        apply_field_style(top_chord_type)
        row = self._add_grid_row(grid, row, "Top Chord Section Type:", top_chord_type)
        self.cross_top_chord_type_combo = top_chord_type
        self._bind_end_schema_widget(VIEW_CROSS_BRACING, "top_chord_type", top_chord_type)

        top_chord_size = QComboBox()
        self._configure_combo_box(top_chord_size)
        apply_field_style(top_chord_size)
        row = self._add_grid_row(grid, row, "Top Chord Section Designation:", top_chord_size)
        self.cross_top_chord_size_combo = top_chord_size

        self.cross_bottom_chord_checkbox = QCheckBox()
        self.cross_bottom_chord_checkbox.setFixedHeight(28)
        self.cross_bottom_chord_checkbox.setStyleSheet("margin-left: 2px;")
        self.cross_bottom_chord_checkbox.setChecked(self._end_schema_default(VIEW_CROSS_BRACING, "bottom_chord_enabled", "True").lower() == "true")
        row = self._add_grid_row(grid, row, "Bottom Chord:", self.cross_bottom_chord_checkbox)
        self._bind_end_schema_widget(VIEW_CROSS_BRACING, "bottom_chord_enabled", self.cross_bottom_chord_checkbox)

        bottom_chord_type = QComboBox()
        bottom_chord_type.addItems(section_type_options)
        self._configure_combo_box(bottom_chord_type)
        apply_field_style(bottom_chord_type)
        row = self._add_grid_row(grid, row, "Bottom Chord Section Type:", bottom_chord_type)
        self.cross_bottom_chord_type_combo = bottom_chord_type
        self._bind_end_schema_widget(VIEW_CROSS_BRACING, "bottom_chord_type", bottom_chord_type)

        bottom_chord_size = QComboBox()
        self._configure_combo_box(bottom_chord_size)
        apply_field_style(bottom_chord_size)
        row = self._add_grid_row(grid, row, "Bottom Chord Section Designation:", bottom_chord_size)
        self.cross_bottom_chord_size_combo = bottom_chord_size

        inputs_layout.addLayout(grid)
        inputs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_layout.addWidget(inputs_box)
        left_layout.addStretch(1)

        layout.addWidget(left_column)

        right_column = QWidget()
        self.cross_right_column = right_column
        right_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        type_box = self._create_inner_box()
        type_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        type_layout = QVBoxLayout(type_box)
        type_layout.setContentsMargins(12, 8, 12, 10)
        type_layout.setSpacing(6)
        type_layout.addWidget(self._create_heading_label("Type of Bracing"))
        self.cross_bracing_layout_widget = BracingLayoutCadWidget(min_height=170)
        type_layout.addWidget(self.cross_bracing_layout_widget)
        right_layout.addWidget(type_box)

        for key, title in [("bracing", "Bracing"), ("top", "Top Chord"), ("bottom", "Bottom Chord")]:
            preview_box = self._create_inner_box()
            self._cross_preview_boxes[key] = preview_box
            preview_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            preview_layout = QVBoxLayout(preview_box)
            preview_layout.setContentsMargins(12, 8, 12, 8)
            preview_layout.setSpacing(6)
            # Make these preview titles bolder without affecting other headings
            preview_heading = QLabel(title)
            preview_heading.setStyleSheet("font-size: 12px; font-weight: 700; color: #4b4b4b; border: none;")
            preview_layout.addWidget(preview_heading)
            widget = PlaceholderSectionPreviewWidget(title, 110)
            preview_layout.addWidget(widget)
            self._cross_previews[key] = widget
            right_layout.addWidget(preview_box)

        right_layout.addStretch()
        layout.addWidget(right_column)
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        # Wire up dynamic designations + previews (same logic as CrossBracingDetailsTab).
        design_combo.currentTextChanged.connect(self._on_cross_design_changed)

        self.cross_bracing_type_combo.currentTextChanged.connect(self._on_cross_bracing_layout_changed)
        self.cross_top_chord_checkbox.toggled.connect(self._on_cross_bracing_layout_changed)
        self.cross_bottom_chord_checkbox.toggled.connect(self._on_cross_bracing_layout_changed)

        bracing_section_type.currentTextChanged.connect(
            lambda label: (self._cross_update_designations_for(bracing_section_size, label), self._update_cross_previews())
        )
        bracing_section_size.currentTextChanged.connect(self._update_cross_previews)

        top_chord_type.currentTextChanged.connect(
            lambda label: (self._cross_update_designations_for(top_chord_size, label), self._update_cross_previews())
        )
        top_chord_size.currentTextChanged.connect(self._update_cross_previews)

        bottom_chord_type.currentTextChanged.connect(
            lambda label: (self._cross_update_designations_for(bottom_chord_size, label), self._update_cross_previews())
        )
        bottom_chord_size.currentTextChanged.connect(self._update_cross_previews)

        self._cross_populate_designations()
        self._on_cross_design_changed(design_combo.currentText())
        return view, type_selector

    def _build_rolled_view(self):
        view = self._create_card_frame()
        layout = QHBoxLayout(view)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        left_column = QWidget()
        left_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)
        left_layout.addWidget(self._create_selection_box(VIEW_ROLLED_BEAM))

        inputs_box = self._create_inner_box()
        inputs_layout = QVBoxLayout(inputs_box)
        inputs_layout.setContentsMargins(12, 8, 12, 8)
        inputs_layout.setSpacing(6)
        inputs_layout.addWidget(self._create_heading_label("Section Inputs:"))

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnMinimumWidth(0, int(getattr(self, "_label_col_width", 260)))
        grid.setColumnMinimumWidth(1, int(getattr(self, "_combo_width", 190)))
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        design_combo = QComboBox()
        design_combo.addItems(self._end_schema_choices(VIEW_ROLLED_BEAM, "design", list(VALUES_GIRDER_DESIGN_MODE)))
        design_combo.setCurrentText(self._end_schema_default(VIEW_ROLLED_BEAM, "design", DESIGN_OPTIMIZED))
        self.rolled_design_combo = design_combo
        self._bind_end_schema_widget(VIEW_ROLLED_BEAM, "design", design_combo)
        self._configure_combo_box(design_combo)
        apply_field_style(design_combo)
        design_combo.setVisible(False)
        row = 0

        type_selector = QComboBox()
        type_selector.addItems(self._end_schema_choices(VIEW_ROLLED_BEAM, "type_selector", list(VALUES_END_DIAPHRAGM_TYPE)))
        type_selector.setCurrentText(self._end_schema_default(VIEW_ROLLED_BEAM, "type_selector", VIEW_ROLLED_BEAM))
        self._configure_combo_box(type_selector)
        apply_field_style(type_selector)
        row = self._add_grid_row(grid, row, "Type:", type_selector)

        is_section_combo = QComboBox()
        self._configure_combo_box(is_section_combo)
        apply_field_style(is_section_combo)
        self._populate_rolled_sections(is_section_combo)
        self._add_grid_row(grid, row, "IS Section:", is_section_combo)
        self.rolled_is_section_combo = is_section_combo
        self._bind_end_schema_widget(VIEW_ROLLED_BEAM, "is_section", is_section_combo)
        self._rolled_inputs = [is_section_combo]

        inputs_layout.addLayout(grid)
        inputs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_layout.addWidget(inputs_box)
        left_layout.addStretch(1)
        layout.addWidget(left_column)

        right_column = QWidget()
        right_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        image_box = self._create_inner_box()
        image_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        image_layout = QVBoxLayout(image_box)
        image_layout.setContentsMargins(12, 8, 12, 10)
        image_layout.setSpacing(6)

        self._rolled_preview = RolledSectionPreview()
        image_layout.addWidget(self._rolled_preview, 1)

        self._rolled_caption = QLabel("Select a rolled section")
        self._rolled_caption.setAlignment(Qt.AlignCenter)
        self._rolled_caption.setStyleSheet(
            "QLabel { font-size: 12px; font-weight: 700; color: #1e1e1e; border: none; padding-top: 6px; }"
        )
        image_layout.addWidget(self._rolled_caption)
        right_layout.addWidget(image_box)

        props_box, props_inputs = self._create_section_properties_box("Section Properties:")
        self._rolled_property_inputs = props_inputs
        props_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        right_layout.addWidget(props_box)
        right_layout.addStretch()

        layout.addWidget(right_column)
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        design_combo.currentTextChanged.connect(self._on_rolled_design_changed)
        is_section_combo.currentTextChanged.connect(self._update_rolled_preview_and_props)
        self._update_rolled_preview_and_props()
        self._on_rolled_design_changed(design_combo.currentText())
        return view, type_selector

    def _build_welded_view(self):
        view = self._create_card_frame()
        layout = QHBoxLayout(view)
        self._welded_view_layout = layout
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        left_column = QWidget()
        left_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)
        left_layout.addWidget(self._create_selection_box(VIEW_WELDED_BEAM))

        inputs_box = self._create_inner_box()
        inputs_layout = QVBoxLayout(inputs_box)
        inputs_layout.setContentsMargins(12, 8, 12, 8)
        inputs_layout.setSpacing(6)
        inputs_layout.addWidget(self._create_heading_label("Section Inputs:"))

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnMinimumWidth(0, int(getattr(self, "_label_col_width", 260)))
        grid.setColumnMinimumWidth(1, int(getattr(self, "_combo_width", 190)))
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        design_combo = QComboBox()
        design_combo.addItems(self._end_schema_choices(VIEW_WELDED_BEAM, "design", list(VALUES_GIRDER_DESIGN_MODE)))
        design_combo.setCurrentText(self._end_schema_default(VIEW_WELDED_BEAM, "design", DESIGN_OPTIMIZED))
        self.welded_design_combo = design_combo
        self._bind_end_schema_widget(VIEW_WELDED_BEAM, "design", design_combo)
        self._configure_combo_box(design_combo)
        apply_field_style(design_combo)
        design_combo.setVisible(False)
        row = 0

        type_selector = QComboBox()
        type_selector.addItems(self._end_schema_choices(VIEW_WELDED_BEAM, "type_selector", list(VALUES_END_DIAPHRAGM_TYPE)))
        type_selector.setCurrentText(self._end_schema_default(VIEW_WELDED_BEAM, "type_selector", VIEW_WELDED_BEAM))
        self._configure_combo_box(type_selector)
        apply_field_style(type_selector)
        row = self._add_grid_row(grid, row, "Type:", type_selector)

        symmetry_combo = QComboBox()
        symmetry_combo.addItems(self._end_schema_choices(VIEW_WELDED_BEAM, "symmetry", list(VALUES_GIRDER_SYMMETRY)))
        self._configure_combo_box(symmetry_combo)
        apply_field_style(symmetry_combo)
        row = self._add_grid_row(grid, row, "Symmetry:", symmetry_combo)
        self._bind_end_schema_widget(VIEW_WELDED_BEAM, "symmetry", symmetry_combo)

        total_depth_widget, total_depth, total_depth_bounds_button = self._create_dimension_input_widget("total_depth")
        row = self._add_grid_row(grid, row, "Total Depth, d (mm):", total_depth_widget)
        self.welded_total_depth = total_depth
        self.welded_total_depth_widget = total_depth_widget
        self.welded_total_depth_bounds_button = total_depth_bounds_button

        web_thick_combo = QComboBox()
        web_thick_combo.addItems(VALUES_PROFILE_SCOPE)
        self._configure_combo_box(web_thick_combo)
        apply_field_style(web_thick_combo)

        web_thick_value = self._create_line_edit()
        web_thick_value.setValidator(QDoubleValidator(0, 1_000_000, 3))
        try:
            web_thick_value.setFixedWidth(78)
            web_thick_value.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        except Exception:
            pass

        web_thick_widget = self._create_mode_value_widget(web_thick_combo, web_thick_value)
        row = self._add_grid_row(grid, row, "Web Thickness, w<sub>t</sub> (mm):", web_thick_widget)
        self.welded_web_thickness_combo = web_thick_combo
        self.welded_web_thickness_value = web_thick_value
        self.welded_web_thickness_widget = web_thick_widget
        self.welded_web_thickness_value_combo = self._attach_thickness_value_dropdown(web_thick_widget, web_thick_value)

        top_width_widget, top_width, top_width_bounds_button = self._create_dimension_input_widget("top_width")
        row = self._add_grid_row(grid, row, "Width of Top Flange, t<sub>fw</sub> (mm):", top_width_widget)
        self.welded_top_width = top_width
        self.welded_top_width_widget = top_width_widget
        self.welded_top_width_bounds_button = top_width_bounds_button

        top_thickness_combo = QComboBox()
        top_thickness_combo.addItems(VALUES_PROFILE_SCOPE)
        self._configure_combo_box(top_thickness_combo)
        apply_field_style(top_thickness_combo)

        top_thickness_value = self._create_line_edit()
        top_thickness_value.setValidator(QDoubleValidator(0, 1_000_000, 3))
        try:
            top_thickness_value.setFixedWidth(78)
            top_thickness_value.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        except Exception:
            pass

        top_thickness_widget = self._create_mode_value_widget(top_thickness_combo, top_thickness_value)
        row = self._add_grid_row(grid, row, "Top Flange Thickness, t<sub>ft</sub> (mm):", top_thickness_widget)
        self.welded_top_thickness_combo = top_thickness_combo
        self.welded_top_thickness_value = top_thickness_value
        self.welded_top_thickness_widget = top_thickness_widget
        self.welded_top_thickness_value_combo = self._attach_thickness_value_dropdown(top_thickness_widget, top_thickness_value)

        bottom_width_widget, bottom_width, bottom_width_bounds_button = self._create_dimension_input_widget("bottom_width")
        row = self._add_grid_row(grid, row, "Width of Bottom Flange, b<sub>fw</sub> (mm):", bottom_width_widget)
        self.welded_bottom_width = bottom_width
        self.welded_bottom_width_widget = bottom_width_widget
        self.welded_bottom_width_bounds_button = bottom_width_bounds_button

        bottom_thickness_combo = QComboBox()
        bottom_thickness_combo.addItems(VALUES_PROFILE_SCOPE)
        self._configure_combo_box(bottom_thickness_combo)
        apply_field_style(bottom_thickness_combo)

        bottom_thickness_value = self._create_line_edit()
        bottom_thickness_value.setValidator(QDoubleValidator(0, 1_000_000, 3))
        try:
            bottom_thickness_value.setFixedWidth(78)
            bottom_thickness_value.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        except Exception:
            pass

        bottom_thickness_widget = self._create_mode_value_widget(bottom_thickness_combo, bottom_thickness_value)
        row = self._add_grid_row(grid, row, "Bottom Flange Thickness, b<sub>ft</sub> (mm):", bottom_thickness_widget)
        self.welded_bottom_thickness_combo = bottom_thickness_combo
        self.welded_bottom_thickness_value = bottom_thickness_value
        self.welded_bottom_thickness_widget = bottom_thickness_widget
        self.welded_bottom_thickness_value_combo = self._attach_thickness_value_dropdown(bottom_thickness_widget, bottom_thickness_value)

        self._welded_inputs = [
            symmetry_combo,
            total_depth,
            web_thick_combo,
            web_thick_value,
            top_width,
            top_thickness_combo,
            top_thickness_value,
            bottom_width,
            bottom_thickness_combo,
            bottom_thickness_value,
        ]

        inputs_layout.addLayout(grid)
        inputs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_layout.addWidget(inputs_box)
        left_layout.addStretch(1)
        layout.addWidget(left_column)

        right_column = QWidget()
        self._welded_right_column = right_column
        right_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        image_box = self._create_inner_box()
        image_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        image_layout = QVBoxLayout(image_box)
        image_layout.setContentsMargins(12, 8, 12, 10)
        image_layout.setSpacing(6)

        self._welded_preview = RolledSectionPreview()
        image_layout.addWidget(self._welded_preview, 1)

        self._welded_caption = QLabel("Enter welded inputs to preview")
        self._welded_caption.setAlignment(Qt.AlignCenter)
        self._welded_caption.setStyleSheet(
            "QLabel { font-size: 12px; font-weight: 700; color: #1e1e1e; border: none; padding-top: 6px; }"
        )
        image_layout.addWidget(self._welded_caption)
        right_layout.addWidget(image_box)

        props_box, props_inputs = self._create_section_properties_box("Section Properties:")
        self._welded_property_inputs = props_inputs
        props_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        right_layout.addWidget(props_box)
        right_layout.addStretch()

        layout.addWidget(right_column)
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        design_combo.currentTextChanged.connect(self._on_welded_design_changed)
        for watcher in (total_depth, top_width, bottom_width):
            watcher.textChanged.connect(self._update_welded_preview_and_props)
        for watcher in (web_thick_value, top_thickness_value, bottom_thickness_value):
            watcher.textChanged.connect(self._update_welded_preview_and_props)
        web_thick_combo.currentTextChanged.connect(
            lambda text: self._on_welded_thickness_mode_changed("welded_web_thickness", text)
        )
        top_thickness_combo.currentTextChanged.connect(
            lambda text: self._on_welded_thickness_mode_changed("welded_top_thickness", text)
        )
        bottom_thickness_combo.currentTextChanged.connect(
            lambda text: self._on_welded_thickness_mode_changed("welded_bottom_thickness", text)
        )
        self._update_welded_preview_and_props()
        self._on_welded_design_changed(design_combo.currentText())
        self._update_welded_thickness_value_enabled_state()
        self._update_welded_dimension_field_mode()
        self._refresh_bounds_tooltips()
        return view, type_selector

    def _handle_type_selection(self, value):
        if self.block_type_sync:
            return
        if value in self.view_order:
            self._set_current_type(value)

    def _adjust_type_stack(self):
        if not hasattr(self, "type_stack"):
            return
        idx = self.type_stack.currentIndex()
        for i in range(self.type_stack.count()):
            w = self.type_stack.widget(i)
            if i == idx:
                w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            else:
                w.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

    def _set_current_type(self, target):
        allowed_types = self._allowed_end_diaphragm_types()
        if not allowed_types:
            return

        if target not in self.view_order:
            return
        if target not in allowed_types:
            target = allowed_types[0]
        if self.current_type == target:
            return

        previous_type = self.current_type
        if previous_type:
            try:
                # Match tab-switch behavior: commit outgoing view before switching.
                self._store_view_state(previous_type)
            except Exception:
                pass
        previous_was_optimized = self._is_optimized(self._design_combo_for_type(previous_type))

        self.current_type = target
        index = self.view_order.index(target)
        self.type_stack.setCurrentIndex(index)
        
        self.block_type_sync = True
        for selector in self.type_selectors:
            selector.setCurrentText(target)
        self.block_type_sync = False

        self._adjust_type_stack()

        try:
            # Load incoming view state for the active girder/member selection.
            self._load_view_state(target)
        except Exception:
            pass

        # If the user was in Optimized mode, keep Optimized when switching types.
        if previous_was_optimized:
            next_design_combo = self._design_combo_for_type(target)
            if next_design_combo is not None:
                next_design_combo.setCurrentText(DESIGN_OPTIMIZED)

        # Ensure enabled/disabled state and previews are updated using view dispatch.
        design_apply_handlers = {
            VIEW_CROSS_BRACING: lambda: self._on_cross_design_changed(self.cross_design_combo.currentText()) if self.cross_design_combo is not None else None,
            VIEW_ROLLED_BEAM: lambda: self._on_rolled_design_changed(self.rolled_design_combo.currentText()) if self.rolled_design_combo is not None else None,
            VIEW_WELDED_BEAM: lambda: self._on_welded_design_changed(self.welded_design_combo.currentText()) if self.welded_design_combo is not None else None,
        }
        preview_refresh_handlers = {
            VIEW_CROSS_BRACING: self._update_cross_previews,
            VIEW_ROLLED_BEAM: self._update_rolled_preview_and_props,
            VIEW_WELDED_BEAM: self._update_welded_preview_and_props,
        }

        design_handler = design_apply_handlers.get(target)
        if design_handler is not None:
            design_handler()

        preview_handler = preview_refresh_handlers.get(target)
        if preview_handler is not None:
            preview_handler()

    # ---- External API -----------------------------------------------------
    def reset_defaults(self) -> None:
        """Reset End Diaphragm inputs (all views) back to initial/default state."""

        # Clear per-selection persistence.
        self._state_by_view_member_key.clear()
        self._active_key_by_view.clear()

        # Reset selection combos to the first option across all views.
        self._block_selection_sync = True
        try:
            for girders_combo, member_combo in (self._selection_by_view or {}).values():
                if girders_combo is not None and girders_combo.count() > 0:
                    girders_combo.setCurrentIndex(0)
                if member_combo is not None and member_combo.count() > 0:
                    member_combo.setCurrentIndex(0)
        finally:
            self._block_selection_sync = False

        # Set the default type and ensure it doesn't try to preserve optimized
        # state from a previous selection.
        try:
            self.current_type = None
            self._set_current_type(VIEW_CROSS_BRACING)
        except Exception:
            pass

        # Apply default view state for current selection.
        try:
            self._restore_all_views_for_current_selection()
        except Exception:
            pass

