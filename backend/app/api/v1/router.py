from fastapi import APIRouter
from app.api.v1.endpoints import health, chat, metrics

# Router principal v1 que agrupa todos los sub-endpoints
api_v1_router = APIRouter()

# Registrar rutas de verificación de salud
api_v1_router.include_router(health.router, tags=["Health"])

# Registrar rutas de chat de atención al cliente
api_v1_router.include_router(chat.router, tags=["Chat"])

# Registrar rutas de métricas y analítica
api_v1_router.include_router(metrics.router, tags=["Metrics"])
