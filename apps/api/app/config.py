"""Gonarra API settings (``GONARRA_*`` environment variables, ``apps/api/.env``).

Google Maps Platform SKU protection (DEC-018, ADR-006): every Routes call must request
``routingPreference=TRAFFIC_UNAWARE`` (the Essentials SKU; traffic-aware routing is billed at a
higher SKU), and every Places request must keep the field mask ``id,businessStatus,location``
(Essentials-level fields only). Widening either moves the call to a pricier SKU and burns the
free tier; change it only with a decision in ``docs/decisions.md``.
"""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, SecretStr, field_validator
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
    # Curator role (T-06): comma-separated Clerk user IDs (JWT `sub`) allowed on /v1/admin.
    # Empty means nobody is a curator (default deny).
    curator_clerk_user_ids: str = ""
    # Clerk Backend API secret (``sk_...``), used only to delete the Clerk user after an account
    # deletion purge (FR-071). Unset: the purge still completes and a warning is logged.
    clerk_secret_key: SecretStr | None = None

    # Product scope (DEC-013): FYP release serves one enabled city.
    default_city_code: str = "da-nang"

    # Public base URL that media_assets.object_key is appended to (catalog Media.url).
    media_base_url: str = "http://localhost:8000/media"

    # Provider secrets (ADR-006, BR-046): server-side only, never logged, never sent to clients.
    gemini_api_key: SecretStr | None = None
    groq_api_key: SecretStr | None = None
    tavily_api_key: SecretStr | None = None
    # Google Maps Platform (Routes + Places). See the module docstring: Routes TRAFFIC_UNAWARE
    # only; Places field mask ``id,businessStatus,location`` only (SKU protection).
    google_maps_api_key: SecretStr | None = None

    # Feature flags (ADR-014 research agent; DEC-019 Could-scope prices).
    research_agent_enabled: bool = False
    stay_prices_enabled: bool = False
    # Haversine Routes estimates for local development when no Google Maps key is set (M3-B).
    # Never allowed in production (select_provider raises); estimates are never cached.
    routes_estimate_enabled: bool = False

    # Free-tier quota caps (DEC-018, architecture §3.3). Exceeding a cap degrades, never fails
    # silently. Per-account caps are per calendar day (UTC+7); global caps per day unless noted.
    quota_account_proposals_per_day: int = 10
    quota_account_questions_per_day: int = 40
    quota_gemini_flash_per_day: int = 200
    quota_gemini_flash_lite_per_day: int = 600
    # Query/corpus embeddings (gemini-embedding-001); query embeddings are cached 90 d.
    quota_gemini_embed_per_day: int = 1000
    quota_groq_per_day: int = 800
    quota_tavily_per_day: int = 25
    quota_tavily_per_month: int = 700
    quota_places_per_day: int = 150
    # Routes matrix elements. 300/day ≈ 9 000/month, kept under the Routes Essentials monthly
    # free threshold so the free tier is never exceeded (free-tier protection).
    quota_routes_elements_per_day: int = 300

    @field_validator(
        "clerk_issuer",
        "clerk_jwks_url",
        "clerk_audience",
        "clerk_secret_key",
        "gemini_api_key",
        "groq_api_key",
        "tavily_api_key",
        "google_maps_api_key",
        mode="before",
    )
    @classmethod
    def _blank_is_unset(cls, value: object) -> object:
        # An empty .env line (``GONARRA_GEMINI_API_KEY=``) means "not configured", not "".
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def authorized_parties(self) -> frozenset[str]:
        return frozenset(
            value.strip() for value in self.clerk_authorized_parties.split(",") if value.strip()
        )

    @property
    def curator_subjects(self) -> frozenset[str]:
        return frozenset(
            value.strip() for value in self.curator_clerk_user_ids.split(",") if value.strip()
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
