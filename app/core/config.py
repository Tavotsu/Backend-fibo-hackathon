import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    Configuración centralizada de la aplicación
    Todas las variables de entorno se cargan aquí
    """
    
    # Bria AI API Configuration
    BRIA_API_KEY: str = os.getenv("BRIA_API_KEY", "")
    BRIA_API_URL: str = "https://engine.prod.bria-api.com/v2"
    BRIA_SP_ENDPOINT: str = "/structured_prompt/generate"
    BRIA_IMAGE_ENDPOINT: str = "/image/generate"
    
    # OpenAI para agente LLM (opcional, alternativa a Gemini)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Google Gemini (usado por FIBO internamente)
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # MongoDB
    MONGO_URI: str = os.getenv("MONGO_URI", "")
    DB_NAME: str = "ai_art_director"
    
    # Supabase Storage (S3-compatible)
    SUPABASE_ENDPOINT_URL: str = os.getenv("SUPABASE_ENDPOINT_URL", "")
    SUPABASE_ACCESS_KEY: str = os.getenv("SUPABASE_ACCESS_KEY", "")
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY", "")
    SUPABASE_BUCKET_NAME: str = os.getenv("SUPABASE_BUCKET_NAME", "")
    SUPABASE_REGION: str = os.getenv("SUPABASE_REGION", "us-east-1")
    
    # Ollama LLM Configuration (para mejoras de prompts)
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
    
    # Async Job Configuration
    DEFAULT_VARIATIONS: int = int(os.getenv("DEFAULT_VARIATIONS", "4"))
    DEFAULT_TIMEOUT_SEC: int = int(os.getenv("DEFAULT_TIMEOUT_SEC", "300"))
    DEFAULT_POLL_EVERY_SEC: int = int(os.getenv("DEFAULT_POLL_EVERY_SEC", "2"))
    
    # CORS Configuration
    CORS_ALLOW_ORIGINS: str = os.getenv("CORS_ALLOW_ORIGINS", "*")
    
    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Data directory for uploaded images
    DATA_DIR: str = os.getenv("DATA_DIR", "./data")
    
    class Config:
        env_file = ".env"
        case_sensitive = True,
        extra="ignore"

# Singleton instance
settings = Settings()
