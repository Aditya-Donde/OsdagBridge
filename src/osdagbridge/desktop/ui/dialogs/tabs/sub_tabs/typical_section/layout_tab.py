from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget
import math

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import LAYOUT_TAB_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


class LayoutTab(SchemaTab):
    schema = LAYOUT_TAB_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self._layout_updating = False
        self._last_spacing_value: float | None = None
        self._last_overhang_value: float | None = None
        self._last_girders_value: int | None = None

        if hasattr(owner, "overall_bridge_width_display") and hasattr(owner, "overall_bridge_width_formula"):
            owner.overall_bridge_width_display.setToolTip(owner.overall_bridge_width_formula)

        self._create_notice_labels(owner, self.builder.page_layout)
        self._wire_owner_side_effects()

    def _create_notice_labels(self, owner, page_layout):
        self.layout_adjust_notice = self._make_notice_label("#000000")
        self.layout_warning_notice = self._make_notice_label("#cc6600")

        container = QWidget()
        container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        container.setFixedWidth(180)
        vlayout = QVBoxLayout(container)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(4)
        vlayout.addWidget(self.layout_adjust_notice)
        vlayout.addWidget(self.layout_warning_notice)
        container.hide()
        self.layout_notice_container = container
        owner.layout_adjust_notice = self.layout_adjust_notice
        owner.layout_warning_notice = self.layout_warning_notice
        owner.layout_notice_container = container
        page_layout.insertWidget(page_layout.count() - 1, container)

    def clear_notices(self) -> None:
        self.layout_adjust_notice.hide()
        self.layout_adjust_notice.setText("")
        self.layout_warning_notice.hide()
        self.layout_warning_notice.setText("")
        self.layout_notice_container.hide()

    def export_layout_state(self) -> dict:
        return {
            "girder_spacing_m": self.widget_float("girder_spacing"),
            "deck_overhang_m": self.widget_float("deck_overhang"),
            "num_girders": self.widget_float("no_of_girders"),
            "deck_thickness_mm": self.widget_float("deck_thickness"),
            "footpath_width_m": self.widget_float("footpath_width"),
            "footpath_thickness_mm": self.widget_float("footpath_thickness"),
        }

    def on_girder_spacing_changed(self) -> None:
        self._handle_owner_layout_change("spacing")

    def on_deck_overhang_changed(self) -> None:
        self._handle_owner_layout_change("overhang")

    def on_no_of_girders_changed(self) -> None:
        self._handle_owner_layout_change("girders")

    def on_footpath_width_changed(self) -> None:
        owner = getattr(self, "owner", None)
        if owner is not None and not getattr(owner, "updating_fields", False):
            recalculate = getattr(owner, "recalculate_girders", None)
            if callable(recalculate):
                recalculate()

    def validate_deck_thickness(self) -> None:
        self._validate_thickness_field(
            "deck_thickness",
            100,
            500,
            200,
            "Deck thickness too small",
            "Deck thickness too large",
        )

    def validate_footpath_thickness(self) -> None:
        self._validate_thickness_field(
            "footpath_thickness",
            100,
            500,
            200,
            "Footpath thickness too small",
            "Footpath thickness too large",
        )

    def _reject_overall_width_override(self, text) -> None:
        owner = getattr(self, "owner", None)
        if owner is None or getattr(owner, "_updating_overall_width_display", False):
            return

        try:
            entered_value = float(text) if text else None
        except ValueError:
            entered_value = None

        try:
            expected_value = float(owner._calculate_overall_bridge_width())
        except Exception:
            expected_value = None

        display = self.get_widget("overall_bridge_width_display")
        if expected_value is None:
            return
        if entered_value is None or abs(expected_value - entered_value) > 1e-6:
            if display is not None and display.hasFocus():
                self._show_owner_warning(
                    "Overall Bridge Width Locked",
                    "Overall Bridge Width is auto-calculated using:\n"
                    f"{owner.overall_bridge_width_formula}",
                )
            updater = getattr(owner, "_update_overall_bridge_width_display", None)
            if callable(updater):
                updater()

    def sync_from_bridge_context(self, footpath_value: str) -> None:
        enabled = footpath_value != "None"
        for bind_name in ("footpath_width", "footpath_thickness"):
            widget = self.get_widget(bind_name)
            if widget is not None:
                widget.setEnabled(enabled)

    def export_bridge_context_cad_params(
        self,
        carriageway_width_m: float | None,
        footpath_value: str,
    ) -> dict:
        params = {}
        if carriageway_width_m is not None:
            params["carriageway_width"] = float(carriageway_width_m) * 1000.0

        params["footpath_config"] = {
            "Both Sides": "both",
            "Single Side": "left",
            "None": "none",
        }.get(footpath_value, "none")
        return params

    def clear_layout_fields(self) -> None:
        self._layout_updating = True
        try:
            for bind_name in ("girder_spacing", "deck_overhang", "no_of_girders"):
                self.set_widget_text(bind_name, "")
        finally:
            self._layout_updating = False

    def clear_linked_inputs(self) -> None:
        self.clear_layout_fields()
        self._last_spacing_value = None
        self._last_overhang_value = None
        self._last_girders_value = None

    def is_layout_updating(self) -> bool:
        return self._layout_updating

    def apply_layout_solution(self, spacing_m: float, overhang_m: float, girders: int) -> dict:
        self._layout_updating = True
        try:
            self.set_widget_text("girder_spacing", f"{float(spacing_m):.2f}")
            self.set_widget_text("deck_overhang", f"{float(overhang_m):.2f}")
            self.set_widget_text("no_of_girders", str(int(girders)))
        finally:
            self._layout_updating = False
        self._last_spacing_value = float(spacing_m)
        self._last_overhang_value = float(overhang_m)
        self._last_girders_value = int(girders)
        return {
            "girder_spacing_m": float(spacing_m),
            "deck_overhang_m": float(overhang_m),
            "num_girders": int(girders),
        }

    def handle_layout_field_change(self, *, changed_field: str) -> dict:
        field_map = {
            "spacing": ("girder_spacing", float, "_last_spacing_value"),
            "overhang": ("deck_overhang", float, "_last_overhang_value"),
            "girders": ("no_of_girders", lambda text: int(float(text)), "_last_girders_value"),
        }
        bind_name, parser, last_attr = field_map[changed_field]
        raw_text = self.widget_text(bind_name, "").strip()
        if not raw_text:
            setattr(self, last_attr, None)
            self.clear_linked_inputs()
            return {
                "ok": False,
                "empty": True,
                "error": "Girder spacing, deck overhang, and number of girders are linked. Please enter all three.",
            }
        try:
            new_value = parser(raw_text)
        except Exception:
            return {"ok": False, "empty": False, "error": None}

        previous = getattr(self, last_attr)
        unchanged = (
            previous == new_value
            if changed_field == "girders"
            else previous is not None and abs(float(new_value) - float(previous)) < 1e-6
        )
        if unchanged:
            return {"ok": False, "empty": False, "error": None, "unchanged": True}

        setattr(self, last_attr, new_value)
        return {"ok": True, "empty": False, "error": None, "value": new_value}

    @staticmethod
    def _clamp(value, lo, hi):
        return max(lo, min(hi, value))

    @staticmethod
    def _deck_overhang_range(overall_width):
        if overall_width <= 0:
            return 0.0, 0.0
        return 0.0, overall_width / 2.0

    def _spacing_candidates_for_overhang(self, overall_width, overhang, spacing_bounds):
        spacing_min, spacing_max = spacing_bounds
        max_n = int(math.floor(overall_width / spacing_min) + 2) if spacing_min > 0 else 50

        best = None
        for n in range(2, max(2, max_n) + 1):
            raw_spacing = (overall_width - 2.0 * overhang) / (n - 1)
            if raw_spacing <= 0:
                continue
            spacing_rounded = round(raw_spacing, 2)
            if spacing_rounded < spacing_min - 1e-6 or spacing_rounded > spacing_max + 1e-6:
                continue
            spacing_rounded = self._clamp(spacing_rounded, spacing_min, spacing_max)
            ideal_min = 0.35 * spacing_rounded
            ideal_max = 0.5 * spacing_rounded
            score = (0, n) if ideal_min <= overhang <= ideal_max else (1, n)
            if best is None or score < best[0]:
                best = (score, spacing_rounded, overhang, n)
        return best

    def _pick_n_for_spacing(self, overall_width, spacing, spacing_bounds):
        spacing_min, spacing_max = spacing_bounds
        spacing = self._clamp(round(spacing, 2), spacing_min, spacing_max)

        overhang_min, overhang_max = self._deck_overhang_range(overall_width)
        max_n = int(math.floor(overall_width / spacing) + 2) if spacing > 0 else 1

        ideal_overhang_min = 0.35 * spacing
        ideal_overhang_max = 0.5 * spacing

        best = None
        for n in range(2, max(2, max_n) + 1):
            if (n - 1) * spacing > overall_width + 1e-6:
                break
            overhang = (overall_width - (n - 1) * spacing) / 2.0
            if overhang < overhang_min - 1e-6 or overhang > overhang_max + 1e-6:
                continue
            if ideal_overhang_min <= overhang <= ideal_overhang_max:
                score = (0, abs(overhang - (ideal_overhang_min + ideal_overhang_max) / 2), n)
            elif overhang <= spacing:
                score = (1, abs(overhang - ideal_overhang_max), n)
            else:
                score = (2, overhang - spacing, n)
            if best is None or score < best[0]:
                best = (score, n, spacing, overhang)
        return best

    def solve_layout_plan(self, *, overall_width: float, changed_field: str, spacing_bounds: tuple[float, float], default_spacing: float) -> dict:
        if overall_width <= 0:
            return {"ok": False, "error": "Overall bridge width must be positive."}

        state = self.export_layout_state()
        spacing_input = state["girder_spacing_m"] if state["girder_spacing_m"] is not None else default_spacing
        overhang_input = state["deck_overhang_m"] if state["deck_overhang_m"] is not None else 0.35 * spacing_input
        girders_input = int(state["num_girders"]) if state["num_girders"] is not None else None

        overhang_min, overhang_max = self._deck_overhang_range(overall_width)

        def build_response(spacing_use, overhang_use, girders_use, old_spacing, old_overhang, old_girders):
            reason_parts = []
            if abs(spacing_use - old_spacing) > 0.01:
                reason_parts.append(f"spacing {old_spacing:.2f}->{spacing_use:.2f}")
            if abs(overhang_use - old_overhang) > 1e-6:
                reason_parts.append(f"overhang {old_overhang:.2f}->{overhang_use:.2f}")
            if old_girders is not None and girders_use != old_girders:
                reason_parts.append(f"girders {old_girders}->{girders_use}")
            warning = None
            if overhang_use > spacing_use + 1e-6:
                warning = f"Overhang ({overhang_use:.2f} m) exceeds girder spacing ({spacing_use:.2f} m)"
            return {
                "ok": True,
                "solution": {"spacing": spacing_use, "overhang": overhang_use, "girders": girders_use},
                "reason": ", ".join(reason_parts) if reason_parts else None,
                "warning": warning,
            }

        if changed_field == "spacing":
            pick = self._pick_n_for_spacing(overall_width, spacing_input, spacing_bounds)
            if not pick:
                return {"ok": False, "error": "Cannot satisfy constraints with the selected girder spacing."}
            _, girders_use, spacing_use, overhang_use = pick
            return build_response(spacing_use, overhang_use, girders_use, spacing_input, overhang_input, girders_input)

        if changed_field == "overhang":
            if overhang_input < overhang_min - 1e-6 or overhang_input > overhang_max + 1e-6:
                return {
                    "ok": False,
                    "error": (
                        f"Deck overhang width must be between {overhang_min:.2f} m and {overhang_max:.2f} m "
                        f"(half of Overall Bridge Width).\n\n"
                        f"Valid range: {overhang_min:.2f} m to {overhang_max:.2f} m\n"
                        f"You entered: {overhang_input:.2f} m\n\n"
                        "To change deck overhang limits, you need to adjust the Overall Bridge Width "
                        "(by modifying carriageway width, crash barriers, footpaths, etc.)."
                    ),
                }
            pick = self._spacing_candidates_for_overhang(overall_width, overhang_input, spacing_bounds)
            if not pick:
                return {"ok": False, "error": "Cannot satisfy constraints with the selected deck overhang."}
            _, spacing_use, overhang_use, girders_use = pick
            return build_response(spacing_use, overhang_use, girders_use, spacing_input, overhang_input, girders_input)

        if changed_field == "girders":
            if girders_input is None:
                return {"ok": False, "error": "Number of girders must be an integer greater than or equal to 2."}
            girders_use = max(2, girders_input)
            try:
                spacing_min = float(spacing_bounds[0])
            except Exception:
                spacing_min = 1.0
            if spacing_min <= 0:
                spacing_min = 1.0
            max_girders = int(math.floor((overall_width + 1e-9) / spacing_min) + 1)
            max_girders = max(2, max_girders)
            girders_use = min(girders_use, max_girders)

            target_spacing = (overall_width / (girders_use - 1 + 0.7) + overall_width / girders_use) / 2.0
            spacing_use = self._clamp(round(target_spacing, 2), *spacing_bounds)
            overhang_use = (overall_width - (girders_use - 1) * spacing_use) / 2.0

            if overhang_use < overhang_min - 1e-6 or overhang_use > overhang_max + 1e-6:
                fallback_girders = int(self._last_girders_value or 2)
                fallback_girders = max(2, min(fallback_girders, max_girders))
                pick = self._pick_n_for_spacing(overall_width, spacing_use, spacing_bounds)
                if pick:
                    _, fallback_girders, spacing_use, overhang_use = pick
                    fallback_girders = max(2, min(int(fallback_girders), max_girders))
                else:
                    spacing_use = self._clamp(spacing_use, *spacing_bounds)
                    overhang_use = self._clamp(max(0.0, overhang_use), overhang_min, overhang_max)
                return {
                    "ok": True,
                    "solution": {"spacing": spacing_use, "overhang": overhang_use, "girders": fallback_girders},
                    "reason": None,
                    "warning": None,
                    "error": (
                        "Cannot satisfy constraints with the selected number of girders. "
                        f"For the current overall width ({overall_width:.2f} m) and minimum spacing ({spacing_min:.2f} m), "
                        f"maximum feasible girders is {max_girders}."
                    ),
                }
            return build_response(spacing_use, overhang_use, girders_use, spacing_input, overhang_input, girders_input)

        pick = self._pick_n_for_spacing(overall_width, spacing_input, spacing_bounds)
        if not pick:
            pick = self._pick_n_for_spacing(overall_width, default_spacing, spacing_bounds)
        if not pick:
            return {"ok": False, "error": "Cannot satisfy layout constraints for the current overall width."}
        _, girders_use, spacing_use, overhang_use = pick
        return build_response(spacing_use, overhang_use, girders_use, spacing_input, overhang_input, girders_input)

    def export_cad_params(self) -> dict:
        state = self.export_layout_state()
        params = {}

        if state["num_girders"] is not None:
            params["num_girders"] = int(float(state["num_girders"]))
        if state["girder_spacing_m"] is not None:
            params["girder_spacing"] = float(state["girder_spacing_m"]) * 1000
        if state["deck_overhang_m"] is not None:
            params["deck_overhang"] = float(state["deck_overhang_m"]) * 1000
        if state["deck_thickness_mm"] is not None:
            params["deck_thickness"] = float(state["deck_thickness_mm"])
        if state["footpath_width_m"] is not None:
            params["footpath_width"] = float(state["footpath_width_m"]) * 1000
        if state["footpath_thickness_mm"] is not None:
            params["footpath_thickness"] = float(state["footpath_thickness_mm"])

        return params

    def set_notices(self, reason: str | None = None, warning: str | None = None) -> None:
        any_visible = bool(reason) or bool(warning)
        if reason:
            self.layout_adjust_notice.setText(f"Values adjusted: {reason}")
            self.layout_adjust_notice.show()
        else:
            self.layout_adjust_notice.hide()
            self.layout_adjust_notice.setText("")

        if warning:
            self.layout_warning_notice.setText(f"Warning: {warning}")
            self.layout_warning_notice.show()
        else:
            self.layout_warning_notice.hide()
            self.layout_warning_notice.setText("")

        self.layout_notice_container.setVisible(any_visible)

    def _handle_owner_layout_change(self, changed_field: str) -> None:
        owner = getattr(self, "owner", None)
        if owner is None or getattr(owner, "updating_fields", False) or self.is_layout_updating():
            return

        result = self.handle_layout_field_change(changed_field=changed_field)
        if result.get("error"):
            clear = getattr(owner, "_clear_adjust_notice", None)
            if callable(clear):
                clear()
            self._show_owner_warning("Layout", result["error"])
            return
        if not result.get("ok"):
            return

        solver = getattr(owner, "_solve_layout", None)
        if callable(solver):
            solver(changed_field)

    def _validate_thickness_field(
        self,
        bind_name: str,
        min_value: float,
        max_value: float,
        default_value: float,
        too_small_msg: str,
        too_large_msg: str,
    ) -> None:
        widget = self.get_widget(bind_name)
        if widget is None:
            return
        try:
            text = widget.text().strip()
            if not text:
                widget.setText(str(int(default_value)))
                return
            value = float(text)
            if value < min_value:
                self._show_owner_critical("Thickness Error", too_small_msg)
                widget.setText(str(int(min_value)))
            elif value > max_value:
                self._show_owner_critical("Thickness Error", too_large_msg)
                widget.setText(str(int(max_value)))
        except Exception:
            widget.setText(str(int(default_value)))

    def _sync_footpath_thickness_from_deck(self, text: str) -> None:
        footpath_widget = self.get_widget("footpath_thickness")
        if footpath_widget is not None and text and not footpath_widget.text():
            footpath_widget.setText(text)

    def _wire_owner_side_effects(self) -> None:
        owner = getattr(self, "owner", None)
        update_preview = getattr(owner, "_update_cad_preview", None) if owner is not None else None
        if callable(update_preview):
            for bind_name in (
                "girder_spacing",
                "no_of_girders",
                "deck_overhang",
                "deck_thickness",
                "footpath_width",
                "footpath_thickness",
            ):
                widget = self.get_widget(bind_name)
                if widget is not None and hasattr(widget, "editingFinished"):
                    widget.editingFinished.connect(update_preview)

        deck_widget = self.get_widget("deck_thickness")
        if deck_widget is not None and hasattr(deck_widget, "textChanged"):
            deck_widget.textChanged.connect(self._sync_footpath_thickness_from_deck)

    def _show_owner_warning(self, title: str, text: str) -> None:
        owner = getattr(self, "owner", None)
        callback = getattr(owner, "show_warning_message", None) if owner is not None else None
        if callable(callback):
            callback(title, text)

    def _show_owner_critical(self, title: str, text: str) -> None:
        owner = getattr(self, "owner", None)
        callback = getattr(owner, "show_critical_message", None) if owner is not None else None
        if callable(callback):
            callback(title, text)

    @staticmethod
    def _make_notice_label(color: str) -> QLabel:
        lbl = QLabel()
        lbl.setStyleSheet(
            f"font-size: 10px; font-style: italic; color: {color}; background-color: transparent;"
        )
        lbl.setWordWrap(True)
        lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        lbl.setFixedWidth(180)
        lbl.hide()
        return lbl
