import os
import logging
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

from app.db.session import init_db, SessionLocal
from app.core.auth import seed_initial_admin

logger = logging.getLogger("lumina")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI application lifespan. Initializes SQLite DB, seeds admin user, and auto-ingests business documents into ChromaDB on startup."""
    # 1. Initialize SQLite persistence and seed admin account
    init_db()
    with SessionLocal() as db:
        seed_initial_admin(db)
    logger.info("SQLite database and Admin seed initialized.")

    # 2. Populate Vector Store if needed
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    vector_store = VectorStore(collection_name="academia_lumina_kb")
    
    if vector_store.count() == 0:
        ingestion = IngestionService(data_dir=data_dir)
        docs = ingestion.load_documents()
        chunks = ingestion.create_chunks(docs)
        vector_store.add_chunks(chunks)
        logger.info("Vector database populated with %d chunks.", len(chunks))
    else:
        logger.info("Vector database active with %d chunks.", vector_store.count())
    
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Modular backend with RAG, Groq LLM and 4 security layers for Academia Lumina.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — parse allowed origins from settings or environment
raw_origins = [orig.strip() for orig in settings.ALLOWED_ORIGINS.split(",") if orig.strip()]
if not raw_origins:
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("ALLOWED_ORIGINS environment variable must be explicitly configured in production.")
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"]
else:
    allowed_origins = raw_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)

app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/", summary="Root welcome route")
def root():
    """Root route for quick health check."""
    return {
        "message": f"Welcome to the {settings.APP_NAME} API",
        "docs": "/docs",
        "health": "/api/v1/health"
    }
