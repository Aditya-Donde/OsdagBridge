from fastapi import APIRouter
from pydantic import BaseModel

from app.services.solvers.solver_service import run_bridge_analysis

router = APIRouter()

class BridgeInput(BaseModel):
    structureType: str
    span: float
    carriagewayWidth: float
    includeMedian: bool
    skewAngle: float
    girderMaterial: str
    deckMaterial: str

@router.post("/analyze")
async def analyze_bridge(data: BridgeInput):
    return run_bridge_analysis(data.dict())