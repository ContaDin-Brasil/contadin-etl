"""ContaDIN - API"""

from fastapi import FastAPI

from app.api.routers import ai_router, data_router

app = FastAPI()

app.include_router(ai_router)
app.include_router(data_router)
