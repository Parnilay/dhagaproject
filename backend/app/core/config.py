from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "Dhaga & Co - Intelligent Returns Triage Engine"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # LLM Settings (Two Models Minimum)
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API Key for Model 1 and Model 2")
    
    # Model 1 (Bulk Triage & Extraction, T=0.0)
    MODEL_1_NAME: str = "gpt-4o-mini"
    MODEL_1_TEMPERATURE: float = 0.0

    # Model 2 (Evaluator & Ambiguity Arbiter, T=0.2)
    MODEL_2_NAME: str = "gpt-4o"
    MODEL_2_TEMPERATURE: float = 0.2

    # Deterministic Confidence Gate Thresholds
    CONFIDENCE_DIRECT_THRESHOLD: float = 0.85   # Path A: >= 0.85 -> Auto Triaged
    CONFIDENCE_REJECTION_THRESHOLD: float = 0.40 # Path C: < 0.40 -> Flagged for Manual Review

    # Supabase Persistence
    SUPABASE_URL: str = Field(default="", description="Supabase project URL")
    SUPABASE_KEY: str = Field(default="", description="Supabase Anon or Service Role Key")

    # CORS Configuration
    CORS_ORIGINS: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
