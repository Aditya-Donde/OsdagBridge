import os

# Force UTF-8 encoding in all subprocesses
os.environ["PYTHONIOENCODING"] = "utf-8"

import builtins
import contextlib
import logging
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Dict, List


# Safe print wrapper to avoid Unicode crashes
_original_print = print

def safe_print(*args, **kwargs):
    try:
        _original_print(*args, **kwargs)
    except UnicodeEncodeError:
        pass

builtins.print = safe_print

# Reconfigure Windows terminal encoding
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="ignore")
    sys.stderr.reconfigure(encoding="utf-8", errors="ignore")

from osdag_core.cli import _get_output_dictionary

from osdag_core.design_type.compression_member.compression_bolted import Compression_bolted
from osdag_core.design_type.compression_member.compression_welded import Compression_welded
from osdag_core.design_type.tension_member.tension_bolted import Tension_bolted
from osdag_core.design_type.tension_member.tension_welded import Tension_welded

MODULE_CLASS_MAP = {
    "Tension Member Design - Bolted to End Gusset": Tension_bolted,
    "Tension Member Design - Welded to End Gusset": Tension_welded,
    "Struts Bolted to End Gusset": Compression_bolted,
    "Struts Welded to End Gusset": Compression_welded,
}

# OUTPUT SUPPRESSION
@contextlib.contextmanager
def suppress_output(enabled: bool = True):
    if not enabled:
        yield
        return

    logging.disable(logging.CRITICAL)

    with open(os.devnull, "w", encoding="utf-8") as devnull:
        with contextlib.redirect_stdout(devnull):
            with contextlib.redirect_stderr(devnull):
                yield

    logging.disable(logging.NOTSET)

def run_calculation(design_dict: Dict[str, Any], quiet: bool = True) -> Dict[str, Any]:
    # Every subprocess needs UTF-8 again
    if sys.platform.startswith("win"):
        sys.stdout.reconfigure(encoding="utf-8", errors="ignore")
        sys.stderr.reconfigure(encoding="utf-8", errors="ignore")

    with suppress_output(quiet):
        module_name = design_dict.get("Module")
        module_class = MODULE_CLASS_MAP.get(module_name)

        if not module_class:
            raise ValueError(f"Unsupported module type: {module_name}")

        module_instance = module_class()
        module_instance.set_osdaglogger(None, None)

        try:
            validation_errors = module_instance.func_for_validation(design_dict)
        except Exception as exc:
            # Some section families are not implemented in osdag_core and blow
            # up mid-design (e.g. channels raise UnboundLocalError 'min_rad').
            # Report that as an un-designable section rather than losing the
            # result entirely — the caller shows it as a failed check.
            return {
                "design_status": False,
                "design_error": f"{type(exc).__name__}: {exc}",
            }

        if validation_errors:
            print(f"[Osdag] Validation errors: {validation_errors}")
            raise RuntimeError("Validation errors occurred during execution.")

        output_dict = _get_output_dictionary(module_instance)

        # On a failed design Osdag returns every value as "", with no flag to
        # distinguish "failed" from "not run". Carry the module's own pass/fail
        # status so consumers can report FAIL instead of N/A.
        output_dict["design_status"] = bool(module_instance.design_status)

        return output_dict

_forkserver_preloaded = False


def design_pool(max_workers: int) -> ProcessPoolExecutor:
    """Executor for osdag_core design checks with a thread-safe start method.

    The default fork start method is unsafe here: the design pipeline runs on a
    QThread while the GUI thread spins the Qt event loop, and a fork taken at that
    moment inherits mutexes locked by other threads — the child deadlocks before it
    ever reaches run_calculation (observed hang in stage 7).

    forkserver avoids that (the server is launched via fork+exec, so workers fork
    from its clean single-threaded state) while staying fast: this module is
    preloaded into the server once, so every worker starts with osdag_core already
    imported and shares those pages copy-on-write. Windows has no forkserver and
    falls back to spawn — its default start method anyway.
    """
    import multiprocessing
    try:
        ctx = multiprocessing.get_context("forkserver")
        global _forkserver_preloaded
        if not _forkserver_preloaded:
            ctx.set_forkserver_preload(["osdagbridge.core.utils.connect"])
            _forkserver_preloaded = True
    except ValueError:
        ctx = multiprocessing.get_context("spawn")
    return ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx)


