"""
Module for IRC 22:2014 bridge design clauses.

@author: Sweta Pal

"""

from osdag_core.utils.common.is800_2007 import IS800_2007 
from osdagbridge.core.utils.codes.keyfile import *
import math

class IRC22_2014:

    # 601.4 Material Strength and Partial Safety Factor (Clause 601.4)

    @staticmethod
    def cl_601_4_material_safety_factors():
        """
        IRC:22-2014 Clause 601.4
        Table 1: Material Safety Factors (γm)

        Returns:
            dict containing partial safety factors for:
                - Steel yield stress
                - Steel ultimate stress
                - Reinforcement
                - Shear concrete
                - Bolts & Rivets
                - Welds
                - Concrete (accidental)
                (Separate factors for ultimate limit & serviceability)
        """

        # values as per Table 1 IRC-22:2014
        gamma_m = {
            "structural_steel_yield": {"ULS": 1.10, "SLS": 1.00},
            "structural_steel_ultimate": {"ULS": 1.25, "SLS": 1.00},
            "steel_reinforcement_yield": {"ULS": 1.15, "SLS": 1.00},
            "shear_concrete": {"ULS": 1.25, "SLS": 1.00},
            "bolts_rivets_shear_tension": {"ULS": 1.25, "SLS": 1.00},
            "welds_shop": {"ULS": 1.25, "SLS": 1.00},
            "welds_field": {"ULS": 1.50, "SLS": 1.00},
            "concrete_basic_seismic": {"ULS": 1.50, "SLS": 1.00},
            "concrete_accidental": {"ULS": 1.20, "SLS": 1.00}
        }

        return gamma_m

    # 602 Material  |  Annex III (Properties of Structural Steel)

    @staticmethod
    def cl_602_annexIII_structural_steel_properties():
        """
        IRC:22-2014
        Clause 602 | Annex-III

        III.1 Structural Steel:
        Properties to be assumed for all grades of steel for design.

        Returns:
            dict containing fundamental steel properties:
                - Young's Modulus
                - Shear Modulus
                - Poisson's Ratio
                - Coefficient of Thermal Expansion
        """

        properties = {
            "E_MPa": E_STEEL_MPA,                 # Young's Modulus (MPa)
            "E_GPa": E_STEEL_MPA / 1000.0,        # Young's Modulus (GPa) - convenience
            "G_MPa": G_STEEL_MPA,                # Shear Modulus (MPa)
            "nu": POISSON_RATIO_STEEL,                     # Poisson's Ratio
            "coefficient_of_thermal_expansion": COTE_STEEL_PER_C  # per °C per unit length
        }

        return properties


    # 602 Material | Annex III (Concrete Properties)

    @staticmethod
    def cl_602_annexIII_concrete_properties(
        grade=None,
        aggregate_type="quartzite",
        is_structural=True
    ):
        """
        IRC:22-2014 Clause 602 | Annex-III | III.2 Concrete
        If structural concrete is used, minimum grade shall be M25.
        """

        agg_factor_map = {
            "quartzite": 1.0,
            "granite": 1.0,
            "limestone": 0.9,
            "sandstone": 0.7,
            "basalt": 1.2
        }
        factor = agg_factor_map.get(aggregate_type.lower(), 1.0)

        concrete = {
            "M15":  {"fck": 15, "fcy": 12, "fctm": 1.6, "Ec": 27},
            "M20":  {"fck": 20, "fcy": 16, "fctm": 1.9, "Ec": 29},
            "M25":  {"fck": 25, "fcy": 20, "fctm": 2.2, "Ec": 30},
            "M30":  {"fck": 30, "fcy": 24, "fctm": 2.8, "Ec": 31},
            "M35":  {"fck": 35, "fcy": 28, "fctm": 3.0, "Ec": 32},
            "M40":  {"fck": 40, "fcy": 32, "fctm": 3.3, "Ec": 33},
            "M45":  {"fck": 45, "fcy": 36, "fctm": 3.4, "Ec": 34},
            "M50":  {"fck": 50, "fcy": 40, "fctm": 3.5, "Ec": 35},
            "M55":  {"fck": 55, "fcy": 44, "fctm": 3.6, "Ec": 36},
            "M60":  {"fck": 60, "fcy": 48, "fctm": 3.7, "Ec": 37},
            "M65":  {"fck": 65, "fcy": 52, "fctm": 4.0, "Ec": 38},
            "M70":  {"fck": 70, "fcy": 56, "fctm": 4.4, "Ec": 38},
            "M75":  {"fck": 75, "fcy": 60, "fctm": 4.5, "Ec": 39},
            "M80":  {"fck": 80, "fcy": 64, "fctm": 4.7, "Ec": 40},
            "M85":  {"fck": 85, "fcy": 68, "fctm": 4.9, "Ec": 40},
            "M90":  {"fck": 90, "fcy": 72, "fctm": 5.0, "Ec": 41},
        }

        # Apply Aggregate Modulus Factor
        for g, props in concrete.items():
            props["Ec"] = round(props["Ec"] * factor, 2)

        #  If grade not asked, return full table
        if grade is None:
            return concrete

        grade = grade.upper()

        # Enforce minimum grade for structural concrete
        if is_structural:
            allowed = ["M25", "M30", "M35", "M40", "M45", "M50", "M55", "M60", "M65", "M70", "M75", "M80", "M85", "M90"]
            if grade not in allowed:
                grade = "M25"

        if grade not in concrete:
            raise ValueError(f"Invalid concrete grade: {grade}")

        return {
            "grade": grade,
            "aggregate_type": aggregate_type.lower(),
            "is_structural": is_structural,
            **concrete[grade]
        }


    # 602 Material | Annex III | III.3 Reinforcement Steel

    @staticmethod
    def cl_602_annexIII_reinforcement_steel_properties():
        """
        IRC:22-2014
        Clause 602 | Annex-III | III.3 Reinforcement Steel

        Reinforcing steel used in concrete construction shall conform to:
            IS:1786 - 2008 (High Strength Deformed Bars & Wires)

        Table covered: Mechanical Properties of High Strength Deformed Bars

        This function stores:
            fy  : characteristic yield strength (MPa)
            fu  : minimum ultimate tensile strength (MPa)
            elongation_min_percent : minimum elongation %

        And CALCULATES:
            fu_required = max((1 + p/100)*fy, fu)
            fu_by_fy_requirement = fu_required / fy
        """

        def _fu_ratio(fy, fu_min, percent_more_than_yield):
            """
            Calculate effective fu/fy requirement based on:
                fu >= (1+p)*fy  AND  fu >= fu_min
            """
            p = percent_more_than_yield / 100.0
            fu_required = max((1.0 + p) * fy, fu_min)
            ratio = fu_required / fy
            return round(fu_required, 2), round(ratio, 4)

        # Values exactly as per Table 3 (IS:1786-2008)
        # percent_more_than_yield corresponds to the "10%, 12%, 8%, ..." row in the table
        reinforcement_raw = {
            "Fe415":  {"fy": 415.0, "fu": 485.0, "elongation_min_percent": 14.5, "percent_more_than_yield": 10.0},
            "Fe415D": {"fy": 415.0, "fu": 500.0, "elongation_min_percent": 18.0, "percent_more_than_yield": 12.0},
            "Fe500":  {"fy": 500.0, "fu": 545.0, "elongation_min_percent": 12.0, "percent_more_than_yield": 8.0},
            "Fe500D": {"fy": 500.0, "fu": 565.0, "elongation_min_percent": 16.0, "percent_more_than_yield": 10.0},
            "Fe550":  {"fy": 550.0, "fu": 585.0, "elongation_min_percent": 10.0, "percent_more_than_yield": 6.0},
            "Fe550D": {"fy": 550.0, "fu": 600.0, "elongation_min_percent": 14.5, "percent_more_than_yield": 8.0},
            "Fe600":  {"fy": 600.0, "fu": 660.0, "elongation_min_percent": 10.0, "percent_more_than_yield": 6.0},
        }

        # Build final dictionary with calculated values
        reinforcement = {}

        for grade, props in reinforcement_raw.items():
            fy = props["fy"]
            fu_min = props["fu"]
            percent_more = props["percent_more_than_yield"]

            fu_required, ratio_required = _fu_ratio(fy, fu_min, percent_more)

            reinforcement[grade] = {
                "fy": fy,
                "fu": fu_min,
                "elongation_min_percent": props["elongation_min_percent"],

                # from Table condition
                "percent_more_than_yield": percent_more,

                # calculated outputs (requested improvement)
                "fu_required": fu_required,
                "fu_by_fy_requirement": ratio_required
            }

        return reinforcement


    # 603.2 Effective Width of Concrete Slab
    # 603.2.1 Simply Supported Girder (Pinned at Both Ends)

    # 603.2.1  Effective Width of Simply Supported Girder

    @staticmethod
    def cl_603_2_1_effective_width_simply_supported(Lo, beam_type="inner", B=None, B1=None, B2=None, B0=None):
        """
        IRC:22-2014 Clause 603.2.1
        Effective Width of Simply Supported Girder

        Inner beam:
            beff = min(Lo/4, (B1+B2)/2)
            if equal spacing (B1=B2=B): beff = min(Lo/4, B)

        Outer beam:
            beff = min(Lo/8, B1/2) + min(B0, Lo/8)
        """

        beam_type = beam_type.lower()

        if beam_type not in ["inner", "outer"]:
            raise ValueError("beam_type must be 'inner' or 'outer'")

        if Lo <= 0:
            raise ValueError("Lo must be positive")

        # ---------------- INNER BEAM ----------------
        if beam_type == "inner":
            if B is not None:
                # equal spacing case: B1=B2=B
                beff = min(Lo / 4.0, B)
                eq_used = "Eq 3.3 (equal spacing)"
            else:
                if B1 is None or B2 is None:
                    raise ValueError("For inner beam provide either B (equal spacing) OR both B1 and B2.")
                beff = min(Lo / 4.0, (B1 + B2) / 2.0)
                eq_used = "Eq 3.2 (general)"

        # ---------------- OUTER BEAM ----------------
            """# B0 = distance from edge beam to free edge of slab (X in IRC figure)"""
        else:
            if B1 is None or B0 is None:
                raise ValueError("For outer beam provide B1 and B0 (where X=B0).")

            beff = min(Lo / 8.0, B1 / 2.0) + min(B0, Lo / 8.0)
            eq_used = "Eq 3.4 (outer beam)"

        return {
            "beam_type": beam_type,
            "Lo_m": Lo,
            "beff_m": round(beff, 4),
            "equation_used": eq_used,
            "clause": "IRC 22:2014 - 603.2.1"
        }


    #table 2 -> Classification of steel cross-section
    @staticmethod
    def cl_603_check_steel_web_classification(
        depth_web_mm,
        tw_mm,
        fy_MPa,
        axial_force_N,
        load_type="Compression"
    ):
        """
        IRC:22-2014 Clause 603
        Web classification (Ref: IS800 Table 2)

        Returns:
            section_class : Plastic / Compact / Semi-Compact / Slender
        """

        checks = IS800_2007.Table2_web_OfI_H_box_section(
            depth=depth_web_mm,
            web_thickness=tw_mm,
            f_y=fy_MPa,
            axial_load=axial_force_N,
            load_type=load_type
        )

        ratio = depth_web_mm / tw_mm
        eps = math.sqrt(250 / fy_MPa)

        if ratio <= 67*eps:
            section_class = "Plastic"
        elif ratio <= 83*eps:
            section_class = "Compact"
        elif ratio <= 124*eps:
            section_class = "Semi-Compact"
        else:
            section_class = "Slender"

        return {
            "section_class": section_class,
            "checks": checks,
            "clause": "IRC 22:2014 - 603 (Web Classification)"
        }

    
    @staticmethod
    def cl_602_table2_i_outstanding_compression_flange(
        width_mm,
        thickness_mm,
        fy_MPa,
        section_type=KEY_SECTION_FABRICATION[0]
    ):
        """
        IRC:22-2014 Clause 602 (Ref: IS800:2007 Table 2 (i))
        Outstanding element of compression flange.

        Returns:
            list: [section_class, ratio]
        """
        return IS800_2007.Table2_i(
            width=width_mm,
            thickness=thickness_mm,
            f_y=fy_MPa,
            section_type=section_type
        )

    @staticmethod
    def cl_602_table2_iii_web_classification(
        depth_mm,
        thickness_mm,
        fy_MPa,
        classification_type="Neutral axis at mid-depth"
    ):
        """
        IRC:22-2014 Clause 602 (Ref: IS800:2007 Table 2 (iii))
        Web of an I/H/Box section classification.

        Returns:
            str: section_class
        """
        return IS800_2007.Table2_iii(
            depth=depth_mm,
            thickness=thickness_mm,
            f_y=fy_MPa,
            classification_type=classification_type
        )


    @staticmethod
    def cl_603_3_1_positive_moment_capacity(
            fck,
            fy,
            beff,
            ds,
            As,
            Af,
            bf,
            tf,
            tw,
            dc,
            combination_type="basic",
            is_compact=True,
            beff_compact_limit=None,
            fabrication=KEY_SECTION_FABRICATION[0]  # default = rolled
        ):
        """
        IRC:22-2014
        Clause 603.3.1 + Annexure I (I.1)
        Positive Moment Resistance of Composite Beam
        """

        beff_used = beff
        beff_compact_limit = None
        beff_flange_limit = None
        beff_web_limit = None

        if not is_compact:

            eps = math.sqrt(250.0 / fy)
            fabrication = fabrication.lower()

            if fabrication == KEY_SECTION_FABRICATION[0]:      # rolled
                flange_compact_ratio = 10.5 * eps
                section_type = "Rolled"
            elif fabrication == KEY_SECTION_FABRICATION[1]:    # welded
                flange_compact_ratio = 9.4 * eps
                section_type = "Welded"
            else:
                raise ValueError(
                    f"Invalid fabrication type '{fabrication}'. "
                    f"Allowed: {KEY_SECTION_FABRICATION}"
                )

            IS800_2007.Table2_i(
                width=bf,
                thickness=tf,
                f_y=fy,
                section_type=section_type
            )

            beff_flange_limit = flange_compact_ratio * tf

            IS800_2007.Table2_iii(
                depth=ds,
                thickness=tw,
                f_y=fy,
                classification_type="Neutral axis at mid-depth"
            )

            web_compact_ratio = 105.0 * eps
            beff_web_limit = web_compact_ratio * tw

            beff_compact_limit = min(beff_flange_limit, beff_web_limit)
            beff_used = min(beff, beff_compact_limit)

            return {
                "beff_input": beff,
                "beff_used": round(beff_used, 3),
                "beff_compact_limit": round(beff_compact_limit, 3),
                "beff_flange_limit": round(beff_flange_limit, 3),
                "beff_web_limit": round(beff_web_limit, 3),
            }


