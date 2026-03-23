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
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from osdagbridge.core.utils.common import VALUES_YES_NO, VALUES_STIFFENER_DESIGN
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style

OUTSTAND_DEFAULT_TEXT = "NA"
VALUES_BEARING_STIFFENER_COUNT = ["1", "2", "3", "4"]
VALUES_STIFFENER_THICKNESS_MODE = ["All", "Customized"]
VALUES_LONGITUDINAL_STIFFENER = ["No", "Yes and 1 stiffener", "Yes and 2 stiffeners"]
MIN_BEARING_SPACING_MM = 50


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

        draw = frame.adjusted(14, 18, -14, -24)
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

        # Bearing settings are governed by exterior member IDs (first/last segment of the girder).
        bearing_source_state: dict = {}
        if self._segments:
            first_id = str(self._segments[0].get("id") or "")
            last_id = str(self._segments[-1].get("id") or "")
            first_state = self._state_for(first_id)
            last_state = self._state_for(last_id)
            bearing_source_state = first_state or last_state
        if not bearing_source_state:
            bearing_source_state = self._state_for(self._active_member_id)

        # Bearing stiffeners are support-only and should mirror at both ends.
        bearing_count = self._parse_positive_int(bearing_source_state.get("bearing_stiffeners_each_end")) or 2
        bearing_count = max(1, min(8, bearing_count))

        min_member_length_mm = min((float(seg.get("length") or 0.0) for seg in self._segments), default=0.0) * 1000.0
        px_per_mm = girder_rect.width() / max(1.0, total_length * 1000.0)
        custom_bearing_spacing_mm = self._parse_positive_int(bearing_source_state.get("bearing_spacing_mm"))
        if custom_bearing_spacing_mm:
            bearing_spacing_mm = float(custom_bearing_spacing_mm)
        else:
            # Auto spacing: derive from the smallest member length for consistent visual density.
            bearing_spacing_mm = max(MIN_BEARING_SPACING_MM, min_member_length_mm / float(bearing_count + 1))
        spacing_px_uniform = max(8.0, min(24.0, bearing_spacing_mm * px_per_mm))
        edge_offset_uniform = spacing_px_uniform

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

            # Keep a clear support zone near ends so intermediate lines do not overlap
            # with bearing stiffeners and make the drawing look cluttered.
            spacing_px = spacing_px_uniform
            edge_offset = edge_offset_uniform
            bearing_zone_px = edge_offset + ((bearing_count - 1) * spacing_px) + 6.0

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
                        if is_first and x_pos <= (left + bearing_zone_px):
                            pos_mm += float(spacing_mm)
                            continue
                        if is_last and x_pos >= (right - bearing_zone_px):
                            pos_mm += float(spacing_mm)
                            continue
                        if (x_pos - left) > 3.0 and (right - x_pos) > 3.0:
                            painter.drawLine(int(x_pos), int(web_top), int(x_pos), int(web_bottom))
                        pos_mm += float(spacing_mm)

            # Bearing stiffeners only at first and last member of the selected girder.
            # Draw these after intermediate lines so bearing stiffeners remain visible.
            if is_first or is_last:
                painter.setPen(QPen(self.BEARING_COLOR, 2.0))
                for i in range(bearing_count):
                    if is_first:
                        x_pos = left + edge_offset + (i * spacing_px)
                    else:
                        x_pos = right - edge_offset - (i * spacing_px)
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
        self._girder_details_tab = None
        self._state_by_member: Dict[str, dict] = {}
        self._active_member_id: Optional[str] = None
        self._is_loading_ui: bool = False
        self.init_ui()

    def init_ui(self):
        combo_width = 190  # keep all combo boxes strictly same width
        self._form_label_width = 245

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

        girder_label = QLabel("Select Member ID")
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

        self.bearing_count_combo = QComboBox()
        self.bearing_count_combo.addItems(VALUES_BEARING_STIFFENER_COUNT)
        apply_field_style(self.bearing_count_combo)
        self.bearing_count_combo.setFixedWidth(combo_width)
        self.bearing_count_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        bearing_count_row = 0
        row = self._add_form_row(
            inputs_grid,
            0,
            "No. of Bearing Stiffeners at each end\n(on one side only):",
            self.bearing_count_combo,
        )
        # Keep references so bearing rows can be fully hidden for interior members.
        self._bearing_count_label_widget = inputs_grid.itemAtPosition(bearing_count_row, 0).widget()
        self._bearing_count_field_widget = self.bearing_count_combo

        self.bearing_spacing_input = QLineEdit()
        self.bearing_spacing_input.setValidator(QIntValidator(1, 10**9, self.bearing_spacing_input))
        apply_field_style(self.bearing_spacing_input)
        self.bearing_spacing_input.setFixedWidth(combo_width)
        self.bearing_spacing_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        bearing_spacing_row = row
        row = self._add_form_row(inputs_grid, row, "Bearing Stiffener Spacing (mm):", self.bearing_spacing_input)
        self._bearing_spacing_label_widget = inputs_grid.itemAtPosition(bearing_spacing_row, 0).widget()
        self._bearing_spacing_field_widget = self.bearing_spacing_input

        self.bearing_thick_combo = QComboBox()
        self.bearing_thick_combo.addItems(VALUES_STIFFENER_THICKNESS_MODE)
        apply_field_style(self.bearing_thick_combo)
        self.bearing_thick_combo.setFixedWidth(combo_width)
        self.bearing_thick_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        bearing_thick_row = row
        row = self._add_form_row(inputs_grid, row, "Bearing Stiffener Thickness (mm):", self.bearing_thick_combo)
        self._bearing_thick_label_widget = inputs_grid.itemAtPosition(bearing_thick_row, 0).widget()
        self._bearing_thick_field_widget = self.bearing_thick_combo

        self.bearing_outstand_input = QTextEdit()
        self.bearing_outstand_input.setReadOnly(True)
        self.bearing_outstand_input.setText(OUTSTAND_DEFAULT_TEXT)
        self.bearing_outstand_input.setFixedHeight(28)
        self.bearing_outstand_input.setFixedWidth(combo_width)
        self.bearing_outstand_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bearing_outstand_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bearing_outstand_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.bearing_outstand_input.setStyleSheet(
            "QTextEdit { border: 1px solid #d0d0d0; border-radius: 6px; background: #ffffff; "
            "color: #5b5b5b; font-size: 11px; }"
        )
        bearing_outstand_row = row
        row = self._add_form_row(inputs_grid, row, "Outstand of Bearing Stiffener (mm):", self.bearing_outstand_input)
        self._bearing_outstand_label_widget = inputs_grid.itemAtPosition(bearing_outstand_row, 0).widget()
        self._bearing_outstand_field_widget = self.bearing_outstand_input

        self._bearing_row_widgets = [
            (self._bearing_count_label_widget, self._bearing_count_field_widget),
            (self._bearing_spacing_label_widget, self._bearing_spacing_field_widget),
            (self._bearing_thick_label_widget, self._bearing_thick_field_widget),
            (self._bearing_outstand_label_widget, self._bearing_outstand_field_widget),
        ]

        self.intermediate_combo = QComboBox()
        self.intermediate_combo.addItems(VALUES_YES_NO)
        apply_field_style(self.intermediate_combo)
        self.intermediate_combo.setFixedWidth(combo_width)
        self.intermediate_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row = self._add_form_row(inputs_grid, row, "Intermediate Stiffener:", self.intermediate_combo)

        self.intermediate_spacing_input = QLineEdit()
        self.intermediate_spacing_input.setValidator(QIntValidator(1, 10**9, self.intermediate_spacing_input))
        apply_field_style(self.intermediate_spacing_input)
        self.intermediate_spacing_input.setPlaceholderText("NA")
        self.intermediate_spacing_input.setFixedWidth(combo_width)
        self.intermediate_spacing_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row = self._add_form_row(inputs_grid, row, "Intermediate Stiffener Spacing:", self.intermediate_spacing_input)

        self.intermediate_thick_combo = QComboBox()
        self.intermediate_thick_combo.addItems(VALUES_STIFFENER_THICKNESS_MODE)
        apply_field_style(self.intermediate_thick_combo)
        self.intermediate_thick_combo.setFixedWidth(combo_width)
        self.intermediate_thick_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row = self._add_form_row(inputs_grid, row, "Intermediate Stiffener Thickness (mm):", self.intermediate_thick_combo)

        self.intermediate_outstand_input = QTextEdit()
        self.intermediate_outstand_input.setReadOnly(True)
        self.intermediate_outstand_input.setText(OUTSTAND_DEFAULT_TEXT)
        self.intermediate_outstand_input.setFixedHeight(28)
        self.intermediate_outstand_input.setFixedWidth(combo_width)
        self.intermediate_outstand_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.intermediate_outstand_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.intermediate_outstand_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.intermediate_outstand_input.setStyleSheet(
            "QTextEdit { border: 1px solid #d0d0d0; border-radius: 6px; background: #ffffff; "
            "color: #5b5b5b; font-size: 11px; }"
        )
        row = self._add_form_row(inputs_grid, row, "Outstand of Intermediate Stiffener (mm):", self.intermediate_outstand_input)

        self.longitudinal_combo = QComboBox()
        self.longitudinal_combo.addItems(VALUES_LONGITUDINAL_STIFFENER)
        apply_field_style(self.longitudinal_combo)
        self.longitudinal_combo.setFixedWidth(combo_width)
        self.longitudinal_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row = self._add_form_row(inputs_grid, row, "Longitudinal Stiffener:", self.longitudinal_combo)

        self.long_thick_combo = QComboBox()
        self.long_thick_combo.addItems(VALUES_STIFFENER_THICKNESS_MODE)
        apply_field_style(self.long_thick_combo)
        self.long_thick_combo.setFixedWidth(combo_width)
        self.long_thick_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row = self._add_form_row(inputs_grid, row, "Longitudinal Stiffener Thickness (mm):", self.long_thick_combo)

        left_layout.addLayout(inputs_grid)

        buckling_heading = QLabel("Web Buckling Details")
        buckling_heading.setStyleSheet("font-size: 11px; font-weight: 700; color: #000000; border: none; margin-top: 4px;")
        left_layout.addWidget(buckling_heading)

        buckling_grid = QGridLayout()
        buckling_grid.setContentsMargins(0, 0, 0, 0)
        buckling_grid.setHorizontalSpacing(12)
        buckling_grid.setVerticalSpacing(10)
        buckling_grid.setColumnMinimumWidth(0, self._form_label_width)

        self.method_combo = QComboBox()
        self.method_combo.addItems(VALUES_STIFFENER_DESIGN)
        apply_field_style(self.method_combo)
        self.method_combo.setFixedWidth(combo_width)
        self.method_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._add_form_row(buckling_grid, 0, "Shear Buckling Design Method:", self.method_combo)

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
        preview_top_layout.setSpacing(12)

        self.stiffener_cad_preview = StiffenerCadPreviewWidget()
        self.stiffener_cad_preview.setStyleSheet(
            "QWidget { border: 1px solid #d8d8d8; border-radius: 8px; background-color: #f8f8f8; }"
        )
        preview_top_layout.addWidget(self.stiffener_cad_preview, 3)
        preview_top_layout.addWidget(self._create_stiffener_legend_widget(), 1, Qt.AlignTop)

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
        self.intermediate_combo.currentTextChanged.connect(self._on_intermediate_changed)
        self.longitudinal_combo.currentTextChanged.connect(self._on_longitudinal_changed)
        self.intermediate_spacing_input.textChanged.connect(self._on_any_input_changed)
        self.intermediate_thick_combo.currentTextChanged.connect(self._on_any_input_changed)
        self.long_thick_combo.currentTextChanged.connect(self._on_any_input_changed)
        self.method_combo.currentTextChanged.connect(self._on_any_input_changed)
        self.apply_to_all_btn.clicked.connect(self._apply_current_to_all_members)

        # Defaults
        self._on_intermediate_changed(self.intermediate_combo.currentText())
        self._on_longitudinal_changed(self.longitudinal_combo.currentText())
        self.refresh_girder_members()
        self._update_dynamic_cad_preview()

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
        return {
            "bearing_stiffeners_each_end": "2",
            "bearing_spacing_mm": "",
            "bearing_thickness_mode": "All",
            "bearing_outstand_mm": OUTSTAND_DEFAULT_TEXT,
            "intermediate_stiffener": "No",
            "intermediate_spacing_mm": "NA",
            "intermediate_outstand_mm": OUTSTAND_DEFAULT_TEXT,
            "longitudinal_stiffener": "Yes and 1 stiffener",
            "intermediate_thickness_mode": "All",
            "longitudinal_thickness_mode": "All",
            "shear_buckling_method": VALUES_STIFFENER_DESIGN[0] if VALUES_STIFFENER_DESIGN else "",
        }

    def _store_current_member_state(self) -> None:
        if self._is_loading_ui:
            return
        if not self._active_member_id:
            return
        self._state_by_member[self._active_member_id] = {
            "bearing_stiffeners_each_end": self.bearing_count_combo.currentText(),
            "bearing_spacing_mm": self.bearing_spacing_input.text().strip(),
            "bearing_thickness_mode": self.bearing_thick_combo.currentText(),
            "bearing_outstand_mm": self.bearing_outstand_input.toPlainText().strip(),
            "intermediate_stiffener": self.intermediate_combo.currentText(),
            "intermediate_spacing_mm": self.intermediate_spacing_input.text().strip(),
            "intermediate_outstand_mm": self.intermediate_outstand_input.toPlainText().strip(),
            "longitudinal_stiffener": self.longitudinal_combo.currentText(),
            "intermediate_thickness_mode": self.intermediate_thick_combo.currentText(),
            "longitudinal_thickness_mode": self.long_thick_combo.currentText(),
            "shear_buckling_method": self.method_combo.currentText(),
        }
        self._update_dynamic_cad_preview()

    def _load_member_state(self, member_id: str) -> None:
        # Ensure every member has a state entry.
        if member_id not in self._state_by_member:
            self._state_by_member[member_id] = dict(self._default_member_state())
        state = dict(self._state_by_member.get(member_id) or self._default_member_state())

        self._is_loading_ui = True

        block_a = self.intermediate_combo.blockSignals(True)
        block_b = self.longitudinal_combo.blockSignals(True)
        block_c = self.method_combo.blockSignals(True)
        try:
            self.intermediate_combo.setCurrentText(state.get("intermediate_stiffener", "No"))
            self.longitudinal_combo.setCurrentText(state.get("longitudinal_stiffener", "Yes and 1 stiffener"))
            self.intermediate_thick_combo.setCurrentText(state.get("intermediate_thickness_mode", "All"))
            self.long_thick_combo.setCurrentText(state.get("longitudinal_thickness_mode", "All"))
            self.method_combo.setCurrentText(state.get("shear_buckling_method", self.method_combo.itemText(0)))

            self.bearing_count_combo.setCurrentText(state.get("bearing_stiffeners_each_end", "2"))
            self.bearing_spacing_input.setText(str(state.get("bearing_spacing_mm", "")))
            self.bearing_thick_combo.setCurrentText(state.get("bearing_thickness_mode", "All"))
            self.bearing_outstand_input.setText(state.get("bearing_outstand_mm", OUTSTAND_DEFAULT_TEXT))
            self.intermediate_outstand_input.setText(state.get("intermediate_outstand_mm", OUTSTAND_DEFAULT_TEXT))

            # spacing text is managed by _on_intermediate_changed
            self.intermediate_spacing_input.setText(str(state.get("intermediate_spacing_mm", "NA")))
        finally:
            self.intermediate_combo.blockSignals(block_a)
            self.longitudinal_combo.blockSignals(block_b)
            self.method_combo.blockSignals(block_c)
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
        value = computed if computed is not None else OUTSTAND_DEFAULT_TEXT
        prev_a = self.bearing_outstand_input.blockSignals(True)
        prev_b = self.intermediate_outstand_input.blockSignals(True)
        try:
            self.bearing_outstand_input.setText(value)
            self.intermediate_outstand_input.setText(value)
        finally:
            self.bearing_outstand_input.blockSignals(prev_a)
            self.intermediate_outstand_input.blockSignals(prev_b)

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



