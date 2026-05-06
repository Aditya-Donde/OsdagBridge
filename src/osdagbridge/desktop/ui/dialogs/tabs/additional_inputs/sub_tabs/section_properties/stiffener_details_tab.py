"""Stiffener Details tab.

This tab is part of Member Properties (Section Properties) and stores inputs per girder member.
"""

from __future__ import annotations

import copy
import re
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QWidget,
)

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import STIFFENER_DETAILS_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.builder import UIBuilder
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


class StiffenerDetailsTab(SchemaTab):
    """Tab for Stiffener Details driven by schema."""
    schema = STIFFENER_DETAILS_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self._girder_details_tab = None
        self._girder_state: Dict[str, object] = {}
        self._state_by_member: Dict[str, dict] = {}
        self._active_member_id: Optional[str] = None
        self._is_loading_ui: bool = False
        
        # Initial state
        self.refresh_girder_members()

    def bind_girder_details_tab(self, girder_details_tab) -> None:
        """Bind to the Girder Details tab to populate members and detect optimized members."""
        self._girder_details_tab = girder_details_tab
        export_state = getattr(girder_details_tab, "export_dependency_state", None)
        if callable(export_state):
            try:
                self._girder_state = dict(export_state() or {})
            except Exception:
                self._girder_state = {}
        self.refresh_girder_members()
        self._update_dynamic_cad_preview()

    def refresh_from_girder_state(self, state: dict) -> None:
        self._girder_state = dict(state or {})
        self.refresh_girder_members()
        self._update_dynamic_cad_preview()

    def refresh_girder_members(self) -> None:
        """Refresh the Select Girder Member dropdown from Girder Details segment chains."""
        self._store_current_member_state()

        members = []
        if isinstance(self._girder_state.get("member_ids"), list):
            members = [str(member_id) for member_id in self._girder_state.get("member_ids", []) if member_id]
        elif self._girder_details_tab is not None and hasattr(self._girder_details_tab, "list_all_member_ids"):
            try:
                members = list(self._girder_details_tab.list_all_member_ids() or [])
            except Exception:
                members = []

        if not members:
            members = ["G1-1"]

        previous = self.girder_member_combo.blockSignals(True)
        try:
            current = self.girder_member_combo.currentText().strip()
            self.girder_member_combo.clear()
            for member_id in members:
                self.girder_member_combo.addItem(str(member_id), str(member_id))
            target = current if current in members else members[0]
            self.girder_member_combo.setCurrentText(target)
        finally:
            self.girder_member_combo.blockSignals(previous)

        self._on_member_changed(self.girder_member_combo.currentText())
        self._update_dynamic_cad_preview()

    def validate(self) -> list[str]:
        """Validate current stored inputs before saving the dialog."""
        errors = schema_io.validate(self, STIFFENER_DETAILS_SCHEMA)
        self._store_current_member_state()
        for member_id, state in self._state_by_member.items():
            if self._is_member_optimized(member_id):
                continue
            try:
                self._validate_outstand_values(member_id, state)
            except ValueError as exc:
                errors.append(str(exc))
            if state.get("intermediate_stiffener") == "Yes":
                spacing = str(state.get("intermediate_spacing_mm") or "").strip()
                if not spacing.isdigit() or int(spacing) <= 0:
                    try:
                        self.girder_member_combo.setCurrentText(str(member_id))
                        self.intermediate_spacing_input.setFocus()
                        self.intermediate_spacing_input.selectAll()
                    except Exception:
                        pass
                    errors.append(
                        f"Intermediate Stiffener Spacing (mm) is required for member '{member_id}' when Intermediate Stiffener is Yes."
                    )
        return list(dict.fromkeys(errors))

    def collect_data(self) -> dict:
        self._store_current_member_state()
        current_state = schema_io.collect_values(self, STIFFENER_DETAILS_SCHEMA)
        if self._active_member_id:
            self._state_by_member[self._active_member_id] = dict(current_state)
        for member_id in self._list_current_member_ids():
            if member_id not in self._state_by_member:
                self._state_by_member[member_id] = dict(current_state)
        data = dict(current_state)
        data.update({"stiffener_by_member": copy.deepcopy(self._state_by_member)})
        return data

    def reset_defaults(self) -> None:
        """Reset UI + per-member stored values to the initial defaults."""
        self._state_by_member.clear()
        self._active_member_id = None
        self.refresh_girder_members()

    def restore_data(self, data: dict) -> None:
        """Restore previously saved stiffener inputs."""
        if not isinstance(data, dict):
            return
        restored = data.get("stiffener_by_member", {})
        has_nested_state = isinstance(restored, dict) and bool(restored)
        self._state_by_member = copy.deepcopy(restored) if has_nested_state else {}
        self.refresh_girder_members()
        if has_nested_state:
            return

        schema_io.restore_values(self, STIFFENER_DETAILS_SCHEMA, data)
        current_state = schema_io.collect_values(self, STIFFENER_DETAILS_SCHEMA)
        for member_id in self._list_current_member_ids():
            self._state_by_member[member_id] = dict(current_state)
        if self._active_member_id:
            self._load_member_state(self._active_member_id)

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self.refresh_girder_members()

    def _get_default_state(self) -> dict:
        # Temporary reset to get default values from schema_io
        schema_io.reset_defaults(self, STIFFENER_DETAILS_SCHEMA)
        return schema_io.collect_values(self, STIFFENER_DETAILS_SCHEMA)

    def _store_current_member_state(self) -> None:
        if self._is_loading_ui or not self._active_member_id:
            return
        self._state_by_member[self._active_member_id] = schema_io.collect_values(self, STIFFENER_DETAILS_SCHEMA)
        self._update_dynamic_cad_preview()

    def _load_member_state(self, member_id: str) -> None:
        if member_id not in self._state_by_member:
            self._state_by_member[member_id] = self._get_default_state()
        
        state = self._state_by_member[member_id]
        self._is_loading_ui = True
        try:
            schema_io.restore_values(self, STIFFENER_DETAILS_SCHEMA, state)
        finally:
            self._is_loading_ui = False

        self._on_intermediate_changed(self.intermediate_combo.currentText())
        self._on_longitudinal_changed(self.longitudinal_combo.currentText())
        self._update_outstand_fields(member_id)
        self._refresh_enabled_state(member_id)
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
        self._store_current_member_state()

    def _update_outstand_fields(self, member_id: str) -> None:
        computed = self._compute_outstand_value(member_id)
        if computed is None:
            return

        for widget in [self.bearing_outstand_input, self.intermediate_outstand_input]:
            if not widget.text().strip():
                prev = widget.blockSignals(True)
                widget.setText(computed)
                widget.blockSignals(prev)

    def _parse_non_negative_float(self, value: str) -> Optional[float]:
        try:
            text = str(value or "").strip()
            if text == "": return None
            parsed = float(text)
            return parsed if parsed >= 0.0 else None
        except Exception:
            return None

    def _validate_outstand_values(self, member_id: str, state: dict) -> None:
        computed = self._compute_outstand_value(member_id)
        if computed is None:
            return
        max_val = float(computed)
        for key, label in [
            ("bearing_outstand_input", "Outstand of Bearing Stiffener (mm)"),
            ("intermediate_outstand_input", "Outstand of Intermediate Stiffener (mm)"),
        ]:
            raw = str(state.get(key) or "").strip()
            parsed = self._parse_non_negative_float(raw)
            if parsed is not None and parsed > max_val:
                raise ValueError(f"{label} must be <= {max_val:.3f} for member '{member_id}'.")

    def _compute_outstand_value(self, member_id: str) -> Optional[str]:
        dims_by_member = self._girder_state.get("section_dimensions_by_member")
        if isinstance(dims_by_member, dict):
            dims = dims_by_member.get(member_id)
        elif self._girder_details_tab and hasattr(self._girder_details_tab, "get_member_section_dimensions"):
            dims = self._girder_details_tab.get_member_section_dimensions(member_id)
        else:
            dims = None
        if not isinstance(dims, dict): return None
        try:
            tw = float(dims.get("web_thickness_mm") or 0.0)
            bf = min(float(dims.get("top_flange_width_mm") or 0.0), float(dims.get("bottom_flange_width_mm") or 0.0))
            if tw <= 0 or bf <= 0: return None
            outstand = (bf - tw) / 2.0
            return f"{outstand:.3f}".rstrip("0").rstrip(".") if outstand > 0 else None
        except (TypeError, ValueError):
            return None

    def _on_intermediate_changed(self, text: str) -> None:
        is_yes = str(text).strip() == "Yes"
        if not is_yes:
            prev = self.intermediate_spacing_input.blockSignals(True)
            self.intermediate_spacing_input.setText("NA")
            self.intermediate_spacing_input.blockSignals(prev)
        elif self.intermediate_spacing_input.text().strip().upper() == "NA":
            self.intermediate_spacing_input.clear()
        self._refresh_enabled_state(self._active_member_id or "")
        self._store_current_member_state()

    def _on_longitudinal_changed(self, text: str) -> None:
        self._refresh_enabled_state(self._active_member_id or "")
        self._store_current_member_state()

    def _on_thickness_mode_changed(self, _text: str) -> None:
        self._update_thickness_value_enabled_state(self._active_member_id or "")
        self._store_current_member_state()

    def _update_thickness_value_enabled_state(self, member_id: str) -> None:
        optimized = self._is_member_optimized(member_id)
        base_enabled = not optimized
        inter_yes = self.intermediate_combo.currentText().strip() == "Yes"
        long_yes = self.longitudinal_combo.currentText().strip().startswith("Yes")

        for mode_combo, value_combo, applicable in [
            (self.bearing_thick_combo, self.bearing_thick_value_combo, True),
            (self.intermediate_thick_combo, self.intermediate_thick_value_combo, inter_yes),
            (self.long_thick_combo, self.long_thick_value_combo, long_yes),
        ]:
            if not optimized:
                mode_combo.setVisible(False)
                value_combo.setVisible(True)
                value_combo.setEnabled(base_enabled and applicable)
            else:
                mode_combo.setVisible(True)
                mode_combo.setEnabled(base_enabled and applicable)
                is_custom = mode_combo.currentText().strip().lower() == "custom"
                value_combo.setVisible(is_custom)
                value_combo.setEnabled(base_enabled and applicable and is_custom)

    def _is_member_optimized(self, member_id: str) -> bool:
        optimized = self._girder_state.get("optimized_members")
        if isinstance(optimized, set):
            return member_id in optimized
        if isinstance(optimized, (list, tuple)):
            return member_id in optimized
        if not self._girder_details_tab or not hasattr(self._girder_details_tab, "is_member_optimized"):
            return False
        return bool(self._girder_details_tab.is_member_optimized(member_id))

    def _refresh_enabled_state(self, member_id: str) -> None:
        optimized = self._is_member_optimized(member_id)
        exterior = self._is_exterior_member(member_id)
        base_enabled = not optimized

        self.bearing_count_combo.setEnabled(base_enabled and exterior)
        self.bearing_spacing_input.setEnabled(base_enabled and exterior)
        self.bearing_thick_combo.setEnabled(base_enabled)
        self.bearing_outstand_input.setEnabled(base_enabled)
        self.intermediate_outstand_input.setEnabled(base_enabled)
        self.intermediate_combo.setEnabled(base_enabled)
        self.longitudinal_combo.setEnabled(base_enabled)
        self.method_combo.setEnabled(base_enabled)

        inter_yes = self.intermediate_combo.currentText().strip() == "Yes"
        long_yes = self.longitudinal_combo.currentText().strip().startswith("Yes")

        self.intermediate_spacing_input.setEnabled(base_enabled and inter_yes)
        self.intermediate_thick_combo.setEnabled(base_enabled and inter_yes)
        self.long_thick_combo.setEnabled(base_enabled and long_yes)
        self._update_thickness_value_enabled_state(member_id)
        self.apply_to_all_btn.setEnabled(base_enabled)

    def _is_exterior_member(self, member_id: str) -> bool:
        g_idx, m_idx = self._parse_member_indices(member_id)
        if g_idx is None: return True
        indices = [m for g, m in [self._parse_member_indices(mid) for mid in self._list_current_member_ids()] if g == g_idx]
        return m_idx in {min(indices), max(indices)} if indices else True

    @staticmethod
    def _parse_member_indices(member_id: str) -> tuple[Optional[int], Optional[int]]:
        m = re.match(r"^G(\d+)M(\d+)$", str(member_id or "").strip())
        return (int(m.group(1)), int(m.group(2))) if m else (None, None)

    def _list_current_member_ids(self) -> list[str]:
        return [self.girder_member_combo.itemText(i) for i in range(self.girder_member_combo.count())]

    def _segments_for_girder(self, girder: str) -> list[dict]:
        segment_chain = self._girder_state.get("segment_chain")
        if isinstance(segment_chain, dict):
            segments = segment_chain.get(girder)
            if isinstance(segments, list):
                return list(segments)

        if self._girder_details_tab is None:
            return []
        getter = getattr(self._girder_details_tab, "segments_for_girder", None)
        if callable(getter):
            try:
                return list(getter(girder) or [])
            except Exception:
                return []
        return []

    def _apply_current_to_all_members(self) -> None:
        self._store_current_member_state()
        if not self._active_member_id: return
        template = dict(self._state_by_member[self._active_member_id])
        for mid in self._list_current_member_ids():
            if not self._is_member_optimized(mid):
                self._state_by_member[mid] = dict(template)
        self._load_member_state(self._active_member_id)

    def _update_dynamic_cad_preview(self) -> None:
        if not hasattr(self, "stiffener_cad_preview") or not self._girder_details_tab:
            return
        active_id = self._active_member_id or self.girder_member_combo.currentText()
        m = re.match(r"^(G\d+)M\d+$", active_id)
        girder = m.group(1) if m else ""
        if not girder: return
        
        segments = self._segments_for_girder(girder)
        
        dims = {}
        dims_by_member = self._girder_state.get("section_dimensions_by_member")
        if isinstance(dims_by_member, dict):
            dims.update({str(key): value for key, value in dims_by_member.items()})
        elif hasattr(self._girder_details_tab, "get_member_section_dimensions"):
            for seg in segments:
                mid = seg.get("id")
                dims[mid] = self._girder_details_tab.get_member_section_dimensions(mid)

        self.stiffener_cad_preview.set_data(
            segments=segments,
            stiffener_by_member=self._state_by_member,
            active_member_id=active_id,
            section_dims_by_member=dims,
        )
        if self._active_member_id:
            self._update_outstand_fields(self._active_member_id)
