"""Crash Barrier sub-tab for Typical Section Details."""

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    CRASH_BARRIER_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab
from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.sub_tabs.typical_section.barrier_form_helper import (
    BarrierFormConfig,
    BarrierFormHelper,
)
from osdagbridge.desktop.cad.irc5_geometry import CrashBarrierGeometry


def _compact_rows(schema: dict, groups: tuple[tuple[int, ...], ...]) -> list[dict]:
    fields = [
        field
        for row in schema.get("rows", []) or []
        for field in row.get("fields", []) or []
    ]
    fields = [
        {**field, "width": 240} if index == 0 else field
        for index, field in enumerate(fields)
    ]
    return [
        {"fields": [fields[index] for index in group if index < len(fields)]}
        for group in groups
    ]


_CRASH_BARRIER_VIEW_SCHEMA = {
    "row_vertical_spacing": 20,
    "cards": [
        {
            "title": "Crash Barrier Inputs:",
            "label_width": 185,
            "field_width": 200,
            "rows": _compact_rows(
                CRASH_BARRIER_TAB_SCHEMA,
                ((0,), (2, 3), (1, 4), (5, 6)),
            ),
        }
    ]
}

_CRASH_BARRIER_CONFIG = BarrierFormConfig(
    type_bind="crash_barrier_type",
    width_bind="crash_barrier_width",
    height_bind="crash_barrier_height",
    density_bind="crash_barrier_density",
    area_bind="crash_barrier_area",
    load_bind="crash_barrier_load",
    post_spacing_bind="crash_barrier_post_spacing",
    density_label_bind="crash_barrier_density_label",
    area_label_bind="crash_barrier_area_label",
    post_spacing_label_bind="crash_barrier_post_spacing_label",
    metallic_type_prefixes=("IRC 5 - Metallic Crash Barrier",),
    rcc_type_prefixes=(
        "IRC 5 - RCC Crash Barrier",
        "IRC 5 - High Containment RCC Crash Barrier",
    ),
    custom_fallback_type="IRC 5 - RCC Crash Barrier",
    width_geom_keys=("bottom_width",),
    height_geom_keys=("total_height",),
)


class CrashBarrierTab(SchemaTab):
    """Schema-driven crash barrier page bound onto the Typical Section owner."""
    schema = _CRASH_BARRIER_VIEW_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self.setStyleSheet("background-color: white;")

    def export_barrier_state(self) -> dict:
        return BarrierFormHelper.export_state(self, _CRASH_BARRIER_CONFIG)

    def export_cad_params(self) -> dict:
        state = self.export_barrier_state()
        params = {}
        if state.get("type"):
            params["crash_barrier_type"] = state["type"]
        if state.get("width_m") is not None:
            params["crash_barrier_width"] = float(state["width_m"]) * 1000
        if state.get("height_m") is not None:
            params["crash_barrier_height"] = float(state["height_m"]) * 1000
        return params

    def is_metallic(self, barrier_type: str) -> bool:
        return BarrierFormHelper.is_metallic(_CRASH_BARRIER_CONFIG, barrier_type)

    def is_rcc(self, barrier_type: str) -> bool:
        return BarrierFormHelper.is_rcc(_CRASH_BARRIER_CONFIG, barrier_type)

    def effective_type(self, barrier_type: str) -> str:
        return BarrierFormHelper.effective_type(_CRASH_BARRIER_CONFIG, barrier_type)

    def auto_compute_load(self, barrier_type: str) -> None:
        BarrierFormHelper.auto_compute_load(self, _CRASH_BARRIER_CONFIG, barrier_type)

    def apply_defaults(self, barrier_type: str, geom: dict | None, *, force: bool = False) -> None:
        BarrierFormHelper.apply_defaults(
            self,
            _CRASH_BARRIER_CONFIG,
            barrier_type,
            geom,
            force=force,
        )

    def update_visibility(self, barrier_type: str) -> None:
        BarrierFormHelper.update_visibility(
            self,
            _CRASH_BARRIER_CONFIG,
            barrier_type,
        )

    def sync_from_parent_geometry(self, barrier_type: str, geom: dict | None, *, force: bool = False) -> dict:
        self.apply_defaults(barrier_type, geom, force=force)
        params = self.export_cad_params()
        if barrier_type:
            params["crash_barrier_type"] = barrier_type
        return params

    def sync_from_parent_state(self, *, force: bool = False) -> dict:
        barrier_type = self.export_barrier_state().get("type")
        if not barrier_type:
            return {}
        effective_barrier_type = self.effective_type(barrier_type)
        geom = CrashBarrierGeometry.get_geometry(effective_barrier_type)
        return self.sync_from_parent_geometry(barrier_type, geom, force=force)

    def _auto_compute_crash_barrier_load(self) -> None:
        barrier_type = self.export_barrier_state().get("type", "")
        self.auto_compute_load(barrier_type)

    def on_crash_barrier_type_changed(self, barrier_type) -> None:
        owner = getattr(self, "owner", None)
        if barrier_type in ["Flexible", "Semi-Rigid"] and getattr(owner, "footpath_value", None) == "None":
            callback = getattr(owner, "show_critical_message", None) if owner is not None else None
            if callable(callback):
                callback(
                    "Crash Barrier Type Not Permitted",
                    f"{barrier_type} crash barriers are not permitted on bridges without an outer "
                    "footpath per IRC 5 Clause 109.6.4.",
                )

        params = self.sync_from_parent_state(force=True)
        push = getattr(owner, "_push_cad_params", None) if owner is not None else None
        if callable(push):
            push(params)

        recalculate = getattr(owner, "recalculate_girders", None) if owner is not None else None
        if callable(recalculate):
            recalculate()
