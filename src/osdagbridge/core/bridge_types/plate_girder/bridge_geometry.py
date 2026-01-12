from __future__ import annotations
from dataclasses import dataclass
import warnings

@dataclass(frozen=True)
class Point:
    x: float
    z: float


@dataclass(frozen=True)
class LineLoadGeometry:
    start: Point
    end: Point


@dataclass(frozen=True)
class PatchLoadGeometry:
    p1: Point
    p2: Point
    p3: Point
    p4: Point

@dataclass(frozen=True)
class SectionComponent:
    name: str
    width: float
    z_start: float
    z_end: float

    @property
    def center(self) -> float:
        return 0.5 * (self.z_start + self.z_end)
    

@classmethod
def from_layout(cls, layout: CrossSectionLayout, span: float):
    bridge = BridgeGeometry(span=span, width=layout.total_width)
    layout.validate_against_bridge(bridge.width)
    return cls(bridge, layout)


class BridgeGeometry:
    """
    Defines global coordinate system of the bridge.
    Origin: bottom-left corner of deck
    x → span
    z → width
    """

    def __init__(self, span: float, width: float):
        self.span = span
        self.width = width

    def bounds(self):
        return {
            "x_min": 0.0,
            "x_max": self.span,
            "z_min": 0.0,
            "z_max": self.width,
        }


class BridgeComponent:
    def __init__(self, bridge: BridgeGeometry):
        self.bridge = bridge

    def to_global(self):
        """
        Must return LineLoadGeometry or PatchLoadGeometry
        """
        raise NotImplementedError


class CrashBarrier(BridgeComponent):
    def __init__(self, bridge, offset_from_edge: float, side="left"):
        super().__init__(bridge)
        self.offset = offset_from_edge
        self.side = side

    def to_global(self) -> LineLoadGeometry:
        if self.side == "left":
            z = self.offset
        elif self.side == "right":
            z = self.bridge.width - self.offset
        else:
            raise ValueError("side must be 'left' or 'right'")

        return LineLoadGeometry(
            start=Point(x=0.0, z=z),
            end=Point(x=self.bridge.span, z=z),
        )

class DeckLoad(BridgeComponent):
    def to_global(self) -> PatchLoadGeometry:
        return PatchLoadGeometry(
            p1=Point(0.0, 0.0),
            p2=Point(self.bridge.span, 0.0),
            p3=Point(self.bridge.span, self.bridge.width),
            p4=Point(0.0, self.bridge.width),
        )


class OverlayLoad(BridgeComponent):
    def __init__(self, bridge, edge_clearance: float):
        super().__init__(bridge)
        self.c = edge_clearance

    def to_global(self) -> PatchLoadGeometry:
        return PatchLoadGeometry(
            p1=Point(0.0, self.c),
            p2=Point(self.bridge.span, self.c),
            p3=Point(self.bridge.span, self.bridge.width - self.c),
            p4=Point(0.0, self.bridge.width - self.c),
        )


class RailingLoad(BridgeComponent):
    def __init__(self, bridge, offset_from_edge: float, side="left"):
        super().__init__(bridge)
        self.offset = offset_from_edge
        self.side = side

    def to_global(self) -> LineLoadGeometry:
        z = self.offset if self.side == "left" else self.bridge.width - self.offset

        return LineLoadGeometry(
            start=Point(x=0.0, z=z),
            end=Point(x=self.bridge.span, z=z),
        )


class MedianLoad(BridgeComponent):
    def __init__(self, bridge, offset_from_edge: float, side="left"):
        super().__init__(bridge)
        self.offset = offset_from_edge
        self.side = side

    def to_global(self) -> LineLoadGeometry:
        z = self.offset if self.side == "left" else self.bridge.width - self.offset

        return LineLoadGeometry(
            start=Point(x=0.0, z=z),
            end=Point(x=self.bridge.span, z=z),
        )
    

class FootpathLoad(BridgeComponent):
    def __init__(self, bridge, start_offset: float, width: float):
        super().__init__(bridge)
        self.start = start_offset
        self.width = width

    def to_global(self) -> PatchLoadGeometry:
        return PatchLoadGeometry(
            p1=Point(0.0, self.start),
            p2=Point(self.bridge.span, 0.0),
            p3=Point(self.bridge.span, self.start + self.width),
            p4=Point(0.0, self.start + self.width),
        )


