"""T-08 against the migrated Compose database. Everything runs inside one outer transaction that
is rolled back at the end (service commits release savepoints), so nothing is left behind."""

import logging
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import Settings, get_settings
from app.db.session import get_db_session
from app.main import create_app
from app.models.account import Account
from app.models.planning import AccountDeletionJob, PlanPreview, PreviewRevision, Trip
from app.repositories.accounts import (
    DeletedSubjectError,
    SQLAlchemyAccountRepository,
    subject_sha256,
)
from app.security.clerk import get_account_allowing_deletion
from app.trips.deletion import run_deletion_jobs

pytestmark = pytest.mark.integration


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


@dataclass
class Fixture:
    session: AsyncSession
    account: Account
    city_id: uuid.UUID
    publications: list[tuple[uuid.UUID, uuid.UUID]]  # (place_id, publication_id)
    candidate_id: uuid.UUID
    app: FastAPI


async def _publication(db: AsyncSession, city_id: uuid.UUID, slug: str, lng: float) -> Any:
    place_id = await db.scalar(
        text(
            "INSERT INTO places (city_id, slug, category_code, workflow_state, location,"
            " visit_minutes_min, visit_minutes_suggested, visit_minutes_max)"
            " VALUES (:city, :slug, 'MUSEUM', 'PUBLISHED',"
            " ST_GeogFromText(:point), 30, 60, 120) RETURNING id"
        ),
        {"city": city_id, "slug": slug, "point": f"SRID=4326;POINT({lng} 16.05)"},
    )
    loc_ids = {}
    for locale in ("vi", "en"):
        loc_ids[locale] = await db.scalar(
            text(
                "INSERT INTO place_localizations (place_id, locale, localization_revision, name,"
                " translation_origin) VALUES (:p, :l, 1, :n, 'ORIGINAL') RETURNING id"
            ),
            {"p": place_id, "l": locale, "n": f"{slug} {locale}"},
        )
    publication_id = await db.scalar(
        text(
            "INSERT INTO catalog_publications (place_id, city_id, publication_revision,"
            " category_code, location, visit_minutes_min, visit_minutes_suggested,"
            " visit_minutes_max, localization_vi_id, localization_en_id)"
            " VALUES (:p, :city, 1, 'MUSEUM', ST_GeogFromText(:point), 30, 60, 120, :vi, :en)"
            " RETURNING id"
        ),
        {
            "p": place_id,
            "city": city_id,
            "point": f"SRID=4326;POINT({lng} 16.05)",
            "vi": loc_ids["vi"],
            "en": loc_ids["en"],
        },
    )
    return place_id, publication_id


@pytest.fixture
async def fx(session: AsyncSession) -> Fixture:
    db = session
    account = Account(clerk_user_id=f"t08_{uuid.uuid4()}")
    db.add(account)
    await db.flush()
    city_id = await db.scalar(text("SELECT id FROM cities WHERE code = 'da-nang'"))
    assert city_id is not None, "run `uv run python -m app.cli seed` first"
    suffix = uuid.uuid4().hex[:8]
    pubs = [
        await _publication(db, city_id, f"t08-museum-{suffix}", 108.21),
        await _publication(db, city_id, f"t08-bridge-{suffix}", 108.22),
        await _publication(db, city_id, f"t08-market-{suffix}", 108.23),
    ]
    source_id = await db.scalar(
        text(
            "INSERT INTO sources (publisher, source_kind, license_code)"
            " VALUES ('example.com', 'WEB', 'UNKNOWN') RETURNING id"
        )
    )
    revision_id = await db.scalar(
        text(
            "INSERT INTO source_revisions (source_id, locator, retrieved_at)"
            " VALUES (:s, :url, now()) RETURNING id"
        ),
        {"s": source_id, "url": f"https://example.com/cafe-{suffix}"},
    )
    candidate_id = await db.scalar(
        text(
            "INSERT INTO web_place_candidates (city_id, name, source_revision_id, fetched_at)"
            " VALUES (:city, 'Cafe found on the web', :rev, now()) RETURNING id"
        ),
        {"city": city_id, "rev": revision_id},
    )
    await db.commit()

    app = create_app()

    async def db_session() -> AsyncIterator[AsyncSession]:
        yield db

    app.dependency_overrides[get_db_session] = db_session
    account_id, clerk_user_id = account.id, account.clerk_user_id
    # A transient copy per request, like get_current_account in its own session. The deletion
    # guard (get_current_account) still runs its real query against this session.
    app.dependency_overrides[get_account_allowing_deletion] = lambda: Account(
        id=account_id, clerk_user_id=clerk_user_id
    )
    return Fixture(db, account, city_id, pubs, candidate_id, app)


