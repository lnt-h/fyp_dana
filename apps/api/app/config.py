from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="GONARRA_",
        extra="ignore",
    )

    app_name: str = "Gonarra API"
    environment: Literal["development", "test", "staging", "production"] = "development"
    database_url: str = "postgresql+psycopg://gonarra:gonarra@localhost:5432/gonarra"
    clerk_issuer: AnyHttpUrl | None = None
    clerk_jwks_url: AnyHttpUrl | None = None
    clerk_audience: str | None = None
    clerk_authorized_parties: str = ""

    @property
    def authorized_parties(self) -> frozenset[str]:
        return frozenset(
            value.strip()
            for value in self.clerk_authorized_parties.split(",")
            if value.strip()
        )

    @property
    def jwks_url(self) -> str | None:
        if self.clerk_jwks_url is not None:
            return str(self.clerk_jwks_url)
        if self.clerk_issuer is not None:
            return f"{str(self.clerk_issuer).rstrip('/')}/.well-known/jwks.json"
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
