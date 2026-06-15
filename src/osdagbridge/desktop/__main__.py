import sys
import os


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

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QTextStream
from osdagbridge.desktop.resources import resources_rc

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

# Import template_page
from osdagbridge.desktop.ui.template_page import CustomWindow
from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge

def load_stylesheet():
    """Load the global QSS stylesheet from resources."""
    file = QFile(":/themes/lightstyle.qss")
    if file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(file)
        stylesheet = stream.readAll()
        file.close()
        return stylesheet
    return ""

def main():
    # Create the Qt application instance
    app = QApplication(sys.argv)
    
    # Load and apply the global stylesheet
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)
    
    window = CustomWindow("OsdagBridge", PlateGirderBridge)
    window.showMaximized()
    window.show()

    # Execute the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
