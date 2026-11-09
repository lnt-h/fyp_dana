from fastapi import APIRouter, Depends

from app.api.input_guard import reject_nul_characters
from app.api.routes import (
    admin,
    catalog,
    deletion,
    guide,
    health,
    identity,
    preferences,
    previews,
    trips,
)

# Every route rejects NUL characters in the path, query and JSON body with 422 first.
api_router = APIRouter(dependencies=[Depends(reject_nul_characters)])
api_router.include_router(health.router)
api_router.include_router(identity.router, prefix="/v1")
api_router.include_router(preferences.router, prefix="/v1")
api_router.include_router(catalog.router, prefix="/v1")
api_router.include_router(trips.router, prefix="/v1")
api_router.include_router(previews.router, prefix="/v1")
api_router.include_router(deletion.router, prefix="/v1")
api_router.include_router(guide.router, prefix="/v1")
api_router.include_router(admin.router, prefix="/v1")
