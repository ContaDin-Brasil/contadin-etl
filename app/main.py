"""ContaDIN - API"""

from fastapi import FastAPI

from app.api.domain.generate.routers import router as generate_router

app = FastAPI()

app.include_router(generate_router)
