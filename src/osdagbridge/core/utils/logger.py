"""Bridge analysis and design structured logger."""
import logging
import time
from datetime import datetime
from typing import Callable, Optional, List

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
