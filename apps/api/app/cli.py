"""Gonarra operations CLI (ADR-012).

Usage from apps/api:
    uv run python -m app.cli seed        # idempotent reference data for Đà Nẵng
    uv run python -m app.cli db-check    # alembic head vs database revision
    uv run python -m app.cli run-deletion-jobs   # purge accounts with a pending deletion job
    uv run python -m app.cli routes warm [--limit 50]   # pre-fill routes_matrix_cache (M3-B)

Content pipeline (DEC-022, app/ingestion/cli.py): `policy list|activate`, `areas load`,
`ingest wikidata|wikipedia|osm|commons|sheet`, `web-candidates promote`, `publish auto [--dry-run]`,
`closure-rules load` and `pipeline run` (all steps). See apps/api/data/README.md.

Grounded descriptions (D3, app/research/enrich.py):
    uv run python -m app.cli enrich descriptions [--limit 150] [--food-cafe-cap 40]
Then `publish auto`, `publish summary` and `publish audit-sample`.
"""

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import typer
from sqlalchemy import delete, func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.system import SYSTEM_ACCOUNT_CLERK_USER_ID
from app.db.session import engine, session_factory
from app.models.account import Account
from app.models.providers import DataProvider, ProviderFieldRule, ProviderPolicy
from app.models.reference import Area, Category, City, FactField

app = typer.Typer(help="Gonarra operations CLI.", no_args_is_help=True)

# ---------------------------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------------------------

# Rough post-merger Đà Nẵng envelope (former Đà Nẵng + Quảng Nam, incl. Hội An and Cù Lao Chàm).
# A generous rectangle, deliberately larger than the city, so OUTSIDE_CITY never rejects a real
# Hội An place. Replace with the authoritative polygon from OQ-121.
_DA_NANG_RING = (
    (107.20, 14.90),
    (108.95, 14.90),
    (108.95, 16.35),
    (107.20, 16.35),
    (107.20, 14.90),
)
DA_NANG_BOUNDARY_EWKT = (
    "SRID=4326;MULTIPOLYGON(((" + ", ".join(f"{lng} {lat}" for lng, lat in _DA_NANG_RING) + ")))"
)


@dataclass(frozen=True)
class CitySeed:
    code: str
    name_vi: str
    name_en: str
    is_enabled: bool
    boundary: str | None


CITIES: tuple[CitySeed, ...] = (
    # Đà Nẵng only (owner 2026-11-08): the product has a single city. Hội An is an area of Đà Nẵng
    # (2025 merger), not a city. The former disabled roadmap rows (ha-noi, ho-chi-minh-city, hue)
    # are removed by the seed when nothing references them (remove_stale_cities).
    CitySeed("da-nang", "Đà Nẵng", "Da Nang", True, DA_NANG_BOUNDARY_EWKT),
)

# Travel areas of Đà Nẵng (ADR-012 0.4, OQ-121): curator-defined, not wards. Boundaries stay NULL
# until the curator draws them.
AREAS: tuple[tuple[str, str, str], ...] = (
    ("da-nang-center", "Trung tâm Đà Nẵng (Hải Châu, Thanh Khê)", "Da Nang city centre"),
    ("son-tra", "Bán đảo Sơn Trà", "Son Tra Peninsula"),
    ("my-khe-ngu-hanh-son", "Biển Mỹ Khê – Ngũ Hành Sơn", "My Khe Beach – Marble Mountains"),
    ("ba-na-hoa-vang", "Bà Nà – Hòa Vang", "Ba Na Hills – Hoa Vang"),
    ("hoi-an-old-town", "Phố cổ Hội An", "Hoi An Ancient Town"),
    (
        "hoi-an-beaches-islands",
        "Biển và đảo Hội An (An Bàng, Cửa Đại, Cù Lao Chàm)",
        "Hoi An beaches and islands (An Bang, Cua Dai, Cham Islands)",
    ),
    # 2026-11-08: real tourist clusters outside the first six polygons (data/areas/da-nang.yaml).
    (
        "hoi-an-outskirts",
        "Ven Hội An (Thanh Chiêm, Gò Nổi, Nam Phước)",
        "Hoi An outskirts (Thanh Chiem, Go Noi, Nam Phuoc)",
    ),
    ("my-son", "Thánh địa Mỹ Sơn", "My Son Sanctuary"),
    ("tam-ky", "Tam Kỳ – Tam Thanh", "Tam Ky – Tam Thanh"),
)

