from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
from typing import Optional, Tuple

# Import constants from common.py for consistency
from osdagbridge.core.utils.common import (
    DEFAULT_GIRDER_SPACING,
    DEFAULT_CRASH_BARRIER_WIDTH,
    DEFAULT_RAILING_WIDTH,
    MIN_FOOTPATH_WIDTH,
)

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
        o_min, o_max = self._deck_overhang_range(overall_width)
        
        # Parse inputs (0 means use default)
        spacing_input = girder_spacing if girder_spacing > 0 else DEFAULT_GIRDER_SPACING
        overhang_input = deck_overhang if deck_overhang > 0 else 0.5 * spacing_input  # spacing / 2
        girders_input = no_of_girders if no_of_girders >= 2 else 0
        
        # =====================================================================
        # Case: spacing changed -> n is FIXED, solve for overhang
        # =====================================================================
        if changed_field == "spacing":
            if girders_input < 2:
                raise ValueError("Number of girders must be at least 2")
            
            n = girders_input
            spacing_use = self._clamp(spacing_input, *spacing_bounds)
            # overhang = (width - (n - 1) * spacing) / 2
            overhang_use = (overall_width - (n - 1) * spacing_use) / 2.0
            
            if overhang_use < o_min - 1e-6:
                raise ValueError(
                    f"Spacing {spacing_use:.2f}m too large for {n} girders. "
                    f"Overhang would be {overhang_use:.2f}m (negative)."
                )
            overhang_use = self._clamp(overhang_use, o_min, o_max)
        
        # =====================================================================
        # Case: overhang changed -> n is FIXED, solve for spacing
        # =====================================================================
        elif changed_field == "overhang":
            if girders_input < 2:
                raise ValueError("Number of girders must be at least 2")
            
            # Check if overhang is within valid range
            if overhang_input < o_min - 1e-6 or overhang_input > o_max + 1e-6:
                raise ValueError(
                    f"Deck overhang must be between {o_min:.2f}m and {o_max:.2f}m. "
                    f"You entered: {overhang_input:.2f}m"
                )
            
            n = girders_input
            overhang_use = self._clamp(overhang_input, o_min, o_max)
            # spacing = (width - 2 * overhang) / (n - 1)
            spacing_use = (overall_width - 2 * overhang_use) / (n - 1)
            
            if spacing_use < spacing_bounds[0] - 1e-6:
                raise ValueError(
                    f"Overhang {overhang_use:.2f}m too large for {n} girders. "
                    f"Spacing would be {spacing_use:.2f}m (below minimum {spacing_bounds[0]:.2f}m)."
                )
            spacing_use = self._clamp(spacing_use, *spacing_bounds)
        
        # =====================================================================
        # Case: girders changed -> compute spacing and overhang where overhang = spacing / 2
        # From width = (n-1)*spacing + 2*overhang and overhang = spacing/2:
        # width = (n-1)*spacing + spacing = n*spacing => spacing = width/n
        # =====================================================================
        elif changed_field == "girders":
            if girders_input < 2:
                raise ValueError("Number of girders must be at least 2")
            
            n = girders_input
            # spacing = overall_width / n (gives overhang = spacing / 2)
            spacing_use = overall_width / n
            spacing_use = self._clamp(round(spacing_use, 2), *spacing_bounds)
            overhang_use = (overall_width - (n - 1) * spacing_use) / 2.0
            
            # Check if overhang is within valid range
            if overhang_use < o_min - 1e-6 or overhang_use > o_max + 1e-6:
                raise ValueError(
                    f"Cannot satisfy constraints with {n} girders. "
                    f"Overhang would be {overhang_use:.2f}m."
                )
            overhang_use = self._clamp(overhang_use, o_min, o_max)
        
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
        min_d, max_d = self.get_preliminary_depth_bounds(span)
        
        if user_value is not None:
            return max(min_d, min(max_d, user_value))
        
        return span / DEFAULT_DEPTH_SPAN_RATIO
    
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
            b_f = B_top if B_top > 0 else 0.3 * D  # Eq. 3.2
            t_f = t_f_top if t_f_top > 0 else b_f / 24.0  # Eq. 3.3
            d_web = D - 2 * t_f  # Eq. 3.4
            tw = t_w if t_w > 0 else d_web / 200.0  # Eq. 3.5
            
            # Area (m²)
            A = (2 * b_f * t_f) + (d_web * tw)
            
            # Mass (kg/m) - density 7850 kg/m³
            M = 7850 * A
            
            # Second moment of area about Z-axis (m⁴)
            I_z = (tw * d_web**3 / 12) + (b_f * t_f**3 / 6) + (b_f * t_f * ((D - t_f) / 2)**2) * 2
            
            # Second moment of area about Y-axis (m⁴)
            I_y = (d_web * tw**3 / 12) + (2 * t_f * b_f**3 / 12)
            
            # Radius of gyration (m)
            r_z = sqrt(I_z / A)
            r_y = sqrt(I_y / A)
            
            # Elastic section modulus (m³)
            Z_ez = I_z / (D / 2)
            Z_ey = I_y / (b_f / 2)
            
            # Plastic section modulus (m³)
            Z_pz = (b_f * t_f * (D - t_f)) + (tw * d_web**2 / 4)
            Z_py = (2 * t_f * b_f**2 / 4) + (d_web * tw**2 / 4)
            
            # Torsion constant (m⁴)
            I_t = (2 * b_f * t_f**3 / 3) + (d_web * tw**3 / 3)
            
            # Warping constant (m⁶)
            h = D - t_f  # distance between flange centroids
            I_w = (t_f * b_f**3 * h**2) / 24
            
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
            bf_top = B_top if B_top > 0 else 0.3 * D
            bf_bot = B_bot if B_bot > 0 else 0.35 * D
            tf_top = t_f_top if t_f_top > 0 else bf_top / 24.0
            tf_bot = t_f_bot if t_f_bot > 0 else bf_bot / 24.0
            d_web = D - tf_top - tf_bot
            tw = t_w if t_w > 0 else d_web / 200.0
            
            # Area (m²)
            A = (bf_top * tf_top) + (bf_bot * tf_bot) + (d_web * tw)
            
            # Mass (kg/m)
            M = 7850 * A
            
            # Centroid from bottom (m)
            A_top = bf_top * tf_top
            A_bot = bf_bot * tf_bot
            A_web = d_web * tw
            y_top = D - tf_top / 2
            y_bot = tf_bot / 2
            y_web = tf_bot + d_web / 2
            y_c = (A_top * y_top + A_bot * y_bot + A_web * y_web) / A
            
            # Second moment of area about Z-axis (m⁴)
            I_top = (bf_top * tf_top**3) / 12 + A_top * (y_top - y_c)**2
            I_bot = (bf_bot * tf_bot**3) / 12 + A_bot * (y_c - y_bot)**2
            I_web = (tw * d_web**3) / 12 + A_web * (y_c - y_web)**2
            I_z = I_top + I_bot + I_web
            
            # Second moment of area about Y-axis (m⁴)
            I_y = (tf_top * bf_top**3 / 12) + (tf_bot * bf_bot**3 / 12) + (d_web * tw**3 / 12)
            
            # Radius of gyration (m)
            r_z = sqrt(I_z / A)
            r_y = sqrt(I_y / A)
            
            # Elastic section modulus (m³) - min of top/bottom
            Z_ez_top = I_z / (D - y_c)
            Z_ez_bot = I_z / y_c
            Z_ez = min(Z_ez_top, Z_ez_bot)
            
            B_max = max(bf_top, bf_bot)
            Z_ey = (I_y * 2) / B_max
            
            # Plastic section modulus about Z (m³)
            half_A = A / 2
            # Find plastic neutral axis
            if A_bot >= half_A:
                y_pna = half_A / bf_bot
            elif A_bot + A_web >= half_A:
                y_pna = tf_bot + (half_A - A_bot) / tw
            else:
                y_pna = D - (A - half_A) / bf_top
            
            # Plastic modulus when PNA is in web
            if y_pna >= tf_bot and y_pna <= D - tf_top:
                Z_pz = (
                    bf_bot * y_pna**2 - 
                    (bf_bot - tw) * max(0, y_pna - tf_bot)**2 + 
                    bf_top * (D - y_pna)**2 - 
                    (bf_top - tw) * max(0, D - tf_top - y_pna)**2
                ) / 2
            else:
                Z_pz = A_top * abs(D - tf_top/2 - D/2) + A_bot * abs(D/2 - tf_bot/2) + A_web * abs(D/2 - y_web)
            
            # Plastic section modulus about Y (m³)
            Z_py = (tf_top * bf_top**2 / 4) + (tf_bot * bf_bot**2 / 4) + (d_web * tw**2 / 4)
            
            # Torsion constant (m⁴)
            h = D - (tf_top + tf_bot) / 2
            I_t = (bf_top * tf_top**3 + bf_bot * tf_bot**3 + h * tw**3) / 3
            
            # Warping constant (m⁶)
            numerator = (h**2) * tf_top * tf_bot * (bf_top**3) * (bf_bot**3)
            denominator = 12 * (tf_top * bf_top**3 + tf_bot * bf_bot**3)
            I_w = numerator / denominator if denominator != 0 else 0
            
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


# Legacy function for backward compatibility
def preliminary_sizing(dto):
    """Legacy stub - use BridgeConfigurationSolver instead."""
    return {"name": dto.name}
