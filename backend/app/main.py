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
    Application lifespan handler.
    On startup, automatically populates ChromaDB vector database with business knowledge base
    documents if collection is currently empty.
    """
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    vector_store = VectorStore(collection_name="academia_lumina_kb")
    
    if vector_store.count() == 0:
        ingestion = IngestionService(data_dir=data_dir)
        docs = ingestion.load_documents()
        chunks = ingestion.create_chunks(docs)
        vector_store.add_chunks(chunks)
        print(f"[Lifespan] Vector store populated with {len(chunks)} knowledge chunks.")
    else:
        print(f"[Lifespan] Vector store active with {vector_store.count()} indexed chunks.")
    
    yield

# FastAPI application initialization with metadata
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Modular FastAPI backend with RAG, Groq Llama 3.3 70B, and 4 security layers for Academia Lumina.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Register SlowAPI rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API router
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/", summary="Root welcome endpoint")
def root():
    """
    Root path for quick availability check.
    """
    return {
        "message": f"Welcome to the {settings.APP_NAME} API",
        "docs": "/docs",
        "health": "/api/v1/health"
    }
