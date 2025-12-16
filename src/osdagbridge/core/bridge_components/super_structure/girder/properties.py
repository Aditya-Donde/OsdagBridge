"""Access rolled girder properties sourced from the bundled SQLite table.

The beam geometry and sectional properties are stored inside
``core/data/ResourceFiles/Intg_osdag.sqlite`` and originate from
IS 808:1989 (Rev.).  This module provides a thin loader that exposes the
data both as rich ``BeamSection`` records and in the minimal format that
the UI preview widgets currently expect.
"""

from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class BeamSection:
    """Representation of a rolled steel beam from the reference table."""

    id: int
    designation: str
    mass_per_meter_kg: float
    area_cm2: float
    depth_mm: float
    flange_width_mm: float
    web_thickness_mm: float
    flange_thickness_mm: float
    flange_slope: Optional[float]
    root_radius_r1_mm: Optional[float]
    root_radius_r2_mm: Optional[float]
    moment_of_inertia_zz_cm4: Optional[float]
    moment_of_inertia_yy_cm4: Optional[float]
    radius_of_gyration_z_cm: Optional[float]
    radius_of_gyration_y_cm: Optional[float]
    elastic_section_modulus_z_cm3: Optional[float]
    elastic_section_modulus_y_cm3: Optional[float]
    plastic_section_modulus_z_cm3: Optional[float]
    plastic_section_modulus_y_cm3: Optional[float]
    torsion_constant_cm4: Optional[float]
    warping_constant_cm6: Optional[float]
    source: Optional[str]
    section_type: Optional[str]

    @property
    def outline_dict(self) -> Dict[str, float]:
        """Return the minimal dictionary expected by preview widgets."""

        return {
            "designation": self.designation,
            "depth_mm": self.depth_mm,
            "top_flange_width_mm": self.flange_width_mm,
            "bottom_flange_width_mm": self.flange_width_mm,
            "web_thickness_mm": self.web_thickness_mm,
            "top_flange_thickness_mm": self.flange_thickness_mm,
            "bottom_flange_thickness_mm": self.flange_thickness_mm,
        }

    def as_dict(self) -> Dict[str, Any]:
        """Expose the full record as a plain dictionary copy."""

        return asdict(self)


# Backwards compatibility for callers importing RolledSection directly.
RolledSection = BeamSection

_DB_PATH = Path(__file__).resolve().parents[3] / "data" / "ResourceFiles" / "Intg_osdag.sqlite"
_BEAM_CACHE: Optional[Dict[str, BeamSection]] = None


def _text_or_none(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _optional_float(value: Optional[float]) -> Optional[float]:
    return None if value is None else float(value)


def _load_beam_sections() -> Dict[str, BeamSection]:
    if not _DB_PATH.exists():  # pragma: no cover - defensive guard
        raise FileNotFoundError(f"Beam property database not found at {_DB_PATH}")

    with sqlite3.connect(_DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT * FROM Beams").fetchall()

    beam_map: Dict[str, BeamSection] = {}
    for row in rows:
        designation = row["Designation"]
        beam = BeamSection(
            id=int(row["Id"]),
            designation=designation,
            mass_per_meter_kg=float(row["Mass"]),
            area_cm2=float(row["Area"]),
            depth_mm=float(row["D"]),
            flange_width_mm=float(row["B"]),
            web_thickness_mm=float(row["tw"]),
            flange_thickness_mm=float(row["T"]),
            flange_slope=_optional_float(row["FlangeSlope"]),
            root_radius_r1_mm=_optional_float(row["R1"]),
            root_radius_r2_mm=_optional_float(row["R2"]),
            moment_of_inertia_zz_cm4=_optional_float(row["Iz"]),
            moment_of_inertia_yy_cm4=_optional_float(row["Iy"]),
            radius_of_gyration_z_cm=_optional_float(row["rz"]),
            radius_of_gyration_y_cm=_optional_float(row["ry"]),
            elastic_section_modulus_z_cm3=_optional_float(row["Zz"]),
            elastic_section_modulus_y_cm3=_optional_float(row["Zy"]),
            plastic_section_modulus_z_cm3=_optional_float(row["Zpz"]),
            plastic_section_modulus_y_cm3=_optional_float(row["Zpy"]),
            torsion_constant_cm4=_optional_float(row["It"]),
            warping_constant_cm6=_optional_float(row["Iw"]),
            source=_text_or_none(row["Source"]),
            section_type=_text_or_none(row["Type"]),
        )
        beam_map[designation] = beam

    return beam_map


def _beams() -> Dict[str, BeamSection]:
    global _BEAM_CACHE
    if _BEAM_CACHE is None:
        _BEAM_CACHE = _load_beam_sections()
    return _BEAM_CACHE


def get_beam_profile(designation: str) -> Optional[BeamSection]:
    """Return the full beam profile record from the SQLite table."""

    return _beams().get(designation)


def get_rolled_section(designation: str) -> Optional[Dict[str, float]]:
    """Return the rolled section outline expected by existing UI code."""

    section = get_beam_profile(designation)
    return section.outline_dict if section else None


def list_available_sections() -> Dict[str, BeamSection]:
    """Expose the cached beam table for downstream consumers."""

    return dict(_beams())


__all__ = [
    "BeamSection",
    "RolledSection",
    "get_beam_profile",
    "get_rolled_section",
    "list_available_sections",
]
