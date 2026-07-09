import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
SRC_DIR = ROOT_DIR / "src"

sys.path.append(str(SRC_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.cross_section import router as cross_section_router
from app.api.routes import bridge
from app.api.routes.top_view import router as top_view_router
from app.api.routes.schemas import router as schemas_router
from app.api.routes.materials import router as materials_router

app = FastAPI(title="OsdagBridge API")
app.include_router(cross_section_router)
app.include_router(top_view_router)
app.include_router(schemas_router)
app.include_router(materials_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bridge.router, prefix="/bridge", tags=["Bridge"])