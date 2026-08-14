from __future__ import annotations
from dataclasses import dataclass
from math import ceil, sqrt
from typing import Optional, Tuple

# Import constants from common.py for consistency
from osdagbridge.core.utils.common import (
    DEFAULT_GIRDER_SPACING,
    DEFAULT_CRASH_BARRIER_WIDTH,
    DEFAULT_RAILING_WIDTH,
    MIN_FOOTPATH_WIDTH,
    KEY_COMP_N,
    KEY_COMP_AC_TRANS_MM2,
    KEY_COMP_Y_FROM_BOT,
    KEY_COMP_Y_TOP,
    KEY_COMP_Y_BOT,
    KEY_COMP_I,
    KEY_COMP_S_TOP,
    KEY_COMP_S_BOT,
    KEY_MP_GIRDER_MASS,
    KEY_MP_GIRDER_SECTIONAL_AREA,
    KEY_MP_GIRDER_SECTIONAL_IZ,
    KEY_MP_GIRDER_SECTIONAL_IY,
    KEY_MP_GIRDER_RADIUS_GYRATION_Z,
    KEY_MP_GIRDER_RADIUS_GYRATION_Y,
    KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ,
    KEY_MP_GIRDER_ELASTIC_MODULUS_ZY,
    KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ,
    KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY,
    KEY_MP_GIRDER_TORSION_CONSTANT_IT,
    KEY_MP_GIRDER_WARPING_CONSTANT_IW,
    KEY_MP_GIRDER_CENTROID_YCG,
    KEY_MP_GIRDER_WEB_DEPTH,
    KEY_MP_GIRDER_FLANGE_AREA_TOP,
    KEY_MP_GIRDER_FLANGE_AREA_BOT,
    KEY_MP_GIRDER_WEB_AREA,
)

STEEL_DENSITY_KG_M3 = 7850.0  # IRC 24 / IS 2062 structural-steel density

# Import IRC 5:2015 for footpath width per Clause 104.3.6
from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015

# Import existing functions from bridge_geometry.py (Point 1 and validation)
from osdagbridge.core.bridge_types.plate_girder.bridge_geometry import (
    CrossSectionLayout,
)

# Default values per IRC 5 and RDSO standard practice
DEFAULT_DECK_OVERHANG_RATIO = 0.5  # overhang = spacing / 2 (i.e., 0.5 * spacing)
DEFAULT_DECK_THICKNESS = 200  # mm (RDSO composite-girder drawings: 200-250mm)
DEFAULT_FOOTPATH_WIDTH = 1.5  # m (IRC 5 Clause 104.3.6 minimum)

# Optimization bounds
MIN_GIRDER_SPACING = 1.0  # m (IRC:24 - not less than 1/20 of span for main girders)
MIN_DECK_THICKNESS = 150  # mm
MAX_DECK_THICKNESS = 250  # mm

# Section 3.1.2: Preliminary Girder Sizing Guidelines
# D_empirical = Span / 18, optimize between Span/15 to Span/25
DEFAULT_DEPTH_SPAN_RATIO = 18  # D = Span / 18
MIN_DEPTH_SPAN_RATIO = 25  # D_min = Span / 25 (shallower)
MAX_DEPTH_SPAN_RATIO = 15  # D_max = Span / 15 (deeper)
KEY_MAX_CAMBER_M = 4.0  # m

# Plate dimensions are ordered in 10 mm increments, so the empirical depth and
# flange widths are rounded up to that grid before any property is derived.
SIZE_INCREMENT_M = 0.010  # m

def ceil_to_size_increment(value_m: float) -> float:
    """Round a metre dimension up to the next 10 mm."""
    return ceil(round(value_m / SIZE_INCREMENT_M, 6)) * SIZE_INCREMENT_M

@dataclass
class BridgeLayoutResult:
    """Result of bridge layout calculation (Points 2-4)."""
    overall_width: float
    no_of_girders: int
    girder_spacing: float
    deck_overhang: float


