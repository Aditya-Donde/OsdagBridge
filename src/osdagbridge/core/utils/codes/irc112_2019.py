"""IRC 112:2020 — Code of Practice for Concrete Road Bridges."""

from __future__ import annotations


class IRC112_2019:
    """
    Static helpers for IRC 112:2020 clauses used in bridge deck design.
    Method names follow the pattern cl_<clause>_<topic>.
    """

    # IRC 112:2020 Table B.3.1 — α_e for solid slabs spanning in one direction
    # (b/l_o, α_e_simply_supported, α_e_continuous)
    # l_o = effective span of the slab panel (transverse girder spacing S)
    # b   = panel dimension parallel to supports (longitudinal cross-bracing spacing)
    _TABLE_B31 = [
        (0.1, 0.40, 0.40), (0.2, 0.80, 0.80), (0.3, 1.16, 1.16),
        (0.4, 1.48, 1.44), (0.5, 1.72, 1.68), (0.6, 1.96, 1.84),
        (0.7, 2.12, 1.96), (0.8, 2.24, 2.08), (0.9, 2.36, 2.16),
        (1.0, 2.48, 2.24), (1.1, 2.60, 2.28), (1.2, 2.64, 2.36),
        (1.3, 2.72, 2.40), (1.4, 2.80, 2.48), (1.5, 2.84, 2.52),
        (1.6, 2.88, 2.56), (1.7, 2.92, 2.60), (1.8, 2.96, 2.60),
        (1.9, 3.00, 2.60), (2.0, 3.04, 2.60),
    ]

    @staticmethod
    def table_B31_alpha_e(b_lo: float, continuous: bool = True) -> float:
        """
        IRC 112:2020 Table B.3.1 — α_e coefficient for Eq. B3.1 / B3.2.

        Parameters
        ----------
        b_lo : float
            Ratio b / l_o where:
              l_o = effective span of the slab element (the span direction, m)
              b   = slab dimension parallel to the supports (perpendicular to span, m)
            For a plate girder bridge deck:
              l_o = girder spacing S          (transverse span of the deck panel)
              b   = cross-bracing spacing L_cb (longitudinal panel dimension,
                    bounded by adjacent cross-bracings / diaphragms)
            Typical b/l_o ≈ 1–3, so the full table range is relevant.
        continuous : bool
            True (default) for a continuous slab (deck over multiple girder spans);
            False for a simply supported slab.

        Returns
        -------
        float
            Interpolated α_e value.
        """
        table = IRC112_2019._TABLE_B31
        col = 2 if continuous else 1
        if b_lo <= table[0][0]:
            return table[0][col]
        if b_lo >= table[-1][0]:
            return table[-1][col]
        for i in range(len(table) - 1):
            x0, x1 = table[i][0], table[i + 1][0]
            if x0 <= b_lo <= x1:
                t = (b_lo - x0) / (x1 - x0)
                return table[i][col] + t * (table[i + 1][col] - table[i][col])
        return table[-1][col]

    @staticmethod
    def eq_B31_effective_width(
        l_o: float,
        a: float,
        b1: float,
        b_lo: float,
        continuous: bool = True,
        b_cap: float | None = None,
    ) -> float:
        """
        IRC 112:2020 Eq. B3.1 — effective width for a concentrated load on a
        solid slab spanning in one direction.

        bef = α_e × a × (1 - a/l_o) + b_1
        subject to bef ≤ b_cap (if supplied).

        Parameters
        ----------
        l_o     : effective span (m)
        a       : load distance from nearer support (m)
        b1      : breadth of load concentration area including twice the wearing
                  course thickness (m) — tyre_contact_width + 2 × wc_thickness
        b_lo    : b / l_o ratio for Table B.3.1 lookup
        continuous : True for continuous slab (default)
        b_cap   : optional upper limit on bef (m); e.g. l_o to cap at one panel
        """
        alpha_e = IRC112_2019.table_B31_alpha_e(b_lo, continuous)
        bef = alpha_e * a * (1.0 - a / l_o) + b1
        if b_cap is not None:
            bef = min(bef, b_cap)
        return bef

    @staticmethod
    def eq_B32_effective_width_cantilever(
        a: float,
        b1: float,
        l_parallel: float,
        b_cap: float | None = None,
    ) -> float:
        """
        IRC 112:2020 Eq. B3.2 — effective width for a concentrated load on a
        cantilever solid slab.

        bef = 1.2 × a + b_1
        subject to bef ≤ l_parallel / 3  (IRC 112:2020 Cl. B3.2 proviso).

        Parameters
        ----------
        a           : distance of load CG from the face of cantilever support (m)
        b1          : tyre contact width + 2 × wearing course thickness (m)
        l_parallel  : length of cantilever slab parallel to the support (m);
                      typically the bridge longitudinal span — used for the
                      one-third limit.
        b_cap       : additional upper bound (m); pass overhang length if needed.
        """
        bef = 1.2 * a + b1
        bef = min(bef, l_parallel / 3.0)
        if b_cap is not None:
            bef = min(bef, b_cap)
        return bef
