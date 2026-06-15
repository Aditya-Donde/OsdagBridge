import sys
import re
import queue
import multiprocessing as mp
from PySide6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QDialog, QLabel, QProgressBar, QPushButton, QTextEdit, QWidget
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QIcon

from osdagbridge.core.utils.logger import bridge_logger

# Green spinner animation
class _SpinnerLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.setFixedSize(24, 24)
        self.setStyleSheet("border: none; background: transparent;")
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def _tick(self):
        self.angle = (self.angle - 6) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(3, 3, -3, -3)
        pen = QPen(QColor(0x90, 0xAF, 0x13))
        pen.setWidthF(2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawArc(r, int(self.angle * 16), 80 * 16)

    def stop(self):
        self._timer.stop()


# Progress dialog
class AnalysisProgressDialog(QDialog):
    def __init__(self, cancel_event, is_light_theme=True, parent=None):
        super().__init__(parent)
        self._cancel_event = cancel_event
        self._is_light = is_light_theme
        first_stage_name = "INPUT VALIDATION"
        total_stages = 14
        if bridge_logger.STAGE_MAP:
            first_stage_name = bridge_logger.STAGE_MAP[0][1]
            total_stages = len(bridge_logger.STAGE_MAP)
        self._stage_list = [sid for sid, _ in bridge_logger.STAGE_MAP]
        self._current_stage_text = f"STAGE 1/{total_stages} : {first_stage_name}"
        self._current_pct = 0

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setModal(False)
        self.setFixedSize(500, 400)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        try:
            self.setWindowIcon(QIcon(":/images/osdag_logo.png"))
        except Exception:
            pass

        self._build_ui()
        self._center()

    def _build_ui(self):
        bg = "#FFFFFF" if self._is_light else "#2C2C2C"
        fg = "#1F1F1F" if self._is_light else "#D0D0D0"
        sub_fg = "#777777" if self._is_light else "#A0A0A0"
        log_bg = "#F8F8F8" if self._is_light else "#1E1E1E"
        log_fg = "#555555" if self._is_light else "#A0A0A0"
        log_bdr = "#DDDDDD" if self._is_light else "#444444"
        btn_bdr = "#CCCCCC" if self._is_light else "#555555"
        bar_bg = "#E8E8E8" if self._is_light else "#444444"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg};
                border: 1px solid #90AF13;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        title_row = QWidget()
        title_row.setObjectName("title_row")
        title_row.setStyleSheet(f"QWidget#title_row {{ background-color: {bg}; border-bottom: 2px solid #90AF13; }}")
        title_row.setFixedHeight(36)
        tr_layout = QHBoxLayout(title_row)
        tr_layout.setContentsMargins(10, 0, 10, 2)
        tr_layout.setSpacing(8)

        self._spinner = _SpinnerLabel()
        tr_layout.addWidget(self._spinner)

        brand_lbl = QLabel("Osdag")
        brand_lbl.setStyleSheet(
            "color: #90AF13; font-weight: 700; font-size: 12px; "
            "letter-spacing: 1px; border: none; background: transparent;"
        )
        tr_layout.addWidget(brand_lbl)

        dot_lbl = QLabel("·")
        dot_lbl.setStyleSheet("color: #CCCCCC; font-size: 13px; border: none; background: transparent;")
        tr_layout.addWidget(dot_lbl)

        title_lbl = QLabel("Analysis running in background")
        title_lbl.setStyleSheet(
            f"color: {fg}; font-weight: 600; font-size: 11px; "
            "border: none; background: transparent;"
        )
        tr_layout.addWidget(title_lbl)
        tr_layout.addStretch()

        title_row._drag_pos = QPoint()

        def _press(ev):
            if ev.button() == Qt.MouseButton.LeftButton:
                title_row._drag_pos = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()

        def _move(ev):
            if ev.buttons() == Qt.MouseButton.LeftButton:
                self.move(ev.globalPosition().toPoint() - title_row._drag_pos)

        title_row.mousePressEvent = _press
        title_row.mouseMoveEvent = _move

        root.addWidget(title_row)

        content = QWidget()
        content.setStyleSheet(f"background-color: {bg};")
        c = QVBoxLayout(content)
        c.setContentsMargins(16, 14, 16, 14)
        c.setSpacing(10)

        # Status Card grouping high-level progress details
        self._status_card = QWidget()
        self._status_card.setObjectName("status_card")
        self._status_card.setStyleSheet(f"""
            QWidget#status_card {{
                background-color: {log_bg};
                border: 1px solid {log_bdr};
                border-radius: 6px;
            }}
        """)
        card_layout = QVBoxLayout(self._status_card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)

        # Stage label (Main status)
        self._stage_lbl = QLabel(f"{self._current_stage_text} [0%]")
        self._stage_lbl.setStyleSheet(
            f"color: {fg}; font-weight: 700; font-size: 12px; border: none; background: transparent;"
        )
        self._stage_lbl.setWordWrap(True)
        card_layout.addWidget(self._stage_lbl)

        # Progress Bar (Sleeker, 6px high)
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(6)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {bar_bg};
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: #90AF13;
                border-radius: 3px;
            }}
        """)
        card_layout.addWidget(self._progress)

        # Sub-status label (Created as hidden to avoid printing text below progress bar, keeping layout clean)
        self._sub_lbl = QLabel(self)
        self._sub_lbl.hide()

        c.addWidget(self._status_card)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Courier New", 8))
        self._log.setStyleSheet(f"""
            QTextEdit {{
                background-color: {log_bg};
                color: {log_fg};
                border: 1px solid {log_bdr};
                border-radius: 4px;
            }}
        """)
        c.addWidget(self._log)

        self._stop_btn = QPushButton("Stop Analysis")
        self._stop_btn.setFixedHeight(30)
        self._stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {btn_bdr};
                border-radius: 5px;
                font-size: 11px;
                font-weight: 500;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: #90AF13;
                color: white;
                border-color: #90AF13;
            }}
            QPushButton:pressed {{
                background-color: #6B7D20;
                color: white;
            }}
            QPushButton:disabled {{
                background-color: {"#F0F0F0" if self._is_light else "#3A3A3A"};
                color: {"#AAAAAA" if self._is_light else "#666666"};
                border-color: {"#DDDDDD" if self._is_light else "#444444"};
            }}
        """)
        self._stop_btn.clicked.connect(self._on_stop)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self._stop_btn)
        btn_row.addStretch()
        c.addLayout(btn_row)

        root.addWidget(content)

    def _center(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2,
        )

    def handle_message(self, msg: str, level: str) -> None:
        if level == "progress":
            try:
                pct = int(msg.replace("__progress__", ""))
                self._current_pct = pct
                self._progress.setValue(pct)
                if hasattr(self, '_current_stage_text') and self._current_stage_text:
                    self._stage_lbl.setText(f"{self._current_stage_text} [{pct}%]")
            except ValueError:
                pass
            return

        color = {
            "error":   "#FF4444",
            "success": "#00BB00",
            "warning": "#FFA500",
        }.get(level, "#888888")

        html_msg = (
            msg.replace("&", "&amp;")
               .replace("<", "&lt;")
               .replace(">", "&gt;")
        )
        # Smart scroll down only if the user was already at the bottom (with a 15px tolerance)
        scrollbar = self._log.verticalScrollBar()
        was_at_bottom = scrollbar.value() >= scrollbar.maximum() - 15

        self._log.append(
            f'<span style="color:{color}; white-space:pre;">{html_msg}</span>'
        )
        
        if was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())
        bare = msg.split("]", 1)[-1].strip() if "]" in msg else msg.strip()
        if not bare:
            return

        if "STAGE" in bare.upper() and ":" in bare:
            try:
                parts = bare.split(":", 1)
                stage_part = parts[0].strip() # e.g. "STAGE 8 COMPLETE [100%]"

                # Strip bracketed percentage (e.g. [100%]) from stage_part
                stage_part_clean = re.sub(r'\s*\[\d+%\s*\]$', '', stage_part)
                stage_id = stage_part_clean.replace("STAGE", "").replace("COMPLETE", "").strip()

                if stage_id in self._stage_list:
                    idx = self._stage_list.index(stage_id) + 1
                    name = bridge_logger.STAGE_MAP[idx - 1][1]
                    is_complete = "COMPLETE" in stage_part.upper()
                    suffix = " COMPLETE" if is_complete else ""
                    clean_bare = f"STAGE {idx}/{len(self._stage_list)}{suffix} : {name}"
                else:
                    clean_bare = re.sub(r'\s*\[\d+%\s*\]$', '', bare)
            except Exception:
                clean_bare = re.sub(r'\s*\[\d+%\s*\]$', '', bare)

            self._current_stage_text = clean_bare
            self._stage_lbl.setText(f"{clean_bare} [{self._current_pct}%]")

    def _on_stop(self):
        self._cancel_event.set()
        self._stage_lbl.setText("Stopping analysis…")
        self._sub_lbl.setText("Please wait for the current step to finish.")
        self._stop_btn.setEnabled(False)

    def closeEvent(self, event):
        self._spinner.stop()
        super().closeEvent(event)


