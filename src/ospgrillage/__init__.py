import os as _os
import sys as _sys
import warnings as _warnings


def _register_conda_dll_directories():
    """Add the active conda environment's native DLL folders to the Windows DLL
    search path.

    Installer-launched apps (e.g. a conda-constructor build) do not "activate"
    the environment, so ``<prefix>/Library/bin`` — where the BLAS/LAPACK backend
    (MKL ``mkl_rt``/``libblas`` or OpenBLAS) lives — is absent from the DLL search
    path. numpy/scipy/openseespy then import fine but crash the whole process
    with a native ``ERROR_MOD_NOT_FOUND`` (``0xc06d007f``) the first time they
    delay-load LAPACK (e.g. ``numpy.linalg.lstsq`` during grillage meshing).
    Registering these directories before numpy is imported prevents that crash.
    No-op on non-Windows platforms and in already-activated environments.
    """
    if _os.name != "nt":
        return
    prefix = _sys.prefix
    candidates = [
        _os.path.join(prefix, "Library", "bin"),
        _os.path.join(prefix, "Library", "mingw-w64", "bin"),
        _os.path.join(prefix, "Library", "usr", "bin"),
        _os.path.join(prefix, "DLLs"),
        prefix,
    ]
    path_entries = _os.environ.get("PATH", "").split(_os.pathsep)
    for path in candidates:
        if not _os.path.isdir(path):
            continue
        try:
            _os.add_dll_directory(path)
        except (OSError, AttributeError):
            pass
        # Some native libraries resolve dependents via PATH rather than the
        # secure add_dll_directory list; prepend for completeness.
        if path not in path_entries:
            _os.environ["PATH"] = path + _os.pathsep + _os.environ.get("PATH", "")
            path_entries.insert(0, path)


_register_conda_dll_directories()

import numpy as np  # re-exported: tests and users access ospgrillage.np
import openseespy.opensees as ops  # re-exported: tests and users access ospgrillage.ops
import opsvis as opsv  # used internally by postprocessing (section_force_distribution_3d)
import matplotlib.pyplot as plt  # re-exported: users access ospgrillage.plt
from ospgrillage.utils import *
from ospgrillage.mesh import *
from ospgrillage.load import *
from ospgrillage.material import *
from ospgrillage.members import *
from ospgrillage.osp_grillage import *
from ospgrillage.postprocessing import *

__version__ = "0.6.0"

# Explicit public API — everything a user should access from `import ospgrillage`
__all__ = [
    "__version__",
    # Grillage model
    "OspGrillage",
    "OspGrillageBeam",
    "OspGrillageShell",
    "create_grillage",
    # Members & sections
    "GrillageMember",
    "Section",
    "create_member",
    "create_section",
    # Materials
    "Material",
    "create_material",
    # Loads
    "LoadCase",
    "LoadModel",
    "Loads",
    "MovingLoad",
    "NodalLoad",
    "NodeForces",
    "PatchLoading",
    "Path",
    "PointLoad",
    "LineLoading",
    "LoadVertex",
    "LoadPoint",  # deprecated alias for LoadVertex
    "CompoundLoad",
    "Line",
    "ShapeFunction",
    "create_load_vertex",
    "create_load",
    "create_load_case",
    "create_load_model",
    "create_moving_load",
    "create_moving_path",
    "create_compound_load",
    # Mesh / geometry
    "Point",
    "Mesh",
    "create_point",
    # Post-processing & plotting
    "Envelope",
    "Members",
    "PostProcessor",
    "create_envelope",
    "model_proxy_from_results",
    "plot_force",
    "plot_bmd",
    "plot_sfd",
    "plot_tmd",
    "plot_def",
    "plot_model",
    "plot_srf",
]


# ---------------------------------------------------------------------------
# Backwards-compatible lazy access for deprecated re-exports
# ---------------------------------------------------------------------------
# Hide opsv from the public namespace — it is imported above for internal use
# by postprocessing.py but should not be accessed as og.opsv by users.
def __getattr__(name):
    if name == "opsv":
        _warnings.warn(
            "og.opsv is deprecated — use og.plot_model() for mesh visualisation. "
            "Direct opsv access will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2,
        )
        return opsv
    if name == "opsplt":
        _warnings.warn(
            "og.opsplt is deprecated — use og.plot_model() for mesh visualisation. "
            "vfo/opsplt will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            import vfo.vfo as _opsplt

            return _opsplt
        except ImportError:
            raise ImportError(
                "vfo is no longer a required dependency. "
                "Install it with: pip install vfo"
            ) from None
    raise AttributeError(f"module 'ospgrillage' has no attribute {name!r}")
