from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Gemini Configuration
    gemini_api_key: str
    gemini_model: str = "gemini-pro"
    gemini_embedding_model: str = "models/embedding-001"
    
    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "insurance_claims"
    embedding_dimension: int = 768
    
    # Backend Configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    debug_mode: bool = True
    
    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()
