"""Catalog search, detail and preferences against the Compose database.

Requires ``alembic upgrade head``; conftest seeds reference data. Every test runs inside one
outer transaction that is rolled back (the session joins it with savepoints), so nothing is left
behind and parallel agents sharing the database are unaffected. Names carry a random token so
assertions never depend on other rows in the catalog.
"""

import random
import string
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import null, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.catalog.normalize import normalize_search_text
from app.catalog.places import PlacesRepository
from app.catalog.preferences import PreferencesRepository
from app.catalog.reference import ReferenceRepository
from app.catalog.search import InvalidCursorError, Near, search_catalog
from app.config import get_settings
from app.db.session import get_db_session
from app.db.types import ewkt_point
from app.main import create_app
from app.models.account import Account
from app.models.catalog import (
    FactEvidence,
    Place,
    PlaceAlias,
    PlaceClosureRule,
    PlaceFact,
    PlaceLocalization,
    Source,
    SourceRevision,
)
from app.models.reference import City, FactField
from app.security.clerk import (
    AuthenticatedUser,
    get_current_account,
    get_current_user,
    get_optional_account,
)

pytestmark = pytest.mark.integration


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async with AsyncSession(
            bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
        ) as db:
            yield db
        await transaction.rollback()
    await engine.dispose()


@pytest.fixture
def token() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=10))


async def da_nang_id(session: AsyncSession) -> uuid.UUID:
    city_id = await session.scalar(select(City.id).where(City.code == "da-nang"))
    assert city_id is not None, "run `uv run python -m app.cli seed` first"
    return city_id


async def create_place(
    session: AsyncSession,
    *,
    city_id: uuid.UUID,
    name_vi: str,
    name_en: str,
    category_code: str = "RELIGIOUS_SITE",
    area_code: str | None = None,
    lng: float = 108.2772,
    lat: float = 16.1003,
    aliases: tuple[str, ...] = (),
    publish: bool = True,
) -> uuid.UUID:
    """A complete candidate (both locales, search names, required facts with sources)."""
    now = datetime.now(UTC)
    place = Place(
        city_id=city_id,
        area_code=area_code,
        slug=f"p-{uuid.uuid4().hex[:12]}",
        category_code=category_code,
        workflow_state="READY_TO_PUBLISH",
        location=ewkt_point(lng, lat),
        visit_minutes_min=30,
        visit_minutes_suggested=60,
        visit_minutes_max=90,
        has_no_media=True,
    )
    session.add(place)
    await session.flush()
    for locale, name in (("vi", name_vi), ("en", name_en)):
        session.add(
            PlaceLocalization(
                place_id=place.id,
                locale=locale,
                localization_revision=1,
                name=name,
                short_description=f"short {locale}",
                description=f"description {locale}",
                translation_origin="ORIGINAL",
                review_state="APPROVED",
                reviewed_at=now,
            )
        )
    seen: set[str] = set()
    for locale, kind, alias in (
        ("vi", "NAME", name_vi),
        ("en", "NAME", name_en),
        *(("vi", "ALIAS", a) for a in aliases),
    ):
        normalized = normalize_search_text(alias)
        if normalized in seen:
            continue
        seen.add(normalized)
        session.add(
            PlaceAlias(
                place_id=place.id,
                locale=locale,
                alias_kind=kind,
                alias=alias,
                alias_normalized=normalized,
                review_state="APPROVED",
            )
        )
    source = Source(
        publisher="Sở Du lịch Đà Nẵng",
        source_kind="OFFICIAL",
        license_code="ALL-RIGHTS-RESERVED",
        attribution_text="© Sở Du lịch Đà Nẵng",
        homepage_url="https://example.invalid",
    )
    session.add(source)
    await session.flush()
    revision = SourceRevision(
        source_id=source.id,
        locator=f"https://example.invalid/{place.id}",
        title="Thông tin điểm đến",
        retrieved_at=now,
    )
    session.add(revision)
    await session.flush()
    required = (
        await session.scalars(select(FactField.code).where(FactField.required_for_publication))
    ).all()
    for code in required:
        known = code == "OPENING_HOURS"
        fact = PlaceFact(
            place_id=place.id,
            field_code=code,
            fact_revision=1,
            knowledge_state="KNOWN" if known else "UNKNOWN",
            # SQL NULL, not JSON null: the JSONB column maps Python None to 'null'::jsonb.
            value={"text": "06:00-21:00"} if known else null(),
            verified_at=now,
            review_state="APPROVED",
        )
        session.add(fact)
        await session.flush()
        session.add(
            FactEvidence(
                place_fact_id=fact.id, source_revision_id=revision.id, supported_claim=code
            )
        )
    await session.flush()
    if publish:
        await session.execute(
            text("SELECT fn_publish_place(:place_id, NULL)"), {"place_id": place.id}
        )
    return place.id