def run_parallel_designs(design_dicts: List[Dict[str, Any]], quiet: bool = True) -> List[Dict[str, Any]]:
    cpu_count = os.cpu_count() or 4
    max_workers = min(cpu_count, len(design_dicts))

    with design_pool(max_workers) as executor:
        futures = [
            executor.submit(run_calculation, design_dict, quiet) 
            for design_dict in design_dicts
        ]
        results = [future.result() for future in futures]

    return results

# TENSION BOLTED
design_dict_tension_bolted = {
    "Bolt.Bolt_Hole_Type": "Standard",
    "Bolt.Diameter": ["8", "10", "12", "16", "20", "24", "30", "36", "42", "48", "56", "64", "14", "18", "22", "27", "33", "39", "45", "52", "60"],
    "Bolt.Grade": ["3.6", "4.6", "4.8", "5.6", "5.8", "6.8", "8.8", "9.8", "10.9", "12.9"],
    "Bolt.Slip_Factor": "0.3",
    "Bolt.TensionType": "Pre-tensioned",
    "Bolt.Type": "Bearing Bolt",
    "Conn_Location": "Long Leg",
    "Connector.Material": "E 250 (Fe 410 W)A",
    "Connector.Plate.Thickness_List": ["8", "10", "12", "14", "16", "18", "20", "22", "25", "28", "32", "36", "40", "45", "50", "56", "63", "75", "80", "90", "100", "110", "120"],
    "Design.Design_Method": "Limit State Design",
    "Detailing.Corrosive_Influences": "No",
    "Detailing.Edge_type": "Sheared or hand flame cut",
    "Detailing.Gap": "10",
    "Load.Axial": "4",
    "Material": "E 250 (Fe 410 W)A",
    "Member.Designation": [
        "20 x 20 x 3",
        "20 x 20 x 4",
        "25 x 25 x 3",
        "25 x 25 x 4",
        "25 x 25 x 5",
        "30 x 30 x 3",  
        "30 x 30 x 4",
        "30 x 30 x 5",
        "35 x 35 x 3",
        "35 x 35 x 4",
        "35 x 35 x 5",
        "35 x 35 x 6",
        "40 x 40 x 3",
        "40 x 40 x 4",
        "40 x 40 x 5",
        "40 x 40 x 6",
        "45 x 45 x 3",
        "45 x 45 x 4",
        "45 x 45 x 5",
        "45 x 45 x 6",
        "50 x 50 x 3",
        "50 x 50 x 4",
        "50 x 50 x 5",
        "50 x 50 x 6",
        "55 x 55 x 4",
        "55 x 55 x 5",
        "55 x 55 x 6",
        "55 x 55 x 8",
        "60 x 60 x 4",
        "60 x 60 x 5",
        "60 x 60 x 6",
        "60 x 60 x 8",
        "65 x 65 x 4",
        "65 x 65 x 5",
        "65 x 65 x 6",
        "65 x 65 x 8",
        "70 x 70 x 5",
        "70 x 70 x 6",
        "70 x 70 x 8",
        "70 x 70 x 10",
        "75 x 75 x 5",
        "75 x 75 x 6",
        "75 x 75 x 8",
        "75 x 75 x 10",
        "80 x 80 x 6",
        "80 x 80 x 8",
        "80 x 80 x 10",
        "80 x 80 x 12",
        "90 x 90 x 6",
        "90 x 90 x 8",
        "90 x 90 x 10",
        "90 x 90 x 12",
        "100 x 100 x 6",
        "100 x 100 x 8",
        "100 x 100 x 10",
        "100 x 100 x 12",
        "110 x 110 x 8",
        "110 x 110 x 10",
        "110 x 110 x 12",
        "110 x 110 x 16",
        # "130 x 130 x 8",
        # "130 x 130 x 10",
        # "130 x 130 x 12",
        # "130 x 130 x 16",
        # "150 x 150 x 10",
        # "150 x 150 x 12",
        # "150 x 150 x 16",
        # "150 x 150 x 20",
        # "200 x 200 x 12",
        # "200 x 200 x 16",
        # "200 x 200 x 20",
        # "200 x 200 x 25",
        # "50 x 50 x 7",
        # "50 x 50 x 8",
        # "55 x 55 x 10",
        # "60 x 60 x 10",
        # "65 x 65 x 10",
        # "70 x 70 x 7",
        # "100 x 100 x 7",
        # "100 x 100 x 15",
        # "120 x 120 x 8",
        # "120 x 120 x 10",
        # "120 x 120 x 12",
        # "120 x 120 x 15",
        # "130 x 130 x 9",
        # "150 x 150 x 15",
        # "150 x 150 x 18",
        # "180 x 180 x 15",
        # "180 x 180 x 18",
        # "180 x 180 x 20",
        # "200 x 200 x 24",
        # "30 x 20 x 3",
        # "30 x 20 x 4",
        # "30 x 20 x 5",
        # "40 x 25 x 3",
        # "40 x 25 x 4",
        # "40 x 25 x 5",
        # "40 x 25 x 6",
        # "45 x 30 x 3",
        # "45 x 30 x 4",
        # "45 x 30 x 5",
        # "45 x 30 x 6",
        # "50 x 30 x 3",
        # "50 x 30 x 4",
        # "50 x 30 x 5",
        # "50 x 30 x 6",
        # "60 x 40 x 5",
        # "60 x 40 x 6",
        # "60 x 40 x 8",
        # "65 x 45 x 5",
        # "65 x 45 x 6",
        # "65 x 45 x 8",
        # "70 x 45 x 5",
        # "70 x 45 x 6",
        # "70 x 45 x 8",
        # "70 x 45 x 10",
        # "75 x 50 x 5",
        # "75 x 50 x 6",
        # "75 x 50 x 8",
        # "75 x 50 x 10",
        # "80 x 50 x 5",
        # "80 x 50 x 6",
        # "80 x 50 x 8",
        # "80 x 50 x 10",
        # "90 x 60 x 6",
        # "90 x 60 x 8",
        # "90 x 60 x 10",
        # "90 x 60 x 12",
        # "100 x 65 x 6",
        # "100 x 65 x 8",
        # "100 x 65 x 10",
        # "100 x 75 x 6",
        # "100 x 75 x 8",
        # "100 x 75 x 10",
        # "100 x 75 x 12",
        # "125 x 75 x 6",
        # "125 x 75 x 8",
        # "125 x 75 x 10",
        # "125 x 95 x 6",
        # "125 x 95 x 8",
        # "125 x 95 x 10",
        # "125 x 95 x 12",
        # "150 x 115 x 8",
        # "150 x 115 x 10",
        # "150 x 115 x 12",
        # "150 x 115 x 16",
        # "200 x 100 x 10",
        # "200 x 100 x 12",
        # "200 x 100 x 16",
        # "200 x 150 x 10",
        # "200 x 150 x 12",
        # "200 x 150 x 16",
        # "200 x 150 x 20",
        # "40 x 20 x 3",
        # "40 x 20 x 4",
        # "40 x 20 x 5",
        # "60 x 30 x 5",
        # "60 x 30 x 6",
        # "60 x 40 x 7",
        # "65 x 50 x 5",
        # "65 x 50 x 6",
        # "65 x 50 x 7",
        # "65 x 50 x 8",
        # "70 x 50 x 5",
        # "70 x 50 x 6",
        # "70 x 50 x 7",
        # "70 x 50 x 8",
        # "75 x 50 x 7",
        # "80 x 40 x 5",
        # "80 x 40 x 6",
        # "80 x 40 x 7",
        # "80 x 40 x 8",
        # "80 x 60 x 6",
        # "80 x 60 x 7",
        # "80 x 60 x 8",
        # "90 x 65 x 6",
        # "90 x 65 x 7",
        # "90 x 65 x 8",
        # "90 x 65 x 10",
        # "100 x 50 x 6",
        # "100 x 50 x 7",
        # "100 x 50 x 8",
        # "100 x 50 x 10",
        # "100 x 65 x 7",
        # "120 x 80 x 8",
        # "120 x 80 x 10",
        # "120 x 80 x 12",
        # "125 x 75 x 12",
        # "135 x 65 x 8",
        # "135 x 65 x 10",
        # "135 x 65 x 12",
        # "150 x 75 x 9",
        # "150 x 75 x 15",
        # "150 x 90 x 10",
        # "150 x 90 x 12",
        # "150 x 90 x 15",
        # "200 x 100 x 15",
        # "200 x 150 x 15",
        # "200 x 150 x 18",
    ],
    "Member.Length": "1500",
    "Member.Material": "E 250 (Fe 410 W)A",
    "Member.Profile": "Back to Back Angles",
    "Module": "Tension Member Design - Bolted to End Gusset",
    "out_titles_status": [1, 1, 1, 1, 1],
}

