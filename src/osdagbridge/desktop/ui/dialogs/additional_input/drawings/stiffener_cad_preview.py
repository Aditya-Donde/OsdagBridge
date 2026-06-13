from __future__ import annotations

import re
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from osdagbridge.core.utils.common import MIN_BEARING_STIFFENER_SPACING_MM

MIN_BEARING_SPACING_MM = MIN_BEARING_STIFFENER_SPACING_MM


class StiffenerCadPreviewWidget(QWidget):
    """2D CAD-style stiffener preview driven by per-member stiffener inputs."""

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
            cleaned.append({"id": str(seg.get("id") or ""), "start": start, "end": end, "length": length})
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

    def paintEvent(self, _event):  # noqa: N802
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

        cad_bg = draw.adjusted(0, 14, 0, -8)
        painter.fillRect(cad_bg, self.THEME_CANVAS)

        girder_rect = cad_bg.adjusted(14, 18, -14, -18)
        painter.fillRect(girder_rect, self.THEME_GIRDER)

        active_dims = self._dims_for(self._active_member_id)
        try:
            depth_mm = float(active_dims.get("depth_mm") or 0.0)
            top_t_mm = float(active_dims.get("top_flange_thickness_mm") or 0.0)
            bot_t_mm = float(active_dims.get("bottom_flange_thickness_mm") or 0.0)
        except (TypeError, ValueError):
            depth_mm = top_t_mm = bot_t_mm = 0.0

        if depth_mm > 0.0 and top_t_mm > 0.0 and bot_t_mm > 0.0:
            top_flange_px = int(round((top_t_mm / depth_mm) * girder_rect.height()))
            bottom_flange_px = int(round((bot_t_mm / depth_mm) * girder_rect.height()))
        else:
            top_flange_px = max(4, int(round(girder_rect.height() * 0.08)))
            bottom_flange_px = max(4, int(round(girder_rect.height() * 0.08)))

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
            int(girder_rect.left()), int(web_top),
            int(girder_rect.width()), int(max(1, web_bottom - web_top + 1)),
            self.THEME_WEB,
        )

        painter.setPen(QPen(self.THEME_GIRDER_BORDER, 1.0))
        painter.drawRect(girder_rect)
        painter.drawLine(int(girder_rect.left()), int(web_top),    int(girder_rect.right()), int(web_top))
        painter.drawLine(int(girder_rect.left()), int(web_bottom), int(girder_rect.right()), int(web_bottom))

        web_height = max(1.0, web_bottom - web_top)

        active_girder = self._member_girder(self._active_member_id)
        if not active_girder and self._segments:
            active_girder = self._member_girder(str(self._segments[0].get("id") or ""))

        px_per_mm = girder_rect.width() / max(1.0, total_length * 1000.0)

        def resolve_bearing_params(seg_state: dict, seg_len_mm: float) -> tuple[int, float, float, float]:
            count = self._parse_positive_int(seg_state.get("bearing_stiffeners_each_end")) or 2
            count = max(1, min(8, count))
            custom_spacing_mm = self._parse_positive_int(seg_state.get("bearing_spacing_mm"))
            spacing_mm = float(custom_spacing_mm) if custom_spacing_mm else max(MIN_BEARING_SPACING_MM, seg_len_mm / float(count + 1))
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

            painter.setPen(QPen(self.BEARING_COLOR, 2.0))
            if is_first and left_count > 0:
                for i in range(left_count):
                    x_pos = max(left + 2.0, min(right - 2.0, left + left_offset + (i * left_spacing_px)))
                    painter.drawLine(int(x_pos), int(web_top), int(x_pos), int(web_bottom))
            if is_last and right_count > 0:
                for i in range(right_count):
                    x_pos = max(left + 2.0, min(right - 2.0, right - right_offset - (i * right_spacing_px)))
                    painter.drawLine(int(x_pos), int(web_top), int(x_pos), int(web_bottom))

            long_mode = str(seg_state.get("longitudinal_stiffener") or "")
            levels = self._longitudinal_levels(long_mode, web_top, web_height)
            if levels:
                painter.setPen(QPen(self.LONG_COLOR, 3.0))
                for y_pos in levels:
                    painter.drawLine(int(left), int(y_pos), int(right), int(y_pos))
