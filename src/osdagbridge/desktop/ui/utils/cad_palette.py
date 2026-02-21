"""Shared color palette for 2D CAD-style previews.

Keep all 2D CAD previews visually consistent across the desktop UI.
"""

from __future__ import annotations

from PySide6.QtGui import QColor


# Brand / primary accent used in CAD dimension lines.
OSDAG_BRAND_GREEN = QColor("#90AF13")

# Typography used by CAD preview widgets.
OSDAG_FONT_FAMILY = "Ubuntu Sans"

# Core CAD canvas + ink.
CAD_CANVAS_BG = QColor("#ffffff")
CAD_SHAPE_FILL = QColor("#fefefe")
CAD_OUTLINE = QColor("#1b1b1b")
CAD_TEXT = QColor("#0f0f0f")

# Dimension system colors.
CAD_DIMENSION = QColor(OSDAG_BRAND_GREEN)
CAD_LABEL_BG = QColor(255, 255, 255, 230)

# Placeholder styling (when no section/geometry is available).
CAD_PLACEHOLDER_BORDER = QColor("#b7b7b7")
CAD_PLACEHOLDER_TEXT = QColor("#6f6f6f")
