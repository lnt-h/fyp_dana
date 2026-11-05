from fastapi import APIRouter

from app.api.routes import deletion, health, identity, previews, trips

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(identity.router, prefix="/v1")
api_router.include_router(trips.router, prefix="/v1")
api_router.include_router(previews.router, prefix="/v1")
api_router.include_router(deletion.router, prefix="/v1")
