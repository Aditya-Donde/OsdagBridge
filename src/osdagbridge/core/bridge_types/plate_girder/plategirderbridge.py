"""Main PG bridge file """

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, Mapping, Optional

from osdagbridge.core.utils.common import (
    DEFAULT_CRASH_BARRIER_WIDTH,
    DEFAULT_GIRDER_SPACING,
    DEFAULT_RAILING_WIDTH,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_CRASH_BARRIER_WIDTH,
    KEY_DECK_OVERHANG,
    KEY_DECK_THICKNESS,
    KEY_FOOTPATH_WIDTH,
    KEY_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_GIRDER_DEPTH,
    KEY_GIRDER_SPACING,
    KEY_GIRDER_SYMMETRY,
    KEY_GIRDER_TOP_FLANGE_WIDTH,
    KEY_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_GIRDER_WEB_THICKNESS,
    KEY_INCLUDE_MEDIAN,
    KEY_NO_OF_GIRDERS,
    KEY_RAILING_WIDTH,
    KEY_SKEW_ANGLE,
    KEY_SPAN,
    MIN_FOOTPATH_WIDTH,
)

from .bridge_geometry import BridgeGeometry, CrossSectionLayout
from .cad_generator import export_step
from .designer import design
from .initial_sizing import BridgeConfigurationSolver, preliminary_sizing
from .report_generator import section_report
from .ui_fields import FrontendData
from .ui_fields_additional_input import (
    CRASH_BARRIER_TAB_SCHEMA,
    DESIGN_OPTIONS_CONT_SCHEMA,
    DESIGN_OPTIONS_SCHEMA,
    GIRDER_DETAILS_SCHEMA,
    LANE_DETAILS_TAB_SCHEMA,
    LAYOUT_TAB_SCHEMA,
    MEDIAN_TAB_SCHEMA,
    RAILING_TAB_SCHEMA,
    SUPPORT_CONDITIONS_SCHEMA,
    WEARING_COURSE_TAB_SCHEMA,
)

try:
    from .dto import PlateGirderDTO
except Exception:
    @dataclass
    class PlateGirderDTO:
        """Fallback DTO when dto.py is unavailable."""

        name: str


def _first_present(source: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in source and source[key] not in ("", None):
            return source[key]
    return None


def _as_float(value: Any, default: float) -> float:
    if value in ("", None):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int) -> int:
    if value in ("", None):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _to_m(value: Any) -> float:
    """Accept meters directly; if value looks like mm, convert to meters."""
    as_float = _as_float(value, 0.0)
    return as_float / 1000.0 if as_float > 10.0 else as_float


