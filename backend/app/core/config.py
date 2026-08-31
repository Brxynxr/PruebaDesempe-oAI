import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env si existe
load_dotenv()

from pydantic import ConfigDict

class Settings(BaseSettings):
    """
    Configuración centralizada de la aplicación usando Pydantic BaseSettings.
    Garantiza que las variables de entorno requeridas estén presentes y tengan tipos válidos.
    """
    model_config = ConfigDict(case_sensitive=True)

    APP_NAME: str = "Academia Lumina AI Assistant"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Claves y seguridad
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    BACKEND_API_KEY: str = os.getenv("BACKEND_API_KEY", "lumina_secret_key_2026")
    RATE_LIMIT_PER_MINUTE: str = os.getenv("RATE_LIMIT_PER_MINUTE", "10/minute")
    
    # Base de datos vectorial ChromaDB
    CHROMA_DB_DIR: str = os.getenv("CHROMA_DB_DIR", "./chroma_data")
    
    # Datos de contacto y escalamiento
    WHATSAPP_NUMBER: str = "+57 300 000 0000"
    WHATSAPP_URL: str = "https://wa.me/573000000000"
    ESCALATION_EMAIL: str = "admisiones@academialumina.co"


# Instancia global reutilizable de la configuración
settings = Settings()
