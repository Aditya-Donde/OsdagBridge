"""Median sub-tab for Typical Section Details."""

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    MEDIAN_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.typical_section.barrier_form_helper import (
    BarrierFormConfig,
    BarrierFormHelper,
)
from osdagbridge.desktop.cad.irc5_geometry import MedianGeometry


_MEDIAN_VIEW_SCHEMA = {
    "row_vertical_spacing": 20,
    "cards": [
        {
            "title": "Median Inputs:",
            "label_width": MEDIAN_TAB_SCHEMA.get("label_width", 210),
            "field_width": 200,
            "rows": MEDIAN_TAB_SCHEMA.get("rows", []),
        }
    ]
}

_MEDIAN_CONFIG = BarrierFormConfig(
    type_bind="median_type",
    width_bind="median_width",
    height_bind="median_height",
    density_bind="median_density",
    area_bind="median_area",
    load_bind="median_load",
    post_spacing_bind="median_post_spacing",
    density_label_bind="median_density_label",
    area_label_bind="median_area_label",
    post_spacing_label_bind="median_post_spacing_label",
    metallic_type_prefixes=("IRC 5 - Metallic Crash Barrier",),
    rcc_type_prefixes=("IRC 5 - RCC Crash Barrier", "IRC 5 - Raised Kerb"),
    custom_fallback_type="IRC 5 - Raised Kerb",
    width_geom_keys=("median_width",),
    height_geom_keys=("barrier_height", "kerb_height"),
    active_bind_names=(
        "median_type",
        "median_density",
        "median_width",
        "median_height",
        "median_area",
        "median_load",
        "median_post_spacing",
        "median_density_label",
        "median_area_label",
        "median_post_spacing_label",
    ),
)


class MedianTab(SchemaTab):
    """Schema-driven median page bound onto the Typical Section owner."""
    schema = _MEDIAN_VIEW_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self.setStyleSheet("background-color: white;")

    def export_median_state(self, *, include_median: bool = True) -> dict:
        return BarrierFormHelper.export_state(
            self,
            _MEDIAN_CONFIG,
            included=include_median,
        )

    def export_cad_params(self, *, include_median: bool = True) -> dict:
        state = self.export_median_state(include_median=include_median)
        params = {"median_present": bool(state.get("included"))}
        if not state.get("included"):
            return params
        if state.get("type"):
            params["median_type"] = state["type"]
        if state.get("width_m") is not None:
            params["median_width"] = float(state["width_m"]) * 1000
        if state.get("height_m") is not None:
            params["median_height"] = float(state["height_m"]) * 1000
        return params

    def is_metallic(self, median_type: str) -> bool:
        return BarrierFormHelper.is_metallic(_MEDIAN_CONFIG, median_type)

    def is_rcc(self, median_type: str) -> bool:
        return BarrierFormHelper.is_rcc(_MEDIAN_CONFIG, median_type)

    def effective_type(self, median_type: str) -> str:
        return BarrierFormHelper.effective_type(_MEDIAN_CONFIG, median_type)

    def auto_compute_load(self, median_type: str) -> None:
        BarrierFormHelper.auto_compute_load(self, _MEDIAN_CONFIG, median_type)

    def apply_defaults(self, median_type: str, geom: dict | None, *, force: bool = False, include_median: bool = True) -> None:
        BarrierFormHelper.apply_defaults(
            self,
            _MEDIAN_CONFIG,
            median_type,
            geom,
            force=force,
            active=include_median,
        )

    def update_visibility(self, median_type: str, *, include_median: bool = True) -> None:
        BarrierFormHelper.update_visibility(
            self,
            _MEDIAN_CONFIG,
            median_type,
            active=include_median,
        )

    def sync_from_parent_geometry(self, median_type: str, geom: dict | None, *, force: bool = False, include_median: bool = True) -> dict:
        self.apply_defaults(median_type, geom, force=force, include_median=include_median)
        params = self.export_cad_params(include_median=include_median)
        if include_median and median_type:
            params["median_type"] = median_type
        return params

    def sync_from_parent_state(self, *, include_median: bool = True, force: bool = False) -> dict:
        median_type = self.export_median_state(include_median=include_median).get("type")
        if not include_median or not median_type:
            return self.export_cad_params(include_median=include_median)
        effective_median_type = self.effective_type(median_type)
        geom = MedianGeometry.get_geometry(effective_median_type)
        return self.sync_from_parent_geometry(
            median_type,
            geom,
            force=force,
            include_median=include_median,
        )

    def on_median_type_changed(self, median_type) -> None:
        owner = getattr(self, "owner", None)
        params = self.sync_from_parent_state(
            include_median=True,
            force=True,
        )
        push = getattr(owner, "_push_cad_params", None) if owner is not None else None
        if callable(push):
            push(params)

        recalculate = getattr(owner, "recalculate_girders", None) if owner is not None else None
        if callable(recalculate):
            recalculate()