# TENSION WELDED
design_dict_tension_welded = {
    "Conn_Location": "Long Leg",
    "Connector.Material": "E 165 (Fe 290)",
    "Connector.Plate.Thickness_List": ["8", "10", "12"],
    "Design.Design_Method": "Limit State Design",
    "Load.Axial": "5",
    "Material": "E 165 (Fe 290)",
    "Member.Designation": [
        "20 x 20 x 3",
        "25 x 25 x 3",
    ],
    "Member.Length": "500",
    "Member.Material": "E 165 (Fe 290)",
    "Member.Profile": "Angles",
    "Module": "Tension Member Design - Welded to End Gusset",
    "Weld.Fab": "Shop Weld",
    "Weld.Material_Grade_OverWrite": "290",
    "out_titles_status": [1, 1, 1, 1, 1],
}

# STRUTS BOLTED
design_dict_struts_bolted = {
    "Bolt.Bolt_Hole_Type": "Standard",
    "Bolt.Diameter": ["8", "10", "12", "16", "20", "24", "30", "36", "42", "48", "56", "64", "14", "18", "22", "27", "33", "39", "45", "52", "60"
],
    "Bolt.Grade": ["3.6", "4.6", "4.8", "5.6", "5.8", "6.8", "8.8", "9.8", "10.9", "12.9"],
    "Bolt.Slip_Factor": "0.3",
    "Bolt.TensionType": "Pre-tensioned",
    "Bolt.Type": "Bearing Bolt",
    "Conn_Location": "Long Leg",
    "Connector.Material": "E 250 (Fe 410 W)A",
    "Connector.Plate.Thickness_List": ["8", "10", "12", "16", "18", "20", "22", "25", "28", "32", "36", "40", "45", "50", "56", "63", "75", "80", "90", "100", "110", "120"],
    "Design.Design_Method": "Limit State Design",
    "Detailing.Corrosive_Influences": "No",
    "Detailing.Edge_type": "Sheared or hand flame cut",
    "Detailing.Gap": "10",
    "End_1": "Fixed",
    "End_2": "Fixed",
    "Load.Axial": "10",
    "Material": "E 250 (Fe 410 W)A",
    "Member.Designation": [
        "20 x 20 x 3",
        "20 x 20 x 4",
        "25 x 25 x 3",
        "25 x 25 x 4",
        "25 x 25 x 5",
        "30 x 30 x 3",
        "30 x 30 x 4",
        "30 x 30 x 5",
        "35 x 35 x 3",
        "35 x 35 x 4",
        "35 x 35 x 5",
        "35 x 35 x 6",
        "40 x 40 x 3",
        "40 x 40 x 4",
        "40 x 40 x 5",
        "40 x 40 x 6",
        "45 x 45 x 3",
        "45 x 45 x 4",
        "45 x 45 x 5",
        "45 x 45 x 6",
        "50 x 50 x 3",
        "50 x 50 x 4",
        "50 x 50 x 5",
        "50 x 50 x 6",
        "55 x 55 x 4",
        "55 x 55 x 5",
        "55 x 55 x 6",
        "55 x 55 x 8",
        "60 x 60 x 4",
        "60 x 60 x 5",
        "60 x 60 x 6",
        "60 x 60 x 8",
        "65 x 65 x 4",
        "65 x 65 x 5",
        "65 x 65 x 6",
        "65 x 65 x 8",
        "70 x 70 x 5",
        "70 x 70 x 6",
        "70 x 70 x 8",
        "70 x 70 x 10",
        "75 x 75 x 5",
        "75 x 75 x 6",
        "75 x 75 x 8",
        "75 x 75 x 10",
        "80 x 80 x 6",
        "80 x 80 x 8",
        "80 x 80 x 10",
        "80 x 80 x 12",
        "90 x 90 x 6",
        "90 x 90 x 8",
        "90 x 90 x 10",
        "90 x 90 x 12",
        "100 x 100 x 6",
        "100 x 100 x 8",
        "100 x 100 x 10",
        "100 x 100 x 12",
        "110 x 110 x 8",
        "110 x 110 x 10",
        "110 x 110 x 12",
        "110 x 110 x 16",
        # "130 x 130 x 8",
        # "130 x 130 x 10",
        # "130 x 130 x 12",
        # "130 x 130 x 16",
        # "150 x 150 x 10",
        # "150 x 150 x 12",
        # "150 x 150 x 16",
        # "150 x 150 x 20",
        # "200 x 200 x 12",
        # "200 x 200 x 16",
        # "200 x 200 x 20",
        # "200 x 200 x 25",
        # "50 x 50 x 7",
        # "50 x 50 x 8",
        # "55 x 55 x 10",
        # "60 x 60 x 10",
        # "65 x 65 x 10",
        # "70 x 70 x 7",
        # "100 x 100 x 7",
        # "100 x 100 x 15",
        # "120 x 120 x 8",
        # "120 x 120 x 10",
        # "120 x 120 x 12",
        # "120 x 120 x 15",
        # "130 x 130 x 9",
        # "150 x 150 x 15",
        # "150 x 150 x 18",
        # "180 x 180 x 15",
        # "180 x 180 x 18",
        # "180 x 180 x 20",
        # "200 x 200 x 24",
        # "30 x 20 x 3",
        # "30 x 20 x 4",
        # "30 x 20 x 5",
        # "40 x 25 x 3",
        # "40 x 25 x 4",
        # "40 x 25 x 5",
        # "40 x 25 x 6",
        # "45 x 30 x 3",
        # "45 x 30 x 4",
        # "45 x 30 x 5",
        # "45 x 30 x 6",
        # "50 x 30 x 3",
        # "50 x 30 x 4",
        # "50 x 30 x 5",
        # "50 x 30 x 6",
        # "60 x 40 x 5",
        # "60 x 40 x 6",
        # "60 x 40 x 8",
        # "65 x 45 x 5",
        # "65 x 45 x 6",
        # "65 x 45 x 8",
        # "70 x 45 x 5",
        # "70 x 45 x 6",
        # "70 x 45 x 8",
        # "70 x 45 x 10",
        # "75 x 50 x 5",
        # "75 x 50 x 6",
        # "75 x 50 x 8",
        # "75 x 50 x 10",
        # "80 x 50 x 5",
        # "80 x 50 x 6",
        # "80 x 50 x 8",
        # "80 x 50 x 10",
        # "90 x 60 x 6",
        # "90 x 60 x 8",
        # "90 x 60 x 10",
        # "90 x 60 x 12",
        # "100 x 65 x 6",
        # "100 x 65 x 8",
        # "100 x 65 x 10",
        # "100 x 75 x 6",
        # "100 x 75 x 8",
        # "100 x 75 x 10",
        # "100 x 75 x 12",
        # "125 x 75 x 6",
        # "125 x 75 x 8",
        # "125 x 75 x 10",
        # "125 x 95 x 6",
        # "125 x 95 x 8",
        # "125 x 95 x 10",
        # "125 x 95 x 12",
        # "150 x 115 x 8",
        # "150 x 115 x 10",
        # "150 x 115 x 12",
        # "150 x 115 x 16",
        # "200 x 100 x 10",
        # "200 x 100 x 12",
        # "200 x 100 x 16",
        # "200 x 150 x 10",
        # "200 x 150 x 12",
        # "200 x 150 x 16",
        # "200 x 150 x 20",
        # "40 x 20 x 3",
        # "40 x 20 x 4",
        # "40 x 20 x 5",
        # "60 x 30 x 5",
        # "60 x 30 x 6",
        # "60 x 40 x 7",
        # "65 x 50 x 5",
        # "65 x 50 x 6",
        # "65 x 50 x 7",
        # "65 x 50 x 8",
        # "70 x 50 x 5",
        # "70 x 50 x 6",
        # "70 x 50 x 7",
        # "70 x 50 x 8",
        # "75 x 50 x 7",
        # "80 x 40 x 5",
        # "80 x 40 x 6",
        # "80 x 40 x 7",
        # "80 x 40 x 8",
        # "80 x 60 x 6",
        # "80 x 60 x 7",
        # "80 x 60 x 8",
        # "90 x 65 x 6",
        # "90 x 65 x 7",
        # "90 x 65 x 8",
        # "90 x 65 x 10",
        # "100 x 50 x 6",
        # "100 x 50 x 7",
        # "100 x 50 x 8",
        # "100 x 50 x 10",
        # "100 x 65 x 7",
        # "120 x 80 x 8",
        # "120 x 80 x 10",
        # "120 x 80 x 12",
        # "125 x 75 x 12",
        # "135 x 65 x 8",
        # "135 x 65 x 10",
        # "135 x 65 x 12",
        # "150 x 75 x 9",
        # "150 x 75 x 15",
        # "150 x 90 x 10",
        # "150 x 90 x 12",
        # "150 x 90 x 15",
        # "200 x 100 x 15",
        # "200 x 150 x 15",
        # "200 x 150 x 18",
    ],
    "Member.Length": "1500",
    "Member.Material": "E 250 (Fe 410 W)A",
    "Member.Profile": "Back to Back Angles",
    "Module": "Struts Bolted to End Gusset",
    "is_leg_loaded": "Yes",
}

