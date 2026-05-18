"""Quick test for solve_bridge_layout — prints the full input_dict after solving."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from osdagbridge.core.bridge_types.plate_girder.defaults import (
    extend_basic_input_dict,
    solve_bridge_layout,
    BASIC_INPUT_DICT,
)
from osdagbridge.core.utils.common import (
    KEY_GIRDER_SYMMETRY, KEY_GIRDER_DEPTH, KEY_GIRDER_WEB_DEPTH, KEY_GIRDER_WEB_THICKNESS,
    KEY_GIRDER_TOP_FLANGE_WIDTH, KEY_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_GIRDER_BOTTOM_FLANGE_WIDTH, KEY_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_GIRDER_SECTIONAL_AREA, KEY_GIRDER_MASS,
    KEY_GIRDER_SECTIONAL_IZ, KEY_GIRDER_SECTIONAL_IY,
    KEY_GIRDER_RADIUS_GYRATION_Z, KEY_GIRDER_RADIUS_GYRATION_Y,
    KEY_GIRDER_ELASTIC_MODULUS_ZZ, KEY_GIRDER_ELASTIC_MODULUS_ZY,
    KEY_GIRDER_PLASTIC_MODULUS_ZUZ, KEY_GIRDER_PLASTIC_MODULUS_ZUY,
    KEY_GIRDER_TORSION_CONSTANT_IT, KEY_GIRDER_WARPING_CONSTANT_IW,
)

# Build a minimal input dict (same as what the UI would have after user fills required fields)
input_dict = dict(BASIC_INPUT_DICT)
input_dict.update({
    "geometry.span":             30.0,    # metres
    "geometry.carriageway_width": 7.5,   # metres (2-lane)
    "geometry.footpath":         "None", # no footpath
    "geometry.design_mode":      "Optimized",
    "geometry.include_median":   "No",
})

# Step 1: extend with additional-input defaults (mirrors common_design_func)
extend_basic_input_dict(input_dict)

# Patch in crash barrier and median widths (extend sets them to None; provide defaults)
input_dict["typical_section.crash_barrier.width"] = 0.45   # metres
input_dict["typical_section.median.width"]         = 0.0

# Step 2: solve layout (the function under test)
solve_bridge_layout(input_dict)

# ── Print results ────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("  Layout keys written to input_dict")
print("=" * 60)
layout_keys = [
    "typical_section.overall_bridge_width",
    "typical_section.no_of_girders",
    "typical_section.girder_spacing",
    "typical_section.deck_overhang",
    "typical_section.no_of_footpaths",
    "typical_section.footpath_width",
    "typical_section.railing.width",
]
for k in layout_keys:
    print(f"  {k:<60} = {input_dict.get(k)}")

print("\n" + "=" * 60)
print("  Member / section property keys written to input_dict")
print("=" * 60)
section_keys = [
    KEY_GIRDER_SYMMETRY,
    KEY_GIRDER_DEPTH,
    KEY_GIRDER_WEB_DEPTH,
    KEY_GIRDER_WEB_THICKNESS,
    KEY_GIRDER_TOP_FLANGE_WIDTH,
    KEY_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_GIRDER_SECTIONAL_AREA,
    KEY_GIRDER_MASS,
    KEY_GIRDER_SECTIONAL_IZ,
    KEY_GIRDER_SECTIONAL_IY,
    KEY_GIRDER_RADIUS_GYRATION_Z,
    KEY_GIRDER_RADIUS_GYRATION_Y,
    KEY_GIRDER_ELASTIC_MODULUS_ZZ,
    KEY_GIRDER_ELASTIC_MODULUS_ZY,
    KEY_GIRDER_PLASTIC_MODULUS_ZUZ,
    KEY_GIRDER_PLASTIC_MODULUS_ZUY,
    KEY_GIRDER_TORSION_CONSTANT_IT,
    KEY_GIRDER_WARPING_CONSTANT_IW,
]
for k in section_keys:
    print(f"  {k:<60} = {input_dict.get(k)}")

print("\n" + "=" * 60)
print("  Typical Section tab keys (after _update_typical_section_defaults)")
print("=" * 60)
ts_keys = [
    "typical_section.deck_thickness",
    "typical_section.footpath_thickness",
    "typical_section.crash_barrier.type",
    "typical_section.crash_barrier.density",
    "typical_section.crash_barrier.width",
    "typical_section.crash_barrier.height",
    "typical_section.crash_barrier.area",
    "typical_section.crash_barrier.load",
    "typical_section.crash_barrier.post_spacing",
    "typical_section.median.type",
    "typical_section.median.density",
    "typical_section.median.width",
    "typical_section.median.height",
    "typical_section.median.area",
    "typical_section.median.load",
    "typical_section.median.post_spacing",
    "typical_section.railing.type",
    "typical_section.railing.height",
    "typical_section.railing.load_mode",
    "typical_section.railing.load_value",
    "typical_section.wearing_course.material",
    "typical_section.wearing_course.density",
    "typical_section.wearing_course.thickness",
]
for k in ts_keys:
    print(f"  {k:<45} = {input_dict.get(k)}")
