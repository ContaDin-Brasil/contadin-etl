"""Routers da API"""

from app.api.routers.ai import router as ai_router
from app.api.routers.data import router as data_router

__all__ = ["ai_router", "data_router"]
