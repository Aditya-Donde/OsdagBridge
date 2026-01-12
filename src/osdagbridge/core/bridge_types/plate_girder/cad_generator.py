"""
CAD generator for Plate Girder Bridge.

Thin orchestration layer:
- Defines all high-level parameters
- Calls individual builders
- Returns assembled CAD components
"""

# ---------------------------------------------------------------------
# Builder imports (ONLY high-level builders)
# ---------------------------------------------------------------------

from osdagbridge.core.bridge_components.super_structure.plate_girder.builder import (
    build_girders
)

from osdagbridge.core.bridge_components.super_structure.deck.builder import (
    build_deck
)

from osdagbridge.core.bridge_components.super_structure.crash_barrier.builder import (
    build_crash_barriers
)

from osdagbridge.core.bridge_components.super_structure.railing.builder import (
    build_railings
)

from osdagbridge.core.bridge_components.super_structure.median.builder import (
    build_median
)

# ---------------------------------------------------------------------
# GIRDERS PARAMETERS
# ---------------------------------------------------------------------

span_length_L = 25000

girder_section_d = 900
girder_section_bf = 500
girder_section_tf = 260
girder_section_tw = 100

num_girders = 5
girder_spacing = 2750

# ---------------------------------------------------------------------
# DECK PARAMETERS
# ---------------------------------------------------------------------

carriageway_width = 12000
deck_thickness = 400

footpath_config = "LEFT"          # NONE / LEFT / RIGHT / BOTH
crash_barrier_base_width = 600
footpath_width = 1500
railing_width = 300

# ---------------------------------------------------------------------
# CRASH BARRIER PARAMETERS
# ---------------------------------------------------------------------

crash_barrier_width = 175
crash_barrier_height = 900

# ---------------------------------------------------------------------
# MEDIAN PARAMETERS
# ---------------------------------------------------------------------

enable_median = True
median_gap = 800

# ---------------------------------------------------------------------
# RAILING PARAMETERS
# ---------------------------------------------------------------------

railing_height = 1200
rail_count = 3

# ---------------------------------------------------------------------
# STIFFENER PARAMETERS
# ---------------------------------------------------------------------

stiffener_width = 200
stiffener_length = 10

# ---------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------

def generate_cad():

    # -------------------------
    # Plate girder system
    # -------------------------
    girders, stiffeners = build_girders(
        span_length_L=span_length_L,
        girder_section_d=girder_section_d,
        girder_section_bf=girder_section_bf,
        girder_section_tf=girder_section_tf,
        girder_section_tw=girder_section_tw,
        num_girders=num_girders,
        girder_spacing=girder_spacing,
        stiffener_width=stiffener_width,
        stiffener_length=stiffener_length
    )

    # -------------------------
    # Deck system
    # -------------------------
    deck_out = build_deck(
        span_length_L=span_length_L,
        girder_section_d=girder_section_d,
        deck_thickness=deck_thickness,

        footpath_config=footpath_config,
        carriageway_width=carriageway_width,
        crash_barrier_base_width=crash_barrier_base_width,
        footpath_width=footpath_width,
        railing_width=railing_width
    )

    # -------------------------
    # Crash barrier system
    # -------------------------
    crash_barriers = build_crash_barriers(
        span_length_L=span_length_L,
        deck_top_z=deck_out["deck_top_z"],

        footpath_config=footpath_config,
        carriageway_width=carriageway_width,

        crash_barrier_width=crash_barrier_width,
        crash_barrier_height=crash_barrier_height,
        crash_barrier_base_width=crash_barrier_base_width,

        footpath_width=footpath_width,
        railing_width=railing_width
    )

    # -------------------------
    # Median system
    # -------------------------
    median_barriers = []

    if enable_median:
        carriageway_center_y = deck_out["carriageway_center_y"]

        median_barriers = build_median(
            span_length=span_length_L,
            deck_top_z=deck_out["deck_top_z"],
            carriageway_center_y=carriageway_center_y,

            crash_barrier_width=crash_barrier_width,
            crash_barrier_height=crash_barrier_height,
            crash_barrier_base_width=crash_barrier_base_width,

            median_gap=median_gap
        )

    # -------------------------
    # Railing system
    # -------------------------
    railings = build_railings(
        span_length=span_length_L,
        deck_top_z=deck_out["deck_top_z"],
        total_deck_width=deck_out["total_deck_width"],

        footpath_config=footpath_config,

        railing_width=railing_width,
        railing_height=railing_height,
        rail_count=rail_count
    )

    # -------------------------
    # Final output
    # -------------------------
    return {
        "girders": girders,
        "stiffeners": stiffeners,

        "deck_slab": deck_out["deck_slab"],
        "deck_textures": deck_out["deck_textures"],
        "deck_top_z": deck_out["deck_top_z"],
        "total_deck_width": deck_out["total_deck_width"],

        "crash_barriers": crash_barriers,
        "median_barriers": median_barriers,
        "railings": railings
    }
