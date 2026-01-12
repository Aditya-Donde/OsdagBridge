"""

Creates median barriers using existing crash barrier geometry.
"""

from OCC.Core.gp import gp_Trsf, gp_Vec
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

from osdagbridge.core.bridge_components.super_structure.crash_barrier.builder import (
    create_crash_barrier_left,
    create_crash_barrier_right
)


def _translate(shape, x=0.0, y=0.0, z=0.0):
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(x, y, z))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def build_median(
    span_length,
    deck_top_z,
    carriageway_center_y,
    crash_barrier_width,
    crash_barrier_height,
    crash_barrier_base_width,
    median_gap
):
    """
    Build median barriers.
    """

    median_barriers = []

    offset = (median_gap / 2.0) + (crash_barrier_base_width / 2.0)

    # Left median barrier
    left_barrier = create_crash_barrier_left(
        length=span_length,
        width=crash_barrier_width,
        height=crash_barrier_height,
        base_width=crash_barrier_base_width
    )

    left_barrier = _translate(
        left_barrier,
        x=0.0,
        y=carriageway_center_y - offset,
        z=deck_top_z
    )

    median_barriers.append(left_barrier)

    # Right median barrier
    right_barrier = create_crash_barrier_right(
        length=span_length,
        width=crash_barrier_width,
        height=crash_barrier_height,
        base_width=crash_barrier_base_width
    )

    right_barrier = _translate(
        right_barrier,
        x=0.0,
        y=carriageway_center_y + offset,
        z=deck_top_z
    )

    median_barriers.append(right_barrier)

    return median_barriers