async def test_search_is_diacritic_insensitive_and_excludes_candidates(
    session: AsyncSession, token: str
) -> None:
    city_id = await da_nang_id(session)
    published = await create_place(
        session,
        city_id=city_id,
        name_vi=f"Chùa Linh Ứng {token}",
        name_en=f"Linh Ung Pagoda {token}",
        aliases=(f"Quan Âm Sơn Trà {token}",),
    )
    candidate = await create_place(
        session,
        city_id=city_id,
        name_vi=f"Chùa Linh Ứng Bãi Bụt {token}",
        name_en=f"Linh Ung Bai But {token}",
        publish=False,
    )

    for query in (
        f"chua linh ung {token}",
        f"CHÙA LINH ỨNG {token}",
        f"linh ung pagoda {token}",
        f"quan am son tra {token}",
        f"Linh Ứng {token}",
        f"chua lin ung {token}",  # typo: trigram similarity, not substring
    ):
        page = await search_catalog(session, city_id=city_id, q=query)
        ids = [item.place_id for item in page.items]
        assert published in ids[:5], query
        assert candidate not in ids, query

    item = next(
        i
        for i in (await search_catalog(session, city_id=city_id, q=token, limit=50)).items
        if i.place_id == published
    )
    assert item.trust_level == "VERIFIED"
    assert item.name("vi") == f"Chùa Linh Ứng {token}"
    assert item.name("en") == f"Linh Ung Pagoda {token}"
    assert abs(item.lat - 16.1003) < 1e-6 and abs(item.lng - 108.2772) < 1e-6


async def test_search_filters_category_area_and_location(session: AsyncSession, token: str) -> None:
    city_id = await da_nang_id(session)
    beach = await create_place(
        session,
        city_id=city_id,
        name_vi=f"Biển Mỹ Khê {token}",
        name_en=f"My Khe Beach {token}",
        category_code="BEACH",
        area_code="my-khe-ngu-hanh-son",
        lng=108.2480,
        lat=16.0610,
    )
    old_town = await create_place(
        session,
        city_id=city_id,
        name_vi=f"Chùa Cầu {token}",
        name_en=f"Japanese Covered Bridge {token}",
        category_code="HERITAGE",
        area_code="hoi-an-old-town",
        lng=108.3262,
        lat=15.8772,
    )

    async def ids(**filters: Any) -> set[uuid.UUID]:
        filters.setdefault("q", token)
        page = await search_catalog(session, city_id=city_id, limit=50, **filters)
        return {item.place_id for item in page.items} & {beach, old_town}

    assert await ids() == {beach, old_town}
    assert await ids(category_code="BEACH") == {beach}
    assert await ids(category_code="beach") == {beach}  # lower-case accepted
    assert await ids(area_code="hoi-an-old-town") == {old_town}
    assert await ids(near=Near(lat=16.0612, lng=108.2482, radius_m=500)) == {beach}
    assert await ids(sort="name") == {beach, old_town}
    assert await ids(q=None, category_code="HERITAGE", area_code="hoi-an-old-town") >= {old_town}


