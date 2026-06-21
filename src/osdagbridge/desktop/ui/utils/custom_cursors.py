"""
Custom Cursor Utility for OsdagBridge GUI

Provides consistent cursor appearance across platforms by using custom cursor
images when the system cursor theme doesn't work properly with Qt.

This fixes the issue where Qt/xcb on Linux shows a tilted/garbled hand cursor
instead of the system's upright pointing hand cursor.

"""

import os
import platform
from functools import lru_cache

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QCursor, QPixmap, QPainter, QColor


def _create_pointing_hand_pixmap(size: int = 32) -> QPixmap:
    """
    Create a classic upright pointing hand cursor with smooth (antialiased) edges.

    The hand silhouette is defined by a pixel grid, but it is rendered at a high
    supersampled resolution and then smoothly scaled down to ``size`` so the
    edges are smooth instead of blocky.

    Args:
        size: Size of the cursor in pixels (default 32)

    Returns:
        QPixmap with transparent background and hand cursor drawn
    """
    # Exact match to user's pixel art reference
    # 0 = transparent, 1 = black (outline), 2 = white (fill)
    cursor_data = [
        "00000000000111100000000000000000",
        "00000000001222100000000000000000",
        "00000000001222100000000000000000",
        "00000000001222100000000000000000",
        "00000000001222100000000000000000",
        "00000000001222100000000000000000",
        "00000000001222111100000000000000",
        "00000000001222222100000000000000",
        "00000000001222222111100000000000",
        "00000001111222222222100000000000",
        "00000012221222222222111000000000",
        "00000012222222222222221000000000",
        "00000001222222222222221000000000",
        "00000000122222222222221000000000",
        "00000000122222222222221000000000",
        "00000000012222222222221000000000",
        "00000000012222222222221000000000",
        "00000000001222222222221000000000",
        "00000000001222222222221000000000",
        "00000000000122222222210000000000",
        "00000000000122222222210000000000",
        "00000000000111111111100000000000",
        "00000000000000000000000000000000",
        "00000000000000000000000000000000",
        "00000000000000000000000000000000",
        "00000000000000000000000000000000",
        "00000000000000000000000000000000",
        "00000000000000000000000000000000",
        "00000000000000000000000000000000",
        "00000000000000000000000000000000",
        "00000000000000000000000000000000",
        "00000000000000000000000000000000",
    ]

    # Render at a high supersampled resolution, then smooth-downscale so the
    # silhouette edges come out smooth rather than blocky.
    supersample = 8
    grid = 32                       # the cursor_data grid is 32 columns wide
    hires = size * supersample
    cell = hires / float(grid)      # size of one grid cell at high resolution

    pixmap = QPixmap(hires, hires)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    # Colors: White outline, Black fill (Inverted as per request)
    outline_color = QColor(255, 255, 255, 255)  # White outline
    fill_color = QColor(0, 0, 0, 255)      # Black fill

    for y, row in enumerate(cursor_data):
        for x, pixel in enumerate(row):
            if pixel == '1':  # Outline
                painter.fillRect(
                    QRectF(x * cell, y * cell, cell, cell), outline_color
                )
            elif pixel == '2':  # Fill
                painter.fillRect(
                    QRectF(x * cell, y * cell, cell, cell), fill_color
                )

    painter.end()

    # Smoothly scale the high-res render down to the requested cursor size.
    return pixmap.scaled(
        size, size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation
    )


@lru_cache(maxsize=4)
def get_pointing_hand_cursor(size: int = 32) -> QCursor:
    """
    Get a custom pointing hand cursor.

    On Linux with Qt6, the standard PointingHandCursor often shows incorrectly
    as a tilted hand instead of the system's upright cursor. This function
    provides a custom cursor that always looks correct.

    The cursor is cached for performance.

    Args:
        size: Cursor size in pixels (default 32)

    Returns:
        QCursor with upright pointing hand
    """
    # The hotspot is at the tip of the pointing finger
    hotspot_x = int(size * 10 / 32)  # Centered on finger tip
    hotspot_y = 0  # At the very top

    pixmap = _create_pointing_hand_pixmap(size)
    return QCursor(pixmap, hotspot_x, hotspot_y)


def should_use_custom_cursor() -> bool:
    """
    Check if we should use custom cursors.

    Returns True on Linux where Qt often fails to use the system cursor theme.
    """
    return platform.system() == "Linux"


def get_cursor(cursor_shape: Qt.CursorShape) -> QCursor:
    """
    Get a cursor, using custom implementation when needed.

    On Linux, PointingHandCursor is replaced with our custom upright hand.
    On other platforms, uses the standard Qt cursor.

    Args:
        cursor_shape: The Qt cursor shape to get

    Returns:
        QCursor for the requested shape
    """
    if cursor_shape == Qt.CursorShape.PointingHandCursor and should_use_custom_cursor():
        # Get cursor size from environment or use default
        size = int(os.environ.get("XCURSOR_SIZE", "32"))
        return get_pointing_hand_cursor(size)

    return QCursor(cursor_shape)


# Convenience function
def pointing_hand_cursor() -> QCursor:
    """Get the pointing hand cursor (custom on Linux, standard elsewhere)."""
    return get_cursor(Qt.CursorShape.PointingHandCursor)