CATEGORIES: tuple[tuple[str, str, str], ...] = (
    ("HERITAGE", "Di sản & di tích", "Heritage & historic sites"),
    ("MUSEUM", "Bảo tàng", "Museums"),
    ("RELIGIOUS_SITE", "Chùa, đền & nhà thờ", "Pagodas, temples & churches"),
    ("BEACH", "Biển", "Beaches"),
    ("NATURE", "Thiên nhiên", "Nature"),
    ("VIEWPOINT", "Điểm ngắm cảnh", "Viewpoints"),
    ("MARKET", "Chợ", "Markets"),
    ("FOOD", "Ẩm thực", "Food"),
    ("CAFE", "Cà phê", "Cafés"),
    ("NIGHTLIFE", "Về đêm", "Evening & nightlife"),
    ("THEME_PARK", "Khu vui chơi", "Theme parks"),
    ("CRAFT_VILLAGE", "Làng nghề", "Craft villages"),
)

# schema.sql Section 9: operational fact vocabulary, 180-day staleness (ASM-008).
FACT_FIELDS: tuple[tuple[str, bool, bool, str, int | None], ...] = (
    ("OPENING_HOURS", True, True, "HOURS", 180),
    ("ADMISSION_PRICE", True, True, "MONEY", 180),
    ("ADDRESS_VI", True, True, "TEXT", 180),
    ("ENTRANCE_LOCATION", True, True, "LOCATION", 180),
    ("PAYMENT_METHODS", True, False, "TEXT", 180),
    ("DRESS_CODE", True, False, "TEXT", 180),
    ("ACCESS_RULES", True, False, "TEXT", 180),
)

CANONICAL = "ALLOW_CANONICAL"
EPHEMERAL = "ALLOW_EPHEMERAL"
IDENTIFIER = "ALLOW_IDENTIFIER_ONLY"
DENY = "DENY"


@dataclass(frozen=True)
class ProviderSeed:
    key: str
    display_name: str
    kind: str
    terms_url: str
    purpose: str
    attribution: str | None
    # field name -> (persistence class, max retention)
    fields: dict[str, tuple[str, timedelta | None]]


_OPEN_PLACE_FIELDS: dict[str, tuple[str, timedelta | None]] = {
    "id": (IDENTIFIER, None),
    "name": (CANONICAL, None),
    "location": (CANONICAL, None),
    "category": (CANONICAL, None),
}

