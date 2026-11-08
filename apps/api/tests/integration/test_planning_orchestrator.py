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


async def _publish(db: AsyncSession, city_id: uuid.UUID, slug: str, cat: str, pt: str) -> Any:
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
            " visit_minutes_max, localization_vi_id, localization_en_id)"
            " VALUES (:p, :city, 1, :cat, ST_GeogFromText(:pt), 30, 60, 120, :vi, :en)"
        ),
        {"p": place_id, "city": city_id, "cat": cat, "pt": pt, "vi": loc["vi"], "en": loc["en"]},
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
