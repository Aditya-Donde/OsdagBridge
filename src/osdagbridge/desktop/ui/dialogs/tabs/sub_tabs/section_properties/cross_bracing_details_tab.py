import sys
import os
import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar, QLabel, QLineEdit,
    QComboBox, QGroupBox, QFormLayout, QPushButton, QScrollArea,
    QCheckBox, QMessageBox, QSizePolicy, QSpacerItem, QStackedWidget,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QDialog, QSizeGrip
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QDoubleValidator, QIntValidator, QPainter, QPen, QColor

from osdagbridge.core.utils.common import *
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import CROSS_BRACING_DETAILS_SCHEMA
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.utils.cad_palette import CAD_DIMENSION
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.widgets.section_viewer import SectionPreviewWidget, SectionCatalog
from osdagbridge.desktop.ui.widgets.placeholder_section_preview import PlaceholderSectionPreviewWidget


class BracingLayoutCadWidget(QWidget):
    """Simple CAD-like bracing layout preview for K/X bracing."""

    def __init__(self, min_height: int = 170, parent=None):
        super().__init__(parent)
        self._bracing_type = "K-Bracing"
        self._top_chord = False
        self._bottom_chord = True
        self._member_label = ""
        self._girder_pair = ""
        self.setMinimumHeight(int(min_height))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_layout(
        self,
        bracing_type: str,
        top_chord: bool,
        bottom_chord: bool,
        member_label: str = "",
        girder_pair: str = "",
    ) -> None:
        self._bracing_type = (bracing_type or "K-Bracing").strip() or "K-Bracing"
        self._top_chord = bool(top_chord)
        self._bottom_chord = bool(bottom_chord)
        self._member_label = (member_label or "").strip()
        self._girder_pair = (girder_pair or "").strip()
        self.update()

    def paintEvent(self, _event):  # noqa: N802 (Qt naming)
        from PySide6.QtCore import QPointF
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Plain background (no outer border line).
        canvas = self.rect()
        painter.fillRect(canvas, QColor("#ffffff"))

        # Reserve extra bottom space for member/girder labels so they are never clipped.
        draw = canvas.adjusted(24, 14, -24, -38)
        if draw.width() <= 10 or draw.height() <= 10:
            return

        # Coordinates
        x_left = draw.left() + int(draw.width() * 0.15)
        x_right = draw.right() - int(draw.width() * 0.15)
        y_top = draw.top() + int(draw.height() * 0.10)
        y_bottom = draw.bottom() - int(draw.height() * 0.14)
        
        fw = 40  # flange width
        ft = 8   # flange thickness
        wt = 6   # web thickness

        # Connection points at web outer faces (clean two-line I-section look).
        x_l_conn = x_left + wt // 2
        x_r_conn = x_right - wt // 2

        strut_offset = 12
        y_T_WP = y_top + strut_offset if self._top_chord else y_top + 15
        y_B_WP = y_bottom - strut_offset if self._bottom_chord else y_bottom - 15

        wp_tl = QPointF(x_l_conn, y_T_WP)
        wp_tr = QPointF(x_r_conn, y_T_WP)
        wp_bl = QPointF(x_l_conn, y_B_WP)
        wp_br = QPointF(x_r_conn, y_B_WP)

        # Monochrome CAD style: line-only geometry, no fill shading.
        line_color = QColor("#000000")

        # 1. Draw top/bottom bracing lines based on current selection.
        painter.setPen(QPen(line_color, 2))
        if self._top_chord:
            painter.drawLine(wp_tl, wp_tr)
        if self._bottom_chord:
            painter.drawLine(wp_bl, wp_br)

        # 2. Draw Bracing Members
        brace_pen = QPen(line_color, 2)
        brace_pen.setCapStyle(Qt.RoundCap)
        brace_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(brace_pen)
        
        if self._bracing_type == "K-Bracing":
            if self._top_chord and not self._bottom_chord:
                apex = QPointF((x_l_conn + x_r_conn) / 2.0, y_T_WP)
                painter.drawLine(wp_bl, apex)
                painter.drawLine(wp_br, apex)
            else:
                apex = QPointF((x_l_conn + x_r_conn) / 2.0, y_B_WP)
                painter.drawLine(wp_tl, apex)
                painter.drawLine(wp_tr, apex)
        else:
            painter.drawLine(wp_tl, wp_br)
            painter.drawLine(wp_bl, wp_tr)

        # 3. Draw I-Girders
        painter.setPen(QPen(line_color, 1.6))
        painter.setBrush(Qt.NoBrush)

        # Girder body outlines (double-line geometry with flange/web rectangles)
        # Left Girder
        painter.drawRect(int(x_left - fw//2), int(y_top - ft), fw, ft)
        painter.drawRect(int(x_left - fw//2), int(y_bottom), fw, ft)
        painter.drawRect(int(x_left - wt//2), int(y_top), wt, int(y_bottom - y_top))

        # Right Girder
        painter.drawRect(int(x_right - fw//2), int(y_top - ft), fw, ft)
        painter.drawRect(int(x_right - fw//2), int(y_bottom), fw, ft)
        painter.drawRect(int(x_right - wt//2), int(y_top), wt, int(y_bottom - y_top))

        # 4. Label boxes below the girders (no arrows/leaders).

        def compact_member_label(raw_text: str) -> str:
            text = (raw_text or "").strip()
            if " to " in text:
                parts = [part.strip() for part in text.split(" to ", 1)]
                if len(parts) == 2 and parts[0] and parts[1]:
                    return f"{parts[0]} - {parts[1]}"
            return text or "B1M1"

        pair_text = self._girder_pair or "G1 to G2"
        left_girder, right_girder = "G1", "G2"
        if " to " in pair_text:
            parts = [part.strip() for part in pair_text.split(" to ", 1)]
            if len(parts) == 2 and parts[0] and parts[1]:
                left_girder, right_girder = parts[0], parts[1]

        pen = QPen(CAD_DIMENSION, 1.1)
        painter.setPen(pen)

        label_bg = QColor(255, 255, 255, 225)
        pad_x = 6
        pad_y = 3

        def draw_label_box(text: str, center_x: float, box_y: float, font_size: int = 8) -> None:
            if not text:
                return
            
            f = painter.font()
            f.setPointSize(font_size)
            f.setBold(True)
            painter.setFont(f)
            fm = painter.fontMetrics()

            txt_w = fm.horizontalAdvance(text)
            txt_h = fm.height()
            box_w = txt_w + (2 * pad_x)
            box_h = txt_h + (2 * pad_y)

            box_x = center_x - (box_w / 2.0)
            # Keep labels visible while preserving a common baseline.
            box_x = max(8.0, min(box_x, self.width() - box_w - 8.0))
            box_y = max(8.0, min(box_y, self.height() - box_h - 8.0))

            # Draw label box
            painter.setPen(Qt.NoPen)
            painter.setBrush(label_bg)
            painter.drawRoundedRect(int(box_x), int(box_y), int(box_w), int(box_h), 4, 4)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(CAD_DIMENSION, 1.0))
            painter.drawText(int(box_x + pad_x), int(box_y + box_h - pad_y - 2), text)

        # Uniform row under girders: left, center, right labels with equal spacing.
        member_text = compact_member_label(self._member_label)
        label_y = y_bottom + ft + 12
        mid_x = (x_left + x_right) / 2.0

        draw_label_box(f"Girder {left_girder}", x_left, label_y, 8)
        draw_label_box(member_text, mid_x, label_y, 11)
        draw_label_box(f"Girder {right_girder}", x_right, label_y, 8)


class _CrossBracingDetailsSchemaBuilder:
    """Local schema-driven widget builder for Cross Bracing tab."""

    def __init__(self, owner: QWidget):
        self.owner = owner

    def create_widget(self, field_def: dict) -> QWidget:
        field_type = str(field_def.get("type") or "line").strip().lower()

        if field_type in {"combo", "combo_dynamic"}:
            widget = QComboBox()
            for choice in field_def.get("choices") or []:
                widget.addItem(str(choice))
            default = field_def.get("default")
            if default is not None:
                widget.setCurrentText(str(default))
            self.owner._configure_combo_box(widget)

        elif field_type == "checkbox":
            widget = QCheckBox()
            widget.setChecked(bool(field_def.get("default", False)))
            widget.setFixedHeight(28)
            widget.setStyleSheet("margin-left: 2px;")

        else:
            widget = QLineEdit()
            default = field_def.get("default")
            if default is not None:
                widget.setText(str(default))
            self._apply_validator(widget, field_def.get("validator"))
            if bool(field_def.get("read_only", False)):
                widget.setReadOnly(True)
                try:
                    widget.setFocusPolicy(Qt.NoFocus)
                except Exception:
                    pass

        if field_type not in {"checkbox"}:
            apply_field_style(widget)

        if isinstance(widget, QLineEdit):
            widget.setFixedSize(self.owner._combo_width, 28)
            widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        elif isinstance(widget, QComboBox):
            widget.setFixedHeight(28)
            widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        field_id = str(field_def.get("id") or "").strip()
        if field_id:
            widget.setObjectName(field_id)

        bind_name = str(field_def.get("bind") or "").strip()
        if bind_name:
            setattr(self.owner, bind_name, widget)

        self._connect_handlers(widget, field_def)
        return widget

    def _apply_validator(self, widget: QLineEdit, validator_def: dict | None) -> None:
        if not validator_def:
            return

        vtype = str(validator_def.get("type") or "").strip().lower()
        if vtype == "double_range":
            bottom = float(validator_def.get("bottom", 0.0))
            top = float(validator_def.get("top", 1e12))
            decimals = int(validator_def.get("decimals", 3))
            widget.setValidator(QDoubleValidator(bottom, top, decimals, widget))
            return

        if vtype == "int_range":
            bottom = int(validator_def.get("bottom", 0))
            top = int(validator_def.get("top", 1_000_000_000))
            widget.setValidator(QIntValidator(bottom, top, widget))

    def _connect_handlers(self, widget: QWidget, field_def: dict) -> None:
        owner = self.owner

        on_change = field_def.get("on_change")
        if on_change and isinstance(widget, QComboBox):
            handler = getattr(owner, str(on_change), None)
            if callable(handler):
                widget.currentTextChanged.connect(handler)

        on_text_changed = field_def.get("on_text_changed")
        if on_text_changed and isinstance(widget, QLineEdit):
            handler = getattr(owner, str(on_text_changed), None)
            if callable(handler):
                widget.textChanged.connect(handler)

        on_editing_finished = field_def.get("on_editing_finished")
        if on_editing_finished and isinstance(widget, QLineEdit):
            handler = getattr(owner, str(on_editing_finished), None)
            if callable(handler):
                widget.editingFinished.connect(handler)

        on_toggled = field_def.get("on_toggled")
        if on_toggled and isinstance(widget, QCheckBox):
            handler = getattr(owner, str(on_toggled), None)
            if callable(handler):
                widget.toggled.connect(handler)

class CrossBracingDetailsTab(QWidget):
    """Tab for Cross-Bracing Details with visual previews"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.catalog = SectionCatalog()
        self._schema_builder = _CrossBracingDetailsSchemaBuilder(self)
        self._girder_details_tab = None
        self._global_design_mode = "Optimized"
        self._field_widgets: dict[str, QWidget] = {}

        # Keep all combo boxes strictly uniform in width.
        self._combo_width = 190
        # Keep label columns uniform across all left-panel grids.
        self._label_col_width = 260

        # Persist UI state per (girder-pair, member-id) so switching selection
        # restores user inputs for that specific member.
        self._state_by_member_key: dict[str, dict] = {}
        self._active_member_key: str | None = None
        self._selection_sync_guard = False
        self._updating_chord_rules = False
        self.init_ui()

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

        primary_card = self._create_card_frame()
        card_layout = QHBoxLayout(primary_card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(12)

        # Left column (inputs)
        left_column = QWidget()
        left_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        selection_box = self._create_inner_box()
        selection_layout = QGridLayout(selection_box)
        selection_layout.setContentsMargins(12, 8, 12, 8)
        selection_layout.setHorizontalSpacing(12)
        selection_layout.setVerticalSpacing(8)
        selection_layout.setColumnMinimumWidth(0, int(self._label_col_width))
        selection_layout.setColumnMinimumWidth(1, int(self._combo_width))
        selection_layout.setColumnStretch(0, 0)
        selection_layout.setColumnStretch(1, 1)

        self._build_overview_inputs_from_schema(selection_layout)
        self._bind_widgets_from_schema("overview")

        self.member_id_combo = QComboBox()
        # Populated from Girder Details when bound. (No Custom option.)
        self._configure_combo_box(self.member_id_combo)
        # Member IDs are software-generated and must not be typed/edited.
        self.member_id_combo.setEditable(False)
        try:
            self.member_id_combo.setInsertPolicy(QComboBox.NoInsert)
        except Exception:
            pass
        # Hide the dropdown entirely; show a read-only display instead.
        self.member_id_combo.setVisible(False)

        # Keep the two selectors aligned and persist state per selection.
        self.select_girders_combo.currentIndexChanged.connect(self._on_select_girders_index_changed)

        selection_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        left_layout.addWidget(selection_box)

        inputs_box = self._create_inner_box()
        inputs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        inputs_layout = QVBoxLayout(inputs_box)
        inputs_layout.setContentsMargins(12, 8, 12, 8)
        inputs_layout.setSpacing(6)
        inputs_layout.addWidget(self._create_heading_label("Section Inputs:"))

        inputs_grid = QGridLayout()
        inputs_grid.setContentsMargins(0, 0, 0, 0)
        inputs_grid.setHorizontalSpacing(12)
        inputs_grid.setVerticalSpacing(8)
        inputs_grid.setColumnMinimumWidth(0, int(self._label_col_width))
        inputs_grid.setColumnMinimumWidth(1, int(self._combo_width))
        inputs_grid.setColumnStretch(0, 0)
        inputs_grid.setColumnStretch(1, 1)

        self._build_section_inputs_from_schema(inputs_grid)
        self._bind_widgets_from_schema("section_inputs")

        inputs_layout.addLayout(inputs_grid)
        left_layout.addWidget(inputs_box)
        left_layout.addStretch(1)

        card_layout.addWidget(left_column)

        # Right column (previews)
        right_column = QWidget()
        self.right_column = right_column
        right_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Match End Diaphragm cross-bracing view: show a bracing-layout diagram at the top.
        type_box = self._create_inner_box()
        type_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        type_layout = QVBoxLayout(type_box)
        type_layout.setContentsMargins(12, 8, 12, 10)
        type_layout.setSpacing(6)
        type_layout.addWidget(self._create_heading_label(self._schema_label("bracing_type", "Type of Bracing:").rstrip(":")))
        self.bracing_layout_widget = BracingLayoutCadWidget(170)
        self.bracing_layout_widget.setFixedHeight(170)
        type_layout.addWidget(self.bracing_layout_widget)
        right_layout.addWidget(type_box)

        self.bracing_preview_box, self.bracing_preview_label = self._create_preview_box("Bracing")
        right_layout.addWidget(self.bracing_preview_box)

        self.top_chord_preview_box, self.top_chord_preview_label = self._create_preview_box("Top Chord")
        right_layout.addWidget(self.top_chord_preview_box)

        self.bottom_chord_preview_box, self.bottom_chord_preview_label = self._create_preview_box("Bottom Chord")
        right_layout.addWidget(self.bottom_chord_preview_box)

        right_layout.addStretch()

        card_layout.addWidget(right_column)
        # Keep both panels visually balanced like Girder Details.
        card_layout.setStretch(0, 1)
        card_layout.setStretch(1, 1)
        container_layout.addWidget(primary_card)
        container_layout.addStretch()

        self.bracing_type_combo.currentTextChanged.connect(self._update_previews)
        self.bracing_type_combo.currentTextChanged.connect(self._on_bracing_layout_changed)
        self.bracing_section_type_combo.currentTextChanged.connect(self._on_bracing_type_changed)
        self.bracing_section_combo.currentTextChanged.connect(self._update_previews)
        self.top_chord_checkbox.toggled.connect(self._on_bracing_layout_changed)
        self.top_chord_type_combo.currentTextChanged.connect(self._on_top_chord_type_changed)
        self.top_chord_size_combo.currentTextChanged.connect(self._update_previews)
        self.bottom_chord_checkbox.toggled.connect(self._on_bracing_layout_changed)
        self.bottom_chord_type_combo.currentTextChanged.connect(self._on_bottom_chord_type_changed)
        self.bottom_chord_size_combo.currentTextChanged.connect(self._update_previews)
        self.design_combo.currentTextChanged.connect(self._on_design_changed)
        self.spacing_input.textChanged.connect(self._on_span_or_spacing_changed)
        self._populate_designations()
        self._on_design_changed(self._global_design_mode)

        # Seed selection drop-downs with a safe default until Girder Details is bound.
        self.refresh_girder_options()

        # Ensure initial selection loads its saved/default state.
        self._load_state_for_current_member()
        self._on_bracing_layout_changed()

    def _on_span_or_spacing_changed(self, *_args) -> None:
        # Member IDs are derived from Span + Spacing (software-driven).
        try:
            self._refresh_member_id_display()
        except Exception:
            pass

    def _current_member_id(self) -> str:
        return f"B{self._pair_index()}M1"

    def _current_member_key(self) -> str:
        pair = (self.select_girders_combo.currentText() or "").strip()
        member = self._current_member_id()
        return f"{pair}::{member}".strip(":")

    @staticmethod
    def _normalize_member_id(text: str, pair_index: int | None = None) -> str:
        """Normalize legacy IDs/ranges to the canonical format B{pair}M{member}.

        Accepts:
        - 'B1M3' (canonical)
        - 'B1-3' (legacy hyphen)
        - 'B1-1 to B1-15' (legacy range; coerces to M1)
        """
        raw = (text or "").strip().replace(" ", "")
        if not raw:
            return ""

        upper = raw.upper()

        # Canonical already.
        if "M" in upper and upper.startswith("B"):
            return upper

        # Legacy range like B1-1toB1-15 -> choose first.
        if upper.startswith("B") and "TO" in upper:
            # Try to keep the pair index if provided.
            if pair_index is not None:
                return f"B{pair_index}M1"
            # Attempt to parse pair number from prefix.
            try:
                after_b = upper[1:]
                pair_num = int("".join(ch for ch in after_b if ch.isdigit()) or 0)
            except Exception:
                pair_num = 0
            return f"B{pair_num}M1" if pair_num > 0 else ""

        # Legacy single member like B1-3.
        if upper.startswith("B") and "-" in upper:
            try:
                b_part, m_part = upper.split("-", 1)
                pair_num = int(b_part[1:])
                mem_num = int("".join(ch for ch in m_part if ch.isdigit()))
                return f"B{pair_num}M{mem_num}"
            except Exception:
                return ""

        # Fallback: if only a member number is present and pair_index is known.
        if pair_index is not None:
            try:
                mem_num = int("".join(ch for ch in upper if ch.isdigit()))
                if mem_num > 0:
                    return f"B{pair_index}M{mem_num}"
            except Exception:
                pass
        return ""

    @staticmethod
    def _member_number(text: str) -> int | None:
        text = (text or "").strip().upper().replace(" ", "")
        if not text:
            return None
        if text.startswith("B") and "M" in text:
            try:
                _b, m = text.split("M", 1)
                return int("".join(ch for ch in m if ch.isdigit()) or 0) or None
            except Exception:
                return None
        if text.startswith("B") and "-" in text:
            try:
                _b, m = text.split("-", 1)
                return int("".join(ch for ch in m if ch.isdigit()) or 0) or None
            except Exception:
                return None
        return None

    def _pair_index(self) -> int:
        return max(0, int(self.select_girders_combo.currentIndex())) + 1

    def _get_total_span_m(self) -> float | None:
        tab = self._girder_details_tab
        if tab is None:
            return None
        getter = getattr(tab, "_get_total_span", None)
        if getter is None or not callable(getter):
            return None
        try:
            span = getter()
        except Exception:
            return None
        try:
            span = float(span)
        except Exception:
            return None
        return span if span > 0 else None

    def _get_cross_bracing_spacing_m(self) -> float | None:
        text = (self.spacing_input.text() or "").strip()
        if not text:
            return None
        try:
            spacing_m = float(text)
        except Exception:
            return None
        if spacing_m <= 0:
            return None
        return spacing_m

    def _cross_bracing_member_count(self) -> int:
        """Compute number of cross bracing members (m) for a pair.

        Based on the provided reference:
            m = Span / CrossBracingSpacing - 1

        Span is read from Girder Details "Total Span (m)".
        Spacing is read from this tab "Spacing (m)".
        """
        span_m = self._get_total_span_m()
        spacing_m = self._get_cross_bracing_spacing_m()
        if not span_m or not spacing_m:
            return 1
        raw = (span_m / spacing_m) - 1.0
        try:
            m = int(math.floor(raw + 1e-9))
        except Exception:
            m = 1
        return max(1, m)

    def _member_ids_for_pair(self, pair_index: int) -> list[str]:
        count = self._cross_bracing_member_count()
        return [f"B{pair_index}M{i}" for i in range(1, count + 1)]

    def _refresh_member_id_display(self) -> None:
        pair_index = self._pair_index()
        count = self._cross_bracing_member_count()
        member_id = f"B{pair_index}M1"
        display_text = member_id if count <= 1 else f"B{pair_index}M1 to B{pair_index}M{count}"
        if hasattr(self, "member_id_display") and self.member_id_display is not None:
            prev = self.member_id_display.blockSignals(True)
            try:
                self.member_id_display.setText(display_text)
            finally:
                self.member_id_display.blockSignals(prev)

        # Keep the hidden combo in sync for any existing code paths.
        block = self.member_id_combo.blockSignals(True)
        try:
            self.member_id_combo.clear()
            self.member_id_combo.addItems([member_id])
            self.member_id_combo.setCurrentIndex(0)
        finally:
            self.member_id_combo.blockSignals(block)

    def _default_member_state(self) -> dict:
        # Use schema defaults/choices for new members.
        state: dict[str, object] = {}
        for field in self._schema_fields("section_inputs"):
            field_id = str(field.get("id") or "").strip()
            if not field_id:
                continue
            field_type = str(field.get("type") or "line").strip().lower()
            if field_type in {"combo", "combo_dynamic"}:
                choices = self._schema_choices(field_id, [])
                fallback = choices[0] if choices else ""
                state[field_id] = str(self._schema_default(field_id, fallback))
            elif field_type == "checkbox":
                state[field_id] = bool(self._schema_default(field_id, False))
            else:
                state[field_id] = str(self._schema_default(field_id, ""))

        # Keep extra designation metadata for robust restore.
        state["bracing_section_data"] = None
        state["bracing_section_text"] = ""
        state["top_chord_data"] = None
        state["top_chord_text"] = ""
        state["bottom_chord_data"] = None
        state["bottom_chord_text"] = ""
        return state

    def _schema_fields(self, section: str) -> list[dict]:
        """Return normalized schema field dicts for a section.

        Filters non-dict entries and returns shallow copies so callers can work
        with a stable list without mutating source schema objects.
        """
        return [dict(field) for field in CROSS_BRACING_DETAILS_SCHEMA.get(section, []) if isinstance(field, dict)]

    def _bind_widgets_from_schema(self, section: str) -> None:
        """Bind registered widgets to schema-declared attribute names.

        For each field with both `id` and `bind`, finds the registered widget
        and sets `self.<bind>` to that widget.
        """
        for field in self._schema_fields(section):
            field_id = str(field.get("id") or "").strip()
            bind_name = str(field.get("bind") or "").strip()
            if not field_id or not bind_name:
                continue

            widget = self._widget_for_field(field_id)
            if widget is None:
                continue
            setattr(self, bind_name, widget)

    def _register_field_widget(self, field_id: str, widget: QWidget) -> None:
        """Register a created field widget under its schema field id."""
        key = str(field_id or "").strip()
        if key:
            self._field_widgets[key] = widget

    def _widget_for_field(self, field_id: str):
        """Return the registered widget for a schema field id, if present."""
        return self._field_widgets.get(str(field_id or "").strip())

    def _schema_field_def(self, field_id: str) -> dict:
        """Find and return a single schema field definition by id.

        Searches both `overview` and `section_inputs`. Returns empty dict when
        no matching field exists.
        """
        target = str(field_id or "").strip()
        if not target:
            return {}
        for section in ("overview", "section_inputs"):
            for field in self._schema_fields(section):
                if str(field.get("id") or "").strip() == target:
                    return field
        return {}

    def _schema_label(self, field_id: str, fallback: str) -> str:
        """Resolve field label from schema with fallback text."""
        field = self._schema_field_def(field_id)
        label = field.get("label")
        return str(label if label is not None else fallback)

    def _schema_choices(self, field_id: str, fallback: list[str]) -> list[str]:
        """Resolve combo choices from schema with fallback list."""
        field = self._schema_field_def(field_id)
        choices = field.get("choices") or fallback
        return [str(choice) for choice in choices]

    def _schema_default(self, field_id: str, fallback):
        """Resolve field default value from schema with fallback."""
        field = self._schema_field_def(field_id)
        return field.get("default", fallback)

    def _apply_double_validator_from_schema(
        self,
        line_edit: QLineEdit,
        field_id: str,
        fallback_bottom: float,
        fallback_top: float,
        fallback_decimals: int,
    ) -> None:
        """Apply a numeric range validator using schema validator metadata.

        Uses fallback bounds/decimals when validator metadata is absent.
        """
        field = self._schema_field_def(field_id)
        validator = field.get("validator") if isinstance(field.get("validator"), dict) else {}
        bottom = float(validator.get("bottom", fallback_bottom))
        top = float(validator.get("top", fallback_top))
        decimals = int(validator.get("decimals", fallback_decimals))
        line_edit.setValidator(QDoubleValidator(bottom, top, decimals))

    def _create_widget_from_schema(self, field_def: dict):
        """Create a widget from schema via local schema builder."""
        return self._schema_builder.create_widget(field_def)

    def _build_overview_select_girders_field(self, selection_layout: QGridLayout, row: int, field_def: dict, widget: QWidget) -> int:
        """Render the schema-defined `select_girders` overview row."""
        field_id = str(field_def.get("id") or "")
        self._register_field_widget(field_id, widget)
        label = self._schema_label(field_id, str(field_def.get("label") or ""))
        selection_layout.addWidget(self._create_label(label), row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        selection_layout.addWidget(widget, row, 1, Qt.AlignLeft | Qt.AlignVCenter)
        return row + 1

    def _build_overview_member_id_field(self, selection_layout: QGridLayout, row: int, field_def: dict, widget: QWidget) -> int:
        """Render the schema-defined `member_id` overview row."""
        field_id = str(field_def.get("id") or "")
        self._register_field_widget(field_id, widget)
        label = self._schema_label(field_id, str(field_def.get("label") or ""))
        selection_layout.addWidget(self._create_label(label), row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        selection_layout.addWidget(widget, row, 1, Qt.AlignLeft | Qt.AlignVCenter)
        return row + 1

    def _overview_schema_handlers(self) -> dict[tuple[str, str], callable]:
        """Return dispatch map for overview field-specific builders."""
        return {
            ("id", "select_girders"): self._build_overview_select_girders_field,
            ("id", "member_id"): self._build_overview_member_id_field,
        }

    def _build_overview_field_from_schema(self, selection_layout: QGridLayout, row: int, field_def: dict) -> int:
        """Build one overview row using handler dispatch + schema metadata."""
        field_id = str(field_def.get("id") or "")
        field_type = str(field_def.get("type") or "").strip().lower()
        widget = self._schema_builder.create_widget(field_def)

        handlers = self._overview_schema_handlers()
        handler = handlers.get(("id", field_id)) or handlers.get(("type", field_type))
        if handler is not None:
            return handler(selection_layout, row, field_def, widget)

        self._register_field_widget(field_id, widget)
        label = self._schema_label(field_id, str(field_def.get("label") or ""))
        selection_layout.addWidget(self._create_label(label), row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        selection_layout.addWidget(widget, row, 1, Qt.AlignLeft | Qt.AlignVCenter)
        return row + 1

    def _build_overview_inputs_from_schema(self, selection_layout: QGridLayout) -> None:
        """Build all overview rows from schema order."""
        row = 0
        for field in self._schema_fields("overview"):
            row = self._build_overview_field_from_schema(selection_layout, row, field)

    def _build_section_hidden_design_field(self, inputs_grid: QGridLayout, row: int, field_def: dict) -> int:
        """Build hidden design control row (stored but not shown in UI)."""
        field_id = str(field_def.get("id") or "")
        widget = self._schema_builder.create_widget(field_def)
        self._register_field_widget(field_id, widget)
        widget.setVisible(False)
        return row

    def _build_section_standard_field(self, inputs_grid: QGridLayout, row: int, field_def: dict) -> int:
        """Build a standard visible section-input row from schema."""
        field_id = str(field_def.get("id") or "")
        widget = self._schema_builder.create_widget(field_def)
        self._register_field_widget(field_id, widget)
        row = self._add_grid_row(inputs_grid, row, self._schema_label(field_id, str(field_def.get("label") or "")), widget)

        if field_id == "spacing" and isinstance(widget, QLineEdit):
            self._apply_double_validator_from_schema(widget, "spacing", 0.0, 100000.0, 2)
        return row

    def _section_schema_handlers(self) -> dict[tuple[str, str], callable]:
        """Return dispatch map for section-input field builders."""
        return {
            ("id", "design"): self._build_section_hidden_design_field,
            ("type", "combo"): self._build_section_standard_field,
            ("type", "combo_dynamic"): self._build_section_standard_field,
            ("type", "checkbox"): self._build_section_standard_field,
            ("type", "line"): self._build_section_standard_field,
        }

    def _build_section_input_from_schema(self, inputs_grid: QGridLayout, row: int, field_def: dict) -> int:
        """Build one section-input row using id/type handler dispatch."""
        field_id = str(field_def.get("id") or "")
        field_type = str(field_def.get("type") or "").strip().lower()

        handlers = self._section_schema_handlers()
        handler = handlers.get(("id", field_id)) or handlers.get(("type", field_type))
        if handler is not None:
            return handler(inputs_grid, row, field_def)

        return self._build_section_standard_field(inputs_grid, row, field_def)

    def _build_section_inputs_from_schema(self, inputs_grid: QGridLayout) -> None:
        """Build all section-input rows from schema order."""
        row = 0
        for field in self._schema_fields("section_inputs"):
            row = self._build_section_input_from_schema(inputs_grid, row, field)

    def _snapshot_current_state(self) -> dict:
        """Capture current UI state for the active pair/member selection.

        Includes schema-driven section-input values and extra designation data
        required for robust combo restore (data/text for section selections).
        """
        state: dict[str, object] = {}
        for field in self._schema_fields("section_inputs"):
            field_id = str(field.get("id") or "").strip()
            if not field_id:
                continue
            widget = self._widget_for_field(field_id)
            if isinstance(widget, QCheckBox):
                state[field_id] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                state[field_id] = widget.currentText()
            elif isinstance(widget, QLineEdit):
                state[field_id] = widget.text()

        state["design"] = self._global_design_mode
        state["bracing_section_data"] = self.bracing_section_combo.currentData()
        state["bracing_section_text"] = self.bracing_section_combo.currentText()
        state["top_chord_data"] = self.top_chord_size_combo.currentData()
        state["top_chord_text"] = self.top_chord_size_combo.currentText()
        state["bottom_chord_data"] = self.bottom_chord_size_combo.currentData()
        state["bottom_chord_text"] = self.bottom_chord_size_combo.currentText()
        return state

    def _store_current_member_state(self) -> None:
        if not hasattr(self, "select_girders_combo") or not hasattr(self, "member_id_combo"):
            return
        key = self._active_member_key or self._current_member_key()
        if not key:
            return
        self._state_by_member_key[key] = self._snapshot_current_state()
        self._active_member_key = key

    def _set_combo_to_data_or_text(self, combo: QComboBox, desired_data, desired_text: str) -> None:
        if desired_data is not None:
            idx = combo.findData(desired_data)
            if idx >= 0:
                combo.setCurrentIndex(idx)
                return
        if desired_text:
            idx = combo.findText(desired_text)
            if idx >= 0:
                combo.setCurrentIndex(idx)

    def _apply_state(self, state: dict) -> None:
        # Apply in a safe order: set section types first (to repopulate size combos),
        # then set sizes, then design mode.
        self.design_combo.setCurrentText(self._global_design_mode)
        self.bracing_type_combo.setCurrentText(state.get("bracing_type") or self.bracing_type_combo.currentText())

        self.bracing_section_type_combo.setCurrentText(state.get("bracing_section_type") or self.bracing_section_type_combo.currentText())
        self._update_designations_for(self.bracing_section_combo, self.bracing_section_type_combo.currentText())
        self._set_combo_to_data_or_text(
            self.bracing_section_combo,
            state.get("bracing_section_data"),
            state.get("bracing_section_text") or "",
        )

        self.top_chord_checkbox.setChecked(bool(state.get("top_chord_enabled", False)))

        self.top_chord_type_combo.setCurrentText(state.get("top_chord_type") or self.top_chord_type_combo.currentText())
        self._update_designations_for(self.top_chord_size_combo, self.top_chord_type_combo.currentText())
        self._set_combo_to_data_or_text(
            self.top_chord_size_combo,
            state.get("top_chord_data"),
            state.get("top_chord_text") or "",
        )

        # For K-bracing, bottom chord is mandatory.
        effective_bracing = (state.get("bracing_type") or self.bracing_type_combo.currentText() or "").strip()
        if effective_bracing == "K-Bracing":
            self.bottom_chord_checkbox.setChecked(True)
        else:
            self.bottom_chord_checkbox.setChecked(bool(state.get("bottom_chord_enabled", True)))

        self.bottom_chord_type_combo.setCurrentText(state.get("bottom_chord_type") or self.bottom_chord_type_combo.currentText())
        self._update_designations_for(self.bottom_chord_size_combo, self.bottom_chord_type_combo.currentText())
        self._set_combo_to_data_or_text(
            self.bottom_chord_size_combo,
            state.get("bottom_chord_data"),
            state.get("bottom_chord_text") or "",
        )

        self.spacing_input.setText(state.get("spacing") or "")
        self._on_bracing_layout_changed()

        # Ensure enable/disable and previews match the restored design state.
        self._on_design_changed(self._global_design_mode)

    def _load_state_for_current_member(self) -> None:
        key = self._current_member_key()
        if not key:
            return
        self._active_member_key = key
        state = self._state_by_member_key.get(key)
        if state is None:
            state = self._default_member_state()
        guard_a = self.design_combo.blockSignals(True)
        guard_b = self.bracing_type_combo.blockSignals(True)
        guard_c = self.bracing_section_type_combo.blockSignals(True)
        guard_d = self.bracing_section_combo.blockSignals(True)
        guard_d2 = self.top_chord_checkbox.blockSignals(True)
        guard_e = self.top_chord_type_combo.blockSignals(True)
        guard_f = self.top_chord_size_combo.blockSignals(True)
        guard_g2 = self.bottom_chord_checkbox.blockSignals(True)
        guard_g = self.bottom_chord_type_combo.blockSignals(True)
        guard_h = self.bottom_chord_size_combo.blockSignals(True)
        try:
            self._apply_state(state)
        finally:
            self.design_combo.blockSignals(guard_a)
            self.bracing_type_combo.blockSignals(guard_b)
            self.bracing_section_type_combo.blockSignals(guard_c)
            self.bracing_section_combo.blockSignals(guard_d)
            self.top_chord_checkbox.blockSignals(guard_d2)
            self.top_chord_type_combo.blockSignals(guard_e)
            self.top_chord_size_combo.blockSignals(guard_f)
            self.bottom_chord_checkbox.blockSignals(guard_g2)
            self.bottom_chord_type_combo.blockSignals(guard_g)
            self.bottom_chord_size_combo.blockSignals(guard_h)

        # After restoring, refresh previews explicitly.
        self._update_previews()

    def _on_select_girders_index_changed(self, idx: int) -> None:
        if self._selection_sync_guard:
            return
        self._store_current_member_state()
        self._selection_sync_guard = True
        try:
            self._refresh_member_id_display()
        finally:
            self._selection_sync_guard = False
        self._load_state_for_current_member()

    def bind_girder_details_tab(self, girder_details_tab) -> None:
        """Bind to Girder Details so girder pair options reflect user inputs."""
        self._girder_details_tab = girder_details_tab
        try:
            length_input = getattr(girder_details_tab, "length_input", None)
            if length_input is not None and hasattr(length_input, "textChanged"):
                length_input.textChanged.connect(self._on_span_or_spacing_changed)
        except Exception:
            pass
        self.refresh_girder_options()

    def showEvent(self, event):  # noqa: N802 (Qt naming)
        super().showEvent(event)
        # When the tab becomes visible, refresh in case girder count changed.
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
        """Populate Select Girders + Member ID based on Girder Details."""
        # Save current member state before rebuilding lists.
        try:
            self._store_current_member_state()
        except Exception:
            pass
        pairs = self._girder_pairs()

        prev_pair = self.select_girders_combo.currentText().strip() if hasattr(self, "select_girders_combo") else ""

        block_a = self.select_girders_combo.blockSignals(True)
        try:
            self.select_girders_combo.clear()
            self.select_girders_combo.addItems(pairs)
            if prev_pair in pairs:
                self.select_girders_combo.setCurrentText(prev_pair)
            else:
                self.select_girders_combo.setCurrentIndex(0)
        finally:
            self.select_girders_combo.blockSignals(block_a)

        # Update the (read-only) Member ID display for the selected pair.
        self._refresh_member_id_display()

        # Restore saved/default state for the currently selected member after refresh.
        self._load_state_for_current_member()

    def _create_card_frame(self):
        card = QFrame()
        card.setStyleSheet("QFrame { border: 1px solid #d0d0d0; border-radius: 12px; background-color: #ffffff; }")
        return card

    def _create_inner_box(self):
        box = QFrame()
        box.setStyleSheet(
            "QFrame { border: 1px solid #cfcfcf; border-radius: 8px; background-color: #ffffff; }"
            "QFrame QComboBox, QFrame QLineEdit { border: none; border-bottom: 1px solid #d0d0d0; border-radius: 0px; min-height: 28px; padding: 4px 8px; background-color: #ffffff; }"
            "QFrame QComboBox:hover, QFrame QLineEdit:hover { border-bottom: 1px solid #5d5d5d; }"
            "QFrame QComboBox:focus, QFrame QLineEdit:focus { border-bottom: 1px solid #90AF13; }"
            "QFrame QLabel { border: none; }"
        )
        return box

    def _normalize_label_text(self, text: str) -> str:
        return str(text or "").rstrip(": ")

    def _create_heading_label(self, text):
        label = QLabel(self._normalize_label_text(text))
        label.setStyleSheet("font-size: 12px; font-weight: 700; color: #4b4b4b; border: none;")
        return label

    def _create_label(self, text):
        label = QLabel(self._normalize_label_text(text))
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
        # Left-align the widget so fixed-width combos line up.
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

    def _create_bracing_layout_placeholder(self, text: str, height: int):
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumHeight(height)
        label.setStyleSheet(
            "QLabel { border: 1px solid #d0d0d0; border-radius: 10px; background-color: #f7f7f7; "
            "font-weight: bold; color: #5b5b5b; }"
        )
        return label

    def _create_preview_box(self, title):
        box = self._create_inner_box()
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 12px; font-weight: 700; color: #4b4b4b; border: none;")
        layout.addWidget(heading)
        image = PlaceholderSectionPreviewWidget(title, 110)
        image.setFixedHeight(110)
        layout.addWidget(image)
        box.setFixedHeight(154)
        return box, image

    def _update_previews(self):
        if self.design_combo.currentText() != "Custom":
            # Hide geometry when optimization controls the section selection.
            for widget in [
                self.bracing_preview_label,
                self.top_chord_preview_label,
                self.bottom_chord_preview_label,
            ]:
                widget.set_section("", "")
            return
        self._set_preview(self.bracing_preview_label, self.bracing_section_type_combo, self.bracing_section_combo)
        if self.top_chord_checkbox.isChecked():
            self._set_preview(self.top_chord_preview_label, self.top_chord_type_combo, self.top_chord_size_combo)
        else:
            self.top_chord_preview_label.set_section("", "")
        if self.bottom_chord_checkbox.isChecked():
            self._set_preview(self.bottom_chord_preview_label, self.bottom_chord_type_combo, self.bottom_chord_size_combo)
        else:
            self.bottom_chord_preview_label.set_section("", "")

    def _apply_custom_mode(self, is_custom: bool):
        # Only allow manual section selection in Custom mode.
        # Keep the preview/diagram column visible in Optimized mode (like Girder Details).
        self.right_column.setVisible(True)
        for widget in [
            self.bracing_section_type_combo,
            self.bracing_section_combo,
            self.top_chord_type_combo,
            self.top_chord_size_combo,
            self.bottom_chord_type_combo,
            self.bottom_chord_size_combo,
        ]:
            widget.setEnabled(is_custom)
        self._on_bracing_layout_changed()

    def _on_design_changed(self, label: str):
        is_custom = label == "Custom"
        self._apply_custom_mode(is_custom)
        self._update_previews()

    def set_design_mode(self, mode_str: str) -> None:
        mode = "Custom" if str(mode_str or "").strip().lower() in {"custom", "customized"} else "Optimized"
        self._global_design_mode = mode
        if hasattr(self, "design_combo") and self.design_combo is not None:
            prev = self.design_combo.blockSignals(True)
            try:
                self.design_combo.setCurrentText(mode)
            finally:
                self.design_combo.blockSignals(prev)
        self._on_design_changed(mode)

    # ---- Helpers for section labels -------------------------------------
    def _display_name_for(self, designation: str, section_type: str) -> str:
        name = (designation or "").strip()
        if section_type in ("angle", "double_angle_long", "double_angle_short"):
            name = name.lstrip("∠⌒⟡⟠").strip()
            if not name.upper().startswith("IS"):
                name = f"IS {name}"
        return name

    def _fill_combo(self, combo: QComboBox, items, section_type: str):
        combo.blockSignals(True)
        combo.clear()
        for des in items:
            combo.addItem(self._display_name_for(des, section_type), des)
        combo.blockSignals(False)

    def _set_preview(self, widget: SectionPreviewWidget, type_combo: QComboBox, size_combo: QComboBox):
        stype = self._map_section_type(type_combo.currentText())
        designation = size_combo.currentData() or size_combo.currentText()
        show_double_total = True
        if stype in ("double_angle_long", "double_angle_short"):
            show_double_total = False
        widget.set_section(stype, designation, show_double_total)

    def _populate_designations(self):
        angles = self.catalog.list_angles()

        self._fill_combo(self.bracing_section_combo, angles, "angle")
        self._fill_combo(self.top_chord_size_combo, angles, "angle")
        self._fill_combo(self.bottom_chord_size_combo, angles, "angle")

    def _map_section_type(self, label: str) -> str:
        mapping = {
            "Angle": "angle",
            "Double Angle (Long Leg)": "double_angle_long",
            "Double Angle (Short Leg)": "double_angle_short",
            "Channel": "channel",
            "Double Channel": "double_channel",
        }
        return mapping.get(label, "angle")

    def _on_bracing_type_changed(self, label: str):
        self._update_designations_for(self.bracing_section_combo, label)
        self._update_previews()

    def _on_top_chord_type_changed(self, label: str):
        self._update_designations_for(self.top_chord_size_combo, label)
        self._update_previews()

    def _on_bottom_chord_type_changed(self, label: str):
        self._update_designations_for(self.bottom_chord_size_combo, label)
        self._update_previews()

    def _on_bracing_layout_changed(self, *_args):
        if self._updating_chord_rules:
            return
        self._updating_chord_rules = True
        try:
            bracing = (self.bracing_type_combo.currentText() or "").strip()
            is_custom = self.design_combo.currentText() == "Custom"

            if bracing == "K-Bracing":
                self.bottom_chord_checkbox.setChecked(True)
                # Keep enabled so the checked state is always visually clear.
                self.bottom_chord_checkbox.setEnabled(True)
                self.top_chord_checkbox.setEnabled(True)
            else:
                self.bottom_chord_checkbox.setEnabled(True)
                self.top_chord_checkbox.setEnabled(True)

            top_enabled = is_custom and self.top_chord_checkbox.isChecked()
            bottom_enabled = is_custom and self.bottom_chord_checkbox.isChecked()

            self.top_chord_type_combo.setEnabled(top_enabled)
            self.top_chord_size_combo.setEnabled(top_enabled)
            self.bottom_chord_type_combo.setEnabled(bottom_enabled)
            self.bottom_chord_size_combo.setEnabled(bottom_enabled)

            self.top_chord_preview_box.setVisible(self.top_chord_checkbox.isChecked())
            show_bottom = self.bottom_chord_checkbox.isChecked() or bracing == "K-Bracing"
            if show_bottom and not self.bottom_chord_checkbox.isChecked():
                self.bottom_chord_checkbox.setChecked(True)
            self.bottom_chord_preview_box.setVisible(show_bottom)

            if hasattr(self, "bracing_layout_widget") and self.bracing_layout_widget is not None:
                self.bracing_layout_widget.set_layout(
                    bracing,
                    self.top_chord_checkbox.isChecked(),
                    self.bottom_chord_checkbox.isChecked(),
                    self.member_id_display.text() if hasattr(self, "member_id_display") else "",
                    self.select_girders_combo.currentText() if hasattr(self, "select_girders_combo") else "",
                )
        finally:
            self._updating_chord_rules = False

        self._update_previews()

    def _update_designations_for(self, combo: QComboBox, type_label: str):
        stype = self._map_section_type(type_label)
        if stype in ("angle", "double_angle_long", "double_angle_short"):
            items = self.catalog.list_angles()
        else:
            items = self.catalog.list_channels()
        self._fill_combo(combo, items, stype)

    # ---- External API -----------------------------------------------------
    def reset_defaults(self):
        # Clear per-member persistence so Defaults returns to a clean slate.
        self._state_by_member_key.clear()
        self._active_member_key = None

        # Refresh girder options (may have changed after Girder Defaults).
        try:
            self.refresh_girder_options()
        except Exception:
            pass

        # Drop any state that may have been snapshotted during refresh.
        self._state_by_member_key.clear()
        self._active_member_key = None

        # Reset selection to the first pair/member in a guarded way.
        self._selection_sync_guard = True
        try:
            if self.select_girders_combo.count() > 0:
                self.select_girders_combo.setCurrentIndex(0)
            if self.member_id_combo.count() > 0:
                self.member_id_combo.setCurrentIndex(0)
        finally:
            self._selection_sync_guard = False

        # With no saved state for this member, this applies default UI values
        # (Optimized + first options) and updates enable/disable + previews.
        self._load_state_for_current_member()

    def collect_data(self):
        # Ensure the latest edits are persisted to the active member.
        self._store_current_member_state()

        pairs = self._girder_pairs()

        # For the UI we configure only one member (always M1) per pair.
        # For the solver/export, expand the configured state to all members.
        by_member: dict[str, dict] = {}
        for pair_idx, pair_label in enumerate(pairs, start=1):
            base_member = f"B{pair_idx}M1"
            base_key = f"{pair_label}::{base_member}"
            base_state = self._state_by_member_key.get(base_key)
            if base_state is None:
                base_state = dict(self._default_member_state())
                self._state_by_member_key[base_key] = dict(base_state)

            for member_id in self._member_ids_for_pair(pair_idx):
                payload = dict(base_state or {})
                payload["select_girders"] = pair_label
                payload["member_id"] = member_id
                by_member[member_id] = payload

        # Backward compatible: keep current selection fields at the top-level.
        current_pair = (self.select_girders_combo.currentText() or "").strip()
        current_member = self._current_member_id().strip().upper()
        payload: dict[str, object] = {
            "select_girders": current_pair,
            "member_id": current_member,
            "cross_bracing_by_member": by_member,
        }

        for field in self._schema_fields("section_inputs"):
            field_id = str(field.get("id") or "").strip()
            if not field_id:
                continue
            widget = self._widget_for_field(field_id)
            if isinstance(widget, QCheckBox):
                payload[field_id] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                payload[field_id] = widget.currentText()
            elif isinstance(widget, QLineEdit):
                payload[field_id] = widget.text()

        payload["design"] = self._global_design_mode
        return payload

    def restore_data(self, data: dict) -> None:
        """Restore previously saved cross bracing inputs."""
        if not isinstance(data, dict):
            return

        restored = data.get("cross_bracing_by_member")
        if isinstance(restored, dict):
            # Prefer restoring from the configured member (always M1) for each pair.
            rebuilt: dict[str, dict] = {}
            for _member_id, payload in restored.items():
                if not isinstance(payload, dict):
                    continue
                pair_label = str(payload.get("select_girders") or "").strip()
                member_id = str(payload.get("member_id") or _member_id or "").strip().upper()
                if not pair_label:
                    continue
                # Only store state for M1 in the UI.
                if not member_id.endswith("M1"):
                    continue
                state = dict(payload)
                state.pop("select_girders", None)
                state.pop("member_id", None)
                rebuilt[f"{pair_label}::{member_id}"] = state
            if rebuilt:
                self._state_by_member_key = rebuilt

        # Refresh dropdowns and try to restore selection.
        try:
            self.refresh_girder_options()
        except Exception:
            pass

        target_pair = str(data.get("select_girders") or "").strip()
        target_member = str(data.get("member_id") or "").strip().upper()
        if target_pair:
            try:
                self.select_girders_combo.setCurrentText(target_pair)
            except Exception:
                pass
        # Member ID is software-driven (always M1) so just refresh the display.
        try:
            self._refresh_member_id_display()
        except Exception:
            pass

        # Ensure UI reflects stored state for restored selection.
        try:
            self._load_state_for_current_member()
        except Exception:
            pass