class BridgeConfigurationSolver:
    """
    Core backend solver for bridge configuration calculations.
    
    Implements the 6 configuration points from section 3.1.1:
    1. Calculate Overall Bridge Width
    2. Girder Spacing (optimize between 1m and width - flange_width)
    3. Deck Overhang Width (default = spacing / 2)
    4. Calculate No. of Girders from equation
    5. Deck Thickness (150-250mm)
    6. Footpath Width (IRC 5 Clause 104.3.6)
    
    Constraint solving logic:
    - Number of girders is user-specified and FIXED during adjustments
    - When spacing changes: overhang adjusts to satisfy equation
    - When overhang changes: spacing adjusts to satisfy equation
    - Default relationship: overhang = spacing / 2
    """
    
    def __init__(
        self,
        carriageway_width: float,
        crash_barrier_width: float = DEFAULT_CRASH_BARRIER_WIDTH,
        footpath_width: float = 0.0,
        railing_width: float = 0.0,
        median_width: float = 0.0,
        n_footpaths: int = 0,
        flange_width: float = 0.0,  # max of top/bottom flange for spacing limit
    ):
        """
        Initialize solver with bridge component widths.
        
        Parameters:
        - carriageway_width : float - Width of the carriageway in meters.
        - crash_barrier_width : float - Width of each crash barrier in meters.
        - footpath_width : float - Width of each footpath in meters.
        - railing_width : float - Width of each railing in meters.
        - median_width : float - Width of median in meters.
        - n_footpaths : int - Number of footpaths (0, 1, or 2).
        - flange_width : float - Maximum flange width for spacing upper bound.
        """
        self.carriageway_width = carriageway_width
        self.crash_barrier_width = crash_barrier_width
        self.footpath_width = footpath_width if footpath_width > 0 else 0.0
        self.railing_width = railing_width
        self.median_width = median_width
        self.n_footpaths = n_footpaths
        self.flange_width = flange_width
    
    # =========================================================================
    # Point 1: Calculate Overall Bridge Width
    # Uses CrossSectionLayout.total_width from bridge_geometry.py
    # =========================================================================
    def calculate_overall_bridge_width(self) -> float:
        """
        Calculate overall bridge width from component widths.
        
        Delegates to CrossSectionLayout.total_width from bridge_geometry.py.
        
        Formula:
            OverallBridgeWidth = CarriagewayWidth + 2 * CrashBarrierWidth
                               + No.ofFootpath * FootpathWidth
                               + No.ofFootpath * RailingWidth + MedianWidth
        
        Returns
        -------
        float
            Overall bridge width in meters.
        """
        layout = CrossSectionLayout(
            carriageway_width=self.carriageway_width,
            crash_barrier_width=self.crash_barrier_width,
            footpath_width=self.footpath_width,
            railing_width=self.railing_width,
            median_width=self.median_width,
            n_footpaths=self.n_footpaths,
        )
        return layout.total_width
    
    def verify_bridge_width(
        self,
        no_of_girders: int,
        girder_spacing: float,
        deck_overhang: float,
        tol: float = 1e-6,
    ) -> bool:
        """
        Verify that layout parameters satisfy the width equation.
        
        Calls CrossSectionLayout.verify_bridge_width() from bridge_geometry.py.
        
        Formula:
            OverallBridgeWidth = (n - 1) * spacing + 2 * overhang
        
        Returns
        -------
        bool
            True if layout is valid.
        
        Raises
        ------
        ValueError
            If the computed width does not match layout width.
        """
        layout = CrossSectionLayout(
            carriageway_width=self.carriageway_width,
            crash_barrier_width=self.crash_barrier_width,
            railing_width=self.railing_width,
            footpath_width=self.footpath_width,
            median_width=self.median_width,
            n_footpaths=self.n_footpaths,
        )
        return layout.verify_bridge_width(
            num_long_grid=no_of_girders,
            ext_to_int_dist=girder_spacing,
            edge_beam_dist=deck_overhang,
            tol=tol,
        )
    
    # =========================================================================
    # Points 2-4: Girder Layout Solving (Spacing, Overhang, No. of Girders)
    # All constraint logic consolidated in _solve_layout
    # =========================================================================
    
    def _spacing_bounds(self, overall_width):
        """Get spacing bounds [min, max] for given overall width."""
        min_spacing = MIN_GIRDER_SPACING
        max_spacing = max(min_spacing, overall_width - self.flange_width)
        return min_spacing, max_spacing
    
    def _deck_overhang_range(self, overall_width):
        """Get overhang bounds [min, max] for given overall width."""
        min_overhang = 0.0
        max_overhang = overall_width / 2.0
        return min_overhang, max_overhang
    
    def _clamp(self, value, lo, hi):
        """Clamp value to [lo, hi] range."""
        return max(lo, min(hi, value))
    
    def _solve_layout(
        self,
        *,
        no_of_girders: int = 0,
        girder_spacing: float = 0.0,
        deck_overhang: float = 0.0,
        changed_field: str,
    ) -> BridgeLayoutResult:
        """
        Solve complete bridge layout configuration (Points 2-4).
        
        Constraint logic:
        - Number of girders is FIXED after user sets it
        - When spacing changes: overhang adjusts to satisfy width equation
        - When overhang changes: spacing adjusts to satisfy width equation
        
        Width equation: OverallBridgeWidth = (n - 1) * spacing + 2 * overhang
        
        Parameters
        ----------
        no_of_girders : int
            User-specified number of girders. Must be >= 2.
        girder_spacing : float
            User-specified girder spacing in meters.
        deck_overhang : float
            User-specified deck overhang in meters.
        changed_field : str
            Which field was changed: "spacing", "overhang", or "girders".
        
        Returns
        -------
        BridgeLayoutResult
            Complete layout configuration (overall_width, no_of_girders, girder_spacing, deck_overhang).
        """
        # Validate changed_field
        if changed_field not in ("spacing", "overhang", "girders"):
            raise ValueError(f"changed_field must be 'spacing', 'overhang', or 'girders', got '{changed_field}'")
        
        # Get overall bridge width
        overall_width = self.calculate_overall_bridge_width()
        if overall_width <= 0:
            raise ValueError("Overall bridge width must be positive.")
        
        # Get bounds
        spacing_bounds = self._spacing_bounds(overall_width)
        
        # Parse inputs (0 means use default)
        spacing_input = girder_spacing if girder_spacing > 0 else DEFAULT_GIRDER_SPACING
        overhang_input = deck_overhang if deck_overhang > 0 else 0.5 * spacing_input  # spacing / 2
        girders_input = no_of_girders if no_of_girders >= 2 else 0
        
        # =====================================================================
        # Case: spacing changed → n fixed, derive overhang.
        # (n-1)*spacing + 2*overhang = overall_width
        # =====================================================================
        if changed_field == "spacing":
            if girders_input < 2:
                raise ValueError("Number of girders must be at least 2.")
            n = girders_input
            spacing_use = spacing_input
            overhang_use = (overall_width - (n - 1) * spacing_use) / 2.0
            if overhang_use < 0:
                raise ValueError(
                    f"Spacing {spacing_use:.3f} m is too large for {n} girders "
                    f"(overhang = {overhang_use:.3f} m). Reduce spacing or number of girders."
                )

        # =====================================================================
        # Case: overhang changed → n fixed, derive spacing.
        # (n-1)*spacing + 2*overhang = overall_width
        # =====================================================================
        elif changed_field == "overhang":
            if girders_input < 2:
                raise ValueError("Number of girders must be at least 2.")
            n = girders_input
            overhang_use = overhang_input
            spacing_use = (overall_width - 2 * overhang_use) / (n - 1)
            if spacing_use < spacing_bounds[0]:
                raise ValueError(
                    f"Overhang {overhang_use:.3f} m is too large for {n} girders "
                    f"(spacing = {spacing_use:.3f} m, min = {spacing_bounds[0]:.2f} m)."
                )

        # =====================================================================
        # Case: girders changed → overhang = spacing / 2.
        # n*spacing = overall_width  →  spacing = overall_width / n
        # overhang  = spacing / 2
        # =====================================================================
        elif changed_field == "girders":
            if girders_input < 2:
                raise ValueError("Number of girders must be at least 2.")
            n = girders_input
            spacing_use = overall_width / n
            overhang_use = spacing_use / 2
            if spacing_use < spacing_bounds[0]:
                raise ValueError(
                    f"{n} girders requires spacing = {spacing_use:.3f} m, "
                    f"which is below the minimum ({spacing_bounds[0]:.2f} m)."
                )
        
        # Build result
        result = BridgeLayoutResult(
            overall_width=overall_width,
            no_of_girders=n,
            girder_spacing=round(spacing_use, 4),
            deck_overhang=round(overhang_use, 4),
        )
        
        # Verify using CrossSectionLayout.verify_bridge_width (with tolerance for rounding)
        self.verify_bridge_width(
            no_of_girders=result.no_of_girders,
            girder_spacing=result.girder_spacing,
            deck_overhang=result.deck_overhang,
            tol=1e-3,  # Larger tolerance due to rounding
        )
        
        return result
    
    # =========================================================================
    # Point 5: Deck Thickness
    # =========================================================================
    def get_deck_thickness(self, user_value: Optional[float] = None) -> float:
        """
        Get deck thickness with defaults and bounds.
        
        Default: 200mm. Range: [150mm, 250mm].
        """
        if user_value is None:
            return DEFAULT_DECK_THICKNESS
        return max(MIN_DECK_THICKNESS, min(MAX_DECK_THICKNESS, user_value))
    
    # =========================================================================
    # Point 6: Footpath Width (IRC 5:2015 Clause 104.3.6)
    # =========================================================================
    def get_footpath_width(self, user_value: float = 0.0, footpath: str = "Both Sides") -> float:
        """
        Get footpath width with validation per IRC 5:2015 Clause 104.3.6.
        
        Uses IRC5_2015.cl_104_3_6_footpath_width to validate.
        Minimum clear width: 1.5m when footpath is provided.
        """
        # Get IRC 5:2015 requirement
        irc_result = IRC5_2015.cl_104_3_6_footpath_width(footpath, user_value)
        min_width = irc_result["required_min_clear_width"]  # 1.5m
        
        if user_value <= 0 or user_value < min_width:
            return min_width
        return user_value
    
    # =========================================================================
    # Section 3.1.2: Preliminary Girder Depth
    # =========================================================================
    def get_preliminary_depth_bounds(self, span: float) -> Tuple[float, float]:
        """
        Get valid range for preliminary girder depth.
        
        Range: [Span/25, Span/15] (shallower to deeper)
        
        Parameters
        ----------
        span : float
            Bridge span in meters.
        
        Returns
        -------
        Tuple[float, float]
            (min_depth, max_depth) in meters.
        """
        min_depth = span / MIN_DEPTH_SPAN_RATIO  # Span/25 (shallower)
        max_depth = span / MAX_DEPTH_SPAN_RATIO  # Span/15 (deeper)
        return min_depth, max_depth
    
    def compute_preliminary_depth(
        self,
        span: float,
        user_value: Optional[float] = None,
    ) -> float:
        """
        Compute preliminary depth of girder section.
        
        For highway bridges: D_empirical = Span / 18
        Optimization range: Span/25 to Span/15
        
        Parameters
        ----------
        span : float
            Bridge span in meters.
        user_value : float, optional
            User-specified depth in meters.
        
        Returns
        -------
        float
            Preliminary girder depth in meters.
        """
        if user_value is not None:
            return user_value
        return ceil_to_size_increment(span / DEFAULT_DEPTH_SPAN_RATIO)

    # =========================================================================
    # Section 3.2: Section Properties Based on D_empirical
    # =========================================================================
    def compute_section_properties(
        self,
        *,
        span: float,
        symmetry: str = "Girder Symmetric",
        user_depth: float = 0.0,
        B_top: float = 0.0,
        B_bot: float = 0.0,
        t_f_top: float = 0.0,
        t_f_bot: float = 0.0,
        t_w: float = 0.0,
    ) -> dict:
        """
        Compute all section properties for a plate girder.
        
        For Type="Welded":
        - Symmetry="Girder Symmetric" -> symmetric calculations (same top/bottom)
        - Symmetry="Girder Unsymmetric" -> unsymmetric calculations (different top/bottom)
        
        All dimensions and outputs in METERS.
        
        Parameters
        ----------
        span : float
            Bridge span in meters (used for default D calculation).
        symmetry : str
            "Girder Symmetric" or "Girder Unsymmetric".
        user_depth : float, optional
            User-specified total section depth D in meters.
        B_top, B_bot : float, optional
            Flange widths in meters.
        t_f_top, t_f_bot : float, optional
            Flange thicknesses in meters.
        t_w : float, optional
            Web thickness in meters.
        
        Returns
        -------
        dict
            All section properties in meters (m, m², m³, m⁴, m⁶).
        """
        
        # Step 1: Get preliminary depth D (m)
        D = self.compute_preliminary_depth(span, user_depth if user_depth > 0 else None)
        
        # Determine if symmetric or unsymmetric
        is_symmetric = symmetry.lower() in ("symmetric", "girder symmetric")
        
        if is_symmetric:
            # =========================================================
            # SYMMETRIC SECTION: B_top = B_bot, t_f_top = t_f_bot
            # =========================================================
            # Default dimensions based on D_empirical formulas
            b_f = B_top if B_top > 0 else ceil_to_size_increment(0.3 * D)  # Eq. 3.2
            t_f = t_f_top if t_f_top > 0 else b_f / 24.0  # Eq. 3.3
            d_web = D - 2 * t_f  # Eq. 3.4
            tw = t_w if t_w > 0 else d_web / 200.0  # Eq. 3.5

            # Strong-axis + area properties come from the shared equation source
            # (unit-agnostic; here everything is in metres). Symmetric section =
            # top flange equal to bottom flange.
            _p = steel_i_section_properties(
                D=D, bf_top=b_f, tf_top=t_f, bf_bot=b_f, tf_bot=t_f, tw=tw,
            )
            A = _p[KEY_MP_GIRDER_SECTIONAL_AREA]
            I_z = _p[KEY_MP_GIRDER_SECTIONAL_IZ]
            Z_ez = _p[KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ]
            Z_pz = _p[KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ]
            I_y = _p[KEY_MP_GIRDER_SECTIONAL_IY]
            r_z = _p[KEY_MP_GIRDER_RADIUS_GYRATION_Z]
            r_y = _p[KEY_MP_GIRDER_RADIUS_GYRATION_Y]
            Z_ey = _p[KEY_MP_GIRDER_ELASTIC_MODULUS_ZY]
            Z_py = _p[KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY]
            I_t = _p[KEY_MP_GIRDER_TORSION_CONSTANT_IT]
            I_w = _p[KEY_MP_GIRDER_WARPING_CONSTANT_IW]

            # Mass (kg/m) - density 7850 kg/m³
            M = STEEL_DENSITY_KG_M3 * A

            return {
                "symmetry": "Girder Symmetric",
                # Input dimensions (m)
                "D": round(D, 6),
                "B_top": round(b_f, 6),
                "B_bot": round(b_f, 6),
                "t_f_top": round(t_f, 6),
                "t_f_bot": round(t_f, 6),
                "t_w": round(tw, 6),
                "d_web": round(d_web, 6),
                # Section properties (m) - 12 properties
                "Mass": round(M, 4),  # kg/m
                "Area": round(A, 8),  # m²
                "I_z": round(I_z, 10),  # m⁴
                "I_y": round(I_y, 10),  # m⁴
                "r_z": round(r_z, 6),  # m
                "r_y": round(r_y, 6),  # m
                "Z_ez": round(Z_ez, 8),  # m³
                "Z_ey": round(Z_ey, 8),  # m³
                "Z_pz": round(Z_pz, 8),  # m³
                "Z_py": round(Z_py, 8),  # m³
                "I_t": round(I_t, 12),  # m⁴
                "I_w": round(I_w, 14),  # m⁶
            }
            
        else:
            # =========================================================
            # UNSYMMETRIC SECTION: Different top/bottom flanges
            # =========================================================
            bf_top = B_top if B_top > 0 else ceil_to_size_increment(0.3 * D)
            bf_bot = B_bot if B_bot > 0 else ceil_to_size_increment(0.35 * D)
            tf_top = t_f_top if t_f_top > 0 else bf_top / 24.0
            tf_bot = t_f_bot if t_f_bot > 0 else bf_bot / 24.0
            d_web = D - tf_top - tf_bot
            tw = t_w if t_w > 0 else d_web / 200.0

            # Strong-axis + area properties come from the shared equation source
            # (unit-agnostic; here everything is in metres).
            _p = steel_i_section_properties(
                D=D, bf_top=bf_top, tf_top=tf_top,
                bf_bot=bf_bot, tf_bot=tf_bot, tw=tw,
            )
            A = _p[KEY_MP_GIRDER_SECTIONAL_AREA]
            I_z = _p[KEY_MP_GIRDER_SECTIONAL_IZ]
            Z_ez = _p[KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ]
            Z_pz = _p[KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ]
            I_y = _p[KEY_MP_GIRDER_SECTIONAL_IY]
            r_z = _p[KEY_MP_GIRDER_RADIUS_GYRATION_Z]
            r_y = _p[KEY_MP_GIRDER_RADIUS_GYRATION_Y]
            Z_ey = _p[KEY_MP_GIRDER_ELASTIC_MODULUS_ZY]
            Z_py = _p[KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY]
            I_t = _p[KEY_MP_GIRDER_TORSION_CONSTANT_IT]
            I_w = _p[KEY_MP_GIRDER_WARPING_CONSTANT_IW]

            # Mass (kg/m)
            M = STEEL_DENSITY_KG_M3 * A

            return {
                "symmetry": "Girder Unsymmetric",
                # Input dimensions (m)
                "D": round(D, 6),
                "B_top": round(bf_top, 6),
                "B_bot": round(bf_bot, 6),
                "t_f_top": round(tf_top, 6),
                "t_f_bot": round(tf_bot, 6),
                "t_w": round(tw, 6),
                "d_web": round(d_web, 6),
                # Section properties (m) - 12 properties
                "Mass": round(M, 4),  # kg/m
                "Area": round(A, 8),  # m²
                "I_z": round(I_z, 10),  # m⁴
                "I_y": round(I_y, 10),  # m⁴
                "r_z": round(r_z, 6),  # m
                "r_y": round(r_y, 6),  # m
                "Z_ez": round(Z_ez, 8),  # m³
                "Z_ey": round(Z_ey, 8),  # m³
                "Z_pz": round(Z_pz, 8),  # m³
                "Z_py": round(Z_py, 8),  # m³
                "I_t": round(I_t, 12),  # m⁴
                "I_w": round(I_w, 14),  # m⁶
            }


