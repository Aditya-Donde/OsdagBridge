from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Optional

RESOURCE_DB_NAME = "Intg_osdag.sqlite"
RESOURCE_SQL_NAME = "Intg_osdag.sql"
REQUIRED_TABLES = ("Material", "Beams", "Concrete_Grade_Properties")


def _resource_files_dir(start_path: Optional[Path] = None) -> Path:
    """Resolve the ResourceFiles directory from a calling module path."""
    probe = (start_path or Path(__file__)).resolve()
    for parent in (probe, *probe.parents):
        candidate = parent / "core" / "data" / "ResourceFiles"
        if candidate.exists():
            return candidate

    # Fallback from this module location: core/utils -> core/data/ResourceFiles
    return Path(__file__).resolve().parents[1] / "data" / "ResourceFiles"


def locate_resource_database(start_path: Optional[Path] = None) -> Path:
    return _resource_files_dir(start_path) / RESOURCE_DB_NAME


def _sql_seed_path(start_path: Optional[Path] = None) -> Path:
    return _resource_files_dir(start_path) / RESOURCE_SQL_NAME


def _has_required_tables(db_path: Path) -> bool:
    if not db_path.exists():
        return False

    try:
        connection = sqlite3.connect(str(db_path))
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        available = {str(row[0]).strip() for row in cursor.fetchall() if row and row[0]}
        return all(table in available for table in REQUIRED_TABLES)
    except sqlite3.Error:
        return False
    finally:
        try:
            connection.close()
        except Exception:
            pass


def ensure_resource_database(start_path: Optional[Path] = None) -> Path:
    """Create and seed Intg_osdag.sqlite from Intg_osdag.sql when needed."""
    db_path = locate_resource_database(start_path)

    if _has_required_tables(db_path):
        return db_path

    sql_path = _sql_seed_path(start_path)
    if not sql_path.exists():
        return db_path

    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Rebuild when the DB file exists but is empty/corrupt/incomplete.
    if db_path.exists():
        db_path.unlink()

    connection = sqlite3.connect(str(db_path))
    try:
        script = sql_path.read_text(encoding="utf-8")
        connection.executescript(script)
        connection.commit()
    finally:
        connection.close()

    return db_path
