"""
Crash barrier geometry calculations.
Takes dimensions from IRC5_2015 and computes areas only.
"""

from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015
from osdagbridge.core.utils.common import (
    KEY_CRASH_BARRIER_TYPE,
    KEY_FOOTPATH,
    KEY_RAILING_TYPE
)

#  BASIC AREA UTILITIES

def trapezoidal_area(top_w, bottom_w, height):
    return ((top_w + bottom_w) / 2) * height

def rectangular_area(width, height):
    return width * height

def post_and_spacer_area(section_area, post_height, spacer_height, spacing):
    return section_area * (post_height + spacer_height) / spacing

def w_beam_area(thickness, dev_length, n):
    return n * thickness * dev_length

# FIG 1(a) : RCC Railing + Footpath
def rcc_railing_area():
    geom = IRC5_2015.cl_109_6_3_shapes(
        barrier_type=KEY_CRASH_BARRIER_TYPE[2],     # Rigid
        footpath=KEY_FOOTPATH[1],                   # With footpath
        railing_type=KEY_RAILING_TYPE[0],           # RCC Railing
        design_dict={},
        crash_barrier_type=None
    )

    barrier_area = trapezoidal_area(
        geom['crash_barrier_top_notch'],
        geom['crash_barrier_width'],
        geom['crash_barrier_height']
    )

    return {
        "type": "Rigid Barrier with RCC Railing",
        "barrier_area": barrier_area
    }

# FIG 1(b): Steel Railing + Footpath

def steel_railing_area():
    geom = IRC5_2015.cl_109_6_3_shapes(
        barrier_type=KEY_CRASH_BARRIER_TYPE[2],     # Rigid
        footpath=KEY_FOOTPATH[1],                   # With footpath
        railing_type=KEY_RAILING_TYPE[1],           # Steel railing
        design_dict={},
        crash_barrier_type=None
    )

    barrier_area = trapezoidal_area(
        geom['crash_barrier_top_notch'],
        geom['crash_barrier_width'],
        geom['crash_barrier_height']
    )

    return {
        "type": "Rigid Barrier with Steel Railing",
        "barrier_area": barrier_area
    }