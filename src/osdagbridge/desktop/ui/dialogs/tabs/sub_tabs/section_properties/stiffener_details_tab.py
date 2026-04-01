"""Stiffener Details tab.

This tab is part of Member Properties (Section Properties) and stores inputs per girder member.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIntValidator, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import STIFFENER_DETAILS_SCHEMA
from osdagbridge.core.utils.common import (
    MIN_BEARING_STIFFENER_SPACING_MM,
    SAIL_APPROVED_THICKNESS_VALUES,
    STIFFENER_DETAILS_DEFAULTS,
)
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style

_STIFFENER_DEFAULTS = dict(STIFFENER_DETAILS_DEFAULTS)
MIN_BEARING_SPACING_MM = int(_STIFFENER_DEFAULTS.get("min_bearing_spacing_mm", MIN_BEARING_STIFFENER_SPACING_MM))


class StiffenerCadPreviewWidget(QWidget):
    """2D CAD-style stiffener preview driven by per-member stiffener inputs."""

    # Keep preview colors aligned with the desktop theme palette.
    THEME_BG = QColor("#f4f4f4")
    THEME_BORDER = QColor("#d0d0d0")
    THEME_TEXT = QColor("#333333")
    THEME_CANVAS = QColor("#f8f8f8")
    THEME_GIRDER = QColor("#d9d9d9")
    THEME_FLANGE = QColor("#c9c9c9")
    THEME_WEB = QColor("#dcdcdc")
    THEME_GIRDER_BORDER = QColor("#3a3a3a")
    THEME_SEGMENT_LINE = QColor("#888888")
    BEARING_COLOR = QColor("#90AF13")
    INTERMEDIATE_COLOR = QColor("#6B7D20")
    LONG_COLOR = QColor("#4a4a4a")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._segments: List[dict] = []
        self._stiffener_by_member: Dict[str, dict] = {}
        self._section_dims_by_member: Dict[str, dict] = {}
        self._active_member_id: str = ""
        self.setMinimumHeight(210)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_data(
        self,
        segments: List[dict],
        stiffener_by_member: Dict[str, dict],
        active_member_id: str,
        section_dims_by_member: Optional[Dict[str, dict]] = None,
    ) -> None:
        cleaned: List[dict] = []
        for seg in segments or []:
            try:
                start = float(seg.get("start", 0.0))
                end = float(seg.get("end", 0.0))
            except Exception:
                continue
            length = max(0.0, end - start)
            if length <= 0.0:
                continue
            cleaned.append(
                {
                    "id": str(seg.get("id") or ""),
                    "start": start,
                    "end": end,
                    "length": length,
                }
            )
        self._segments = cleaned
        self._stiffener_by_member = dict(stiffener_by_member or {})
        self._section_dims_by_member = dict(section_dims_by_member or {})
        self._active_member_id = str(active_member_id or "").strip()
        self.update()

    @staticmethod
    def _member_girder(member_id: str) -> str:
        match = re.match(r"^(G\d+)M\d+$", str(member_id or "").strip())
        return match.group(1) if match else ""

    def _state_for(self, member_id: str) -> dict:
        return dict(self._stiffener_by_member.get(str(member_id or "").strip()) or {})

    def _dims_for(self, member_id: str) -> dict:
        return dict(self._section_dims_by_member.get(str(member_id or "").strip()) or {})

    def _parse_positive_int(self, value) -> Optional[int]:
        try:
            text = str(value or "").strip()
            if not text.isdigit():
                return None
            parsed = int(text)
            return parsed if parsed > 0 else None
        except Exception:
            return None

    def _longitudinal_levels(self, mode: str, web_top: float, web_height: float) -> List[float]:
        text = str(mode or "").strip().lower()
        if "2" in text:
            return [web_top + (web_height / 3.0), web_top + (2.0 * web_height / 3.0)]
        if "1" in text:
            return [web_top + (web_height / 3.0)]
        return []

    def paintEvent(self, _event):  # noqa: N802 (Qt naming)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        frame = self.rect().adjusted(6, 6, -6, -6)
        painter.fillRect(frame, self.THEME_BG)
        painter.setPen(QPen(self.THEME_BORDER, 1.0))
        painter.drawRect(frame)

        draw = frame.adjusted(14, 6, -14, -24)
        if draw.width() < 20 or draw.height() < 20:
            return

        if not self._segments:
            painter.setPen(QPen(self.THEME_TEXT, 1.0))
            painter.drawText(draw, Qt.AlignCenter, "No member segments")
            return

        total_length = sum(float(seg.get("length") or 0.0) for seg in self._segments)
        if total_length <= 0.0:
            painter.setPen(QPen(self.THEME_TEXT, 1.0))
            painter.drawText(draw, Qt.AlignCenter, "Invalid segment lengths")
            return

        # Girder strip inside a light themed canvas.
        cad_bg = draw.adjusted(0, 14, 0, -8)
        painter.fillRect(cad_bg, self.THEME_CANVAS)

        girder_rect = cad_bg.adjusted(14, 18, -14, -18)
        painter.fillRect(girder_rect, self.THEME_GIRDER)

        # Draw separate top and bottom flange thickness bands similar to girder CAD.
        active_dims = self._dims_for(self._active_member_id)
        try:
            depth_mm = float(active_dims.get("depth_mm") or 0.0)
            top_t_mm = float(active_dims.get("top_flange_thickness_mm") or 0.0)
            bot_t_mm = float(active_dims.get("bottom_flange_thickness_mm") or 0.0)
        except (TypeError, ValueError):
            depth_mm = 0.0
            top_t_mm = 0.0
            bot_t_mm = 0.0

        if depth_mm > 0.0 and top_t_mm > 0.0 and bot_t_mm > 0.0:
            top_flange_px = int(round((top_t_mm / depth_mm) * girder_rect.height()))
            bottom_flange_px = int(round((bot_t_mm / depth_mm) * girder_rect.height()))
        else:
            # Fallback for missing dimensions.
            top_flange_px = max(4, int(round(girder_rect.height() * 0.08)))
            bottom_flange_px = max(4, int(round(girder_rect.height() * 0.08)))

        # Keep a workable web region even with very thick flanges.
        max_each = max(4, int(round(girder_rect.height() * 0.22)))
        top_flange_px = min(max_each, max(3, top_flange_px))
        bottom_flange_px = min(max_each, max(3, bottom_flange_px))
        if top_flange_px + bottom_flange_px > girder_rect.height() - 8:
            overflow = (top_flange_px + bottom_flange_px) - (girder_rect.height() - 8)
            reduce_top = overflow // 2
            reduce_bottom = overflow - reduce_top
            top_flange_px = max(3, top_flange_px - reduce_top)
            bottom_flange_px = max(3, bottom_flange_px - reduce_bottom)

        flange_x = int(girder_rect.left())
        flange_w = int(girder_rect.width())
        top_flange_y = int(girder_rect.top())
        bottom_flange_y = int(girder_rect.bottom() - bottom_flange_px + 1)

        painter.fillRect(flange_x, top_flange_y, flange_w, int(top_flange_px), self.THEME_FLANGE)
        painter.fillRect(flange_x, bottom_flange_y, flange_w, int(bottom_flange_px), self.THEME_FLANGE)

        web_top = girder_rect.top() + top_flange_px
        web_bottom = girder_rect.bottom() - bottom_flange_px
        if web_bottom < web_top:
            web_bottom = web_top

        painter.fillRect(
            int(girder_rect.left()),
            int(web_top),
            int(girder_rect.width()),
            int(max(1, web_bottom - web_top + 1)),
            self.THEME_WEB,
        )

        painter.setPen(QPen(self.THEME_GIRDER_BORDER, 1.0))
        painter.drawRect(girder_rect)
        painter.drawLine(int(girder_rect.left()), int(web_top), int(girder_rect.right()), int(web_top))
        painter.drawLine(int(girder_rect.left()), int(web_bottom), int(girder_rect.right()), int(web_bottom))

        web_height = max(1.0, web_bottom - web_top)

        # Resolve selected girder from active member (fallback to first segment's girder).
        active_girder = self._member_girder(self._active_member_id)
        if not active_girder and self._segments:
            active_girder = self._member_girder(str(self._segments[0].get("id") or ""))

        px_per_mm = girder_rect.width() / max(1.0, total_length * 1000.0)

        def resolve_bearing_params(seg_state: dict, seg_len_mm: float) -> tuple[int, float, float, float]:
            count = self._parse_positive_int(seg_state.get("bearing_stiffeners_each_end")) or 2
            count = max(1, min(8, count))
            custom_spacing_mm = self._parse_positive_int(seg_state.get("bearing_spacing_mm"))
            if custom_spacing_mm:
                spacing_mm = float(custom_spacing_mm)
            else:
                spacing_mm = max(MIN_BEARING_SPACING_MM, seg_len_mm / float(count + 1))
            spacing_px = max(8.0, min(24.0, spacing_mm * px_per_mm))
            edge_offset = spacing_px
            bearing_zone = edge_offset + ((count - 1) * spacing_px) + 6.0
            return count, spacing_px, edge_offset, bearing_zone

        x = float(girder_rect.left())
        segment_rects: List[dict] = []
        for idx, seg in enumerate(self._segments):
            ratio = float(seg["length"]) / total_length
            width = girder_rect.width() * ratio
            if idx == len(self._segments) - 1:
                width = max(1.0, float(girder_rect.right()) - x)
            segment_rects.append({"id": seg["id"], "left": x, "right": x + width})
            x += width

        # Draw segment labels close to the girder for better visual association.
        label_gap = 4
        label_height = 20
        label_bottom = int(max(draw.top() + label_height, girder_rect.top() - label_gap))
        label_top = int(max(draw.top(), label_bottom - label_height))
        for idx, seg_rect in enumerate(segment_rects):
            left = float(seg_rect["left"])
            right = float(seg_rect["right"])
            label_rect = draw.adjusted(0, 0, 0, 0)
            label_rect.setTop(label_top)
            label_rect.setBottom(label_bottom)
            label_rect.setLeft(int(left))
            label_rect.setRight(int(right))

            seg_id = str(seg_rect["id"] or "")
            painter.setPen(QPen(self.THEME_TEXT, 1.0))
            painter.drawText(label_rect, Qt.AlignHCenter | Qt.AlignVCenter, seg_id)

            if idx > 0:
                painter.setPen(QPen(self.THEME_SEGMENT_LINE, 1.0))
                painter.drawLine(int(left), int(girder_rect.top()), int(left), int(girder_rect.bottom()))

        # Draw per-segment stiffeners.
        for idx, seg_rect in enumerate(segment_rects):
            seg_id = str(seg_rect["id"] or "")
            seg_state = self._state_for(seg_id)
            left = float(seg_rect["left"])
            right = float(seg_rect["right"])
            width = max(1.0, right - left)
            is_first = idx == 0
            is_last = idx == len(segment_rects) - 1

            seg_len_mm = float(self._segments[idx]["length"]) * 1000.0
            left_count = right_count = 0
            left_spacing_px = right_spacing_px = 0.0
            left_offset = right_offset = 0.0
            left_zone = right_zone = 0.0
            if is_first:
                left_count, left_spacing_px, left_offset, left_zone = resolve_bearing_params(seg_state, seg_len_mm)
            if is_last:
                right_count, right_spacing_px, right_offset, right_zone = resolve_bearing_params(seg_state, seg_len_mm)

            seg_girder = self._member_girder(seg_id)
            if active_girder and seg_girder and seg_girder != active_girder:
                continue

            # Intermediate stiffeners between segment ends as per segment-wise spacing.
            include_intermediate = str(seg_state.get("intermediate_stiffener") or "").strip() == "Yes"
            spacing_mm = self._parse_positive_int(seg_state.get("intermediate_spacing_mm"))
            if include_intermediate and spacing_mm and float(self._segments[idx]["length"]) > 0.0:
                seg_len_mm = float(self._segments[idx]["length"]) * 1000.0
                if seg_len_mm > spacing_mm:
                    painter.setPen(QPen(self.INTERMEDIATE_COLOR, 2.0))
                    pos_mm = float(spacing_mm)
                    while pos_mm < seg_len_mm:
                        ratio = pos_mm / seg_len_mm
                        x_pos = left + (ratio * width)
                        if is_first and x_pos <= (left + left_zone):
                            pos_mm += float(spacing_mm)
                            continue
                        if is_last and x_pos >= (right - right_zone):
                            pos_mm += float(spacing_mm)
                            continue
                        if (x_pos - left) > 3.0 and (right - x_pos) > 3.0:
                            painter.drawLine(int(x_pos), int(web_top), int(x_pos), int(web_bottom))
                        pos_mm += float(spacing_mm)

            # Bearing stiffeners only at first and last member of the selected girder.
            # Draw these after intermediate lines so bearing stiffeners remain visible.
            painter.setPen(QPen(self.BEARING_COLOR, 2.0))
            if is_first and left_count > 0:
                for i in range(left_count):
                    x_pos = left + left_offset + (i * left_spacing_px)
                    x_pos = max(left + 2.0, min(right - 2.0, x_pos))
                    painter.drawLine(int(x_pos), int(web_top), int(x_pos), int(web_bottom))
            if is_last and right_count > 0:
                for i in range(right_count):
                    x_pos = right - right_offset - (i * right_spacing_px)
                    x_pos = max(left + 2.0, min(right - 2.0, x_pos))
                    painter.drawLine(int(x_pos), int(web_top), int(x_pos), int(web_bottom))

            # Longitudinal stiffeners by option: none / one at 1/3 / two at 1/3 and 2/3 from top.
            long_mode = str(seg_state.get("longitudinal_stiffener") or "")
            levels = self._longitudinal_levels(long_mode, web_top, web_height)
            if levels:
                painter.setPen(QPen(self.LONG_COLOR, 3.0))
                for y_pos in levels:
                    painter.drawLine(int(left), int(y_pos), int(right), int(y_pos))

class StiffenerDetailsTab(QWidget):
    """Tab for Stiffener Details with compact layout"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._defaults = dict(STIFFENER_DETAILS_DEFAULTS)
        self._combo_width = int(self._defaults.get("combo_width", 190) or 190)
        self._form_label_width = int(self._defaults.get("form_label_width", 245) or 245)
        self._thickness_values = self._schema_thickness_values()
        self._schema_state_bindings_cache: Optional[list[dict]] = None
        self._girder_details_tab = None
        self._state_by_member: Dict[str, dict] = {}
        self._active_member_id: Optional[str] = None
        self._is_loading_ui: bool = False
        self.init_ui()

    def _schema_field(self, field_id: str, section: str = "stiffener_inputs") -> dict:
        for field in STIFFENER_DETAILS_SCHEMA.get(section, []):
            if str(field.get("id")) == field_id:
                return dict(field)
        return {}

    def _schema_choices(self, field_id: str, section: str = "stiffener_inputs") -> list[str]:
        field = self._schema_field(field_id, section)
        return [str(choice) for choice in field.get("choices") or []]

    def _schema_label(self, field_id: str, section: str = "stiffener_inputs", fallback: str = "") -> str:
        field = self._schema_field(field_id, section)
        return str(field.get("label") or fallback)

    def _schema_thickness_values(self) -> list[str]:
        return [str(v).strip() for v in SAIL_APPROVED_THICKNESS_VALUES if str(v).strip()]

    def _schema_default(self, key: str, fallback: str = "") -> str:
        return str(self._defaults.get(key, fallback))

    def _schema_fields(self, section: str) -> list[dict]:
        return [dict(field) for field in STIFFENER_DETAILS_SCHEMA.get(section, []) if isinstance(field, dict)]

    def _schema_state_bindings(self) -> list[dict]:
        if self._schema_state_bindings_cache is not None:
            return [dict(entry) for entry in self._schema_state_bindings_cache]

        bindings: list[dict] = []
        for section in ("stiffener_inputs", "web_buckling_inputs"):
            for field in self._schema_fields(section):
                field_id = str(field.get("id") or "").strip()
                if not field_id:
                    continue

                field_type = str(field.get("type") or "").strip().lower()
                if field_type == "mode_value":
                    bind_mode = str(field.get("bind_mode") or "").strip()
                    bind_value = str(field.get("bind_value") or "").strip()
                    if bind_mode:
                        bindings.append(
                            {
                                "state_key": f"{field_id}_mode",
                                "bind": bind_mode,
                                "kind": "mode",
                                "field_id": field_id,
                            }
                        )
                    if bind_value:
                        bindings.append(
                            {
                                "state_key": f"{field_id}_value",
                                "bind": bind_value,
                                "kind": "thickness",
                                "field_id": field_id,
                            }
                        )
                    continue

                bind = str(field.get("bind") or "").strip()
                if bind:
                    bindings.append(
                        {
                            "state_key": field_id,
                            "bind": bind,
                            "kind": field_type,
                            "field_id": field_id,
                        }
                    )

        self._schema_state_bindings_cache = [dict(entry) for entry in bindings]
        return [dict(entry) for entry in bindings]

    def _schema_default_for_state_key(self, state_key: str, *, fallback: str = "") -> str:
        if state_key in self._defaults:
            return str(self._defaults.get(state_key, fallback))
        if state_key.endswith("_mode"):
            return "All"
        if state_key.endswith("_value"):
            return self._thickness_values[0] if self._thickness_values else ""
        return str(fallback)

    def _get_state_widget_value(self, binding: dict) -> str:
        widget = getattr(self, str(binding.get("bind") or ""), None)
        if widget is None:
            return ""
        if isinstance(widget, QComboBox):
            value = widget.currentText()
        elif isinstance(widget, QLineEdit):
            value = widget.text().strip()
        else:
            return ""

        kind = str(binding.get("kind") or "").strip().lower()
        if kind == "mode":
            return self._normalize_thickness_mode(value)
        if kind == "thickness":
            return self._normalize_sail_value(value)
        return str(value)

    def _set_state_widget_value(self, binding: dict, state: dict) -> None:
        widget = getattr(self, str(binding.get("bind") or ""), None)
        if widget is None:
            return

        key = str(binding.get("state_key") or "").strip()
        if not key:
            return
        raw_value = state.get(key, self._schema_default_for_state_key(key))
        kind = str(binding.get("kind") or "").strip().lower()
        value = str(raw_value)
        if kind == "mode":
            value = self._normalize_thickness_mode(value)
        elif kind == "thickness":
            value = self._normalize_sail_value(value)

        if isinstance(widget, QComboBox):
            widget.setCurrentText(value)
        elif isinstance(widget, QLineEdit):
            widget.setText(value)

    def _apply_line_validator(self, widget: QLineEdit, validator: dict | None) -> None:
        validator = validator if isinstance(validator, dict) else {}
        if str(validator.get("type") or "").strip().lower() != "int_range":
            return
        bottom = int(validator.get("bottom", -2147483648))
        top = int(validator.get("top", 2147483647))
        widget.setValidator(QIntValidator(bottom, top, widget))

    def init_ui(self):
        combo_width = self._combo_width

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

        girder_label = QLabel(self._normalize_label_text(self._schema_label("member_id", "overview", "Select Member ID:")))
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
        stiffener_heading.setIndent(0)
        stiffener_heading.setContentsMargins(0, 0, 0, 0)
        stiffener_heading.setStyleSheet("font-size: 11px; font-weight: 700; color: #000000; border: none;")
        left_layout.addWidget(stiffener_heading)

        inputs_grid = QGridLayout()
        inputs_grid.setContentsMargins(0, 0, 0, 0)
        inputs_grid.setHorizontalSpacing(12)
        inputs_grid.setVerticalSpacing(10)
        inputs_grid.setColumnMinimumWidth(0, self._form_label_width)
        inputs_grid.setColumnStretch(0, 0)
        inputs_grid.setColumnStretch(1, 1)
        self._build_stiffener_inputs_from_schema(inputs_grid, combo_width)

        left_layout.addLayout(inputs_grid)

        buckling_heading = QLabel("Web Buckling Details")
        buckling_heading.setStyleSheet("font-size: 11px; font-weight: 700; color: #000000; border: none; margin-top: 4px;")
        left_layout.addWidget(buckling_heading)

        buckling_grid = QGridLayout()
        buckling_grid.setContentsMargins(0, 0, 0, 0)
        buckling_grid.setHorizontalSpacing(12)
        buckling_grid.setVerticalSpacing(10)
        buckling_grid.setColumnMinimumWidth(0, self._form_label_width)
        self._build_web_buckling_inputs_from_schema(buckling_grid, combo_width)

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

        # Dynamic image box
        image_box = self._create_card_frame()
        image_layout = QVBoxLayout(image_box)
        image_layout.setContentsMargins(16, 16, 16, 16)
        image_layout.setSpacing(8)

        self.dynamic_image_label = QLabel("Dynamic Image")
        self.dynamic_image_label.setVisible(False)
        image_layout.addWidget(self.dynamic_image_label)

        preview_top_row = QWidget()
        preview_top_row.setMinimumHeight(240)
        preview_top_layout = QHBoxLayout(preview_top_row)
        preview_top_layout.setContentsMargins(0, 0, 0, 0)
        preview_top_layout.setSpacing(6)
        preview_top_layout.setAlignment(Qt.AlignTop)

        self.stiffener_cad_preview = StiffenerCadPreviewWidget()
        self.stiffener_cad_preview.setStyleSheet(
            "QWidget { border: 1px solid #d8d8d8; border-radius: 8px; background-color: #f8f8f8; }"
        )
        preview_top_layout.addWidget(self.stiffener_cad_preview, 3, Qt.AlignTop)
        legend_widget = self._create_stiffener_legend_widget()
        legend_widget.setMinimumWidth(0)
        legend_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        preview_top_layout.addWidget(legend_widget, 1, Qt.AlignTop)

        image_layout.addWidget(preview_top_row, 0, Qt.AlignTop)
        image_layout.addStretch(1)
        container_layout.addWidget(image_box)

        # Input + description card below CAD preview.
        container_layout.addWidget(card_frame)


        # Signals
        self.girder_member_combo.currentTextChanged.connect(self._on_member_changed)
        self.bearing_count_combo.currentTextChanged.connect(self._on_any_input_changed)
        self.bearing_spacing_input.textChanged.connect(self._on_any_input_changed)
        self.bearing_thick_combo.currentTextChanged.connect(self._on_any_input_changed)
        self.bearing_thick_combo.currentTextChanged.connect(self._on_thickness_mode_changed)
        self.bearing_thick_value_combo.currentTextChanged.connect(self._on_any_input_changed)
        self.intermediate_combo.currentTextChanged.connect(self._on_intermediate_changed)
        self.longitudinal_combo.currentTextChanged.connect(self._on_longitudinal_changed)
        self.intermediate_spacing_input.textChanged.connect(self._on_any_input_changed)
        self.intermediate_thick_combo.currentTextChanged.connect(self._on_any_input_changed)
        self.intermediate_thick_combo.currentTextChanged.connect(self._on_thickness_mode_changed)
        self.intermediate_thick_value_combo.currentTextChanged.connect(self._on_any_input_changed)
        self.long_thick_combo.currentTextChanged.connect(self._on_any_input_changed)
        self.long_thick_combo.currentTextChanged.connect(self._on_thickness_mode_changed)
        self.long_thick_value_combo.currentTextChanged.connect(self._on_any_input_changed)
        self.method_combo.currentTextChanged.connect(self._on_any_input_changed)
        self.bearing_outstand_input.textChanged.connect(self._on_any_input_changed)
        self.intermediate_outstand_input.textChanged.connect(self._on_any_input_changed)
        self.apply_to_all_btn.clicked.connect(self._apply_current_to_all_members)

        # Defaults
        self._on_intermediate_changed(self.intermediate_combo.currentText())
        self._on_longitudinal_changed(self.longitudinal_combo.currentText())
        self._update_thickness_value_enabled_state(self._active_member_id or "")
        self.refresh_girder_members()
        self._update_dynamic_cad_preview()

    def _set_field_width(self, widget: QWidget, width: int = 190) -> None:
        widget.setMaximumWidth(width)
        widget.setMinimumWidth(width)
        widget.setMinimumHeight(28)
        widget.setMaximumHeight(40)

    def _create_mode_value_widget(self, mode_combo: QComboBox, value_combo: QComboBox) -> QWidget:
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._set_field_width(wrapper, 190)

        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(mode_combo)
        layout.addWidget(value_combo)
        return wrapper

    def _create_card_frame(self):
        card = QFrame()
        card.setStyleSheet(
            "QFrame { border: 1px solid #d6d6d6; border-radius: 8px; background-color: #f7f7f7; }"
        )
        return card

    def _create_stiffener_legend_widget(self) -> QWidget:
        legend = QFrame()
        legend.setMinimumWidth(180)
        legend.setStyleSheet(
            "QFrame { border: 1px solid #d8d8d8; border-radius: 8px; background-color: #ffffff; }"
        )

        layout = QVBoxLayout(legend)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QLabel("Legend")
        title.setStyleSheet("font-size: 11px; font-weight: 700; color: #333333; border: none;")
        layout.addWidget(title)

        items = [
            ("Bearing stiffener", StiffenerCadPreviewWidget.BEARING_COLOR),
            ("Intermediate stiffener", StiffenerCadPreviewWidget.INTERMEDIATE_COLOR),
            ("Longitudinal stiffener", StiffenerCadPreviewWidget.LONG_COLOR),
        ]

        for text, color in items:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            swatch = QLabel()
            swatch.setFixedSize(22, 10)
            swatch.setStyleSheet(
                f"QLabel {{ border: 1px solid #777777; border-radius: 2px; background-color: {color.name()}; }}"
            )

            label = QLabel(text)
            label.setStyleSheet("font-size: 10px; color: #3a3a3a; border: none;")

            row_layout.addWidget(swatch, 0, Qt.AlignVCenter)
            row_layout.addWidget(label, 1, Qt.AlignVCenter)
            layout.addWidget(row)

        layout.addStretch(1)
        return legend

    def _normalize_label_text(self, text: str) -> str:
        return str(text or "").rstrip(": ")

    def _create_label(self, text):
        label = QLabel(self._normalize_label_text(text))
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

    def _build_stiffener_inputs_from_schema(self, inputs_grid: QGridLayout, combo_width: int) -> None:
        self._bearing_row_widgets = []
        row = 0
        for field in self._schema_fields("stiffener_inputs"):
            row = self._build_stiffener_input_row(inputs_grid, row, field, combo_width)

    def _build_web_buckling_inputs_from_schema(self, buckling_grid: QGridLayout, combo_width: int) -> None:
        row = 0
        for field in self._schema_fields("web_buckling_inputs"):
            row = self._build_stiffener_input_row(buckling_grid, row, field, combo_width, section="web_buckling_inputs")

    def _line_placeholder_for_field(self, field_def: dict) -> str:
        field_id = str(field_def.get("id") or "").strip()
        explicit = field_def.get("placeholder")
        if explicit is not None:
            return str(explicit)
        if field_id in {"bearing_outstand_mm", "intermediate_outstand_mm"}:
            return self._schema_default("outstand_default_text", "NA")
        if field_id == "intermediate_spacing_mm":
            return self._schema_default("intermediate_spacing_mm", "NA")
        return ""

    def _build_stiffener_input_row(
        self,
        grid: QGridLayout,
        row: int,
        field_def: dict,
        combo_width: int,
        *,
        section: str = "stiffener_inputs",
    ) -> int:
        field_id = str(field_def.get("id") or "").strip()
        field_type = str(field_def.get("type") or "").strip().lower()

        widget: QWidget
        if field_type in {"combo", "combo_dynamic"}:
            combo = QComboBox()
            for choice in field_def.get("choices") or []:
                combo.addItem(str(choice))
            default = field_def.get("default")
            if default is not None:
                combo.setCurrentText(str(default))
            apply_field_style(combo)
            combo.setFixedWidth(combo_width)
            combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            bind = str(field_def.get("bind") or "").strip()
            if bind:
                setattr(self, bind, combo)
            widget = combo

        elif field_type == "mode_value":
            mode_combo = QComboBox()
            for choice in field_def.get("mode_choices") or []:
                mode_combo.addItem(str(choice))
            default_mode = field_def.get("default_mode")
            if default_mode is not None:
                mode_combo.setCurrentText(str(default_mode))
            apply_field_style(mode_combo)
            mode_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self._set_field_width(mode_combo, combo_width)

            value_combo = QComboBox()
            value_combo.addItems(self._thickness_values)
            apply_field_style(value_combo)
            value_combo.setVisible(False)
            value_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self._set_field_width(value_combo, combo_width)

            bind_mode = str(field_def.get("bind_mode") or "").strip()
            bind_value = str(field_def.get("bind_value") or "").strip()
            if bind_mode:
                setattr(self, bind_mode, mode_combo)
            if bind_value:
                setattr(self, bind_value, value_combo)

            wrapper = self._create_mode_value_widget(mode_combo, value_combo)
            widget = wrapper

        else:
            line = QLineEdit()
            default = field_def.get("default")
            if default is not None:
                line.setText(str(default))
            self._apply_line_validator(line, field_def.get("validator"))
            placeholder = self._line_placeholder_for_field(field_def)
            if placeholder:
                line.setPlaceholderText(placeholder)
            apply_field_style(line)
            line.setFixedWidth(combo_width)
            line.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            bind = str(field_def.get("bind") or "").strip()
            if bind:
                setattr(self, bind, line)
            widget = line

        label_text = str(field_def.get("label") or self._schema_label(field_id, section, field_id))
        current_row = row
        row = self._add_form_row(grid, row, label_text, widget)

        if field_id.startswith("bearing_"):
            label_widget = grid.itemAtPosition(current_row, 0).widget()
            self._bearing_row_widgets.append((label_widget, widget))
            if field_id == "bearing_stiffeners_each_end":
                self._bearing_count_label_widget = label_widget
                self._bearing_count_field_widget = widget

        return row

    def bind_girder_details_tab(self, girder_details_tab) -> None:
        """Bind to the Girder Details tab to populate members and detect optimized members."""
        self._girder_details_tab = girder_details_tab
        self.refresh_girder_members()
        self._update_dynamic_cad_preview()

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
        self._update_dynamic_cad_preview()

    def validate(self) -> None:
        """Validate current stored inputs before saving the dialog."""
        self._store_current_member_state()
        for member_id, state in self._state_by_member.items():
            if self._is_member_optimized(member_id):
                continue
            self._validate_outstand_values(member_id, state)
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
        defaults: dict[str, str] = {}
        for binding in self._schema_state_bindings():
            key = str(binding.get("state_key") or "").strip()
            if not key:
                continue
            defaults[key] = self._schema_default_for_state_key(key)

        if "shear_buckling_method" not in defaults:
            defaults["shear_buckling_method"] = self.method_combo.itemText(0) if self.method_combo.count() else ""
        return defaults

    @staticmethod
    def _normalize_thickness_mode(value: str) -> str:
        text = str(value or "").strip().lower()
        if text in {"custom", "customized"}:
            return "Custom"
        return "All"

    def _normalize_sail_value(self, value: str) -> str:
        text = str(value or "").strip()
        if text in self._thickness_values:
            return text
        return self._thickness_values[0] if self._thickness_values else ""

    def _store_current_member_state(self) -> None:
        if self._is_loading_ui:
            return
        if not self._active_member_id:
            return
        state = dict(self._state_by_member.get(self._active_member_id) or self._default_member_state())
        for binding in self._schema_state_bindings():
            key = str(binding.get("state_key") or "").strip()
            if not key:
                continue
            state[key] = self._get_state_widget_value(binding)
        self._state_by_member[self._active_member_id] = state
        self._update_dynamic_cad_preview()

    def _load_member_state(self, member_id: str) -> None:
        # Ensure every member has a state entry.
        if member_id not in self._state_by_member:
            self._state_by_member[member_id] = dict(self._default_member_state())
        state = dict(self._state_by_member.get(member_id) or self._default_member_state())

        self._is_loading_ui = True

        blocked_widgets: list[tuple[QWidget, bool]] = []
        for binding in self._schema_state_bindings():
            widget = getattr(self, str(binding.get("bind") or ""), None)
            if widget is None or not hasattr(widget, "blockSignals"):
                continue
            blocked_widgets.append((widget, widget.blockSignals(True)))
        try:
            for binding in self._schema_state_bindings():
                self._set_state_widget_value(binding, state)
        finally:
            for widget, previous in blocked_widgets:
                widget.blockSignals(previous)
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
        self._update_dynamic_cad_preview()

    def _on_any_input_changed(self, *_args) -> None:
        """Persist UI edits into per-member state as the user types/selects."""
        self._store_current_member_state()

    def _update_outstand_fields(self, member_id: str) -> None:
        computed = self._compute_outstand_value(member_id)
        value = computed if computed is not None else ""

        bearing_current = self.bearing_outstand_input.text().strip()
        inter_current = self.intermediate_outstand_input.text().strip()
        bearing_value = value if bearing_current == "" else bearing_current
        inter_value = value if inter_current == "" else inter_current

        prev_a = self.bearing_outstand_input.blockSignals(True)
        prev_b = self.intermediate_outstand_input.blockSignals(True)
        try:
            self.bearing_outstand_input.setText(bearing_value)
            self.intermediate_outstand_input.setText(inter_value)
        finally:
            self.bearing_outstand_input.blockSignals(prev_a)
            self.intermediate_outstand_input.blockSignals(prev_b)

        if computed is not None:
            state = dict(self._state_by_member.get(member_id) or self._default_member_state())
            if not str(state.get("bearing_outstand_mm") or "").strip():
                state["bearing_outstand_mm"] = computed
            if not str(state.get("intermediate_outstand_mm") or "").strip():
                state["intermediate_outstand_mm"] = computed
            self._state_by_member[member_id] = state

    def _parse_non_negative_float(self, value: str) -> Optional[float]:
        try:
            text = str(value or "").strip()
            if text == "":
                return None
            parsed = float(text)
            return parsed if parsed >= 0.0 else None
        except Exception:
            return None

    def _validate_outstand_values(self, member_id: str, state: dict) -> None:
        computed = self._compute_outstand_value(member_id)
        max_value = None
        if computed is not None:
            try:
                max_value = float(computed)
            except (TypeError, ValueError):
                max_value = None

        for key, label in (
            ("bearing_outstand_mm", "Outstand of Bearing Stiffener (mm)"),
            ("intermediate_outstand_mm", "Outstand of Intermediate Stiffener (mm)"),
        ):
            raw = str(state.get(key) or "").strip()
            parsed = self._parse_non_negative_float(raw)
            if parsed is None:
                if max_value is not None:
                    state[key] = f"{max_value:.3f}".rstrip("0").rstrip(".")
                continue
            if max_value is not None and parsed > max_value:
                raise ValueError(f"{label} must be between 0 and {max_value:.3f} for member '{member_id}'.")


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
        is_yes = str(text).strip().startswith("Yes")
        if not is_yes:
            prev_mode = self.long_thick_combo.blockSignals(True)
            try:
                self.long_thick_combo.setCurrentText("All")
            finally:
                self.long_thick_combo.blockSignals(prev_mode)
        self._refresh_enabled_state(self._active_member_id or "")
        self._store_current_member_state()

    def _is_custom_thickness_mode(self, combo: QComboBox | None) -> bool:
        if combo is None:
            return False
        return (combo.currentText() or "").strip().lower() == "custom"

    def _on_thickness_mode_changed(self, _text: str) -> None:
        self._update_thickness_value_enabled_state(self._active_member_id or "")
        self._store_current_member_state()

    def _update_thickness_value_enabled_state(self, member_id: str) -> None:
        member_id = str(member_id or self._active_member_id or "").strip()
        optimized = self._is_member_optimized(member_id) if member_id else False
        base_enabled = not optimized

        intermediate_yes = self.intermediate_combo.currentText().strip() == "Yes"
        longitudinal_yes = self.longitudinal_combo.currentText().strip().startswith("Yes")

        configs = [
            (self.bearing_thick_combo, self.bearing_thick_value_combo, True),
            (self.intermediate_thick_combo, self.intermediate_thick_value_combo, intermediate_yes),
            (self.long_thick_combo, self.long_thick_value_combo, longitudinal_yes),
        ]

        for mode_combo, value_combo, applicable in configs:
            if not optimized:
                if mode_combo.currentText().strip().lower() != "custom":
                    prev = mode_combo.blockSignals(True)
                    mode_combo.setCurrentText("Custom")
                    mode_combo.blockSignals(prev)
                mode_combo.setVisible(False)
                mode_combo.setEnabled(False)

                value_combo.setVisible(True)
                value_combo.setEnabled(base_enabled and applicable)
            else:
                mode_combo.setVisible(True)
                mode_combo.setEnabled(base_enabled and applicable)

                is_custom_mode = self._is_custom_thickness_mode(mode_combo)
                value_combo.setVisible(is_custom_mode)
                value_combo.setEnabled(base_enabled and applicable and is_custom_mode)

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
        exterior = self._is_exterior_member(member_id) if member_id else False
        self._update_bearing_count_label(member_id)

        base_enabled = not optimized
        show_bearing_rows = bool(exterior)
        for label_widget, field_widget in getattr(self, "_bearing_row_widgets", []):
            if label_widget is not None:
                label_widget.setVisible(show_bearing_rows)
            if field_widget is not None:
                field_widget.setVisible(show_bearing_rows)
        self.bearing_count_combo.setEnabled(base_enabled and exterior)
        self.bearing_spacing_input.setEnabled(base_enabled and exterior)
        if exterior:
            self.bearing_count_combo.setToolTip("")
            self.bearing_spacing_input.setToolTip("Leave empty for auto spacing from minimum member length.")
        else:
            hint = "Bearing count/spacing is editable only for exterior member IDs (end members)."
            self.bearing_count_combo.setToolTip(hint)
            self.bearing_spacing_input.setToolTip(hint)
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
        self._update_thickness_value_enabled_state(member_id)

        # If optimized, applying changes makes no sense.
        self.apply_to_all_btn.setEnabled(base_enabled)

    @staticmethod
    def _parse_member_indices(member_id: str) -> tuple[Optional[int], Optional[int]]:
        match = re.match(r"^G(\d+)M(\d+)$", str(member_id or "").strip())
        if not match:
            return None, None
        try:
            return int(match.group(1)), int(match.group(2))
        except Exception:
            return None, None

    def _is_exterior_member(self, member_id: str) -> bool:
        current_girder, current_member = self._parse_member_indices(member_id)
        if current_girder is None or current_member is None:
            return True

        members_in_same_girder: List[int] = []
        for mid in self._list_current_member_ids():
            g_idx, m_idx = self._parse_member_indices(mid)
            if g_idx == current_girder and m_idx is not None:
                members_in_same_girder.append(m_idx)

        if not members_in_same_girder:
            return True

        return current_member in {min(members_in_same_girder), max(members_in_same_girder)}

    def _count_members_in_girder(self, member_id: str) -> int:
        current_girder, _ = self._parse_member_indices(member_id)
        if current_girder is None:
            return 0

        count = 0
        for mid in self._list_current_member_ids():
            g_idx, _ = self._parse_member_indices(mid)
            if g_idx == current_girder:
                count += 1
        return count

    def _update_bearing_count_label(self, member_id: str) -> None:
        label_widget = getattr(self, "_bearing_count_label_widget", None)
        if label_widget is None:
            return

        text = "No. of Bearing Stiffeners\n(on one side only)"
        label_widget.setText(text)

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
        self._update_dynamic_cad_preview()

    def _resolve_preview_segments_for_active_member(self) -> List[dict]:
        if self._girder_details_tab is None:
            return []

        active_member = str(self._active_member_id or "").strip()
        match = re.match(r"^(G\d+)M\d+$", active_member)
        girder = match.group(1) if match else ""
        if not girder:
            current = str(self.girder_member_combo.currentText() or "").strip()
            fallback = re.match(r"^(G\d+)M\d+$", current)
            girder = fallback.group(1) if fallback else ""
        if not girder:
            return []

        try:
            if hasattr(self._girder_details_tab, "_ensure_girder_segments"):
                segments = self._girder_details_tab._ensure_girder_segments(girder)  # type: ignore[attr-defined]
            else:
                segments = (getattr(self._girder_details_tab, "segment_chain", {}) or {}).get(girder, [])
        except Exception:
            segments = []

        return list(segments or [])

    def _resolve_preview_section_dimensions(self, segments: List[dict]) -> Dict[str, dict]:
        dims_by_member: Dict[str, dict] = {}
        if self._girder_details_tab is None:
            return dims_by_member
        if not hasattr(self._girder_details_tab, "get_member_section_dimensions"):
            return dims_by_member

        for seg in segments or []:
            member_id = str((seg or {}).get("id") or "").strip()
            if not member_id:
                continue
            try:
                dims = self._girder_details_tab.get_member_section_dimensions(member_id)
            except Exception:
                dims = None
            if isinstance(dims, dict):
                dims_by_member[member_id] = dict(dims)

        return dims_by_member

    def _update_dynamic_cad_preview(self) -> None:
        if not hasattr(self, "stiffener_cad_preview"):
            return
        segments = self._resolve_preview_segments_for_active_member()
        dims_by_member = self._resolve_preview_section_dimensions(segments)
        self.stiffener_cad_preview.set_data(
            segments=segments,
            stiffener_by_member=self._state_by_member,
            active_member_id=self._active_member_id or self.girder_member_combo.currentText(),
            section_dims_by_member=dims_by_member,
        )
        if self._active_member_id:
            self._update_outstand_fields(self._active_member_id)
