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
    Ensures required environment variables are loaded and validated.
    """
    model_config = ConfigDict(case_sensitive=True)

    APP_NAME: str = "Academia Lumina AI Assistant"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # API Keys and Security
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    BACKEND_API_KEY: str = os.getenv("BACKEND_API_KEY", "lumina_dev_api_key_2026")
    RATE_LIMIT_PER_MINUTE: str = os.getenv("RATE_LIMIT_PER_MINUTE", "10/minute")
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000")
    
    # ChromaDB persistence directory
    CHROMA_DB_DIR: str = os.getenv("CHROMA_DB_DIR", "./chroma_data")
    
    # Contact and escalation parameters (100% loaded from environment variables)
    ADVISOR_NAME: str = os.getenv("ADVISOR_NAME", "Admissions Advisor")
    WHATSAPP_NUMBER: str = os.getenv("WHATSAPP_NUMBER", "+57 324 783 6387")
    WHATSAPP_URL: str = os.getenv("WHATSAPP_URL", "https://wa.me/573247836387")
    ESCALATION_EMAIL: str = os.getenv("ESCALATION_EMAIL", "admissions@academialumina.edu.co")

    # SMTP Server configuration for lead notifications
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    SMTP_SENDER_EMAIL: str = os.getenv("SMTP_SENDER_EMAIL", "")

# Global reusable configuration instance
settings = Settings()
