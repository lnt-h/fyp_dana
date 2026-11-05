from fastapi import APIRouter

from app.api.routes import catalog, health, identity, preferences

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(identity.router, prefix="/v1")
api_router.include_router(preferences.router, prefix="/v1")
api_router.include_router(catalog.router, prefix="/v1")