class LoadPlacementManager:
    """
    Generates load geometries using BridgeGeometry and CrossSectionLayout
    """

    def __init__(self, bridge: BridgeGeometry, layout: CrossSectionLayout):
        self.bridge = bridge
        self.layout = layout

    # -------------------------
    # Patch loads
    # -------------------------
    def deck_load(self) -> PatchLoadGeometry:
        return PatchLoadGeometry(
            p1=Point(0.0, 0.0),
            p2=Point(self.bridge.span, 0.0),
            p3=Point(self.bridge.span, self.bridge.width),
            p4=Point(0.0, self.bridge.width),
        )

    def overlay_load(self, edge_clearance: float) -> PatchLoadGeometry:
        return PatchLoadGeometry(
            p1=Point(0.0, edge_clearance),
            p2=Point(self.bridge.span, edge_clearance),
            p3=Point(self.bridge.span, self.bridge.width - edge_clearance),
            p4=Point(0.0, self.bridge.width - edge_clearance),
        )

    def footpath_load(self, side: str) -> PatchLoadGeometry:
        comp = self.layout.get_component(f"footpath_{side}")
        return PatchLoadGeometry(
            p1=Point(0.0, comp.z_start),
            p2=Point(self.bridge.span, comp.z_start),
            p3=Point(self.bridge.span, comp.z_end),
            p4=Point(0.0, comp.z_end),
        )
    

    # -------------------------
    # Line loads
    # -------------------------
    def crash_barrier_load(self, side: str) -> LineLoadGeometry:
        comp = self.layout.get_component(f"crash_barrier_{side}")
        z = comp.center
        return LineLoadGeometry(
            start=Point(0.0, z),
            end=Point(self.bridge.span, z),
        )

    def railing_load(self, side: str) -> LineLoadGeometry:
        comp = self.layout.get_component(f"railing_{side}")
        z = comp.center
        return LineLoadGeometry(
            start=Point(0.0, z),
            end=Point(self.bridge.span, z),
        )
    
    def median_line_load(self) -> LineLoadGeometry:
        """
        Line load corresponding to median (acting along its centerline)
        """
        comp = self.layout.get_component("median")
        z = comp.center

        return LineLoadGeometry(
            start=Point(0.0, z),
            end=Point(self.bridge.span, z),
        )

class CrossSectionLayout:
    """
    Defines ordered cross-section layout of bridge deck.
    """

    ORDER = [
        "railing_left",
        "footpath_left",
        "crash_barrier_left",
        "carriageway_left",
        "median",
        "carriageway_right",
        "crash_barrier_right",
        "footpath_right",
        "railing_right",
    ]

    def __init__(
        self,
        *,
        carriageway_width: float,
        crash_barrier_width: float,
        railing_width: float = 0.0,
        footpath_width: float = 0.0,
        median_width: float = 0.0,
        no_of_footpaths: int = 0,   # 0, 1, or 2
    ):
        self.carriageway_width = carriageway_width
        self.crash_barrier_width = crash_barrier_width
        self.railing_width = railing_width
        self.footpath_width = footpath_width
        self.median_width = median_width
        self.no_of_footpaths = no_of_footpaths

        self._components = []
        self._build_layout()

    def _build_layout(self):
        z = 0.0

        def add(name, width):
            nonlocal z
            if width <= 0:
                return
            comp = SectionComponent(
                name=name,
                width=width,
                z_start=z,
                z_end=z + width,
            )
            self._components.append(comp)
            z += width
        # Left side
        if self.no_of_footpaths >= 1:
            add("railing_left", self.railing_width)
            add("footpath_left", self.footpath_width)

        add("crash_barrier_left", self.crash_barrier_width)
        add("carriageway_left", self.carriageway_width / 2.0)

        # Median
        add("median", self.median_width)

        # Right side
        add("carriageway_right", self.carriageway_width / 2.0)
        add("crash_barrier_right", self.crash_barrier_width)

        if self.no_of_footpaths >= 2:
            add("footpath_right", self.footpath_width)
            add("railing_right", self.railing_width)

        self.total_width = z

    def get_component(self, name: str) -> SectionComponent:
        for c in self._components:
            if c.name == name:
                return c
        raise KeyError(f"Component '{name}' not present in layout")

    def has_component(self, name: str) -> bool:
        return any(c.name == name for c in self._components)

    def components(self):
        return list(self._components)
    
    def validate_against_bridge(self, bridge_width: float, tol: float = 1e-6):
        """
        Validate that cross-section width matches bridge width.

        Parameters
        ----------
        bridge_width : float
            Width used in BridgeGeometry
        tol : float
            Numerical tolerance

        Raises
        ------
        ValueError if widths do not match
        """

        if abs(self.total_width - bridge_width) > tol:
            raise ValueError(
                f"Cross-section width mismatch:\n"
                f"  CrossSectionLayout width = {self.total_width:.3f} m\n"
                f"  BridgeGeometry width     = {bridge_width:.3f} m\n"
                f"  Difference               = {abs(self.total_width - bridge_width):.6f} m"
            )
    
    def describe(self):
        return " | ".join(
            f"{c.name}({c.width:.2f})" for c in self._components
        )



