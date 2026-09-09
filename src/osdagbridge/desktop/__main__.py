import sys
import os

# Print a Python traceback instead of a bare core dump on a native crash (stderr may be None).
import faulthandler
try:
    faulthandler.enable()
except Exception:
    pass


def _register_conda_dll_directories():
    """Add the active conda environment's native DLL folders to the Windows DLL
    search path before numpy/scipy/openseespy are imported.

    A conda-constructor-installed app launched from its shortcut does not
    "activate" the environment, so ``<prefix>/Library/bin`` (MKL/OpenBLAS, Qt,
    etc.) is not on the DLL search path. Native extensions then crash the whole
    process with ``ERROR_MOD_NOT_FOUND`` (``0xc06d007f``) the first time they
    delay-load a backend DLL — e.g. ``numpy.linalg.lstsq`` during grillage
    meshing, which silently closes the window and hangs the loader. No-op on
    non-Windows and in already-activated environments.
    """
    if os.name != "nt":
        return
    prefix = sys.prefix
    candidates = [
        os.path.join(prefix, "Library", "bin"),
        os.path.join(prefix, "Library", "mingw-w64", "bin"),
        os.path.join(prefix, "Library", "usr", "bin"),
        os.path.join(prefix, "DLLs"),
        prefix,
    ]
    path_entries = os.environ.get("PATH", "").split(os.pathsep)
    for path in candidates:
        if not os.path.isdir(path):
            continue
        try:
            os.add_dll_directory(path)
        except (OSError, AttributeError):
            pass
        if path not in path_entries:
            os.environ["PATH"] = path + os.pathsep + os.environ.get("PATH", "")
            path_entries.insert(0, path)


_register_conda_dll_directories()


def _ensure_std_streams():
    """Guarantee sys.stdout/sys.stderr are writable.

    When launched as a gui-script, Windows runs this under pythonw.exe, which
    has no console: sys.stdout/sys.stderr are None. The desktop app prints a lot
    of debug output, and the first print() against None raises AttributeError
    and kills the app silently. Redirect the missing stream(s) to a log file
    (falling back to os.devnull) so the GUI can launch without a console window.
    """
    if sys.stdout is not None and sys.stderr is not None:
        return
    try:
        import tempfile
        log_path = os.path.join(tempfile.gettempdir(), "osdagbridge.log")
        stream = open(log_path, "a", buffering=1, encoding="utf-8")
    except Exception:
        stream = open(os.devnull, "w")
    if sys.stdout is None:
        sys.stdout = stream
    if sys.stderr is None:
        sys.stderr = stream


_ensure_std_streams()

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QIcon, QFont, QFontDatabase
from PySide6.QtCore import QElapsedTimer, QThread, QTimer, Signal
from osdagbridge.desktop.resources import icons_rc, mainPageIcons_rc


def _app_icon():
    """Return the OsdagBridge application icon (the same .ico used for the
    desktop / Start Menu shortcut), or an empty QIcon if it can't be found."""
    try:
        from importlib.resources import files
        ico = files('osdagbridge.desktop.resources').joinpath('osdagbridge.ico')
        if ico.is_file():
            return QIcon(str(ico))
    except Exception:
        pass
    return QIcon()


def _set_windows_app_id():
    """Give the app its own Windows taskbar identity so the taskbar shows the
    OsdagBridge icon instead of the generic Python/pythonw icon. Must run before
    the main window is shown. No-op on non-Windows."""
    if os.name != "nt":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "Osdag.OsdagBridge.Desktop.1"
        )
    except Exception:
        pass

