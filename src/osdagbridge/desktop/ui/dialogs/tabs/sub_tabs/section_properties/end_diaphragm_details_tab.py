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

# Reuse the same rolled section catalog that backs the Girder tab.
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.girder_details_tab import (  # noqa: E501
    girder_properties,
)

class EndDiaphragmDetailsTab(QWidget):
    """Tab for End Diaphragm Details with type-specific layouts"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._girder_details_tab = None
        self._select_girders_combos = []
        self._member_id_combos = []
        # Member ID is software-generated (E{pair}M1 / E{pair}M2).
        # Show both IDs as a read-only display; inputs apply to both ends.
        self._member_id_display_by_view: dict[str, QLineEdit] = {}

        # Keep all combo boxes strictly uniform in width.
        self._combo_width = 190

        # Persist UI state per (view_type, girder-pair, member-id).
        # Also sync selection (girder/member index) across all three views.
        self._selection_by_view: dict[str, tuple[QComboBox, QComboBox]] = {}
        self._state_by_view_member_key: dict[str, dict] = {}
        self._active_key_by_view: dict[str, str] = {}
        self._block_selection_sync = False
        # Cross bracing uses angle/channel section previews backed by the Osdag DB.
        self._cross_catalog = SectionCatalog()
        self._cross_previews = {}
        self.cross_right_column = None
        self.cross_design_combo = None
        self.cross_bracing_section_type_combo = None
        self.cross_bracing_section_combo = None
        self.cross_top_bracket_type_combo = None
        self.cross_top_bracket_size_combo = None
        self.cross_bottom_bracket_type_combo = None
        self.cross_bottom_bracket_size_combo = None
        self.cross_bracing_type_combo = None

        self._rolled_property_inputs = {}
        self._welded_property_inputs = {}
        self._rolled_preview = None
        self._welded_preview = None
        self._rolled_caption = None
        self._welded_caption = None

        self.rolled_design_combo = None
        self.welded_design_combo = None
        self._rolled_inputs = []
        self._welded_inputs = []
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
        if key == "Cross Bracing":
            angles = []
            try:
                angles = list(self._cross_catalog.list_angles() or [])
            except Exception:
                angles = []
            first_angle = angles[0] if angles else ""
            return {
                "design": "Optimized",
                "bracing_type": "K-Bracing",
                "bracing_section_type": "Angle",
                "bracing_section_data": first_angle,
                "bracing_section_text": "",
                "top_bracket_type": "Angle",
                "top_bracket_data": first_angle,
                "top_bracket_text": "",
                "bottom_bracket_type": "Angle",
                "bottom_bracket_data": first_angle,
                "bottom_bracket_text": "",
            }
        if key == "Rolled Beam":
            first = ""
            if self.rolled_is_section_combo is not None and self.rolled_is_section_combo.count() > 0:
                first = self.rolled_is_section_combo.itemText(0)
            return {
                "design": "Optimized",
                "is_section": first,
            }
        if key == "Welded Beam":
            return {
                "design": "Optimized",
                "welded_values": ["" for _ in (self._welded_inputs or [])],
            }
        return {"design": "Optimized"}

    def _snapshot_view_state(self, view_key: str) -> dict:
        key = (view_key or "").strip()
        if key == "Cross Bracing":
            return {
                "design": self.cross_design_combo.currentText() if self.cross_design_combo is not None else "",
                "bracing_type": self.cross_bracing_type_combo.currentText() if self.cross_bracing_type_combo is not None else "",
                "bracing_section_type": self.cross_bracing_section_type_combo.currentText() if self.cross_bracing_section_type_combo is not None else "",
                "bracing_section_data": self.cross_bracing_section_combo.currentData() if self.cross_bracing_section_combo is not None else None,
                "bracing_section_text": self.cross_bracing_section_combo.currentText() if self.cross_bracing_section_combo is not None else "",
                "top_bracket_type": self.cross_top_bracket_type_combo.currentText() if self.cross_top_bracket_type_combo is not None else "",
                "top_bracket_data": self.cross_top_bracket_size_combo.currentData() if self.cross_top_bracket_size_combo is not None else None,
                "top_bracket_text": self.cross_top_bracket_size_combo.currentText() if self.cross_top_bracket_size_combo is not None else "",
                "bottom_bracket_type": self.cross_bottom_bracket_type_combo.currentText() if self.cross_bottom_bracket_type_combo is not None else "",
                "bottom_bracket_data": self.cross_bottom_bracket_size_combo.currentData() if self.cross_bottom_bracket_size_combo is not None else None,
                "bottom_bracket_text": self.cross_bottom_bracket_size_combo.currentText() if self.cross_bottom_bracket_size_combo is not None else "",
            }
        if key == "Rolled Beam":
            return {
                "design": self.rolled_design_combo.currentText() if self.rolled_design_combo is not None else "",
                "is_section": self.rolled_is_section_combo.currentText() if self.rolled_is_section_combo is not None else "",
            }
        if key == "Welded Beam":
            values = []
            for widget in (self._welded_inputs or []):
                if isinstance(widget, QComboBox):
                    values.append(widget.currentText())
                elif isinstance(widget, QLineEdit):
                    values.append(widget.text())
                else:
                    values.append("")
            return {
                "design": self.welded_design_combo.currentText() if self.welded_design_combo is not None else "",
                "welded_values": values,
            }
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

    def _apply_view_state(self, view_key: str, state: dict) -> None:
        key = (view_key or "").strip()
        if key == "Cross Bracing":
            if self.cross_design_combo is not None:
                self.cross_design_combo.setCurrentText(state.get("design") or self.cross_design_combo.currentText())
            if self.cross_bracing_type_combo is not None:
                desired = (state.get("bracing_type") or "").strip()
                # Backward compatibility: older UI exposed Diagonal/Horizontal.
                if desired in {"Diagonal", "Horizontal"}:
                    desired = "X-Bracing"
                if desired and self.cross_bracing_type_combo.findText(desired) >= 0:
                    self.cross_bracing_type_combo.setCurrentText(desired)
                else:
                    # Keep current selection if desired isn't supported.
                    self.cross_bracing_type_combo.setCurrentText(self.cross_bracing_type_combo.currentText())

            if self.cross_bracing_section_type_combo is not None:
                self.cross_bracing_section_type_combo.setCurrentText(state.get("bracing_section_type") or self.cross_bracing_section_type_combo.currentText())
                self._cross_update_designations_for(self.cross_bracing_section_combo, self.cross_bracing_section_type_combo.currentText())
                self._set_combo_to_data_or_text(
                    self.cross_bracing_section_combo,
                    state.get("bracing_section_data"),
                    state.get("bracing_section_text") or "",
                )

            if self.cross_top_bracket_type_combo is not None:
                self.cross_top_bracket_type_combo.setCurrentText(state.get("top_bracket_type") or self.cross_top_bracket_type_combo.currentText())
                self._cross_update_designations_for(self.cross_top_bracket_size_combo, self.cross_top_bracket_type_combo.currentText())
                self._set_combo_to_data_or_text(
                    self.cross_top_bracket_size_combo,
                    state.get("top_bracket_data"),
                    state.get("top_bracket_text") or "",
                )

            if self.cross_bottom_bracket_type_combo is not None:
                self.cross_bottom_bracket_type_combo.setCurrentText(state.get("bottom_bracket_type") or self.cross_bottom_bracket_type_combo.currentText())
                self._cross_update_designations_for(self.cross_bottom_bracket_size_combo, self.cross_bottom_bracket_type_combo.currentText())
                self._set_combo_to_data_or_text(
                    self.cross_bottom_bracket_size_combo,
                    state.get("bottom_bracket_data"),
                    state.get("bottom_bracket_text") or "",
                )

            self._on_cross_design_changed(self.cross_design_combo.currentText() if self.cross_design_combo is not None else "")
            self._update_cross_previews()
            return

        if key == "Rolled Beam":
            if self.rolled_design_combo is not None:
                self.rolled_design_combo.setCurrentText(state.get("design") or self.rolled_design_combo.currentText())
            if self.rolled_is_section_combo is not None:
                desired = state.get("is_section") or ""
                if desired:
                    self.rolled_is_section_combo.setCurrentText(desired)
                elif self.rolled_is_section_combo.count() > 0:
                    self.rolled_is_section_combo.setCurrentIndex(0)
            self._on_rolled_design_changed(self.rolled_design_combo.currentText() if self.rolled_design_combo is not None else "")
            self._update_rolled_preview_and_props()
            return

        if key == "Welded Beam":
            if self.welded_design_combo is not None:
                self.welded_design_combo.setCurrentText(state.get("design") or self.welded_design_combo.currentText())
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
            self._on_welded_design_changed(self.welded_design_combo.currentText() if self.welded_design_combo is not None else "")
            self._update_welded_preview_and_props()
            return

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
        return (combo.currentText() or "").strip() == "Optimized"

    def _design_combo_for_type(self, view_type: str | None) -> QComboBox | None:
        key = (view_type or "").strip()
        if key == "Cross Bracing":
            return self.cross_design_combo
        if key == "Rolled Beam":
            return self.rolled_design_combo
        if key == "Welded Beam":
            return self.welded_design_combo
        return None

    def _apply_rolled_custom_mode(self, is_custom: bool) -> None:
        for widget in self._rolled_inputs:
            if widget is not None:
                widget.setEnabled(is_custom)

    def _on_rolled_design_changed(self, label: str) -> None:
        is_custom = (label or "").strip() == "Customized"
        self._apply_rolled_custom_mode(is_custom)

    def _apply_welded_custom_mode(self, is_custom: bool) -> None:
        for widget in self._welded_inputs:
            if widget is not None:
                widget.setEnabled(is_custom)
        self._update_welded_thickness_value_enabled_state()

    def _on_welded_design_changed(self, label: str) -> None:
        is_custom = (label or "").strip() == "Customized"
        self._apply_welded_custom_mode(is_custom)

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

        self.type_stack = QStackedWidget()
        container_layout.addWidget(self.type_stack)

        self.views = {}
        self.view_order = []
        self.type_selector_map = {}
        self.type_selectors = []
        self.current_type = None
        self.block_type_sync = False

        cross_view, cross_selector = self._build_cross_bracing_view()
        self._add_type_view("Cross Bracing", cross_view, cross_selector)
        rolled_view, rolled_selector = self._build_rolled_view()
        self._add_type_view("Rolled Beam", rolled_view, rolled_selector)
        welded_view, welded_selector = self._build_welded_view()
        self._add_type_view("Welded Beam", welded_view, welded_selector)

        self._set_current_type("Cross Bracing")

        # Now that all views/widgets exist, restore saved/default state for the
        # current (girder, member) selection across all views.
        self._restore_all_views_for_current_selection()

    def _add_type_view(self, key, widget, type_selector):
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

    def _create_heading_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 12px; font-weight: 700; color: #4b4b4b; border: none; padding: 0px; margin: 0px;")
        return label

    def _create_label(self, text):
        label = QLabel(text)
        # Keep default label styling, but emphasize the bracing type selector.
        weight = "700" if (text or "").strip() == "Type of Bracing:" else "400"
        label.setStyleSheet(f"font-size: 11px; font-weight: {weight}; color: #4b4b4b; border: none;")
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
        layout.addWidget(widget, row, 1)
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

    def _is_custom_thickness_mode(self, combo: QComboBox | None) -> bool:
        if combo is None:
            return False
        return (combo.currentText() or "").strip().lower() == "custom"

    def _update_welded_thickness_value_enabled_state(self) -> None:
        is_custom_design = (self.welded_design_combo.currentText() or "").strip() == "Customized" if self.welded_design_combo else False

        for mode_combo, value_input in (
            (getattr(self, "welded_web_thickness_combo", None), getattr(self, "welded_web_thickness_value", None)),
            (getattr(self, "welded_top_thickness_combo", None), getattr(self, "welded_top_thickness_value", None)),
            (getattr(self, "welded_bottom_thickness_combo", None), getattr(self, "welded_bottom_thickness_value", None)),
        ):
            if mode_combo is None or value_input is None:
                continue

            show_value = bool(is_custom_design and self._is_custom_thickness_mode(mode_combo))
            value_input.setVisible(show_value)
            value_input.setEnabled(show_value)

            try:
                total_width = int(getattr(self, "_combo_width", 190))
                if show_value:
                    mode_combo.setFixedWidth(max(96, total_width - 84))
                    value_input.setFixedWidth(78)
                else:
                    mode_combo.setFixedWidth(total_width)
            except Exception:
                pass

    def _create_selection_box(self, view_key: str):
        box = self._create_inner_box()
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QGridLayout(box)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(8)
        layout.setColumnMinimumWidth(0, 120)
        layout.setColumnStretch(1, 1)

        girders_combo = QComboBox()
        # Populated from Girder Details when bound. (No All option.)
        self._configure_combo_box(girders_combo)
        apply_field_style(girders_combo)
        layout.addWidget(self._create_label("Select Girders:"), 0, 0)
        layout.addWidget(girders_combo, 0, 1)

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
        try:
            member_display.setFixedWidth(int(getattr(self, "_combo_width", 190)))
        except Exception:
            pass
        layout.addWidget(self._create_label("Member ID:"), 1, 0)
        layout.addWidget(member_display, 1, 1)

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
        current_view = str(self.current_type or "").strip() or "Cross Bracing"
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
        combos = self._selection_by_view.get(str(self.current_type or "Cross Bracing"))
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
                    self._rebuild_member_ids_for_view(str(self.current_type or "Cross Bracing"), previous_member=target_member)
                    try:
                        self._refresh_member_id_display(str(self.current_type or "Cross Bracing"))
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
            "Mass, M (Kg/m)",
            "Sectional Area, a (cm2)",
            "2nd Moment of Area, Iz (cm4)",
            "2nd Moment of Area, Iy (cm4)",
            "Radius of Gyration, rz (cm)",
            "Radius of Gyration, ry (cm)",
            "Elastic Modulus, Zz (cm3)",
            "Elastic Modulus, Zy (cm3)",
            "Plastic Modulus, Zuz (cm3)",
            "Plastic Modulus, Zuy (cm3)"
        ]

        inputs = {}
        for row, name in enumerate(properties):
            label = self._create_label(name)
            field = self._create_line_edit()
            field.setReadOnly(True)
            grid.addWidget(label, row, 0)
            grid.addWidget(field, row, 1)
            inputs[name] = field

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
        self._cross_fill_combo(self.cross_top_bracket_size_combo, angles, "angle")
        self._cross_fill_combo(self.cross_bottom_bracket_size_combo, angles, "angle")

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

        is_custom = self.cross_design_combo.currentText() == "Customized"
        if not is_custom:
            for widget in self._cross_previews.values():
                widget.set_section("", "")
            return

        self._cross_set_preview(
            "bracing",
            self.cross_bracing_section_type_combo,
            self.cross_bracing_section_combo,
        )
        self._cross_set_preview(
            "top",
            self.cross_top_bracket_type_combo,
            self.cross_top_bracket_size_combo,
        )
        self._cross_set_preview(
            "bottom",
            self.cross_bottom_bracket_type_combo,
            self.cross_bottom_bracket_size_combo,
        )

    def _apply_cross_custom_mode(self, is_custom: bool) -> None:
        # Keep preview/diagram column visible even in Optimized mode.
        if self.cross_right_column is not None:
            self.cross_right_column.setVisible(True)
        for widget in (
            self.cross_bracing_section_type_combo,
            self.cross_bracing_section_combo,
            self.cross_top_bracket_type_combo,
            self.cross_top_bracket_size_combo,
            self.cross_bottom_bracket_type_combo,
            self.cross_bottom_bracket_size_combo,
        ):
            if widget is not None:
                widget.setEnabled(is_custom)

    def _on_cross_design_changed(self, label: str) -> None:
        is_custom = (label or "").strip() == "Customized"
        self._apply_cross_custom_mode(is_custom)
        self._update_cross_previews()

    # ---- View builders ----
    def _build_cross_bracing_view(self):
        view = self._create_card_frame()
        layout = QHBoxLayout(view)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)
        left_layout.addWidget(self._create_selection_box("Cross Bracing"))

        inputs_box = self._create_inner_box()
        inputs_layout = QVBoxLayout(inputs_box)
        inputs_layout.setContentsMargins(12, 4, 12, 8)
        inputs_layout.setSpacing(6)
        title = self._create_heading_label("Section Inputs:")
        title.setStyleSheet("font-size: 12px; font-weight: 700; color: #4b4b4b; border: none; margin-top: 0px; margin-bottom: 2px;")
        inputs_layout.addWidget(title)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 130)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        design_combo = QComboBox()
        design_combo.addItems(["Customized", "Optimized"])
        if design_combo.count() > 1:
            design_combo.setCurrentIndex(1)  # Default to Optimized
        self._configure_combo_box(design_combo)
        apply_field_style(design_combo)
        row = self._add_grid_row(grid, 0, "Design:", design_combo)
        self.cross_design_combo = design_combo

        type_selector = QComboBox()
        type_selector.addItems(VALUES_END_DIAPHRAGM_TYPE)
        type_selector.setCurrentText("Cross Bracing")
        self._configure_combo_box(type_selector)
        apply_field_style(type_selector)
        row = self._add_grid_row(grid, row, "Type:", type_selector)

        bracing_combo = QComboBox()
        # Keep consistent with the standalone Cross Bracing tab.
        bracing_combo.addItems(["K-Bracing", "X-Bracing"])
        self._configure_combo_box(bracing_combo)
        apply_field_style(bracing_combo)
        row = self._add_grid_row(grid, row, "Type of Bracing:", bracing_combo)
        self.cross_bracing_type_combo = bracing_combo

        section_type_options = [
            "Angle",
            "Double Angle (Long Leg)",
            "Double Angle (Short Leg)",
            "Channel",
            "Double Channel",
        ]

        bracing_section_type = QComboBox()
        bracing_section_type.addItems(section_type_options)
        self._configure_combo_box(bracing_section_type)
        apply_field_style(bracing_section_type)
        row = self._add_grid_row(grid, row, "Bracing Section Type:", bracing_section_type)
        self.cross_bracing_section_type_combo = bracing_section_type

        bracing_section_size = QComboBox()
        self._configure_combo_box(bracing_section_size)
        apply_field_style(bracing_section_size)
        row = self._add_grid_row(grid, row, "Bracing Section:", bracing_section_size)
        self.cross_bracing_section_combo = bracing_section_size

        top_bracket_type = QComboBox()
        top_bracket_type.addItems(section_type_options)
        self._configure_combo_box(top_bracket_type)
        apply_field_style(top_bracket_type)
        row = self._add_grid_row(grid, row, "Top Bracket Section:", top_bracket_type)
        self.cross_top_bracket_type_combo = top_bracket_type

        top_bracket_size = QComboBox()
        self._configure_combo_box(top_bracket_size)
        apply_field_style(top_bracket_size)
        row = self._add_grid_row(grid, row, "Top Bracket Size:", top_bracket_size)
        self.cross_top_bracket_size_combo = top_bracket_size

        bottom_bracket_type = QComboBox()
        bottom_bracket_type.addItems(section_type_options)
        self._configure_combo_box(bottom_bracket_type)
        apply_field_style(bottom_bracket_type)
        row = self._add_grid_row(grid, row, "Bottom Bracket Section:", bottom_bracket_type)
        self.cross_bottom_bracket_type_combo = bottom_bracket_type

        bottom_bracket_size = QComboBox()
        self._configure_combo_box(bottom_bracket_size)
        apply_field_style(bottom_bracket_size)
        row = self._add_grid_row(grid, row, "Bottom Bracket Size:", bottom_bracket_size)
        self.cross_bottom_bracket_size_combo = bottom_bracket_size

        inputs_layout.addLayout(grid)
        inputs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        left_layout.addWidget(inputs_box)
        left_layout.addStretch()

        layout.addWidget(left_column)

        right_column = QWidget()
        self.cross_right_column = right_column
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        type_box = self._create_inner_box()
        type_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        type_layout = QVBoxLayout(type_box)
        type_layout.setContentsMargins(12, 8, 12, 10)
        type_layout.setSpacing(6)
        type_layout.addWidget(self._create_heading_label("Type of Bracing"))
        type_layout.addWidget(self._create_image_placeholder("Bracing Layout", 170))
        right_layout.addWidget(type_box)

        for key, title in [("bracing", "Bracing"), ("top", "Top Bracket"), ("bottom", "Bottom Bracket")]:
            preview_box = self._create_inner_box()
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
        layout.setStretch(0, 3)
        layout.setStretch(1, 4)

        # Wire up dynamic designations + previews (same logic as CrossBracingDetailsTab).
        design_combo.currentTextChanged.connect(self._on_cross_design_changed)

        bracing_section_type.currentTextChanged.connect(
            lambda label: (self._cross_update_designations_for(bracing_section_size, label), self._update_cross_previews())
        )
        bracing_section_size.currentTextChanged.connect(self._update_cross_previews)

        top_bracket_type.currentTextChanged.connect(
            lambda label: (self._cross_update_designations_for(top_bracket_size, label), self._update_cross_previews())
        )
        top_bracket_size.currentTextChanged.connect(self._update_cross_previews)

        bottom_bracket_type.currentTextChanged.connect(
            lambda label: (self._cross_update_designations_for(bottom_bracket_size, label), self._update_cross_previews())
        )
        bottom_bracket_size.currentTextChanged.connect(self._update_cross_previews)

        self._cross_populate_designations()
        self._on_cross_design_changed(design_combo.currentText())
        return view, type_selector

    def _build_rolled_view(self):
        view = self._create_card_frame()
        layout = QHBoxLayout(view)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.addWidget(self._create_selection_box("Rolled Beam"))

        inputs_box = self._create_inner_box()
        inputs_layout = QVBoxLayout(inputs_box)
        inputs_layout.setContentsMargins(12, 4, 12, 8)
        inputs_layout.setSpacing(6)
        title = self._create_heading_label("Section Inputs")
        title.setStyleSheet("font-size: 12px; font-weight: 600; color: #4b4b4b; border: none; margin-top: 0px; margin-bottom: 2px;")
        inputs_layout.addWidget(title)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnMinimumWidth(0, 130)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        design_combo = QComboBox()
        design_combo.addItems(["Customized", "Optimized"])
        if design_combo.count() > 1:
            design_combo.setCurrentIndex(1)  # Default to Optimized
        self.rolled_design_combo = design_combo
        self._configure_combo_box(design_combo)
        apply_field_style(design_combo)
        row = self._add_grid_row(grid, 0, "Design:", design_combo)

        type_selector = QComboBox()
        type_selector.addItems(VALUES_END_DIAPHRAGM_TYPE)
        type_selector.setCurrentText("Rolled Beam")
        self._configure_combo_box(type_selector)
        apply_field_style(type_selector)
        row = self._add_grid_row(grid, row, "Type:", type_selector)

        is_section_combo = QComboBox()
        self._configure_combo_box(is_section_combo)
        apply_field_style(is_section_combo)
        self._populate_rolled_sections(is_section_combo)
        self._add_grid_row(grid, row, "IS Section:", is_section_combo)
        self.rolled_is_section_combo = is_section_combo
        self._rolled_inputs = [is_section_combo]

        inputs_layout.addLayout(grid)
        inputs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        left_layout.addWidget(inputs_box)
        left_layout.addStretch()
        layout.addWidget(left_column)

        right_column = QWidget()
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

        design_combo.currentTextChanged.connect(self._on_rolled_design_changed)
        is_section_combo.currentTextChanged.connect(self._update_rolled_preview_and_props)
        self._update_rolled_preview_and_props()
        self._on_rolled_design_changed(design_combo.currentText())
        return view, type_selector

    def _build_welded_view(self):
        view = self._create_card_frame()
        layout = QHBoxLayout(view)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.addWidget(self._create_selection_box("Welded Beam"))

        inputs_box = self._create_inner_box()
        inputs_layout = QVBoxLayout(inputs_box)
        inputs_layout.setContentsMargins(12, 8, 12, 10)
        inputs_layout.setSpacing(8)
        inputs_layout.addWidget(self._create_heading_label("Section Inputs:"))

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 150)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        design_combo = QComboBox()
        design_combo.addItems(["Customized", "Optimized"])
        if design_combo.count() > 1:
            design_combo.setCurrentIndex(1)  # Default to Optimized
        self.welded_design_combo = design_combo
        self._configure_combo_box(design_combo)
        apply_field_style(design_combo)
        row = self._add_grid_row(grid, 0, "Design:", design_combo)

        type_selector = QComboBox()
        type_selector.addItems(VALUES_END_DIAPHRAGM_TYPE)
        type_selector.setCurrentText("Welded Beam")
        self._configure_combo_box(type_selector)
        apply_field_style(type_selector)
        row = self._add_grid_row(grid, row, "Type:", type_selector)

        symmetry_combo = QComboBox()
        symmetry_combo.addItems(["Girder Symmetric", "Girder Unsymmetric"])
        self._configure_combo_box(symmetry_combo)
        apply_field_style(symmetry_combo)
        row = self._add_grid_row(grid, row, "Symmetry:", symmetry_combo)

        total_depth = self._create_line_edit()
        total_depth.setValidator(QDoubleValidator(0, 1_000_000, 3))
        try:
            total_depth.setFixedWidth(int(getattr(self, "_combo_width", 190)))
            total_depth.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        except Exception:
            pass
        row = self._add_grid_row(grid, row, "Total Depth (mm):", total_depth)
        self.welded_total_depth = total_depth

        web_thick_combo = QComboBox()
        web_thick_combo.addItems(VALUES_PROFILE_SCOPE if "VALUES_PROFILE_SCOPE" in globals() else ["All", "Custom"])
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
        row = self._add_grid_row(grid, row, "Web Thickness (mm):", web_thick_widget)
        self.welded_web_thickness_combo = web_thick_combo
        self.welded_web_thickness_value = web_thick_value

        top_width = self._create_line_edit()
        top_width.setValidator(QDoubleValidator(0, 1_000_000, 3))
        try:
            top_width.setFixedWidth(int(getattr(self, "_combo_width", 190)))
            top_width.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        except Exception:
            pass
        row = self._add_grid_row(grid, row, "Width of Top Flange (mm):", top_width)
        self.welded_top_width = top_width

        top_thickness_combo = QComboBox()
        top_thickness_combo.addItems(VALUES_PROFILE_SCOPE if "VALUES_PROFILE_SCOPE" in globals() else ["All", "Custom"])
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
        row = self._add_grid_row(grid, row, "Top Flange Thickness (mm):", top_thickness_widget)
        self.welded_top_thickness_combo = top_thickness_combo
        self.welded_top_thickness_value = top_thickness_value

        bottom_width = self._create_line_edit()
        bottom_width.setValidator(QDoubleValidator(0, 1_000_000, 3))
        try:
            bottom_width.setFixedWidth(int(getattr(self, "_combo_width", 190)))
            bottom_width.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        except Exception:
            pass
        row = self._add_grid_row(grid, row, "Width of Bottom Flange (mm):", bottom_width)
        self.welded_bottom_width = bottom_width

        bottom_thickness_combo = QComboBox()
        bottom_thickness_combo.addItems(VALUES_PROFILE_SCOPE if "VALUES_PROFILE_SCOPE" in globals() else ["All", "Custom"])
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
        row = self._add_grid_row(grid, row, "Bottom Flange Thickness (mm):", bottom_thickness_widget)
        self.welded_bottom_thickness_combo = bottom_thickness_combo
        self.welded_bottom_thickness_value = bottom_thickness_value

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
        inputs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        left_layout.addWidget(inputs_box)
        left_layout.addStretch()
        layout.addWidget(left_column)

        right_column = QWidget()
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

        design_combo.currentTextChanged.connect(self._on_welded_design_changed)
        for watcher in (total_depth, top_width, bottom_width):
            watcher.textChanged.connect(self._update_welded_preview_and_props)
        for watcher in (web_thick_value, top_thickness_value, bottom_thickness_value):
            watcher.textChanged.connect(self._update_welded_preview_and_props)
        for combo in (web_thick_combo, top_thickness_combo, bottom_thickness_combo):
            combo.currentTextChanged.connect(lambda _t: self._update_welded_thickness_value_enabled_state())
            combo.currentTextChanged.connect(self._update_welded_preview_and_props)
        self._update_welded_preview_and_props()
        self._on_welded_design_changed(design_combo.currentText())
        self._update_welded_thickness_value_enabled_state()
        return view, type_selector

    def _handle_type_selection(self, value):
        if self.block_type_sync:
            return
        if value in self.view_order:
            self._set_current_type(value)

    def _set_current_type(self, target):
        if target not in self.view_order:
            return
        if self.current_type == target:
            return

        previous_type = self.current_type
        previous_was_optimized = self._is_optimized(self._design_combo_for_type(previous_type))

        self.current_type = target
        index = self.view_order.index(target)
        self.type_stack.setCurrentIndex(index)
        self.block_type_sync = True
        for selector in self.type_selectors:
            selector.setCurrentText(target)
        self.block_type_sync = False

        # If the user was in Optimized mode, keep Optimized when switching types.
        if previous_was_optimized:
            next_design_combo = self._design_combo_for_type(target)
            if next_design_combo is not None:
                next_design_combo.setCurrentText("Optimized")

        # Ensure enabled/disabled state matches the selected design for the active view.
        if target == "Cross Bracing" and self.cross_design_combo is not None:
            self._on_cross_design_changed(self.cross_design_combo.currentText())
        elif target == "Rolled Beam" and self.rolled_design_combo is not None:
            self._on_rolled_design_changed(self.rolled_design_combo.currentText())
        elif target == "Welded Beam" and self.welded_design_combo is not None:
            self._on_welded_design_changed(self.welded_design_combo.currentText())

        # Refresh preview/properties for the active view.
        if target == "Cross Bracing":
            self._update_cross_previews()
        elif target == "Rolled Beam":
            self._update_rolled_preview_and_props()
        elif target == "Welded Beam":
            self._update_welded_preview_and_props()

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
            self._set_current_type("Cross Bracing")
        except Exception:
            pass

        # Apply default view state for current selection.
        try:
            self._restore_all_views_for_current_selection()
        except Exception:
            pass