# @warnings.deprecated("This function is deprecated, use CrossSectionLayout.total_width instead.")   
def calculate_bridge_width(
    carriageway_width: float,
    crash_barrier_width: float,
    median_width: float,
    no_of_footpaths: int,
    footpath_width: float,
    railing_width: float,
) -> float:
    """
    Calculate overall bridge width based on components.

    Returns
    -------
    float
        Overall bridge width (x-direction)
    """

    return (
        carriageway_width
        + 2.0 * crash_barrier_width
        + median_width
        + no_of_footpaths * footpath_width
        + no_of_footpaths * railing_width
    )

def create_default_load_placement(
    span: float,
    carriageway_width: float,
    crash_barrier_width: float,
    no_of_footpaths: int,
    footpath_width: float,
    railing_width: float,
    median_width: float,
) -> LoadPlacementManager:
    """
    Create default bridge load placement from UI inputs.
    """

    # -----------------------------
    # Calculate bridge width
    # -----------------------------
    bridge_width = calculate_bridge_width(
        carriageway_width=carriageway_width,
        crash_barrier_width=crash_barrier_width,
        no_of_footpaths=no_of_footpaths,
        footpath_width=footpath_width,
        railing_width=railing_width,
        median_width=median_width,
    )

    # -----------------------------
    # Bridge geometry
    # -----------------------------
    bridge = BridgeGeometry(span=span, width=bridge_width)

    manager = LoadPlacementManager(bridge)

    # -----------------------------
    # Components
    # -----------------------------
    deck = DeckLoad(bridge)
    overlay = OverlayLoad(bridge, edge_clearance=0.30)     #is edge clearance needed?

    # Crash barriers (both sides of carriageway)
    left_crash_barrier = CrashBarrier(
        bridge,
        offset_from_edge=crash_barrier_width / 2.0,
        side="left",
    )

    right_crash_barrier = CrashBarrier(
        bridge,
        offset_from_edge=crash_barrier_width / 2.0,
        side="right",
    )
    
    medain = MedianLoad(
        bridge,
        offset_from_edge=median_width / 2.0,
        side="left"
    )

    # Footpath & railing (example: left side only)
    if no_of_footpaths >= 1:
        footpath = FootpathLoad(
            bridge,
            start_offset=crash_barrier_width,
            width=footpath_width,
        )

        railing = RailingLoad(
            bridge,
            offset_from_edge=crash_barrier_width + footpath_width + railing_width / 2.0,
            side="left",
        )

        manager.add_component(footpath)
        manager.add_component(railing)

    # -----------------------------
    # Register common components
    # -----------------------------
    manager.add_component(deck)
    manager.add_component(overlay)
    manager.add_component(medain)
    manager.add_component(left_crash_barrier)
    manager.add_component(right_crash_barrier)

    return manager

