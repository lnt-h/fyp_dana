"""In-memory ``TripStore`` and an app wired to it (no database)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.routes.trips import get_leg_measurer, get_trip_store
from app.main import create_app
from app.models.account import Account
from app.models.planning import (
    AccountDeletionJob,
    IdempotencyRecord,
    PlanPreview,
    PreviewRevision,
    Trip,
)
from app.security.clerk import get_account_allowing_deletion, get_deletion_pending
from app.trips.repository import (
    CandidateInfo,
    CityInfo,
    PublicationInfo,
    SavedItinerary,
)
from app.trips.snapshot import PlanSnapshot, PublishedPlace

NOW = datetime(2026, 11, 6, 9, 0, tzinfo=UTC)


@dataclass
class FakeStore:
    cities: dict[uuid.UUID, CityInfo] = field(default_factory=dict)
    trips: dict[uuid.UUID, Trip] = field(default_factory=dict)
    previews: dict[uuid.UUID, PlanPreview] = field(default_factory=dict)
    revisions: dict[tuple[uuid.UUID, int], PreviewRevision] = field(default_factory=dict)
    saved: dict[uuid.UUID, PlanSnapshot] = field(default_factory=dict)
    pubs: dict[uuid.UUID, PublicationInfo] = field(default_factory=dict)
    cands: dict[uuid.UUID, CandidateInfo] = field(default_factory=dict)
    published: dict[uuid.UUID, PublishedPlace] = field(default_factory=dict)
    idem: dict[tuple[uuid.UUID, str, str], IdempotencyRecord] = field(default_factory=dict)
    pending_idem: dict[tuple[uuid.UUID, str, str], IdempotencyRecord] = field(default_factory=dict)
    jobs: list[AccountDeletionJob] = field(default_factory=list)
    commits: int = 0
    leg_measurer: Any = None  # app.trips.measure.LegMeasurer for manual edits (None = unmeasured)
    rollbacks: int = 0
    saves: int = 0

    async def commit(self) -> None:
        self.commits += 1
        self.idem.update(self.pending_idem)
        self.pending_idem.clear()

    async def rollback(self) -> None:
        self.rollbacks += 1
        self.pending_idem.clear()

    async def get_city(self, city_id: uuid.UUID) -> CityInfo | None:
        return self.cities.get(city_id)

    async def get_account_locale(self, account_id: uuid.UUID) -> str | None:
        return None

    async def get_trip(
        self, account_id: uuid.UUID, trip_id: uuid.UUID, *, for_update: bool = False
    ) -> Trip | None:
        trip = self.trips.get(trip_id)
        return trip if trip is not None and trip.account_id == account_id else None

    async def list_trips(self, account_id: uuid.UUID, **_: Any) -> list[Trip]:
        return [t for t in self.trips.values() if t.account_id == account_id]

    async def add_trip(self, trip: Trip) -> Trip:
        trip.id = uuid.uuid4()
        trip.created_at = trip.updated_at = NOW
        self.trips[trip.id] = trip
        return trip

    async def update_trip_title(self, trip: Trip, title: str | None) -> Trip:
        trip.title = title
        return trip

    async def delete_trip(self, trip: Trip) -> None:
        self.trips.pop(trip.id, None)

    async def saved_itinerary(self, trip_id: uuid.UUID) -> SavedItinerary:
        return SavedItinerary(
            snapshot=self.saved.get(trip_id, PlanSnapshot(days=[])), trip_day_ids={}
        )

    async def active_preview_id(self, trip_id: uuid.UUID) -> uuid.UUID | None:
        return next(
            (p.id for p in self.previews.values() if p.trip_id == trip_id and p.status == "ACTIVE"),
            None,
        )

    async def replace_itinerary(self, trip: Trip, snapshot: PlanSnapshot) -> Trip:
        self.saves += 1
        self.saved[trip.id] = snapshot
        trip.revision += 1
        trip.status = "SAVED"
        trip.saved_at = NOW
        if snapshot.preferences is not None:
            trip.planning_preferences = snapshot.preferences.model_dump(
                mode="json", exclude_none=True
            )
        return trip

    async def get_preview(
        self, account_id: uuid.UUID, preview_id: uuid.UUID, *, for_update: bool = False
    ) -> PlanPreview | None:
        preview = self.previews.get(preview_id)
        return preview if preview is not None and preview.account_id == account_id else None

    async def get_revision(self, preview_id: uuid.UUID, revision: int) -> PreviewRevision | None:
        return self.revisions.get((preview_id, revision))

    async def append_revision(
        self, preview: PlanPreview, revision: PreviewRevision
    ) -> PreviewRevision:
        revision.created_at = NOW
        self.revisions[(preview.id, revision.preview_revision)] = revision
        preview.head_revision = revision.preview_revision
        return revision

    async def set_preview_status(self, preview: PlanPreview, status: str) -> None:
        preview.status = status

    async def publications(self, ids: set[uuid.UUID]) -> dict[uuid.UUID, PublicationInfo]:
        return {i: self.pubs[i] for i in ids if i in self.pubs}

    async def candidates(self, ids: set[uuid.UUID]) -> dict[uuid.UUID, CandidateInfo]:
        return {i: self.cands[i] for i in ids if i in self.cands}

    async def published_places(
        self, place_ids: set[uuid.UUID], city_id: uuid.UUID
    ) -> dict[uuid.UUID, PublishedPlace]:
        return {i: self.published[i] for i in place_ids if i in self.published}

    async def publication_facts(self, publication_id: uuid.UUID, field_codes: Any) -> list[Any]:
        return []

    async def claim_idempotency(
        self,
        account_id: uuid.UUID,
        operation: str,
        key: str,
        request_sha256: str,
        expires_at: datetime,
    ) -> IdempotencyRecord | None:
        scope = (account_id, operation, key)
        if scope in self.idem:
            return self.idem[scope]
        self.pending_idem[scope] = IdempotencyRecord(
            account_id=account_id,
            operation=operation,
            idempotency_key=key,
            request_sha256=request_sha256,
            state="IN_PROGRESS",
            expires_at=expires_at,
        )
        return None

    async def complete_idempotency(
        self,
        account_id: uuid.UUID,
        operation: str,
        key: str,
        *,
        status: int,
        body: dict[str, Any],
        resource_id: uuid.UUID | None,
    ) -> None:
        record = self.pending_idem[(account_id, operation, key)]
        record.state = "COMPLETED"
        record.response_status = status
        record.response_body = body
        record.resource_id = resource_id

    async def open_deletion_job(self, account_id: uuid.UUID) -> AccountDeletionJob | None:
        return self.open_deletion_job_sync(account_id)

    def open_deletion_job_sync(self, account_id: uuid.UUID) -> AccountDeletionJob | None:
        return next(
            (
                j
                for j in self.jobs
                if j.account_id == account_id and j.status in ("REQUESTED", "IN_PROGRESS", "FAILED")
            ),
            None,
        )

    async def latest_deletion_job(self, account_id: uuid.UUID) -> AccountDeletionJob | None:
        jobs = [j for j in self.jobs if j.account_id == account_id]
        return jobs[-1] if jobs else None

    async def add_deletion_job(self, account_id: uuid.UUID) -> AccountDeletionJob:
        job = AccountDeletionJob(
            id=uuid.uuid4(),
            account_id=account_id,
            status="REQUESTED",
            attempt_count=0,
            requested_at=NOW,
            updated_at=NOW,
        )
        self.jobs.append(job)
        return job

    # -- builders ------------------------------------------------------------------------------

    def add_city(self, *, enabled: bool = True) -> CityInfo:
        city = CityInfo(
            id=uuid.uuid4(),
            code="da-nang",
            name_vi="Đà Nẵng",
            name_en="Da Nang",
            time_zone="Asia/Ho_Chi_Minh",
            is_enabled=enabled,
        )
        self.cities[city.id] = city
        return city

    def make_trip(self, account_id: uuid.UUID, city_id: uuid.UUID, **overrides: Any) -> Trip:
        values: dict[str, Any] = {
            "id": uuid.uuid4(),
            "account_id": account_id,
            "city_id": city_id,
            "title": "Đà Nẵng",
            "start_date": date(2026, 12, 1),
            "day_count": 2,
            "status": "DRAFT",
            "revision": 0,
            "planning_preferences": {},
            "saved_at": None,
            "created_at": NOW,
            "updated_at": NOW,
        }
        values.update(overrides)
        trip = Trip(**values)
        self.trips[trip.id] = trip
        return trip

    def make_publication(self, name: str) -> PublicationInfo:
        info = PublicationInfo(
            id=uuid.uuid4(),
            place_id=uuid.uuid4(),
            state="PUBLISHED",
            name_vi=f"{name} VI",
            name_en=f"{name} EN",
            location="SRID=4326;POINT(108.2208 16.0544)",
            entrance_location=None,
        )
        self.pubs[info.id] = info
        self.published[info.place_id] = PublishedPlace(
            place_id=info.place_id,
            catalog_publication_id=info.id,
            visit_minutes_min=30,
            visit_minutes_suggested=60,
            visit_minutes_max=120,
        )
        return info

    def make_candidate(self, name: str) -> CandidateInfo:
        info = CandidateInfo(
            id=uuid.uuid4(),
            name=name,
            name_vi=None,
            name_en=None,
            location=None,
            source_url="https://example.com/cafe",
            fetched_at=NOW,
        )
        self.cands[info.id] = info
        return info

    def make_preview(
        self,
        trip: Trip,
        snapshots: list[dict[str, Any]],
        *,
        health: str = "GOOD",
    ) -> PlanPreview:
        preview = PlanPreview(
            id=uuid.uuid4(),
            account_id=trip.account_id,
            trip_id=trip.id,
            base_trip_revision=trip.revision,
            head_revision=len(snapshots),
            status="ACTIVE",
            expires_at=datetime.now(UTC) + timedelta(days=1),
            created_at=NOW,
            updated_at=NOW,
        )
        self.previews[preview.id] = preview
        for number, snapshot in enumerate(snapshots, start=1):
            self.revisions[(preview.id, number)] = PreviewRevision(
                plan_preview_id=preview.id,
                preview_revision=number,
                parent_revision=number - 1 or None,
                origin="GENERATED",
                plan_health=health,
                snapshot=PlanSnapshot.model_validate(snapshot).model_dump(mode="json"),
                model_version="gemini-test",
                created_at=NOW,
            )
        return preview


def verified_stop(pub: PublicationInfo, ordinal: int, start: time) -> dict[str, Any]:
    end = time(start.hour + 1, start.minute)
    return {
        "id": str(uuid.uuid4()),
        "trust_level": "VERIFIED",
        "place_id": str(pub.place_id),
        "catalog_publication_id": str(pub.id),
        "ordinal": ordinal,
        "planned_arrival": start.isoformat(),
        "planned_departure": end.isoformat(),
        "visit_minutes": 60,
    }


def web_stop(candidate: CandidateInfo, ordinal: int, start: time) -> dict[str, Any]:
    end = time(start.hour + 1, start.minute)
    return {
        "id": str(uuid.uuid4()),
        "trust_level": "WEB_UNVERIFIED",
        "web_place_candidate_id": str(candidate.id),
        "ordinal": ordinal,
        "planned_arrival": start.isoformat(),
        "planned_departure": end.isoformat(),
        "visit_minutes": 60,
    }


def day(index: int, stops: list[dict[str, Any]]) -> dict[str, Any]:
    legs = [
        {
            "from_stop_id": a["id"],
            "to_stop_id": b["id"],
            "travel_mode": "WALK",
            "availability": "AVAILABLE",
            "distance_m": 800,
            "duration_s": 600,
            "data_provider_id": str(uuid.uuid4()),
            "measured_at": NOW.isoformat(),
        }
        for a, b in zip(stops, stops[1:], strict=False)
    ]
    return {
        "day_index": index,
        "day_window_start": "08:00:00",
        "day_window_end": "18:00:00",
        "stops": stops,
        "legs": legs,
    }


@dataclass
class World:
    store: FakeStore
    app: FastAPI
    account_id: uuid.UUID
    city: CityInfo


@pytest.fixture
def world() -> World:
    store = FakeStore()
    account_id = uuid.uuid4()
    app = create_app()
    app.dependency_overrides[get_account_allowing_deletion] = lambda: Account(
        id=account_id, clerk_user_id="user_a"
    )
    # The real guard query runs on the session; here it reads the fake store's jobs.
    app.dependency_overrides[get_deletion_pending] = lambda: (
        store.open_deletion_job_sync(account_id) is not None
    )
    app.dependency_overrides[get_trip_store] = lambda: store
    app.dependency_overrides[get_leg_measurer] = lambda: store.leg_measurer
    return World(store=store, app=app, account_id=account_id, city=store.add_city())


@pytest.fixture
async def client(world: World) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=world.app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


Factory = Callable[..., Any]
