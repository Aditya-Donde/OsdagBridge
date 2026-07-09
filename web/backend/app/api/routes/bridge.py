from fastapi import APIRouter
from app.models.bridge import BridgeInput
from app.services.bridge.native_bridge_solver import run_bridge_analysis

router = APIRouter()


@router.post("/analyze")
def analyze_bridge(data: BridgeInput):
    return run_bridge_analysis(data)