def _stop(place: tuple[uuid.UUID, uuid.UUID], ordinal: int, start: str, end: str) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "trust_level": "VERIFIED",
        "place_id": str(place[0]),
        "catalog_publication_id": str(place[1]),
        "ordinal": ordinal,
        "planned_arrival": start,
        "planned_departure": end,
        "visit_minutes": 60,
    }


async def _preview(fx: Fixture, trip_id: uuid.UUID) -> tuple[PlanPreview, list[dict[str, Any]]]:
    db = fx.session
    stops = [
        _stop(fx.publications[0], 1, "09:00:00", "10:00:00"),
        _stop(fx.publications[1], 2, "10:30:00", "11:30:00"),
    ]
    web = {
        "id": str(uuid.uuid4()),
        "trust_level": "WEB_UNVERIFIED",
        "web_place_candidate_id": str(fx.candidate_id),
        "ordinal": 3,
        "planned_arrival": "12:00:00",
        "planned_departure": "13:00:00",
        "visit_minutes": 60,
    }
    leg = {
        "from_stop_id": stops[0]["id"],
        "to_stop_id": stops[1]["id"],
        "travel_mode": "WALK",
        "availability": "UNAVAILABLE",
    }
    window = {"day_index": 1, "day_window_start": "08:00:00", "day_window_end": "18:00:00"}
    rev1 = {"days": [{**window, "stops": stops, "legs": [leg]}]}
    leg2 = {**leg, "from_stop_id": stops[1]["id"], "to_stop_id": web["id"]}
    rev2 = {"days": [{**window, "stops": [*stops, web], "legs": [leg, leg2]}]}
    preview = PlanPreview(
        account_id=fx.account.id,
        trip_id=trip_id,
        base_trip_revision=0,
        head_revision=2,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    db.add(preview)
    await db.flush()
    for number, snapshot in ((1, rev1), (2, rev2)):
        db.add(
            PreviewRevision(
                plan_preview_id=preview.id,
                preview_revision=number,
                parent_revision=number - 1 or None,
                origin="GENERATED",
                plan_health="WARNING",
                snapshot=snapshot,
                model_version="test-model",
            )
        )
    await db.commit()
    return preview, [*stops, web]


async def _client(fx: Fixture) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=fx.app), base_url="http://test")