async def test_search_pagination_is_stable(session: AsyncSession, token: str) -> None:
    city_id = await da_nang_id(session)
    created = {
        await create_place(
            session, city_id=city_id, name_vi=f"Điểm {n} {token}", name_en=f"Spot {n} {token}"
        )
        for n in ("Một", "Hai", "Ba")
    }
    for sort in ("relevance", "name"):
        seen: list[uuid.UUID] = []
        cursor = None
        for _ in range(10):
            page = await search_catalog(
                session,
                city_id=city_id,
                q=token,
                sort=sort,
                limit=2,
                cursor=cursor,  # type: ignore[arg-type]
            )
            assert len(page.items) <= 2
            seen.extend(item.place_id for item in page.items)
            cursor = page.next_cursor
            if cursor is None:
                break
        assert len(seen) == len(set(seen)), sort
        assert created <= set(seen), sort

    first = await search_catalog(session, city_id=city_id, q=token, limit=1)
    assert first.next_cursor is not None
    with pytest.raises(InvalidCursorError):
        await search_catalog(
            session, city_id=city_id, q=token, category_code="BEACH", cursor=first.next_cursor
        )


async def test_place_detail_and_http_routes(session: AsyncSession, token: str) -> None:
    city_id = await da_nang_id(session)
    place_id = await create_place(
        session,
        city_id=city_id,
        name_vi=f"Ngũ Hành Sơn {token}",
        name_en=f"Marble Mountains {token}",
        category_code="NATURE",
        area_code="my-khe-ngu-hanh-son",
    )
    candidate_id = await create_place(
        session,
        city_id=city_id,
        name_vi=f"Ứng viên {token}",
        name_en=f"Cand {token}",
        publish=False,
    )
    revision_id = await session.scalar(
        select(SourceRevision.id).where(
            SourceRevision.locator == f"https://example.invalid/{place_id}"
        )
    )
    session.add(
        PlaceClosureRule(
            city_id=city_id,
            source_revision_id=revision_id,
            applies_to="PLACE",
            place_id=place_id,
            rule_kind="WEEKLY",
            effect="CLOSED",
            params={"weekdays": [1]},
            severity="BLOCKING",
            note_vi="Đóng cửa thứ Hai",
            note_en="Closed on Mondays",
            review_state="APPROVED",
            verified_at=datetime.now(UTC),
        )
    )
    await session.flush()

    detail = await PlacesRepository(session).get_published_detail(place_id)
    assert detail is not None
    assert detail.area is not None and detail.area.code == "my-khe-ngu-hanh-son"
    states = {fact.field_code: fact.knowledge_state for fact in detail.facts}
    assert states["OPENING_HOURS"] == "KNOWN" and states["ADMISSION_PRICE"] == "UNKNOWN"
    assert all(fact.sources for fact in detail.facts)
    assert await PlacesRepository(session).get_published_detail(candidate_id) is None
    pool = await PlacesRepository(session).list_published(city_id, category_codes=["NATURE"])
    assert place_id in {p.place_id for p in pool}

    account = Account(clerk_user_id=f"integration_{uuid.uuid4()}")
    session.add(account)
    await session.flush()

    app: FastAPI = create_app()

    async def same_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db_session] = same_session
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser("u", None)
    app.dependency_overrides[get_current_account] = lambda: account
    app.dependency_overrides[get_optional_account] = lambda: account
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        cities = (await client.get("/v1/cities")).json()["items"]
        assert [c["code"] for c in cities] == ["da-nang"]
        assert "hoi-an-old-town" in {a["code"] for a in cities[0]["areas"]}
        assert cities[0]["centre"] is not None

        categories = (await client.get("/v1/categories")).json()["items"]
        assert "HERITAGE" in {c["code"] for c in categories}

        found = await client.get(
            "/v1/places", params={"q": f"ngu hanh son {token}", "category_code": "nature"}
        )
        assert found.status_code == 200
        assert found.json()["items"][0]["id"] == str(place_id)
        assert found.json()["items"][0]["trust_level"] == "VERIFIED"

        body = (await client.get(f"/v1/places/{place_id}", params={"locale": "en"})).json()
        assert body["name"] == f"Marble Mountains {token}"
        assert body["name_vi"] == f"Ngũ Hành Sơn {token}"
        assert body["area"]["code"] == "my-khe-ngu-hanh-son"
        facts = {fact["field_code"]: fact for fact in body["facts"]}
        assert facts["ADMISSION_PRICE"]["value"] is None
        assert facts["ADMISSION_PRICE"]["source"]["publisher"] == "Sở Du lịch Đà Nẵng"
        assert facts["OPENING_HOURS"]["freshness"] == "CURRENT"
        assert "Closed on Mondays" in {rule["note"] for rule in body["closure_rules"]}
        assert body["attributions"][0]["attribution_text"] == "© Sở Du lịch Đà Nẵng"

        assert (await client.get(f"/v1/places/{candidate_id}")).status_code == 404
        bad = await client.get("/v1/places", params={"cursor": "garbage"})
        assert bad.status_code == 400 and bad.json()["error"]["code"] == "invalid_cursor"
        hoi_an = await client.get("/v1/places", params={"city_code": "hoi-an"})
        assert hoi_an.status_code == 422

        defaults = (await client.get("/v1/me/preferences")).json()
        assert defaults["locale"] == "vi" and defaults["updated_at"] is None
        saved = await client.put(
            "/v1/me/preferences",
            json={
                "locale": "en",
                "pace": "RELAXED",
                "interest_category_codes": ["heritage", "BEACH"],
                "allowed_modes": ["WALK"],
                "day_start_time": "08:00",
                "day_end_time": "20:30",
                "ai_notice_acknowledged": True,
            },
        )
        assert saved.status_code == 200, saved.text
        stored = saved.json()
        assert stored["interest_category_codes"] == ["HERITAGE", "BEACH"]
        assert stored["ai_notice_acknowledged_at"] is not None
        again = await client.put(
            "/v1/me/preferences",
            json={"locale": "en", "interest_category_codes": [], "allowed_modes": ["DRIVE"]},
        )
        # The AI-notice acknowledgement is kept once recorded.
        assert again.json()["ai_notice_acknowledged_at"] == stored["ai_notice_acknowledged_at"]

        # Account locale now drives the default content language.
        default_locale = (await client.get(f"/v1/places/{place_id}")).json()
        assert default_locale["name"] == f"Marble Mountains {token}"

    assert await PreferencesRepository(session).get_locale(account.id) == "en"
    assert await ReferenceRepository(session).get_enabled_city(city_code="hoi-an") is None


async def test_seed_keeps_only_da_nang_and_removes_unreferenced_cities(
    session: AsyncSession, token: str
) -> None:
    from app.cli import remove_stale_cities

    free, used = f"x-{token}-free", f"x-{token}-used"
    for code in (free, used):
        session.add(City(code=code, name_vi=code, name_en=code, time_zone="Asia/Ho_Chi_Minh"))
    await session.flush()
    used_id = await session.scalar(select(City.id).where(City.code == used))
    await session.execute(
        text(
            "INSERT INTO places (city_id, slug, category_code, location)"
            " VALUES (:c, :s, 'HERITAGE', ST_GeogFromText('SRID=4326;POINT(105.8 21.0)'))"
        ),
        {"c": used_id, "s": f"p-{token}"},
    )
    removed = await remove_stale_cities(session)
    assert free in removed and used not in removed and "da-nang" not in removed
    codes = set((await session.scalars(select(City.code))).all())
    assert "da-nang" in codes and used in codes and free not in codes
    assert await remove_stale_cities(session) == []  # idempotent (the used one is kept)
