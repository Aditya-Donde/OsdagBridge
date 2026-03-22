from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

__all__ = [
    "SectionComponent",
    "Point",
    "LineLoadGeometry",
    "PatchLoadGeometry",
    "SectionProperties",
    "MaterialProperties",
    "GrillageGeometry",
    "DeckLayoutProperties",
]

# ------------------------------------------------------------------
# DTOs for cross-section components
# ------------------------------------------------------------------

@dataclass(frozen=True)
class SectionComponent:
    name: str
    width: float
    z_start: float
    z_end: float

    @property
    def center(self) -> float:
        return 0.5 * (self.z_start + self.z_end)


# ------------------------------------------------------------------
# DTOs for load geometry
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# DTOs for bridge geometry and properties (for analyser file)
# ------------------------------------------------------------------

@dataclass(frozen=True)
class SectionProperties:
    """
    Holds cross-section properties for a single grillage member.

    Attributes
    ----------
    A : float
        Cross-sectional area (m^2).
    J : float
        Torsional constant (m^3).
    Iz : float
        Second moment of area about z-axis (m^4).
    Iy : float
        Second moment of area about y-axis (m^4).
    Az : float
        Shear area in z-direction (m^2).
    Ay : float
        Shear area in y-direction (m^2).
    """
    A: float
    J: float
    Iz: float
    Iy: float
    Az: float
    Ay: float


@dataclass(frozen=True)
class MaterialProperties:
    """
    Holds custom material properties for a grillage member.

    Attributes
    ----------
    material : str
        Material type string (e.g. "steel", "concrete").
    E : float
        Elastic modulus (Pa).
    v : float
        Poisson's ratio.
    rho : float
        Density (kN/m^3).
    Fy : float, optional
        Yield strength (Pa). Required for steel.
    E0 : float, optional
        Initial elastic modulus (Pa). Required for steel.
    b : float, optional
        Strain-hardening ratio. Required for steel.
    """
    material: str
    E: float
    v: float
    rho: float
    Fy: Optional[float] = None
    E0: Optional[float] = None
    b: Optional[float] = None

    def __post_init__(self) -> None:
        if self.material == "steel":
            if any(val is None for val in (self.Fy, self.E0, self.b)):
                raise ValueError(
                    "Fy, E0, and b are all required when material is 'steel'."
                )


@dataclass(frozen=True)
class GrillageGeometry:
    """
    Holds grillage grid geometry parameters.

    Attributes
    ----------
    L : float
        Bridge span length (m).
    n_l : int
        Number of longitudinal grid lines.
    n_t : int
        Number of transverse grid lines.
    edge_dist : float
        Edge beam distance / overhang (m). Use 0 for no overhang.
    ext_to_int_dist : float
        Distance from exterior to interior beam (m).
    angle : float
        Skew angle in degrees. Use 0 for a right bridge.
    """
    L: float
    n_l: int
    n_t: int
    edge_dist: float
    ext_to_int_dist: float
    angle: float


@dataclass(frozen=True)
class DeckLayoutProperties:
    """
    Holds deck cross-section layout properties.

    Attributes
    ----------
    carriageway_width : float
        Width of the carriageway (m).
    crash_barrier_width : float
        Width of each crash barrier (m).
    footpath_width : float
        Width of each footpath (m).
    railing_width : float
        Width of each railing (m).
    median_width : float
        Width of the median (m). Use 0 if no median.
    n_footpaths : int
        Number of footpaths.
    """
    carriageway_width: float
    crash_barrier_width: float
    footpath_width: float
    railing_width: float
    median_width: float
    n_footpaths: int