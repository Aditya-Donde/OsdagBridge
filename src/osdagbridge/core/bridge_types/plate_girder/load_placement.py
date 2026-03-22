from __future__ import annotations

from .bridge_geometry import (
    BridgeGeometry,
    CrossSectionLayout,
)
from .dto import (
    LineLoadGeometry,
    PatchLoadGeometry,
    Point,
)


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

'''
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

    layout = CrossSectionLayout(
        carriageway_width=carriageway_width,
        crash_barrier_width=crash_barrier_width,
        railing_width=railing_width,
        footpath_width=footpath_width,
        median_width=median_width,
        no_of_footpaths=no_of_footpaths,
    )

    manager = LoadPlacementManager(bridge, layout)

    return manager
'''