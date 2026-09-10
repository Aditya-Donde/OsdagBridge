"""
Recents database for OsdagBridge.

Backs the "Recent Projects" and "Recently Used Modules" cards on the home page
with a small sqlite file kept alongside this module.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from osdagbridge.desktop.data.module_keys import KEY_DISP_PLATE_GIRDER_BRIDGE

SQLITE_FILE = Path(__file__).resolve().parent / 'user_data.sqlite'

PROJECT_TABLE = 'recent_projects'
MODULE_TABLE = 'recent_modules'

KEY_SEARCH_MODULE = 'modules'
KEY_SEARCH_PROJ = 'projects'

ID = 'id'
PROJECT_NAME = 'project_name'
PROJECT_PATH = 'project_path'
CREATION_DATE = 'creation_date'
LAST_EDITED = 'last_edited'
MODULE_KEY = 'module_key'
RELATED_MODULE = 'module'
RELATED_SUBMODULE = 'submodule'
LAST_OPENED = 'opened_at'
REPORT_FILE_PATH = 'files_path'

#------------------------------------Search-logic-start------------------------------------------------------------
SEARCH_MODULE_MAP = {
    'Composite Plate Girder Bridge Superstructure': KEY_DISP_PLATE_GIRDER_BRIDGE,
}

def _search_modules(keywords: list, module_map: dict = SEARCH_MODULE_MAP) -> list[tuple]:
    """
    Search modules by keyword(s).

    Args:
        keywords: list of lowercase keywords from the query
        module_map: dict with module names as keys

    Returns:
        list of (module_key, score) tuples, sorted by relevance
    """

    results = []

    for module_name, module_key in module_map.items():
        module_lower = module_name.lower()

        # Count matching keywords
        score = 0
        matched_count = 0

        for keyword in keywords:
            if keyword in module_lower:
                matched_count += 1
                # Exact word match gets higher score
                if f" {keyword} " in f" {module_lower} ":
                    score += 3
                else:
                    score += 2

        # Only include if at least one keyword matches
        if matched_count > 0:
            # Bonus for matching all keywords
            if matched_count == len(keywords):
                score += 5

            results.append((module_key, score))

    # Sort by score descending
    results.sort(key=lambda x: -x[1])
    return results

def _search_projects(keywords: list, module_keys: list[tuple]) -> list[dict]:
    """
    Search recent_projects by project_name keyword(s) and module_key.

    Args:
        keywords: list - lowercase keywords from query
        module_keys: List[tuple] - list of (module_key, score) tuples from module search

    Returns:
        List of project dicts sorted by relevance score, then by last_edited
    """
    # Extract module keys for filtering
    matched_module_keys = {mk[0] for mk in module_keys} if module_keys else set()

    with _db(as_dicts=True) as cursor:
        cursor.execute(f"""
            SELECT {ID}, {PROJECT_NAME}, {PROJECT_PATH}, {MODULE_KEY},
                   {CREATION_DATE}, {LAST_EDITED}, {REPORT_FILE_PATH}
            FROM {PROJECT_TABLE}
        """)
        rows = cursor.fetchall()

    results = []

    for row in rows:
        if MODULE_MAP.get(row[3]) is None:
            continue
        project_name_lower = row[1].lower()
        project_module_key = row[3]  # Get project's module_key

        # Calculate relevance score
        score = 0
        matched_count = 0
        matched_by_module = False  # Track if matched by module

        # Check if project's module_key matches any searched modules
        if project_module_key in matched_module_keys:
            matched_by_module = True
            # Get the module's search score
            module_score = next((ms[1] for ms in module_keys if ms[0] == project_module_key), 0)
            score += module_score  # Add module relevance to project score

        # Search in project_name
        for keyword in keywords:
            if keyword in project_name_lower:
                matched_count += 1
                # Exact word match gets higher score
                if f" {keyword} " in f" {project_name_lower} ":
                    score += 3
                # Match at start of name
                elif project_name_lower.startswith(keyword):
                    score += 4
                else:
                    score += 2

        if matched_by_module or matched_count > 0:
            # Bonus for matching all keywords in project name
            if matched_count == len(keywords):
                score += 5

            project_dict = {
                ID: row[0],
                PROJECT_NAME: row[1],
                PROJECT_PATH: row[2],
                RELATED_SUBMODULE: MODULE_MAP.get(row[3])[0],
                MODULE_KEY: row[3],
                CREATION_DATE: _format_datetime(row[4]),
                LAST_EDITED: _format_datetime(row[5]),
                REPORT_FILE_PATH: row[6],
                'score': score
            }

            results.append(project_dict)

    # Sort by score descending, then by last_edited descending
    results.sort(key=lambda x: (-x['score'], x[LAST_EDITED]), reverse=False)

    return results

def _get_module_data(keys: list[tuple]) -> list[dict]:
    records = []
    for key, _ in keys:
        dat = MODULE_MAP[key]
        r = {
            MODULE_KEY: key,
            RELATED_MODULE: dat[1],
            RELATED_SUBMODULE: dat[0],
        }
        records.append(r)

    return records

def search_projects_and_modules(query: str) -> dict[str, list]:
    """
    Search both projects and modules with a single query.

    Args:
        query: str - space-separated keywords

    Returns:
        dict with 'projects' and 'modules' keys containing search results
    """
    keywords = query.lower().split()
    if not keywords:
        return {}

    modules = _search_modules(keywords)

    return {
        KEY_SEARCH_PROJ: _search_projects(keywords, modules),
        KEY_SEARCH_MODULE: _get_module_data(modules)
    }
#------------------------------------Search-logic-end------------------------------------------------------------

MODULE_MAP = {
    #-------------------------------Submodule---------------Module------------Open-module-function--------Related-Navbar-Parent-
    KEY_DISP_PLATE_GIRDER_BRIDGE: ['Composite Plate Girder', 'Plate Girder Bridge', 'open_plate_girder_bridge', "Plate Girder Bridge"],
}

# To retrieve the name of a module function that can open the required module
def get_module_function(key: str):
    record = MODULE_MAP.get(key)
    if record is None:
        return 'None'
    return record[2]

@contextmanager
def _db(as_dicts: bool = False):
    """Yield a cursor on the recents database, committing on the way out.

    Every query below used to repeat the same connect / commit / close dance,
    with its own try/finally to make sure the handle was released.
    """
    conn = sqlite3.connect(SQLITE_FILE)
    if as_dicts:
        conn.row_factory = sqlite3.Row
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.close()


def create_user_database():
    """
    Ensure SQLite database and required tables exist.
    Creates user_data.sqlite next to this module if missing.
    """
    SQLITE_FILE.parent.mkdir(parents=True, exist_ok=True)  # Ensure folder exists

    with _db() as cursor:
        # Always ensure tables exist
        cursor.executescript("""
    CREATE TABLE IF NOT EXISTS recent_projects (
        id INTEGER PRIMARY KEY,
        project_name TEXT NOT NULL,
        project_path TEXT NOT NULL UNIQUE,
        files_path TEXT NOT NULL,
        module_key TEXT NOT NULL,
        creation_date DATETIME NOT NULL,
        last_edited DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS recent_modules (
        id INTEGER PRIMARY KEY,
        module_key TEXT NOT NULL UNIQUE,
        opened_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
        """)

def _format_datetime(dt_str: str) -> str:
    """
    Convert a datetime string from 'YYYY-MM-DD HH:MM:SS' to a readable format like '16 Sep 2025, 14:32'.
    Returns the original string if parsing fails or input is None/empty.
    """
    if not dt_str:
        return dt_str

    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d %b %Y, %H:%M")
    except ValueError:
        return dt_str  # Return if parsing fails

def fetch_all_recent_projects() -> List[Dict]:
    """
    Retrieve all records from recent_projects table, sorted by last opened date descending.
    """
    with _db(as_dicts=True) as cursor:
        cursor.execute(f"""
            SELECT {ID}, {PROJECT_NAME}, {PROJECT_PATH}, {MODULE_KEY},
                   {CREATION_DATE}, {LAST_EDITED}, {REPORT_FILE_PATH}
            FROM {PROJECT_TABLE}
            ORDER BY {LAST_EDITED} DESC;
        """)
        rows = cursor.fetchall()

    result = []
    for row in rows:
        if MODULE_MAP.get(row[3]) is None:
            # A record left behind by a module that no longer exists.
            continue
        r = {
            ID: row[0],
            PROJECT_NAME: row[1],
            PROJECT_PATH: row[2],
            RELATED_SUBMODULE: MODULE_MAP.get(row[3])[0],
            MODULE_KEY: row[3],
            CREATION_DATE: _format_datetime(row[4]),
            LAST_EDITED: _format_datetime(row[5]),
            REPORT_FILE_PATH: row[6],
        }

        result.append(r)
    return result

def fetch_all_recent_modules() -> list[dict]:
    """
    Retrieve all records from recent_modules table, sorted by last opened date descending.
    """
    records = []
    try:
        with _db() as cursor:
            cursor.execute(f"""
                SELECT {ID}, {MODULE_KEY}, {LAST_OPENED}
                FROM {MODULE_TABLE}
                ORDER BY {LAST_OPENED} DESC;
            """)
            rows = cursor.fetchall()
        for row in rows:
            dat = MODULE_MAP.get(row[1])
            if dat is None:
                continue
            r = {
                ID: row[0],
                MODULE_KEY: row[1],
                RELATED_MODULE: dat[1],
                RELATED_SUBMODULE: dat[0],
                LAST_OPENED: _format_datetime(row[2])
            }
            records.append(r)
    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")
    return records

def delete_project_record(project_id: int) -> bool:
    """
    Delete a project record from the recent_projects table using its ID.

    Args:
        project_id (int): The ID of the project to delete.

    Returns:
        bool: True if the deletion was successful, False otherwise.
    """
    try:
        with _db() as cursor:
            cursor.execute(f"DELETE FROM {PROJECT_TABLE} WHERE {ID} = ?;", (project_id,))
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")
        return False

def update_project_path(project_id: int, new_path: str, new_name: str) -> int | None:
    """
    Update the project_path and project_name for a project in the recent_projects table using its ID.
    If the new_path already exists in another record (with a different ID), delete those records,
    then update the file name and path in the given id.

    Args:
        project_id (int): The ID of the project to update.
        new_path (str): The new project path.
        new_name (str): The new project name.

    Returns:
        int | None: The ID of the updated record (project_id) if update was successful,
                    or None if an error occurred.
    """
    try:
        with _db() as cursor:
            # Drop any other record already holding the new path
            cursor.execute(
                f"DELETE FROM {PROJECT_TABLE} WHERE {PROJECT_PATH} = ? AND {ID} != ?;",
                (new_path, project_id)
            )
            # Now update the path and name for the given id
            cursor.execute(
                f"UPDATE {PROJECT_TABLE} SET {PROJECT_PATH} = ?, {PROJECT_NAME} = ? WHERE {ID} = ?;",
                (new_path, new_name, project_id)
            )
        return project_id
    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")
        return None

def get_project_by_id(project_id: int) -> dict | None:
    """
    Retrieve a single project record from the recent_projects table by its ID.

    Args:
        project_id (int): The ID of the project to retrieve.

    Returns:
        dict | None: The project's id, name and path, or None if not found.
    """
    try:
        with _db() as cursor:
            cursor.execute(
                f"SELECT {ID}, {PROJECT_NAME}, {PROJECT_PATH} "
                f"FROM {PROJECT_TABLE} WHERE {ID} = ?;",
                (project_id,)
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return {
            ID: row[0],
            PROJECT_NAME: row[1],
            PROJECT_PATH: row[2],
        }
    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")
        return None

def insert_recent_project(data: dict) -> int | None:
    """
    Insert a new record into the recent_projects table.

    data (dict): Dictionary containing project details. Must include keys:
            - PROJECT_NAME: Name of the project
            - PROJECT_PATH: Path to the project (unique identifier)
            - MODULE_KEY: Module identifier
            Optional keys:
            - REPORT_FILE_PATH: Path to the generated .tex and .png files
            - creation_date: Creation timestamp (defaults to current time)
            - last_edited: Last edited timestamp (defaults to current time)
    Returns:
        int | None: ID of the inserted or updated record, or None if insertion failed.
    """
    # Fill missing dates with current timestamp
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    creation_date = data.get("creation_date", now_str)
    last_edited = data.get("last_edited", now_str)

    try:
        with _db() as cursor:
            # If there is some conflict in Path(UNIQUE) then last_edited date is updated.
            cursor.execute(f"""
                INSERT INTO {PROJECT_TABLE}
                ({PROJECT_NAME}, {PROJECT_PATH}, {REPORT_FILE_PATH}, {MODULE_KEY}, {CREATION_DATE}, {LAST_EDITED})
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT({PROJECT_PATH})
                DO UPDATE SET
                    {MODULE_KEY}=excluded.{MODULE_KEY},
                    {LAST_EDITED}=excluded.{LAST_EDITED};
            """, (
                data[PROJECT_NAME],
                data[PROJECT_PATH],
                data.get(REPORT_FILE_PATH, ""),
                data[MODULE_KEY],
                creation_date,
                last_edited
            ))

            cursor.execute(
                f"SELECT id FROM {PROJECT_TABLE} WHERE {PROJECT_PATH} = ?",
                (data[PROJECT_PATH],)
            )
            row = cursor.fetchone()
            return row[0] if row else None

    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")
        return None

def insert_recent_module(module_key: str) -> int | None:
    """
    Insert a new record into recent_modules table.
    If the module already exists, update its opened_at timestamp.

    Args:
        module_key (str): Key of the module from MODULE_MAP.

    Returns:
        ID of the inserted record, or None if insertion failed.
    """
    opened_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with _db() as cursor:
            cursor.execute(f"""
                INSERT INTO {MODULE_TABLE}
                ({MODULE_KEY}, {LAST_OPENED})
                VALUES (?, ?)
                ON CONFLICT({MODULE_KEY})
                DO UPDATE SET
                    {LAST_OPENED}=excluded.{LAST_OPENED};
            """, (module_key, opened_at))
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")
        return None

def refactor_database():
    """
    Cleans up the database by:
    1. Removing projects whose file path no longer exists.
    2. Ensuring at most 10 most recent projects remain (drop oldest).
    3. Removing modules older than 60 days.
    4. Ensuring at most 10 most recent modules remain (drop oldest).
    """
    with _db(as_dicts=True) as cursor:
        _prune(cursor)


def _prune(cursor):
    """The individual clean-up steps, sharing one open cursor."""
    # Remove projects whose .osi file has since been deleted or moved
    cursor.execute(f"SELECT {ID}, {PROJECT_PATH} FROM {PROJECT_TABLE};")
    missing = [str(row[ID]) for row in cursor.fetchall() if not Path(row[PROJECT_PATH]).exists()]
    if missing:
        cursor.execute(f"DELETE FROM {PROJECT_TABLE} WHERE {ID} IN ({','.join(missing)});")
        print(f"[INFO] Deleted {len(missing)} project record(s) whose file no longer exists.")

    # Remove projects older than 60 days
    cutoff_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(f"""
        DELETE FROM {PROJECT_TABLE}
        WHERE {LAST_EDITED} < ?;
    """, (cutoff_date,))
    old_projects_deleted = cursor.rowcount
    if old_projects_deleted > 0:
        print(f"[INFO] Deleted {old_projects_deleted} project records older than 60 days.")

    # Keep only 10 most recent projects
    cursor.execute(f"""
        SELECT {ID} FROM {PROJECT_TABLE}
        ORDER BY {LAST_EDITED} DESC
        LIMIT -1 OFFSET 10;
    """)
    rows_to_delete = cursor.fetchall()
    if rows_to_delete:
        ids_to_delete = [str(row[ID]) for row in rows_to_delete]
        cursor.execute(f"DELETE FROM {PROJECT_TABLE} WHERE {ID} IN ({','.join(ids_to_delete)});")
        print(f"[INFO] Deleted {len(ids_to_delete)} oldest project(s) to maintain max 10 records.")

    # Remove modules older than 60 days
    cursor.execute(f"""
        DELETE FROM {MODULE_TABLE}
        WHERE {LAST_OPENED} < ?;
    """, (cutoff_date,))
    old_modules_deleted = cursor.rowcount
    if old_modules_deleted > 0:
        print(f"[INFO] Deleted {old_modules_deleted} module records older than 60 days.")

    # Keep only 10 most recent modules
    cursor.execute(f"""
        SELECT {ID} FROM {MODULE_TABLE}
        ORDER BY {LAST_OPENED} DESC
        LIMIT -1 OFFSET 10;
    """)
    rows_to_delete = cursor.fetchall()
    if rows_to_delete:
        ids_to_delete = [str(row[ID]) for row in rows_to_delete]
        cursor.execute(f"DELETE FROM {MODULE_TABLE} WHERE {ID} IN ({','.join(ids_to_delete)});")
        print(f"[INFO] Deleted {len(ids_to_delete)} oldest module(s) to maintain max 10 records.")