# STRUTS WELDED
design_dict_struts_welded = {
    " In_Plane": "1.0",
    " Out_of_Plane": "1.0",
    "Bolt.Number": "1.0",
    "Conn_Location": "Long Leg",
    "Connector.Plate.Thickness_List": "8",
    "Design.Design_Method": "Limit State Design",
    "Effective.Area_Para": "1.0",
    "End_1": "Fixed",
    "End_2": "Fixed",
    "Load.Axial": "9",
    "Load.Type": "Concentric Load",
    "Material": "E 165 (Fe 290)",
    "Member.Designation": [
        "25 x 25 x 3",
        "40 x 40 x 3",
    ],
    "Member.Length": "900",
    "Member.Material": "E 165 (Fe 290)",
    "Member.Profile": "Angles",
    "Module": "Struts Welded to End Gusset",
    "Optimum.AllowUR": "1.0",
    "Weld.Fab": "Shop Weld",
    "Weld.Material_Grade_OverWrite": "290",
    "out_titles_status": [1, 1, 1, 1, 1],
}

# STANDALONE TESTING
if __name__ == "__main__":
    """
    Standalone testing:
    Runs 10 parallel Osdag designs
    using ProcessPoolExecutor
    """

    design_dicts = [
        design_dict_tension_bolted,
        design_dict_tension_welded,
        design_dict_struts_bolted,
        design_dict_struts_welded,
    ]

    start_time = time.perf_counter()
    results = run_parallel_designs(design_dicts, quiet=True)
    end_time = time.perf_counter()
    total_time = end_time - start_time

    print("\nParallel execution completed\n")
    print(f"Total designs : {len(results)}")
    print(f"Execution time: {total_time:.4f} seconds")
    print(f"Average/design: {total_time / len(results):.4f} seconds")
    print("\nSample outputs:\n")

    for index, result in enumerate(results):
        print(f"\nDesign {index + 1}:\n")
        print(result)