# ADR-006 0.2. Policies are seeded as DRAFT revision 1: the owner records the terms version and
# activates each policy before the first live call (OQ-016).
PROVIDERS: tuple[ProviderSeed, ...] = (
    ProviderSeed(
        "overture_places",
        "Overture Maps Places",
        "OPEN_DATASET",
        "https://docs.overturemaps.org/attribution/",
        "Candidate import (ADR-012)",
        "© Overture Maps Foundation",
        _OPEN_PLACE_FIELDS,
    ),
    ProviderSeed(
        "foursquare_os_places",
        "Foursquare Open Source Places",
        "OPEN_DATASET",
        "https://opensource.foursquare.com/os-places/",
        "Candidate import (ADR-012)",
        "Foursquare Open Source Places (Apache-2.0)",
        _OPEN_PLACE_FIELDS,
    ),
    ProviderSeed(
        "wikidata",
        "Wikidata",
        "OPEN_DATASET",
        "https://www.wikidata.org/wiki/Wikidata:Licensing",
        "Candidate import and identity (ADR-012)",
        "Wikidata (CC0)",
        {
            **_OPEN_PLACE_FIELDS,
            "description": (CANONICAL, None),
            "aliases": (CANONICAL, None),
            "sitelinks": (CANONICAL, None),
            "image": (CANONICAL, None),  # P18 Commons file names (commons.py)
        },
    ),
    # DEC-022: Wikipedia lead summaries become place descriptions and OVERVIEW chunks, with
    # CC BY-SA 4.0 attribution recorded per page revision.
    ProviderSeed(
        "wikipedia",
        "Wikipedia",
        "OPEN_DATASET",
        "https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use",
        "Place descriptions and Guide overview text with attribution (DEC-022)",
        "Wikipedia contributors (CC BY-SA 4.0)",
        {
            "title": (CANONICAL, None),
            "page_url": (CANONICAL, None),
            "summary": (CANONICAL, None),
        },
    ),
    # DEC-022: the owner's place sheet (CSV, apps/api/data/README.md); each row names its source.
    ProviderSeed(
        "gonarra_sheet",
        "Gonarra operator place sheet",
        "OPERATOR_DATA",
        "https://github.com/lnt-h/fyp_dana/blob/main/apps/api/data/README.md",
        "Owner-maintained places, descriptions and facts (DEC-022)",
        None,
        {
            "id": (IDENTIFIER, None),
            "name": (CANONICAL, None),
            "location": (CANONICAL, None),
            "category": (CANONICAL, None),
            "area": (CANONICAL, None),
            "short_description": (CANONICAL, None),
            "description": (CANONICAL, None),
            "wikidata_id": (IDENTIFIER, None),
            "source": (CANONICAL, None),
            "facts": (CANONICAL, None),
            "visit_minutes": (CANONICAL, None),
        },
    ),
    ProviderSeed(
        "openstreetmap",
        "OpenStreetMap",
        "OPEN_DATASET",
        "https://www.openstreetmap.org/copyright",
        "Candidate import, coordinates and opening hours (ADR-012, osm.py)",
        "© OpenStreetMap contributors (ODbL)",
        {
            **_OPEN_PLACE_FIELDS,
            "opening_hours": (CANONICAL, None),
            "facts": (CANONICAL, None),
            "website": (CANONICAL, None),
            "wikidata": (IDENTIFIER, None),
            "image": (CANONICAL, None),
            "wikimedia_commons": (CANONICAL, None),
        },
    ),
    ProviderSeed(
        "wikimedia_commons",
        "Wikimedia Commons",
        "MEDIA_LIBRARY",
        "https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia",
        "Place photos with per-file licence (commons.py)",
        "Wikimedia Commons contributors (per-file licence and author)",
        {
            "file_url": (CANONICAL, None),
            "creator": (CANONICAL, None),
            "license": (CANONICAL, None),
            "title": (CANONICAL, None),
            "description_url": (CANONICAL, None),
            "attribution": (CANONICAL, None),
            "width": (CANONICAL, None),
            "height": (CANONICAL, None),
            "mime": (CANONICAL, None),
        },
    ),
    # D3 (2026-11-08): grounded AI descriptions (app/research/enrich.py). The description is
    # Gonarra's own text written only from the cited source revisions; prompts and raw model
    # responses are never stored.
    ProviderSeed(
        "gonarra_ai_summary",
        "Gonarra grounded AI descriptions",
        "AI_SERVICE",
        "https://github.com/lnt-h/fyp_dana/blob/main/apps/api/data/README.md",
        "Place descriptions summarised from cited sources (enrich descriptions, D3)",
        "Short description written by Gonarra with AI assistance, only from the cited sources",
        {
            "description": (CANONICAL, None),
            "cited_urls": (CANONICAL, None),
            "model": (CANONICAL, None),
        },
    ),
    ProviderSeed(
        "google_places",
        "Google Places API",
        "RUNTIME_API",
        "https://cloud.google.com/maps-platform/terms",
        "Existence/status check of web candidates",
        "Google Maps",
        {
            "place_id": (IDENTIFIER, None),
            "location": (EPHEMERAL, timedelta(days=30)),
            "business_status": (DENY, None),
            "regular_opening_hours": (DENY, None),
        },
    ),
    ProviderSeed(
        "google_routes",
        "Google Routes API",
        "RUNTIME_API",
        "https://cloud.google.com/maps-platform/terms",
        "Leg distance and duration (ADR-011)",
        "Google Maps",
        {
            "distance_m": (EPHEMERAL, timedelta(days=30)),
            "duration_s": (EPHEMERAL, timedelta(days=30)),
        },
    ),
    ProviderSeed(
        "liteapi",
        "LiteAPI",
        "RUNTIME_API",
        "https://www.liteapi.travel/terms",
        "Indicative stay prices (Could, flag-gated)",
        "LiteAPI",
        {"price": (DENY, None), "rate": (DENY, None)},
    ),
    ProviderSeed(
        "gemini",
        "Google Gemini API",
        "AI_SERVICE",
        "https://ai.google.dev/gemini-api/terms",
        "Selection, rationales, Guide answers, embeddings",
        None,
        {
            "prompt": (DENY, None),
            "response": (DENY, None),
            "chunk_embedding": (CANONICAL, None),
            "query_embedding": (EPHEMERAL, timedelta(days=90)),
        },
    ),
    ProviderSeed(
        "groq",
        "Groq API",
        "AI_SERVICE",
        "https://groq.com/terms-of-use/",
        "Fallback model and research extraction",
        None,
        {"prompt": (DENY, None), "response": (DENY, None)},
    ),
    ProviderSeed(
        "tavily",
        "Tavily Search API",
        "WEB_SEARCH",
        "https://tavily.com/terms",
        "Research agent web search (ADR-014)",
        None,
        {
            "result_url": (EPHEMERAL, timedelta(days=7)),
            "result_title": (EPHEMERAL, timedelta(days=7)),
            "result_snippet": (EPHEMERAL, timedelta(days=7)),
        },
    ),
    ProviderSeed(
        "web_page",
        "Fetched web pages",
        "WEB_CONTENT",
        "https://www.robotstxt.org/",
        "Evidence pages for WEB_UNVERIFIED candidates (ADR-014)",
        None,
        {
            "url": (CANONICAL, None),
            "content_sha256": (CANONICAL, None),
            "retrieved_at": (CANONICAL, None),
            "extracted_text": (EPHEMERAL, timedelta(days=7)),
        },
    ),
)

