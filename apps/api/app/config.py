"""Gonarra API settings (``GONARRA_*`` environment variables, ``apps/api/.env``).

Google Maps Platform SKU protection (DEC-018, ADR-006): every Routes call must request
``routingPreference=TRAFFIC_UNAWARE`` (the Essentials SKU; traffic-aware routing is billed at a
higher SKU), and every Places request must keep the field mask ``id,businessStatus,location``
(Essentials-level fields only). Widening either moves the call to a pricier SKU and burns the
free tier; change it only with a decision in ``docs/decisions.md``.
"""

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, AnyHttpUrl, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ESTIMATE_ENVIRONMENTS = frozenset({"development", "test", "demo"})
# Environments where provider persistence policies in DRAFT status may be used (ADR-006);
# staging and production require ACTIVE policies.
DRAFT_POLICY_ENVIRONMENTS = frozenset({"development", "test", "demo"})
# Environments where the shared demo user (``demo_shared_user``) may be switched on.
DEMO_USER_ENVIRONMENTS = frozenset({"development", "test", "demo"})
# Subject (in place of a Clerk ``sub``) of the one account shared by every unsigned demo caller.
DEMO_SHARED_SUBJECT = "demo_shared_user"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="GONARRA_",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "Gonarra API"
    # Fails safe: unset means ``production`` (no /docs, no estimates, no demo user, ACTIVE provider
    # policies only). Local development sets ``GONARRA_ENVIRONMENT=development`` in
    # ``apps/api/.env``; the test suite sets ``test`` (``tests/conftest.py``).
    # ``demo``: owner demo builds without Google Maps Platform (estimate routing may be enabled,
    # legs are labelled ``estimated``). Never used for staging or production.
    environment: Literal["development", "test", "demo", "staging", "production"] = "production"
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
    # Owner demo builds only (GONARRA_DEMO_SHARED_USER): a request with no Authorization header
    # is treated as the one shared account ``demo_shared_user`` instead of 401, so anyone who
    # opens the app can use it without signing in. A bearer token, when sent, is still verified.
    # Never grants the curator role (only ``curator_clerk_user_ids`` does). Refused unless
    # ``environment`` is development, test or demo (see ``_demo_user_only_outside_production``).
    demo_shared_user: bool = False

    # Product scope (DEC-013): FYP release serves one enabled city.
    default_city_code: str = "da-nang"
    # Guide session retention (OQ-019; expired sessions answer 404, Q-Q3 sweep).
    guide_session_ttl_days: int = 30

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
    # Research agent in propose_trip: off by default (SPK-004: 107-212 s per run). When on, it runs
    # only for a thin catalog pool and under ``research_timeout_s``; on timeout the plan proceeds.
    research_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "research_enabled", "GONARRA_RESEARCH_ENABLED", "GONARRA_RESEARCH_AGENT_ENABLED"
        ),
    )
    research_timeout_s: float = 45.0
    stay_prices_enabled: bool = False
    # Haversine Routes estimates when no Google Maps key is set (M3-B; demo mode). Allowed only
    # in development, test and demo (select_provider raises in staging/production); estimates are
    # never cached and every estimated leg carries ``estimated=true`` plus a LEG_ESTIMATED notice.
    routes_estimate_enabled: bool = False
    # Routes provider choice (GONARRA_ROUTES_PROVIDER): ``auto`` = Google when a key is set, else
    # the estimate when routes_estimate_enabled, else none. ``estimate`` forces the haversine
    # estimate even when a (possibly unusable) Google key is present — still refused in
    # staging/production. ``google`` never estimates; ``none`` makes every leg UNAVAILABLE.
    routes_provider: Literal["auto", "google", "estimate", "none"] = "auto"

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

    @model_validator(mode="after")
    def _demo_user_only_outside_production(self) -> "Settings":
        if self.demo_shared_user and self.environment not in DEMO_USER_ENVIRONMENTS:
            raise ValueError(
                "GONARRA_DEMO_SHARED_USER is allowed only when GONARRA_ENVIRONMENT is "
                "development, test or demo"
            )
        return self

    @property
    def draft_policies_allowed(self) -> bool:
        """Whether DRAFT provider policies may stand in for ACTIVE ones (never staging/prod)."""
        return self.environment in DRAFT_POLICY_ENVIRONMENTS

    @property
    def estimates_allowed(self) -> bool:
        """Whether the haversine estimate provider may exist in this environment."""
        return self.environment in ESTIMATE_ENVIRONMENTS

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