def steel_i_section_properties(
    D: float,
    bf_top: float,
    tf_top: float,
    bf_bot: float,
    tf_bot: float,
    tw: float,
) -> dict:
    """Bare-steel geometric/section properties of a welded I-girder.

    Single source of the steel-section equations (area, centroid, second moment,
    elastic/plastic section moduli). Callers must *read* these values, not
    recompute them, so a future custom girder shape only needs its equations
    changed here.

    Unit-agnostic: pass a consistent unit set (the designer passes mm) and the
    outputs follow (mm, mm2, mm3, mm4). Coordinate origin at the bottom fibre,
    upward positive.
    """
    dw = D - tf_top - tf_bot
    Af_top = bf_top * tf_top
    Af_bot = bf_bot * tf_bot
    Aw = dw * tw
    A_steel = Af_top + Aw + Af_bot

    # Steel centroid measured from bottom fibre.
    y_b = tf_bot / 2.0
    y_w = tf_bot + dw / 2.0
    y_t = tf_bot + dw + tf_top / 2.0
    y_cg_from_bot = (Af_bot * y_b + Aw * y_w + Af_top * y_t) / A_steel

    # Second moment of area about the centroidal strong axis.
    yc = y_cg_from_bot
    Iz_steel = (
        bf_bot * tf_bot ** 3 / 12.0
        + Af_bot * (yc - y_b) ** 2
        + tw * dw ** 3 / 12.0
        + Aw * (yc - y_w) ** 2
        + bf_top * tf_top ** 3 / 12.0
        + Af_top * (yc - y_t) ** 2
    )

    # Plastic section modulus about the strong axis.
    half_area = A_steel / 2.0
    if Af_bot >= half_area:
        y_pna = half_area / bf_bot
    elif Af_bot + Aw >= half_area:
        y_pna = tf_bot + (half_area - Af_bot) / tw
    else:
        y_pna = tf_bot + dw + (half_area - Af_bot - Aw) / bf_top

    def _rect_moment(b, t, y_bot_of_rect):
        y_top = y_bot_of_rect + t
        if y_pna >= y_top:
            return b * t * (y_pna - (y_bot_of_rect + t / 2.0))
        elif y_pna <= y_bot_of_rect:
            return b * t * ((y_bot_of_rect + t / 2.0) - y_pna)
        else:
            t_below = y_pna - y_bot_of_rect
            t_above = y_top - y_pna
            return b * t_below * t_below / 2.0 + b * t_above * t_above / 2.0

    Zp_steel = (
        _rect_moment(bf_bot, tf_bot, 0.0)
        + _rect_moment(tw, dw, tf_bot)
        + _rect_moment(bf_top, tf_top, tf_bot + dw)
    )

    # Elastic section modulus about the strong axis (governing extreme fibre).
    Ze_steel = Iz_steel / max(yc, D - yc)

    # --- Weak (minor) axis, torsion and warping -----------------------------
    # Second moment of area about the weak axis.
    Iy_steel = (
        tf_top * bf_top ** 3 / 12.0
        + tf_bot * bf_bot ** 3 / 12.0
        + dw * tw ** 3 / 12.0
    )

    # Radii of gyration.
    rz_steel = sqrt(Iz_steel / A_steel)
    ry_steel = sqrt(Iy_steel / A_steel)

    # Weak-axis elastic section modulus (extreme fibre = widest flange).
    Zey_steel = Iy_steel / (max(bf_top, bf_bot) / 2.0)

    # Weak-axis plastic section modulus.
    Zpy_steel = (
        tf_top * bf_top ** 2 / 4.0
        + tf_bot * bf_bot ** 2 / 4.0
        + dw * tw ** 2 / 4.0
    )

    # St. Venant torsion constant of a thin open section: (1/3)·Sum(b·t^3).
    # The web contributes its clear depth dw (its actual plate length).
    It_steel = (bf_top * tf_top ** 3 + bf_bot * tf_bot ** 3 + dw * tw ** 3) / 3.0

    # Warping constant about the shear centre (h_f = distance between flange centroids).
    h_f = D - (tf_top + tf_bot) / 2.0
    _flange_iy = tf_top * bf_top ** 3 + tf_bot * bf_bot ** 3
    Iw_steel = (
        h_f ** 2 * tf_top * tf_bot * bf_top ** 3 * bf_bot ** 3
        / (12.0 * _flange_iy)
        if _flange_iy != 0 else 0.0
    )

    # Keyed output only — every value is addressed by its member-property key so
    # the whole pipeline speaks one vocabulary. Mass = density x area is only
    # meaningful when dimensions are in metres (kg/m). (The section designation is
    # a mm-formatted label, not a unit-agnostic number, so it is built by the
    # caller from its own dimensions, not here.)
    return {
        KEY_MP_GIRDER_SECTIONAL_AREA:      A_steel,
        KEY_MP_GIRDER_MASS:                STEEL_DENSITY_KG_M3 * A_steel,
        KEY_MP_GIRDER_SECTIONAL_IZ:        Iz_steel,
        KEY_MP_GIRDER_SECTIONAL_IY:        Iy_steel,
        KEY_MP_GIRDER_RADIUS_GYRATION_Z:   rz_steel,
        KEY_MP_GIRDER_RADIUS_GYRATION_Y:   ry_steel,
        KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ:  Ze_steel,
        KEY_MP_GIRDER_ELASTIC_MODULUS_ZY:  Zey_steel,
        KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ: Zp_steel,
        KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY: Zpy_steel,
        KEY_MP_GIRDER_TORSION_CONSTANT_IT: It_steel,
        KEY_MP_GIRDER_WARPING_CONSTANT_IW: Iw_steel,
        KEY_MP_GIRDER_CENTROID_YCG:        y_cg_from_bot,
        KEY_MP_GIRDER_WEB_DEPTH:           dw,
        KEY_MP_GIRDER_FLANGE_AREA_TOP:     Af_top,
        KEY_MP_GIRDER_FLANGE_AREA_BOT:     Af_bot,
        KEY_MP_GIRDER_WEB_AREA:            Aw,
    }