PROVIDER_POLICY_TERMS_VERSION = "UNRECORDED"


async def remove_stale_cities(session: AsyncSession) -> list[str]:
    """Delete city rows not in :data:`CITIES` that nothing references (idempotent).

    Each delete runs in a savepoint; a city still referenced (areas, places, trips …) raises a
    foreign-key error and is kept. Returns the codes that were deleted."""
    keep = [city.code for city in CITIES]
    stale = (await session.execute(select(City.id, City.code).where(City.code.not_in(keep)))).all()
    removed: list[str] = []
    for city_id, code in stale:
        try:
            async with session.begin_nested():
                await session.execute(delete(City).where(City.id == city_id))
        except IntegrityError:
            typer.echo(f"city {code} is still referenced; kept", err=True)
            continue
        removed.append(code)
    return removed


async def seed_reference_data(session: AsyncSession) -> dict[str, int]:
    """Upsert cities, areas, categories, fact fields, providers, policies and field rules.

    Idempotent: reference rows are updated in place; policy revisions and their field rules are
    immutable once written, so existing ones are left untouched.
    """
    for city in CITIES:
        stmt = insert(City).values(
            code=city.code,
            name_vi=city.name_vi,
            name_en=city.name_en,
            time_zone="Asia/Ho_Chi_Minh",
            is_enabled=city.is_enabled,
            boundary=city.boundary,
        )
        await session.execute(
            stmt.on_conflict_do_update(
                index_elements=[City.code],
                set_={
                    "name_vi": stmt.excluded.name_vi,
                    "name_en": stmt.excluded.name_en,
                    "is_enabled": stmt.excluded.is_enabled,
                    "boundary": func.coalesce(City.boundary, stmt.excluded.boundary),
                },
            )
        )

    await remove_stale_cities(session)
    city_id = await session.scalar(select(City.id).where(City.code == "da-nang"))
    assert city_id is not None
    for sort_order, (code, name_vi, name_en) in enumerate(AREAS, start=1):
        area_stmt = insert(Area).values(
            code=code, city_id=city_id, name_vi=name_vi, name_en=name_en, sort_order=sort_order
        )
        await session.execute(
            area_stmt.on_conflict_do_update(
                index_elements=[Area.code],
                set_={
                    "name_vi": area_stmt.excluded.name_vi,
                    "name_en": area_stmt.excluded.name_en,
                    "sort_order": area_stmt.excluded.sort_order,
                },
            )
        )

    for sort_order, (code, name_vi, name_en) in enumerate(CATEGORIES, start=1):
        cat_stmt = insert(Category).values(
            code=code, name_vi=name_vi, name_en=name_en, sort_order=sort_order
        )
        await session.execute(
            cat_stmt.on_conflict_do_update(
                index_elements=[Category.code],
                set_={
                    "name_vi": cat_stmt.excluded.name_vi,
                    "name_en": cat_stmt.excluded.name_en,
                    "sort_order": cat_stmt.excluded.sort_order,
                },
            )
        )

    for code, operational, required, kind, stale in FACT_FIELDS:
        ff_stmt = insert(FactField).values(
            code=code,
            is_operational=operational,
            required_for_publication=required,
            value_kind=kind,
            stale_after_days=stale,
        )
        await session.execute(
            ff_stmt.on_conflict_do_update(
                index_elements=[FactField.code],
                set_={
                    "is_operational": ff_stmt.excluded.is_operational,
                    "required_for_publication": ff_stmt.excluded.required_for_publication,
                    "value_kind": ff_stmt.excluded.value_kind,
                    "stale_after_days": ff_stmt.excluded.stale_after_days,
                },
            )
        )

    for provider in PROVIDERS:
        dp_stmt = insert(DataProvider).values(
            provider_key=provider.key,
            display_name=provider.display_name,
            provider_kind=provider.kind,
        )
        provider_id = await session.scalar(
            dp_stmt.on_conflict_do_update(
                index_elements=[DataProvider.provider_key],
                set_={
                    "display_name": dp_stmt.excluded.display_name,
                    "provider_kind": dp_stmt.excluded.provider_kind,
                },
            ).returning(DataProvider.id)
        )
        await session.execute(
            insert(ProviderPolicy)
            .values(
                data_provider_id=provider_id,
                policy_revision=1,
                terms_version=PROVIDER_POLICY_TERMS_VERSION,
                terms_url=provider.terms_url,
                purpose=provider.purpose,
                attribution_text=provider.attribution,
                status="DRAFT",
            )
            .on_conflict_do_nothing(
                index_elements=[ProviderPolicy.data_provider_id, ProviderPolicy.policy_revision]
            )
        )
        policy_id = await session.scalar(
            select(ProviderPolicy.id).where(
                ProviderPolicy.data_provider_id == provider_id,
                ProviderPolicy.policy_revision == 1,
            )
        )
        for field_name, (persistence_class, retention) in provider.fields.items():
            await session.execute(
                insert(ProviderFieldRule)
                .values(
                    provider_policy_id=policy_id,
                    field_name=field_name,
                    persistence_class=persistence_class,
                    max_retention=retention,
                )
                .on_conflict_do_nothing()
            )

    # DEC-022: the automated pipeline's reviewer account (no Clerk user behind it).
    await session.execute(
        insert(Account)
        .values(clerk_user_id=SYSTEM_ACCOUNT_CLERK_USER_ID)
        .on_conflict_do_nothing(index_elements=[Account.clerk_user_id])
    )

    await session.commit()
    return await reference_counts(session)


