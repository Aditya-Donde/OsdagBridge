import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[5]
sys.path.append(str(ROOT_DIR))

from src.osdagbridge.core.solvers.native_solver import (
    run_native_analysis,
)

def run_bridge_analysis(data):
    result = run_native_analysis(data)

    return {
        "status": "success",
        "input": data,
        "result": result,
    }