# Create Intg_osdag.sqlite if not Exist
def create_sqlite():
    import sqlite3
    import subprocess
    from importlib.resources import files
    import shutil
    
    try:
        # Get paths
        sqlpath = files('osdagbridge.core.data.ResourceFiles').joinpath('Intg_osdag.sql')
        sqlitepath = files('osdagbridge.core.data.ResourceFiles').joinpath('Intg_osdag.sqlite')

        if not sqlpath.exists():
            print(f"[ERROR] SQL file not found: {sqlpath}")
            return

        # Determine if we need to create or update
        needs_creation = not sqlitepath.exists()
        needs_update = (sqlitepath.exists() and 
                    (sqlitepath.stat().st_size == 0 or 
                        sqlitepath.stat().st_mtime < sqlpath.stat().st_mtime - 1))

        if not needs_creation and not needs_update:
            # print("[INFO] Database is up to date")
            return

        # Create backup if updating existing database
        backup_path = None
        if needs_update:
            backup_path = sqlitepath.with_suffix('.sqlite.backup')
            shutil.copy2(sqlitepath, backup_path)

        # Create/update database
        target_path = sqlitepath
        if needs_update:
            # Create in temp location first
            target_path = sqlitepath.parent / 'Intg_osdag_temp.sqlite'

        # Try Python sqlite3 first
        try:
            with open(sqlpath, 'r', encoding='utf-8') as sql_file:
                sql_content = sql_file.read()
            
            conn = sqlite3.connect(target_path)
            conn.executescript(sql_content)
            conn.close()
            
            print(f"[INFO] Intg_osdag sqlite database {'created' if needs_creation else 'updated'} using python sqlite3")
            
        except Exception as e:
            print(f"[ERROR] Python sqlite3 failed: {e}, trying command line")
            
            # Fallback to command line
            result = subprocess.run([
                'sqlite3', str(target_path), 
                f'.read {sqlpath}'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"[ERROR] Command line sqlite3 failed: {result.stderr}")
            
            print(f"[INFO] Intg_osdag sqlite database {'created' if needs_creation else 'updated'} using command line")

        # If updating, replace the original
        if needs_update:
            sqlitepath.unlink()
            target_path.rename(sqlitepath)
            if backup_path and backup_path.exists():
                backup_path.unlink()

        # Touch the SQL file to update timestamp
        sqlpath.touch()

    except Exception as e:
        print(f"[ERROR] Database setup failed: {e}")
        
        # Cleanup on failure
        if needs_update:
            # Restore backup if available
            if backup_path and backup_path.exists():
                if not sqlitepath.exists():
                    shutil.copy2(backup_path, sqlitepath)
                backup_path.unlink()
            
            # Remove temp file
            temp_path = sqlitepath.parent / 'Intg_osdag_temp.sqlite'
            if temp_path.exists():
                temp_path.unlink()

create_sqlite()


def ensure_osdag_core_db():
    """Build the osdag_core sqlite database if it is missing or empty.

    The installed `osdag` package ships a 0-byte placeholder
    `Intg_osdag.sqlite` alongside the `Intg_osdag.sql` that defines its
    tables (Beams, Angles, Columns, ...), but nothing populates it. When the
    desktop app queries it via osdag_core.Common, every lookup fails with
    "no such table: Beams/Angles". Build the database from the bundled SQL on
    startup so those section tables are always available.
    """
    import sqlite3
    from importlib.resources import files

    try:
        db_dir = files('osdag_core.data.ResourceFiles.Database')
        sqlpath = db_dir.joinpath('Intg_osdag.sql')
        sqlitepath = db_dir.joinpath('Intg_osdag.sqlite')

        if not sqlpath.exists():
            print(f"[ERROR] osdag_core SQL file not found: {sqlpath}")
            return

        # Decide whether the database needs (re)building: missing, empty, or
        # has no tables at all.
        needs_build = True
        if sqlitepath.exists() and sqlitepath.stat().st_size > 0:
            try:
                conn = sqlite3.connect(str(sqlitepath))
                has_tables = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' LIMIT 1"
                ).fetchone()
                conn.close()
                needs_build = has_tables is None
            except Exception:
                needs_build = True

        if not needs_build:
            return

        with open(sqlpath, 'r', encoding='utf-8') as sql_file:
            sql_content = sql_file.read()

        conn = sqlite3.connect(str(sqlitepath))
        conn.executescript(sql_content)
        conn.commit()
        conn.close()
        print("[INFO] osdag_core Intg_osdag sqlite database built from SQL")

    except Exception as e:
        print(f"[ERROR] osdag_core database setup failed: {e}")


