from fastapi import APIRouter
from app.api.v1.endpoints import health, chat, metrics

# Main v1 API Router aggregating endpoint modules
api_v1_router = APIRouter()

# Register health check routes
api_v1_router.include_router(health.router, tags=["Health"])

# Register customer support chat routes
api_v1_router.include_router(chat.router, tags=["Chat"])

# Register analytics metrics routes
api_v1_router.include_router(metrics.router, tags=["Metrics"])
