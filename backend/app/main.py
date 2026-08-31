import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.security import limiter
from app.api.v1.router import api_v1_router
from app.services.ingestion_service import IngestionService
from app.db.vector_store import VectorStore

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida de la aplicación FastAPI.
    Al iniciar la aplicación, se realiza la ingesta automática de los documentos del negocio
    en ChromaDB si la colección no se encuentra poblada.
    """
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    vector_store = VectorStore(collection_name="academia_lumina_kb")
    
    if vector_store.count() == 0:
        ingestion = IngestionService(data_dir=data_dir)
        docs = ingestion.load_documents()
        chunks = ingestion.create_chunks(docs)
        vector_store.add_chunks(chunks)
        print(f"[Lifespan] Base de datos vectorial poblada con {len(chunks)} fragmentos.")
    else:
        print(f"[Lifespan] Base de datos vectorial activa con {vector_store.count()} fragmentos.")
    
    yield

# Inicialización de la aplicación FastAPI con metadata oficial
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Backend modular con RAG, Groq Llama 3.3 70B y 4 protecciones de seguridad para Academia Lumina.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Asociar el limiter de SlowAPI a la aplicación
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
