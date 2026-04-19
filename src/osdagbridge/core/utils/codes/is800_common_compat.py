"""Minimal compatibility constants for the copied IS 800 helper module.

These values mirror the corresponding names from ``osdag_core.Common`` closely
enough for the local fallback copy of ``is800_2007.py`` to import and run in a
standalone OsdagBridge checkout.
"""

KEY_Plastic = "Plastic"
KEY_Compact = "Compact"
KEY_SemiCompact = "Semi-Compact"

KEY_DISP_SUPPORT1 = "Simply Supported"
KEY_DISP_SUPPORT2 = "Cantilever"

KEY_DISP_LOAD1 = "Normal"
KEY_DISP_LOAD2 = "Destabilizing"

Torsion_Restraint1 = "Fully Restrained"
Torsion_Restraint2 = "Partially Restrained-support connection"
Torsion_Restraint3 = "Partially Restrained-bearing support"

Warping_Restraint1 = "Both flanges fully restrained"
Warping_Restraint2 = "Compression flange fully restrained"
Warping_Restraint4 = "Compression flange partially restrained"
Warping_Restraint5 = "Warping not restrained in both flanges"

Support1 = "Continous, with lateral restraint to top flange"
Support2 = "Continous, with partial torsional restraint"
Support3 = "Continous, with lateral and torsional restraint"
Support4 = "Restrained laterally, torsionally and against rotation on flange"

Top1 = "Free"
Top2 = "Lateral restraint to top flange"
Top3 = "Torsional rwstraint"
Top4 = "Lateral and Torsional restraint"

KEY_DP_FAB_SHOP = "Shop Weld"
KEY_DP_FAB_FIELD = "Field weld"
