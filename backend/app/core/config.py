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
    
    # Database Configuration (Configurable for SQLite, PostgreSQL, etc.)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # API Keys and Security
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_API_KEYS: str = os.getenv("GROQ_API_KEYS", os.getenv("GROQ_API_KEY", ""))
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    BACKEND_API_KEY: str = os.getenv("BACKEND_API_KEY", "lumina_dev_api_key_2026" if os.getenv("ENVIRONMENT", "development") != "production" else "")
    RATE_LIMIT_PER_MINUTE: str = os.getenv("RATE_LIMIT_PER_MINUTE", "10/minute")
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # ChromaDB persistence directory
    CHROMA_DB_DIR: str = os.getenv("CHROMA_DB_DIR", "./chroma_data")
    
    # Contact and escalation parameters (100% loaded from environment variables)
    ADVISOR_NAME: str = os.getenv("ADVISOR_NAME", "Admissions Advisor")
    WHATSAPP_NUMBER: str = os.getenv("WHATSAPP_NUMBER", "+57 300 000 0000")
    WHATSAPP_URL: str = os.getenv("WHATSAPP_URL", "https://wa.me/573000000000")
    ESCALATION_EMAIL: str = os.getenv("ESCALATION_EMAIL", "admissions@academialumina.edu.co")

    # Admin Authentication & JWT Settings
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "LuminaAdmin2026!" if os.getenv("ENVIRONMENT", "development") != "production" else "")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "lumina_jwt_secret_key_change_in_production_2026" if os.getenv("ENVIRONMENT", "development") != "production" else "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

    # SMTP Server configuration for lead notifications
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    SMTP_SENDER_EMAIL: str = os.getenv("SMTP_SENDER_EMAIL", "")

    # Telegram Bot configuration for instant lead and escalation push alerts
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    def validate_production_settings(self):
        """Validates critical security variables when deployed in production."""
        if self.ENVIRONMENT == "production":
            missing = []
            if not self.BACKEND_API_KEY:
                missing.append("BACKEND_API_KEY")
            if not self.JWT_SECRET_KEY:
                missing.append("JWT_SECRET_KEY")
            if not self.ADMIN_PASSWORD:
                missing.append("ADMIN_PASSWORD")
            if not self.GROQ_API_KEY:
                missing.append("GROQ_API_KEY")
            if missing:
                raise RuntimeError(
                    f"Production environment requires non-empty environment variables: {', '.join(missing)}. "
                    "Configure them in the Render Dashboard (Environment → Environment Variables)."
                )

# Global reusable configuration instance
settings = Settings()
settings.validate_production_settings()
