"""Stiffener Details CAD preview widget.

Self-contained 2D painter widget for the Stiffener Details sub-tab.
Public API:
    set_data(segments, stiffener_by_member, active_member_id, section_dims_by_member)
    update_stiffener(working_input_dict, segments, section_dims_by_member)
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from osdagbridge.core.utils.common import (
    MIN_BEARING_STIFFENER_SPACING_MM,
    KEY_MP_STIFFENER_SELECT_MEMBER_ID,
    KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
    KEY_MP_STIFFENER_SPACING,
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_LONGITUDINAL,
)

MIN_BEARING_SPACING_MM: int = int(MIN_BEARING_STIFFENER_SPACING_MM)


class StiffenerDetailsCad(QWidget):
    """2D CAD-style stiffener preview widget.

    Driven externally via:
        set_data(...)          — low-level, pass all data explicitly
        update_stiffener(...)  — high-level, reads from working_input_dict
    """

    # ── Theme palette ──────────────────────────────────────────────────────────
    THEME_BG            = QColor("#f4f4f4")
    THEME_BORDER        = QColor("#d0d0d0")
    THEME_TEXT          = QColor("#333333")
    THEME_CANVAS        = QColor("#f8f8f8")
    THEME_GIRDER        = QColor("#d9d9d9")
    THEME_FLANGE        = QColor("#c9c9c9")
    THEME_WEB           = QColor("#dcdcdc")
    THEME_GIRDER_BORDER = QColor("#3a3a3a")
    THEME_SEGMENT_LINE  = QColor("#888888")
    BEARING_COLOR       = QColor("#90AF13")
    INTERMEDIATE_COLOR  = QColor("#6B7D20")
    LONG_COLOR          = QColor("#4a4a4a")

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._segments:               List[dict]         = []
        self._stiffener_by_member:    Dict[str, dict]    = {}
        self._section_dims_by_member: Dict[str, dict]    = {}
        self._active_member_id:       str                = ""
        self.setMinimumHeight(210)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_data(
        self,
        segments:               List[dict],
        stiffener_by_member:    Dict[str, dict],
        active_member_id:       str,
        section_dims_by_member: Optional[Dict[str, dict]] = None,
    ) -> None:
        """Low-level update — pass all data explicitly."""
        cleaned: List[dict] = []
        for seg in segments or []:
            try:
                start  = float(seg.get("start", 0.0))
                end    = float(seg.get("end",   0.0))
            except Exception:
                continue
            length = max(0.0, end - start)
            if length <= 0.0:
                continue
            cleaned.append({
                "id":     str(seg.get("id") or ""),
                "start":  start,
                "end":    end,
                "length": length,
            })
        self._segments               = cleaned
        self._stiffener_by_member    = dict(stiffener_by_member or {})
        self._section_dims_by_member = dict(section_dims_by_member or {})
        self._active_member_id       = str(active_member_id or "").strip()
        self.update()

    def update_stiffener(self, working_input_dict: dict, active_member_id: str = "") -> None:
        from osdagbridge.core.utils.common import KEY_MP_GD_SEGMENT_TABLE, KEY_TS_NO_OF_GIRDERS
        active_member_id = str(active_member_id or "").strip()

        if active_member_id:
            state = dict(working_input_dict)
            match = re.match(r"G(\d+)M(\d+)", active_member_id)
            suffix = f".G{match.group(1)}.M{match.group(2)}" if match else ""
            if suffix:
                for k, v in working_input_dict.items():
                    if k.endswith(suffix):
                        state[k[:-len(suffix)]] = v
            self._stiffener_by_member[active_member_id] = state

        match = re.match(r"G(\d+)M\d+", active_member_id)
        if match:
            seg_key = f"{KEY_MP_GD_SEGMENT_TABLE}.G{match.group(1)}"
            segments = working_input_dict.get(seg_key) or []
        else:
            girder_count = int(float(str(working_input_dict.get(KEY_TS_NO_OF_GIRDERS) or 1)))
            segments = []
            for gi in range(1, girder_count + 1):
                segments.extend(working_input_dict.get(f"{KEY_MP_GD_SEGMENT_TABLE}.G{gi}") or [])

        self.set_data(
            segments            = segments or self._segments,
            stiffener_by_member = self._stiffener_by_member,
            active_member_id    = active_member_id,
        )

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _member_girder(member_id: str) -> str:
        match = re.match(r"^(G\d+)M\d+$", str(member_id or "").strip())
        return match.group(1) if match else ""

    def _state_for(self, member_id: str) -> dict:
        return dict(self._stiffener_by_member.get(str(member_id or "").strip()) or {})

    def _dims_for(self, member_id: str) -> dict:
        return dict(self._section_dims_by_member.get(str(member_id or "").strip()) or {})

    @staticmethod
    def _parse_positive_int(value) -> Optional[int]:
        try:
            text = str(value or "").strip()
            if not text.isdigit():
                return None
            parsed = int(text)
            return parsed if parsed > 0 else None
        except Exception:
            return None

    @staticmethod
    def _longitudinal_levels(mode: str, web_top: float, web_height: float) -> List[float]:
        text = str(mode or "").strip().lower()
        if "2" in text:
            return [web_top + (web_height / 3.0), web_top + (2.0 * web_height / 3.0)]
        if "1" in text:
            return [web_top + (web_height / 3.0)]
        return []

    # ── Paint ──────────────────────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:  # noqa: N802
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

        # Canvas + girder strip
        cad_bg      = draw.adjusted(0, 14, 0, -8)
        painter.fillRect(cad_bg, self.THEME_CANVAS)
        girder_rect = cad_bg.adjusted(14, 18, -14, -18)
        painter.fillRect(girder_rect, self.THEME_GIRDER)

        # Flange thickness bands
        active_dims = self._dims_for(self._active_member_id)
        try:
            depth_mm  = float(active_dims.get("depth_mm")                or 0.0)
            top_t_mm  = float(active_dims.get("top_flange_thickness_mm")  or 0.0)
            bot_t_mm  = float(active_dims.get("bottom_flange_thickness_mm") or 0.0)
        except (TypeError, ValueError):
            depth_mm = top_t_mm = bot_t_mm = 0.0

        if depth_mm > 0.0 and top_t_mm > 0.0 and bot_t_mm > 0.0:
            top_flange_px    = int(round((top_t_mm / depth_mm) * girder_rect.height()))
            bottom_flange_px = int(round((bot_t_mm / depth_mm) * girder_rect.height()))
        else:
            top_flange_px    = max(4, int(round(girder_rect.height() * 0.08)))
            bottom_flange_px = max(4, int(round(girder_rect.height() * 0.08)))

        max_each = max(4, int(round(girder_rect.height() * 0.22)))
        top_flange_px    = min(max_each, max(3, top_flange_px))
        bottom_flange_px = min(max_each, max(3, bottom_flange_px))
        if top_flange_px + bottom_flange_px > girder_rect.height() - 8:
            overflow         = (top_flange_px + bottom_flange_px) - (girder_rect.height() - 8)
            reduce_top       = overflow // 2
            reduce_bottom    = overflow - reduce_top
            top_flange_px    = max(3, top_flange_px    - reduce_top)
            bottom_flange_px = max(3, bottom_flange_px - reduce_bottom)

        flange_x       = int(girder_rect.left())
        flange_w       = int(girder_rect.width())
        top_flange_y   = int(girder_rect.top())
        bottom_flange_y = int(girder_rect.bottom() - bottom_flange_px + 1)

        painter.fillRect(flange_x, top_flange_y,    flange_w, int(top_flange_px),    self.THEME_FLANGE)
        painter.fillRect(flange_x, bottom_flange_y, flange_w, int(bottom_flange_px), self.THEME_FLANGE)

        web_top    = girder_rect.top()    + top_flange_px
        web_bottom = girder_rect.bottom() - bottom_flange_px
        if web_bottom < web_top:
            web_bottom = web_top

        painter.fillRect(
            int(girder_rect.left()), int(web_top),
            int(girder_rect.width()), int(max(1, web_bottom - web_top + 1)),
            self.THEME_WEB,
        )

        painter.setPen(QPen(self.THEME_GIRDER_BORDER, 1.0))
        painter.drawRect(girder_rect)
        painter.drawLine(int(girder_rect.left()), int(web_top),    int(girder_rect.right()), int(web_top))
        painter.drawLine(int(girder_rect.left()), int(web_bottom), int(girder_rect.right()), int(web_bottom))

        web_height = max(1.0, web_bottom - web_top)

        # Active girder
        active_girder = self._member_girder(self._active_member_id)
        if not active_girder and self._segments:
            active_girder = self._member_girder(str(self._segments[0].get("id") or ""))

        px_per_mm = girder_rect.width() / max(1.0, total_length * 1000.0)

        def resolve_bearing_params(seg_state: dict, seg_len_mm: float):
            raw_count = (
                seg_state.get(KEY_MP_STIFFENER_NO_BEARING_STIFFENERS)
                or seg_state.get("bearing_stiffeners_each_end")
            )
            count = self._parse_positive_int(raw_count) or 2
            count = max(1, min(8, count))

            raw_spacing = (
                seg_state.get(KEY_MP_STIFFENER_SPACING)
                or seg_state.get("bearing_spacing_mm")
            )
            custom_spacing_mm = self._parse_positive_int(raw_spacing)
            if custom_spacing_mm:
                spacing_mm = float(custom_spacing_mm)
            else:
                spacing_mm = max(MIN_BEARING_SPACING_MM, seg_len_mm / float(count + 1))

            spacing_px  = max(8.0, min(24.0, spacing_mm * px_per_mm))
            edge_offset = spacing_px
            bearing_zone = edge_offset + ((count - 1) * spacing_px) + 6.0
            return count, spacing_px, edge_offset, bearing_zone

        # Build segment rects
        x = float(girder_rect.left())
        segment_rects: List[dict] = []
        for idx, seg in enumerate(self._segments):
            ratio = float(seg["length"]) / total_length
            width = girder_rect.width() * ratio
            if idx == len(self._segments) - 1:
                width = max(1.0, float(girder_rect.right()) - x)
            segment_rects.append({"id": seg["id"], "left": x, "right": x + width})
            x += width

        # Segment labels + partition lines
        label_gap    = 4
        label_height = 20
        label_bottom = int(max(draw.top() + label_height, girder_rect.top() - label_gap))
        label_top    = int(max(draw.top(), label_bottom - label_height))
        for idx, seg_rect in enumerate(segment_rects):
            left  = float(seg_rect["left"])
            right = float(seg_rect["right"])
            lr    = draw.adjusted(0, 0, 0, 0)
            lr.setTop(label_top);  lr.setBottom(label_bottom)
            lr.setLeft(int(left)); lr.setRight(int(right))
            painter.setPen(QPen(self.THEME_TEXT, 1.0))
            painter.drawText(lr, Qt.AlignHCenter | Qt.AlignVCenter, str(seg_rect["id"] or ""))
            if idx > 0:
                painter.setPen(QPen(self.THEME_SEGMENT_LINE, 1.0))
                painter.drawLine(int(left), int(girder_rect.top()), int(left), int(girder_rect.bottom()))

        # Per-segment stiffeners
        for idx, seg_rect in enumerate(segment_rects):
            seg_id    = str(seg_rect["id"] or "")
            seg_state = self._state_for(seg_id)
            left      = float(seg_rect["left"])
            right     = float(seg_rect["right"])
            width     = max(1.0, right - left)
            is_first  = idx == 0
            is_last   = idx == len(segment_rects) - 1

            seg_len_mm = float(self._segments[idx]["length"]) * 1000.0
            left_count  = right_count  = 0
            left_spacing_px = right_spacing_px = 0.0
            left_offset  = right_offset  = 0.0
            left_zone    = right_zone    = 0.0
            if is_first:
                left_count, left_spacing_px, left_offset, left_zone   = resolve_bearing_params(seg_state, seg_len_mm)
            if is_last:
                right_count, right_spacing_px, right_offset, right_zone = resolve_bearing_params(seg_state, seg_len_mm)

            seg_girder = self._member_girder(seg_id)
            if active_girder and seg_girder and seg_girder != active_girder:
                continue

            # Intermediate stiffeners — support both old and new keys
            intermediate_val = (
                seg_state.get(KEY_MP_STIFFENER_INTERMEDIATE)
                or seg_state.get("intermediate_stiffener")
                or ""
            )
            include_intermediate = str(intermediate_val).strip() == "Yes"

            spacing_raw = (
                seg_state.get(KEY_MP_STIFFENER_INTERMEDIATE_SPACING)
                or seg_state.get("intermediate_spacing_mm")
            )
            spacing_mm = self._parse_positive_int(spacing_raw)

            if include_intermediate and spacing_mm and float(self._segments[idx]["length"]) > 0.0:
                seg_len_mm_int = float(self._segments[idx]["length"]) * 1000.0
                if seg_len_mm_int > spacing_mm:
                    painter.setPen(QPen(self.INTERMEDIATE_COLOR, 2.0))
                    pos_mm = float(spacing_mm)
                    while pos_mm < seg_len_mm_int:
                        ratio  = pos_mm / seg_len_mm_int
                        x_pos  = left + (ratio * width)
                        if is_first and x_pos <= (left + left_zone):
                            pos_mm += float(spacing_mm); continue
                        if is_last and x_pos >= (right - right_zone):
                            pos_mm += float(spacing_mm); continue
                        if (x_pos - left) > 3.0 and (right - x_pos) > 3.0:
                            painter.drawLine(int(x_pos), int(web_top), int(x_pos), int(web_bottom))
                        pos_mm += float(spacing_mm)

            # Bearing stiffeners
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

            # Longitudinal stiffeners — support both old and new keys
            long_mode = str(
                seg_state.get(KEY_MP_STIFFENER_LONGITUDINAL)
                or seg_state.get("longitudinal_stiffener")
                or ""
            )
            levels = self._longitudinal_levels(long_mode, web_top, web_height)
            if levels:
                painter.setPen(QPen(self.LONG_COLOR, 3.0))
                for y_pos in levels:
                    painter.drawLine(int(left), int(y_pos), int(right), int(y_pos))