from fastapi import APIRouter
from app.api.v1.endpoints import health, chat, metrics, admin, websocket

# Main v1 router that groups all sub-endpoints
api_v1_router = APIRouter()

# Register health check routes
api_v1_router.include_router(health.router, tags=["Health"])

# Register customer service chat routes
api_v1_router.include_router(chat.router, tags=["Chat"])

# Register metrics and analytics routes
api_v1_router.include_router(metrics.router, tags=["Metrics"])

# Register admin and backoffice routes
api_v1_router.include_router(admin.router)

# Register real-time WebSocket routes
api_v1_router.include_router(websocket.router)

