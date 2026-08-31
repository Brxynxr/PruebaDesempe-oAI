import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Settings(BaseSettings):
    """
    Centralized application settings powered by Pydantic BaseSettings.
    Ensures required environment variables exist and are strictly typed.
    """
    model_config = ConfigDict(case_sensitive=True)

    APP_NAME: str = "Academia Lumina AI Assistant"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Credentials & Security
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    BACKEND_API_KEY: str = os.getenv("BACKEND_API_KEY", "lumina_secret_key_2026")
    RATE_LIMIT_PER_MINUTE: str = os.getenv("RATE_LIMIT_PER_MINUTE", "10/minute")
    
    # ChromaDB Vector Database Storage Directory
    CHROMA_DB_DIR: str = os.getenv("CHROMA_DB_DIR", "./chroma_data")
    
    # Contact & Escalation Parameters
    WHATSAPP_NUMBER: str = "+57 324 783 6387"
    WHATSAPP_URL: str = "https://wa.me/573247836387"
    ESCALATION_EMAIL: str = "admisiones@academialumina.co"

# Global reusable settings instance
settings = Settings()
