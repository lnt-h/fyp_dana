"""propose_trip end to end over HTTP + SSE against the migrated database (no API keys).

Rule-based selector, demo estimate routing, no rationales. Everything runs inside one outer
transaction that is rolled back at the end; the orchestrator's session factory hands out the
same session (its commits release savepoints), so nothing is left behind.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import Settings, get_settings
from app.db.session import get_db_session
from app.main import create_app
from app.models.account import Account
from app.planning.orchestrator import PlanningOrchestrator
from app.planning.workflows import get_planning_workflow
from app.security.clerk import get_account_allowing_deletion

pytestmark = pytest.mark.integration

# (slug, category, lng, lat) — central Đà Nẵng.
PLACES = [
    ("museum", "MUSEUM", 108.2230, 16.0600),
    ("bridge", "HERITAGE", 108.2272, 16.0612),
    ("beach", "BEACH", 108.2468, 16.0602),
    ("market", "MARKET", 108.2240, 16.0680),
    ("lunch", "FOOD", 108.2200, 16.0670),
]


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    async with engine.connect() as connection:
        outer = await connection.begin()
        db = AsyncSession(
            bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        try:
            yield db
        finally:
            await db.close()
            await outer.rollback()
    await engine.dispose()


async def _publish(
    db: AsyncSession,
    city_id: uuid.UUID,
    slug: str,
    cat: str,
    pt: str,
    corpus_revision: int | None = None,
) -> Any:
    place_id = await db.scalar(
        text(
            "INSERT INTO places (city_id, slug, category_code, workflow_state, location,"
            " visit_minutes_min, visit_minutes_suggested, visit_minutes_max)"
            " VALUES (:city, :slug, :cat, 'PUBLISHED', ST_GeogFromText(:pt), 30, 60, 120)"
            " RETURNING id"
        ),
        {"city": city_id, "slug": slug, "cat": cat, "pt": pt},
    )
    loc: dict[str, Any] = {}
    for locale in ("vi", "en"):
        loc[locale] = await db.scalar(
            text(
                "INSERT INTO place_localizations (place_id, locale, localization_revision, name,"
                " translation_origin) VALUES (:p, :l, 1, :n, 'ORIGINAL') RETURNING id"
            ),
            {"p": place_id, "l": locale, "n": f"{slug} {locale}"},
        )
    await db.execute(
        text(
            "INSERT INTO catalog_publications (place_id, city_id, publication_revision,"
            " category_code, location, visit_minutes_min, visit_minutes_suggested,"
            " visit_minutes_max, localization_vi_id, localization_en_id, corpus_revision)"
            " VALUES (:p, :city, 1, :cat, ST_GeogFromText(:pt), 30, 60, 120, :vi, :en, :cr)"
        ),
        {
            "p": place_id,
            "city": city_id,
            "cat": cat,
            "pt": pt,
            "vi": loc["vi"],
            "en": loc["en"],
            "cr": corpus_revision,
        },
    )
    return place_id


def _events(body: str) -> list[tuple[str, dict[str, Any]]]:
    events = []
    for block in body.split("\n\n"):
        if not block or block.startswith(":"):
            continue
        name, data = block.split("\n")
        events.append((name.removeprefix("event: "), json.loads(data.removeprefix("data: "))))
    return events


async def test_propose_trip_end_to_end_over_sse(session: AsyncSession) -> None:
    db = session
    account = Account(clerk_user_id=f"planner_{uuid.uuid4()}")
    db.add(account)
    await db.flush()
    city_id = await db.scalar(text("SELECT id FROM cities WHERE code = 'da-nang'"))
    assert city_id is not None
    suffix = uuid.uuid4().hex[:8]
    seeded = {
        await _publish(db, city_id, f"wt-{slug}-{suffix}", cat, f"SRID=4326;POINT({lng} {lat})")
        for slug, cat, lng, lat in PLACES
    }
    trip_id = await db.scalar(
        text(
            "INSERT INTO trips (account_id, city_id, start_date, day_count)"
            " VALUES (:a, :c, DATE '2026-11-10', 2) RETURNING id"
        ),
        {"a": account.id, "c": city_id},
    )
    await db.commit()

    app = create_app()

    async def db_session() -> AsyncIterator[AsyncSession]:
        yield db

    @asynccontextmanager
    async def shared() -> AsyncIterator[AsyncSession]:
        yield db  # the orchestrator commits release savepoints of the outer transaction

    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        environment="test",
        routes_estimate_enabled=True,
    )
    account_id, clerk_user_id = account.id, account.clerk_user_id
    app.dependency_overrides[get_db_session] = db_session
    app.dependency_overrides[get_account_allowing_deletion] = lambda: Account(
        id=account_id, clerk_user_id=clerk_user_id
    )
    app.dependency_overrides[get_planning_workflow] = lambda: PlanningOrchestrator(shared, settings)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with client.stream(
            "POST",
            f"/v1/trips/{trip_id}/plan-previews",
            json={
                "source": "GENERATE",
                "expected_trip_revision": 0,
                "locale": "en",
                "request_text": "museums and a beach",
            },
            headers={"Accept": "text/event-stream"},
        ) as response:
            body = "".join([chunk async for chunk in response.aiter_text()])
        assert response.status_code == 200
        events = _events(body)
        stages = [data["stage"] for name, data in events if name == "progress"]
        assert stages == [
            "VALIDATING_REQUEST",
            "SELECTING_PLACES",
            "ROUTING",
            "SCHEDULING",
            "CHECKING_HEALTH",
        ]
        name, ready = events[-1]
        assert name == "preview_ready", ready
        assert ready["preview_revision"] == 1
        assert ready["plan_health"] in ("GOOD", "WARNING")  # hours unknown → WARNING

        preview = (await client.get(f"/v1/plan-previews/{ready['preview_id']}")).json()
        days = preview["days"]
        assert len(days) >= 1 and preview["origin"] == "GENERATED"
        stops = [stop for day in days for stop in day["stops"]]
        assert len(stops) >= 2
        assert {uuid.UUID(stop["place_id"]) for stop in stops} <= seeded
        assert all(stop["trust_level"] == "VERIFIED" for stop in stops)
        assert all(stop["planned_arrival"] for stop in stops)
        legs = [leg for day in days for leg in day["legs"]]
        assert legs and all(leg["estimated"] is True for leg in legs)
        assert all(leg["availability"] == "AVAILABLE" and leg["duration_s"] for leg in legs)
        assert any(
            c["type"] == "LEG_ESTIMATED" and c["severity"] == "INFO"
            for leg in legs
            for c in leg["conflicts"]
        )
        assert preview["assumptions"]  # the demo estimate is disclosed

        # JSON mode: a second proposal replaces the ACTIVE preview (one per trip).
        again = await client.post(
            f"/v1/trips/{trip_id}/plan-previews",
            json={"source": "GENERATE", "expected_trip_revision": 0, "locale": "vi"},
        )
        assert again.status_code == 201, again.text
        assert again.json()["id"] != ready["preview_id"]
        old = await client.get(f"/v1/plan-previews/{ready['preview_id']}")
        assert old.status_code == 410

        # Regenerate day 1 of the new preview keeps the plan valid.
        regen = await client.post(
            f"/v1/plan-previews/{again.json()['id']}/regenerate",
            json={"expected_revision": 1, "day_index": 1},
        )
        assert regen.status_code == 201, regen.text
        assert regen.json()["preview_revision"] == 2
        assert regen.json()["origin"] == "DAY_REGENERATED"

        stale = await client.post(
            f"/v1/trips/{trip_id}/plan-previews",
            json={"source": "GENERATE", "expected_trip_revision": 5, "locale": "vi"},
        )
        assert stale.status_code == 409


async def _planner_app(db: AsyncSession, day_count: int = 2) -> tuple[Any, uuid.UUID, set[Any]]:
    account = Account(clerk_user_id=f"planner_{uuid.uuid4()}")
    db.add(account)
    await db.flush()
    city_id = await db.scalar(text("SELECT id FROM cities WHERE code = 'da-nang'"))
    assert city_id is not None
    suffix = uuid.uuid4().hex[:8]
    seeded = {
        await _publish(db, city_id, f"wt-{slug}-{suffix}", cat, f"SRID=4326;POINT({lng} {lat})")
        for slug, cat, lng, lat in PLACES
    }
    trip_id = await db.scalar(
        text(
            "INSERT INTO trips (account_id, city_id, start_date, day_count)"
            " VALUES (:a, :c, DATE '2026-11-10', :d) RETURNING id"
        ),
        {"a": account.id, "c": city_id, "d": day_count},
    )
    await db.commit()
    app = create_app()

    async def db_session() -> AsyncIterator[AsyncSession]:
        yield db

    @asynccontextmanager
    async def shared() -> AsyncIterator[AsyncSession]:
        yield db

    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        environment="test",
        routes_estimate_enabled=True,
    )
    account_id, clerk_user_id = account.id, account.clerk_user_id
    app.dependency_overrides[get_db_session] = db_session
    app.dependency_overrides[get_account_allowing_deletion] = lambda: Account(
        id=account_id, clerk_user_id=clerk_user_id
    )
    app.dependency_overrides[get_planning_workflow] = lambda: PlanningOrchestrator(shared, settings)
    return app, trip_id, seeded


def _modes(preview: dict[str, Any], day_index: int | None = None) -> set[str]:
    return {
        leg["travel_mode"]
        for day in preview["days"]
        if day_index is None or day["day_index"] == day_index
        for leg in day["legs"]
    }


async def test_regenerate_reuses_preview_preferences_and_replays_idempotently(
    session: AsyncSession,
) -> None:
    app, trip_id, _ = await _planner_app(session)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post(
            f"/v1/trips/{trip_id}/plan-previews",
            json={
                "source": "GENERATE",
                "expected_trip_revision": 0,
                "locale": "en",
                "preferences": {"allowed_modes": ["WALK"], "day_start_time": "09:00"},
            },
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        assert created.status_code == 201, created.text
        preview = created.json()
        assert preview["planning_preferences"]["allowed_modes"] == ["WALK"]
        assert preview["planning_preferences"]["day_start_time"] == "09:00"
        assert _modes(preview) <= {"WALK"}
        # Assumptions are stored as keys and rendered in the caller's locale.
        assert any("estimates" in a for a in preview["assumptions"])
        vi = (await client.get(f"/v1/plan-previews/{preview['id']}?locale=vi")).json()
        assert vi["assumptions"] and any("ước tính" in a for a in vi["assumptions"])
        stored = await session.scalar(
            text(
                "SELECT snapshot -> 'assumptions' FROM preview_revisions"
                " WHERE plan_preview_id = :p AND preview_revision = 1"
            ),
            {"p": preview["id"]},
        )
        assert stored == ["estimated_legs"]

        # Regenerate: the preview's WALK preference wins over the account default (WALK+DRIVE
        # → DRIVE), and the day window keeps 09:00.
        key = str(uuid.uuid4())
        body = {"expected_revision": 1, "day_index": 1, "locale": "en"}
        regen = await client.post(
            f"/v1/plan-previews/{preview['id']}/regenerate",
            json=body,
            headers={"Idempotency-Key": key},
        )
        assert regen.status_code == 201, regen.text
        assert regen.json()["preview_revision"] == 2
        assert _modes(regen.json(), 1) <= {"WALK"}
        assert regen.json()["planning_preferences"]["allowed_modes"] == ["WALK"]
        day1 = next(d for d in regen.json()["days"] if d["day_index"] == 1)
        assert day1["day_window_start"] == "09:00"

        # Same key + body: replay of revision 2, not revision_conflict.
        again = await client.post(
            f"/v1/plan-previews/{preview['id']}/regenerate",
            json=body,
            headers={"Idempotency-Key": key},
        )
        assert again.status_code == 201, again.text
        assert again.json()["preview_revision"] == 2
        assert again.json()["head_revision"] == 2
        reused = await client.post(
            f"/v1/plan-previews/{preview['id']}/regenerate",
            json={**body, "day_index": 2},
            headers={"Idempotency-Key": key},
        )
        assert reused.status_code == 409
        assert reused.json()["error"]["code"] == "idempotency_key_reused"

        # Save copies the effective preferences to the trip.
        saved = await client.post(
            f"/v1/plan-previews/{preview['id']}/accept",
            json={"expected_preview_revision": 2, "expected_trip_revision": 0},
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        assert saved.status_code == 200, saved.text
        assert saved.json()["planning_preferences"]["allowed_modes"] == ["WALK"]


async def test_failed_propose_releases_its_idempotency_claim(session: AsyncSession) -> None:
    app, trip_id, _ = await _planner_app(session)
    key = str(uuid.uuid4())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # A must-see id that is not a UUID of this city still parses, but an invalid stored
        # preference makes the step after the claim fail: the claim must not stay IN_PROGRESS.
        await session.execute(
            text(
                'UPDATE trips SET planning_preferences = \'{"must_see_place_ids": ["x"]}\''
                " WHERE id = :t"
            ),
            {"t": trip_id},
        )
        await session.commit()
        failed = await client.post(
            f"/v1/trips/{trip_id}/plan-previews",
            json={"source": "GENERATE", "expected_trip_revision": 0, "locale": "en"},
            headers={"Idempotency-Key": key},
        )
        assert failed.status_code >= 400
        state = await session.scalar(
            text("SELECT state FROM idempotency_records WHERE idempotency_key = :k"), {"k": key}
        )
        assert state is None  # released, so a retry re-evaluates


async def test_pool_famous_means_a_wikipedia_lead_not_any_description(
    session: AsyncSession,
) -> None:
    from app.planning.pool import load_pool

    db = session
    city_id = await db.scalar(text("SELECT id FROM cities WHERE code = 'da-nang'"))
    suffix = uuid.uuid4().hex[:8]
    plain = await _publish(
        db, city_id, f"wt-plain-{suffix}", "MUSEUM", "SRID=4326;POINT(108.22 16.06)", 1
    )
    wiki = await _publish(
        db, city_id, f"wt-wiki-{suffix}", "MUSEUM", "SRID=4326;POINT(108.23 16.06)", 1
    )
    # Every place has a description now (short / AI_SUMMARY): that alone is not fame.
    await db.execute(
        text(
            "UPDATE place_localizations SET description = 'A long description.',"
            " translation_origin = 'AI_SUMMARY' WHERE place_id IN (:a, :b)"
        ),
        {"a": plain, "b": wiki},
    )
    provider = await db.scalar(
        text("SELECT id FROM data_providers WHERE provider_key = 'wikipedia'")
    )
    source = await db.scalar(
        text(
            "INSERT INTO sources (data_provider_id, publisher, source_kind, license_code,"
            " attribution_text) VALUES (:p, 'Wikipedia', 'REFERENCE', 'CC-BY-SA-4.0',"
            " 'Wikipedia contributors') RETURNING id"
        ),
        {"p": provider},
    )
    revision = await db.scalar(
        text(
            "INSERT INTO source_revisions (source_id, locator, retrieved_at)"
            " VALUES (:s, :u, now()) RETURNING id"
        ),
        {"s": source, "u": f"https://vi.wikipedia.org/wiki/{suffix}"},
    )
    vector = "[" + ",".join(["0.01"] * 768) + "]"
    chunk = await db.scalar(
        text(
            "INSERT INTO knowledge_chunks (city_id, place_id, locale, section, corpus_revision,"
            " chunk_index, content, content_sha256, embedding, embedding_model, review_state)"
            " VALUES (:city, :p, 'vi', 'OVERVIEW', 1, 0, 'Lead.', repeat('a', 64),"
            " CAST(:v AS vector), 'test', 'APPROVED') RETURNING id"
        ),
        {"city": city_id, "p": wiki, "v": vector},
    )
    await db.execute(
        text("INSERT INTO knowledge_chunk_sources VALUES (:c, :r)"),
        {"c": chunk, "r": revision},
    )
    pool = {p.place_id: p for p in await load_pool(db, city_id)}
    assert pool[wiki].famous is True
    assert pool[plain].famous is False
