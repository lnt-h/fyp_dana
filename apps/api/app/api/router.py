from fastapi import APIRouter

from app.api.routes import admin, health, identity

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(identity.router, prefix="/v1")
api_router.include_router(admin.router, prefix="/v1")
