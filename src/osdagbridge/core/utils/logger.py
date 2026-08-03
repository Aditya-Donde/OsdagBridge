"""Bridge analysis and design structured logger."""
import logging
import time
from datetime import datetime
from typing import Callable, Optional, List

from osdagbridge.core.utils.common import KEY_SD_VERDICT, KEY_DD_VERDICT

log = logging.getLogger("osdagbridge")
_SEP = "-" * 45

class BridgeLogger:
    """
    Singleton logger callback bridge for the plate-girder design pipeline.
    Routes log messages to the UI without backend depending on Qt.
    """
    STAGE_MAP = [
        ("1", "INPUT VALIDATION"),
        ("2", "BRIDGE LAYOUT SOLVING"),
        ("3", "GRILLAGE SETUP"),
        ("4A", "DEAD LOAD APPLICATION"),
        ("4B", "LIVE LOAD APPLICATION"),
        ("4C", "WIND LOAD APPLICATION"),
        ("4D", "TEMPERATURE LOAD APPLICATION"),
        ("4E", "SEISMIC LOAD APPLICATION"),
        ("4F", "LOAD COMBINATION ENVELOPE"),
        ("4G", "STRUCTURAL ANALYSIS"),
        ("5", "GIRDER DESIGN CHECKS"),
        ("6", "DECK SLAB DESIGN"),
        ("7", "TRANSVERSE MEMBER DESIGN"),
        ("8", "3D CAD & DRAWING GENERATION"),
    ]

    _instance: Optional["BridgeLogger"] = None

    def __init__(self) -> None:
        self._callbacks: List[Callable[[str, str], None]] = []
        self._cancel_pollers: List[Callable[[], bool]] = []
        self._cancelled: bool = False
        self._start_time: float = 0.0
        # History of "success" (green) log lines from the most recent run.
        # Consumed by the report generator to build the "Design Log" chapter.
        self._success_log: List[str] = []

    @classmethod
    def get_instance(cls) -> "BridgeLogger":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_callback(self, callback: Callable[[str, str], None]) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[str, str], None]) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def add_cancel_poller(self, poller: Callable[[], bool]) -> None:
        if poller not in self._cancel_pollers:
            self._cancel_pollers.append(poller)

    def remove_cancel_poller(self, poller: Callable[[], bool]) -> None:
        if poller in self._cancel_pollers:
            self._cancel_pollers.remove(poller)

    @staticmethod
    def _ts() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _emit(self, raw: str, level: str = "info") -> None:
        log.info(raw)
        if level == "success":
            self._success_log.append(raw)
        for cb in list(self._callbacks):
            try:
                cb(raw, level)
            except Exception:
                pass

    def _blank(self) -> None:
        log.info("")  # Visual separator in raw Python log only; not sent to UI callbacks

    def info(self, message: str) -> None:
        self._emit(f"[{self._ts()}]   {message}", "info")

    def success(self, message: str) -> None:
        self._emit(f"[{self._ts()}]   {message}", "success")

    def warning(self, message: str) -> None:
        self._emit(f"[{self._ts()}]   WARNING : {message}", "warning")

    def error(self, message: str) -> None:
        self._emit(f"[{self._ts()}]   ERROR : {message}", "error")

    # Per-category display label + remedy. Keyed by the same check keys stored in
    # the verdict dict / output_dict (common.KEY_CHECK_* string values). The remedy
    # is printed only when that category fails — see girder_verdict().
    _VERDICT_CHECKS = {
        "flexure":          ("Flexure",
                             "Increase girder depth D or flange area (b_f x t_f)."),
        "shear":            ("Shear",
                             "Increase web thickness t_w or depth D; if buckling governs, reduce stiffener spacing."),
        "interaction":      ("Interaction",
                             "Relieve the dominant term: thicken the web, or deepen the girder / thicken flanges."),
        "ltb":              ("Lateral Torsional Buckling",
                             "Reduce cross-bracing spacing (shorter L_LT), or widen the compression flange."),
        "shear_long_trans": ("Longitudinal Shear",
                             "Reduce stud longitudinal spacing, or increase stud diameter / count."),
        "fatigue":          ("Fatigue",
                             "Lower the stress range: deeper girder / thicker flanges, or a better weld detail."),
        "stress":           ("Stress Limitation",
                             "Increase the section modulus Z (deeper girder or thicker flanges)."),
        "deflection":       ("Deflection",
                             "Increase girder depth D or moment of inertia I_z."),
    }

    def girder_verdict(self, output_dict: dict) -> None:
        """Print the girder verdict read from output_dict[KEY_SD_VERDICT].

        Passing categories print one green line; failing categories print a red
        line then their remedy. Remedies never print for a passing check.
        """
        verdict = (output_dict or {}).get(KEY_SD_VERDICT) or {}
        if not verdict:
            return

        status = verdict.get("status", "FAIL")
        max_ur = verdict.get("max_ur", 0.0)
        headline = f"GIRDER : {status}  (max UR = {max_ur:.3f})"
        self._emit(f"[{self._ts()}]   {headline}",
                   "success" if status == "PASS" else "error")

        for key, (label, remedy) in self._VERDICT_CHECKS.items():
            row = verdict.get(key)
            if not row:
                continue
            ur = row.get("ur", 0.0)
            if row.get("pass", True):
                self._emit(f"[{self._ts()}]     PASS : {label} (UR = {ur:.3f})",
                           "success")
            else:
                self._emit(f"[{self._ts()}]     FAIL : {label} (UR = {ur:.3f})",
                           "error")
                self._emit(f"[{self._ts()}]       -> {remedy}", "warning")

    # Per-check display label + remedy for the deck verdict. Keyed by the deck
    # check keys stored in the verdict dict (common.KEY_DD_CHECK_* string values).
    _DECK_VERDICT_CHECKS = {
        "deck.flexure":            ("ULS Flexure",
                                    "Increase the deck thickness, or raise the upper bar-diameter bound so a larger reinforcement area can be provided."),
        "deck.oneway_shear":       ("One-Way Shear",
                                    "Increase the deck thickness: v_Rd,c grows with the effective depth d, and the reinforcement ratio is capped at 0.02 so extra steel cannot raise capacity beyond that."),
        "deck.punching_shear":     ("Punching Shear",
                                    "Increase the deck thickness (deeper d and longer control perimeter), or raise the concrete grade."),
        "deck.sls_stress_concrete":("SLS Concrete Stress",
                                    "Raise the concrete grade (limit is 0.48 f_ck) or increase the deck thickness."),
        "deck.sls_stress_reinforcement":("SLS Reinforcement Stress",
                                    "Increase the deck thickness, or raise the upper bar-diameter bound so more tension steel can be provided (limit is 0.80 f_y)."),
        "deck.crack_width":        ("Crack Width",
                                    "Use smaller bars at closer spacing for the same steel area, reduce the clear cover, or raise the concrete grade."),
        "deck.composite_transverse_shear":("Composite Transverse Shear",
                                    "Increase the transverse reinforcement crossing the shear plane, the deck thickness, or the concrete grade (IRC 22:2015 Cl.606.10)."),
        "deck.composite_crack_control":("Composite Crack Control",
                                    "Increase the top-mat reinforcement over the girder to meet the IRC 22:2015 Cl.604.4 minimum area."),
    }

    def deck_verdict(self, output_dict: dict) -> None:
        """Print the deck verdict read from output_dict[KEY_DD_VERDICT].

        Passing checks print one green line; failing checks print a red line
        then their remedy. Remedies never print for a passing check.
        """
        verdict = (output_dict or {}).get(KEY_DD_VERDICT) or {}
        if not verdict:
            return

        status = verdict.get("status", "FAIL")
        max_ur = verdict.get("max_ur", 0.0)
        self._emit(f"[{self._ts()}]   DECK SLAB : {status}  (max UR = {max_ur:.3f})",
                   "success" if status == "PASS" else "error")

        for key, (label, remedy) in self._DECK_VERDICT_CHECKS.items():
            row = verdict.get(key)
            if not row:
                continue
            ur = row.get("ur", 0.0)
            if row.get("pass", True):
                self._emit(f"[{self._ts()}]     PASS : {label} (UR = {ur:.3f})",
                           "success")
            else:
                self._emit(f"[{self._ts()}]     FAIL : {label} (UR = {ur:.3f})",
                           "error")
                self._emit(f"[{self._ts()}]       -> {remedy}", "warning")

    def final_verdict(self, output_dict: dict) -> None:
        """Print one combined verdict for the girder and deck designs.

        Lists every failing check from either section, worst UR first, each with
        its remedy. When nothing fails, prints a single PASS line — passing
        checks are not repeated here; girder_verdict() / deck_verdict() already
        give the per-section breakdown.
        """
        out = output_dict or {}
        sections = (
            ("Girder", out.get(KEY_SD_VERDICT) or {}, self._VERDICT_CHECKS),
            ("Deck",   out.get(KEY_DD_VERDICT) or {}, self._DECK_VERDICT_CHECKS),
        )
        if not any(verdict for _, verdict, _ in sections):
            return                       # neither design ran — nothing to report

        failures = []                    # (section, label, ur, remedy)
        failed_sections = []
        max_ur = 0.0
        for name, verdict, checks in sections:
            if not verdict:
                continue
            max_ur = max(max_ur, float(verdict.get("max_ur", 0.0)))
            if verdict.get("status", "FAIL") != "PASS":
                failed_sections.append(name)
            for key, (label, remedy) in checks.items():
                row = verdict.get(key)
                if row and not row.get("pass", True):
                    failures.append((name, label, float(row.get("ur", 0.0)), remedy))

        failures.sort(key=lambda f: f[2], reverse=True)   # worst offender first

        self._blank()
        if not failures and not failed_sections:
            self._emit(f"[{self._ts()}]   FINAL VERDICT : PASS  (max UR = {max_ur:.3f})",
                       "success")
            self._emit(f"[{self._ts()}]     All girder and deck design checks are satisfied.",
                       "success")
            return

        self._emit(f"[{self._ts()}]   FINAL VERDICT : FAIL  (max UR = {max_ur:.3f})", "error")
        for name, label, ur, remedy in failures:
            self._emit(f"[{self._ts()}]     FAIL : {name} - {label} (UR = {ur:.3f})", "error")
            self._emit(f"[{self._ts()}]       -> {remedy}", "warning")
        if not failures:
            # Section status says FAIL but no individual check is flagged — report
            # it rather than printing a bare FAIL headline with nothing under it.
            self._emit(f"[{self._ts()}]     {' and '.join(failed_sections)} design reported "
                       f"FAIL with no failing check listed.", "error")

    def get_success_log(self) -> List[str]:
        """Return the green (success) log lines captured during the last run."""
        return list(self._success_log)

    def analysis_start(self) -> None:
        self._cancelled = False
        self._start_time = time.time()
        self._success_log = []  # start a fresh design log for this run
        self._blank()
        self._emit(f"[{self._ts()}] {_SEP} S T A R T I N G   A N A L Y S I S", "info")
        self._blank()

    def analysis_complete(self) -> None:
        elapsed = time.time() - self._start_time
        self._blank()
        self._emit(f"[{self._ts()}] {_SEP} A N A L Y S I S   C O M P L E T E", "success")
        self._emit(f"[{self._ts()}]   TOTAL SOLUTION TIME .. : {elapsed:.2f} [SEC]", "success")
        self._emit(f"[{self._ts()}] {'=' * 60}", "success")
        self._blank()

    def analysis_failed(self, reason: str) -> None:
        elapsed = time.time() - self._start_time
        self._blank()
        self._emit(f"[{self._ts()}] {_SEP} A N A L Y S I S   F A I L E D", "error")
        self._emit(f"[{self._ts()}]   REASON  .. : {reason}", "error")
        self._emit(f"[{self._ts()}]   ELAPSED .. : {elapsed:.2f} [SEC]", "error")
        self._blank()

    def stage_start(self, stage: str) -> None:
        idx = next((i for i, (sid, name) in enumerate(self.STAGE_MAP) if sid == stage), -1)
        name = self._stage_name(stage)
        self._blank()
        
        if idx != -1:
            pct = int(idx / len(self.STAGE_MAP) * 100)
            self._emit(
                f"[{self._ts()}]   STAGE {stage} : {name}  [{pct}%]",
                "info"
            )
        else:
            self._emit(
                f"[{self._ts()}]   STAGE {stage} : {name}",
                "info"
            )
            
        if idx != -1:
            self.stage_progress(idx)

    def stage_complete(self, stage: str) -> None:
        idx = next((i for i, (sid, name) in enumerate(self.STAGE_MAP) if sid == stage), -1)
        name = self._stage_name(stage)
        
        if idx != -1:
            pct = int((idx + 1) / len(self.STAGE_MAP) * 100)
            self._emit(
                f"[{self._ts()}]   STAGE {stage} COMPLETE [{pct}%] : {name}",
                "success"
            )
            self.stage_progress(idx + 1)
        else:
            self._emit(
                f"[{self._ts()}]   STAGE {stage} COMPLETE : {name}",
                "success"
            )

    def stage_progress(self, stages_done: int) -> None:
        pct = int(stages_done / len(self.STAGE_MAP) * 100)
        self._emit(f"__progress__{pct}", "progress")
        
    def sub_step(self, message: str) -> None:
        """Log a named sub-step."""
        self._emit(f"[{self._ts()}]     {message}", "info")

    def cancel(self) -> None:
        self._cancelled = True

    def check_cancel(self) -> None:
        if any(poller() for poller in list(self._cancel_pollers)):
            self._cancelled = True
            
        if self._cancelled:
            self._cancelled = False
            raise RuntimeError("Analysis cancelled by user")

    def _stage_name(self, stage: str) -> str:
        for sid, name in self.STAGE_MAP:
            if sid == stage:
                return name
        return "UNKNOWN"

bridge_logger = BridgeLogger.get_instance()