@dataclass
class PlateGirderRunResult:
    dto: PlateGirderDTO
    initial_sizing: Dict[str, Any] = field(default_factory=dict)
    geometry: Dict[str, Any] = field(default_factory=dict)
    analysis: Dict[str, Any] = field(default_factory=dict)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    design: Dict[str, Any] = field(default_factory=dict)
    modifier: Dict[str, Any] = field(default_factory=dict)
    cad: Dict[str, Any] = field(default_factory=dict)
    report: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PlateGirderBridge:
    """Coordinator that stitches all plate-girder modules."""

    def __init__(
        self,
        basic_inputs: Optional[Mapping[str, Any]] = None,
        additional_inputs: Optional[Mapping[str, Any]] = None,
        modifier_hook: Optional[Callable[[PlateGirderRunResult], Dict[str, Any]]] = None,
    ) -> None:
        self.basic_inputs = dict(basic_inputs or {})
        self.additional_inputs = dict(additional_inputs or {})
        self.modifier_hook = modifier_hook
        self._analysis_engine = None

    @staticmethod
    def get_basic_input_schema() -> list:
        return FrontendData().input_values()

    @staticmethod
    def get_additional_input_schema() -> Dict[str, Dict[str, Any]]:
        return {
            "layout": LAYOUT_TAB_SCHEMA,
            "crash_barrier": CRASH_BARRIER_TAB_SCHEMA,
            "median": MEDIAN_TAB_SCHEMA,
            "railing": RAILING_TAB_SCHEMA,
            "wearing_course": WEARING_COURSE_TAB_SCHEMA,
            "lane_details": LANE_DETAILS_TAB_SCHEMA,
            "support_conditions": SUPPORT_CONDITIONS_SCHEMA,
            "design_options": DESIGN_OPTIONS_SCHEMA,
            "design_options_cont": DESIGN_OPTIONS_CONT_SCHEMA,
            "girder_details": GIRDER_DETAILS_SCHEMA,
        }

    def _footpath_count(self) -> int:
        footpath_value = _first_present(self.basic_inputs, "footpath", "Footpath")
        if footpath_value is None:
            return 0
        text = str(footpath_value).strip().lower()
        if "both" in text:
            return 2
        if "single" in text:
            return 1
        return 0

    def _build_dto(self) -> PlateGirderDTO:
        structure_name = _first_present(
            self.basic_inputs,
            "Structure Type",
            "structure_type",
            "name",
        )
        return PlateGirderDTO(name=str(structure_name or "plate_girder_bridge"))

    def _run_initial_sizing(self, dto: PlateGirderDTO) -> Dict[str, Any]:
        span = _as_float(_first_present(self.basic_inputs, KEY_SPAN, "span"), 33.5)
        carriageway_width = _as_float(
            _first_present(self.basic_inputs, KEY_CARRIAGEWAY_WIDTH, "carriageway_width"),
            10.0,
        )
        no_of_footpaths = self._footpath_count()
        include_median = _as_bool(_first_present(self.basic_inputs, KEY_INCLUDE_MEDIAN, "include_median"))

        crash_barrier_width = _as_float(
            _first_present(self.additional_inputs, KEY_CRASH_BARRIER_WIDTH, "crash_barrier_width"),
            DEFAULT_CRASH_BARRIER_WIDTH,
        )
        footpath_width = _as_float(
            _first_present(self.additional_inputs, KEY_FOOTPATH_WIDTH, "footpath_width"),
            MIN_FOOTPATH_WIDTH if no_of_footpaths else 0.0,
        )
        railing_width = _as_float(
            _first_present(self.additional_inputs, KEY_RAILING_WIDTH, "railing_width"),
            DEFAULT_RAILING_WIDTH if no_of_footpaths else 0.0,
        )
        median_width = _as_float(_first_present(self.additional_inputs, "median_width"), 0.0)
        if not include_median:
            median_width = 0.0

        n_girders = max(
            2,
            _as_int(_first_present(self.additional_inputs, KEY_NO_OF_GIRDERS, "no_of_girders"), 4),
        )
        girder_spacing = _as_float(
            _first_present(self.additional_inputs, KEY_GIRDER_SPACING, "girder_spacing"),
            DEFAULT_GIRDER_SPACING,
        )
        deck_overhang = _as_float(
            _first_present(self.additional_inputs, KEY_DECK_OVERHANG, "deck_overhang"),
            0.5 * DEFAULT_GIRDER_SPACING,
        )

        top_flange_w = _to_m(
            _first_present(self.additional_inputs, KEY_GIRDER_TOP_FLANGE_WIDTH, "top_flange_width")
        )
        bot_flange_w = _to_m(
            _first_present(self.additional_inputs, KEY_GIRDER_BOTTOM_FLANGE_WIDTH, "bottom_flange_width")
        )
        max_flange_width = max(top_flange_w, bot_flange_w, 0.0)

        solver = BridgeConfigurationSolver(
            carriageway_width=carriageway_width,
            crash_barrier_width=crash_barrier_width,
            footpath_width=footpath_width,
            railing_width=railing_width,
            median_width=median_width,
            no_of_footpaths=no_of_footpaths,
            flange_width=max_flange_width,
        )

        changed_field = "girders"
        if _first_present(self.additional_inputs, KEY_DECK_OVERHANG, "deck_overhang") is not None:
            changed_field = "overhang"
        elif _first_present(self.additional_inputs, KEY_GIRDER_SPACING, "girder_spacing") is not None:
            changed_field = "spacing"

        layout_result = solver._solve_layout(
            no_of_girders=n_girders,
            girder_spacing=girder_spacing,
            deck_overhang=deck_overhang,
            changed_field=changed_field,
        )

        deck_thickness = solver.get_deck_thickness(
            _as_float(_first_present(self.additional_inputs, KEY_DECK_THICKNESS, "deck_thickness"), 200.0)
        )
        footpath_width_checked = solver.get_footpath_width(
            user_value=footpath_width,
            footpath={0: "None", 1: "Single Side", 2: "Both Sides"}.get(no_of_footpaths, "None"),
        )
        section_properties = solver.compute_section_properties(
            span=span,
            symmetry=str(
                _first_present(self.additional_inputs, KEY_GIRDER_SYMMETRY, "symmetry")
                or "Girder Symmetric"
            ),
            user_depth=_to_m(_first_present(self.additional_inputs, KEY_GIRDER_DEPTH, "depth")),
            B_top=top_flange_w,
            B_bot=bot_flange_w,
            t_f_top=_to_m(
                _first_present(self.additional_inputs, KEY_GIRDER_TOP_FLANGE_THICKNESS, "top_flange_thickness")
            ),
            t_f_bot=_to_m(_first_present(self.additional_inputs, "bottom_flange_thickness")),
            t_w=_to_m(_first_present(self.additional_inputs, KEY_GIRDER_WEB_THICKNESS, "web_thickness")),
        )

        return {
            "legacy_initial_sizing": preliminary_sizing(dto),
            "layout": asdict(layout_result),
            "deck_thickness_mm": deck_thickness,
            "footpath_width_m": footpath_width_checked,
            "section_properties": section_properties,
            "inputs_resolved": {
                "span_m": span,
                "carriageway_width_m": carriageway_width,
                "crash_barrier_width_m": crash_barrier_width,
                "railing_width_m": railing_width,
                "median_width_m": median_width,
                "no_of_footpaths": no_of_footpaths,
            },
        }

    def _build_geometry(self, initial_sizing: Dict[str, Any]) -> Dict[str, Any]:
        span = _as_float(_first_present(self.basic_inputs, KEY_SPAN, "span"), 33.5)
        layout_data = initial_sizing["layout"]
        resolved = initial_sizing["inputs_resolved"]

        layout = CrossSectionLayout(
            carriageway_width=resolved["carriageway_width_m"],
            crash_barrier_width=resolved["crash_barrier_width_m"],
            railing_width=resolved["railing_width_m"],
            footpath_width=initial_sizing["footpath_width_m"],
            median_width=resolved["median_width_m"],
            no_of_footpaths=resolved["no_of_footpaths"],
        )
        geometry = BridgeGeometry(span=span, width=layout.total_width)
        layout.verify_bridge_width(
            num_long_grid=layout_data["no_of_girders"],
            ext_to_int_dist=layout_data["girder_spacing"],
            edge_beam_dist=layout_data["deck_overhang"],
            tol=1e-3,
        )

        return {
            "span_m": geometry.span,
            "width_m": geometry.width,
            "bounds": geometry.bounds(),
            "cross_section": layout.describe(),
        }

    def _prepare_or_run_analysis(
        self,
        initial_sizing: Dict[str, Any],
        run_analysis: bool,
        include_live_load: bool,
    ) -> Dict[str, Any]:
        try:
            from .analyser import BridgeGrillageModel  # Imported lazily: heavy deps.
        except Exception as exc:
            return {"status": "skipped", "reason": f"analysis backend import failed: {exc}"}

        layout = initial_sizing["layout"]
        span = _as_float(_first_present(self.basic_inputs, KEY_SPAN, "span"), 33.5)
        skew = _as_float(_first_present(self.basic_inputs, KEY_SKEW_ANGLE, "skew_angle"), 0.0)

        engine = BridgeGrillageModel()
        engine.L = span
        engine.n_l = layout["no_of_girders"]
        engine.ext_to_int_dist = layout["girder_spacing"]
        engine.edge_dist = layout["deck_overhang"]
        engine.angle = skew
        engine.create_model()

        created_dead = []
        for method_name in (
            "create_self_weight_load",
            "create_deck_load",
            "create_wearing_course_load",
            "create_footpath_load",
            "create_crash_barrier_load",
            "create_railing_load",
            "create_median_load",
        ):
            method = getattr(engine, method_name)
            load_case = method()
            if load_case is not None:
                created_dead.append(method_name)

        created_live = []
        if include_live_load:
            for method_name in (
                "create_vehicle_load_cases",
                "add_vehicle_load_cases_from_combinations",
                "create_moving_vehicle_load_cases",
            ):
                getattr(engine, method_name)()
                created_live.append(method_name)

        status = "prepared"
        if run_analysis:
            engine.analyze()
            status = "completed"

        self._analysis_engine = engine
        return {
            "status": status,
            "dead_load_steps": created_dead,
            "live_load_steps": created_live,
        }

    def _collect_analysis_results(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        if analysis.get("status") == "skipped":
            return {"status": "skipped", "reason": analysis.get("reason")}
        if analysis.get("status") != "completed":
            return {
                "status": "not_run",
                "note": "Analysis model is prepared. Run with run_analysis=True to produce results.",
            }
        return {"status": "completed", "note": "Use BridgeGrillageModel results/plot APIs for detailed tables."}

    def run(
        self,
        *,
        run_analysis: bool = False,
        include_live_load: bool = True,
        cad_path: Optional[str] = None,
    ) -> PlateGirderRunResult:
        dto = self._build_dto()
        initial_sizing = self._run_initial_sizing(dto)
        geometry = self._build_geometry(initial_sizing)
        analysis = self._prepare_or_run_analysis(initial_sizing, run_analysis, include_live_load)
        analysis_results = self._collect_analysis_results(analysis)
        design_result = design(dto)

        modifier_result: Dict[str, Any] = {"status": "skipped", "reason": "no modifier hook provided"}
        if self.modifier_hook is not None:
            temp = PlateGirderRunResult(
                dto=dto,
                initial_sizing=initial_sizing,
                geometry=geometry,
                analysis=analysis,
                analysis_results=analysis_results,
                design=design_result,
            )
            modifier_result = self.modifier_hook(temp)

        cad_result: Dict[str, Any] = {"status": "skipped"}
        if cad_path:
            export_step(dto, cad_path)
            cad_result = {"status": "generated", "path": cad_path}

        report_result = section_report(dto)

        return PlateGirderRunResult(
            dto=dto,
            initial_sizing=initial_sizing,
            geometry=geometry,
            analysis=analysis,
            analysis_results=analysis_results,
            design=design_result,
            modifier=modifier_result,
            cad=cad_result,
            report=report_result,
        )


def run_plategirder_bridge(
    basic_inputs: Optional[Mapping[str, Any]] = None,
    additional_inputs: Optional[Mapping[str, Any]] = None,
    *,
    run_analysis: bool = False,
    include_live_load: bool = True,
    cad_path: Optional[str] = None,
    modifier_hook: Optional[Callable[[PlateGirderRunResult], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Functional wrapper around PlateGirderBridge."""
    bridge = PlateGirderBridge(
        basic_inputs=basic_inputs,
        additional_inputs=additional_inputs,
        modifier_hook=modifier_hook,
    )
    return bridge.run(
        run_analysis=run_analysis,
        include_live_load=include_live_load,
        cad_path=cad_path,
    ).to_dict()
