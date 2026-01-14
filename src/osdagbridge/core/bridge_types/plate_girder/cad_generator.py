"""
CAD generator for Plate Girder Bridge.

"""

# Builder imports

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

from osdagbridge.core.bridge_components.super_structure.cross_bracing.builder import (
    build_cross_bracings
)


# CAD GENERATOR CLASS

class PlateGirderCADGenerator:
    """
    Plate Girder Bridge CAD Generator.

    Holds parameters and generates assembled CAD geometry.
    """

    def __init__(self):

        # GIRDERS PARAMETERS
        self.span_length_L = 25000

        self.girder_section_d = 900
        self.girder_section_bf = 500
        self.girder_section_tf = 260
        self.girder_section_tw = 100

        self.num_girders = 5
        self.girder_spacing = 2750

        # DECK PARAMETERS
        self.carriageway_width = 12000
        self.deck_thickness = 400

        self.footpath_config = "LEFT"   # NONE / LEFT / RIGHT / BOTH
        self.crash_barrier_base_width = 600
        self.footpath_width = 1500
        self.railing_width = 300

        # CRASH BARRIER PARAMETERS
        self.crash_barrier_width = 175
        self.crash_barrier_height = 900

        # MEDIAN PARAMETERS
        self.enable_median = True
        self.median_gap = 800

        # RAILING PARAMETERS
        self.railing_height = 1200
        self.rail_count = 3

        # STIFFENER PARAMETERS
        self.stiffener_width = 200
        self.stiffener_length = 10

        # CROSS BRACING PARAMETERS
        self.cross_bracing_spacing = 4000
        self.cross_bracing_thickness = 5

        self.bracing_type = "K"   # "X" or "K"
        self.x_bracket_option = "BOTH"
        self.k_top_bracket = True

        self.cross_bracing_section_type = "CHANNEL"
        self.cross_bracing_section_dims = {
            "depth": 100,
            "flange_width": 50,
            "web_thickness": 5,
            "flange_thickness": 7
        }

    # MAIN CAD GENERATION

    def generate(self):
        """
        Generate full bridge CAD.

        Returns
        -------
        dict
            Dictionary of assembled CAD components
        """

        # Plate girder system
        girders, stiffeners = build_girders(
            span_length_L=self.span_length_L,
            girder_section_d=self.girder_section_d,
            girder_section_bf=self.girder_section_bf,
            girder_section_tf=self.girder_section_tf,
            girder_section_tw=self.girder_section_tw,
            num_girders=self.num_girders,
            girder_spacing=self.girder_spacing,
            stiffener_width=self.stiffener_width,
            stiffener_length=self.stiffener_length
        )

        # Cross bracing system
        cross_bracings = build_cross_bracings(
            span_length_L=self.span_length_L,
            num_girders=self.num_girders,
            girder_spacing=self.girder_spacing,
            girder_depth=self.girder_section_d,
            flange_thickness=self.girder_section_tf,
            flange_width=self.girder_section_bf,

            bracing_type=self.bracing_type,
            section_type=self.cross_bracing_section_type,
            section_dims=self.cross_bracing_section_dims,
            thickness=self.cross_bracing_thickness,

            panel_spacing=self.cross_bracing_spacing,
            bracket_option=self.x_bracket_option,
            top_bracket=self.k_top_bracket
        )

        # Deck system
        deck_out = build_deck(
            span_length_L=self.span_length_L,
            girder_section_d=self.girder_section_d,
            deck_thickness=self.deck_thickness,

            footpath_config=self.footpath_config,
            carriageway_width=self.carriageway_width,
            crash_barrier_base_width=self.crash_barrier_base_width,
            footpath_width=self.footpath_width,
            railing_width=self.railing_width
        )

        # Crash barrier system
        crash_barriers = build_crash_barriers(
            span_length_L=self.span_length_L,
            deck_top_z=deck_out["deck_top_z"],

            footpath_config=self.footpath_config,
            carriageway_width=self.carriageway_width,

            crash_barrier_width=self.crash_barrier_width,
            crash_barrier_height=self.crash_barrier_height,
            crash_barrier_base_width=self.crash_barrier_base_width,

            footpath_width=self.footpath_width,
            railing_width=self.railing_width
        )

        # Median system
        median_barriers = []
        if self.enable_median:
            median_barriers = build_median(
                span_length=self.span_length_L,
                deck_top_z=deck_out["deck_top_z"],
                carriageway_center_y=deck_out["carriageway_center_y"],

                crash_barrier_width=self.crash_barrier_width,
                crash_barrier_height=self.crash_barrier_height,
                crash_barrier_base_width=self.crash_barrier_base_width,

                median_gap=self.median_gap
            )

        # Railing system
        railings = build_railings(
            span_length=self.span_length_L,
            deck_top_z=deck_out["deck_top_z"],
            total_deck_width=deck_out["total_deck_width"],

            footpath_config=self.footpath_config,

            railing_width=self.railing_width,
            railing_height=self.railing_height,
            rail_count=self.rail_count
        )

        return {
            "girders": girders,
            "stiffeners": stiffeners,
            "cross_bracings": cross_bracings,

            "deck_slab": deck_out["deck_slab"],
            "deck_textures": deck_out["deck_textures"],
            "deck_top_z": deck_out["deck_top_z"],
            "total_deck_width": deck_out["total_deck_width"],

            "crash_barriers": crash_barriers,
            "median_barriers": median_barriers,
            "railings": railings
        }

