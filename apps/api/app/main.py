from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.config import get_settings
from app.db.session import engine
from app.observability import install_observability

# info.version of the documented contract (docs/04-design/api/openapi.yaml).
API_VERSION = "1.0.4"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=API_VERSION,
        lifespan=lifespan,
        docs_url=None if settings.environment == "production" else "/docs",
    )
    install_observability(application)
    application.include_router(api_router)
    return application


app = create_app()