# result = IRC22_2014.cl_603_3_3_1_buckling_resistance_moment(section_class="compact",Zp=6.5e6,Ze=5.8e6,fy=345,Iy=8.2e8,It=2.5e5,Iw=3.1e11,LLT=6000,section_type="rolled")
    @staticmethod
    def cl_603_3_3_1_buckling_resistance_moment(
        section_class,                 # plastic / compact / semi-compact
        Zp,                             # mm3
        Ze,                             # mm3
        fy,                             # MPa
        gamma_mo=GAMMA_M0_STEEL,
        support="KEY_DISP_SUPPORT1",

        Iy=None,                        # mm4
        It=None,                        # mm4
        Iw=None,                        # mm6
        LLT=None,                       # mm

        section_type=KEY_SECTION_FABRICATION[0],  # rolled / welded

        E=E_STEEL_MPA,                  # MPa
        G=G_STEEL_MPA                  # MPa
    ):
        """
        IRC:22-2014 Clause 603.3.3.1
        Annexure I: I.5 Buckling Resistance Moment (Construction Stage)

        Uses IS 800:2007 Clause 8.2.1.2
        """

        # ------------------ Validation ------------------
        if None in [Iy, It, Iw, LLT]:
            raise ValueError("Iy, It, Iw and LLT must be provided")

        section_class = section_class.lower()
        section_type = section_type.lower()

        if section_class not in KEY_SECTION_CLASS:
            raise ValueError(f"Invalid section_class. Allowed: {KEY_SECTION_CLASS}")

        if section_type not in KEY_SECTION_FABRICATION:
            raise ValueError(f"Invalid section_type. Allowed: {KEY_SECTION_FABRICATION}")

        # ------------------ Step 1: Mpl ------------------
        Mpl = IS800_2007.cl_8_2_1_2_design_bending_strength(
            section_class=section_class,
            Zp=Zp,
            Ze=Ze,
            fy=fy,
            gamma_mo=gamma_mo,
            support=support
        )  # Nmm

        if Mpl is None:
            raise ValueError("IS800 cl_8_2_1_2_design_bending_strength returned None")

        # ------------------ Step 2: βb ------------------
        if section_class in ["plastic", "compact"]:
            beta_b = 1.0
        elif section_class in ["semi-compact"]:
            beta_b = Ze / Zp
        else:
            raise ValueError("Buckling check not applicable for slender sections")

        # ------------------ Step 3: αLT ------------------
        alpha_LT = 0.21 if section_type == "rolled" else 0.49

        # ------------------ Step 4: Mcr ------------------
        term1 = (math.pi ** 2 * E * Iy) / (LLT ** 2)
        term2 = (G * It) + (math.pi ** 2 * E * Iw) / (LLT ** 2)
        Mcr = math.sqrt(term1 * term2)  # Nmm

        # ------------------ Step 5: λLT ------------------
        lambda_LT = math.sqrt(beta_b * (Zp * fy) / Mcr)

        # ------------------ Step 6: χLT ------------------
        if lambda_LT <= 0.4:
            chi_LT = 1.0
        else:
            phi_LT = 0.5 * (1 + alpha_LT * (lambda_LT - 0.2) + lambda_LT ** 2)
            chi_LT = 1.0 / (phi_LT + math.sqrt(phi_LT ** 2 - lambda_LT ** 2))
            chi_LT = min(chi_LT, 1.0)

        # ------------------ Step 7: Buckling Moment ------------------
        Mpl_buck = chi_LT * Mpl

        return {
            "section_class": section_class,
            "section_type": section_type,
            "beta_b": round(beta_b, 4),
            "alpha_LT": round(alpha_LT, 4),
            "lambda_LT": round(lambda_LT, 4),
            "chi_LT": round(chi_LT, 4),
            "Mcr_kNm": round(Mcr / 1e6, 3),
            "Mpl_kNm": round(Mpl / 1e6, 3),
            "Mpl_buckling_kNm": round(Mpl_buck / 1e6, 3),
            "clause": "IRC 22:2014 - 603.3.3.1 Annex I (I.5) + IS 800:2007 8.2.1.2"
        }


    # 603.3.3.2  VERTICAL SHEAR :  (1) PLASTIC SHEAR RESISTANCE

    @staticmethod
    def cl_603_3_3_2_plastic_shear_resistance(
        section_type,
        fyw,
        fabrication=KEY_SECTION_FABRICATION[0],     
        h=None,                   
        d=None,                   # web depth for welded/plate girder I-major
        tw=None,                  # web thickness
        bf=None,                  # flange width for I-minor
        tf=None                   # flange thickness for I-minor
    ):
        """
        IRC:22-2014
        Clause 603.3.3.2 (1) Plastic Shear Resistance
        (Reference: IS 800:2007 Clause 8.4.1 for shear area)

        Vn = Vp = (Av * fyw) / √3
        Vd = Vn / γm0
        γm0 = 1.10

        section_type:
            - "i_major" : major axis bending of I section
            - "i_minor" : minor axis bending of I section

        fabrication:
            - "rolled" : Av = h * tw
            - "welded" : Av = d * tw   (plate girder)

        For i_minor:
            Av = 2 * bf * tf

        @author: Sweta Pal
        """


        gamma_m0 = GAMMA_M0_STEEL
        section_type = section_type.lower()
        fabrication = fabrication.lower()

        # SHEAR AREA Av

        if section_type == KEY_SECTION_TYPE[0]:
            if fabrication == KEY_SECTION_FABRICATION[0]:
                if h is None or tw is None:
                    raise ValueError("For rolled i_major section: h and tw are required")
                Av = h * tw

            elif fabrication == KEY_SECTION_FABRICATION[1]:
                if d is None or tw is None:
                    raise ValueError("For welded i_major section: d and tw are required")
                Av = d * tw

            else:
                raise ValueError("fabrication must be 'rolled' or 'welded'")

        elif section_type == KEY_SECTION_TYPE[1]:
            #  consistent symbols as per IRC22/IS800
            if bf is None or tf is None:
                raise ValueError("For i_minor section: bf and tf are required")
            Av = 2.0 * bf * tf

        else:
            raise ValueError("section_type must be 'i_major' or 'i_minor'")

        # NOMINAL + DESIGN SHEAR

        Vn_N = (Av * fyw) / math.sqrt(3)      # N
        Vd_N = Vn_N / gamma_m0          # N

        return {
            "section_type": section_type,
            "fabrication": fabrication,
            "Av_mm2": round(Av, 3),
            "fyw_MPa": fyw,
            "Vn_kN": round(Vn_N / 1000.0, 3),
            "Vd_kN": round(Vd_N / 1000.0, 3),
            "gamma_m0": gamma_m0,
            "clause": "IRC 22:2014 - 603.3.3.2 (1) Plastic Shear Resistance (Eq 3.5) + IS800 8.4.1"
        }



    # 603.3.3.2 (2)(a)
    # Shear Buckling Resistance – Simple Post-Critical Method

    @staticmethod
    def cl_603_3_3_2_shear_buckling_post_critical(
        Av_mm2,
        fyw_MPa,
        d_mm,
        tw_mm,
        c_mm=None,
        stiffeners_at_support_only=True,
        mu=0.3
    ):
        """
        IRC:22-2014 Clause 603.3.3.2 (2)(a)
        Simple Post-Critical Shear Buckling Method
        Uses IS 800:2007 Clause 8.4.2.2(a)

        @author: Sweta Pal
        """

        import math
        E_MPa = E_STEEL_MPA

        # 1) Get shear buckling coefficient Kv from IS800
        support = "only support" if stiffeners_at_support_only else "intermediate"

        Kv = IS800_2007.cl_8_4_2_2_K_v_Simple_postcritical(
            support=support,
            c=c_mm if c_mm is not None else 0,
            d=d_mm
        )

        # 2) Elastic shear buckling stress τ_cr
        tau_cr = (Kv * math.pi**2 * E_MPa) / (12 * (1 - mu**2)) * (tw_mm / d_mm)**2

        # 3) Slenderness parameter λ_w
        lambda_w = math.sqrt(fyw_MPa / (math.sqrt(3) * tau_cr))

        # 4) Post-critical shear stress τ_b
        if lambda_w <= 1.2:
            tau_b = fyw_MPa / math.sqrt(3)
        else:
            tau_b = (1.2 / lambda_w) * (fyw_MPa / math.sqrt(3))

        # 5) Design shear resistance
        Vrd_N = Av_mm2 * tau_b

        return {
            "Kv": round(Kv, 3),
            "tau_cr_MPa": round(tau_cr, 3),
            "lambda_w": round(lambda_w, 3),
            "tau_b_MPa": round(tau_b, 3),
            "Vrd_kN": round(Vrd_N / 1e3, 3),
            "clause": "IRC 22:2014 - 603.3.3.2 (IS 800:2007 8.4.2.2a)"
        }


    @staticmethod
    def cl_603_3_3_2_tension_field_method(
        c_mm,
        d_mm,
        tw_mm,
        fyw_MPa,
        bf_mm,
        tf_mm,
        fyf_MPa,
        Nf_N,          
        Av_mm2,
        tau_b_MPa,
        Vp_kN,
    ):
        """
        IRC:22-2014 Clause 603.3.3.2 (2)(b)
        Tension Field Method

        Note:
        Uses IS 800:2007 Clause 8.4.2.2(b)
        """

        gamma_m0=GAMMA_M0_STEEL
        # IS800 function returns V_tf in kN (as per your shared code)
        phi, Mfr, s, wtf, psi, fv, Vtf = IS800_2007.cl_8_4_2_2_TensionField(
            c=c_mm,
            d=d_mm,
            tw=tw_mm,
            fyw=fyw_MPa,
            bf=bf_mm,
            tf=tf_mm,
            fyf=fyf_MPa,
            Nf=Nf_N,
            gamma_mo=gamma_m0,
            A_v=Av_mm2,
            tau_b=tau_b_MPa,
            V_p=Vp_kN
        )

        return {
            "phi_deg": round(phi, 3),
            "Mfr_Nmm": round(Mfr, 3),
            "s_mm": round(s, 3),
            "wtf_mm": round(wtf, 3),
            "psi_MPa": round(psi, 3),
            "fv_MPa": round(fv, 3),
            "Vtf_kN": round(Vtf, 3),
            "clause": "IRC 22:2014 - 603.3.3.2 (2)(b) | Uses IS 800:2007 8.4.2.2(b)"
        }


    @staticmethod
    def cl_603_3_3_3_reduced_bending_under_high_shear(
        Md_kNm,          # bending resistance from 603.3.3.1
        Mfd_kNm,         # plastic strength excluding shear area
        V_kN,            # factored shear force
        Vd_kN            # design shear strength
    ):
        """
        IRC:22-2014 Clause 603.3.3.3
        Reduction in bending resistance under high shear force
        (Ref: IS 800:2007, 9.2.2(a),(b))
        """

        if Vd_kN <= 0:
            raise ValueError("Vd_kN must be > 0")

        # No reduction condition
        if V_kN <= 0.6 * Vd_kN:
            return {
                "Md_kNm": round(Md_kNm, 3),
                "Mdv_kNm": round(Md_kNm, 3),
                "beta": 0.0,
                "is_reduction_required": False,
                "clause": "IRC 22:2014 - 603.3.3.3"
            }

        # Eq. 3.13
        beta = (2 * V_kN / Vd_kN - 1) ** 2
        beta = min(beta, 1.0)

        Mdv_kNm = Md_kNm - beta * (Md_kNm - Mfd_kNm)

        return {
            "Md_kNm": round(Md_kNm, 3),
            "Mfd_kNm": round(Mfd_kNm, 3),
            "Mdv_kNm": round(Mdv_kNm, 3),
            "beta": round(beta, 4),
            "is_reduction_required": True,
            "clause": "IRC 22:2014 - 603.3.3.3"
        }



    # 604.3 Stresses and Deflection — Modular Ratio
    @staticmethod
    def cl_604_3_modular_ratio(
            fck=None,
            concrete_grade=None,
            Ecm=None,          # MPa (Concrete modulus at 28 days) — from Annex III Table III.1
            Eci=None,          # MPa (Concrete modulus before 28 days)
            Kc=0.5,            # creep factor (given in clause)
            aggregate_type="quartzite"
    ):
        
        """
        IRC:22-2014
        Clause 604.3 - Stresses and Deflection
        Modular Ratio (m)

        Clause states:
            Es = 2.0 x 10^5 N/mm2 
            Ecm = modulus of cast-in-situ concrete at 28 days (Annex-III Table III.1)
            m_short = Es/Ecm >= 7.5
            m_long  = Es/(Kc*Ecm) >= 15.0
            m_before = Es/Eci (if concrete age i < 28 days)

            @author: Sweta Pal
        """

        # As per clause (fixed)
        Es = E_STEEL_MPA  # MPa (N/mm2)

        # Ecm from Annex III Table III.1 if not provided
        if Ecm is None:
            if concrete_grade is None:
                raise ValueError("Provide Ecm OR concrete_grade (Ecm can be obtained from Annex III Table III.1).")

            # NOTE: Ecm comes from IRC22 Annex III concrete table (III.2)
            concrete_table = IRC22_2014.cl_602_annexIII_concrete_properties(aggregate_type=aggregate_type)
            if concrete_grade not in concrete_table:
                raise ValueError(f"Unknown concrete grade '{concrete_grade}'. Valid: {list(concrete_table.keys())}")

            Ecm = concrete_table[concrete_grade]["Ec"] * 1000  # Ec stored in GPa → convert to MPa

        # BEFORE 28 DAYS
        m_before = None
        if Eci is not None:
            m_before = Es / Eci

        # AFTER 28 DAYS

        # Short-term
        m_short = Es / Ecm
        m_short = max(m_short, 7.5)

        # Long-term
        m_long = Es / (Kc * Ecm)
        m_long = max(m_long, 15.0)

        return {
            "Es_MPa": Es,
            "Ecm_MPa": round(Ecm, 2),
            "Eci_MPa": None if Eci is None else round(Eci, 2),
            "Kc": Kc,
            "m_before_28days": None if m_before is None else round(m_before, 3),
            "m_short_term": round(m_short, 3),
            "m_long_term": round(m_long, 3),
            "clause": "IRC 22:2014 - 604.3"
        }


    # 604.3.1  Limiting Stresses for Serviceability

    @staticmethod
    def cl_604_3_1_limiting_stresses(
        f_ck_cu,        # MPa : concrete cube strength (IRC 22 Annex III Table III.1)
        f_yk_reinf,     # MPa : reinforcement yield strength (IRC 22 Annex III / IS 1786)
        f_y_struct,     # MPa : structural steel yield strength (IRC 22 Annex III / steel grade)
        fbc=None,       # MPa : bending compressive stress in steel section
        fbt=None,       # MPa : bending tensile stress in steel section
        fp=0.0,         # MPa : bearing stress in steel section
        tau_b=0.0       # MPa : shear stress in steel section
    ):
        """
        IRC:22-2014 Clause 604.3.1 - Limiting Stresses for Serviceability

        1. Concrete compressive stress limit  -> IRC 112-2011 Cl. 12.2.1
        2. Reinforcement tensile stress limit -> IRC 112-2011 Cl. 12.2.2
        3. Structural steel equivalent stress -> must be <= 0.9 f_y (structural steel)

        symbols :
        - f_ck_cu (concrete cube strength) comes from IRC22 Annex III Table III.1
        - f_yk_reinf is characteristic yield strength of reinforcement
        - f_y_struct is characteristic yield strength of structural steel

        @author: Sweta Pal
        """


        # Concrete allowable stress

        # IRC 112-2011 Clause 12.2.1: σc,max <= k1 * f_ck
        k1 = 0.48
        sigma_c_allow = k1 * f_ck_cu

        # Reinforcement allowable tensile stress

        # IRC 112-2011 Clause 12.2.2: σs,max <= k3 * f_yk
        k3 = 0.80
        sigma_s_allow = k3 * f_yk_reinf

        # 3) Structural steel equivalent stress

        # Equivalent stress must be <= 0.9 f_y (structural)
        steel_limit = 0.9 * f_y_struct

        fe_comp = None
        fe_tens = None

        steel_equivalent_stress_checked = False
        steel_safe = None  # None = not evaluated

        if fbc is not None and fbt is not None:
            steel_equivalent_stress_checked = True

            # Equivalent compressive stress (En 4.1)
            fe_comp = math.sqrt(fbc**2 + fp**2 + fbc * fp + 3 * (tau_b**2))

            # Equivalent tensile stress (En 4.2)
            fe_tens = math.sqrt(fbt**2 + fp**2 + fbt * fp + 3 * (tau_b**2))

            steel_safe = (fe_comp <= steel_limit) and (fe_tens <= steel_limit)

        return {
            # Concrete check
            "k1": k1,
            "concrete_allowable_stress_MPa": round(sigma_c_allow, 3),

            # Reinforcement check
            "k3": k3,
            "reinforcement_allowable_stress_MPa": round(sigma_s_allow, 3),

            # Structural steel check
            "steel_equivalent_limit_0.9fy_MPa": round(steel_limit, 3),
            "steel_equivalent_compressive_fe_MPa": None if fe_comp is None else round(fe_comp, 3),
            "steel_equivalent_tensile_fe_MPa": None if fe_tens is None else round(fe_tens, 3),
            "steel_equivalent_stress_checked": steel_equivalent_stress_checked,
            "steel_serviceability_safe": steel_safe,
            "clause": "IRC 22:2014 - 604.3.1 + IRC 112-2011 12.2.1 / 12.2.2"
        }



    # 604.3.2  Limit of Deflection and Camber
    @staticmethod
    def cl_604_3_2_deflection_limits(
        span_m,
        defl_live_impact_mm=None,
        defl_total_mm=None,
        cantilever_m=0,
        cant_defl_total_mm=None,
        cant_defl_live_impact_mm=None
    ):

        """
        IRC 22:2014
        Clause 604.3.2 - Limit of Deflection and Camber

        Checks:
        Main Span
            Live load + Impact  <= L / 800
            Total deflection    <= L / 600

        Cantilever Tip (if exists)
            Total deflection            <= Lc / 300
            Live load + Impact defl     <= Lc / 400

        Parameters:
            span_m (float): span of girder in meters
            defl_live_impact_mm (float): deflection under live + impact (mm)
            defl_total_mm (float): total deflection DL + SDL + LL + IMP (mm)

            cantilever_m (float): cantilever length (m), 0 if none
            cant_defl_total_mm (float): total tip deflection (mm)
            cant_defl_live_impact_mm (float): tip deflection LL + impact (mm)

        Returns:
            dict describing limits and pass / fail status
        """

        span_mm = span_m * 1000

        # MAIN GIRDER LIMITS
        allow_live_impact = span_mm / 800.0
        allow_total = span_mm / 600.0

        live_ok = None
        total_ok = None

        if defl_live_impact_mm is not None:
            live_ok = defl_live_impact_mm <= allow_live_impact

        if defl_total_mm is not None:
            total_ok = defl_total_mm <= allow_total


        # CANTILEVER CHECKS
        cantilever_results = None

        if cantilever_m > 0:
            Lc_mm = cantilever_m * 1000

            allow_cant_total = Lc_mm / 300.0
            allow_cant_live = Lc_mm / 400.0

            cant_total_ok = None
            cant_live_ok = None

            if cant_defl_total_mm is not None:
                cant_total_ok = cant_defl_total_mm <= allow_cant_total

            if cant_defl_live_impact_mm is not None:
                cant_live_ok = cant_defl_live_impact_mm <= allow_cant_live

            cantilever_results = {
                "cantilever_length_mm": Lc_mm,
                "allow_total_mm": round(allow_cant_total, 3),
                "allow_live_impact_mm": round(allow_cant_live, 3),
                "total_ok": cant_total_ok,
                "live_impact_ok": cant_live_ok
            }

        return {
            "span_mm": span_mm,

            "main_girder_limits": {
                "allow_live_impact_mm": round(allow_live_impact, 3),
                "allow_total_mm": round(allow_total, 3),
                "live_check_ok": live_ok,
                "total_check_ok": total_ok
            },

            "cantilever_check": cantilever_results,

            "clause": "IRC 22:2014 - 604.3.2"
        }

    @staticmethod
    def cl_604_4_crack_control_As_min(
        fctm,                 # MPa (mean tensile strength of concrete) - IRC 22 Table III.1
        beff,                 # mm effective flange width in tension zone
        t_slab,               # mm slab thickness in tension zone
        fy,                   # MPa reinforcement yield strength (f_yk from IRC 22 Annex III)
        kc=0.5,               # coefficient kc >= 0.5 (IRC:112 Cl 12.3.3)
        sigma_s=None,         # MPa steel stress; if None -> take fy
        width_mm=None,        # mm flange width or web width for selecting k (restraint coefficient)
        element_type="flange",# "flange" or "web"
        As_provided=None      # mm2 
    ):
        """
        IRC 22:2014
        Clause 604.4 - Control of cracking in concrete
        Ref: IRC:112-2011 Clause 12.3.3 (Minimum reinforcement for crack control)

        Formula:
            As_min = kc * k * fct_eff * Act / sigma_s

        Assumptions:
            - Cracking considered after 28 days ⇒ fct_eff = fctm
            - fctm taken from IRC 22 Table III.1 (Annexure III)

        k (restraint coefficient):
            k = 1.0  for web h <= 300 mm OR flange width <= 300 mm
            k = 0.65 for web h > 800 mm OR flange width > 800 mm
            Intermediate values may be interpolated.
        """

        # validity checks 
        if kc < 0.5:
            raise ValueError("kc must be >= 0.5 as per IRC:112-2011 Clause 12.3.3")

        if sigma_s is None:
            sigma_s = fy  # assume steel stress = fy unless user gives lower value

        #  define fct_eff 
        #  cracking after 28 days -> fct_eff = fctm
        fct_eff = fctm

        #  compute k based on width/web-height 
        # If width_mm not provided, default to k=1.0 
        if width_mm is None:
            k = 1.0
            k_basis = "width_mm not provided → assumed k = 1.0"
        else:
            if width_mm <= 300:
                k = 1.0
                k_basis = f"{element_type} dimension <= 300 mm → k = 1.0"
            elif width_mm > 800:
                k = 0.65
                k_basis = f"{element_type} dimension > 800 mm → k = 0.65"
            else:
                # Linear interpolation between (300,1.0) and (800,0.65)
                k = 1.0 - (width_mm - 300) * (1.0 - 0.65) / (800 - 300)
                k_basis = f"{element_type} dimension between 300–800 mm → interpolated k"

        # tensile concrete area 
        Act = beff * t_slab  # mm2

        #  minimum reinforcement 
        As_min = kc * k * fct_eff * Act / sigma_s

        result = {
            "Act_mm2": round(Act, 2),
            "kc": kc,
            "k": round(k, 4),
            "k_basis": k_basis,
            "fctm_MPa": fctm,
            "fct_eff_MPa": fct_eff,  
            "sigma_s_MPa": sigma_s,
            "As_min_mm2": round(As_min, 2),
            "clause": "IRC 22:2014 - 604.4 | IRC 112-2011 Cl.12.3.3"
        }

        if As_provided is not None:
            result["As_provided_mm2"] = As_provided
            result["is_ok"] = As_provided >= As_min

        return result


    @staticmethod
    def cl_605_2_fatigue_design(
            tp_mm,                     # thicker plate thickness (mm)
            f_MPa,                     # actual fatigue stress range (MPa)
            Nsc=None,                  # no. of stress cycles 
            section_type=KEY_SECTION_FABRICATION[1],     # "welded" or "rolled"
            gamma_mft=1.35,            # γ_mft = partial safety factor for fatigue strength (Table 3)
            gamma_ff=1.0               # γ_ff  = partial safety factor for fatigue actions/effects (usually 1.0)
        ):
        """
        IRC:22-2015
        Clause 605.2 - Fatigue Design

        Includes:
        1) Thickness correction factor μr (only for welded sections with tp > 25 mm):
                μr = (25/tp)^0.25 ≤ 1.0

        2) Low fatigue exemption:
                f < 27/γ_mft
            OR Nsc < 5e6 * ((27/γ_mft)/(γ_ff*f))^3

        Notes:
        - For rolled sections, μr = 1.0 always.
        - For welded sections, μr reduces fatigue capacity for tp > 25 mm.
        """


        if tp_mm <= 0:
            raise ValueError("tp_mm must be > 0")
        if f_MPa <= 0:
            raise ValueError("f_MPa must be > 0")

        section_type = section_type.lower()
        if section_type not in ["welded", "rolled"]:
            raise ValueError("section_type must be 'welded' or 'rolled'")

        # 1) Capacity reduction factor μr (only if welded & tp>25)

        if section_type == KEY_SECTION_FABRICATION[0]:
            mu_r = 1.0
            mu_r_reason = "Rolled section → thickness correction not required"
        else:
            if tp_mm <= 25:
                mu_r = 1.0
                mu_r_reason = "Welded section but tp ≤ 25 mm → no correction"
            else:
                mu_r = min((25.0 / tp_mm) ** 0.25, 1.0)
                mu_r_reason = "Welded section & tp > 25 mm → correction applied"

        # 2) Low fatigue exemption checks
        
        stress_limit = 27.0 / gamma_mft
        stress_ok = f_MPa < stress_limit

        cycle_limit = None
        cycle_ok = None
        if Nsc is not None:
            if Nsc <= 0:
                raise ValueError("Nsc must be > 0 when provided")

            cycle_limit = 5e6 * ((27.0 / gamma_mft) / (gamma_ff * f_MPa)) ** 3
            cycle_ok = Nsc < cycle_limit

        # Fatigue not required if any exemption satisfied
        fatigue_required = not (stress_ok or (cycle_ok is True))

        return {
            "section_type": section_type,
            "tp_mm": tp_mm,
            "mu_r": round(mu_r, 4),
            "mu_r_reason": mu_r_reason,

            "gamma_mft": gamma_mft,     # fatigue strength
            "gamma_ff": gamma_ff,       # fatigue action

            "stress_limit_27_by_gamma_mft_MPa": round(stress_limit, 3),
            "f_MPa": f_MPa,
            "stress_condition_ok": stress_ok,

            "Nsc_input": Nsc,
            "cycle_limit_Nsc": None if cycle_limit is None else round(cycle_limit),
            "cycle_condition_ok": cycle_ok,

            "fatigue_required": fatigue_required,
            "clause": "IRC 22:2015 - 605.2 Fatigue Design"
        }


    @staticmethod
    def cl_605_3_fatigue_strength(
            Nsc,                    # number of stress cycles
            section_type=KEY_SECTION_FABRICATION[0],  # "rolled" / "welded"
            ffn=None,               # normal fatigue strength at 5e6 cycles (MPa)
            tfn=None                # shear fatigue strength at 5e6 cycles (MPa)
        ):
        """
        IRC 22:2015
        Clause 605.3 - Fatigue Strength

        Computes:
            - Design normal fatigue stress range f_f
            - Design shear fatigue stress range tau_f

        Equations (IRC 22:2015 - 605.3):

            For Normal Stress range:
                When Nsc <= 5 x 10^6:
                    f_f = f_fn * (5x10^6 / Nsc)^(1/3)
                When 5 x 10^6 <= Nsc <= 10^8:
                    f_f = f_fn * (5x10^6 / Nsc)^(1/5)

            For Shear Stress range:
                tau_f = tau_fn * (5x10^6 / Nsc)^(1/5)

        Default values (as per correction note):
            - ffn = 118 MPa for rolled sections if not provided
            - ffn = 92 MPa for welded sections if not provided
            - tfn = 59 MPa if not provided

        Returns:
            dict
        """


        if Nsc is None or Nsc <= 0:
            raise ValueError("Nsc must be a positive number")

        section_type = section_type.lower().strip()
        if section_type not in ["rolled", "welded"]:
            raise ValueError("section_type must be 'rolled' or 'welded'")

        # Default fatigue strengths
        if ffn is None:
            ffn = 118.0 if section_type == KEY_SECTION_FABRICATION[0] else 92.0

        if tfn is None:
            tfn = 59.0

        # Normal fatigue stress range f_f
        
        if Nsc <= 5e6:
            exponent = 1.0 / 3.0
        elif Nsc <= 1e8:
            exponent = 1.0 / 5.0
        else:
            # IRC curve normally specified up to 1e8,
            # conservatively continue using 1/5 beyond 1e8
            exponent = 1.0 / 5.0

        f_f = ffn * (5e6 / Nsc) ** exponent

        # Shear fatigue stress range tau_f

        tau_f = tfn * (5e6 / Nsc) ** (1.0 / 5.0)

        return {
            "Nsc": Nsc,
            "section_type": section_type,
            "ffn_MPa_used": ffn,
            "tfn_MPa_used": tfn,
            "normal_exponent_used": round(exponent, 4),
            "f_f_normal_MPa": round(f_f, 3),
            "tau_f_shear_MPa": round(tau_f, 3),
            "clause": "IRC 22:2015 - 605.3 Fatigue Strength"
        }



    @staticmethod
    def cl_605_4_fatigue_assessment(
        ff,                 # Normal fatigue strength range for NSC (from 605.3)
        tf,                 # Shear fatigue strength range for NSC (from 605.3)
        mu_r=1.0,           # Capacity reduction factor (605.2), default 1.0
        gamma_mft=1.35,     # Partial safety factor for fatigue strength (Table 3)
        fy=None,            # Yield stress of steel (MPa)

        # Stress RANGE values (constant stress range assumption)
        f_range=None,       # Actual normal stress RANGE in service (MPa)
        tau_range=None,     # Actual shear stress RANGE in service (MPa)

        # Absolute MAX stress values from software (important correction)
        sigma_max=None,     # Absolute maximum normal stress (MPa)
        tau_max=None        # Absolute maximum shear stress (MPa)
    ):
        """
        IRC:22-2015
        Clause 605.4 – Fatigue Assessment

        Design fatigue strength for NSC life cycles:
            f_fd   = μr * f_f / γ_mft      Eq 5.4
            τ_fd   = μr * τ_f / γ_mft      Eq 5.5

        Constant stress range requirement:
            f_range   <= f_fd
            tau_range <= tau_fd

        Absolute max stress limits:
            sigma_max <= fy
            tau_max   <= tau_y

        Note:
            τy is not explicitly defined in IRC22 clause text here.
            As per assumption:
                tau_y = 0.43 * fy   (Assumed based on IRC:24 Table G.2)
        """


        if fy is None:
            raise ValueError("fy (yield stress) must be provided")

        # Design fatigue strengths (Eq 5.4, 5.5)

        f_fd = mu_r * ff / gamma_mft
        tau_fd = mu_r * tf / gamma_mft

        
        # Normal elastic limit
        sigma_limit = fy

        # Shear elastic limit 
        tau_y = 0.43 * fy  # Assumption: IRC 24 Table G.2

        results = {
            "f_fd_MPa": round(f_fd, 3),
            "tau_fd_MPa": round(tau_fd, 3),
            "sigma_limit_MPa": round(sigma_limit, 3),
            "tau_y_limit_MPa": round(tau_y, 3),
            "mu_r": mu_r,
            "gamma_mft": gamma_mft,
            "clause": "IRC 22:2015 - 605.4 Fatigue Assessment"
        }

        # Stress RANGE checks (fatigue range)
        if f_range is not None:
            results["f_range_MPa"] = f_range
            results["range_check_normal_ok"] = (f_range <= f_fd)

        if tau_range is not None:
            results["tau_range_MPa"] = tau_range
            results["range_check_shear_ok"] = (tau_range <= tau_fd)

        # Absolute MAX stress checks 
        if sigma_max is not None:
            results["sigma_max_MPa"] = sigma_max
            results["absolute_check_sigma_ok"] = (abs(sigma_max) <= sigma_limit)

        if tau_max is not None:
            results["tau_max_MPa"] = tau_max
            results["absolute_check_tau_ok"] = (abs(tau_max) <= tau_y)

        # Overall summary flags (only computed if relevant values provided)
        range_ok = None
        abs_ok = None

        if (f_range is not None) or (tau_range is not None):
            range_ok = True
            if f_range is not None:
                range_ok = range_ok and (f_range <= f_fd)
            if tau_range is not None:
                range_ok = range_ok and (tau_range <= tau_fd)

        if (sigma_max is not None) or (tau_max is not None):
            abs_ok = True
            if sigma_max is not None:
                abs_ok = abs_ok and (abs(sigma_max) <= sigma_limit)
            if tau_max is not None:
                abs_ok = abs_ok and (abs(tau_max) <= tau_y)

        results["range_checks_overall"] = range_ok
        results["absolute_stress_checks_overall"] = abs_ok

        return results


    @staticmethod
    def cl_606_3_1_stud_connector_strength(
        d_mm,                     # stud diameter (mm)
        hs_mm,                    # stud height (mm)
        fu_MPa=500,               # stud ultimate strength (MPa)
        grade=None,               # ex: "M25", "M30" (preferred)
        fck_cu_MPa=None,          # if grade not given
        Ecm_MPa=None,             # if grade not given
        gamma_v=1.25,
        use_table7_reference=True,
        debug=False
    ):
        """
        IRC:22-2015 Clause 606.3.1 – Stud connector strength (Eq 6.1)

        NOTE:
        - fck_cu and Ecm should ideally come from IRC22 Table III.1 (Annexure III).
        - Provide either:
            (a) grade="M25"/"M30" etc -> will fetch fck_cu & Ecm from Table III.1
            OR
            (b) explicitly give fck_cu_MPa and Ecm_MPa
        """

        # Fetch concrete properties from IRC Table III.1 
        if (fck_cu_MPa is None or Ecm_MPa is None):
            if grade is None:
                raise ValueError("Provide either grade='Mxx' OR provide fck_cu_MPa and Ecm_MPa")

            # Example expected function: cl_602_annexIII_concrete_properties()

            table = IRC22_2014.cl_602_annexIII_concrete_properties()

            if grade not in table:
                raise ValueError(f"{grade} not found in IRC22 Table III.1 concrete properties")

        row = table[grade]

        # Handles different possible keys safely
        if "fck_cu" in row:
            fck_cu_MPa = row["fck_cu"]
        elif "fck" in row:
            fck_cu_MPa = row["fck"]   # cube strength from Annex III
        else:
            raise KeyError("Concrete table must provide fck or fck_cu")

        # Modulus of elasticity (usually stored in GPa)
        if "Ec" in row:
            Ecm_MPa = row["Ec"] * 1000 if row["Ec"] < 1000 else row["Ec"]
        else:
            raise KeyError("Concrete table must provide Ec")

        if d_mm <= 0 or hs_mm <= 0:
            raise ValueError("Stud diameter and height must be positive")

        if fu_MPa > 500:
            print("Warning: fu > 500 MPa. IRC recommends fu ≤ 500 MPa")

        # fck cylinder
        fck_cyl_MPa = 0.8 * fck_cu_MPa

        # alpha
        slenderness = hs_mm / d_mm
        if slenderness >= 4.0:
            alpha = 1.0
        elif 3.0 < slenderness < 4.0:
            alpha = 0.2 * (slenderness + 1.0)
        else:
            alpha = 0.2 * (slenderness + 1.0)  # outside range, keep as per eqn with warning
            print("Warning: hs/d < 3, outside recommended range")

        # strengths (Eq 6.1) 
        Qu_steel_N = (0.8 * fu_MPa * math.pi * d_mm**2 / 4.0) / gamma_v
        Qu_conc_N  = (0.29 * alpha * d_mm**2 * math.sqrt(fck_cyl_MPa * Ecm_MPa)) / gamma_v

        if Qu_steel_N <= Qu_conc_N:
            Qu_N = Qu_steel_N
            governs = "steel"
        else:
            Qu_N = Qu_conc_N
            governs = "concrete"

        #  Table 7 reference 
        Qu_table7_kN = None
        table7_note = None

        if use_table7_reference:
            TABLE7 = {
                25: {25: 112, 22: 87, 20: 72, 16: 46, 12: 26},
                30: {25: 125, 22: 97, 20: 80, 16: 51, 12: 29},
                40: {25: 149, 22: 115, 20: 95, 16: 61, 12: 34},
                50: {25: 156, 22: 120, 20: 100, 16: 64, 12: 36}
            }

            std_ds = [12, 16, 20, 22, 25]
            std_grades = [25, 30, 40, 50]

            d_key = int(round(d_mm))
            if d_key in std_ds and 25 <= fck_cu_MPa <= 50:
                if hs_mm > 100:
                    table7_note = "hs > 100 mm: Table 7 recommends using 100 mm values"

                if fck_cu_MPa in TABLE7:
                    Qu_table7_kN = TABLE7[int(fck_cu_MPa)][d_key]
                else:
                    # interpolate
                    lower = max(g for g in std_grades if g <= fck_cu_MPa)
                    upper = min(g for g in std_grades if g >= fck_cu_MPa)
                    ql = TABLE7[lower][d_key]
                    qu = TABLE7[upper][d_key]
                    Qu_table7_kN = ql + (qu - ql) * (fck_cu_MPa - lower) / (upper - lower)
                    Qu_table7_kN = round(Qu_table7_kN, 3)
                    table7_note = (table7_note + " | " if table7_note else "") + \
                                "Interpolated Table 7 value"

        result = {
            "Qu_kN": round(Qu_N / 1000.0, 3),
            "governing_mode": governs,
            "alpha": round(alpha, 4),
            "clause": "IRC 22:2015 - 606.3.1 (Eq 6.1)"
        }

        if use_table7_reference:
            result["Qu_table7_kN"] = Qu_table7_kN
            if table7_note:
                result["table7_note"] = table7_note

        if debug:
            result.update({
                "fck_cu_MPa": fck_cu_MPa,
                "fck_cyl_MPa": round(fck_cyl_MPa, 3),
                "Ecm_MPa": Ecm_MPa,
                "slenderness_h_by_d": round(slenderness, 3),
                "Qu_steel_kN": round(Qu_steel_N / 1000.0, 3),
                "Qu_concrete_kN": round(Qu_conc_N / 1000.0, 3),
            })

        return result


    @staticmethod
    def cl_606_3_2_stud_connector_fatigue_strength(
        Nsc,
        tau_fn_MPa=67.0,       # MPa (default per IRC Table 5/8 guidance)
        stud_d_mm=None,        # 16, 20, 22, 25 (optional for Table 8)
        use_table8=False       # if True, return Qr from Table 8 also
    ):
        """
        IRC:22-2015
        Clause 606.3.2 - Fatigue strength of shear connectors (Stud)

        Equation:
            tau_f = tau_fn * (5e6 / Nsc)^(1/5)

        Optional:
            Returns Table 8 nominal fatigue strength Qr (kN) for headed studs (phi 16/20/22/25)
            using log interpolation for intermediate Nsc.
        """


        if Nsc <= 0:
            raise ValueError("Nsc must be positive")

        # --- Clause equation ---
        tau_f_MPa = tau_fn_MPa * ((5e6 / Nsc) ** (1.0 / 5.0))

        result = {
            "tau_f_MPa": round(tau_f_MPa, 3),
            "clause": "IRC 22:2015 - 606.3.2"
        }

        #  Table 8 values
        if use_table8:
            if stud_d_mm is None:
                raise ValueError("stud_d_mm must be provided when use_table8=True")

            TABLE8_Qr_kN = {
                25: {1e5: 71, 5e5: 52, 2e6: 39, 1e7: 28, 1e8: 18},
                22: {1e5: 55, 5e5: 40, 2e6: 30, 1e7: 22, 1e8: 14},
                20: {1e5: 46, 5e5: 33, 2e6: 25, 1e7: 18, 1e8: 11},
                16: {1e5: 29, 5e5: 21, 2e6: 16, 1e7: 11, 1e8: 7},
            }

            d_key = int(round(stud_d_mm))
            if d_key not in TABLE8_Qr_kN:
                raise ValueError("stud_d_mm must be one of 16, 20, 22, 25 as per Table 8")

            # log interpolation between nearest points
            points = sorted(TABLE8_Qr_kN[d_key].items())  # list of (N, Qr)
            Ns = [p[0] for p in points]

            if Nsc <= Ns[0]:
                Qr = TABLE8_Qr_kN[d_key][Ns[0]]
            elif Nsc >= Ns[-1]:
                Qr = TABLE8_Qr_kN[d_key][Ns[-1]]
            else:
                # find bracket
                for i in range(len(Ns) - 1):
                    N1, N2 = Ns[i], Ns[i + 1]
                    if N1 <= Nsc <= N2:
                        Q1 = TABLE8_Qr_kN[d_key][N1]
                        Q2 = TABLE8_Qr_kN[d_key][N2]

                        # log interpolation
                        logN = math.log10(Nsc)
                        logN1 = math.log10(N1)
                        logN2 = math.log10(N2)

                        Qr = Q1 + (Q2 - Q1) * ((logN - logN1) / (logN2 - logN1))
                        break

            result["Qr_table8_kN"] = round(Qr, 3)

        return result



    @staticmethod
    def cl_606_4_1_longitudinal_shear_and_spacing(
        V_kN,              # Vertical shear at section (kN)
        beff_mm,           # Effective slab width (mm)
        xu_mm,             # NA depth from top concrete (mm) -> from IRC22 603.3.1
        t_slab_mm,         # slab thickness (mm)

        Qu_kN,             # stud design capacity (kN) -> from IRC22 606.3.1 

        # Material 
        Es_MPa=E_STEEL_MPA,      # MPa (as per IRC 22 clause 604.3)
        Ecm_MPa=None,      # MPa secant modulus of concrete (can be taken from IRC22 Table III.1)

        # Steel section inputs
        As_mm2=0.0,        # steel area (mm2) (from software/user)
        Is_mm4=0.0,        # steel second moment of area (mm4) (from software/user)
        ys_mm=None,        # CG distance from top of section to steel CG (mm)
        D_mm=None,         # total depth of girder (mm) - needed only if ys_mm not given

        Ic_mm4=None,       # composite inertia if already known (optional)
        studs_per_section=2
    ):
        """
        IRC 22:2015 - Clause 606.4.1
        @author: Sweta Pal

        Longitudinal Shear and Spacing of Shear Connectors (ULS)

        Notes / Corrections:
        - Ecm is used instead of Ec. (Ecm may be taken from IRC 22 Table III.1)
        - xu is obtained from IRC 22 Clause 603.3.1 (neutral axis depth)
        - Composite inertia must include steel inertia Is_mm4 (previously missing)
        - Qu must come from Clause 606.3.1, not assumed 100 kN
        - ys_mm is CG distance steel to top of section;
        default assumption: ys = D/2 + t_slab (if ys not given)
        """

        if Ecm_MPa is None:
            raise ValueError("Ecm_MPa must be provided (can be taken from IRC22 Table III.1)")

        if Qu_kN <= 0:
            raise ValueError("Qu_kN must be positive (obtain from Clause 606.3.1)")

        # Convert kN to N
        V_N = V_kN * 1e3
        Qu_N = Qu_kN * 1e3

        # Default ys if not provided
        if ys_mm is None:
            if D_mm is None:
                raise ValueError("Provide either ys_mm OR D_mm (for default ys = D/2 + t_slab)")
            ys_mm = (D_mm / 2.0) + t_slab_mm

        # Modular ratio (n)
        n = Es_MPa / Ecm_MPa

        # Effective thickness of concrete in compression block
        t_eff = min(xu_mm, t_slab_mm)

        # Transformed compressive concrete area
        Aec = n * beff_mm * t_eff  # mm2

        # Distance from NA to centroid of concrete compression block
        Y = xu_mm - (t_eff / 2.0)

        # Composite inertia calculation (if not supplied)
        if Ic_mm4 is None:
            # Steel inertia about composite NA
            I_steel = Is_mm4 + As_mm2 * (ys_mm - xu_mm) ** 2

            # Concrete inertia about composite NA (transformed)
            I_conc = (n * beff_mm * (t_eff ** 3) / 12.0) + Aec * (Y ** 2)

            Ic_mm4 = I_steel + I_conc

        # Longitudinal shear per unit length (N/mm)
        VL_N_per_mm = V_N * (Aec * Y) / Ic_mm4

        # Connector spacing
        total_Qu_N = studs_per_section * Qu_N
        spacing_mm = total_Qu_N / VL_N_per_mm

        return {
            "n_modular_ratio": round(n, 3),
            "VL_N_per_mm": round(VL_N_per_mm, 3),
            "studs_per_section": studs_per_section,
            "spacing_mm": round(spacing_mm, 2),
            "clause": "IRC 22:2015 - 606.4.1 Longitudinal Shear and Spacing"
        }



    @staticmethod
    def cl_606_4_1_1_full_shear_spacing(
        As_mm2,             # Asl in clause: tensile reinforcement area in longitudinal direction (mm2)
        fyk_MPa,            # reinforcement yield strength f_yk (MPa)
        fck_cu_MPa,         # concrete cube compressive strength f_ck_cu (MPa) (from IRC22 Table III.1)
        beff_mm,            # effective slab width (mm)
        xu_mm,              # NA depth from top concrete (mm) -> from IRC22 603.3.1
        t_slab_mm,          # slab thickness (mm)
        Qu_kN,              # stud capacity (kN) -> from IRC22 606.3.1
        shear_span_mm,      # L = length from zero moment to max moment section (mm)
        studs_per_section=2,
        gamma_m=GAMMA_M0_STEEL
    ):
        """
        IRC 22:2015 Clause 606.4.1.1 Full Shear Connection

        Corrections included:
        - Asl treated as As (tensile reinforcement steel area)
        - fy replaced by fyk since steel is reinforcement
        - fck replaced by fck_cu (cube) from IRC22 Table III.1 (mention in comment)
        - Qu must be obtained from IRC22 Clause 606.3.1 (not assumed)

        Returns:
            H1, H2, governing H, spacing S
        """

        if shear_span_mm <= 0:
            raise ValueError("shear_span_mm must be positive")

        if Qu_kN <= 0:
            raise ValueError("Qu_kN must be positive (obtain from Clause 606.3.1)")

        # Effective concrete compressive area:
        # Aec = b_eff * min(xu, t_slab)
        t_eff = min(xu_mm, t_slab_mm)
        Aec_mm2 = beff_mm * t_eff

        # Longitudinal force due to bending
        # H1 = As * fyk / gamma_m  (converted to kN)
        H1_kN = (As_mm2 * fyk_MPa / gamma_m) * 1e-3

        # H2 = 0.36 * fck_cu * Aec  (converted to kN)
        H2_kN = (0.36 * fck_cu_MPa * Aec_mm2) * 1e-3

        H_kN = min(H1_kN, H2_kN)

        # Total stud capacity per section
        total_Qu_kN = studs_per_section * Qu_kN

        # Longitudinal shear force per unit length (kN/mm)
        H_per_mm_kN = H_kN / shear_span_mm

        # Stud spacing
        spacing_mm = total_Qu_kN / H_per_mm_kN

        return {
            "Aec_mm2": round(Aec_mm2, 2),
            "H1_kN": round(H1_kN, 3),
            "H2_kN": round(H2_kN, 3),
            "H_governing_kN": round(H_kN, 3),
            "spacing_mm": round(spacing_mm, 2),
            "clause": "IRC 22:2015 - 606.4.1.1 Full Shear Connection"
        }



    @staticmethod
    def cl_606_4_2_fatigue_shear_spacing(
        Vr_kN,             # shear range due to LL + impact (kN)
        beff_mm,           # effective slab width (mm)
        xu_mm,             # NA depth from top concrete (mm) -> from IRC22 603.3.1
        t_slab_mm,         # slab thickness (mm)
        I_composite_mm4,   # composite moment of inertia (mm4) (same as 606.4.1; may move to another file)
        Qu_kN,             # stud capacity (kN) -> from Clause 606.3.1
        studs_per_section=2
    ):
        """
        IRC 22:2015 Clause 606.4.2
        Serviceability Limit State (Fatigue) Stud Spacing

        Corrections:
        - Y must use t_eff, not t_slab (same as 606.4.1)
        - I_composite equation same as 606.4.1 (can be reused; likely moved to another file later)
        """

        if Vr_kN <= 0:
            raise ValueError("Vr_kN must be positive")

        if I_composite_mm4 <= 0:
            raise ValueError("I_composite_mm4 must be positive")

        if Qu_kN <= 0:
            raise ValueError("Qu_kN must be positive (obtain from Clause 606.3.1)")

        # effective concrete thickness in compression
        t_eff = min(xu_mm, t_slab_mm)

        # transformed compression area of concrete
        Aec_mm2 = beff_mm * t_eff

        # CG distance of compression block from NA (same as 606.4.1)
        Y_mm = xu_mm - t_eff / 2

        # Longitudinal shear per unit length (kN/mm)
        # Vr_per_mm = Vr * (Aec * Y) / I
        Vr_per_mm_kN = (Vr_kN * Aec_mm2 * Y_mm) / I_composite_mm4

        # total stud resistance per section
        total_Qu_kN = studs_per_section * Qu_kN

        # spacing
        spacing_mm = total_Qu_kN / Vr_per_mm_kN

        return {
            "Aec_mm2": round(Aec_mm2, 2),
            "t_eff_mm": round(t_eff, 2),
            "Y_mm": round(Y_mm, 2),
            "Vr_per_mm_kN": round(Vr_per_mm_kN, 6),
            "spacing_SR_mm": round(spacing_mm, 2),
            "clause": "IRC 22:2015 - 606.4.2 Fatigue Limit State"
        }


    @staticmethod
    def cl_606_6_shear_connector_detailing(
        d_stud_mm,             # stud diameter (ds)
        h_stud_mm,             # stud height (hs)
        t_flange_mm,           # top flange thickness (tf)

        d_stud_head_mm=None,   # stud head diameter (needed for check)
        edge_distance_mm=None, # estud (if not given, calculated)
        b_tf_mm=None,          # top flange width (needed for edge distance calc)
        s_ts_mm=None,          # transverse spacing of studs (needed for edge distance calc)
        n_s=None,              # no. studs per section (needed for edge distance calc)

        t_slab_mm=None,        # slab thickness (needed for clear cover calc)
        clear_cover_stud_mm=None,  # ccstud (if not given, calculated)

        # reinforcement info for projection check
        ccbottom_mm=None,      # bottom slab cover to transverse reinforcement
        d_bar_mm=None,         # bar diameter

        required_clear_cover_mm=MIN_EDGE_DISTANCE_MM  # required minimum clear cover
    ):
        """
        IRC 22:2015 Clause 606.6 - Detailing of Shear Connectors
        @author: Sweta Pal

        Checks:
        1) d_stud <= 2 * t_flange
        2) h_stud >= max(4*d_stud, 100)
        3) stud head diameter >= 1.5*d_stud
        4) edge distance >= 25 mm (can be computed)
        5) stud projection above bottom reinforcement >= ccbottom + dbar + 40
        6) clear cover of stud >= 25 mm (can be computed)
        """

        results = {}

        #  1. Stud diameter limit 
        limit_d = 2 * t_flange_mm
        results["stud_diameter_limit_mm"] = round(limit_d, 2)
        results["stud_diameter_check"] = (d_stud_mm <= limit_d)

        # 2. Stud height requirement 
        min_h_required = max(4 * d_stud_mm, 100.0)
        results["required_min_height_mm"] = round(min_h_required, 2)
        results["stud_height_check"] = (h_stud_mm >= min_h_required)

        # 3. Stud head diameter check 
        min_head_d = 1.5 * d_stud_mm
        results["required_head_diameter_mm"] = round(min_head_d, 2)

        if d_stud_head_mm is None:
            results["stud_head_check"] = None
            results["stud_head_check_note"] = "Stud head diameter not provided"
        else:
            results["provided_head_diameter_mm"] = round(d_stud_head_mm, 2)
            results["stud_head_check"] = (d_stud_head_mm >= min_head_d)

        # 4. Edge distance check
        # If edge_distance_mm not provided, compute using:
        # e = (b_tf - s_ts*(n_s-1) - d_s)/2
        if edge_distance_mm is None:
            if (b_tf_mm is not None) and (s_ts_mm is not None) and (n_s is not None):
                edge_distance_mm = (b_tf_mm - s_ts_mm * (n_s - 1) - d_stud_mm) / 2.0
                results["edge_distance_calculated_mm"] = round(edge_distance_mm, 2)
                results["edge_distance_formula"] = "(b_tf - s_ts*(n_s-1) - d_s)/2"
            else:
                edge_distance_mm = None

        results["required_edge_distance_mm"] = MIN_EDGE_DISTANCE_MM
        if edge_distance_mm is None:
            results["edge_distance_check"] = None
            results["edge_distance_check_note"] = "Edge distance not provided and insufficient data to calculate"
        else:
            results["edge_distance_mm"] = round(edge_distance_mm, 2)
            results["edge_distance_check"] = (edge_distance_mm >= 25.0)

        # 5. Projection check above bottom reinforcement 
        # h_stud >= ccbottom + dbar + 40
        if ccbottom_mm is None or d_bar_mm is None:
            results["projection_check"] = None
            results["projection_check_note"] = "ccbottom_mm / d_bar_mm not provided"
        else:
            min_projection = ccbottom_mm + d_bar_mm + 40.0
            results["required_min_projection_mm"] = round(min_projection, 2)
            results["projection_check"] = (h_stud_mm >= min_projection)

        # 6. Clear cover check 
        # If clear_cover_stud_mm not provided:
        # cc_stud = (t_slab - h_stud)
        if clear_cover_stud_mm is None:
            if t_slab_mm is not None:
                clear_cover_stud_mm = t_slab_mm - h_stud_mm
                results["clear_cover_calculated_mm"] = round(clear_cover_stud_mm, 2)
                results["clear_cover_formula"] = "(t_slab - h_stud)"
            else:
                clear_cover_stud_mm = None

        results["required_clear_cover_mm"] = required_clear_cover_mm
        if clear_cover_stud_mm is None:
            results["clear_cover_check"] = None
            results["clear_cover_check_note"] = "clear cover not provided and t_slab_mm not given"
        else:
            results["clear_cover_stud_mm"] = round(clear_cover_stud_mm, 2)
            results["clear_cover_check"] = (clear_cover_stud_mm >= required_clear_cover_mm)

        checks = [
            results["stud_diameter_check"],
            results["stud_height_check"],
            results["stud_head_check"],
            results["edge_distance_check"],
            results["projection_check"],
            results["clear_cover_check"]
        ]

        # overall = True only if every check is True (ignore None checks)
        results["all_requirements_satisfied"] = all(x is True for x in checks if x is not None)

        results["clause"] = "IRC 22:2015 - Clause 606.6 Detailing of Shear Connectors"
        return results



    @staticmethod
    def cl_606_9_shear_connector_spacing_limits(
        tslab_mm,      # slab thickness
        h_stud_mm,     # stud height
        provided_spacing_mm=None
    ):
        """
        IRC 22:2015 Clause 606.9
        Limiting Criteria for Spacing of Shear Connectors
        """

        # Maximum Allowable Spacing 
        max1 = 600                          # absolute max
        max2 = 3 * tslab_mm                 # 3 * slab thickness
        max3 = 4 * h_stud_mm               # 4 * stud height

        governing_max = min(max1, max2, max3)

        # Minimum Allowable Spacing 
        min_spacing = 75

        result = {
            "max_spacing_limit_mm": governing_max,
            "limit_600_mm": max1,
            "limit_3_tslab_mm": max2,
            "limit_4_hstud_mm": max3,
            "minimum_spacing_limit_mm": min_spacing,
            "clause": "IRC 22:2015 - Clause 606.9 Limiting Criteria for Shear Connector Spacing"
        }

        if provided_spacing_mm is not None:
            result["provided_spacing_mm"] = provided_spacing_mm
            result["is_spacing_acceptable"] = (
                provided_spacing_mm >= min_spacing and
                provided_spacing_mm <= governing_max
            )

        return result

    @staticmethod
    def cl_606_10_transverse_shear_check(
        VL_kN,          # Longitudinal shear per unit length (kN) from earlier clause
        fck,            # MPa
        fyk,            # MPa (yield strength of transverse reinforcement)
        L_mm,           # length of possible shear plane (mm)
        Ast_cm2_per_m,  # provided transverse steel area per metre (cm2/m)
        n_layers=6      # default based on 200mm spacing assumption
    ):
        """
        IRC 22:2015 - Clause 606.10 Transverse Shear Check
        @author: Sweta Pal

        Returns:
            governing_capacity_kN/m
            check_pass
            details
        """


        # Convert units where required
        VL = VL_kN  #  kN/m
        L = L_mm / 1000.0  # convert mm to metres
        Ast = Ast_cm2_per_m  # cm2/m as required by clause

        # Capacity 1 
        Vcap1 = 0.632 * L * math.sqrt(fck)

        # Capacity 2 
        Vcap2 = 0.232 * L * math.sqrt(fck) + 0.1 * Ast * fyk * n_layers * 1e-3
        # Note: 0.1 * Ast * fyk gives kN since Ast in cm2 and fyk MPa

        # Minimum Steel Requirement 
        Ast_min = (2.5 * VL) / fyk  # cm2/m

        check1 = VL <= Vcap1
        check2 = VL <= Vcap2
        min_steel_ok = Ast >= Ast_min

        return {
            "VL_kN_per_m": round(VL, 3),
            "Vcap1_kN_per_m": round(Vcap1, 3),
            "Vcap2_kN_per_m": round(Vcap2, 3),
            "governing_capacity_kN_per_m": round(max(Vcap1, Vcap2), 3),
            "check_ok": check1 or check2,
            "min_Ast_required_cm2_per_m": round(Ast_min, 3),
            "Ast_provided_ok": min_steel_ok,
            "clause": "IRC 22:2015 - Clause 606.10 Transverse Shear Check"
        }
