from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .core.config import settings
from .core.logging import logger
from .api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME}...")
    logger.info(f"Direct Confidence Threshold (Path A): {settings.CONFIDENCE_DIRECT_THRESHOLD}")
    logger.info(f"Rejection Threshold (Path C): {settings.CONFIDENCE_REJECTION_THRESHOLD}")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent Returns Triage Engine for Dhaga & Co. Ingests messy, code-mixed Hinglish and vernacular return requests and standardizes them into structured category intelligence.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for decoupled frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 master router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", summary="Root Status")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "operational",
        "docs_url": "/docs",
        "api_v1_url": settings.API_V1_STR,
        "health_check": f"{settings.API_V1_STR}/health"
    }
