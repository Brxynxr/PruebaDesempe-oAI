from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_v1_router

# Inicialización de la aplicación FastAPI con metadata oficial
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Backend modular con RAG y FastAPI para el asistente de atención al cliente de Academia Lumina.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración de CORS para permitir peticiones desde el frontend en React e integraciones como n8n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción se restringe a los dominios del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión del router principal de API v1
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/", summary="Ruta raíz de bienvenida")
def root():
    """
    Ruta raíz para comprobación rápida de funcionamiento.
    """
    return {
        "message": f"Bienvenido a la API de {settings.APP_NAME}",
        "docs": "/docs",
        "health": "/api/v1/health"
    }
