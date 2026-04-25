"""Shared helpers for barrier-like typical section forms."""

from __future__ import annotations

from dataclasses import dataclass

from osdagbridge.core.utils.common import DEFAULT_CONCRETE_DENSITY


@dataclass(frozen=True)
class BarrierFormConfig:
    """Configuration for crash-barrier-like schema tabs."""

    type_bind: str
    width_bind: str
    height_bind: str
    density_bind: str
    area_bind: str
    load_bind: str
    post_spacing_bind: str
    density_label_bind: str
    area_label_bind: str
    post_spacing_label_bind: str
    metallic_type_prefixes: tuple[str, ...]
    rcc_type_prefixes: tuple[str, ...]
    custom_fallback_type: str
    width_geom_keys: tuple[str, ...]
    height_geom_keys: tuple[str, ...]
    active_bind_names: tuple[str, ...] = ()


class BarrierFormHelper:
    """Shared state/default/visibility helpers for barrier-like forms."""

    @staticmethod
    def export_state(tab, cfg: BarrierFormConfig, *, included: bool | None = None) -> dict:
        state = {
            "type": tab.widget_current_text(cfg.type_bind),
            "width_m": tab.widget_float(cfg.width_bind),
            "height_m": tab.widget_float(cfg.height_bind),
            "density": tab.widget_float(cfg.density_bind),
            "area": tab.widget_float(cfg.area_bind),
            "load": tab.widget_float(cfg.load_bind),
            "post_spacing_m": tab.widget_float(cfg.post_spacing_bind),
        }
        if included is not None:
            state["included"] = bool(included)
        return state

    @staticmethod
    def is_metallic(cfg: BarrierFormConfig, selected_type: str) -> bool:
        value = str(selected_type)
        return any(value.startswith(prefix) for prefix in cfg.metallic_type_prefixes)

    @staticmethod
    def is_rcc(cfg: BarrierFormConfig, selected_type: str) -> bool:
        value = str(selected_type)
        return any(value.startswith(prefix) for prefix in cfg.rcc_type_prefixes)

    @staticmethod
    def effective_type(cfg: BarrierFormConfig, selected_type: str) -> str:
        value = str(selected_type)
        return cfg.custom_fallback_type if value == "Custom" else value

    @staticmethod
    def auto_compute_load(tab, cfg: BarrierFormConfig, selected_type: str) -> None:
        if not BarrierFormHelper.is_rcc(cfg, selected_type):
            return
        try:
            density = float(tab.widget_text(cfg.density_bind).strip() or 0.0)
            area = float(tab.widget_text(cfg.area_bind).strip() or 0.0)
            tab.set_widget_text(cfg.load_bind, f"{density * area:.2f}")
        except Exception:
            tab.set_widget_text(cfg.load_bind, "")

    @staticmethod
    def apply_defaults(
        tab,
        cfg: BarrierFormConfig,
        selected_type: str,
        geom: dict | None,
        *,
        force: bool = False,
        active: bool = True,
    ) -> None:
        is_rcc = BarrierFormHelper.is_rcc(cfg, selected_type)
        is_metallic = BarrierFormHelper.is_metallic(cfg, selected_type)
        is_custom = selected_type == "Custom"

        def maybe_set(bind_name: str, value: str) -> None:
            if force or not tab.widget_text(bind_name).strip():
                tab.set_widget_text(bind_name, value)

        width_mm = BarrierFormHelper._first_geom_value(geom, cfg.width_geom_keys)
        height_mm = BarrierFormHelper._first_geom_value(geom, cfg.height_geom_keys)

        if active and is_rcc and geom:
            maybe_set(cfg.density_bind, f"{DEFAULT_CONCRETE_DENSITY:.1f}")
            if width_mm is not None:
                maybe_set(cfg.width_bind, f"{width_mm / 1000:.2f}")
            if height_mm is not None:
                maybe_set(cfg.height_bind, f"{height_mm / 1000:.2f}")
            width_m = tab.widget_float(cfg.width_bind)
            height_m = tab.widget_float(cfg.height_bind)
            if width_m is not None and height_m is not None:
                maybe_set(cfg.area_bind, f"{width_m * height_m:.2f}")
            BarrierFormHelper.auto_compute_load(tab, cfg, selected_type)
        elif active and is_metallic:
            maybe_set(cfg.post_spacing_bind, "1")
            if force:
                tab.set_widget_text(cfg.load_bind, "")
        elif active and is_custom:
            if width_mm is not None:
                maybe_set(cfg.width_bind, f"{width_mm / 1000:.2f}")
            if height_mm is not None:
                maybe_set(cfg.height_bind, f"{height_mm / 1000:.2f}")
            if force:
                tab.set_widget_text(cfg.load_bind, "")

        BarrierFormHelper.update_visibility(
            tab,
            cfg,
            selected_type,
            active=active,
        )

    @staticmethod
    def update_visibility(
        tab,
        cfg: BarrierFormConfig,
        selected_type: str,
        *,
        active: bool = True,
    ) -> None:
        is_metallic = BarrierFormHelper.is_metallic(cfg, selected_type)
        is_rcc = BarrierFormHelper.is_rcc(cfg, selected_type)
        is_custom = selected_type == "Custom"

        for bind_name in cfg.active_bind_names:
            widget = tab.get_widget(bind_name)
            if widget is not None:
                widget.setEnabled(active)

        hide_density_area = is_metallic or is_custom
        for bind_name in (
            cfg.density_bind,
            cfg.density_label_bind,
            cfg.area_bind,
            cfg.area_label_bind,
        ):
            widget = tab.get_widget(bind_name)
            if widget is not None:
                widget.setVisible(active and not hide_density_area)
        if hide_density_area:
            tab.set_widget_text(cfg.density_bind, "")
            tab.set_widget_text(cfg.area_bind, "")

        for bind_name in (cfg.post_spacing_bind, cfg.post_spacing_label_bind):
            widget = tab.get_widget(bind_name)
            if widget is not None:
                widget.setVisible(active and is_metallic)
        if active and is_metallic and not tab.widget_text(cfg.post_spacing_bind).strip():
            tab.set_widget_text(cfg.post_spacing_bind, "1")
        if not active or not is_metallic:
            tab.set_widget_text(cfg.post_spacing_bind, "")

        load_widget = tab.get_widget(cfg.load_bind)
        if load_widget is not None:
            load_widget.setEnabled(active)
            load_widget.setReadOnly(active and is_rcc)
            if active:
                load_widget.setPlaceholderText(
                    "" if not is_custom else "Enter custom load per IRC 6 guidance"
                )
        if active and is_rcc:
            BarrierFormHelper.auto_compute_load(tab, cfg, selected_type)
        elif active and load_widget is not None:
            load_widget.setReadOnly(False)

    @staticmethod
    def _first_geom_value(geom: dict | None, keys: tuple[str, ...]):
        if not geom:
            return None
        for key in keys:
            value = geom.get(key)
            if value is not None:
                return value
        return None