async def test_trip_preview_edit_and_save_flow(fx: Fixture) -> None:
    async with await _client(fx) as client:
        created = await client.post(
            "/v1/trips",
            json={"city_id": str(fx.city_id), "start_date": "2026-12-01", "day_count": 2},
        )
        assert created.status_code == 201, created.text
        trip_id = uuid.UUID(created.json()["id"])
        await fx.session.refresh(fx.account)  # expired by the replay/409 rollbacks
        preview, stops = await _preview(fx, trip_id)
        preview_id = preview.id  # ORM objects expire on the service's rollbacks

        read = await client.get(f"/v1/plan-previews/{preview_id}?revision=2&locale=en")
        assert read.status_code == 200, read.text
        read_stops = read.json()["days"][0]["stops"]
        assert read_stops[0]["name"].endswith(" en") and read_stops[0]["location"]["longitude"]
        assert read_stops[2]["trust_level"] == "WEB_UNVERIFIED"
        assert read_stops[2]["web_source"]["candidate_id"] == str(fx.candidate_id)
        assert read_stops[2]["place_id"] is None

        edited = await client.patch(
            f"/v1/plan-previews/{preview_id}",
            json={
                "expected_revision": 2,
                "edits": [
                    {
                        "op": "ADD_STOP",
                        "day_index": 2,
                        "place_id": str(fx.publications[2][0]),
                    }
                ],
            },
        )
        # Day 2 is not part of this preview yet: a manual edit never invents a day.
        assert edited.status_code == 422, edited.text
        edited = await client.patch(
            f"/v1/plan-previews/{preview_id}",
            json={
                "expected_revision": 2,
                "edits": [
                    {
                        "op": "ADD_STOP",
                        "day_index": 1,
                        "to_ordinal": 2,
                        "place_id": str(fx.publications[2][0]),
                    }
                ],
            },
        )
        assert edited.status_code == 200, edited.text
        assert edited.json()["preview_revision"] == 3
        assert edited.json()["origin"] == "MANUAL_EDIT"
        assert len(edited.json()["days"][0]["stops"]) == 4

        key = str(uuid.uuid4())
        stale = await client.post(
            f"/v1/plan-previews/{preview_id}/accept",
            json={"expected_preview_revision": 2, "expected_trip_revision": 0},
            headers={"Idempotency-Key": key},
        )
        assert stale.status_code == 409
        assert stale.json()["error"]["code"] == "revision_conflict"

        no_ack = await client.post(
            f"/v1/plan-previews/{preview_id}/accept",
            json={"expected_preview_revision": 3, "expected_trip_revision": 0},
            headers={"Idempotency-Key": key},
        )
        assert no_ack.status_code == 422
        assert no_ack.json()["error"]["code"] == "web_unverified_acknowledgement_required"

        body = {
            "expected_preview_revision": 3,
            "expected_trip_revision": 0,
            "acknowledge_web_unverified": True,
        }
        saved = await client.post(
            f"/v1/plan-previews/{preview_id}/accept", json=body, headers={"Idempotency-Key": key}
        )
        assert saved.status_code == 200, saved.text
        assert saved.headers["idempotent-replayed"] == "false"
        replay = await client.post(
            f"/v1/plan-previews/{preview_id}/accept", json=body, headers={"Idempotency-Key": key}
        )
        assert replay.status_code == 200
        assert replay.headers["idempotent-replayed"] == "true"
        assert replay.json() == saved.json()

        trip = await fx.session.get(Trip, trip_id, populate_existing=True)
        assert trip is not None and trip.revision == 1 and trip.status == "SAVED"
        stop_count = await fx.session.scalar(
            text("SELECT count(*) FROM trip_stops WHERE trip_id = :t"), {"t": trip_id}
        )
        assert stop_count == 4

        detail = (await client.get(f"/v1/trips/{trip_id}")).json()
        assert detail["revision"] == 1 and detail["active_preview_id"] is None
        saved_stops = detail["days"][0]["stops"]
        assert detail["days"][0]["trip_day_id"] is not None
        assert [s["trust_level"] for s in saved_stops].count("WEB_UNVERIFIED") == 1
        assert saved_stops[0]["id"] == stops[0]["id"]  # stable ids from preview to trip

        verified_card = await client.get(
            f"/v1/trips/{trip_id}/stops/{saved_stops[0]['id']}/place-card"
        )
        assert verified_card.status_code == 200, verified_card.text
        card = verified_card.json()
        assert card["address_vi"]["knowledge_state"] == "UNKNOWN"
        assert card["directions"]["target"] == "PLACE_POSITION"
        web_card = (
            await client.get(f"/v1/trips/{trip_id}/stops/{stops[2]['id']}/place-card")
        ).json()
        assert web_card["trust_level"] == "WEB_UNVERIFIED" and web_card["place_id"] is None

        link = await client.get(f"/v1/trips/{trip_id}/handoff-links?kind=STAY")
        assert link.status_code == 200 and "checkIn=2026-12-01" in link.json()["url"]

        stale_delete = await client.delete(f"/v1/trips/{trip_id}?expected_revision=0")
        assert stale_delete.status_code == 409


