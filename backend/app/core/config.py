import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Locate absolute path of .env file inside the backend folder
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(base_dir, ".env")

if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path, override=False)
else:
    load_dotenv(override=False)

class Settings(BaseSettings):
    """
    Centralized application configuration using Pydantic BaseSettings.
    Ensures required environment variables are present and have valid types.
    """
    model_config = ConfigDict(case_sensitive=True)

    APP_NAME: str = "Academia Lumina AI Assistant"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # API Keys and Security
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    BACKEND_API_KEY: str = os.getenv("BACKEND_API_KEY", "lumina_secret_key_2026")
    RATE_LIMIT_PER_MINUTE: str = os.getenv("RATE_LIMIT_PER_MINUTE", "10/minute")
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000")
    
    # ChromaDB persistence directory
    CHROMA_DB_DIR: str = os.getenv("CHROMA_DB_DIR", "./chroma_data")
    
    # Contact and escalation parameters
    WHATSAPP_NUMBER: str = "+57 324 783 6387"
    WHATSAPP_URL: str = "https://wa.me/573247836387"
    ESCALATION_EMAIL: str = os.getenv("ESCALATION_EMAIL", "bmegami7@gmail.com")

    # SMTP Server configuration for sending real emails
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    SMTP_SENDER_EMAIL: str = os.getenv("SMTP_SENDER_EMAIL", "")

# Global reusable configuration instance
settings = Settings()
