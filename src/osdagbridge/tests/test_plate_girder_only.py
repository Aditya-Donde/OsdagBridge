"""
Test file for Plate Girder Bridge CAD Generator
(Girder + Stiffeners + Deck + Crash Barriers + Median + Railings)
"""

from OCC.Display.SimpleGui import init_display
from OCC.Display.backend import load_backend
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

load_backend("pyside6")

from osdagbridge.core.bridge_types.plate_girder.cad_generator import (
    generate_cad
)

# Colors (RGB 0–1)

COLOR_GIRDER = (72/255, 72/255, 54/255)
COLOR_STIFFENER = (30/255, 30/255, 30/255)
COLOR_DECK = (180/255, 180/255, 180/255)
COLOR_DECK_TEXTURE = (150/255, 150/255, 150/255)
COLOR_CRASH_BARRIER = (120/255, 120/255, 120/255)
COLOR_MEDIAN = (110/255, 110/255, 110/255)
COLOR_RAILING = (90/255, 90/255, 90/255)


def main():
    display, start_display, _, _ = init_display()

    cad = generate_cad()

    # Quantity colors
    girder_color = Quantity_Color(*COLOR_GIRDER, Quantity_TOC_RGB)
    stiffener_color = Quantity_Color(*COLOR_STIFFENER, Quantity_TOC_RGB)
    deck_color = Quantity_Color(*COLOR_DECK, Quantity_TOC_RGB)
    deck_texture_color = Quantity_Color(*COLOR_DECK_TEXTURE, Quantity_TOC_RGB)
    crash_barrier_color = Quantity_Color(*COLOR_CRASH_BARRIER, Quantity_TOC_RGB)
    median_color = Quantity_Color(*COLOR_MEDIAN, Quantity_TOC_RGB)
    railing_color = Quantity_Color(*COLOR_RAILING, Quantity_TOC_RGB)

    # Display girders
    for girder in cad["girders"]:
        display.DisplayColoredShape(girder, girder_color, update=False)

    # Display stiffeners
    for stiffener in cad["stiffeners"]:
        display.DisplayColoredShape(stiffener, stiffener_color, update=False)

    # Display deck slab
    display.DisplayColoredShape(
        cad["deck_slab"],
        deck_color,
        update=False
    )

    # Display deck textures
    for tex in cad["deck_textures"]:
        display.DisplayColoredShape(tex, deck_texture_color, update=False)

    # Display crash barriers
    for barrier in cad["crash_barriers"]:
        display.DisplayColoredShape(barrier, crash_barrier_color, update=False)

    # Display median barriers (optional)
    if "median_barriers" in cad:
        for median in cad["median_barriers"]:
            display.DisplayColoredShape(median, median_color, update=False)

    # Display railings
    for railing in cad["railings"]:
        display.DisplayColoredShape(railing, railing_color, update=False)

    display.FitAll()
    start_display()


if __name__ == "__main__":
    main()
