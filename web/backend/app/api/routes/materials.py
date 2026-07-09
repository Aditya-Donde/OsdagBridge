import sqlite3
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/materials", tags=["Materials"])

def _locate_resource_file(file_name: str) -> Path:
    # Go up from web/backend/app/api/routes/materials.py to root
    root_dir = Path(__file__).resolve().parents[5]
    return root_dir / "src" / "osdagbridge" / "core" / "data" / "ResourceFiles" / file_name

def _execute_resource_query(query: str):
    db_path = _locate_resource_file("Intg_osdag.sqlite")
    if not db_path.exists():
        return None

    connection = sqlite3.connect(str(db_path))
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error:
        return None
    finally:
        connection.close()

def _normalize_steel_material_name(name: str) -> str:
    return "".join(str(name or "").upper().split())

def _load_concrete_grade_values_from_db():
    rows = _execute_resource_query(
        """
        SELECT Grade, fck, fctm, Ecm
        FROM Concrete_Grade_Properties
        """
    )
    values = {}
    if rows is not None:
        for grade, fck, fctm, ecm in rows:
            key = str(grade).strip().upper()
            values[key] = {
                "fck": float(fck),
                "fctm": float(fctm),
                "Ecm": float(ecm),
            }
    return values

def _load_steel_material_values_from_db():
    values = {}
    rows = _execute_resource_query(
        '''
        SELECT [Material Name], [Yield Strength], [Ultimate Tensile Strength]
        FROM Material
        '''
    )
    if rows is None:
        rows = _execute_resource_query(
            '''
            SELECT Grade, [Yield Strength], [Ultimate Tensile Strength]
            FROM Steel_Grade_Properties
            '''
        )
    if rows is None:
        return {}

    try:
        for material_name, fy, fu in rows:
            key = _normalize_steel_material_name(material_name)
            if not key:
                continue
            values[key] = {"Fy": float(fy), "Fu": float(fu)}
        return values
    except (TypeError, ValueError):
        return {}

@router.get("/base-values")
def get_material_base_values():
    return {
        "steel": _load_steel_material_values_from_db(),
        "concrete": _load_concrete_grade_values_from_db()
    }
