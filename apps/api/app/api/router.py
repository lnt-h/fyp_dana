from fastapi import APIRouter

from app.api.routes import (
    admin,
    catalog,
    deletion,
    health,
    identity,
    preferences,
    previews,
    trips,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(identity.router, prefix="/v1")
api_router.include_router(preferences.router, prefix="/v1")
api_router.include_router(catalog.router, prefix="/v1")
api_router.include_router(trips.router, prefix="/v1")
api_router.include_router(previews.router, prefix="/v1")
api_router.include_router(deletion.router, prefix="/v1")
api_router.include_router(admin.router, prefix="/v1")
