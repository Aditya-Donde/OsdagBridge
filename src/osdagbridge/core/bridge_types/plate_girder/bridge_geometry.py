from __future__ import annotations

from osdagbridge.core.bridge_types.plate_girder.dto import SectionComponent


class BridgeGeometry:
    """
    Defines global coordinate system of the bridge.
    Origin: bottom-left corner of deck
    x → span
    z → width
    """

    def __init__(self, span: float, width: float) -> None:
        self.span = span
        self.width = width

    @classmethod
    def from_layout(cls, layout: CrossSectionLayout, span: float) -> BridgeGeometry:
        bridge = cls(span=span, width=layout.total_width)
        layout.validate_against_bridge(bridge.width)
        return bridge

    @property
    def bounds(self) -> dict[str, float]:
        return {
            "x_min": 0.0,
            "x_max": self.span,
            "z_min": 0.0,
            "z_max": self.width,
        }


class CrossSectionLayout:
    """
    Defines ordered cross-section layout of bridge deck.
    """

    def __init__(
        self,
        *,
        carriageway_width: float,
        crash_barrier_width: float,
        railing_width: float = 0.0,
        footpath_width: float = 0.0,
        median_width: float = 0.0,
        n_footpaths: int = 0,   # 0, 1, or 2
    ):
        self.carriageway_width = carriageway_width
        self.crash_barrier_width = crash_barrier_width
        self.railing_width = railing_width
        self.footpath_width = footpath_width
        self.median_width = median_width
        self.n_footpaths = n_footpaths

        self.total_width: float = 0.0
        self._components: list[SectionComponent] = []
        self._build_layout()

    def _build_layout(self) -> None:
        z = 0.0

        def add(name: str, width: float) -> None:
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
        if self.n_footpaths >= 1:
            add("railing_left", self.railing_width)
            add("footpath_left", self.footpath_width)

        add("crash_barrier_left", self.crash_barrier_width)

        # Carriageway + median logic
        if self.median_width > 0.0:
            add("carriageway_left", self.carriageway_width)
            add("median", self.median_width)
            add("carriageway_right", self.carriageway_width)
        else:
            add("carriageway", self.carriageway_width)

        add("crash_barrier_right", self.crash_barrier_width)

        # Right side
        if self.n_footpaths >= 2:
            add("footpath_right", self.footpath_width)
            add("railing_right", self.railing_width)

        # for c in self._components:
        #     print(c.name, c.z_start, c.z_end)

        self.total_width = z

    def verify_bridge_width(
        self,
        num_long_grid: int,
        ext_to_int_dist: float,
        edge_beam_dist: float,
        tol: float = 1e-6,
    ) -> bool:
        """
        Cross-check that the cross-section total_width matches the overall
        bridge width derived from grillage geometry parameters.

        This is a grillage geometry cross-check, not a construction validator.
        For construction-time width validation, see validate_against_bridge().

        Formula:
            OverallBridgeWidth = (num_long_grid - 1) * ext_to_int_dist + 2 * edge_beam_dist

        Parameters
        ----------
        num_long_grid : int
            Number of longitudinal girders (n_l in analyser).
        ext_to_int_dist : float
            Spacing between exterior and interior girders.
        edge_beam_dist : float
            Edge distance / deck overhang.
        tol : float
            Numerical tolerance for comparison.

        Returns
        -------
        bool
            True if widths match within tolerance.

        Raises
        ------
        ValueError
            If the computed width does not match `total_width`.
        """
        computed_width = (num_long_grid - 1) * ext_to_int_dist + 2 * edge_beam_dist

        if abs(self.total_width - computed_width) > tol:
            raise ValueError(
                f"Bridge width verification failed:\n"
                f"  CrossSectionLayout total_width = {self.total_width:.4f} m\n"
                f"  Computed from grillage geometry = {computed_width:.4f} m\n"
                f"    (num_long_grid - 1) * ext_to_int_dist + 2 * edge_beam_dist\n"
                f"    = ({num_long_grid} - 1) * {ext_to_int_dist:.4f} + 2 * {edge_beam_dist:.4f}\n"
                f"  Difference = {abs(self.total_width - computed_width):.6f} m"
            )
        return True

    def get_component(self, name: str) -> SectionComponent:
        for c in self._components:
            if c.name == name:
                return c
        raise KeyError(f"Component '{name}' not present in layout")

    def has_component(self, name: str) -> bool:
        return any(c.name == name for c in self._components)

    @property
    def components(self) -> list[SectionComponent]:
        return list(self._components)

    def validate_against_bridge(self, bridge_width: float, tol: float = 1e-6) -> None:
        """
        Validate that cross-section width matches bridge width.
        Called during construction via BridgeGeometry.from_layout().

        For grillage geometry cross-checking, see verify_bridge_width().

        Parameters
        ----------
        bridge_width : float
            Width used in BridgeGeometry.
        tol : float
            Numerical tolerance.

        Raises
        ------
        ValueError
            If widths do not match.
        """
        if abs(self.total_width - bridge_width) > tol:
            raise ValueError(
                f"Cross-section width mismatch:\n"
                f"  CrossSectionLayout width = {self.total_width:.3f} m\n"
                f"  BridgeGeometry width     = {bridge_width:.3f} m\n"
                f"  Difference               = {abs(self.total_width - bridge_width):.6f} m"
            )

    def describe(self) -> str:
        return " | ".join(
            f"{c.name}({c.width:.2f})" for c in self._components
        )


'''
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
'''