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
    BRIA_API_URL: str = "https://engine.prod.bria-api.com/v1"
    BRIA_IMAGE_GENERATE_ENDPOINT: str = "/v2/image/generate"
    BRIA_STRUCTURED_PROMPT_ENDPOINT: str = "/v2/structured_prompt/generate"
    
    # OpenAI para agente LLM (opcional, alternativa a Gemini)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Google Gemini (usado por FIBO internamente)
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # MongoDB
    MONGO_URI: str = os.getenv("MONGO_URI", "")
    DB_NAME: str = "ai_art_director"
    
    # Supabase Storage & Auth
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "") # Service Role Key for Backend or Anon if just verifying
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "") # Optional for manual verify
    
    # S3 Compatibility (Keep existing if relying on boto3)
    SUPABASE_ENDPOINT_URL: str = os.getenv("SUPABASE_ENDPOINT_URL", "")
    SUPABASE_ACCESS_KEY: str = os.getenv("SUPABASE_ACCESS_KEY", "")
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY", "")
    SUPABASE_BUCKET_NAME: str = os.getenv("SUPABASE_BUCKET_NAME", "")
    SUPABASE_REGION: str = os.getenv("SUPABASE_REGION", "us-east-1")

    # Auth Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-it")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 1 week
    
    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True,
        extra="ignore"

# Singleton instance
settings = Settings()