def composite_section_properties(
    beff_mm: float,
    ds_mm: float,
    h_haunch_mm: float,
    A_steel_mm2: float,
    Iz_steel_mm4: float,
    y_cg_from_bot_mm: float,
    D_steel_mm: float,
    n: float,
) -> dict:
    """
    Transformed composite section properties for a steel-concrete composite girder.

    Concrete area is converted to equivalent steel area by dividing by n = Es/Ecm.
    All dimensions in mm; coordinate origin at bottom of steel section (upward +ve).

    Returns I_comp_mm4, composite NA depths, section moduli, and transformed area.
    """
    Ac_trans  = beff_mm * ds_mm / n
    y_steel   = y_cg_from_bot_mm
    y_slab    = D_steel_mm + h_haunch_mm + ds_mm / 2.0
    A_total   = A_steel_mm2 + Ac_trans
    y_comp_bot = (A_steel_mm2 * y_steel + Ac_trans * y_slab) / A_total
    I_steel   = Iz_steel_mm4 + A_steel_mm2 * (y_comp_bot - y_steel) ** 2
    I_conc    = beff_mm * ds_mm ** 3 / (12.0 * n) + Ac_trans * (y_comp_bot - y_slab) ** 2
    I_comp    = I_steel + I_conc
    total_depth = D_steel_mm + h_haunch_mm + ds_mm
    y_top     = total_depth - y_comp_bot
    y_bot     = y_comp_bot
    return {
        KEY_COMP_N            : round(n, 3),
        KEY_COMP_AC_TRANS_MM2 : round(Ac_trans, 1),
        KEY_COMP_Y_FROM_BOT   : round(y_comp_bot, 3),
        KEY_COMP_Y_TOP        : round(y_top, 3),
        KEY_COMP_Y_BOT        : round(y_bot, 3),
        KEY_COMP_I            : round(I_comp, 0),
        KEY_COMP_S_TOP        : round(I_comp / y_top, 0),
        KEY_COMP_S_BOT        : round(I_comp / y_bot, 0),
    }


# Legacy function for backward compatibility
def preliminary_sizing(dto):
    """Legacy stub - use BridgeConfigurationSolver instead."""
    return {"name": dto.name}