ensure_osdag_core_db()

from osdagbridge.desktop.ui.utils.theme_manager import ThemeManager
from osdagbridge.desktop.ui.windows.launch_screen import OsdagBridgeLaunchScreen

# Keep the launch screen up for at least this long, however fast startup is.
SPLASH_MIN_MS = 5000


class LoadingThread(QThread):
    """Do the slow startup work while the splash screen is on show."""
    ready = Signal()

    def run(self):
        from osdagbridge.desktop.data.database.database_config import (
            create_user_database, refactor_database,
        )
        # Create the user database if it does not exist yet
        create_user_database()
        # Prune it to 10 records, at most 60 days old, whose .osi still exists
        try:
            refactor_database()
        except Exception as e:
            print(f"[ERROR] Failed to clean the recents database: {e}")

        # Pull in the main window's (large) dependency tree here rather than on
        # the GUI thread, so the splash animation keeps running through it. This
        # only imports modules - no widget is built until the GUI thread asks.
        import osdagbridge.desktop.main_window  # noqa: F401

        self.ready.emit()


class LaunchScreenPopup(QMainWindow):
    """Splash screen that hands straight over to the main window.

    The main window is built *behind* the splash and only shown once it is
    ready, so there is never a moment with neither window on screen.
    """

    def __init__(self, build_main_window):
        super().__init__()
        self.ui = OsdagBridgeLaunchScreen()
        self.ui.setupUi(self)
        self.build_main_window = build_main_window
        self.main_window = None
        self.show()

        self.uptime = QElapsedTimer()
        self.uptime.start()

        self.loader = LoadingThread()
        self.loader.ready.connect(self.on_database_ready)
        self.loader.start()

    def on_database_ready(self):
        # Build the main window now, while the splash is still on screen. This
        # overlaps construction with the minimum splash time instead of running
        # after it. Widgets must be created on the GUI thread, so this part
        # cannot move into LoadingThread.
        self.main_window = self.build_main_window()

        remaining = SPLASH_MIN_MS - self.uptime.elapsed()
        QTimer.singleShot(max(0, remaining), self.hand_over)

    def hand_over(self):
        """Show the main window, then drop the splash once it has painted."""
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        QApplication.instance().setQuitOnLastWindowClosed(True)

        # Flush the show/paint events so the main window is actually on screen
        # before the splash disappears - otherwise the desktop flashes through.
        QApplication.processEvents()
        self.close()


def main():
    # Establish the Windows taskbar identity before the QApplication so the
    # taskbar uses our icon, not the host Python interpreter's.
    _set_windows_app_id()

    # Create the Qt application instance
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Bundled Ubuntu Sans - works on every OS without the font being installed
    font_id = QFontDatabase.addApplicationFont(":/fonts/UbuntuSans-Regular.ttf")
    if font_id != -1:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        app.setFont(QFont(font_family, 10))  # Set as default app font
    else:
        print("[WARNING] Failed to load Ubuntu Sans font from resources")

    # Application-wide icon: taskbar, Alt-Tab, and default window icon.
    icon = _app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    # Theme plumbing: every home-page widget reads this off the app instance
    app.theme_manager = ThemeManager(app)
    app.theme_manager.load_theme()

    def build_main_window():
        # Already imported by LoadingThread, so this resolves from sys.modules.
        from osdagbridge.desktop.main_window import MainWindow
        app.main_window = MainWindow()
        return app.main_window

    # Nothing must quit the app while the splash is the only window on screen.
    app.setQuitOnLastWindowClosed(False)
    app.splash = LaunchScreenPopup(build_main_window)

    # Execute the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
