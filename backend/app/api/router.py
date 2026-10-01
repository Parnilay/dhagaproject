from fastapi import APIRouter
from .v1.endpoints import health, triage

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(triage.router, prefix="/triage", tags=["Returns Triage"])
