from fastapi import APIRouter
from ....core.config import settings
from ....services.supabase_service import supabase_service

router = APIRouter()


@router.get("/health", summary="System Health Status")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "supabase_connected": supabase_service.client is not None,
        "models": {
            "model_1": settings.MODEL_1_NAME,
            "model_2": settings.MODEL_2_NAME,
            "provider": "OpenRouter",
            "llm_key_configured": bool(settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY)
        },
        "thresholds": {
            "path_a_direct": settings.CONFIDENCE_DIRECT_THRESHOLD,
            "path_c_rejection": settings.CONFIDENCE_REJECTION_THRESHOLD
        }
    }
