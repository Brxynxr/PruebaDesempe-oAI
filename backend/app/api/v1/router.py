from fastapi import APIRouter
from app.api.v1.endpoints import health, chat

# Router principal v1 que agrupa todos los sub-endpoints
api_v1_router = APIRouter()

# Registrar rutas de verificación de salud
api_v1_router.include_router(health.router, tags=["Health"])

# Registrar rutas de chat de atención al cliente
api_v1_router.include_router(chat.router, tags=["Chat"])