async def test_foreign_trip_is_not_found(fx: Fixture) -> None:
    other = Account(clerk_user_id=f"t08_other_{uuid.uuid4()}")
    fx.session.add(other)
    await fx.session.flush()
    trip = Trip(account_id=other.id, city_id=fx.city_id, day_count=1, start_date=None)
    fx.session.add(trip)
    await fx.session.commit()
    async with await _client(fx) as client:
        response = await client.get(f"/v1/trips/{trip.id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource_not_found"


class _FakeClerk:
    def __init__(self, failures: int = 0) -> None:
        self.failures = failures
        self.deleted: list[str] = []

    async def delete_user(self, user_id: str) -> None:
        if self.failures:
            self.failures -= 1
            raise RuntimeError("clerk unavailable")
        self.deleted.append(user_id)


async def test_deletion_job_and_purge(fx: Fixture) -> None:
    account_id = fx.account.id
    fx_subject = fx.account.clerk_user_id
    candidate_id = fx.candidate_id
    async with await _client(fx) as client:
        created = await client.post(
            "/v1/trips",
            json={"city_id": str(fx.city_id), "start_date": "2026-12-01", "day_count": 1},
        )
        trip_id = uuid.UUID(created.json()["id"])
        await _preview(fx, trip_id)
        requested = await client.post("/v1/me/deletion", json={"confirm": True})
        assert requested.status_code == 202
        job_id = uuid.UUID(requested.json()["id"])
        again = await client.post("/v1/me/deletion", json={"confirm": True})
        assert again.json()["id"] == str(job_id)

    clerk = _FakeClerk()
    report = await run_deletion_jobs(fx.session, job_ids={job_id}, user_deleter=clerk)
    assert report.completed == [job_id]
    assert clerk.deleted == [fx_subject]
    db = fx.session
    assert await db.scalar(select(func.count()).where(Account.id == account_id)) == 0
    assert await db.scalar(select(func.count()).where(Trip.account_id == account_id)) == 0
    assert await db.scalar(select(func.count()).where(PlanPreview.account_id == account_id)) == 0
    job = await db.get(AccountDeletionJob, job_id, populate_existing=True)
    assert job is not None
    assert job.status == "COMPLETED" and job.account_id is None and job.attempt_count == 1
    assert job.clerk_subject_sha256 == subject_sha256(fx_subject)
    # A still-valid token of the purged subject is refused instead of re-creating an account.
    with pytest.raises(DeletedSubjectError):
        await SQLAlchemyAccountRepository(db).get_or_create(fx_subject)
    assert await db.scalar(select(func.count()).where(Account.clerk_user_id == fx_subject)) == 0
    # Catalog rows referenced by the purged trip are untouched.
    assert (
        await db.scalar(
            text("SELECT count(*) FROM web_place_candidates WHERE id = :c"), {"c": candidate_id}
        )
        == 1
    )


async def test_open_deletion_job_blocks_routes_with_real_lookup(fx: Fixture) -> None:
    async with await _client(fx) as client:
        assert (await client.get("/v1/trips")).status_code == 200
        assert (await client.post("/v1/me/deletion", json={"confirm": True})).status_code == 202
        blocked = await client.get("/v1/trips")
        assert blocked.status_code == 409
        assert blocked.json()["error"]["code"] == "deletion_in_progress"
        assert (await client.get("/v1/me/preferences")).status_code == 409
        assert (await client.get("/v1/me/deletion")).status_code == 200


async def test_clerk_failure_keeps_data_and_retry_completes(fx: Fixture) -> None:
    account_id, subject = fx.account.id, fx.account.clerk_user_id
    async with await _client(fx) as client:
        requested = await client.post("/v1/me/deletion", json={"confirm": True})
        job_id = uuid.UUID(requested.json()["id"])
    clerk = _FakeClerk(failures=1)

    first = await run_deletion_jobs(fx.session, job_ids={job_id}, user_deleter=clerk)
    assert first.failed == [job_id]
    job = await fx.session.get(AccountDeletionJob, job_id, populate_existing=True)
    assert job is not None and job.status == "FAILED" and job.failure_reason == "RuntimeError"
    assert job.account_id == account_id
    assert await fx.session.scalar(select(func.count()).where(Account.id == account_id)) == 1
    async with await _client(fx) as client:  # still guarded while FAILED
        assert (await client.get("/v1/trips")).status_code == 409

    second = await run_deletion_jobs(fx.session, job_ids={job_id}, user_deleter=clerk)
    assert second.completed == [job_id]
    assert clerk.deleted == [subject]
    job = await fx.session.get(AccountDeletionJob, job_id, populate_existing=True)
    assert job is not None and job.status == "COMPLETED" and job.attempt_count == 2
    assert await fx.session.scalar(select(func.count()).where(Account.id == account_id)) == 0


async def test_deletion_without_clerk_secret_completes_and_warns(
    fx: Fixture, caplog: pytest.LogCaptureFixture
) -> None:
    subject = fx.account.clerk_user_id
    async with await _client(fx) as client:
        requested = await client.post("/v1/me/deletion", json={"confirm": True})
        job_id = uuid.UUID(requested.json()["id"])
    settings = Settings(_env_file=None, clerk_secret_key=None)  # type: ignore[call-arg]
    with caplog.at_level(logging.WARNING, logger="gonarra.deletion"):
        report = await run_deletion_jobs(fx.session, job_ids={job_id}, settings=settings)
    assert report.completed == [job_id]
    messages = [r.getMessage() for r in caplog.records if "clerk_not_configured" in r.getMessage()]
    assert messages and str(job_id) in messages[0]
    assert subject not in caplog.text


async def _operation_allowed(session: AsyncSession, operation: str) -> bool:
    definition = await session.scalar(
        text(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint"
            " WHERE conname = 'ck_idempotency_records_operation'"
        )
    )
    return definition is not None and f"'{operation}'" in definition


@pytest.fixture
async def widened_operations(fx: Fixture) -> Fixture:
    """Skip until migration 0006 allows TRIP_CREATE and PREVIEW_EDIT in the CHECK."""
    for operation in ("TRIP_CREATE", "PREVIEW_EDIT"):
        if not await _operation_allowed(fx.session, operation):
            pytest.skip(f"idempotency_records CHECK does not allow {operation} (migration 0006)")
    return fx


async def test_create_and_edit_idempotency_persist(widened_operations: Fixture) -> None:
    fx = widened_operations
    account_id = fx.account.id
    body = {"city_id": str(fx.city_id), "start_date": "2026-12-01", "day_count": 1}
    key = {"Idempotency-Key": str(uuid.uuid4())}
    async with await _client(fx) as client:
        first = await client.post("/v1/trips", json=body, headers=key)
        second = await client.post("/v1/trips", json=body, headers=key)
        assert first.status_code == second.status_code == 201, first.text
        assert second.headers["idempotent-replayed"] == "true"
        assert second.json()["id"] == first.json()["id"]
        reused = await client.post("/v1/trips", json={**body, "day_count": 2}, headers=key)
        assert reused.json()["error"]["code"] == "idempotency_key_reused"
        trip_id = uuid.UUID(first.json()["id"])
        count = await fx.session.scalar(select(func.count()).where(Trip.account_id == account_id))
        assert count == 1

        await fx.session.refresh(fx.account)  # expired by the replay/409 rollbacks
        preview, stops = await _preview(fx, trip_id)
        preview_id = preview.id
        edit = {"expected_revision": 2, "edits": [{"op": "LOCK_STOP", "stop_id": stops[0]["id"]}]}
        edit_key = {"Idempotency-Key": str(uuid.uuid4())}
        edited = await client.patch(f"/v1/plan-previews/{preview_id}", json=edit, headers=edit_key)
        assert edited.status_code == 200, edited.text
        replay = await client.patch(f"/v1/plan-previews/{preview_id}", json=edit, headers=edit_key)
        assert replay.status_code == 200 and replay.headers["idempotent-replayed"] == "true"
        assert replay.json() == edited.json()
