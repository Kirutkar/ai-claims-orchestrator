from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Gemini Configuration
    gemini_api_key: str
    gemini_model: str = "gemini-1.5-flash"  # Updated: gemini-pro is deprecated, using gemini-1.5-flash (faster) or gemini-1.5-pro (better quality)
    gemini_embedding_model: str = "models/embedding-001"
    
    # Qdrant Configuration - Docker-aware
    # Supports both QDRANT_URL (cloud) and QDRANT_HOST (local)
    qdrant_host: str = os.getenv("QDRANT_HOST", os.getenv("QDRANT_URL", "localhost"))
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "insurance_claims")
    embedding_dimension: int = 768

    # Backend Configuration
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("PORT", os.getenv("BACKEND_PORT", "8000")))
    debug_mode: bool = os.getenv("DEBUG_MODE", "true").lower() == "true"
    
    # CORS Configuration - Docker-aware
    # Default origins for local development and Docker
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,http://frontend:3000"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file


@lru_cache()
def get_settings():
    return Settings()
