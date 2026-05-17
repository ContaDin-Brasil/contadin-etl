"""Routers da API"""

from app.api.routers.ai import router as ai_router
from app.api.routers.data import router as data_router
from app.api.routers.objectives_insights import router as objectives_insights_router

__all__ = ["ai_router", "data_router", "objectives_insights_router"]