def run_loading_dialog_process(stop_event, is_light_theme=True, label_queue=None, cancel_event=None, ready_event=None):
    """Entry point for the subprocess that owns the loading dialog window."""
    app = QApplication(sys.argv)
    dialog = AnalysisProgressDialog(cancel_event, is_light_theme=is_light_theme)

    # Poll stop event; dispatch queued messages every 50ms
    timer = QTimer()
    def check_events():
        if stop_event.is_set():
            dialog.close()
            return
        if label_queue is not None:
            while True:
                try:
                    item = label_queue.get_nowait()
                    dialog.handle_message(item["msg"], item["level"])
                except queue.Empty:
                    break
                except Exception:
                    break
    timer.timeout.connect(check_events)
    timer.start(50)

    dialog.show()
    if ready_event is not None:
        try:
            # Signal the parent process that the dialog is visible and ready to receive messages
            ready_event.set()
        except Exception:
            pass
    app.exec()


class LoadingDialogManager:
    """
    Manager class to control the loading dialog.
    Uses in-process dialog on Linux to avoid window duplication issues.
    Uses separate process on Windows/macOS for better performance.
    """
    def __init__(self, is_light_theme=True):
        self.process = None
        self.stop_event = None
        self.label_queue = None
        self.cancel_event = mp.Event()
        self.is_light_theme = is_light_theme
        self._dialog = None  # For in-process mode
        
        # Detect OS - Linux has issues with multiprocess GUI windows
        import platform
        self._use_process = platform.system() != "Linux"
    
    def show(self):
        """Show the loading dialog"""
        self.cancel_event.clear()
        if self._use_process:
            # Windows/macOS - use separate process
            if self.process is not None and self.process.is_alive():
                return  # Already running
            
            self.stop_event = mp.Event()
            self.label_queue = mp.Queue()
            self.ready_event = mp.Event()
            self.process = mp.Process(
                target=run_loading_dialog_process,
                args=(self.stop_event, self.is_light_theme, self.label_queue, self.cancel_event, self.ready_event)
            )
            self.process.start()

            # Wait for ready_event to be set, up to 1.5 seconds (yielding to Qt events using QApplication.processEvents)
            import time
            from PySide6.QtWidgets import QApplication
            start_t = time.time()
            while not self.ready_event.is_set() and (time.time() - start_t) < 1.5:
                QApplication.processEvents()
                time.sleep(0.01)
        else:
            # Linux - use in-process dialog to avoid duplicate window issues
            if self._dialog is None:
                self._dialog = AnalysisProgressDialog(self.cancel_event, is_light_theme=self.is_light_theme)
            self._dialog.show()
    
    def hide(self):
        """Hide the loading dialog"""
        if self._use_process:
            if self.process is not None and self.process.is_alive():
                self.stop_event.set()
                self.process.join(timeout=2)  # Wait up to 2 seconds
                if self.process.is_alive():
                    self.process.terminate()  # Force terminate if still running
                self.process = None
                self.stop_event = None
                self.label_queue = None
                self.ready_event = None
        else:
            # Linux in-process mode: just hide the dialog
            if self._dialog is not None:
                self._dialog.hide()
                if hasattr(self._dialog, '_spinner'):
                    self._dialog._spinner.stop()
                self._dialog = None

    def send_message(self, msg: str, level: str) -> None:
        # Send message to dialog queue
        if self._use_process:
            if self.label_queue is not None:
                try:
                    self.label_queue.put_nowait({"msg": msg, "level": level})
                except Exception:
                    pass
        else:
            if self._dialog is not None and hasattr(self._dialog, 'handle_message'):
                self._dialog.handle_message(msg, level)

    def is_cancelled(self) -> bool:
        # Check if Stop was clicked
        return self.cancel_event.is_set()

    def __del__(self):
        """Cleanup when manager is destroyed"""
        self.hide()