async def reference_counts(session: AsyncSession) -> dict[str, int]:
    counts: dict[str, int] = {}
    for model in (City, Area, Category, FactField, DataProvider, ProviderPolicy, ProviderFieldRule):
        count = await session.scalar(select(func.count()).select_from(model))
        counts[str(model.__tablename__)] = int(count or 0)
    return counts


@app.command()
def seed() -> None:
    """Upsert Đà Nẵng reference data (idempotent)."""

    async def run() -> dict[str, int]:
        try:
            async with session_factory() as session:
                return await seed_reference_data(session)
        finally:
            await engine.dispose()

    for table, count in asyncio.run(run()).items():
        typer.echo(f"{table}: {count}")


@app.command("db-check")
def db_check() -> None:
    """Print the alembic head revision and the database revision; exit 1 if they differ."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option(
        "script_location", str(Path(__file__).resolve().parents[1] / "migrations")
    )
    head = ScriptDirectory.from_config(config).get_current_head()

    async def current() -> str | None:
        try:
            async with engine.connect() as conn:
                exists = await conn.scalar(
                    text("SELECT to_regclass('alembic_version') IS NOT NULL")
                )
                if not exists:
                    return None
                version = await conn.scalar(text("SELECT version_num FROM alembic_version"))
                return None if version is None else str(version)
        finally:
            await engine.dispose()

    db_revision = asyncio.run(current())
    typer.echo(f"alembic head: {head}")
    typer.echo(f"database:     {db_revision}")
    if db_revision != head:
        raise typer.Exit(code=1)


@app.command("run-deletion-jobs")
def run_deletion_jobs_command(
    max_attempts: int = typer.Option(10, min=1, help="Skip jobs that failed this many times."),
) -> None:
    """Purge accounts with a REQUESTED, FAILED or stuck job (FR-071); exit 1 if any failed."""
    from app.trips.deletion import run_deletion_jobs

    async def run() -> tuple[int, int]:
        try:
            async with session_factory() as session:
                report = await run_deletion_jobs(session, max_attempts=max_attempts)
                return len(report.completed), len(report.failed)
        finally:
            await engine.dispose()

    completed, failed = asyncio.run(run())
    typer.echo(f"deletion jobs completed: {completed}")
    typer.echo(f"deletion jobs failed:    {failed}")
    if failed:
        raise typer.Exit(code=1)


routes_app = typer.Typer(help="Google Routes matrix cache (ADR-011).", no_args_is_help=True)
app.add_typer(routes_app, name="routes")


@routes_app.command("warm")
def routes_warm_command(
    limit: int = typer.Option(50, min=1, help="Published places to include (plus anchors)."),
) -> None:
    """Pre-fill routes_matrix_cache for published Đà Nẵng places and the fixed anchors.

    Spends ROUTES_ELEMENTS quota (GONARRA_QUOTA_ROUTES_ELEMENTS_PER_DAY); a cold warm of 50 places
    is ≈ 2 900 elements, so it completes over several days. Only Google results are cached.
    """
    from app.ai.quota import QuotaLedger
    from app.config import get_settings
    from app.routing.provider import select_provider
    from app.routing.warm import WarmReport, warm_routes

    settings = get_settings()

    async def run() -> WarmReport:
        try:
            provider = select_provider(settings, estimate_enabled=settings.routes_estimate_enabled)
            ledger = QuotaLedger(session_factory, settings)
            return await warm_routes(
                session_factory,
                ledger=ledger,
                provider=provider,
                city_code=settings.default_city_code,
                place_limit=limit,
            )
        finally:
            await engine.dispose()

    report = asyncio.run(run())
    typer.echo(f"points: {report.points}")
    for mode, stats in report.by_mode.items():
        typer.echo(
            f"{mode}: pairs={stats.pairs} cache_hits={stats.cache_hits} "
            f"requested={stats.requested_elements} quota_denied={stats.quota_denied_elements} "
            f"failed={stats.failed_elements} cached_writes={stats.cached_writes}"
        )


enrich_app = typer.Typer(help="Grounded AI enrichment (D3).", no_args_is_help=True)
app.add_typer(enrich_app, name="enrich")


@enrich_app.command("descriptions")
def enrich_descriptions_command(
    limit: int = typer.Option(150, min=1, help="Places to process (Tavily ≈ 1 000/month)."),
    food_cafe_cap: int = typer.Option(40, min=0, help="Maximum FOOD + CAFE places."),
    retry_insufficient: bool = typer.Option(
        False, "--retry-insufficient", help="Also retry places that had insufficient evidence."
    ),
    samples: int = typer.Option(5, min=0, help="Random enriched samples to print."),
) -> None:
    """Write grounded VI/EN descriptions for prioritised draft places (then run `publish auto`).

    Sources: Wikipedia extracts, the OSM website, else a Tavily search. Every provider call goes
    through the quota ledger; the run stops gracefully when quota is exhausted.
    """
    import random

    from app.config import get_settings
    from app.ingestion.common import PolicyNotActiveError
    from app.research.enrich import EnrichReport, build_enricher

    settings = get_settings()

    async def run() -> EnrichReport:
        enricher, close = build_enricher(settings, session_factory)
        try:
            async with session_factory() as session:
                return await enricher.run(
                    session,
                    city_code=settings.default_city_code,
                    limit=limit,
                    food_cafe_cap=food_cafe_cap,
                    retry_insufficient=retry_insufficient,
                )
        finally:
            await close()
            await engine.dispose()

    try:
        report = asyncio.run(run())
    except PolicyNotActiveError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(
        f"enrich: selected={report.selected} enriched={report.enriched} "
        f"(hoi_an_area={report.hoi_an_enriched}) insufficient_evidence={report.insufficient} "
        f"no_sources={report.no_sources} failed={report.failed}"
    )
    typer.echo(
        f"  tavily searches={report.tavily_calls} cached={report.tavily_cached} "
        f"pages_fetched={report.pages_fetched}"
    )
    typer.echo(
        "  model calls: "
        + (", ".join(f"{k}={v}" for k, v in sorted(report.model_calls.items())) or "none")
    )
    if report.issues:
        typer.echo(
            "  validation issues: " + ", ".join(f"{k}={v}" for k, v in report.issues.most_common())
        )
    if report.stopped:
        typer.echo(f"  stopped: {report.stopped}")
    for sample in random.sample(report.samples, min(samples, len(report.samples))):
        typer.echo(f"\n  [{sample.slug}] {sample.name_vi}")
        typer.echo(f"    VI: {sample.description_vi}")
        typer.echo(f"    EN: {sample.description_en}")
        typer.echo(f"    cited: {' | '.join(sample.cited_urls)}")


def _register_pipeline_commands() -> None:
    from app.ingestion import cli as pipeline

    app.add_typer(pipeline.policy_app, name="policy")
    app.add_typer(pipeline.areas_app, name="areas")
    app.add_typer(pipeline.ingest_app, name="ingest")
    app.add_typer(pipeline.web_app, name="web-candidates")
    app.add_typer(pipeline.publish_app, name="publish")
    app.add_typer(pipeline.calendar_app, name="closure-rules")
    app.add_typer(pipeline.pipeline_app, name="pipeline")


_register_pipeline_commands()

if __name__ == "__main__":
    app()
